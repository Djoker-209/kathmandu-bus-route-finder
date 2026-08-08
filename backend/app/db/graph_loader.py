"""Loads stops/route_stops from Postgres and hands them to the
(database-agnostic) graph_engine to build a NetworkX graph.

The graph is expensive to rebuild (O(stops^2) for the transfer-edge
pass) relative to a single route lookup, so we build it once and cache
it in memory. Call `reload_graph()` after admin writes (new stop,
new route, etc.) to invalidate the cache -- see api/admin.py.

Column mapping note: the production schema (migration 0002) has Text
IDs and columns named `stop_name` / `sequence_no`, not the `Integer`
IDs and `name` / `sequence_order` columns this loader originally
targeted (that was the 0001 scaffold schema). graph_engine's own
dataclass field names (`name`, `sequence_order`) are unchanged -- only
the DB column names being read here changed. Also: the production
`stops` table has explicit `lat`/`lng` float columns, so there's no
need to parse them back out of `geom` via shapely anymore.
"""

import threading

import networkx as nx
from sqlalchemy.orm import Session

from app.graph_engine import build_graph
from app.graph_engine.models import RouteStop as GraphRouteStop
from app.graph_engine.models import Stop as GraphStop
from app.models import RouteStop as RouteStopORM
from app.models import Stop as StopORM

_lock = threading.Lock()
_cached_graph: nx.DiGraph | None = None


def _load_stops(db: Session) -> list[GraphStop]:
    return [
        GraphStop(stop_id=row.stop_id, name=row.stop_name, lat=row.lat, lng=row.lng)
        for row in db.query(StopORM).filter(StopORM.status == "active").all()
    ]


def _load_route_stops(db: Session) -> list[GraphRouteStop]:
    return [
        GraphRouteStop(route_id=row.route_id, stop_id=row.stop_id, sequence_order=row.sequence_no)
        for row in db.query(RouteStopORM).all()
    ]


def build_graph_from_db(db: Session) -> nx.DiGraph:
    """Build a fresh graph straight from the database, bypassing the cache."""
    stops = _load_stops(db)
    route_stops = _load_route_stops(db)
    return build_graph(stops, route_stops)


def get_graph(db: Session) -> nx.DiGraph:
    """Return the cached graph, building it on first use."""
    global _cached_graph
    if _cached_graph is None:
        with _lock:
            if _cached_graph is None:  # re-check after acquiring the lock
                _cached_graph = build_graph_from_db(db)
    return _cached_graph


def reload_graph(db: Session) -> nx.DiGraph:
    """Force a rebuild of the cached graph. Call this after any write
    to stops/routes/route_stops so route lookups see the new data.
    """
    global _cached_graph
    with _lock:
        _cached_graph = build_graph_from_db(db)
    return _cached_graph