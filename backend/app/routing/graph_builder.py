"""
routing/graph_builder.py

Builds the NetworkX directed graph used for shortest-path route finding.

Graph shape:
  - nodes = stop_id, attrs: lat, lng, stop_name
  - route edges: consecutive stops on an active route (by sequence_no),
    weight = haversine distance in meters, route_id attached. Reverse
    edge also added when route.is_bidirectional.
  - transfer edges: stops on DIFFERENT routes within INTERCHANGE_DISTANCE
    meters of each other, weight = distance + TRANSFER_PENALTY,
    route_id=None, is_transfer=True. This is what lets the pathfinder
    consider "get off here, walk to the nearby stop, catch another bus"
    as a single-transfer route, and TRANSFER_PENALTY is what makes it
    prefer a direct route unless the transfer is genuinely faster.

Both constants come from app.graph_engine.constants — see that file for
the placeholder values and the note that they should be re-tuned (Phase 7)
against real Kathmandu interchange measurements before this goes to prod.
"""

import math

import networkx as nx
from sqlalchemy.orm import Session

from app.db.queries import get_active_routes
from app.graph_engine.constants import EARTH_RADIUS, INTERCHANGE_DISTANCE, TRANSFER_PENALTY

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


def build_graph(session: Session) -> nx.DiGraph:
    graph = nx.DiGraph()
    routes = get_active_routes(session)

    stop_coords: dict[str, tuple[float, float]] = {}
    stop_routes: dict[str, set[str]] = {}

    for route in routes:
        ordered = sorted(route.route_stops, key=lambda rs: rs.sequence_no)

        for rs in ordered:
            stop = rs.stop
            if stop is None:
                continue
            if stop.stop_id not in graph:
                graph.add_node(stop.stop_id, lat=stop.lat, lng=stop.lng, stop_name=stop.stop_name)
                stop_coords[stop.stop_id] = (stop.lat, stop.lng)
            stop_routes.setdefault(stop.stop_id, set()).add(route.route_id)

        for a, b in zip(ordered, ordered[1:]):
            if a.stop is None or b.stop is None:
                continue
            dist = haversine_distance_m(a.stop.lat, a.stop.lng, b.stop.lat, b.stop.lng)
            graph.add_edge(a.stop_id, b.stop_id, weight=dist, route_id=route.route_id, is_transfer=False)
            if route.is_bidirectional:
                graph.add_edge(b.stop_id, a.stop_id, weight=dist, route_id=route.route_id, is_transfer=False)

    # Interchange / transfer edges: stops on different routes within walking
    # distance of each other. O(n^2) over stops actually used by active
    # routes (hundreds, not thousands) — fine for this dataset's size; a
    # spatial index (e.g. a KD-tree) would be the Phase-7 upgrade if the
    # stop count grows a lot.
    stop_ids = list(stop_coords.keys())
    for i, sid_a in enumerate(stop_ids):
        lat_a, lng_a = stop_coords[sid_a]
        for sid_b in stop_ids[i + 1:]:
            lat_b, lng_b = stop_coords[sid_b]
            # cheap prefilter before the trig-heavy haversine call
            if abs(lat_a - lat_b) > 0.01 or abs(lng_a - lng_b) > 0.01:
                continue
            dist = haversine_distance_m(lat_a, lng_a, lat_b, lng_b)
            if dist > INTERCHANGE_DISTANCE:
                continue
            if stop_routes[sid_a] == stop_routes[sid_b]:
                # Same route(s) already connect these stops directly.
                continue
            weight = dist + TRANSFER_PENALTY
            graph.add_edge(sid_a, sid_b, weight=weight, route_id=None, is_transfer=True)
            graph.add_edge(sid_b, sid_a, weight=weight, route_id=None, is_transfer=True)

    return graph


def get_cached_graph(session: Session, refresh: bool = False) -> nx.DiGraph:
    global _graph_cache
    if _graph_cache is None or refresh:
        _graph_cache = build_graph(session)
    return _graph_cache


def invalidate_graph_cache() -> None:
    global _graph_cache
    _graph_cache = None