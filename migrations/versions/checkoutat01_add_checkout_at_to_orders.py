"""add checkout_at to orders (reserva temporal al abrir el pago)

Revision ID: checkoutat01
Revises: husbandrymorph01
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'checkoutat01'
down_revision: Union[str, Sequence[str], None] = 'husbandrymorph01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('checkout_at', sa.TIMESTAMP(timezone=False), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'checkout_at')
