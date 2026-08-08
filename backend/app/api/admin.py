"""Write endpoints for populating the network (data entry / ETL use).

Every route here is behind `require_admin_key` -- there's no per-user
auth in this project, just a shared secret for the small team doing
data entry. See app/core/security.py.
"""

from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_admin_key
from app.db.graph_loader import reload_graph
from app.db.session import get_db
from app.models import Route as RouteORM
from app.models import RouteStop as RouteStopORM
from app.models import Stop as StopORM

from .schemas import RouteCreate, RouteOut, RouteStopCreate, StopCreate, StopOut

router = APIRouter(dependencies=[Depends(require_admin_key)])


@router.post("/stops", response_model=StopOut, status_code=status.HTTP_201_CREATED)
def create_stop(payload: StopCreate, db: Session = Depends(get_db)) -> StopOut:
    row = StopORM(
        name=payload.name,
        name_normalized=payload.name.strip().lower(),
        is_interchange=payload.is_interchange,
        verified=payload.verified,
        geom=WKTElement(f"POINT({payload.lng} {payload.lat})", srid=4326),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    point = to_shape(row.geom)
    return StopOut(
        stop_id=row.stop_id,
        name=row.name,
        lat=point.y,
        lng=point.x,
        is_interchange=row.is_interchange,
        verified=row.verified,
    )


@router.post("/routes", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
def create_route(payload: RouteCreate, db: Session = Depends(get_db)) -> RouteOut:
    row = RouteORM(
        route_number=payload.route_number,
        route_name=payload.route_name,
        operator=payload.operator,
        tier=payload.tier,
        source=payload.source,
        verified=payload.verified,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return RouteOut.model_validate(row)


@router.post("/routes/{route_id}/stops", status_code=status.HTTP_201_CREATED)
def add_route_stop(route_id: int, payload: RouteStopCreate, db: Session = Depends(get_db)) -> dict:
    if db.get(RouteORM, route_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Route {route_id} not found.")
    if db.get(StopORM, payload.stop_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stop {payload.stop_id} not found.")

    row = RouteStopORM(route_id=route_id, stop_id=payload.stop_id, sequence_order=payload.sequence_order)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Route {route_id} already has a stop at sequence_order {payload.sequence_order}.",
        ) from exc

    return {"route_id": route_id, "stop_id": payload.stop_id, "sequence_order": payload.sequence_order}


@router.post("/graph/reload", status_code=status.HTTP_200_OK)
def reload_graph_cache(db: Session = Depends(get_db)) -> dict:
    """Rebuild the in-memory routing graph from the current DB state.

    Call this after adding stops/routes/route_stops -- the graph is
    cached (see app/db/graph_loader.py) so writes don't show up in
    /api/route/find until this runs.
    """
    graph = reload_graph(db)
    return {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()}
