"""add husbandry/private fields to morphs

Revision ID: husbandrymorph01
Revises: groupshowinnav01
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'husbandrymorph01'
down_revision: Union[str, Sequence[str], None] = 'groupshowinnav01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('morphs', sa.Column('husbandry_status', sa.String(length=20),
                                      nullable=False, server_default='active'))
    op.add_column('morphs', sa.Column('low_stock_threshold', sa.BigInteger(), nullable=True))
    op.add_column('morphs', sa.Column('private_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('morphs', 'private_notes')
    op.drop_column('morphs', 'low_stock_threshold')
    op.drop_column('morphs', 'husbandry_status')
