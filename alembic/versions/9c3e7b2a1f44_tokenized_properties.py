"""tokenized properties

Revision ID: 9c3e7b2a1f44
Revises: b1a4c7d93210
Create Date: 2026-03-25 23:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9c3e7b2a1f44'
down_revision: Union[str, None] = 'b1a4c7d93210'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tokenized_properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('asset_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('issuer_name', sa.String(length=150), nullable=False),
        sa.Column('issuer_wallet', sa.String(length=120), nullable=False),
        sa.Column('property_type', sa.String(length=80), nullable=True),
        sa.Column('asset_ref', sa.String(length=120), nullable=True),
        sa.Column('fractional_enabled', sa.Boolean(), nullable=False),
        sa.Column('total_units', sa.Integer(), nullable=False),
        sa.Column('valuation_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('chain', sa.String(length=50), nullable=True),
        sa.Column('contract_address', sa.String(length=255), nullable=True),
        sa.Column('token_symbol', sa.String(length=20), nullable=True),
        sa.Column('token_standard', sa.String(length=50), nullable=True),
        sa.Column('tokenization_tx_hash', sa.String(length=255), nullable=True),
        sa.Column('asset_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rights_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tokenized_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_ref'),
    )

    op.create_table(
        'property_token_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('wallet', sa.String(length=120), nullable=False),
        sa.Column('holder_name', sa.String(length=150), nullable=True),
        sa.Column('units_owned', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['tokenized_properties.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('property_id', 'wallet', name='uq_property_token_allocations_property_wallet'),
    )

    op.create_table(
        'property_ledger_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('actor_wallet', sa.String(length=120), nullable=True),
        sa.Column('from_wallet', sa.String(length=120), nullable=True),
        sa.Column('to_wallet', sa.String(length=120), nullable=True),
        sa.Column('tx_hash', sa.String(length=255), nullable=True),
        sa.Column('chain', sa.String(length=50), nullable=True),
        sa.Column('units', sa.Integer(), nullable=True),
        sa.Column('consideration_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=20), nullable=True),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['tokenized_properties.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('property_ledger_events')
    op.drop_table('property_token_allocations')
    op.drop_table('tokenized_properties')
