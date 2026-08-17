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
    """v2 note: 'riding' is an edge between RIDE nodes (stop_id, route_id),
    not between the bare physical stop_id nodes -- see graph_builder.py's
    module docstring for why (v1's flat model let Dijkstra switch routes
    at a shared stop for free). Physical stop_id nodes only connect to
    each other via board/alight/walk edges."""
    graph = gb.build_graph(session=None)
    node_s1 = ("S1", "R_A")
    node_s2 = ("S2", "R_A")
    assert graph.has_edge(node_s1, node_s2)
    assert graph.has_edge(node_s2, node_s1)  # is_bidirectional=True on Route A
    assert graph[node_s1][node_s2]["route_id"] == "R_A"
    assert graph[node_s1][node_s2]["kind"] == "ride"
    assert graph[node_s1][node_s2]["is_transfer"] is False
    # and confirm there is NOT a direct physical-to-physical ride shortcut
    assert not graph.has_edge("S1", "S2")


def test_route_edges_one_directional_when_not_bidirectional(monkeypatch):
    s1 = make_stop("S1", "A", 27.70, 85.31)
    s2 = make_stop("S2", "B", 27.71, 85.32)
    route = make_route("R_ONE_WAY", [s1, s2], bidirectional=False)
    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route])

    graph = gb.build_graph(session=None)
    node_s1 = ("S1", "R_ONE_WAY")
    node_s2 = ("S2", "R_ONE_WAY")
    assert graph.has_edge(node_s1, node_s2)
    assert not graph.has_edge(node_s2, node_s1)


def test_transfer_edge_created_between_close_stops_on_different_routes(two_route_network):
    """v2 note: TRANSFER_PENALTY no longer lives on the walk edge -- it
    moved to the board edge on the far side (see graph_builder.py's
    module docstring on why: it needs to apply to same-stop route
    switches too, which have no walk edge at all). So the walk edge here
    should carry only the real walking distance, and the penalty should
    show up separately on the board edge into route B at S5."""
    from app.routing.constants import TRANSFER_PENALTY

    graph = gb.build_graph(session=None)
    assert graph.has_edge("S2", "S5")
    walk_edge = graph["S2"]["S5"]
    assert walk_edge["is_transfer"] is True
    assert walk_edge["route_id"] is None
    assert walk_edge["kind"] == "walk"
    assert walk_edge["weight"] < TRANSFER_PENALTY  # pure walking distance, ~6m here

    board_edge = graph["S5"][("S5", "R_B")]
    assert board_edge["kind"] == "board"
    assert board_edge["weight"] == TRANSFER_PENALTY


def test_walk_edge_still_created_between_close_stops_on_the_same_route(monkeypatch):
    """v1 suppressed a walk/transfer edge between two stops that already
    share a route. v2 does NOT: build_graph() adds a walk edge between
    any two distinct physical stops within INTERCHANGE_DISTANCE, with no
    same-route check. That's a deliberate simplification, not something
    this test is trying to prove correct -- it's here so that if a future
    change reintroduces the v1 suppression (or removes it further), the
    diff is visible instead of silent.

    Known consequence worth revisiting: on a route whose stops loop back
    near themselves, this can make the pathfinder choose to walk a
    straight-line shortcut between two stops on the SAME route instead of
    riding the bus between them, since walk edges are priced on raw
    haversine distance with no real pedestrian-path check (no rivers,
    walls, one-way alleys, etc. factored in)."""
    s1 = make_stop("S1", "A", 27.70, 85.31)
    s2 = make_stop("S2", "B", 27.70004, 85.31004)  # ~5m from s1
    route = make_route("R_A", [s1, s2])
    monkeypatch.setattr(gb, "get_active_routes", lambda session: [route])

    graph = gb.build_graph(session=None)

    # the real ride edge (between ride nodes) is unaffected -- not a transfer
    ride_edge = graph[("S1", "R_A")][("S2", "R_A")]
    assert ride_edge["is_transfer"] is False

    # ...but a redundant walk edge between the physical stops exists too
    assert graph.has_edge("S1", "S2")
    assert graph["S1"]["S2"]["is_transfer"] is True
    assert graph["S1"]["S2"]["kind"] == "walk"


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