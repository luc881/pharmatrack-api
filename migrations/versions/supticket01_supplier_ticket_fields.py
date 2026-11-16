"""Datos del ticket del proveedor (un ticket por dueño en la venta rápida)

Revision ID: supticket01
Revises: avatars01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "supticket01"
down_revision: Union[str, Sequence[str], None] = "avatars01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("ticket_prefix", sa.String(6), nullable=True))
    op.add_column("suppliers", sa.Column("ticket_lines", sa.String(400), nullable=True))
    op.add_column("suppliers", sa.Column("ticket_qr_url", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("suppliers", "ticket_qr_url")
    op.drop_column("suppliers", "ticket_lines")
    op.drop_column("suppliers", "ticket_prefix")
