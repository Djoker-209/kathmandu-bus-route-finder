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

class StopListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[StopOut]
    
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
    operator: Optional[OperatorOut] = Field(default=None, validation_alias="operator_ref")


class RouteStopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_no: int
    stop: StopOut


class RouteLeg(BaseModel):
    route_id: str
    route_name: str
    board_stop: StopOut
    alight_stop: StopOut
    num_stops: int


class RouteFinderResult(BaseModel):
    origin_stop_id: str
    destination_stop_id: str
    total_cost: float
    transfer_count: int
    legs: list[RouteLeg]


# ---------------------------------------------------------------------------
# Admin write endpoints (app/api/admin.py) -- request bodies only.
# ---------------------------------------------------------------------------

class StopCreate(BaseModel):
    stop_id: str = Field(min_length=1, max_length=20)
    stop_name: str = Field(min_length=1, max_length=150)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    aliases: Optional[str] = None
    zone: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[int] = None
    landmark: Optional[str] = None
    is_major_stop: bool = False
    is_interchange: bool = False


class RouteCreate(BaseModel):
    route_id: str = Field(min_length=1, max_length=20)
    route_name: str = Field(min_length=1, max_length=150)
    vehicle_type: str = Field(min_length=1, max_length=20)
    start_stop_id: str
    end_stop_id: str
    short_name: Optional[str] = None
    operator_id: Optional[str] = None
    is_bidirectional: bool = False


class RouteStopCreate(BaseModel):
    stop_id: str
    sequence_no: int = Field(ge=1)


class RouteRecomputeOut(BaseModel):
    route_id: str
    start_stop_id: str
    end_stop_id: str
    total_stops: int