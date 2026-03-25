"""add raw_data columns for provenance coverage

Revision ID: f0a1b2c3d4e5
Revises: e6f7a8b9c0d1
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f0a1b2c3d4e5"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("infrastructure", sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("census_data", sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("regional_standards", sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("regional_standards", "raw_data")
    op.drop_column("census_data", "raw_data")
    op.drop_column("infrastructure", "raw_data")
