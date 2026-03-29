"""Add contract_templates table

Revision ID: 013
Revises: 012
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_contract_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True, server_default=""),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("variables_json", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_crm_contract_templates_tenant_id", "crm_contract_templates", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_crm_contract_templates_tenant_id", "crm_contract_templates")
    op.drop_table("crm_contract_templates")
