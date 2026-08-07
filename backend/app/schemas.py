from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stop_id: str
    stop_name: str
    lat: float
    lng: float
    zone: Optional[str] = None
    district: Optional[str] = None
    is_major_stop: bool
    is_interchange: bool
    status: str


class StopWithDistance(StopOut):
    distance_m: Optional[float] = None


class OperatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operator_id: str
    name: str
    service_type: Optional[str] = None


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: str
    route_name: str
    short_name: Optional[str] = None
    vehicle_type: str
    start_stop_id: str
    end_stop_id: str
    total_stops: int
    approx_distance_km: Optional[float] = None
    status: str
    # Route.operator (the column) is the free-text name as originally
    # recorded in the source data; the *linked* operator row lives on the
    # relationship Route.operator_ref, so pull from there instead.
    operator: Optional[OperatorOut] = Field(default=None, validation_alias="operator_ref")


class RouteStopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_no: int
    stop: StopOut

class StopListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[StopOut]

class RouteLeg(BaseModel):
    """One uninterrupted ride on a single route, part of a route-finder result."""
    route_id: str
    route_name: str
    board_stop: StopOut
    alight_stop: StopOut
    num_stops: int
    road_geometry: Optional[dict] = None


class RouteFinderResult(BaseModel):
    origin_stop_id: str
    destination_stop_id: str
    total_cost: float
    transfer_count: int
    legs: list[RouteLeg]