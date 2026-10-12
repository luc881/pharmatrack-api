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
    # Alimentación asistida (forzada): no comió solo, se le dio
    assisted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    food_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pieces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grams: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    appetite: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    feeding_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Cómo se ve el ejemplar: active | lethargic | other (+ condition_note)
    condition: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    condition_note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)

    # Ejemplar de la entrada (código individual) cuando se anota uno por uno.
    # Bajas: si se elige el ejemplar/cepa, se descuentan de su inventario.
    # stock_deducted guarda lo que de verdad se descontó, para regresarlo al
    # editar o borrar la entrada.
    deaths: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    animal_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("animals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stock_deducted: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    # Estado del ejemplar antes de la baja: al borrarla regresa a ese
    # (reservado sigue reservado; vendido sin entregar sigue vendido)
    prev_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Cambio por otro ejemplar (utils/animal_replacement.py): a quién pasó la
    # reserva/venta/entrega, y qué uso de lote se movió para poder deshacerlo
    replacement_animal_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("animals.id", ondelete="SET NULL"), nullable=True
    )
    replaced_usage_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("sale_batch_usages.id", ondelete="SET NULL"), nullable=True
    )

    activities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())

    species = relationship("Species")
    morph = relationship("Morph")
    user = relationship("User")
    animal = relationship("Animal", foreign_keys=[animal_id])
    replacement = relationship("Animal", foreign_keys=[replacement_animal_id])

    @property
    def species_name(self) -> Optional[str]:
        sp = self.species
        if not sp:
            return None
        return f"{sp.genus.name} {sp.name}" if sp.genus else sp.name

    @property
    def species_common_name(self) -> Optional[str]:
        return self.species.common_name if self.species else None

    @property
    def morph_name(self) -> Optional[str]:
        return self.morph.name if self.morph else None

    @property
    def animal_code(self) -> Optional[str]:
        return self.animal.code if self.animal else None

    @property
    def replacement_code(self) -> Optional[str]:
        return self.replacement.code if self.replacement else None

    @property
    def user_name(self) -> Optional[str]:
        return self.user.name if self.user else None
