"""CRUD de taxonomía de animales: géneros, especies y morphs."""
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from starlette import status

from ...db.session import db_dependency
from ...models.animals.orm import AnimalGroup, Genus, Species, Morph, Animal, animal_has_morphs
from ...models.animals.schemas import (
    SpeciesAdminResponse,
    AnimalGroupCreate, AnimalGroupUpdate, AnimalGroupResponse, AnimalGroupTreeResponse,
    GenusCreate, GenusUpdate, GenusResponse,
    SpeciesCreate, SpeciesUpdate, SpeciesResponse,
    MorphCreate, MorphUpdate, MorphResponse, MorphAdminResponse,
)
from ...utils.permissions import (
    CAN_READ_ANIMAL_GROUPS, CAN_CREATE_ANIMAL_GROUPS, CAN_UPDATE_ANIMAL_GROUPS, CAN_DELETE_ANIMAL_GROUPS,
    CAN_READ_GENERA, CAN_CREATE_GENERA, CAN_UPDATE_GENERA, CAN_DELETE_GENERA,
    CAN_READ_SPECIES, CAN_CREATE_SPECIES, CAN_UPDATE_SPECIES, CAN_DELETE_SPECIES,
    CAN_READ_MORPHS, CAN_CREATE_MORPHS, CAN_UPDATE_MORPHS, CAN_DELETE_MORPHS,
)
from pharmatrack.utils.pagination import paginate, PaginationParams, PaginatedResponse


groups_router = APIRouter(prefix="/animal-groups", tags=["Animal Taxonomy"])
genera_router = APIRouter(prefix="/genera", tags=["Animal Taxonomy"])
species_router = APIRouter(prefix="/species", tags=["Animal Taxonomy"])
morphs_router = APIRouter(prefix="/morphs", tags=["Animal Taxonomy"])


# =========================================================
# Animal groups (árbol recursivo, patrón product_categories)
# =========================================================
def _build_group_tree(groups: list[AnimalGroup], parent_id: Optional[int] = None) -> list[dict]:
    """Arbol de grupos.

    Los campos se copian desde el ORM en vez de listarlos a mano: al armar el
    dict campo por campo, show_public y feature_home se quedaban fuera y
    Pydantic los rellenaba con su default — el dashboard veia todo como no
    destacado aunque en la BD estuviera marcado.
    """
    return [
        {
            **{c.name: getattr(g, c.name) for c in AnimalGroup.__table__.columns},
            "children": _build_group_tree(groups, g.id),
        }
        for g in groups
        if g.parent_id == parent_id
    ]


def _check_group_cycle(db, group_id: int, new_parent_id: Optional[int]):
    current = new_parent_id
    while current is not None:
        if current == group_id:
            raise HTTPException(status_code=400, detail="Animal group cycle detected.")
        parent = db.get(AnimalGroup, current)
        if not parent:
            break
        current = parent.parent_id


def descendant_group_ids(db, root_id: int) -> set[int]:
    """IDs del grupo raíz y todos sus descendientes."""
    # ponytail: tabla chica, se resuelve en memoria; CTE recursivo si crece a miles
    rows = db.query(AnimalGroup.id, AnimalGroup.parent_id).all()
    children: dict[Optional[int], list[int]] = {}
    for gid, pid in rows:
        children.setdefault(pid, []).append(gid)
    ids, stack = set(), [root_id]
    while stack:
        current = stack.pop()
        ids.add(current)
        stack.extend(children.get(current, []))
    return ids


def hidden_group_ids(db) -> set[int]:
    """IDs de grupos ocultos al publico: los que tienen show_public=False y
    todos sus descendientes (ocultar un raiz oculta su subarbol)."""
    rows = db.query(AnimalGroup.id, AnimalGroup.parent_id, AnimalGroup.show_public).all()
    children: dict = {}
    hidden_roots = []
    for gid, pid, show in rows:
        children.setdefault(pid, []).append(gid)
        if not show:
            hidden_roots.append(gid)
    ids, stack = set(), list(hidden_roots)
    while stack:
        current = stack.pop()
        if current in ids:
            continue
        ids.add(current)
        stack.extend(children.get(current, []))
    return ids


@groups_router.get("", response_model=PaginatedResponse[AnimalGroupResponse],
                   summary="List animal groups", dependencies=CAN_READ_ANIMAL_GROUPS)
async def list_groups(db: db_dependency, parent_id: Optional[int] = None,
                      pagination: PaginationParams = Depends()):
    query = db.query(AnimalGroup)
    if parent_id is not None:
        query = query.filter(AnimalGroup.parent_id == parent_id)
    return paginate(query.order_by(AnimalGroup.name.asc()), pagination)


@groups_router.get("/tree", response_model=list[AnimalGroupTreeResponse],
                   summary="Get full animal group tree", dependencies=CAN_READ_ANIMAL_GROUPS)
async def get_group_tree(db: db_dependency):
    groups = db.query(AnimalGroup).order_by(AnimalGroup.name.asc()).all()
    return _build_group_tree(groups)


@groups_router.get("/{group_id}", response_model=AnimalGroupResponse,
                   summary="Get animal group by ID", dependencies=CAN_READ_ANIMAL_GROUPS)
