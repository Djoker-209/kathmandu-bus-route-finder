"""
API-level tests for PATCH /routes/{route_id}/status — require a live
Postgres/PostGIS instance (docker compose up -d db) with migration 0002
applied and sample data imported. Skip cleanly if no DB is reachable.

Uses R2295986 (Sundhara-Shankhamul) as the test route: known to be the
sole connection between S0018 and S0069 in the current dataset, and
known to already be 'active' before/after this test runs, so the test
restores it to 'active' in a finally block regardless of outcome.
"""
import pytest
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings
from app.db.session import SessionLocal

ADMIN_API_KEY = Settings().admin_api_key
TEST_ROUTE_ID = "R2295986"
ORIGIN_STOP = "S0018"
ADJACENT_STOP = "S0069"


@pytest.fixture
def client():
    session = SessionLocal()
    try:
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
    except OperationalError:
        pytest.skip("No live database available — run `docker compose up -d db` first")
    finally:
        session.close()
    return TestClient(app)


def _set_status(client, route_id, new_status):
    return client.patch(
        f"/routes/{route_id}/status",
        json={"status": new_status},
        headers={"X-Admin-Api-Key": ADMIN_API_KEY},
    )


def test_status_update_requires_admin_key(client):
    # No X-Admin-Api-Key header sent. If require_admin_key declares the
    # header via Header(...) with no default, FastAPI's own request
    # validation rejects this with 422 before require_admin_key's function
    # body ever runs (so the explicit 401 in that function is only reached
    # once a header is present but wrong -- see the "unknown route" test
    # below for that case). Either 401/403 (explicit rejection) or 422
    # (missing-header validation) counts as "the request was not let
    # through" for our purposes.
    resp = client.patch(f"/routes/{TEST_ROUTE_ID}/status", json={"status": "active"})
    assert resp.status_code in (401, 403, 422), (
        f"Expected request to be rejected without an admin key, got {resp.status_code}: {resp.text}"
    )


def test_status_update_rejects_unknown_route(client):
    resp = _set_status(client, "R_DOES_NOT_EXIST", "active")
    assert resp.status_code == 404


def test_status_update_rejects_invalid_status_value(client):
    resp = _set_status(client, TEST_ROUTE_ID, "not_a_real_status")
    assert resp.status_code == 422


def test_status_flip_auto_invalidates_graph(client):
    """
    Setting a route to pending_release must immediately remove it (and
    any stop only reachable via it) from the live routing graph, with no
    separate /admin/rebuild-graph call required. Flipping back to active
    must restore routability. Always restores 'active' afterward.
    """
    try:
        resp = _set_status(client, TEST_ROUTE_ID, "pending_release")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_release"

        resp = client.get(
            "/route-finder", params={"origin": ORIGIN_STOP, "destination": ADJACENT_STOP}
        )
        assert resp.status_code == 404, (
            f"{ORIGIN_STOP} should be unroutable while {TEST_ROUTE_ID} is pending_release"
        )

        resp = _set_status(client, TEST_ROUTE_ID, "active")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

        resp = client.get(
            "/route-finder", params={"origin": ORIGIN_STOP, "destination": ADJACENT_STOP}
        )
        assert resp.status_code == 200, (
            f"{ORIGIN_STOP} should be routable again once {TEST_ROUTE_ID} is active"
        )
    finally:
        # Always leave the route active, regardless of assertion outcome above.
        _set_status(client, TEST_ROUTE_ID, "active")
