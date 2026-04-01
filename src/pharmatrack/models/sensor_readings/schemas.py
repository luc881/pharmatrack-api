from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from ..products.schemas import PaginatedResponse, PaginationParams


class SensorReadingCreate(BaseModel):
    temperature: float = Field(..., description="Temperatura en °C")
    humidity: float = Field(..., description="Humedad relativa en %")
    device_id: Optional[str] = Field(None, max_length=100, description="Identificador del ESP32")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "temperature": 23.5,
                "humidity": 61.2,
                "device_id": "esp32-farmacia-01"
            }
        }
    )


class SensorReadingResponse(BaseModel):
    id: int
    temperature: float
    humidity: float
    recorded_at: datetime
    device_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "SensorReadingCreate",
    "SensorReadingResponse",
    "PaginatedResponse",
    "PaginationParams",
]
