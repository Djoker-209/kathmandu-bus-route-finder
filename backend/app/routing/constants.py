"""Small set of tunable constants (meters) for the routing graph.

Relocated from app/graph_engine/constants.py (2026-08-07) when the old
int-ID graph_engine module was removed as dead code — this is the only
piece of it that was actually used by the live app/routing module.

These are placeholder values; re-tune against real Kathmandu interchange
measurements before this goes to prod (see app/routing/graph_builder.py).
"""

EARTH_RADIUS: int = 6_371_000
INTERCHANGE_DISTANCE: int = 100
TRANSFER_PENALTY: int = 900
