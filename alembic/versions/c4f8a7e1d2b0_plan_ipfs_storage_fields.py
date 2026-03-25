"""plan ipfs storage fields

Revision ID: c4f8a7e1d2b0
Revises: 9c3e7b2a1f44
Create Date: 2026-03-25 23:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4f8a7e1d2b0'
down_revision: Union[str, None] = '9c3e7b2a1f44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('architectural_plans', sa.Column('storage_uri', sa.String(length=500), nullable=True))
    op.add_column('architectural_plans', sa.Column('ipfs_cid', sa.String(length=255), nullable=True))
    op.add_column('architectural_plans', sa.Column('license_code', sa.String(length=50), server_default='custom', nullable=False))
    op.add_column('architectural_plans', sa.Column('asset_status', sa.String(length=50), server_default='draft', nullable=False))
    op.add_column('architectural_plans', sa.Column('mint_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('architectural_plans', 'mint_metadata')
    op.drop_column('architectural_plans', 'asset_status')
    op.drop_column('architectural_plans', 'license_code')
    op.drop_column('architectural_plans', 'ipfs_cid')
    op.drop_column('architectural_plans', 'storage_uri')
