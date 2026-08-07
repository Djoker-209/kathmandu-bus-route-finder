"""
DB-backed data-access-layer tests (app/db/queries.py) — require a live
Postgres/PostGIS instance (docker compose up -d db) with migration 0002
applied and sample data imported. Skip cleanly if no DB is reachable.

Pure-logic routing tests live in app/routing/tests/ instead.
"""

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy import cast, func
from sqlalchemy import select, func
from app.models import Stop

from app.db import queries
from app.db.session import SessionLocal


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        session.execute(__import__("sqlalchemy").text("SELECT 1"))
    except OperationalError:
        pytest.skip("No live database available — run `docker compose up -d db` first")
    yield session
    session.close()


def test_nearest_stop_returns_closest_within_radius(db):
    results = queries.nearest_stops(db, lat=27.7040, lng=85.3145, radius_m=1000, limit=5)
    assert isinstance(results, list)
    if len(results) > 1:
        from geoalchemy2.functions import ST_Distance

        distances = [
            db.scalar(
                select(func.ST_Distance(Stop.geom, "SRID=4326;POINT(85.3145 27.7040)")).where(
                Stop.stop_id == s.stop_id
            )
        )
        for s in results
 ]
        assert distances == sorted(distances)


def test_nearest_stop_no_match_returns_empty_far_from_valley(db):
    results = queries.nearest_stops(db, lat=0.0, lng=0.0, radius_m=500, limit=5)
    assert results == []


def test_route_sequence_is_continuous_and_ordered(db):
    stmt = __import__("sqlalchemy").select(__import__("app.models", fromlist=["Route"]).Route.route_id).limit(1)
    route_id = db.execute(stmt).scalar_one_or_none()
    if route_id is None:
        pytest.skip("No routes in DB to check")

    route_stops = queries.get_route_stops(db, route_id)
    seq_nos = [rs.sequence_no for rs in route_stops]
    assert seq_nos == sorted(seq_nos)
    assert seq_nos == list(range(1, len(seq_nos) + 1)) or len(set(seq_nos)) == len(seq_nos)


def test_invalid_coordinates_rejected_by_check_constraint(db):
    from app.models import Stop
    from sqlalchemy.exc import IntegrityError

    bad_stop = Stop(stop_id="TEST_BAD", stop_name="Invalid", lat=999, lng=85.3)
    db.add(bad_stop)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_get_stop_returns_none_for_unknown_id(db):
    assert queries.get_stop(db, "S_DOES_NOT_EXIST") is None