"""Tests for route_finder.py — Dijkstra (primary) and BFS (comparator)."""
import pytest

from app.graph_engine.graph_builder import build_graph
from app.graph_engine.models import RouteStop, Stop
from app.graph_engine.route_finder import NoRouteFoundError, RouteFinder

STOPS = [
    Stop(1, "A", 27.700, 85.300),
    Stop(2, "B", 27.701, 85.301),
    Stop(3, "C", 27.702, 85.302),
    Stop(4, "D", 27.7021, 85.3021),  # interchange with C
    Stop(5, "E", 27.703, 85.303),
    Stop(99, "Isolated", 27.750, 85.350),
]
ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),
    RouteStop(route_id=2, stop_id=4, sequence_order=1),
    RouteStop(route_id=2, stop_id=5, sequence_order=2),
]


@pytest.fixture
def finder() -> RouteFinder:
    return RouteFinder(build_graph(STOPS, ROUTE_STOPS))


def test_direct_route(finder):
    result = finder.find_route(1, 3)
    assert result.stop_ids == [1, 2, 3]
    assert result.is_transfer is False


def test_transfer_route(finder):
    result = finder.find_route(1, 5)
    assert result.is_transfer is True
    assert result.transfer_stop_id == 4


def test_no_route_to_isolated_stop(finder):
    with pytest.raises(NoRouteFoundError):
        finder.find_route(1, 99)


def test_same_source_and_destination_raises(finder):
    with pytest.raises(ValueError):
        finder.find_route(1, 1)


def test_bfs_matches_dijkstra_on_direct_route(finder):
    dijkstra_result = finder.find_route(1, 3)
    bfs_result = finder.find_route_bfs(1, 3)
    assert dijkstra_result.stop_ids == bfs_result.stop_ids