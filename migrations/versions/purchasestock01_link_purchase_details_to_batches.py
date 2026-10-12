"""La compra suma al stock: cada renglón recuerda el lote al que sumó

Revision ID: purchasestock01
Revises: deliveries01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "purchasestock01"
down_revision: Union[str, Sequence[str], None] = "deliveries01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("purchase_details", sa.Column("batch_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_purchase_details_batch_id",
        "purchase_details",
        "product_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_purchase_details_batch_id", "purchase_details", ["batch_id"])


def downgrade() -> None:
    op.drop_index("ix_purchase_details_batch_id", table_name="purchase_details")
    op.drop_constraint("fk_purchase_details_batch_id", "purchase_details", type_="foreignkey")
    op.drop_column("purchase_details", "batch_id")
