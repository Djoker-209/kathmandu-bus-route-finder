from sqlalchemy import Boolean, Column, ForeignKey, PrimaryKeyConstraint, Text, text
from sqlalchemy.orm import relationship

from .base import Base


class RouteOperator(Base):
    """Many-to-many: a route can have multiple operators, exactly one primary."""

    __tablename__ = "route_operators"

    route_id = Column(Text, ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False)
    operator_id = Column(
        Text, ForeignKey("operators.operator_id", ondelete="RESTRICT"), nullable=False
    )
    is_primary = Column(Boolean, nullable=False, server_default=text("false"))

    __table_args__ = (PrimaryKeyConstraint("route_id", "operator_id"),)

    route = relationship("Route", back_populates="route_operators")
    operator = relationship("Operator", back_populates="route_links")

    def __repr__(self) -> str:
        return f"<RouteOperator route={self.route_id} operator={self.operator_id} primary={self.is_primary}>"