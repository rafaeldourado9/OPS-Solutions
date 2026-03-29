"""Make product price and cost nullable

Revision ID: 011
Revises: 010
Create Date: 2026-03-28
"""
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("crm_products", "price", nullable=True, server_default=None)
    op.alter_column("crm_products", "cost", nullable=True, server_default=None)


def downgrade() -> None:
    op.execute("UPDATE crm_products SET price = 0 WHERE price IS NULL")
    op.execute("UPDATE crm_products SET cost = 0 WHERE cost IS NULL")
    op.alter_column("crm_products", "price", nullable=False, server_default="0")
    op.alter_column("crm_products", "cost", nullable=False, server_default="0")
