"""Add customers table

Revision ID: 002
Revises: 001
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("cpf_cnpj", sa.String(20), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("address", JSONB, nullable=True),
        sa.Column("tags", ARRAY(sa.String), server_default="{}"),
        sa.Column("notes", sa.Text, server_default=""),
        sa.Column("source", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("chat_id", sa.String(100), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "phone", name="uq_customers_tenant_phone"),
    )


def downgrade() -> None:
    op.drop_table("customers")
