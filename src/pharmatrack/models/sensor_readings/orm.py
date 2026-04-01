from sqlalchemy import BigInteger, Double, TIMESTAMP, String
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from ...db.session import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    temperature: Mapped[float] = mapped_column(Double, nullable=False)
    humidity: Mapped[float] = mapped_column(Double, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False), server_default=func.now(), nullable=False
    )
    device_id: Mapped[str] = mapped_column(String(100), nullable=True)
