"""compare_at_price (ofertas) en products/animals + tabla bundle_items

Revision ID: 7a8b9c0d1e2f
Revises: 6f7a8b9c0d1e
Create Date: 2026-07-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '6f7a8b9c0d1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Precio anterior (tachado): price_retail/price siguen siendo lo que se
    # cobra; compare_at_price solo se muestra como oferta en la tienda
    op.add_column('products', sa.Column('compare_at_price', sa.Numeric(12, 2), nullable=True))
    op.add_column('animals', sa.Column('compare_at_price', sa.Numeric(12, 2), nullable=True))

    # Paquetes: un producto con componentes (otros productos, incluidos los
    # gemelos de animales). Vender el paquete descuenta cada componente.
    op.create_table(
        'bundle_items',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('bundle_product_id', sa.BigInteger(),
                  sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('component_product_id', sa.BigInteger(),
                  sa.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.UniqueConstraint('bundle_product_id', 'component_product_id', name='uq_bundle_component'),
    )


def downgrade() -> None:
    op.drop_table('bundle_items')
    op.drop_column('animals', 'compare_at_price')
    op.drop_column('products', 'compare_at_price')
