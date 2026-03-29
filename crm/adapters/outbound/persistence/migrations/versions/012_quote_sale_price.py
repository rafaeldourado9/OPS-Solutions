"""Add sale_price to crm_quotes

Revision ID: 012
Revises: 011
Create Date: 2026-03-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("crm_quotes", sa.Column("sale_price", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("crm_quotes", "sale_price")
