"""Tests for models.py — do the dataclasses hold and expose values correctly."""
from app.graph_engine.models import RouteStop, Stop


def test_stop_holds_values_correctly():
    s = Stop(1, "Ratnapark", 27.7075, 85.3155)
    assert s.stop_id == 1
    assert s.name == "Ratnapark"
    assert s.lat == 27.7075
    assert s.lng == 85.3155


def test_route_stop_holds_values_correctly():
    rs = RouteStop(route_id=1, stop_id=1, sequence_order=1)
    assert rs.route_id == 1
    assert rs.stop_id == 1
    assert rs.sequence_order == 1


def test_stop_is_immutable():
    """Stops are frozen dataclasses -- accidental mutation should fail
    loudly, not silently corrupt the graph later."""
    s = Stop(1, "Ratnapark", 27.7075, 85.3155)
    try:
        s.lat = 0.0
        assert False, "Stop should be immutable (frozen=True)"
    except AttributeError:
        pass
    