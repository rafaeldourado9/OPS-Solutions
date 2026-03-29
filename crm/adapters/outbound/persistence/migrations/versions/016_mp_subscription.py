"""016 mp subscription fields

Revision ID: 016
Revises: 015
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("mp_subscription_id", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("mp_payer_email", sa.Text(), nullable=True))
    op.add_column("tenants", sa.Column("subscription_status", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "subscription_status")
    op.drop_column("tenants", "mp_payer_email")
    op.drop_column("tenants", "mp_subscription_id")
