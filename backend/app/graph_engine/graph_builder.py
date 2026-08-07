"""Graph construction utilities.

This module builds a single directed, weighted graph representing the
city bus network. Node IDs are `stop_id` values. Two edge kinds are
present:

- "route": connects consecutive stops on the same route; weight is
  the geographic distance in metres.
- "transfer": connects geographically close stops from different
  routes and has an added transfer penalty to reflect walking + wait
  overhead.
"""

from collections import defaultdict
from itertools import combinations
from typing import Dict, Iterable

import networkx as nx

from .models import RouteStop, Stop
from .utils import haversine_distance
from .constants import TRANSFER_PENALTY, INTERCHANGE_DISTANCE


# Edge type markers stored on graph edges
EDGE_TYPE_ROUTE = "route"
EDGE_TYPE_TRANSFER = "transfer"


def build_graph(stops: Iterable[Stop], route_stops: Iterable[RouteStop]) -> nx.DiGraph:
    """Construct and return a directed NetworkX graph for the network.

    Args:
        stops: iterable of `Stop` objects describing known stops.
        route_stops: iterable of `RouteStop` objects describing which
            stops belong to which route and their sequence.

    Returns:
        A `networkx.DiGraph` where node IDs are `stop_id` and edges
        have attributes `weight`, `edge_type` and optionally `route_id`.
    """

    graph = nx.DiGraph()

    stops_by_id: Dict[int, Stop] = {s.stop_id: s for s in stops}
    for stop in stops:
        graph.add_node(stop.stop_id, name=stop.name, lat=stop.lat, lng=stop.lng)

    _add_route_edges(graph, stops_by_id, list(route_stops))
    _add_transfer_edges(graph, stops_by_id, list(route_stops))

    return graph


def _add_route_edges(graph: nx.DiGraph, stops_by_id: Dict[int, Stop], route_stops: list[RouteStop]) -> None:
    """Connect consecutive stops within each route in both directions.

    The graph treats routes as bidirectional by default. If your source
    data contained directionality, adjust this function accordingly.
    """
    by_route: dict[int, list[RouteStop]] = defaultdict(list)
    for rs in route_stops:
        by_route[rs.route_id].append(rs)

    for route_id, stops_in_route in by_route.items():
        stops_in_route.sort(key=lambda rs: rs.sequence_order)
        for a, b in zip(stops_in_route, stops_in_route[1:]):
            # Ignore incomplete references (defensive programming)
            if a.stop_id not in stops_by_id or b.stop_id not in stops_by_id:
                continue

            stop_a, stop_b = stops_by_id[a.stop_id], stops_by_id[b.stop_id]
            dist = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)
            graph.add_edge(a.stop_id, b.stop_id, weight=dist, edge_type=EDGE_TYPE_ROUTE, route_id=route_id)
            graph.add_edge(b.stop_id, a.stop_id, weight=dist, edge_type=EDGE_TYPE_ROUTE, route_id=route_id)


def _add_transfer_edges(graph: nx.DiGraph, stops_by_id: Dict[int, Stop], route_stops: list[RouteStop]) -> None:
    """Add transfer edges between geographically close stops on
    different routes.

    A transfer edge's weight is the geographic distance plus a fixed
    penalty to approximate walk + wait time.
    """
    stop_to_routes: dict[int, set[int]] = defaultdict(set)
    for rs in route_stops:
        stop_to_routes[rs.stop_id].add(rs.route_id)

    stop_ids = list(stop_to_routes.keys())
    for id_a, id_b in combinations(stop_ids, 2):
        # Skip if they already share a route -- then no transfer is needed.
        if stop_to_routes[id_a] & stop_to_routes[id_b]:
            continue

        # Defensive: ensure both stops exist in the provided stop list.
        if id_a not in stops_by_id or id_b not in stops_by_id:
            continue

        stop_a, stop_b = stops_by_id[id_a], stops_by_id[id_b]
        dist = haversine_distance(stop_a.lat, stop_a.lng, stop_b.lat, stop_b.lng)

        if dist <= INTERCHANGE_DISTANCE:
            weight = dist + TRANSFER_PENALTY
            graph.add_edge(id_a, id_b, weight=weight, edge_type=EDGE_TYPE_TRANSFER)
            graph.add_edge(id_b, id_a, weight=weight, edge_type=EDGE_TYPE_TRANSFER)

