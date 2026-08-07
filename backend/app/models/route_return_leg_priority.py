from sqlalchemy import Column, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship

from .base import Base


class RouteReturnLegPriority(Base):
    """Auxiliary QA/tracking table — routes flagged for return-leg
    verification. Not a relational entity in its own right; columns
    duplicate routes.* at the time the route was flagged. Kept 1:1 with
    routes.route_id.
    """

    __tablename__ = "route_return_leg_priority"

    route_id = Column(
        Text, ForeignKey("routes.route_id", ondelete="CASCADE"), primary_key=True
    )
    route_name = Column(Text)
    vehicle_type = Column(Text)
    operator = Column(Text)
    total_stops = Column(Integer)
    approx_distance_km = Column(Numeric(6, 2))
    status = Column(Text)

    route = relationship("Route", back_populates="return_leg_priority")

    def __repr__(self) -> str:
        return f"<RouteReturnLegPriority route={self.route_id}>"