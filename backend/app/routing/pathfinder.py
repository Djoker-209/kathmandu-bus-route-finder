"""
routing/pathfinder.py

Shortest-path search over the graph built by graph_builder.py, exposed as
find_shortest_path() — session in, a fully-described result out (or
NoRouteFoundError if either stop is unknown or nothing connects them).
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
    weight: float


@dataclass(frozen=True)
class RouteFinderResult:
    stop_sequence: List[str]
    segments: List[PathSegment]
    total_cost: float
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
        path = nx.shortest_path(graph, origin_stop_id, destination_stop_id, weight="weight")
    except nx.NetworkXNoPath as exc:
        raise NoRouteFoundError(
            f"No route found between '{origin_stop_id}' and '{destination_stop_id}'"
        ) from exc

    segments = [
        PathSegment(
            from_stop_id=u,
            to_stop_id=v,
            route_id=graph[u][v]["route_id"],
            is_transfer=graph[u][v]["is_transfer"],
            weight=graph[u][v]["weight"],
        )
        for u, v in zip(path, path[1:])
    ]

    return RouteFinderResult(
        stop_sequence=path,
        segments=segments,
        total_cost=sum(s.weight for s in segments),
        transfer_count=sum(1 for s in segments if s.is_transfer),
    )