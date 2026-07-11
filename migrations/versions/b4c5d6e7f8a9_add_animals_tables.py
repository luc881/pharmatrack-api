"""add genera, species, morphs, animals, animal_has_morphs tables

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'genera',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'species',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('genus_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('common_name', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['genus_id'], ['genera.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('genus_id', 'name', name='uq_species_genus_name'),
    )
    op.create_index('ix_species_genus_id', 'species', ['genus_id'])

    op.create_table(
        'morphs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('species_id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['species_id'], ['species.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('species_id', 'name', name='uq_morph_species_name'),
    )
    op.create_index('ix_morphs_species_id', 'morphs', ['species_id'])

    op.create_table(
        'animals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('species_id', sa.BigInteger(), nullable=False),
        sa.Column('product_id', sa.BigInteger(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('sex', sa.String(length=10), server_default='unknown', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='available', nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('price_cost', sa.Numeric(12, 2), server_default='0', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image', sa.String(length=250), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['species_id'], ['species.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('product_id'),
    )
    op.create_index('ix_animals_species_id', 'animals', ['species_id'])
    op.create_index('ix_animals_status', 'animals', ['status'])

    op.create_table(
        'animal_has_morphs',
        sa.Column('animal_id', sa.BigInteger(), nullable=False),
        sa.Column('morph_id', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('animal_id', 'morph_id'),
        sa.ForeignKeyConstraint(['animal_id'], ['animals.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['morph_id'], ['morphs.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('animal_has_morphs')
    op.drop_table('animals')
    op.drop_table('morphs')
    op.drop_table('species')
    op.drop_table('genera')
