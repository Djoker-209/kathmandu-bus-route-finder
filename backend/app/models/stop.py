from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Float,
    Integer,
    Text,
    TIMESTAMP,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from .base import Base


class Stop(Base):
    """A physical bus stop. stop_id is TEXT (e.g. 'S0198'), not an integer."""

    __tablename__ = "stops"

    stop_id = Column(Text, primary_key=True)
    stop_name = Column(Text, nullable=False)
    aliases = Column(Text)

    lat = Column(Float(53), nullable=False)
    lng = Column(Float(53), nullable=False)

    # Auto-populated by trg_stops_set_geom on insert/update of lat/lng —
    # never set this directly from the app layer, write lat/lng instead.
    geom = Column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False),
        nullable=False,
    )

    zone = Column(Text)
    district = Column(Text)
    ward = Column(Integer)
    is_major_stop = Column(Boolean, nullable=False, server_default=text("false"))
    landmark = Column(Text)
    has_shelter = Column(Boolean, nullable=False, server_default=text("false"))
    has_ticket_counter = Column(Boolean, nullable=False, server_default=text("false"))
    is_interchange = Column(Boolean, nullable=False, server_default=text("false"))
    wheelchair_access = Column(Boolean, nullable=False, server_default=text("false"))
    audio_support = Column(Boolean, nullable=False, server_default=text("false"))
    status = Column(Text, nullable=False, server_default="active")
    unverified_fields = Column(ARRAY(Text))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    geo_out_of_bounds = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (
        CheckConstraint("lat BETWEEN -90 AND 90", name="ck_stops_lat"),
        CheckConstraint("lng BETWEEN -180 AND 180", name="ck_stops_lng"),
    )

    route_stops = relationship("RouteStop", back_populates="stop")
    routes_starting_here = relationship(
        "Route", foreign_keys="Route.start_stop_id", back_populates="start_stop"
    )
    routes_ending_here = relationship(
        "Route", foreign_keys="Route.end_stop_id", back_populates="end_stop"
    )

    def __repr__(self) -> str:
        return f"<Stop {self.stop_id} {self.stop_name!r}>"