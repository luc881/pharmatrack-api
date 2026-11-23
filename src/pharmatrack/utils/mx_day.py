"""Fechas: la base guarda UTC sin zona; los días y meses son los de México."""
from datetime import date, datetime, timedelta, timezone
from typing import Annotated

from pydantic import PlainSerializer

# UTC-6 fijo: México no tiene horario de verano desde 2022
MX_OFFSET = timedelta(hours=6)


def mx_today() -> date:
    return (datetime.now(timezone.utc) - MX_OFFSET).date()


def utc_iso(value: datetime) -> str:
    """Con su zona: sin ella el navegador la toma como hora local y lo cobrado
    de noche sale con fecha del día siguiente."""
    return (value if value.tzinfo else value.replace(tzinfo=timezone.utc)).isoformat()


UtcDatetime = Annotated[datetime, PlainSerializer(utc_iso, return_type=str, when_used="json")]
