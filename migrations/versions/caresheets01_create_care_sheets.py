"""Fichas de cuidados (care_sheets): una por especie

Revision ID: caresheets01
Revises: husbandrylogs05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "caresheets01"
down_revision: Union[str, Sequence[str], None] = "husbandrylogs05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_sheets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("species_id", sa.BigInteger(), sa.ForeignKey("species.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("slug", sa.String(length=150), nullable=False, unique=True),
        sa.Column("authority", sa.String(length=200), nullable=True),
        sa.Column("origin", sa.String(length=150), nullable=True),
        sa.Column("difficulty", sa.String(length=50), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("taxonomy", sa.JSON(), nullable=True),
        sa.Column("facts", sa.JSON(), nullable=True),
        sa.Column("basics", sa.JSON(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("video", sa.JSON(), nullable=True),
        sa.Column("references", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=False), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("care_sheets")
