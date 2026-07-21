"""add husbandry/private fields to species

Revision ID: husbandryspecies01
Revises: featurehomegrp01
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'husbandryspecies01'
down_revision: Union[str, Sequence[str], None] = 'featurehomegrp01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('species', sa.Column('husbandry_status', sa.String(length=20),
                                       nullable=False, server_default='active'))
    op.add_column('species', sa.Column('low_stock_threshold', sa.BigInteger(), nullable=True))
    op.add_column('species', sa.Column('private_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('species', 'private_notes')
    op.drop_column('species', 'low_stock_threshold')
    op.drop_column('species', 'husbandry_status')
