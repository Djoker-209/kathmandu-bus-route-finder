"""
routing/pathfinder.py

Shortest-path search over the graph built by graph_builder.py, exposed as
find_shortest_path() — session in, a fully-described result out (or
NoRouteFoundError if either stop is unknown or nothing connects them).

The graph now has four edge kinds (see graph_builder.py's module docstring
for why): board, ride, alight, walk. board/alight are internal plumbing —
they don't produce a visible leg on their own — so this module filters
them out of the returned segments, but still counts board edges to get
an accurate transfer_count (each board after the first is a transfer,
whether it happened after walking to a new stop or switching routes at
the same stop).
"""

from dataclasses import dataclass
from typing import List, Optional

import networkx as nx
from sqlalchemy.orm import Session

from app.routing import graph_builder as gb


class NoRouteFoundError(Exception):
    """Raised when origin/destination isn't in the graph, or no path connects them."""


@dataclass(frozen=True)
class PathSegment:
    from_stop_id: str
    to_stop_id: str
    route_id: Optional[str]
    is_transfer: bool
    weight: float  # real distance in meters — board/alight plumbing excluded


@dataclass(frozen=True)
class RouteFinderResult:
    segments: List[PathSegment]
    total_distance_m: float
    transfer_count: int


def find_shortest_path(
    session: Session, origin_stop_id: str, destination_stop_id: str
) -> RouteFinderResult:
    graph = gb.get_cached_graph(session)

    if origin_stop_id not in graph:
        raise NoRouteFoundError(f"Origin stop '{origin_stop_id}' not found in routing graph")
    if destination_stop_id not in graph:
        raise NoRouteFoundError(f"Destination stop '{destination_stop_id}' not found in routing graph")

    try:
        # origin/destination are physical stop_id strings; ride nodes are
        # (stop_id, route_id) tuples, so this always starts/ends "off the bus."
        path = nx.shortest_path(graph, origin_stop_id, destination_stop_id, weight="weight")
    except nx.NetworkXNoPath as exc:
        raise NoRouteFoundError(
            f"No route found between '{origin_stop_id}' and '{destination_stop_id}'"
        ) from exc

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
                    from_stop_id=u[0],
                    to_stop_id=v[0],
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
        # "alight" edges carry no info we need beyond distance_m (always 0).

    return RouteFinderResult(
        segments=segments,
        total_distance_m=total_distance_m,
        transfer_count=max(board_count - 1, 0),
    )
