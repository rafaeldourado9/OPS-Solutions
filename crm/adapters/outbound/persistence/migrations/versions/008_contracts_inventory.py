"""Add contracts, products and stock_movements tables

Revision ID: 008
Revises: 007
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crm_contracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("quote_id", UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("content", sa.Text, server_default=""),
        sa.Column("signed_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_crm_contracts_tenant_status", "crm_contracts", ["tenant_id", "status"])
    op.create_index("idx_crm_contracts_quote_id", "crm_contracts", ["quote_id"])

    op.create_table(
        "crm_products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("unit", sa.String(20), server_default="un"),
        sa.Column("price", sa.Float, server_default="0"),
        sa.Column("cost", sa.Float, server_default="0"),
        sa.Column("stock_quantity", sa.Float, server_default="0"),
        sa.Column("min_stock_alert", sa.Float, server_default="0"),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_crm_products_tenant_sku", "crm_products", ["tenant_id", "sku"], unique=True)

    op.create_table(
        "crm_stock_movements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("crm_products.id"), nullable=False, index=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("reason", sa.String(500), server_default=""),
        sa.Column("reference_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("crm_stock_movements")
    op.drop_index("idx_crm_products_tenant_sku", table_name="crm_products")
    op.drop_table("crm_products")
    op.drop_index("idx_crm_contracts_quote_id", table_name="crm_contracts")
    op.drop_index("idx_crm_contracts_tenant_status", table_name="crm_contracts")
    op.drop_table("crm_contracts")
