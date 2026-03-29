"""Add last_inactivity_email_at to crm_leads

Revision ID: 015
Revises: 014
Create Date: 2026-03-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crm_leads",
        sa.Column("last_inactivity_email_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crm_leads", "last_inactivity_email_at")
