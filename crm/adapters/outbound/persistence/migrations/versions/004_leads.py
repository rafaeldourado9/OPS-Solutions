"""Add leads table

Revision ID: 004
Revises: 003
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(50), server_default="new"),
        sa.Column("value", sa.Float, server_default="0"),
        sa.Column("currency", sa.String(10), server_default="BRL"),
        sa.Column("source", sa.String(100), server_default=""),
        sa.Column("assigned_to", UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, server_default=""),
        sa.Column("expected_close_date", sa.DateTime, nullable=True),
        sa.Column("closed_at", sa.DateTime, nullable=True),
        sa.Column("lost_reason", sa.String(500), server_default=""),
        sa.Column("tags", ARRAY(sa.String), server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_crm_leads_tenant_stage", "crm_leads", ["tenant_id", "stage"])


def downgrade() -> None:
    op.drop_index("idx_crm_leads_tenant_stage", table_name="crm_leads")
    op.drop_table("crm_leads")
