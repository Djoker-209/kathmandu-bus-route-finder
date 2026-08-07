from sqlalchemy import Column, Text, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from .base import Base


class Operator(Base):
    """Bus/microbus/tempo operator. Text PK, matches operators table exactly."""

    __tablename__ = "operators"

    operator_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    service_type = Column(Text)
    contact_number = Column(Text)
    rating = Column(Numeric(2, 1))
    unverified_fields = Column(ARRAY(Text))

    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)",
            name="ck_operators_rating",
        ),
    )

    # routes where this operator is the FK on routes.operator_id
    routes = relationship("Route", back_populates="operator_ref")
    # M2M rows in route_operators
    route_links = relationship("RouteOperator", back_populates="operator")

    def __repr__(self) -> str:
        return f"<Operator {self.operator_id} {self.name!r}>"