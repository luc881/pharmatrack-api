"""Bitácora del plan de manejo de especies (alimentación, suplementos,
actividades, bajas y notas) y el resumen de qué toca según el plan."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import Animal, Morph, Species
from ...models.husbandry_logs.orm import HusbandryLog
from ...models.husbandry_logs.schemas import (
    HusbandryLogCreate, HusbandryLogResponse, HusbandryLogUpdate, HusbandryStatus,
)
from ...models.product_batch.orm import ProductBatch
from ...utils.permissions import CAN_READ_ANIMALS, CAN_UPDATE_ANIMALS
from ...utils.security import user_dependency
from pharmatrack.types.animals import AnimalStatusEnum
from pharmatrack.utils.pagination import PaginatedResponse, PaginationParams, paginate

router = APIRouter(prefix="/husbandry-logs", tags=["Husbandry logs"])

# ponytail: CDMX es UTC-6 todo el año desde 2022 (sin horario de verano)
CDMX = timezone(timedelta(hours=-6))

# ponytail: el resumen mira los últimos 180 días; un plan "cada 6 meses" sin
# registro más reciente se ve como "nunca" (toca hoy).
STATUS_WINDOW_DAYS = 180


def today_mx() -> date:
    return datetime.now(CDMX).date()


def _query(db: Session):
    return db.query(HusbandryLog).options(
        joinedload(HusbandryLog.species).joinedload(Species.genus),
        joinedload(HusbandryLog.morph),
        joinedload(HusbandryLog.user),
        joinedload(HusbandryLog.animal),
    )


def _validate(db: Session, data: HusbandryLogCreate):
    if not db.get(Species, data.species_id):
        raise HTTPException(status_code=404, detail="Species not found.")
    if data.morph_id:
        morph = db.get(Morph, data.morph_id)
        if not morph or morph.species_id != data.species_id:
            raise HTTPException(status_code=400, detail="Morph does not belong to the species.")
    if data.animal_id:
        animal = db.get(Animal, data.animal_id)
        if not animal or animal.species_id != data.species_id:
            raise HTTPException(status_code=400, detail="Animal does not belong to the species.")


def _get(db: Session, log_id: int) -> HusbandryLog:
    log = _query(db).filter(HusbandryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found.")
    return log


# =========================================================
# Bajas ↔ inventario
# =========================================================
def _batches(db: Session, animal: Animal) -> list[ProductBatch]:
    return (
        db.query(ProductBatch)
        .filter(ProductBatch.product_id == animal.product_id)
        .order_by(ProductBatch.id)
        .all()
    )


def _sync_status(animal: Animal, batches: list[ProductBatch], died: bool = False):
    # Bajas que dejan el stock en 0: murió (no «vendido»). Si vuelve a haber
    # (se borró o corrigió la baja), regresa a la venta.
    left = sum(b.quantity for b in batches)
    if left == 0:
        if died:
            animal.status = AnimalStatusEnum.DECEASED.value
    elif animal.status in (AnimalStatusEnum.SOLD.value, AnimalStatusEnum.DECEASED.value):
        animal.status = AnimalStatusEnum.AVAILABLE.value


def _deduct(db: Session, log: HusbandryLog):
    """Descuenta las bajas del inventario del ejemplar/cepa elegido (lotes más
    viejos primero). No deja descontar más de lo que hay."""
    if not (log.deaths and log.animal_id):
        return
    animal = db.get(Animal, log.animal_id)
    batches = _batches(db, animal)
    if log.deaths > sum(b.quantity for b in batches):
        raise HTTPException(status_code=400, detail="Deaths exceed the animal's stock.")
    remaining = log.deaths
    for b in batches:
        take = min(b.quantity, remaining)
        b.quantity -= take
        remaining -= take
    log.stock_deducted = log.deaths
    _sync_status(animal, batches, died=True)


def _restore(db: Session, log: HusbandryLog):
    """Regresa al inventario lo que esta entrada descontó."""
    if not (log.stock_deducted and log.animal_id):
        log.stock_deducted = 0
        return
    animal = db.get(Animal, log.animal_id)
    batches = _batches(db, animal)
    if batches:
        batches[0].quantity += log.stock_deducted
    else:
        db.add(ProductBatch(product_id=animal.product_id, quantity=log.stock_deducted,
                            purchase_price=animal.price_cost))
        db.flush()
        batches = _batches(db, animal)
    log.stock_deducted = 0
    _sync_status(animal, batches)


# =========================================================
# Resumen del plan
# =========================================================
def _norm(s: Optional[str]) -> str:
    return " ".join((s or "").lower().split())


def _done_by(item: dict, log: HusbandryLog) -> bool:
    if item["kind"] == "supplement":
        return bool(log.supplement) and _norm(log.supplement) == _norm(item["name"])
    # Comida: la palomita sin alimento cuenta para cualquier comida del plan
    return log.fed and (not log.food_type or _norm(log.food_type) == _norm(item["name"]))


def build_status(species_list: list[Species], logs: list[HusbandryLog], today: date) -> list[dict]:
    by_species: dict[int, list[HusbandryLog]] = {}
    for log in logs:  # vienen de la más nueva a la más vieja
        by_species.setdefault(log.species_id, []).append(log)

    month_start = today.replace(day=1)
    out = []
    for sp in species_list:
        sp_logs = by_species.get(sp.id, [])
        plan = []
        for item in sp.husbandry_plan or []:
            last = next((l.log_date for l in sp_logs if _done_by(item, l)), None)
            next_due = last + timedelta(days=item["every_days"]) if last else today
            plan.append({**item, "last_done": last, "next_due": next_due,
                         "days_overdue": (today - next_due).days})
        month_logs = [l for l in sp_logs if l.log_date >= month_start]
        acts = [a for l in month_logs for a in (l.activities or [])]
        out.append({
            "species_id": sp.id,
            "species_name": f"{sp.genus.name} {sp.name}" if sp.genus else sp.name,
            "common_name": sp.common_name,
            "last_fed": next((l.log_date for l in sp_logs if l.fed), None),
            "plan": sorted(plan, key=lambda p: -p["days_overdue"]),
            "month": {
                "entries": len(month_logs),
                "feedings": sum(1 for l in month_logs if l.fed),
                "molt": acts.count("molt"),
                "eggs": acts.count("eggs"),
                "births": acts.count("births"),
                "deaths": sum(l.deaths or 0 for l in month_logs),
            },
        })
    return out


# =========================================================
# Rutas
# =========================================================
@router.get("/status", response_model=list[HusbandryStatus], dependencies=CAN_READ_ANIMALS)
async def plan_status(db: db_dependency, species_id: Optional[int] = Query(None, gt=0)):
    """Una fila por especie con plan (o la pedida): próxima fecha de cada
    renglón del plan, última comida y conteos del mes. Sin species_id solo
    entran las especies en cultivo que tienen plan."""
    q = db.query(Species).options(joinedload(Species.genus))
    if species_id:
        q = q.filter(Species.id == species_id)
    else:
        q = q.filter(Species.husbandry_status == "active")
    species_list = [s for s in q.all() if species_id or s.husbandry_plan]
    if not species_list:
        return []

    today = today_mx()
    logs = (
        db.query(HusbandryLog)
        .filter(HusbandryLog.species_id.in_([s.id for s in species_list]),
                HusbandryLog.log_date >= today - timedelta(days=STATUS_WINDOW_DAYS))
        .order_by(HusbandryLog.log_date.desc(), HusbandryLog.id.desc())
        .all()
    )
    rows = build_status(species_list, logs, today)
    return sorted(rows, key=lambda r: -max((p["days_overdue"] for p in r["plan"]), default=-999))


@router.get("", response_model=PaginatedResponse[HusbandryLogResponse], dependencies=CAN_READ_ANIMALS)
async def list_logs(
    db: db_dependency,
    species_id: Optional[int] = Query(None, gt=0),
    morph_id: Optional[int] = Query(None, gt=0),
    animal_id: Optional[int] = Query(None, gt=0),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    pagination: PaginationParams = Depends(),
):
    q = _query(db)
    if species_id:
        q = q.filter(HusbandryLog.species_id == species_id)
    if morph_id:
        q = q.filter(HusbandryLog.morph_id == morph_id)
    if animal_id:
        q = q.filter(HusbandryLog.animal_id == animal_id)
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
    _deduct(db, log)
    db.commit()
    return _get(db, log.id)


@router.put("/{log_id}", response_model=HusbandryLogResponse, dependencies=CAN_UPDATE_ANIMALS)
async def update_log(log_id: int, data: HusbandryLogUpdate, db: db_dependency):
    log = _get(db, log_id)
    _validate(db, data)
    _restore(db, log)
    for k, v in data.model_dump().items():
        setattr(log, k, v)
    _deduct(db, log)
    db.commit()
    db.expire_all()
    return _get(db, log_id)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=CAN_UPDATE_ANIMALS)
async def delete_log(log_id: int, db: db_dependency):
    log = _get(db, log_id)
    _restore(db, log)
    db.delete(log)
    db.commit()
