"""ORM model for `route_stops`, the ordered join table between routes
and stops. Kept in sync with migrations/versions/0002_replace_with_full_schema.py.
"""
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base


class RouteStop(Base):
    __tablename__ = "route_stops"

    route_id = Column(
        Text, ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False
    )
    stop_id = Column(
        Text, ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False
    )
    sequence_no = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("route_id", "sequence_no"),
        CheckConstraint("sequence_no > 0", name="ck_route_stops_sequence_no"),
        Index("idx_route_stops_route_id", "route_id"),
        Index("idx_route_stops_stop_id", "stop_id"),
    )

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RouteStop route={self.route_id} stop={self.stop_id} seq={self.sequence_no}>"