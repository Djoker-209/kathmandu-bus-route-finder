"""
DB-backed tests for app/api/admin.py (write endpoints) -- require a live
Postgres/PostGIS instance, same as tests/test_stops.py. Skip cleanly if
none is reachable.

Uses FastAPI's TestClient against the real app, so these exercise the
full stack: auth dependency, request validation, ORM writes, and the
response schema -- not just the ORM layer in isolation.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.main import app

ADMIN_HEADERS = {"X-Admin-Api-Key": get_settings().admin_api_key}


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
    except OperationalError:
        pytest.skip("No live database available — run `docker compose up -d db` first")
    yield session
    session.close()


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def unique_stop_id():
    """A stop_id that won't collide with real or other test data. Kept
    short -- route_id built from this in test_route_recompute_end_to_end
    must fit RouteCreate's max_length=20, same limit real route_ids
    (e.g. 'R2295986') live under.
    """
    return f"T{uuid.uuid4().hex[:8].upper()}"


def test_create_stop_requires_admin_key(client, unique_stop_id):
    resp = client.post(
        "/admin/stops",
        json={"stop_id": unique_stop_id, "stop_name": "Test Stop", "lat": 27.7, "lng": 85.3},
    )
    assert resp.status_code == 422 or resp.status_code == 401  # missing header vs wrong value


def test_create_stop_rejects_wrong_admin_key(client, unique_stop_id):
    resp = client.post(
        "/admin/stops",
        json={"stop_id": unique_stop_id, "stop_name": "Test Stop", "lat": 27.7, "lng": 85.3},
        headers={"X-Admin-Api-Key": "not-the-real-key"},
    )
    assert resp.status_code == 401


def test_create_stop_succeeds_with_valid_key(client, unique_stop_id, db):
    resp = client.post(
        "/admin/stops",
        json={"stop_id": unique_stop_id, "stop_name": "Test Stop", "lat": 27.7, "lng": 85.3},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["stop_id"] == unique_stop_id
    assert body["status"] == "active"  # server_default, confirms geom/status trigger path worked

    from app.models import Stop
    db.query(Stop).filter(Stop.stop_id == unique_stop_id).delete()
    db.commit()


def test_create_duplicate_stop_id_conflicts(client, unique_stop_id, db):
    payload = {"stop_id": unique_stop_id, "stop_name": "Test Stop", "lat": 27.7, "lng": 85.3}
    first = client.post("/admin/stops", json=payload, headers=ADMIN_HEADERS)
    assert first.status_code == 201

    second = client.post("/admin/stops", json=payload, headers=ADMIN_HEADERS)
    assert second.status_code == 409

    from app.models import Stop
    db.query(Stop).filter(Stop.stop_id == unique_stop_id).delete()
    db.commit()


def test_route_recompute_end_to_end(client, unique_stop_id, db):
    """Full flow: create two stops, a route between placeholder endpoints,
    add route_stops, then recompute -- confirms start/end/total_stops end
    up matching what was actually added, not the placeholders.
    """
    from app.models import Route, RouteStop, Stop

    stop_a = f"{unique_stop_id}A"
    stop_b = f"{unique_stop_id}B"
    route_id = f"R{unique_stop_id}"

    for sid, lat, lng in [(stop_a, 27.70, 85.31), (stop_b, 27.71, 85.32)]:
        resp = client.post(
            "/admin/stops",
            json={"stop_id": sid, "stop_name": sid, "lat": lat, "lng": lng},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201

    resp = client.post(
        "/admin/routes",
        json={
            "route_id": route_id,
            "route_name": "Test Route",
            "vehicle_type": "bus",
            "start_stop_id": stop_a,
            "end_stop_id": stop_a,  # placeholder, both endpoints the same on purpose
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["total_stops"] == 0

    resp = client.post(
        f"/admin/routes/{route_id}/stops",
        json={"stop_id": stop_a, "sequence_no": 1},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    resp = client.post(
        f"/admin/routes/{route_id}/stops",
        json={"stop_id": stop_b, "sequence_no": 2},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201

    resp = client.post(f"/admin/routes/{route_id}/recompute", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["start_stop_id"] == stop_a
    assert body["end_stop_id"] == stop_b
    assert body["total_stops"] == 2

    db.query(RouteStop).filter(RouteStop.route_id == route_id).delete()
    db.query(Route).filter(Route.route_id == route_id).delete()
    db.query(Stop).filter(Stop.stop_id.in_([stop_a, stop_b])).delete(synchronize_session=False)
    db.commit()


def test_graph_reload_invalidates_cache(client):
    resp = client.post("/admin/graph/reload", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert "invalidated" in resp.json()["status"]