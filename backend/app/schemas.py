from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    # Count of merged ride segments (hops) on this leg, NOT physical stops.
    # len(stops) == num_ride_segments + 1 always; use len(stops) for the
    # physical stop count.
    num_ride_segments: int
    stops: list[StopOut] = []  # every physical stop on this leg, in order, board→alight inclusive
    road_geometry: Optional[dict] = None


class RouteFinderResult(BaseModel):
    origin_stop_id: str
    destination_stop_id: str
    total_cost: float
    transfer_count: int
    legs: list[RouteLeg]


# ---------------------------------------------------------------------------
# Admin write endpoints (app/api/admin.py) -- request bodies for creating
# stops/routes/route_stops. Server-generated fields (stop_id, route_id,
# geom, timestamps) are intentionally absent here.
# ---------------------------------------------------------------------------

class StopCreate(BaseModel):
    stop_name: str = Field(min_length=1, max_length=150)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    aliases: str | None = None
    zone: str | None = None
    district: str | None = None
    ward: int | None = None
    landmark: str | None = None
    is_major_stop: bool = False
    has_shelter: bool = False
    has_ticket_counter: bool = False
    is_interchange: bool = False
    wheelchair_access: bool = False
    audio_support: bool = False

    @field_validator("stop_name")
    @classmethod
    def strip_stop_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("stop_name must not be blank")
        return v

class RouteStatusUpdate(BaseModel):
    status: Literal["active", "pending_release"]


class RouteCreate(BaseModel):
    route_name: str = Field(min_length=1, max_length=150)
    short_name: str | None = Field(default=None, max_length=50)
    vehicle_type: str = Field(min_length=1, max_length=50)
    route_type: str | None = Field(default=None, max_length=50)
    operator: str | None = Field(default=None, max_length=100)
    operator_id: str | None = None
    start_stop_id: str
    end_stop_id: str
    total_stops: int = Field(ge=0)
    is_bidirectional: bool = False
    has_ac: bool = False
    is_express: bool = False


class RouteStopCreate(BaseModel):
    stop_id: str
    sequence_no: int = Field(ge=1)


# ---------------------------------------------------------------------------
# Admin login (AdminUser)
# ---------------------------------------------------------------------------

class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
