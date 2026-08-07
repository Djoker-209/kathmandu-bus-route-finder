"""Tests for graph_builder.py — nodes, route edges, and transfer edges."""
from app.graph_engine.models import RouteStop, Stop
from app.graph_engine.graph_builder import build_graph
from app.graph_engine.constants import TRANSFER_PENALTY

# Small hand-built network, independent of sample_data.py, so this
# test doesn't silently break if the sample data changes later.
STOPS = [
    Stop(1, "A", 27.700, 85.300),
    Stop(2, "B", 27.701, 85.301),
    Stop(3, "C", 27.702, 85.302),   # close to stop 4 -> interchange
    Stop(4, "D", 27.7021, 85.3021),  # ~50m from stop 3
]
ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),
    RouteStop(route_id=2, stop_id=4, sequence_order=1),
]


def test_all_stops_become_nodes():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.number_of_nodes() == len(STOPS)


def test_route_edges_connect_consecutive_stops_both_directions():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.has_edge(1, 2)
    assert graph.has_edge(2, 1)
    assert graph[1][2]["edge_type"] == "route"


def test_transfer_edge_created_between_nearby_different_route_stops():
    graph = build_graph(STOPS, ROUTE_STOPS)
    assert graph.has_edge(3, 4)
    assert graph[3][4]["edge_type"] == "transfer"


def test_transfer_edge_weight_includes_penalty():
    graph = build_graph(STOPS, ROUTE_STOPS)
    transfer_weight = graph[3][4]["weight"]
    # The transfer weight must be at least the penalty -- if it isn't,
    # the penalty isn't actually being applied.
    assert transfer_weight >= TRANSFER_PENALTY


def test_no_transfer_edge_between_same_route_stops():
    graph = build_graph(STOPS, ROUTE_STOPS)
    # stops 1 and 3 are on the same route -- no transfer edge needed
    # (they're already connected via route edges through stop 2)
    assert graph.get_edge_data(1, 3) is None
    
