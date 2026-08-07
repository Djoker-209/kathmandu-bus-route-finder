"""Shortest-path helpers for the transport graph."""

from dataclasses import dataclass
from typing import List, Optional

import networkx as nx


class NoRouteFoundError(Exception):
    pass


@dataclass
class RouteResult:
    stop_ids: List[int]
    total_weight: float
    is_transfer: bool
    transfer_stop_id: Optional[int]


class RouteFinder:
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def find_route(self, source_stop_id: int, dest_stop_id: int) -> RouteResult:
        self._validate_nodes(source_stop_id, dest_stop_id)
        try:
            path = nx.dijkstra_path(self.graph, source_stop_id, dest_stop_id, weight="weight")
            total_weight = nx.dijkstra_path_length(self.graph, source_stop_id, dest_stop_id, weight="weight")
        except nx.NetworkXNoPath as exc:
            raise NoRouteFoundError(f"No route between {source_stop_id} and {dest_stop_id}") from exc
        transfer_stop_id = self._first_transfer_edge_target(path)
        return RouteResult(stop_ids=path, total_weight=total_weight, is_transfer=transfer_stop_id is not None, transfer_stop_id=transfer_stop_id)

    def find_route_bfs(self, source_stop_id: int, dest_stop_id: int) -> RouteResult:
        self._validate_nodes(source_stop_id, dest_stop_id)
        try:
            path = nx.shortest_path(self.graph, source_stop_id, dest_stop_id)
        except nx.NetworkXNoPath as exc:
            raise NoRouteFoundError(f"No route between {source_stop_id} and {dest_stop_id}") from exc
        return RouteResult(stop_ids=path, total_weight=float(len(path) - 1), is_transfer=False, transfer_stop_id=None)

    def _first_transfer_edge_target(self, path: List[int]) -> Optional[int]:
        for a, b in zip(path, path[1:]):
            if self.graph.edges[a, b].get("edge_type") == "transfer":
                return b
        return None

    def _validate_nodes(self, source_stop_id: int, dest_stop_id: int) -> None:
        if source_stop_id == dest_stop_id:
            raise ValueError("Source and destination stops are identical.")
        if source_stop_id not in self.graph:
            raise NoRouteFoundError(f"Unknown source stop: {source_stop_id}")
        if dest_stop_id not in self.graph:
            raise NoRouteFoundError(f"Unknown destination stop: {dest_stop_id}")