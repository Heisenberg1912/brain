"""intelligence layers and plan metadata

Revision ID: d4e5f6a7b8c9
Revises: c4f8a7e1d2b0
Create Date: 2026-03-25 23:58:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c4f8a7e1d2b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("masterplans", sa.Column("dataset_version", sa.String(length=50), nullable=False, server_default="seed_v1"))
    op.add_column("masterplans", sa.Column("effective_from", sa.Date(), nullable=True))
    op.add_column("masterplans", sa.Column("effective_to", sa.Date(), nullable=True))
    op.add_column("masterplans", sa.Column("approval_status", sa.String(length=50), nullable=False, server_default="active"))
    op.add_column("masterplans", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column("property_prices", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("infrastructure", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("census_data", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table(
        "location_geo_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("dataset_version", sa.String(length=50), nullable=False),
        sa.Column("terrain_class", sa.String(length=50), nullable=True),
        sa.Column("terrain_slope_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("flood_risk_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("heat_risk_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("climate_risk_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("road_proximity_km", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("transit_proximity_km", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("source", sa.String(length=120), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "regional_standards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("standard_type", sa.String(length=50), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("admin_area", sa.String(length=120), nullable=True),
        sa.Column("region_name", sa.String(length=120), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("version_tag", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_regional_standards_scope",
        "regional_standards",
        ["country_code", "admin_area", "standard_type"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("idx_regional_standards_scope", table_name="regional_standards")
    op.drop_table("regional_standards")
    op.drop_table("location_geo_profiles")

    op.drop_column("census_data", "tags")
    op.drop_column("infrastructure", "tags")
    op.drop_column("property_prices", "tags")

    op.drop_column("masterplans", "tags")
    op.drop_column("masterplans", "approval_status")
    op.drop_column("masterplans", "effective_to")
    op.drop_column("masterplans", "effective_from")
    op.drop_column("masterplans", "dataset_version")
