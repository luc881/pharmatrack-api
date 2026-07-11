"""CRUD de taxonomía de animales: géneros, especies y morphs."""
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import Genus, Species, Morph, Animal, animal_has_morphs
from ...models.animals.schemas import (
    GenusCreate, GenusUpdate, GenusResponse,
    SpeciesCreate, SpeciesUpdate, SpeciesResponse,
    MorphCreate, MorphUpdate, MorphResponse,
)
from ...utils.permissions import (
    CAN_READ_GENERA, CAN_CREATE_GENERA, CAN_UPDATE_GENERA, CAN_DELETE_GENERA,
    CAN_READ_SPECIES, CAN_CREATE_SPECIES, CAN_UPDATE_SPECIES, CAN_DELETE_SPECIES,
    CAN_READ_MORPHS, CAN_CREATE_MORPHS, CAN_UPDATE_MORPHS, CAN_DELETE_MORPHS,
)
from pharmatrack.utils.pagination import paginate, PaginationParams, PaginatedResponse


genera_router = APIRouter(prefix="/genera", tags=["Animal Taxonomy"])
species_router = APIRouter(prefix="/species", tags=["Animal Taxonomy"])
morphs_router = APIRouter(prefix="/morphs", tags=["Animal Taxonomy"])


# =========================================================
# Genera
# =========================================================
@genera_router.get("", response_model=PaginatedResponse[GenusResponse],
                   summary="List genera", dependencies=CAN_READ_GENERA)
async def list_genera(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Genus).order_by(Genus.name.asc())
    return paginate(query, pagination)


@genera_router.get("/{genus_id}", response_model=GenusResponse,
                   summary="Get genus by ID", dependencies=CAN_READ_GENERA)
async def get_genus(genus_id: int, db: db_dependency):
    genus = db.get(Genus, genus_id)
    if not genus:
        raise HTTPException(status_code=404, detail="Genus not found.")
    return genus


@genera_router.post("", response_model=GenusResponse, status_code=status.HTTP_201_CREATED,
                    summary="Create a genus", dependencies=CAN_CREATE_GENERA)
async def create_genus(payload: GenusCreate, db: db_dependency):
    if db.query(Genus).filter(Genus.name == payload.name).first():
        raise HTTPException(status_code=400, detail="A genus with this name already exists.")
    genus = Genus(**payload.model_dump())
    db.add(genus)
    db.commit()
    db.refresh(genus)
    return genus


@genera_router.put("/{genus_id}", response_model=GenusResponse,
                   summary="Update a genus", dependencies=CAN_UPDATE_GENERA)
