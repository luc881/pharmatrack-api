from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.sensor_readings.orm import SensorReading
from ...models.sensor_readings.schemas import (
    SensorReadingCreate,
    SensorReadingResponse,
    PaginatedResponse,
    PaginationParams,
)
from ...utils.permissions import CAN_READ_SENSOR_READINGS
from pharmatrack.utils.pagination import paginate
from ...utils.rate_limit import limiter, LIMIT_READ
from ...utils.logger import get_logger

logger = get_logger(__name__)

LIMIT_SENSOR = "10/minute"

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sensor-readings",
    tags=["Sensor Readings"]
)


# =========================================================
# POST /  — público, lo usa el ESP32
# =========================================================
@router.post(
    "",
    response_model=SensorReadingResponse,
    summary="Registrar lectura de sensor",
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(LIMIT_SENSOR)
async def create_reading(request: Request, data: SensorReadingCreate, db: db_dependency):
    reading = SensorReading(
        temperature=data.temperature,
        humidity=data.humidity,
        device_id=data.device_id,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    logger.info(
        "Sensor reading saved id=%s device=%s temp=%.2f hum=%.2f",
        reading.id, reading.device_id, reading.temperature, reading.humidity,
    )
    return reading


# =========================================================
# GET /latest  — público, útil para el dashboard
# =========================================================
@router.get(
    "/latest",
    response_model=SensorReadingResponse,
    summary="Última lectura del sensor",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(LIMIT_READ)
async def get_latest(request: Request, db: db_dependency):
    reading = (
        db.query(SensorReading)
        .order_by(SensorReading.recorded_at.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No hay lecturas registradas.")
    return reading


# =========================================================
# GET /  — requiere auth, historial paginado
# =========================================================
@router.get(
    "",
    response_model=PaginatedResponse[SensorReadingResponse],
    summary="Historial de lecturas del sensor",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SENSOR_READINGS,
)
@limiter.limit(LIMIT_READ)
async def get_readings(request: Request, db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(SensorReading).order_by(SensorReading.recorded_at.desc())
    return paginate(query, pagination)
