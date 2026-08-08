from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    Time,
    TIMESTAMP,
    text,
)
from sqlalchemy.orm import relationship

from .base import Base


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Text, primary_key=True)
    route_name = Column(Text, nullable=False)
    short_name = Column(Text)
    vehicle_type = Column(Text, nullable=False)
    route_type = Column(Text)

    operator = Column(Text)  # free-text operator name as originally recorded
    operator_id = Column(
        Text, ForeignKey("operators.operator_id", ondelete="SET NULL")
    )
    operator_id_raw = Column(Text)

    start_stop_id = Column(
        Text, ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False
    )
    end_stop_id = Column(
        Text, ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False
    )

    total_stops = Column(Integer, nullable=False)
    approx_distance_km = Column(Numeric(6, 2))
    approx_distance_km_original = Column(Numeric(6, 2))
    haversine_distance_km = Column(Numeric(6, 3))
    max_consecutive_stop_jump_km = Column(Numeric(6, 3))
    distance_flagged_for_recompute = Column(
        Boolean, nullable=False, server_default=text("false")
    )
    estimated_duration_min = Column(Numeric(6, 1))
    service_start_time = Column(Time)
    service_end_time = Column(Time)
    frequency_min = Column(Integer)
    fare_type = Column(Text)
    has_ac = Column(Boolean, nullable=False, server_default=text("false"))
    is_express = Column(Boolean, nullable=False, server_default=text("false"))
    is_multi_operator = Column(Boolean, nullable=False, server_default=text("false"))
    is_bidirectional = Column(Boolean, nullable=False, server_default=text("false"))
    status = Column(Text, nullable=False, server_default="active")
    status_original = Column(Text)
    status_corrected_for_return_leg = Column(
        Boolean, nullable=False, server_default=text("false")
    )
    return_leg_verified = Column(Boolean, nullable=False, server_default=text("false"))
    notes = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint("total_stops >= 0", name="ck_routes_total_stops"),
        Index("idx_routes_end_stop", "end_stop_id"),
        Index("idx_routes_operator_id", "operator_id"),
        Index("idx_routes_start_stop", "start_stop_id"),
        Index("idx_routes_status", "status"),
        Index("idx_routes_vehicle_type", "vehicle_type"),
    )

    operator_ref = relationship("Operator", back_populates="routes")
    start_stop = relationship(
        "Stop", foreign_keys=[start_stop_id], back_populates="routes_starting_here"
    )
    end_stop = relationship(
        "Stop", foreign_keys=[end_stop_id], back_populates="routes_ending_here"
    )
    route_stops = relationship(
        "RouteStop",
        back_populates="route",
        order_by="RouteStop.sequence_no",
        cascade="all, delete-orphan",
    )
    route_operators = relationship(
        "RouteOperator", back_populates="route", cascade="all, delete-orphan"
    )
    return_leg_priority = relationship(
        "RouteReturnLegPriority",
        back_populates="route",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Route {self.route_id} {self.route_name!r}>"