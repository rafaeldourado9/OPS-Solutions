"""Add cost column and multiplier type to premises

Revision ID: 010
Revises: 009
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crm_premises",
        sa.Column("cost", sa.Float, server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("crm_premises", "cost")
