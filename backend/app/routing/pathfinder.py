"""
routing/pathfinder.py

Route finding logic:

1. Look for an active route containing both origin and destination.
2. If a direct route exists, use it directly.
3. If no direct route exists, use NetworkX shortest-path search.

Loop routes are handled correctly even when the same physical stop occurs
multiple times in the same route.
"""

from dataclasses import dataclass
from typing import List, Optional

import networkx as nx
from sqlalchemy.orm import Session

from app.db.queries import get_active_routes
from app.routing import graph_builder as gb


class NoRouteFoundError(Exception):
    """Raised when no route connects the requested stops."""


@dataclass(frozen=True)
class PathSegment:
    from_stop_id: str
    to_stop_id: str
    route_id: Optional[str]
    is_transfer: bool
    weight: float


@dataclass(frozen=True)
class RouteFinderResult:
    segments: List[PathSegment]
    total_distance_m: float
    transfer_count: int
    stop_sequence: List[str]


def _build_direct_route_result(
    graph: nx.DiGraph,
    route,
    origin_stop_id: str,
    destination_stop_id: str,
) -> Optional[RouteFinderResult]:
    """
    Build a direct result from one route.

    Unlike the old implementation, this checks ALL occurrences of the
    origin and destination. This is required for loop routes.
    """

    ordered = [
        rs
        for rs in sorted(
            route.route_stops,
            key=lambda rs: rs.sequence_no,
        )
        if rs.stop is not None
    ]

    if not ordered:
        return None

    origin_indices = [
        i
        for i, rs in enumerate(ordered)
        if rs.stop_id == origin_stop_id
    ]

    destination_indices = [
        i
        for i, rs in enumerate(ordered)
        if rs.stop_id == destination_stop_id
    ]

    if not origin_indices or not destination_indices:
        return None

    candidates: list[tuple[list, float]] = []

    # ------------------------------------------------------------
    # Normal route direction.
    #
    # Origin must occur before destination in the stored sequence.
    # ------------------------------------------------------------
    for origin_index in origin_indices:
        for destination_index in destination_indices:
            if origin_index >= destination_index:
                continue

            selected = ordered[
                origin_index : destination_index + 1
            ]

            distance = _sequence_distance(
                graph,
                route.route_id,
                selected,
            )

            if distance is not None:
                candidates.append(
                    (selected, distance)
                )

    # ------------------------------------------------------------
    # Reverse direction for explicitly bidirectional routes.
    # ------------------------------------------------------------
    if route.is_bidirectional:
        for origin_index in origin_indices:
            for destination_index in destination_indices:
                if origin_index <= destination_index:
                    continue

                forward_slice = ordered[
                    destination_index : origin_index + 1
                ]

                selected = list(
                    reversed(forward_slice)
                )

                distance = _sequence_distance(
                    graph,
                    route.route_id,
                    selected,
                )

                if distance is not None:
                    candidates.append(
                        (selected, distance)
                    )

    if not candidates:
        return None

    selected, total_distance_m = min(
        candidates,
        key=lambda item: item[1],
    )

    segments: list[PathSegment] = []

    stop_sequence = [
        rs.stop_id
        for rs in selected
    ]

    for a, b in zip(selected, selected[1:]):
        node_a = (
            a.stop_id,
            route.route_id,
            a.sequence_no,
        )

        node_b = (
            b.stop_id,
            route.route_id,
            b.sequence_no,
        )

        edge = graph.get_edge_data(
            node_a,
            node_b,
        )

        if edge is None:
            return None

        segments.append(
            PathSegment(
                from_stop_id=a.stop_id,
                to_stop_id=b.stop_id,
                route_id=route.route_id,
                is_transfer=False,
                weight=edge["distance_m"],
            )
        )

    return RouteFinderResult(
        segments=segments,
        total_distance_m=total_distance_m,
        transfer_count=0,
        stop_sequence=stop_sequence,
    )


def _sequence_distance(
    graph: nx.DiGraph,
    route_id: str,
    selected: list,
) -> Optional[float]:
    """
    Return total road-network approximation for a sequence of RouteStop
    occurrences.

    Returns None if one of the required sequence edges does not exist.
    """

    total = 0.0

    for a, b in zip(selected, selected[1:]):
        node_a = (
            a.stop_id,
            route_id,
            a.sequence_no,
        )

        node_b = (
            b.stop_id,
            route_id,
            b.sequence_no,
        )

        edge = graph.get_edge_data(
            node_a,
            node_b,
        )

        if edge is None:
            return None

        total += edge["distance_m"]

    return total


