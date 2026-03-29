"""Add field_mapping to quote_templates

Revision ID: 009
Revises: 008
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crm_quote_templates",
        sa.Column("field_mapping", JSONB, server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("crm_quote_templates", "field_mapping")
