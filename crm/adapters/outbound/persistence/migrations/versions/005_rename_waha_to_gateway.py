"""Rename waha_session/waha_url to gateway_session/gateway_url in tenants

Revision ID: 005
Revises: 004
Create Date: 2026-03-24
"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("tenants", "waha_session", new_column_name="gateway_session")
    op.alter_column("tenants", "waha_url", new_column_name="gateway_url")


def downgrade() -> None:
    op.alter_column("tenants", "gateway_session", new_column_name="waha_session")
    op.alter_column("tenants", "gateway_url", new_column_name="waha_url")
