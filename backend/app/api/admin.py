"""
api/admin.py

Write endpoints for populating the network (data entry / ETL use).

Every route here is behind `require_admin_key` -- there's no per-user
auth in this project, just a shared secret for the small team doing
data entry. See app/core/security.py and .env.example (ADMIN_API_KEY).

Rebuilt 2026-08-07 against the real production schema (text stop_id/
route_id, current column set) -- the previous version of this file
targeted the old int-ID `0001` scaffold schema and was never wired
into main.py. See app/routing/graph_builder.py for the graph this
data ultimately feeds.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_admin_key
from app.db.session import get_db
from app.models import Route as RouteORM
from app.models import RouteStop as RouteStopORM
from app.models import Stop as StopORM
from app.routing.graph_builder import invalidate_graph_cache
from app.schemas import (
    RouteCreate,
    RouteOut,
    RouteRecomputeOut,
    RouteStopCreate,
    StopCreate,
    StopOut,
)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/stops", response_model=StopOut, status_code=status.HTTP_201_CREATED)
def create_stop(payload: StopCreate, db: Session = Depends(get_db)) -> StopOut:
    """Create a stop. `geom` is populated automatically from lat/lng by the
    trg_stops_set_geom DB trigger -- never set it from here.
    """
    if db.get(StopORM, payload.stop_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stop '{payload.stop_id}' already exists.",
        )

    row = StopORM(
        stop_id=payload.stop_id,
        stop_name=payload.stop_name,
        lat=payload.lat,
        lng=payload.lng,
        aliases=payload.aliases,
        zone=payload.zone,
        district=payload.district,
        ward=payload.ward,
        landmark=payload.landmark,
        is_major_stop=payload.is_major_stop,
        is_interchange=payload.is_interchange,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create stop: {exc.orig}",
        ) from exc
    db.refresh(row)
    return StopOut.model_validate(row)


@router.post("/routes", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(payload: RouteCreate, db: Session = Depends(get_db)) -> RouteOut:
    """Create a route row. total_stops starts at 0 -- add stops via
    POST /admin/routes/{route_id}/stops, then call
    POST /admin/routes/{route_id}/recompute to fill in the real
    start_stop_id/end_stop_id/total_stops from what was actually added
    (mirrors the recomputation step in data/scripts/clean_data.py).
    """
    if db.get(RouteORM, payload.route_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Route '{payload.route_id}' already exists.",
        )
    if db.get(StopORM, payload.start_stop_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"start_stop_id '{payload.start_stop_id}' not found.",
        )
    if db.get(StopORM, payload.end_stop_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"end_stop_id '{payload.end_stop_id}' not found.",
        )

    row = RouteORM(
        route_id=payload.route_id,
        route_name=payload.route_name,
        short_name=payload.short_name,
        vehicle_type=payload.vehicle_type,
        start_stop_id=payload.start_stop_id,
        end_stop_id=payload.end_stop_id,
        total_stops=0,
        operator_id=payload.operator_id,
        is_bidirectional=payload.is_bidirectional,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create route: {exc.orig}",
        ) from exc
    db.refresh(row)
    return RouteOut.model_validate(row)


@router.post("/routes/{route_id}/stops", status_code=status.HTTP_201_CREATED)
def add_route_stop(route_id: str, payload: RouteStopCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(RouteORM, route_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route '{route_id}' not found.")
    if db.get(StopORM, payload.stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stop '{payload.stop_id}' not found.")

    row = RouteStopORM(route_id=route_id, stop_id=payload.stop_id, sequence_no=payload.sequence_no)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Route '{route_id}' already has a stop at sequence_no {payload.sequence_no}.",
        ) from exc

    return {"route_id": route_id, "stop_id": payload.stop_id, "sequence_no": payload.sequence_no}


@router.post("/routes/{route_id}/recompute", response_model=RouteRecomputeOut)
def recompute_route_metadata(route_id: str, db: Session = Depends(get_db)) -> RouteRecomputeOut:
    """Recompute start_stop_id / end_stop_id / total_stops from the route's
    actual route_stops rows (min/max sequence_no). Same idea as the
    recomputation step in data/scripts/clean_data.py's cleaning pipeline --
    these three columns are denormalized for read performance, so they have
    to be kept in sync by hand after writes instead of via a DB constraint.
    """
    route = db.get(RouteORM, route_id)
    if route is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route '{route_id}' not found.")

    stops = (
        db.query(RouteStopORM)
        .filter(RouteStopORM.route_id == route_id)
        .order_by(RouteStopORM.sequence_no)
        .all()
    )
    if not stops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Route '{route_id}' has no route_stops yet -- add some first.",
        )

    route.start_stop_id = stops[0].stop_id
    route.end_stop_id = stops[-1].stop_id
    route.total_stops = len(stops)
    db.commit()
    db.refresh(route)

    return RouteRecomputeOut(
        route_id=route.route_id,
        start_stop_id=route.start_stop_id,
        end_stop_id=route.end_stop_id,
        total_stops=route.total_stops,
    )


@router.post("/graph/reload", status_code=status.HTTP_200_OK)
def reload_graph_cache() -> dict:
    """Invalidate the cached routing graph (app/routing/graph_builder.py) so
    the next /route-finder call rebuilds it from the current DB state.
    Call this after adding stops/routes/route_stops -- writes don't show up
    in /route-finder until the cache is invalidated (or it expires/rebuilds
    on its own trigger, if one is ever added).
    """
    invalidate_graph_cache()
    return {"status": "graph cache invalidated -- will rebuild on next /route-finder call"}