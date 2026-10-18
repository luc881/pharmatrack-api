import re
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Text, String, BigInteger, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ...db.session import Base


class CareSheet(Base):
    """Ficha de cuidados de una especie (sitio público: /fichas).

    Una por especie. Lo taxonómico sale de la especie (nombre científico,
    localidad entre comillas, grupo para el filtro) y no se repite aquí; la
    ficha guarda el contenido de cuidados, que manda sobre los campos de
    cuidados de la especie cuando existe. El cuerpo es Markdown (## = sección).
    """

    __tablename__ = "care_sheets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    species_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("species.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    # quién describió la especie, p. ej. "Cumming, Bank, Le Tirant & Bradler, 2020"
    authority: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # Listas ordenadas (JSON): [{rank, name, italic}], [{label, value}], [str],
    # [{src, alt}], {src, alt}, [{text, url}]
    taxonomy: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    facts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    basics: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Morfología por etapa/sexo: [{label: "Hembra", text: "..."}]
    morphology: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    habitat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    video: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    references: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # NULL = borrador; con fecha = publicada (el sitio solo ve estas)
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    species = relationship("Species")

    @property
    def published(self) -> bool:
        return self.published_at is not None

    # 'Gardabagusi "Argopuro"' → binomio "Phyllium gardabagusi" + localidad "Argopuro"
    @property
    def scientific_name(self) -> str:
        epithet = re.split(r'[\s"“]', self.species.name.strip(), maxsplit=1)[0]
        return f"{self.species.genus.name} {epithet.lower()}"

    @property
    def locality(self) -> Optional[str]:
        m = re.search(r'["“]([^"”]+)["”]', self.species.name)
        return m.group(1) if m else None

    @property
    def common_name(self) -> Optional[str]:
        return self.species.common_name

    @property
    def group(self) -> Optional[dict]:
        g = self.species.genus.group
        return {"id": g.id, "name": g.name} if g else None
