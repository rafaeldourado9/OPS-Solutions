"""Add whatsapp_numbers table for multi-WhatsApp support

Revision ID: 018
Revises: 017
Create Date: 2026-03-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_whatsapp_numbers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("session_name", sa.String(100), nullable=False, unique=True),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("agent_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("connected_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("crm_whatsapp_numbers")
