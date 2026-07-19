from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Text, String, BigInteger, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ...db.session import Base


class Article(Base):
    """Artículo de divulgación para el sitio público (estructura tipo phasmaMX).

    El cuerpo es texto libre con convenciones ligeras que el sitio renderea:
    línea en blanco = párrafo, "## " = subtítulo, "> " = cita destacada,
    "img: URL | pie de foto" = imagen intercalada.
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    author_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # NULL = borrador; con fecha = publicado (el sitio público solo ve estos)
    published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    @property
    def published(self) -> bool:
        return self.published_at is not None

    @property
    def reading_minutes(self) -> int:
        words = len((self.body or "").split())
        return max(1, round(words / 200))
