"""
Data shapes used by the graph engine.

stop_id / route_id are typed `str` here because the production schema
(migrations/versions/0002_replace_with_full_schema.py) uses Text primary
keys ("S0198", "R042", etc.), not autoincrement integers. Field NAMES
(`name`, `sequence_order`) are kept as-is even though the DB columns are
now `stop_name` / `sequence_no` — this dataclass is graph_engine's own
internal shape, not a DB mirror, so renaming isn't required, and keeping
it unchanged means the existing test suite doesn't need to change.
The mapping from DB column name to this field name happens in
db/graph_loader.py, not here.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stop:
    stop_id: str
    name: str
    lat: float
    lng: float


@dataclass(frozen=True)
class RouteStop:
    route_id: str
    stop_id: str
    sequence_order: int