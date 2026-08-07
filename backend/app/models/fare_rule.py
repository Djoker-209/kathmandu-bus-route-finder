from sqlalchemy import CheckConstraint, Column, FetchedValue, Numeric, Text
from sqlalchemy.dialects.postgresql import NUMRANGE

from .base import Base


class FareRule(Base):
    """Distance-banded fare lookup, independent of routes/stops. A route's
    fare is found by matching its approx_distance_km into whichever band
    contains it: min_distance_km <= distance < max_distance_km.
    """

    __tablename__ = "fare_rules"

    fare_id = Column(Text, primary_key=True)
    min_distance_km = Column(Numeric(6, 2), nullable=False)
    max_distance_km = Column(Numeric(6, 2), nullable=False)
    fare_npr_min = Column(Numeric(7, 2), nullable=False)
    fare_npr_max = Column(Numeric(7, 2), nullable=False)
    student_discount_pct = Column(Numeric(5, 2))
    verification_note = Column(Text)

    # GENERATED ALWAYS AS (numrange(min_distance_km, max_distance_km, '[)')) STORED
    # in the DB (see 0002 migration). server_default=FetchedValue() tells
    # SQLAlchemy this is populated by Postgres, not the app — never set it
    # in code, and never rely on the in-memory value until the row is refreshed.
    distance_range = Column(NUMRANGE, server_default=FetchedValue(), nullable=True)

    __table_args__ = (
        CheckConstraint("min_distance_km >= 0", name="ck_fare_rules_min_distance"),
        CheckConstraint("max_distance_km > min_distance_km", name="ck_fare_rules_max_gt_min"),
        CheckConstraint("fare_npr_min >= 0", name="ck_fare_rules_fare_min"),
        CheckConstraint("fare_npr_max >= fare_npr_min", name="ck_fare_rules_fare_max_gte_min"),
        CheckConstraint(
            "student_discount_pct IS NULL OR (student_discount_pct BETWEEN 0 AND 100)",
            name="ck_fare_rules_discount_pct",
        ),
        # The fare_rules_distance_range_excl GiST EXCLUDE constraint (no two
        # bands may overlap) is DB-only — created by the 0002 migration,
        # not representable in the ORM layer.
    )

    def __repr__(self) -> str:
        return f"<FareRule {self.fare_id} [{self.min_distance_km},{self.max_distance_km})>"