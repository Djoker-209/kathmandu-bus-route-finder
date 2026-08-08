"""Write endpoints for populating the network (data entry / ETL use).

Every route here is behind `require_admin_key` -- there's no per-user
auth in this project, just a shared secret for the small team doing
data entry. See app/core/security.py.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_admin_key
from app.db.id_generator import next_route_id, next_stop_id
from app.db.session import get_db
from app.routing.graph_builder import get_cached_graph
from app.models import Route as RouteORM
from app.models import RouteStop as RouteStopORM
from app.models import Stop as StopORM

from app.schemas import RouteCreate, RouteOut, RouteStopCreate, StopCreate, StopOut

router = APIRouter(dependencies=[Depends(require_admin_key)])


@router.post("/stops", response_model=StopOut, status_code=status.HTTP_201_CREATED)
def create_stop(payload: StopCreate, db: Session = Depends(get_db)) -> StopOut:
    row = StopORM(
        stop_id=next_stop_id(db),
        stop_name=payload.stop_name,
        aliases=payload.aliases,
        lat=payload.lat,
        lng=payload.lng,
        zone=payload.zone,
        district=payload.district,
        ward=payload.ward,
        landmark=payload.landmark,
        is_major_stop=payload.is_major_stop,
        has_shelter=payload.has_shelter,
        has_ticket_counter=payload.has_ticket_counter,
        is_interchange=payload.is_interchange,
        wheelchair_access=payload.wheelchair_access,
        audio_support=payload.audio_support,
    )
    # geom is populated by the trg_stops_set_geom trigger from lat/lng --
    # do not set it here.
    db.add(row)
    db.commit()
    db.refresh(row)
    return StopOut.model_validate(row)


@router.post("/routes", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(payload: RouteCreate, db: Session = Depends(get_db)) -> RouteOut:
    if db.get(StopORM, payload.start_stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stop {payload.start_stop_id} not found.")
    if db.get(StopORM, payload.end_stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stop {payload.end_stop_id} not found.")

    row = RouteORM(
        route_id=next_route_id(db),
        route_name=payload.route_name,
        short_name=payload.short_name,
        vehicle_type=payload.vehicle_type,
        route_type=payload.route_type,
        operator=payload.operator,
        operator_id=payload.operator_id,
        start_stop_id=payload.start_stop_id,
        end_stop_id=payload.end_stop_id,
        total_stops=payload.total_stops,
        is_bidirectional=payload.is_bidirectional,
        has_ac=payload.has_ac,
        is_express=payload.is_express,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return RouteOut.model_validate(row)


@router.post("/routes/{route_id}/stops", status_code=status.HTTP_201_CREATED)
def add_route_stop(route_id: str, payload: RouteStopCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(RouteORM, route_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route {route_id} not found.")
    if db.get(StopORM, payload.stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stop {payload.stop_id} not found.")

    row = RouteStopORM(route_id=route_id, stop_id=payload.stop_id, sequence_no=payload.sequence_no)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Route {route_id} already has a stop at sequence_no {payload.sequence_no}.",
        ) from exc

    return {"route_id": route_id, "stop_id": payload.stop_id, "sequence_no": payload.sequence_no}


@router.post("/graph/reload", status_code=status.HTTP_200_OK)
def reload_graph_cache(db: Session = Depends(get_db)) -> dict:
    """Rebuild the in-memory routing graph from the current DB state.

    Call this after adding stops/routes/route_stops -- the graph is
    cached (see app/routing/graph_builder.py) so writes don't show up in
    /api/route/find until this runs.
    """
    graph = get_cached_graph(db, refresh=True)
    return {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()}
