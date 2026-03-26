"""Add conversations and messages tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("customer_phone", sa.String(20), server_default=""),
        sa.Column("agent_id", sa.String(100), server_default=""),
        sa.Column("last_message_preview", sa.Text, server_default=""),
        sa.Column("last_message_at", sa.DateTime, nullable=True),
        sa.Column("unread_count", sa.Integer, server_default="0"),
        sa.Column("is_takeover_active", sa.Boolean, server_default="false"),
        sa.Column("takeover_operator_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "chat_id", name="uq_conversations_tenant_chat"),
    )

    op.create_table(
        "crm_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("crm_conversations.id"), nullable=False),
        sa.Column("chat_id", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("media_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_crm_messages_conv_time", "crm_messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_crm_messages_conv_time", table_name="crm_messages")
    op.drop_table("crm_messages")
    op.drop_table("crm_conversations")
