"""monetary columns double to numeric

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # purchases.total
    op.execute(
        "ALTER TABLE purchases "
        "ALTER COLUMN total TYPE NUMERIC(12, 2) "
        "USING total::NUMERIC(12, 2)"
    )
    # purchase_details.unit_price
    op.execute(
        "ALTER TABLE purchase_details "
        "ALTER COLUMN unit_price TYPE NUMERIC(12, 2) "
        "USING unit_price::NUMERIC(12, 2)"
    )
    # purchase_details.quantity (fractional units, e.g. 1.5 kg)
    op.execute(
        "ALTER TABLE purchase_details "
        "ALTER COLUMN quantity TYPE NUMERIC(10, 4) "
        "USING quantity::NUMERIC(10, 4)"
    )
    # products.price_retail
    op.execute(
        "ALTER TABLE products "
        "ALTER COLUMN price_retail TYPE NUMERIC(12, 2) "
        "USING price_retail::NUMERIC(12, 2)"
    )
    # products.price_cost
    op.execute(
        "ALTER TABLE products "
        "ALTER COLUMN price_cost TYPE NUMERIC(12, 2) "
        "USING price_cost::NUMERIC(12, 2)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE purchases ALTER COLUMN total TYPE DOUBLE PRECISION "
        "USING total::DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE purchase_details ALTER COLUMN unit_price TYPE DOUBLE PRECISION "
        "USING unit_price::DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE purchase_details ALTER COLUMN quantity TYPE DOUBLE PRECISION "
        "USING quantity::DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE products ALTER COLUMN price_retail TYPE DOUBLE PRECISION "
        "USING price_retail::DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE products ALTER COLUMN price_cost TYPE DOUBLE PRECISION "
        "USING price_cost::DOUBLE PRECISION"
    )
