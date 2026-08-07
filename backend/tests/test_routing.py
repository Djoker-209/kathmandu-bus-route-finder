"""
tests/test_routing.py

Regression tests for app/routing/graph_builder.py and pathfinder.py.
No live database required — uses lightweight stand-ins shaped like the
real Route/Stop/RouteStop ORM objects (same attributes graph_builder.py
actually reads: route.route_stops, rs.stop, rs.sequence_no,
route.is_bidirectional, route.route_id, stop.stop_id/stop_name/lat/lng).

These are fast, deterministic, and safe to run in CI without PostGIS.
For a live-DB correctness check (does the *real* data produce a graph
that matches a route you know by hand), see scripts/verify_schema.py
and the manual check described in that script's docstring — this file
only proves the routing *algorithm* behaves correctly, not that the
production data is clean.
"""

from types import SimpleNamespace

import pytest

from app.routing import graph_builder as gb
from app.routing.pathfinder import NoRouteFoundError, find_shortest_path


def make_stop(stop_id, name, lat, lng):
    return SimpleNamespace(stop_id=stop_id, stop_name=name, lat=lat, lng=lng)


def make_route(route_id, stops, bidirectional=True, status="active"):
    route_stops = [
        SimpleNamespace(stop_id=s.stop_id, sequence_no=i, stop=s)
        for i, s in enumerate(stops, start=1)
    ]
    return SimpleNamespace(
        route_id=route_id,
        route_stops=route_stops,
        is_bidirectional=bidirectional,
        status=status,
    )


@pytest.fixture(autouse=True)
def _reset_graph_cache():
    """Every test gets a clean graph cache — prevents cross-test leakage."""
    gb.invalidate_graph_cache()
    yield
    gb.invalidate_graph_cache()


@pytest.fixture
def two_route_network(monkeypatch):
    """
    Route A: S1 -> S2 -> S3  (bidirectional)
    Route B: S4 -> S5 -> S6  (bidirectional)
    S5 sits ~6m from S2 -- a real interchange, different routes.
    S6 is far from everything on Route A.
    """
    s1 = make_stop("S1", "Ratnapark", 27.7050, 85.3145)
    s2 = make_stop("S2", "Sundhara", 27.7010, 85.3130)
    s3 = make_stop("S3", "Tripureshwor", 27.6950, 85.3120)
    route_a = make_route("R_A", [s1, s2, s3])

    s4 = make_stop("S4", "Koteshwor", 27.6780, 85.3480)
    s5 = make_stop("S5", "Sundhara West", 27.70104, 85.31305)  # ~6m from S2
    s6 = make_stop("S6", "Kalanki", 27.6935, 85.2800)
    route_b = make_route("R_B", [s4, s5, s6])

    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route_a, route_b])
    return {"route_a": route_a, "route_b": route_b}


def test_haversine_known_distance():
    """Ratnapark -> Sundhara is a known ~470m walk; sanity-check the formula."""
    dist = gb.haversine_distance_m(27.7050, 85.3145, 27.7010, 85.3130)
    assert 400 < dist < 550


def test_route_edges_are_bidirectional_when_flagged(two_route_network):
    graph = gb.build_graph(session=None)
    assert graph.has_edge("S1", "S2")
    assert graph.has_edge("S2", "S1")  # is_bidirectional=True on Route A
    assert graph["S1"]["S2"]["route_id"] == "R_A"
    assert graph["S1"]["S2"]["is_transfer"] is False


def test_route_edges_one_directional_when_not_bidirectional(monkeypatch):
    s1 = make_stop("S1", "A", 27.70, 85.31)
    s2 = make_stop("S2", "B", 27.71, 85.32)
    route = make_route("R_ONE_WAY", [s1, s2], bidirectional=False)
    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route])

    graph = gb.build_graph(session=None)
    assert graph.has_edge("S1", "S2")
    assert not graph.has_edge("S2", "S1")


def test_transfer_edge_created_between_close_stops_on_different_routes(two_route_network):
    graph = gb.build_graph(session=None)
    assert graph.has_edge("S2", "S5")
    edge = graph["S2"]["S5"]
    assert edge["is_transfer"] is True
    assert edge["route_id"] is None
    # weight must include the transfer penalty on top of the real walking distance
    from app.graph_engine.constants import TRANSFER_PENALTY
    assert edge["weight"] > TRANSFER_PENALTY


def test_no_transfer_edge_between_stops_already_sharing_a_route(monkeypatch):
    """Two stops 5m apart but on the SAME route shouldn't get a redundant transfer edge."""
    s1 = make_stop("S1", "A", 27.70, 85.31)
    s2 = make_stop("S2", "B", 27.70004, 85.31004)  # ~5m from s1
    route = make_route("R_A", [s1, s2])
    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route])

    graph = gb.build_graph(session=None)
    edge = graph["S1"]["S2"]
    assert edge["is_transfer"] is False  # it's the direct route edge, not a transfer


def test_shortest_path_prefers_direct_route_over_far_transfer(two_route_network):
    """S1 -> S3 is fully on Route A; should never route through the R_B transfer."""
    result = find_shortest_path(session=None, origin_stop_id="S1", destination_stop_id="S3")
    assert result.stop_sequence == ["S1", "S2", "S3"]
    assert result.transfer_count == 0


def test_shortest_path_uses_transfer_when_necessary(two_route_network):
    """S1 -> S6 requires crossing from Route A to Route B via the S2/S5 interchange."""
    result = find_shortest_path(session=None, origin_stop_id="S1", destination_stop_id="S6")
    assert result.stop_sequence == ["S1", "S2", "S5", "S6"]
    assert result.transfer_count == 1
    transfer_segments = [s for s in result.segments if s.is_transfer]
    assert len(transfer_segments) == 1
    assert transfer_segments[0].from_stop_id == "S2"
    assert transfer_segments[0].to_stop_id == "S5"


def test_unknown_origin_raises(two_route_network):
    with pytest.raises(NoRouteFoundError):
        find_shortest_path(session=None, origin_stop_id="DOES_NOT_EXIST", destination_stop_id="S3")


def test_unknown_destination_raises(two_route_network):
    with pytest.raises(NoRouteFoundError):
        find_shortest_path(session=None, origin_stop_id="S1", destination_stop_id="DOES_NOT_EXIST")


def test_disconnected_network_raises_no_route(monkeypatch):
    s1 = make_stop("S1", "A", 27.70, 85.31)
    s2 = make_stop("S2", "B", 27.71, 85.32)
    route_a = make_route("R_A", [s1, s2])

    # Far away, no route/transfer edge will connect it
    s99 = make_stop("S99", "Isolated", 28.50, 84.00)
    route_isolated = make_route("R_ISO", [s99])

    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route_a, route_isolated])
    with pytest.raises(NoRouteFoundError):
        find_shortest_path(session=None, origin_stop_id="S1", destination_stop_id="S99")


def test_graph_cache_reused_until_invalidated(two_route_network):
    graph1 = gb.get_cached_graph(session=None)
    graph2 = gb.get_cached_graph(session=None)
    assert graph1 is graph2  # same object -- not rebuilt on second call

    gb.invalidate_graph_cache()
    graph3 = gb.get_cached_graph(session=None)
    assert graph3 is not graph1  # rebuilt after invalidation