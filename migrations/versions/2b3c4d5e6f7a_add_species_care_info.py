"""add care info columns to species

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b3c4d5e6f7a'
down_revision: Union[str, Sequence[str], None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS = [
    ('description', sa.Text()),
    ('origin', sa.String(length=150)),
    ('temperature', sa.String(length=50)),
    ('humidity', sa.String(length=50)),
    ('adult_size', sa.String(length=50)),
    ('difficulty', sa.String(length=50)),
    ('rarity', sa.String(length=50)),
]


def upgrade() -> None:
    for name, type_ in COLUMNS:
        op.add_column('species', sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(COLUMNS):
        op.drop_column('species', name)
