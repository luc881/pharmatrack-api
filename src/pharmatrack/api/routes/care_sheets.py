"""Fichas de cuidados: CRUD admin + endpoints públicos (/fichas del sitio).

Una ficha por especie. El público ve solo las publicadas, de cualquier grupo
(también de los ocultos en el catálogo: una ficha no vende nada).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import Animal, Genus, Species
from ...models.care_sheets.orm import CareSheet
from ...models.care_sheets.schemas import (
    CareSheetCreate, CareSheetResponse, CareSheetSummary, CareSheetUpdate,
)
from ...utils.permissions import (
    CAN_CREATE_SPECIES, CAN_DELETE_SPECIES, CAN_READ_SPECIES, CAN_UPDATE_SPECIES,
)
from ...utils.slugify import slugify
from pharmatrack.types.animals import AnimalStatusEnum

router = APIRouter(prefix="/care-sheets", tags=["Care sheets"])
public_router = APIRouter(prefix="/public/care-sheets", tags=["Public"])


def _query(db: Session):
    return db.query(CareSheet).options(
        joinedload(CareSheet.species).joinedload(Species.genus).joinedload(Genus.group)
    )


def _get(db: Session, sheet_id: int) -> CareSheet:
    sheet = _query(db).filter(CareSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Ficha no encontrada.")
    return sheet


def _summary(sheet: CareSheet, available: int = 0) -> CareSheetSummary:
    return CareSheetSummary.model_validate({
        **{k: getattr(sheet, k) for k in (
            "id", "slug", "species_id", "scientific_name", "locality", "common_name", "group",
            "difficulty", "summary", "published", "published_at", "updated_at",
        )},
        "cover": (sheet.photos or [{}])[0].get("src"),
        "available_count": available,
    })


def _save(db: Session, sheet: CareSheet, data: dict, published: bool):
    """Valida especie y slug únicos y aplica los campos."""
    species = db.get(Species, data["species_id"])
    if not species:
        raise HTTPException(status_code=404, detail="Especie no encontrada.")
    if not data.get("slug"):
        data["slug"] = slugify(f"{species.genus.name} {species.name}")
    taken = db.query(CareSheet).filter(CareSheet.id != sheet.id)
    if taken.filter(CareSheet.species_id == data["species_id"]).first():
        raise HTTPException(status_code=409, detail="Esa especie ya tiene ficha.")
    if taken.filter(CareSheet.slug == data["slug"]).first():
        raise HTTPException(status_code=409, detail="Ya hay una ficha con esa dirección (slug).")
    for k, v in data.items():
        setattr(sheet, k, v)
    if published and sheet.published_at is None:
        sheet.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    elif not published:
        sheet.published_at = None


def _dump(payload) -> dict:
    # las listas anidadas se guardan como JSON plano
    return payload.model_dump(exclude={"published"}, mode="json")


# =========================================================
# Admin
# =========================================================
@router.get("", response_model=list[CareSheetSummary], dependencies=CAN_READ_SPECIES,
            summary="Fichas (incluye borradores)")
async def list_sheets(db: db_dependency):
    return [_summary(s) for s in _query(db).order_by(CareSheet.updated_at.desc()).all()]


@router.get("/{sheet_id}", response_model=CareSheetResponse, dependencies=CAN_READ_SPECIES)
async def get_sheet(sheet_id: int, db: db_dependency):
    return _get(db, sheet_id)


@router.post("", response_model=CareSheetResponse, status_code=status.HTTP_201_CREATED,
             dependencies=CAN_CREATE_SPECIES)
async def create_sheet(payload: CareSheetCreate, db: db_dependency):
    sheet = CareSheet()
    _save(db, sheet, _dump(payload), payload.published)
    db.add(sheet)
    db.commit()
    return _get(db, sheet.id)


@router.put("/{sheet_id}", response_model=CareSheetResponse, dependencies=CAN_UPDATE_SPECIES)
async def update_sheet(sheet_id: int, payload: CareSheetUpdate, db: db_dependency):
    sheet = _get(db, sheet_id)
    _save(db, sheet, _dump(payload), payload.published)
    db.commit()
    return _get(db, sheet.id)


@router.delete("/{sheet_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=CAN_DELETE_SPECIES)
async def delete_sheet(sheet_id: int, db: db_dependency):
    db.delete(_get(db, sheet_id))
    db.commit()


# =========================================================
# Público (sin auth): solo publicadas
# =========================================================
@public_router.get("", response_model=list[CareSheetSummary], summary="Fichas publicadas (índice)")
async def public_list_sheets(db: db_dependency):
    sheets = _query(db).filter(CareSheet.published_at.isnot(None)).all()
    # ejemplares disponibles por especie, para «en venta» en el índice
    counts = dict(
        db.query(Animal.species_id, func.count(Animal.id))
        .filter(Animal.species_id.in_([s.species_id for s in sheets]),
                Animal.status == AnimalStatusEnum.AVAILABLE.value)
        .group_by(Animal.species_id)
        .all()
    ) if sheets else {}
    rows = [_summary(s, counts.get(s.species_id, 0)) for s in sheets]
    return sorted(rows, key=lambda r: r.scientific_name)


@public_router.get("/{slug}", response_model=CareSheetResponse, summary="Ficha publicada")
async def public_get_sheet(slug: str, db: db_dependency):
    sheet: Optional[CareSheet] = (
        _query(db).filter(CareSheet.slug == slug, CareSheet.published_at.isnot(None)).first()
    )
    if not sheet:
        raise HTTPException(status_code=404, detail="Ficha no encontrada.")
    return sheet
