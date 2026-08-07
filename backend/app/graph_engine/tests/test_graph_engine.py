"""End-to-end tests for the graph engine.

These tests exercise the full pipeline: sample data -> graph builder ->
RouteFinder. They check direct and transfer routes, ensure edge weights
are sane, and validate node attributes expected by downstream code.
"""
import pytest

from app.graph_engine import build_graph, RouteFinder
from app.graph_engine.sample_data import STOPS, ROUTE_STOPS
from app.graph_engine.route_finder import NoRouteFoundError


def test_full_engine_smoke():
	graph = build_graph(STOPS, ROUTE_STOPS)
	finder = RouteFinder(graph)

	# Direct route: Ratnapark (1) -> Tripureshwor (3) via New Road (2)
	res = finder.find_route(1, 3)
	assert res.stop_ids == [1, 2, 3]
	assert res.is_transfer is False

	# Transfer route: Ratnapark (1) -> Kalanki (5) via Tripureshwor
	res2 = finder.find_route(1, 5)
	assert res2.stop_ids[0] == 1
	assert res2.stop_ids[-1] == 5
	assert res2.is_transfer is True
	assert res2.transfer_stop_id == 4

	# No route exists to isolated stop 99
	with pytest.raises(NoRouteFoundError):
		finder.find_route(1, 99)


def test_graph_sanity_checks():
	graph = build_graph(STOPS, ROUTE_STOPS)

	# Nodes include lat/lng metadata
	for node, data in graph.nodes(data=True):
		assert "lat" in data and "lng" in data

	# All edge weights are non-negative and transfer edges exist
	transfer_found = False
	for u, v, data in graph.edges(data=True):
		assert data.get("weight", 0) >= 0
		if data.get("edge_type") == "transfer":
			transfer_found = True
	assert transfer_found


def test_bfs_vs_dijkstra_on_direct_route():
	graph = build_graph(STOPS, ROUTE_STOPS)
	finder = RouteFinder(graph)

	dij = finder.find_route(1, 3)
	bfs = finder.find_route_bfs(1, 3)
	assert dij.stop_ids == bfs.stop_ids
