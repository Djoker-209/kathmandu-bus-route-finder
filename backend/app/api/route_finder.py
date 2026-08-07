"""
api/route_finder.py

GET /route-finder — shortest path (direct or single/multi-transfer)
between two stop_ids, built on the NetworkX graph in app/routing/.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import queries
from app.db.session import get_db
from app.routing.pathfinder import NoRouteFoundError, find_shortest_path
from app.schemas import RouteFinderResponse, RouteFinderSegmentOut

router = APIRouter(tags=["route-finder"])


@router.get("/route-finder", response_model=RouteFinderResponse)
def route_finder(
    origin_stop_id: str = Query(..., description="stop_id of the origin, e.g. S0198"),
    destination_stop_id: str = Query(..., description="stop_id of the destination, e.g. S0021"),
    db: Session = Depends(get_db),
):
    try:
        result = find_shortest_path(db, origin_stop_id, destination_stop_id)
    except NoRouteFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    stops_by_id = {sid: queries.get_stop(db, sid) for sid in result.stop_sequence}

    segments_out = [
        RouteFinderSegmentOut(
            route_id=seg.route_id,
            is_transfer=seg.is_transfer,
            distance_m=round(seg.distance_m, 1),
            from_stop=stops_by_id[seg.from_stop_id],
            to_stop=stops_by_id[seg.to_stop_id],
        )
        for seg in result.segments
    ]

    return RouteFinderResponse(
        origin_stop_id=origin_stop_id,
        destination_stop_id=destination_stop_id,
        total_distance_m=round(result.total_distance_m, 1),
        transfer_count=result.transfer_count,
        stop_sequence=result.stop_sequence,
        segments=segments_out,
    )