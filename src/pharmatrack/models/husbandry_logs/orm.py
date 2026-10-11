from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, JSON, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...db.session import Base


class HusbandryLog(Base):
    """Bitácora del plan de manejo: entradas por especie (o morph) y día.
    Todo es opcional salvo la fecha: `fed` sola es la palomita rápida."""
    __tablename__ = "husbandry_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("species.id", ondelete="CASCADE"), nullable=False, index=True
    )
    morph_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("morphs.id", ondelete="CASCADE"), nullable=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    fed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
    food_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pieces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grams: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    appetite: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    feeding_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    activities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())

    species = relationship("Species")
    morph = relationship("Morph")
    user = relationship("User")

    @property
    def species_name(self) -> Optional[str]:
        sp = self.species
        if not sp:
            return None
        return f"{sp.genus.name} {sp.name}" if sp.genus else sp.name

    @property
    def morph_name(self) -> Optional[str]:
        return self.morph.name if self.morph else None

    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None
