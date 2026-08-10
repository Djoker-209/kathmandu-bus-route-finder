from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.routing.osrm_client import get_route_geometry, OSRMError
from app.routing.graph_builder import haversine_distance_m
from app.db.session import get_db
from app.db import queries
from app.routing.pathfinder import find_shortest_path, NoRouteFoundError
from app.schemas import RouteFinderResult, RouteLeg, StopOut

router = APIRouter(tags=["route-finder"])

# Stops closer together than this are treated as effectively the same
# point for OSRM waypoint purposes. Forcing OSRM through every single
# stored stop — including ones only a few dozen metres apart — can push
# it into small loops on one-way streets just to legally hit each
# waypoint in order, which shows up as visible zigzagging on the map.
# Thinning keeps the route recognisable while giving OSRM room to pick
# a sane path between waypoints that are meaningfully far apart.
MIN_WAYPOINT_SPACING_M = 80


def _thin_waypoints(stops: list[StopOut]) -> list[tuple[float, float]]:
    if len(stops) < 2:
        return [(s.lat, s.lng) for s in stops]

    thinned = [(stops[0].lat, stops[0].lng)]
    for stop in stops[1:-1]:
        last_lat, last_lng = thinned[-1]
        if haversine_distance_m(last_lat, last_lng, stop.lat, stop.lng) >= MIN_WAYPOINT_SPACING_M:
            thinned.append((stop.lat, stop.lng))
    # Always keep the true final stop, even if it's close to the last
    # kept waypoint — it's the actual alight point, not optional.
    last = stops[-1]
    if thinned[-1] != (last.lat, last.lng):
        thinned.append((last.lat, last.lng))
    return thinned


def _attach_road_geometry(legs: list[RouteLeg]) -> None:
    for leg in legs:
        if leg.route_id == "TRANSFER":
            continue

        coords = _thin_waypoints(leg.stops)
        if len(coords) < 2:
            continue

        try:
            leg.road_geometry = get_route_geometry(coords)
        except OSRMError:
            pass


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
        seg_route_id = seg.route_id or "TRANSFER"
        to_stop = StopOut.model_validate(queries.get_stop(db, seg.to_stop_id))
        if legs and legs[-1].route_id == seg_route_id:
            legs[-1].alight_stop = to_stop
            legs[-1].num_stops += 1
            legs[-1].stops.append(to_stop)
        else:
            from_stop = StopOut.model_validate(queries.get_stop(db, seg.from_stop_id))
            legs.append(
                RouteLeg(
                    route_id=seg_route_id,
                    route_name="Transfer (walk)" if seg.is_transfer else seg.route_id,
                    board_stop=from_stop,
                    alight_stop=to_stop,
                    num_stops=1,
                    stops=[from_stop, to_stop],
                )
            )

    _attach_road_geometry(legs)

    return RouteFinderResult(
        origin_stop_id=origin,
        destination_stop_id=destination,
        total_cost=result.total_distance_m,
        transfer_count=result.transfer_count,
        legs=legs,
    )