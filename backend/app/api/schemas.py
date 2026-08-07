"""Pydantic schemas for request/response bodies.

Kept separate from the ORM models (app/models) on purpose: the DB
shape (geom column, server-managed timestamps, etc.) shouldn't leak
into the API contract, and the API contract shouldn't constrain how
the DB stores things.
"""

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Stops
# ---------------------------------------------------------------------------

class StopOut(BaseModel):
    stop_id: int
    name: str
    lat: float
    lng: float
    is_interchange: bool
    verified: bool

    model_config = {"from_attributes": True}


class StopCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    is_interchange: bool = False
    verified: bool = False

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class RouteOut(BaseModel):
    route_id: int
    route_number: str
    route_name: str
    operator: str | None = None
    tier: int | None = None
    verified: bool

    model_config = {"from_attributes": True}


class RouteCreate(BaseModel):
    route_number: str = Field(min_length=1, max_length=20)
    route_name: str = Field(min_length=1, max_length=150)
    operator: str | None = Field(default=None, max_length=100)
    tier: int | None = Field(default=None, ge=1, le=3)
    source: str | None = Field(default=None, max_length=50)
    verified: bool = False


class RouteStopCreate(BaseModel):
    stop_id: int
    sequence_order: int = Field(ge=1)


# ---------------------------------------------------------------------------
# Route search (the actual "find me a bus" endpoint)
# ---------------------------------------------------------------------------

class RouteLeg(BaseModel):
    """One uninterrupted ride on a single bus route, or a walking
    transfer between two nearby stops on different routes.
    """
    kind: str  # "ride" | "transfer"
    route_id: int | None = None
    route_number: str | None = None
    route_name: str | None = None
    stops: list[StopOut]
    distance_m: float


class RouteSearchResult(BaseModel):
    origin: StopOut
    destination: StopOut
    is_transfer: bool
    transfer_stop: StopOut | None = None
    total_distance_m: float
    legs: list[RouteLeg]
    path: list[StopOut]
