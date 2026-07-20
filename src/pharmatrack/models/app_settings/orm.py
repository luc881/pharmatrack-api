from sqlalchemy import Text, String
from sqlalchemy.orm import Mapped, mapped_column

from ...db.session import Base


class AppSetting(Base):
    """Configuracion clave-valor (JSON en value). Hoy: plantilla del correo de ticket."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
