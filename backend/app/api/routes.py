from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session


from app.db.session import get_db
from app.db import queries
from app.schemas import RouteOut, RouteStopOut

router = APIRouter(prefix="/routes", tags=["routes"])


@router.get("/{route_id}", response_model=RouteOut)
def read_route(route_id: str, db: Session = Depends(get_db)):
    route = queries.get_route(db, route_id)
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return route


@router.get("/{route_id}/stops", response_model=list[RouteStopOut])
def read_route_stops(route_id: str, db: Session = Depends(get_db)):
    if queries.get_route(db, route_id) is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return queries.get_route_stops(db, route_id)