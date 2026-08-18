"""
routing/graph_builder.py

Builds the NetworkX directed graph used for shortest-path route finding.

Ride nodes are sequence-aware:
    (stop_id, route_id, sequence_no)

This is important for loop routes where the same physical stop occurs
multiple times in one route, e.g. NY-03.
"""

import math

import networkx as nx
from sqlalchemy.orm import Session

from app.db.queries import get_active_routes
from app.routing.constants import EARTH_RADIUS, INTERCHANGE_DISTANCE, TRANSFER_PENALTY


_graph_cache: nx.DiGraph | None = None


def haversine_distance_m(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """Great-circle distance in meters between two lat/lng points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * EARTH_RADIUS * math.asin(math.sqrt(a))


def _ride_node(
    stop_id: str,
    route_id: str,
    sequence_no: int,
) -> tuple[str, str, int]:
    """
    Identify a particular occurrence of a stop on a route.

    Example:

        (S0185, R-NY-03, 4)
        (S0185, R-NY-03, 12)

    are deliberately different nodes.
    """
    return (stop_id, route_id, sequence_no)


def build_graph(session: Session) -> nx.DiGraph:
    graph = nx.DiGraph()

    routes = get_active_routes(session)

    # Physical stop coordinates.
    stop_coords: dict[str, tuple[float, float]] = {}

    for route in routes:
        ordered = [
            rs
            for rs in sorted(
                route.route_stops,
                key=lambda rs: rs.sequence_no,
            )
            if rs.stop is not None
        ]

        # ------------------------------------------------------------
        # Create physical + sequence-aware ride nodes.
        # ------------------------------------------------------------
        for rs in ordered:
            stop = rs.stop

            if stop.stop_id not in graph:
                graph.add_node(
                    stop.stop_id,
                    lat=stop.lat,
                    lng=stop.lng,
                    stop_name=stop.stop_name,
                    kind="physical",
                )

                stop_coords[stop.stop_id] = (
                    stop.lat,
                    stop.lng,
                )

            ride_node = _ride_node(
                rs.stop_id,
                route.route_id,
                rs.sequence_no,
            )

            graph.add_node(
                ride_node,
                lat=stop.lat,
                lng=stop.lng,
                stop_name=stop.stop_name,
                kind="ride",
                route_id=route.route_id,
                sequence_no=rs.sequence_no,
            )

            # Boarding this route.
            graph.add_edge(
                stop.stop_id,
                ride_node,
                weight=TRANSFER_PENALTY,
                distance_m=0,
                route_id=route.route_id,
                kind="board",
                is_transfer=False,
            )

            # Getting off the bus.
            graph.add_edge(
                ride_node,
                stop.stop_id,
                weight=0,
                distance_m=0,
                route_id=route.route_id,
                kind="alight",
                is_transfer=False,
            )

        # ------------------------------------------------------------
        # Ordered ride edges.
        #
        # Because sequence_no is part of the node, repeated stops
        # remain distinct occurrences.
        # ------------------------------------------------------------
        for a, b in zip(ordered, ordered[1:]):
            dist = haversine_distance_m(
                a.stop.lat,
                a.stop.lng,
                b.stop.lat,
                b.stop.lng,
            )

            node_a = _ride_node(
                a.stop_id,
                route.route_id,
                a.sequence_no,
            )

            node_b = _ride_node(
                b.stop_id,
                route.route_id,
                b.sequence_no,
            )

            graph.add_edge(
                node_a,
                node_b,
                weight=dist,
                distance_m=dist,
                route_id=route.route_id,
                kind="ride",
                is_transfer=False,
            )

            # Only routes explicitly marked bidirectional get reverse
            # ride edges.
            if route.is_bidirectional:
                graph.add_edge(
                    node_b,
                    node_a,
                    weight=dist,
                    distance_m=dist,
                    route_id=route.route_id,
                    kind="ride",
                    is_transfer=False,
                )

    # ------------------------------------------------------------
    # Walking/interchange edges between different physical stops.
    # ------------------------------------------------------------
    stop_ids = list(stop_coords.keys())

    for i, sid_a in enumerate(stop_ids):
        lat_a, lng_a = stop_coords[sid_a]

        for sid_b in stop_ids[i + 1:]:
            lat_b, lng_b = stop_coords[sid_b]

            # Cheap bounding-box rejection.
            if abs(lat_a - lat_b) > 0.01 or abs(lng_a - lng_b) > 0.01:
                continue

            dist = haversine_distance_m(
                lat_a,
                lng_a,
                lat_b,
                lng_b,
            )

            if dist > INTERCHANGE_DISTANCE:
                continue

            graph.add_edge(
                sid_a,
                sid_b,
                weight=dist,
                distance_m=dist,
                route_id=None,
                kind="walk",
                is_transfer=True,
            )

            graph.add_edge(
                sid_b,
                sid_a,
                weight=dist,
                distance_m=dist,
                route_id=None,
                kind="walk",
                is_transfer=True,
            )

    return graph


def get_cached_graph(
    session: Session,
    refresh: bool = False,
) -> nx.DiGraph:
    global _graph_cache

    if _graph_cache is None or refresh:
        _graph_cache = build_graph(session)

    return _graph_cache


def invalidate_graph_cache() -> None:
    global _graph_cache
    _graph_cache = None
