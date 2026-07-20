"""add feature_home to animal_groups

Revision ID: featurehomegrp01
Revises: 9c0d1e2f3a4b
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'featurehomegrp01'
down_revision: Union[str, Sequence[str], None] = '9c0d1e2f3a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'animal_groups',
        sa.Column('feature_home', sa.Boolean(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('animal_groups', 'feature_home')
