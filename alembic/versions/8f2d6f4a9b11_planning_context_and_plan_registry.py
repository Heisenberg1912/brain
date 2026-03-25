"""planning context and plan registry

Revision ID: 8f2d6f4a9b11
Revises: 38d814fe064a
Create Date: 2026-03-25 22:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8f2d6f4a9b11'
down_revision: Union[str, None] = '38d814fe064a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planning_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('admin_area', sa.String(length=120), nullable=True),
        sa.Column('market_tier', sa.String(length=50), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=False),
        sa.Column('floor_plan_constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('zoning_validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location_intelligence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('massing_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'architectural_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author_name', sa.String(length=150), nullable=False),
        sa.Column('author_wallet', sa.String(length=120), nullable=False),
        sa.Column('current_owner_wallet', sa.String(length=120), nullable=False),
        sa.Column('version_label', sa.String(length=50), nullable=False),
        sa.Column('file_hash', sa.String(length=255), nullable=False),
        sa.Column('preview_url', sa.String(length=500), nullable=True),
        sa.Column('personal_license_allowed', sa.Boolean(), nullable=False),
        sa.Column('commercial_license_allowed', sa.Boolean(), nullable=False),
        sa.Column('resale_license_allowed', sa.Boolean(), nullable=False),
        sa.Column('royalty_bps', sa.Integer(), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=True),
        sa.Column('contract_address', sa.String(length=255), nullable=True),
        sa.Column('token_id', sa.String(length=120), nullable=True),
        sa.Column('mint_tx_hash', sa.String(length=255), nullable=True),
        sa.Column('minted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rights_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('constraint_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('zoning_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location_intelligence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('massing_inputs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash'),
    )

    op.create_table(
        'plan_licenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('grantee_wallet', sa.String(length=120), nullable=False),
        sa.Column('grantee_name', sa.String(length=150), nullable=True),
        sa.Column('personal_use', sa.Boolean(), nullable=False),
        sa.Column('commercial_use', sa.Boolean(), nullable=False),
        sa.Column('resale_use', sa.Boolean(), nullable=False),
        sa.Column('can_sublicense', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['architectural_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'plan_ledger_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_wallet', sa.String(length=120), nullable=True),
        sa.Column('from_wallet', sa.String(length=120), nullable=True),
        sa.Column('to_wallet', sa.String(length=120), nullable=True),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('chain', sa.String(length=50), nullable=True),
        sa.Column('sale_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=20), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['architectural_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('plan_ledger_events')
    op.drop_table('plan_licenses')
    op.drop_table('architectural_plans')
    op.drop_table('planning_contexts')
