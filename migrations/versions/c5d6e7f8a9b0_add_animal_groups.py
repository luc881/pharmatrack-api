"""add animal_groups table and genera.group_id

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-07-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'animal_groups',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('parent_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['animal_groups.id'], ondelete='RESTRICT'),
    )

    op.add_column('genera', sa.Column('group_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        'fk_genera_group_id', 'genera', 'animal_groups', ['group_id'], ['id'], ondelete='RESTRICT'
    )
    op.create_index('ix_genera_group_id', 'genera', ['group_id'])


def downgrade() -> None:
    op.drop_index('ix_genera_group_id', table_name='genera')
    op.drop_constraint('fk_genera_group_id', 'genera', type_='foreignkey')
    op.drop_column('genera', 'group_id')
    op.drop_table('animal_groups')
