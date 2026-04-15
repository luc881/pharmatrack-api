"""create password_reset_tokens table

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("token", sa.String(128), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
