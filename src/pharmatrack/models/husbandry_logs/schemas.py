from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Appetite = Literal["good", "regular", "poor", "refused"]
# Fotos subidas a Cloudinary desde el navegador
HttpsUrl = Annotated[str, StringConstraints(max_length=500, pattern=r"^https://")]

# Lo que se hizo u observó en el terrario además de alimentar
Activity = Literal["misted", "cleaned", "substrate", "molt", "eggs", "births", "deaths"]


class HusbandryLogCreate(BaseModel):
    species_id: int = Field(..., gt=0)
    morph_id: Optional[int] = Field(None, gt=0)
    log_date: date
    fed: bool = False
    food_type: Optional[str] = Field(None, max_length=100)
    pieces: Optional[int] = Field(None, ge=0, le=100000)
    grams: Optional[Decimal] = Field(None, ge=0, le=100000, decimal_places=2)
    appetite: Optional[Appetite] = None
    feeding_notes: Optional[str] = Field(None, max_length=2000)
    supplement: Optional[str] = Field(None, max_length=100)
    deaths: Optional[int] = Field(None, ge=0, le=100000)
    animal_id: Optional[int] = Field(None, gt=0)
    activities: list[Activity] = Field(default_factory=list, max_length=10)
    notes: Optional[str] = Field(None, max_length=4000)
    photos: list[HttpsUrl] = Field(default_factory=list, max_length=12)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _implied_fed(self):
        # Si se anotó cuánto comió, comió (salvo que lo haya rechazado)
        if (self.pieces or self.grams) and self.appetite != "refused":
            self.fed = True
        if self.deaths:
            self.activities = [*self.activities, "deaths"]
        self.activities = list(dict.fromkeys(self.activities))
        return self


# PUT reemplaza la entrada completa
HusbandryLogUpdate = HusbandryLogCreate


class HusbandryLogResponse(BaseModel):
    id: int
    species_id: int
    morph_id: Optional[int] = None
    log_date: date
    fed: bool
    food_type: Optional[str] = None
    pieces: Optional[int] = None
    grams: Optional[Decimal] = None
    appetite: Optional[str] = None
    feeding_notes: Optional[str] = None
    supplement: Optional[str] = None
    deaths: Optional[int] = None
    animal_id: Optional[int] = None
    animal_code: Optional[str] = None
    stock_deducted: int = 0
    activities: Optional[list[str]] = None
    notes: Optional[str] = None
    photos: Optional[list[str]] = None
    user_id: Optional[int] = None
    species_name: Optional[str] = None
    morph_name: Optional[str] = None
    user_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlanStatusItem(BaseModel):
    kind: str
    name: str
    every_days: int
    last_done: Optional[date] = None
    next_due: date
    days_overdue: int  # >0 atrasado, 0 toca hoy, <0 faltan días


class HusbandryStatus(BaseModel):
    """Resumen por especie: plan con próximas fechas y conteos del mes."""
    species_id: int
    species_name: str
    common_name: Optional[str] = None
    last_fed: Optional[date] = None
    plan: list[PlanStatusItem] = []
    month: dict[str, int] = {}