async def get_group(group_id: int, db: db_dependency):
    group = db.get(AnimalGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Animal group not found.")
    return group


@groups_router.post("", response_model=AnimalGroupResponse, status_code=status.HTTP_201_CREATED,
                    summary="Create an animal group", dependencies=CAN_CREATE_ANIMAL_GROUPS)
async def create_group(payload: AnimalGroupCreate, db: db_dependency):
    if payload.parent_id is not None and not db.get(AnimalGroup, payload.parent_id):
        raise HTTPException(status_code=400, detail="Parent animal group not found.")
    conflict = db.query(AnimalGroup).filter(
        AnimalGroup.parent_id == payload.parent_id, AnimalGroup.name == payload.name
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="An animal group with this name already exists at this level.")
    group = AnimalGroup(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@groups_router.put("/{group_id}", response_model=AnimalGroupResponse,
                   summary="Update an animal group", dependencies=CAN_UPDATE_ANIMAL_GROUPS)
async def update_group(group_id: int, payload: AnimalGroupUpdate, db: db_dependency):
    group = db.get(AnimalGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Animal group not found.")

    if payload.parent_id is not None:
        if payload.parent_id == group_id:
            raise HTTPException(status_code=400, detail="Animal group cannot be its own parent.")
        if not db.get(AnimalGroup, payload.parent_id):
            raise HTTPException(status_code=400, detail="Parent animal group not found.")
        _check_group_cycle(db, group_id, payload.parent_id)

    final_parent_id = payload.parent_id if payload.parent_id is not None else group.parent_id
    final_name = payload.name if payload.name is not None else group.name
    conflict = db.query(AnimalGroup).filter(
        AnimalGroup.parent_id == final_parent_id,
        AnimalGroup.name == final_name,
        AnimalGroup.id != group_id,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="An animal group with this name already exists at this level.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


@groups_router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT,
                      summary="Delete an animal group", dependencies=CAN_DELETE_ANIMAL_GROUPS)
async def delete_group(group_id: int, db: db_dependency):
    group = db.get(AnimalGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Animal group not found.")
    if db.query(AnimalGroup.id).filter(AnimalGroup.parent_id == group_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete an animal group that has subgroups.")
    if db.query(Genus.id).filter(Genus.group_id == group_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete an animal group that has genera.")
    db.delete(group)
    db.commit()


# =========================================================
# Genera
# =========================================================
@genera_router.get("", response_model=PaginatedResponse[GenusResponse],
                   summary="List genera", dependencies=CAN_READ_GENERA)
async def list_genera(db: db_dependency, group_id: Optional[int] = None,
                      pagination: PaginationParams = Depends()):
    query = db.query(Genus)
    if group_id is not None:
        query = query.filter(Genus.group_id.in_(descendant_group_ids(db, group_id)))
    return paginate(query.order_by(Genus.name.asc()), pagination)


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
    if payload.group_id is not None and not db.get(AnimalGroup, payload.group_id):
        raise HTTPException(status_code=400, detail="Animal group not found.")
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

    if payload.group_id is not None and not db.get(AnimalGroup, payload.group_id):
        raise HTTPException(status_code=400, detail="Animal group not found.")

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
@species_router.get("", response_model=PaginatedResponse[SpeciesAdminResponse],
                    summary="List species", dependencies=CAN_READ_SPECIES)
async def list_species(db: db_dependency, genus_id: Optional[int] = None,
                       pagination: PaginationParams = Depends()):
    query = db.query(Species)
    if genus_id is not None:
        query = query.filter(Species.genus_id == genus_id)
    return paginate(query.order_by(Species.name.asc()), pagination)


@species_router.get("/{species_id}", response_model=SpeciesAdminResponse,
                    summary="Get species by ID", dependencies=CAN_READ_SPECIES)
async def get_species(species_id: int, db: db_dependency):
    species = db.get(Species, species_id)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found.")
    return species


@species_router.post("", response_model=SpeciesAdminResponse, status_code=status.HTTP_201_CREATED,
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


@species_router.put("/{species_id}", response_model=SpeciesAdminResponse,
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
@morphs_router.get("", response_model=PaginatedResponse[MorphAdminResponse],
                   summary="List morphs", dependencies=CAN_READ_MORPHS)
async def list_morphs(db: db_dependency, species_id: Optional[int] = None,
                      pagination: PaginationParams = Depends()):
    query = db.query(Morph)
    if species_id is not None:
        query = query.filter(Morph.species_id == species_id)
    return paginate(query.order_by(Morph.name.asc()), pagination)


@morphs_router.get("/{morph_id}", response_model=MorphAdminResponse,
                   summary="Get morph by ID", dependencies=CAN_READ_MORPHS)
async def get_morph(morph_id: int, db: db_dependency):
    morph = db.get(Morph, morph_id)
    if not morph:
        raise HTTPException(status_code=404, detail="Morph not found.")
    return morph


@morphs_router.post("", response_model=MorphAdminResponse, status_code=status.HTTP_201_CREATED,
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


@morphs_router.put("/{morph_id}", response_model=MorphAdminResponse,
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
