"""add sale_format and package_size to species

Revision ID: a7b8c9d0e1f2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, Sequence[str], None] = 'd6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('species', sa.Column('sale_format', sa.String(length=20),
                                       server_default='individual', nullable=False))
    op.add_column('species', sa.Column('package_size', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('species', 'package_size')
    op.drop_column('species', 'sale_format')
