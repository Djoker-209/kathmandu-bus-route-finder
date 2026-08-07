"""
Whole-workflow integration test: sample_data -> models -> graph_builder
-> route_finder, exercised end to end exactly as the real API endpoint
will use it later (Phase 10). If this file passes, the entire graph
engine works together, not just in isolated pieces.
"""
from app.graph_engine import build_graph, RouteFinder
from app.graph_engine.sample_data import ROUTE_STOPS, STOPS


def test_full_pipeline_direct_route():
    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    result = finder.find_route(1, 3)  # Ratnapark -> Tripureshwor (Rt.1)

    assert result.stop_ids == [1, 2, 3]
    assert result.is_transfer is False
    assert result.total_weight > 0


def test_full_pipeline_transfer_route():
    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    result = finder.find_route(1, 5)  # Ratnapark -> Kalanki

    assert result.stop_ids[0] == 1
    assert result.stop_ids[-1] == 5
    assert result.is_transfer is True
    assert result.transfer_stop_id == 4  # Tripureshwor (Rt.2 stop)


def test_full_pipeline_no_route_to_isolated_stop():
    from app.graph_engine.route_finder import NoRouteFoundError
    import pytest

    graph = build_graph(STOPS, ROUTE_STOPS)
    finder = RouteFinder(graph)

    with pytest.raises(NoRouteFoundError):
        finder.find_route(1, 99)  # Budhanilkantha, deliberately isolated