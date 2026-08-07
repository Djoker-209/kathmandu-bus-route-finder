"""
api/stops.py

GET /stops         — paginated stop listing
GET /stops/nearby   — nearest stops to a lat/lng, within a radius
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import queries
from app.db.session import get_db
from app.schemas import StopListOut, StopOut

router = APIRouter(tags=["stops"])
settings = get_settings()


@router.get("/stops/nearby", response_model=list[StopOut])
def stops_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of the search point"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of the search point"),
    radius_m: int = Query(
        settings.DEFAULT_NEARBY_RADIUS_M, gt=0, le=5000, description="Search radius in meters"
    ),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Registered before /stops so FastAPI doesn't try to match 'nearby' as a path param."""
    return queries.nearest_stops(db, lat=lat, lng=lng, radius_m=radius_m, limit=limit)


@router.get("/stops", response_model=StopListOut)
def list_stops(
    offset: int = Query(0, ge=0),
    limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    district: str | None = Query(None, description="Optional district filter"),
    db: Session = Depends(get_db),
):
    items = queries.list_stops(db, district=district, limit=limit, offset=offset)
    total = queries.count_stops(db)
    return StopListOut(total=total, limit=limit, offset=offset, items=items)