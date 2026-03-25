"""exchange marketplace

Revision ID: b1a4c7d93210
Revises: 8f2d6f4a9b11
Create Date: 2026-03-25 22:35:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1a4c7d93210'
down_revision: Union[str, None] = '8f2d6f4a9b11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'exchange_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('seller_wallet', sa.String(length=120), nullable=False),
        sa.Column('listing_type', sa.String(length=50), nullable=False),
        sa.Column('asking_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('personal_use', sa.Boolean(), nullable=False),
        sa.Column('commercial_use', sa.Boolean(), nullable=False),
        sa.Column('resale_use', sa.Boolean(), nullable=False),
        sa.Column('can_sublicense', sa.Boolean(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['architectural_plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'exchange_offers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('bidder_wallet', sa.String(length=120), nullable=False),
        sa.Column('bidder_name', sa.String(length=150), nullable=True),
        sa.Column('offer_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=20), nullable=False),
        sa.Column('intended_use', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['listing_id'], ['exchange_listings.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('exchange_offers')
    op.drop_table('exchange_listings')
