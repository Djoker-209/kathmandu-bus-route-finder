"""Tests for utils.py — is the distance calculation numerically correct."""
from app.graph_engine.utils import haversine_distance


def test_distance_between_identical_points_is_zero():
    d = haversine_distance(27.7075, 85.3155, 27.7075, 85.3155)
    assert d == 0


def test_distance_matches_known_real_world_trip():
    """Ratnapark -> Tripureshwor is a known, short real-world distance --
    checked against a plausible range, not an exact hardcoded value,
    since haversine gives straight-line distance, not road distance."""
    d = haversine_distance(27.7075, 85.3155, 27.6953, 85.3130)
    assert 1000 < d < 2000


def test_distance_is_symmetric():
    d1 = haversine_distance(27.7075, 85.3155, 27.6953, 85.3130)
    d2 = haversine_distance(27.6953, 85.3130, 27.7075, 85.3155)
    assert abs(d1 - d2) < 0.001