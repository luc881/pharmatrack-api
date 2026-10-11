"""Bitácora del plan de manejo de especies (alimentación, actividades, notas)."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import Morph, Species
from ...models.husbandry_logs.orm import HusbandryLog
from ...models.husbandry_logs.schemas import HusbandryLogCreate, HusbandryLogResponse, HusbandryLogUpdate
from ...utils.permissions import CAN_READ_ANIMALS, CAN_UPDATE_ANIMALS
from ...utils.security import user_dependency
from pharmatrack.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(prefix="/husbandry-logs", tags=["Husbandry logs"])


def _query(db: Session):
    return db.query(HusbandryLog).options(
        joinedload(HusbandryLog.species).joinedload(Species.genus),
        joinedload(HusbandryLog.morph),
        joinedload(HusbandryLog.user),
    )


def _validate(db: Session, data: HusbandryLogCreate):
    if not db.get(Species, data.species_id):
        raise HTTPException(status_code=404, detail="Species not found.")
    if data.morph_id:
        morph = db.get(Morph, data.morph_id)
        if not morph or morph.species_id != data.species_id:
            raise HTTPException(status_code=400, detail="Morph does not belong to the species.")


def _get(db: Session, log_id: int) -> HusbandryLog:
    log = _query(db).filter(HusbandryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    return log


@router.get("", response_model=PaginatedResponse[HusbandryLogResponse], dependencies=CAN_READ_ANIMALS)
async def list_logs(
    db: db_dependency,
    species_id: Optional[int] = Query(None, gt=0),
    morph_id: Optional[int] = Query(None, gt=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    pagination: PaginationParams = Depends(),
):
    q = _query(db)
    if species_id:
        q = q.filter(HusbandryLog.species_id == species_id)
    if morph_id:
        q = q.filter(HusbandryLog.morph_id == morph_id)
    if date_from:
        q = q.filter(HusbandryLog.log_date >= date_from)
    if date_to:
        q = q.filter(HusbandryLog.log_date <= date_to)
    return paginate(q.order_by(HusbandryLog.log_date.desc(), HusbandryLog.id.desc()), pagination)


@router.post("", response_model=HusbandryLogResponse, status_code=status.HTTP_201_CREATED, dependencies=CAN_UPDATE_ANIMALS)
async def create_log(data: HusbandryLogCreate, db: db_dependency, user: user_dependency):
    _validate(db, data)
    log = HusbandryLog(**data.model_dump(), user_id=user["id"])
    db.add(log)
    db.commit()
    return _get(db, log.id)


@router.put("/{log_id}", response_model=HusbandryLogResponse, dependencies=CAN_UPDATE_ANIMALS)
async def update_log(log_id: int, data: HusbandryLogUpdate, db: db_dependency):
    log = _get(db, log_id)
    _validate(db, data)
    for k, v in data.model_dump().items():
        setattr(log, k, v)
    db.commit()
    db.expire_all()
    return _get(db, log_id)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=CAN_UPDATE_ANIMALS)
async def delete_log(log_id: int, db: db_dependency):
    db.delete(_get(db, log_id))
    db.commit()
