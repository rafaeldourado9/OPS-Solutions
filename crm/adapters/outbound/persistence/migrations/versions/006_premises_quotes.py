"""Add premises and quotes tables

Revision ID: 006
Revises: 005
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_premises",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "crm_quotes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("notes", sa.Text, server_default=""),
        sa.Column("valid_until", sa.DateTime, nullable=True),
        sa.Column("currency", sa.String(10), server_default="BRL"),
        sa.Column("items_json", JSON, server_default="[]"),
        sa.Column("applied_premises_json", JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_crm_quotes_tenant_status", "crm_quotes", ["tenant_id", "status"])
    op.create_index("idx_crm_quotes_tenant_customer", "crm_quotes", ["tenant_id", "customer_id"])
    op.create_index("idx_crm_quotes_tenant_lead", "crm_quotes", ["tenant_id", "lead_id"])


def downgrade() -> None:
    op.drop_index("idx_crm_quotes_tenant_lead", table_name="crm_quotes")
    op.drop_index("idx_crm_quotes_tenant_customer", table_name="crm_quotes")
    op.drop_index("idx_crm_quotes_tenant_status", table_name="crm_quotes")
    op.drop_table("crm_quotes")
    op.drop_table("crm_premises")
