"""ORM model for `route_stops`, the ordered join table between routes
and stops. Kept in sync with migrations/versions/0001_initial_schema.py.
"""

from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RouteStop(Base):
    __tablename__ = "route_stops"
    __table_args__ = (PrimaryKeyConstraint("route_id", "sequence_order"),)

    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False)
    stop_id: Mapped[int] = mapped_column(Integer, ForeignKey("stops.stop_id", ondelete="CASCADE"), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RouteStop route={self.route_id} stop={self.stop_id} seq={self.sequence_order}>"
