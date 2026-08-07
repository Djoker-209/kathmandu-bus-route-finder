from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import queries
from app.routing.pathfinder import find_shortest_path, NoRouteFoundError
from app.schemas import RouteFinderResult, RouteLeg, StopOut

router = APIRouter(tags=["route-finder"])


@router.get("/route-finder", response_model=RouteFinderResult)
def find_route(
    origin: str = Query(..., description="Origin stop_id, e.g. S0198"),
    destination: str = Query(..., description="Destination stop_id, e.g. S0021"),
    db: Session = Depends(get_db),
):
    try:
        result = find_shortest_path(db, origin, destination)
    except NoRouteFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    legs: list[RouteLeg] = []
    for seg in result.segments:
        board_stop = queries.get_stop(db, seg.from_stop_id)
        alight_stop = queries.get_stop(db, seg.to_stop_id)
        legs.append(
            RouteLeg(
                route_id=seg.route_id or "TRANSFER",
                route_name="Transfer (walk)" if seg.is_transfer else seg.route_id,
                board_stop=StopOut.model_validate(board_stop),
                alight_stop=StopOut.model_validate(alight_stop),
                num_stops=1,
            )
        )

    return RouteFinderResult(
        origin_stop_id=origin,
        destination_stop_id=destination,
        total_cost=result.total_cost,
        transfer_count=result.transfer_count,
        legs=legs,
    )