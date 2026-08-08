"""
API-level tests for GET /route-finder — require a live Postgres/PostGIS
instance (docker compose up -d db) with migration 0002 applied and sample
data imported. Skip cleanly if no DB is reachable.

These specifically guard against a regression where the endpoint returned
one RouteLeg per raw graph edge instead of consolidating consecutive
segments that share the same route_id, which also caused transfer_count
to be computed incorrectly (it was reading pathfinder.py's edge-level
is_transfer flag, which only fires on walking-transfer edges — not on
route changes made at a shared stop).
"""
import pytest
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal


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


def test_route_finder_consolidates_consecutive_same_route_legs(client):
    """
    S0044 -> S0275 is a known multi-transfer path that rides 5 distinct
    routes (R3229256 is ridden twice, non-consecutively). Before the fix,
    each raw graph edge became its own leg, several sharing the same
    route_id back-to-back. After the fix, consecutive same-route segments
    must be merged into a single leg per route ridden.
    """
    resp = client.get("/route-finder", params={"origin": "S0044", "destination": "S0275"})
    assert resp.status_code == 200
    body = resp.json()

    legs = body["legs"]
    route_ids = [leg["route_id"] for leg in legs]

    # No two consecutive legs should share a route_id -- if they did,
    # they should have been merged into one leg.
    for prev_route, next_route in zip(route_ids, route_ids[1:]):
        assert prev_route != next_route, (
            f"Consecutive legs both on {prev_route!r} were not consolidated: {route_ids}"
        )

    # Known shape of this specific path as of the current dataset.
    assert route_ids == [
        "R3232098",
        "R-SAJHA-04",
        "R3229256",
        "R3020231",
        "R3229256",
        "R2302674",
    ]


def test_route_finder_transfer_count_matches_leg_boundaries(client):
    """
    transfer_count must equal len(legs) - 1: the number of times the
    rider actually changes route, regardless of whether the graph edge
    connecting them was flagged is_transfer (walking) or not (same-stop
    route change).
    """
    resp = client.get("/route-finder", params={"origin": "S0044", "destination": "S0275"})
    assert resp.status_code == 200
    body = resp.json()

    assert body["transfer_count"] == len(body["legs"]) - 1
    assert body["transfer_count"] == 5


def test_route_finder_leg_num_stops_reflects_consolidated_hops(client):
    """
    A consolidated leg spanning multiple raw hops on the same route must
    report num_stops > 1, and the total across all legs must be
    internally consistent (each leg's num_stops counts the hops folded
    into it, not just always 1 as it did pre-fix).
    """
    resp = client.get("/route-finder", params={"origin": "S0044", "destination": "S0275"})
    assert resp.status_code == 200
    legs = resp.json()["legs"]

    # First leg on R3232098 covers 4 raw hops (S0044 -> S0087) per the
    # known shape of this path.
    assert legs[0]["route_id"] == "R3232098"
    assert legs[0]["num_stops"] == 4

    # At least one leg must have been consolidated (num_stops > 1) --
    # guards against a future regression back to "always 1".
    assert any(leg["num_stops"] > 1 for leg in legs)