def _find_direct_route(
    session: Session,
    graph: nx.DiGraph,
    origin_stop_id: str,
    destination_stop_id: str,
) -> Optional[RouteFinderResult]:
    """
    Find a route containing both stops.

    If multiple direct routes exist, return the shortest direct one.
    Dijkstra is never used when a direct route is available.
    """

    direct_results: list[RouteFinderResult] = []

    for route in get_active_routes(session):
        result = _build_direct_route_result(
            graph,
            route,
            origin_stop_id,
            destination_stop_id,
        )

        if result is not None:
            direct_results.append(result)

    if not direct_results:
        return None

    return min(
        direct_results,
        key=lambda result: result.total_distance_m,
    )


def _physical_stop_id(node) -> str:
    """
    Convert either a physical node or sequence-aware ride node to its
    underlying physical stop ID.
    """

    if isinstance(node, str):
        return node

    return node[0]


def _find_with_dijkstra(
    graph: nx.DiGraph,
    origin_stop_id: str,
    destination_stop_id: str,
) -> RouteFinderResult:
    """Fallback search used only when no direct route exists."""

    try:
        path = nx.shortest_path(
            graph,
            origin_stop_id,
            destination_stop_id,
            weight="weight",
        )
    except nx.NetworkXNoPath as exc:
        raise NoRouteFoundError(
            f"No route found between '{origin_stop_id}' "
            f"and '{destination_stop_id}'"
        ) from exc

    stop_sequence: list[str] = []

    for node in path:
        physical_id = _physical_stop_id(node)

        if (
            not stop_sequence
            or stop_sequence[-1] != physical_id
        ):
            stop_sequence.append(physical_id)

    segments: list[PathSegment] = []

    board_count = 0
    total_distance_m = 0.0

    for u, v in zip(path, path[1:]):
        edge = graph[u][v]
        kind = edge["kind"]

        total_distance_m += edge["distance_m"]

        if kind == "board":
            board_count += 1

        elif kind == "ride":
            segments.append(
                PathSegment(
                    from_stop_id=_physical_stop_id(u),
                    to_stop_id=_physical_stop_id(v),
                    route_id=edge["route_id"],
                    is_transfer=False,
                    weight=edge["distance_m"],
                )
            )

        elif kind == "walk":
            segments.append(
                PathSegment(
                    from_stop_id=u,
                    to_stop_id=v,
                    route_id=None,
                    is_transfer=True,
                    weight=edge["distance_m"],
                )
            )

    return RouteFinderResult(
        segments=segments,
        total_distance_m=total_distance_m,
        transfer_count=max(
            board_count - 1,
            0,
        ),
        stop_sequence=stop_sequence,
    )


def find_shortest_path(
    session: Session,
    origin_stop_id: str,
    destination_stop_id: str,
) -> RouteFinderResult:

    graph = gb.get_cached_graph(session)

    if origin_stop_id not in graph:
        raise NoRouteFoundError(
            f"Origin stop '{origin_stop_id}' "
            f"not found in routing graph"
        )

    if destination_stop_id not in graph:
        raise NoRouteFoundError(
            f"Destination stop '{destination_stop_id}' "
            f"not found in routing graph"
        )

    # Same physical stop.
    if origin_stop_id == destination_stop_id:
        return RouteFinderResult(
            segments=[],
            total_distance_m=0.0,
            transfer_count=0,
            stop_sequence=[origin_stop_id],
        )

    # ------------------------------------------------------------
    # STEP 1: DIRECT ROUTE
    # ------------------------------------------------------------
    direct_result = _find_direct_route(
        session,
        graph,
        origin_stop_id,
        destination_stop_id,
    )

    # ------------------------------------------------------------
    # STEP 2: DIRECT ROUTE ALWAYS WINS
    # ------------------------------------------------------------
    if direct_result is not None:
        return direct_result

    # ------------------------------------------------------------
    # STEP 3: NO DIRECT ROUTE -> DIJKSTRA
    # ------------------------------------------------------------
    return _find_with_dijkstra(
        graph,
        origin_stop_id,
        destination_stop_id,
    )
