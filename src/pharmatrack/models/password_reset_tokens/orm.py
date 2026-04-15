from sqlalchemy import BigInteger, ForeignKey, TIMESTAMP, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from ...db.session import Base
from datetime import datetime


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token: Mapped[str] = mapped_column(String(128), primary_key=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User")
