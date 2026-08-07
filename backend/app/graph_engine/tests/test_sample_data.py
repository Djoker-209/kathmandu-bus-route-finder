"""Tests for sample_data.py — is the miniature Kathmandu network well-formed."""
from app.graph_engine.sample_data import STOPS, ROUTE_STOPS
from app.graph_engine.utils import haversine_distance
from app.graph_engine.constants import INTERCHANGE_DISTANCE


def test_has_at_least_two_routes():
    route_ids = {rs.route_id for rs in ROUTE_STOPS}
    assert len(route_ids) >= 2


def test_has_a_disconnected_stop_for_edge_case_testing():
    connected_ids = {rs.stop_id for rs in ROUTE_STOPS}
    disconnected = [s for s in STOPS if s.stop_id not in connected_ids]
    assert len(disconnected) >= 1


def test_interchange_pair_is_actually_close_enough_to_be_detected():
    """The two Tripureshwor rows (stop 3, stop 4) must be within the
    interchange proximity threshold, or graph_builder.py will silently
    fail to connect them and no transfer route will ever be found."""
    stop_a = next(s for s in STOPS if s.stop_id == 3)
    stop_b = next(s for s in STOPS if s.stop_id == 4)
    d = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)
    assert d <= INTERCHANGE_DISTANCE


def test_all_route_stops_reference_a_real_stop_id():
    """Catches typos: a route_stops row pointing at a stop_id that
    doesn't exist in STOPS would crash graph_builder.py with a KeyError."""
    stop_ids = {s.stop_id for s in STOPS}
    for rs in ROUTE_STOPS:
        assert rs.stop_id in stop_ids
        