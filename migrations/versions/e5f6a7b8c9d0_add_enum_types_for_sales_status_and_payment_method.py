"""add enum types for sales status and payment method

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-14

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PostgreSQL ENUM types
    op.execute(
        "CREATE TYPE salestatusenum AS ENUM "
        "('draft', 'completed', 'cancelled', 'refunded', 'partially_refunded')"
    )
    op.execute(
        "ALTER TABLE sales "
        "ALTER COLUMN status TYPE salestatusenum "
        "USING status::salestatusenum"
    )

    op.execute(
        "CREATE TYPE paymentmethodenum AS ENUM "
        "('cash', 'card', 'transfer')"
    )
    op.execute(
        "ALTER TABLE sale_payments "
        "ALTER COLUMN method_payment TYPE paymentmethodenum "
        "USING method_payment::paymentmethodenum"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE sales "
        "ALTER COLUMN status TYPE VARCHAR(20) "
        "USING status::VARCHAR"
    )
    op.execute("DROP TYPE salestatusenum")

    op.execute(
        "ALTER TABLE sale_payments "
        "ALTER COLUMN method_payment TYPE VARCHAR(30) "
        "USING method_payment::VARCHAR"
    )
    op.execute("DROP TYPE paymentmethodenum")
