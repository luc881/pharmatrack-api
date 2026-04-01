"""add sensor_readings table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('temperature', sa.Double(), nullable=False),
        sa.Column('humidity', sa.Double(), nullable=False),
        sa.Column('recorded_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('sensor_readings')
