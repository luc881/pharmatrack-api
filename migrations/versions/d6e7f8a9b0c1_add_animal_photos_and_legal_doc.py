"""add animal_photos table and legal doc columns to animals

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, Sequence[str], None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'animal_photos',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('animal_id', sa.BigInteger(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_animal_photos_animal_id', 'animal_photos', ['animal_id'])

    op.add_column('animals', sa.Column('requires_legal_doc', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('animals', sa.Column('legal_doc', sa.String(length=150), nullable=True))
    op.add_column('animals', sa.Column('legal_doc_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('animals', 'legal_doc_url')
    op.drop_column('animals', 'legal_doc')
    op.drop_column('animals', 'requires_legal_doc')
    op.drop_index('ix_animal_photos_animal_id', table_name='animal_photos')
    op.drop_table('animal_photos')