async def update_genus(genus_id: int, payload: GenusUpdate, db: db_dependency):
    genus = db.get(Genus, genus_id)
    if not genus:
        raise HTTPException(status_code=404, detail="Genus not found.")

    if payload.name is not None:
        conflict = db.query(Genus).filter(Genus.name == payload.name, Genus.id != genus_id).first()
        if conflict:
            raise HTTPException(status_code=400, detail="A genus with this name already exists.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(genus, key, value)
    db.commit()
    db.refresh(genus)
    return genus


@genera_router.delete("/{genus_id}", status_code=status.HTTP_204_NO_CONTENT,
                      summary="Delete a genus", dependencies=CAN_DELETE_GENERA)
async def delete_genus(genus_id: int, db: db_dependency):
    genus = db.get(Genus, genus_id)
    if not genus:
        raise HTTPException(status_code=404, detail="Genus not found.")
    if db.query(Species.id).filter(Species.genus_id == genus_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete a genus that has species.")
    db.delete(genus)
    db.commit()


# =========================================================
# Species
# =========================================================
@species_router.get("", response_model=PaginatedResponse[SpeciesResponse],
                    summary="List species", dependencies=CAN_READ_SPECIES)
async def list_species(db: db_dependency, genus_id: Optional[int] = None,
                       pagination: PaginationParams = Depends()):
    query = db.query(Species)
    if genus_id is not None:
        query = query.filter(Species.genus_id == genus_id)
    return paginate(query.order_by(Species.name.asc()), pagination)


@species_router.get("/{species_id}", response_model=SpeciesResponse,
                    summary="Get species by ID", dependencies=CAN_READ_SPECIES)
async def get_species(species_id: int, db: db_dependency):
    species = db.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found.")
    return species


@species_router.post("", response_model=SpeciesResponse, status_code=status.HTTP_201_CREATED,
                     summary="Create a species", dependencies=CAN_CREATE_SPECIES)
async def create_species(payload: SpeciesCreate, db: db_dependency):
    if not db.get(Genus, payload.genus_id):
        raise HTTPException(status_code=400, detail="Genus not found.")
    conflict = db.query(Species).filter(
        Species.genus_id == payload.genus_id, Species.name == payload.name
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="A species with this name already exists in this genus.")
    species = Species(**payload.model_dump())
    db.add(species)
    db.commit()
    db.refresh(species)
    return species


@species_router.put("/{species_id}", response_model=SpeciesResponse,
                    summary="Update a species", dependencies=CAN_UPDATE_SPECIES)
async def update_species(species_id: int, payload: SpeciesUpdate, db: db_dependency):
    species = db.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found.")

    if payload.genus_id is not None and not db.get(Genus, payload.genus_id):
        raise HTTPException(status_code=400, detail="Genus not found.")

    final_genus_id = payload.genus_id if payload.genus_id is not None else species.genus_id
    final_name = payload.name if payload.name is not None else species.name
    conflict = db.query(Species).filter(
        Species.genus_id == final_genus_id,
        Species.name == final_name,
        Species.id != species_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="A species with this name already exists in this genus.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(species, key, value)
    db.commit()
    db.refresh(species)
    return species


@species_router.delete("/{species_id}", status_code=status.HTTP_204_NO_CONTENT,
                       summary="Delete a species", dependencies=CAN_DELETE_SPECIES)
async def delete_species(species_id: int, db: db_dependency):
    species = db.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found.")
    if db.query(Morph.id).filter(Morph.species_id == species_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete a species that has morphs.")
    if db.query(Animal.id).filter(Animal.species_id == species_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete a species that has animals.")
    db.delete(species)
    db.commit()


# =========================================================
# Morphs
# =========================================================
@morphs_router.get("", response_model=PaginatedResponse[MorphResponse],
                   summary="List morphs", dependencies=CAN_READ_MORPHS)
async def list_morphs(db: db_dependency, species_id: Optional[int] = None,
                      pagination: PaginationParams = Depends()):
    query = db.query(Morph)
    if species_id is not None:
        query = query.filter(Morph.species_id == species_id)
    return paginate(query.order_by(Morph.name.asc()), pagination)


@morphs_router.get("/{morph_id}", response_model=MorphResponse,
                   summary="Get morph by ID", dependencies=CAN_READ_MORPHS)
async def get_morph(morph_id: int, db: db_dependency):
    morph = db.get(Morph, morph_id)
    if not morph:
        raise HTTPException(status_code=404, detail="Morph not found.")
    return morph


@morphs_router.post("", response_model=MorphResponse, status_code=status.HTTP_201_CREATED,
                    summary="Create a morph", dependencies=CAN_CREATE_MORPHS)
async def create_morph(payload: MorphCreate, db: db_dependency):
    if not db.get(Species, payload.species_id):
        raise HTTPException(status_code=400, detail="Species not found.")
    conflict = db.query(Morph).filter(
        Morph.species_id == payload.species_id, Morph.name == payload.name
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="A morph with this name already exists for this species.")
    morph = Morph(**payload.model_dump())
    db.add(morph)
    db.commit()
    db.refresh(morph)
    return morph


@morphs_router.put("/{morph_id}", response_model=MorphResponse,
                   summary="Update a morph", dependencies=CAN_UPDATE_MORPHS)
async def update_morph(morph_id: int, payload: MorphUpdate, db: db_dependency):
    morph = db.get(Morph, morph_id)
    if not morph:
        raise HTTPException(status_code=404, detail="Morph not found.")

    if payload.species_id is not None and not db.get(Species, payload.species_id):
        raise HTTPException(status_code=400, detail="Species not found.")

    final_species_id = payload.species_id if payload.species_id is not None else morph.species_id
    final_name = payload.name if payload.name is not None else morph.name
    conflict = db.query(Morph).filter(
        Morph.species_id == final_species_id,
        Morph.name == final_name,
        Morph.id != morph_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="A morph with this name already exists for this species.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(morph, key, value)
    db.commit()
    db.refresh(morph)
    return morph


@morphs_router.delete("/{morph_id}", status_code=status.HTTP_204_NO_CONTENT,
                      summary="Delete a morph", dependencies=CAN_DELETE_MORPHS)
async def delete_morph(morph_id: int, db: db_dependency):
    morph = db.get(Morph, morph_id)
    if not morph:
        raise HTTPException(status_code=404, detail="Morph not found.")
    in_use = db.query(animal_has_morphs).filter(animal_has_morphs.c.morph_id == morph_id).first()
    if in_use:
        raise HTTPException(status_code=400, detail="Cannot delete a morph assigned to animals.")
    db.delete(morph)
    db.commit()
