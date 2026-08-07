"""
Data-access helpers for the Kathmandu Bus Route Finder.

Spatial lookups go through PostGIS via GeoAlchemy2 against stops.geom.
Everything else is plain SQLAlchemy ORM. All functions take a live
Session so callers control transaction/connection lifecycle.
"""

from typing import List, Optional, Sequence

from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..models import FareRule, Operator, Route, RouteOperator, RouteStop, Stop


def nearest_stops(
    session: Session,
    lat: float,
    lng: float,
    radius_m: int = 500,
    limit: int = 10,
) -> Sequence[Stop]:
    """Stops within radius_m metres of (lat, lng), nearest first."""
    point = f"SRID=4326;POINT({lng} {lat})"
    stmt = (
        select(Stop)
        .where(ST_DWithin(Stop.geom, point, radius_m))
        .order_by(ST_Distance(Stop.geom, point))
        .limit(limit)
    )
    return session.execute(stmt).scalars().all()


def get_stop(session: Session, stop_id: str) -> Optional[Stop]:
    return session.get(Stop, stop_id)


def get_route(session: Session, route_id: str) -> Optional[Route]:
    """Route with its ordered stops and operators eager-loaded."""
    stmt = (
        select(Route)
        .where(Route.route_id == route_id)
        .options(
            selectinload(Route.route_stops).selectinload(RouteStop.stop),
            selectinload(Route.route_operators).selectinload(RouteOperator.operator),
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def get_route_stops_ordered(session: Session, route_id: str) -> Sequence[RouteStop]:
    """Stops on a route, in sequence_no order, each with its Stop eager-loaded."""
    stmt = (
        select(RouteStop)
        .where(RouteStop.route_id == route_id)
        .options(selectinload(RouteStop.stop))
        .order_by(RouteStop.sequence_no)
    )
    return session.execute(stmt).scalars().all()


def get_operator(session: Session, operator_id: str) -> Optional[Operator]:
    return session.get(Operator, operator_id)


def list_routes_by_stop(session: Session, stop_id: str) -> Sequence[Route]:
    """All routes that pass through a given stop."""
    stmt = (
        select(Route)
        .join(RouteStop, RouteStop.route_id == Route.route_id)
        .where(RouteStop.stop_id == stop_id)
        .distinct()
    )
    return session.execute(stmt).scalars().all()


def list_stops(
    session: Session,
    district: Optional[str] = None,
    status: str = "active",
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Stop]:
    """Paged stop listing, optionally filtered by district."""
    stmt = select(Stop).where(Stop.status == status)
    if district:
        stmt = stmt.where(Stop.district == district)
    stmt = stmt.order_by(Stop.stop_id).limit(limit).offset(offset)
    return session.execute(stmt).scalars().all()


def fare_for_distance(session: Session, distance_km: float) -> Optional[FareRule]:
    """Fare band whose [min, max) range covers distance_km."""
    stmt = (
        select(FareRule)
        .where(FareRule.min_distance_km <= distance_km)
        .where(FareRule.max_distance_km > distance_km)
    )
    return session.execute(stmt).scalar_one_or_none()


# --- Added for GET /stops pagination and the routing graph builder ---


def count_stops(session: Session, status: str = "active") -> int:
    """Total stops matching `status`, for pagination totals alongside list_stops()."""
    stmt = select(func.count()).select_from(Stop).where(Stop.status == status)
    return session.execute(stmt).scalar_one()


def get_active_routes(session: Session) -> Sequence[Route]:
    """
    Active routes with their ordered stops eager-loaded in one query.
    Used by app/routing/graph_builder.py to build the NetworkX graph —
    avoids one query per route + one per route_stop (N+1) while building it.
    """
    stmt = (
        select(Route)
        .where(Route.status == "active")
        .options(selectinload(Route.route_stops).selectinload(RouteStop.stop))
    )
    return session.execute(stmt).scalars().all()