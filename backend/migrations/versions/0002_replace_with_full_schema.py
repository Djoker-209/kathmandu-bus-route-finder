"""Replace scaffold schema with full production schema (operators, stops,
routes, route_stops, route_operators, route_return_leg_priority, fare_rules)

Revision ID: 0002_replace_with_full_schema
Revises: 0001_initial_schema
Create Date: 2026-08-06

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision = "0002_replace_with_full_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # -------------------------
    # Drop 0001 scaffold tables (confirmed empty, nothing in backend/app
    # queries route_number/tier/name_normalized yet)
    # -------------------------
    op.drop_table("route_stops")
    op.drop_table("routes")
    op.drop_table("stops")

    # -------------------------
    # operators
    # -------------------------
    op.create_table(
        "operators",
        sa.Column("operator_id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("service_type", sa.Text),
        sa.Column("contact_number", sa.Text),
        sa.Column("rating", sa.Numeric(2, 1)),
        sa.Column("unverified_fields", postgresql.ARRAY(sa.Text)),
        sa.CheckConstraint(
            "rating IS NULL OR (rating >= 0 AND rating <= 5)",
            name="ck_operators_rating",
        ),
    )

    # -------------------------
    # stops
    # -------------------------
    op.create_table(
        "stops",
        sa.Column("stop_id", sa.Text, primary_key=True),
        sa.Column("stop_name", sa.Text, nullable=False),
        sa.Column("aliases", sa.Text),
        sa.Column("lat", sa.Float(53), nullable=False),
        sa.Column("lng", sa.Float(53), nullable=False),
        sa.Column(
            "geom",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("zone", sa.Text),
        sa.Column("district", sa.Text),
        sa.Column("ward", sa.Integer),
        sa.Column("is_major_stop", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("landmark", sa.Text),
        sa.Column("has_shelter", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("has_ticket_counter", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_interchange", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("wheelchair_access", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("audio_support", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("unverified_fields", postgresql.ARRAY(sa.Text)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("geo_out_of_bounds", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.CheckConstraint("lat BETWEEN -90 AND 90", name="ck_stops_lat"),
        sa.CheckConstraint("lng BETWEEN -180 AND 180", name="ck_stops_lng"),
    )

    op.create_index("idx_stops_geom", "stops", ["geom"], postgresql_using="gist")
    op.create_index("idx_stops_district", "stops", ["district"])
    op.create_index("idx_stops_status", "stops", ["status"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION stops_set_geom() RETURNS trigger AS $$
        BEGIN
            NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326)::geography;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_stops_set_geom
            BEFORE INSERT OR UPDATE OF lat, lng ON stops
            FOR EACH ROW EXECUTE FUNCTION stops_set_geom();
        """
    )

    # -------------------------
    # routes
    # -------------------------
    op.create_table(
        "routes",
        sa.Column("route_id", sa.Text, primary_key=True),
        sa.Column("route_name", sa.Text, nullable=False),
        sa.Column("short_name", sa.Text),
        sa.Column("vehicle_type", sa.Text, nullable=False),
        sa.Column("route_type", sa.Text),
        sa.Column("operator", sa.Text),
        sa.Column("operator_id", sa.Text, sa.ForeignKey("operators.operator_id", ondelete="SET NULL")),
        sa.Column("operator_id_raw", sa.Text),
        sa.Column("start_stop_id", sa.Text, sa.ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("end_stop_id", sa.Text, sa.ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("total_stops", sa.Integer, nullable=False),
        sa.Column("approx_distance_km", sa.Numeric(6, 2)),
        sa.Column("approx_distance_km_original", sa.Numeric(6, 2)),
        sa.Column("haversine_distance_km", sa.Numeric(6, 3)),
        sa.Column("max_consecutive_stop_jump_km", sa.Numeric(6, 3)),
        sa.Column("distance_flagged_for_recompute", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("estimated_duration_min", sa.Numeric(6, 1)),
        sa.Column("service_start_time", sa.Time),
        sa.Column("service_end_time", sa.Time),
        sa.Column("frequency_min", sa.Integer),
        sa.Column("fare_type", sa.Text),
        sa.Column("has_ac", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_express", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_multi_operator", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_bidirectional", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("status_original", sa.Text),
        sa.Column("status_corrected_for_return_leg", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("return_leg_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("total_stops >= 0", name="ck_routes_total_stops"),
    )

    op.create_index("idx_routes_operator_id", "routes", ["operator_id"])
    op.create_index("idx_routes_status", "routes", ["status"])
    op.create_index("idx_routes_vehicle_type", "routes", ["vehicle_type"])
    op.create_index("idx_routes_start_stop", "routes", ["start_stop_id"])
    op.create_index("idx_routes_end_stop", "routes", ["end_stop_id"])

    # -------------------------
    # route_stops
    # -------------------------
    op.create_table(
        "route_stops",
        sa.Column("route_id", sa.Text, sa.ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False),
        sa.Column("stop_id", sa.Text, sa.ForeignKey("stops.stop_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence_no", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("route_id", "sequence_no"),
        sa.CheckConstraint("sequence_no > 0", name="ck_route_stops_sequence_no"),
    )

    op.create_index("idx_route_stops_stop_id", "route_stops", ["stop_id"])
    op.create_index("idx_route_stops_route_id", "route_stops", ["route_id"])

    # -------------------------
    # route_operators
    # -------------------------
    op.create_table(
        "route_operators",
        sa.Column("route_id", sa.Text, sa.ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False),
        sa.Column("operator_id", sa.Text, sa.ForeignKey("operators.operator_id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("route_id", "operator_id"),
    )

    op.create_index("idx_route_operators_operator_id", "route_operators", ["operator_id"])
    op.create_index(
        "uq_route_operators_primary",
        "route_operators",
        ["route_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )

    # -------------------------
    # route_return_leg_priority
    # -------------------------
    op.create_table(
        "route_return_leg_priority",
        sa.Column("route_id", sa.Text, sa.ForeignKey("routes.route_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("route_name", sa.Text),
        sa.Column("vehicle_type", sa.Text),
        sa.Column("operator", sa.Text),
        sa.Column("total_stops", sa.Integer),
        sa.Column("approx_distance_km", sa.Numeric(6, 2)),
        sa.Column("status", sa.Text),
    )

    # -------------------------
    # fare_rules
    # -------------------------
    op.create_table(
        "fare_rules",
        sa.Column("fare_id", sa.Text, primary_key=True),
        sa.Column("min_distance_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_distance_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("fare_npr_min", sa.Numeric(7, 2), nullable=False),
        sa.Column("fare_npr_max", sa.Numeric(7, 2), nullable=False),
        sa.Column("student_discount_pct", sa.Numeric(5, 2)),
        sa.Column("verification_note", sa.Text),
        sa.Column(
            "distance_range",
            postgresql.NUMRANGE,
            sa.Computed(
                "numrange(min_distance_km, max_distance_km, '[)')",
                persisted=True,
            ),
        ),
        sa.CheckConstraint("min_distance_km >= 0", name="ck_fare_rules_min_distance"),
        sa.CheckConstraint("max_distance_km > min_distance_km", name="ck_fare_rules_max_gt_min"),
        sa.CheckConstraint("fare_npr_min >= 0", name="ck_fare_rules_fare_min"),
        sa.CheckConstraint("fare_npr_max >= fare_npr_min", name="ck_fare_rules_fare_max_gte_min"),
        sa.CheckConstraint(
            "student_discount_pct IS NULL OR (student_discount_pct BETWEEN 0 AND 100)",
            name="ck_fare_rules_discount_pct",
        ),
        ExcludeConstraint(
            ("distance_range", "&&"),
            using="gist",
            name="fare_rules_distance_range_excl",
        ),
    )

    op.create_index("idx_fare_rules_distance_range", "fare_rules", ["distance_range"], postgresql_using="gist")


def downgrade() -> None:

    op.drop_table("fare_rules")
    op.drop_table("route_return_leg_priority")
    op.drop_table("route_operators")
    op.drop_table("route_stops")
    op.drop_table("routes")

    op.execute("DROP TRIGGER IF EXISTS trg_stops_set_geom ON stops")
    op.execute("DROP FUNCTION IF EXISTS stops_set_geom()")
    op.drop_table("stops")
    op.drop_table("operators")

    # Recreate 0001 scaffold so the chain stays reversible
    op.create_table(
        "stops",
        sa.Column("stop_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("name_normalized", sa.String(150), nullable=False),
        sa.Column("is_interchange", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_stops_geom", "stops", ["geom"], postgresql_using="gist")
    op.create_index("idx_stops_name_normalized", "stops", ["name_normalized"])

    op.create_table(
        "routes",
        sa.Column("route_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("route_number", sa.String(20), nullable=False),
        sa.Column("route_name", sa.String(150), nullable=False),
        sa.Column("operator", sa.String(100)),
        sa.Column("tier", sa.SmallInteger),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(50)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("tier IN (1,2,3)", name="ck_routes_tier"),
    )
    op.create_index("idx_routes_tier", "routes", ["tier"])
    op.create_index("idx_routes_verified", "routes", ["verified"])

    op.create_table(
        "route_stops",
        sa.Column("route_id", sa.Integer, sa.ForeignKey("routes.route_id", ondelete="CASCADE"), nullable=False),
        sa.Column("stop_id", sa.Integer, sa.ForeignKey("stops.stop_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence_order", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("route_id", "sequence_order"),
    )
    op.create_index("idx_route_stops_route_id", "route_stops", ["route_id"])
    op.create_index("idx_route_stops_stop_id", "route_stops", ["stop_id"])
    op.create_index(
        "uq_route_stop_position",
        "route_stops",
        ["route_id", "stop_id", "sequence_order"],
        unique=True,
    )