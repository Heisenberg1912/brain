"""india wide location scope

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a7b8c9
Create Date: 2026-03-26 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "locations",
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="IN"),
    )
    op.add_column(
        "locations",
        sa.Column("state", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "infrastructure",
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="IN"),
    )
    op.add_column(
        "infrastructure",
        sa.Column("state", sa.String(length=100), nullable=True),
    )

    op.execute("UPDATE locations SET state = 'Karnataka' WHERE city = 'Bangalore' AND state IS NULL")
    op.execute("UPDATE infrastructure SET state = 'Karnataka' WHERE city = 'Bangalore' AND state IS NULL")


def downgrade() -> None:
    op.drop_column("infrastructure", "state")
    op.drop_column("infrastructure", "country_code")
    op.drop_column("locations", "state")
    op.drop_column("locations", "country_code")
