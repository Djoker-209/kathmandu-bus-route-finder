"""
routing/graph_builder.py

Builds the NetworkX directed graph used for shortest-path route finding.

Graph shape (v2 — see note below on why v1 was broken):
  - "physical" nodes: stop_id (string). Represents "standing at this real
    stop, off any bus." attrs: lat, lng, stop_name, kind="physical".
  - "ride" nodes: (stop_id, route_id) tuple. Represents "on this specific
    route, currently at this stop." attrs: lat, lng, stop_name, kind="ride".
  - board edge: physical stop_id -> (stop_id, route_id), weight=
    TRANSFER_PENALTY, distance_m=0, kind="board". This is where the
    penalty actually lives now.
  - alight edge: (stop_id, route_id) -> physical stop_id, weight=0,
    distance_m=0, kind="alight". Free — getting off a bus costs nothing.
  - ride edge: (stop_id, route_id) -> (next_stop_id, route_id), weight=
    haversine distance, distance_m=same, kind="ride". Reverse also added
    when route.is_bidirectional.
  - walk edge: physical stop_id -> physical stop_id, for two DIFFERENT
    stops within INTERCHANGE_DISTANCE metres of each other. weight=
    distance_m=haversine distance (no penalty added here — the board
    edge on the far side already re-applies TRANSFER_PENALTY, so walking
    to a nearby stop and boarding there is priced consistently with
    switching routes at the same stop).

  Why v1 was broken: v1 had ONE node per stop_id, so five different
  routes calling at the same stop were all edges touching the same node.
  Dijkstra could hop from any route's edge to any other route's edge at
  that node for free — nothing in the graph distinguished "the bus I'm
  currently riding" from "a bus that happens to stop here too." Bumping
  TRANSFER_PENALTY did nothing because that constant only applied to the
  separate walking-transfer edges between different nearby stops, never
  to a same-stop route switch (which had no edge, and therefore no cost,
  at all). v2 forces every route switch — same-stop or nearby-stop —
  through an explicit board edge, so the penalty is now unavoidable and
  actually shapes the shortest path.

Both constants live in app.routing.constants — see that file for the
placeholder values and the note that they should be re-tuned (Phase 7)
against real Kathmandu interchange measurements before this goes to prod.
"""

import math

import networkx as nx
from sqlalchemy.orm import Session

from app.db.queries import get_active_routes
from app.routing.constants import EARTH_RADIUS, INTERCHANGE_DISTANCE, TRANSFER_PENALTY

# Simple process-local cache so repeated /route-finder calls in the same
# worker don't rebuild the whole graph from the DB every time. Call
# invalidate_graph_cache() after any write to routes/route_stops/stops.
_graph_cache: nx.DiGraph | None = None


def haversine_distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in meters between two lat/lng points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))


def _ride_node(stop_id: str, route_id: str) -> tuple[str, str]:
    return (stop_id, route_id)


def build_graph(session: Session) -> nx.DiGraph:
    graph = nx.DiGraph()
    routes = get_active_routes(session)

    stop_coords: dict[str, tuple[float, float]] = {}

    for route in routes:
        ordered = [rs for rs in sorted(route.route_stops, key=lambda rs: rs.sequence_no) if rs.stop is not None]

        for rs in ordered:
            stop = rs.stop

            if stop.stop_id not in graph:
                graph.add_node(
                    stop.stop_id, lat=stop.lat, lng=stop.lng, stop_name=stop.stop_name, kind="physical"
                )
                stop_coords[stop.stop_id] = (stop.lat, stop.lng)

            ride_node = _ride_node(stop.stop_id, route.route_id)
            if ride_node not in graph:
                graph.add_node(
                    ride_node, lat=stop.lat, lng=stop.lng, stop_name=stop.stop_name, kind="ride"
                )
                graph.add_edge(
                    stop.stop_id, ride_node,
                    weight=TRANSFER_PENALTY, distance_m=0, route_id=route.route_id,
                    kind="board", is_transfer=False,
                )
                graph.add_edge(
                    ride_node, stop.stop_id,
                    weight=0, distance_m=0, route_id=route.route_id,
                    kind="alight", is_transfer=False,
                )

        for a, b in zip(ordered, ordered[1:]):
            dist = haversine_distance_m(a.stop.lat, a.stop.lng, b.stop.lat, b.stop.lng)
            node_a = _ride_node(a.stop_id, route.route_id)
            node_b = _ride_node(b.stop_id, route.route_id)
            graph.add_edge(node_a, node_b, weight=dist, distance_m=dist, route_id=route.route_id, kind="ride", is_transfer=False)
            if route.is_bidirectional:
                graph.add_edge(node_b, node_a, weight=dist, distance_m=dist, route_id=route.route_id, kind="ride", is_transfer=False)

    # Walking transfer edges between distinct nearby physical stops. Board
    # edges (added above) already carry TRANSFER_PENALTY, so this edge is
    # priced at pure walking distance only — no double-penalizing.
    stop_ids = list(stop_coords.keys())
    for i, sid_a in enumerate(stop_ids):
        lat_a, lng_a = stop_coords[sid_a]
        for sid_b in stop_ids[i + 1:]:
            lat_b, lng_b = stop_coords[sid_b]
            if abs(lat_a - lat_b) > 0.01 or abs(lng_a - lng_b) > 0.01:
                continue
            dist = haversine_distance_m(lat_a, lng_a, lat_b, lng_b)
            if dist > INTERCHANGE_DISTANCE:
                continue
            graph.add_edge(sid_a, sid_b, weight=dist, distance_m=dist, route_id=None, kind="walk", is_transfer=True)
            graph.add_edge(sid_b, sid_a, weight=dist, distance_m=dist, route_id=None, kind="walk", is_transfer=True)

    return graph


def get_cached_graph(session: Session, refresh: bool = False) -> nx.DiGraph:
    global _graph_cache
    if _graph_cache is None or refresh:
        _graph_cache = build_graph(session)
    return _graph_cache


def invalidate_graph_cache() -> None:
    global _graph_cache
    _graph_cache = None
