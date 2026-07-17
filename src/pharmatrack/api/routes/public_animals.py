"""Catálogo público de la tienda: solo lectura, sin autenticación.

El listado expone únicamente animales disponibles; el detalle responde
también reservados/vendidos (con su status) para que un link compartido
muestre "ya no disponible" en lugar de un 404. Los campos internos
(costos, producto gemelo, documentación legal) los recorta
PublicAnimalResponse.
"""
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter

from ...db.session import db_dependency
from ...models.animals.orm import Animal
from ...models.animals.schemas import PublicAnimalResponse
from .animals import list_animals, _query_with_relations
from pharmatrack.types.animals import AnimalStatusEnum
from pharmatrack.utils.pagination import PaginationParams, PaginatedResponse


router = APIRouter(prefix="/public/animals", tags=["Public"])


@router.get("", response_model=PaginatedResponse[PublicAnimalResponse],
            summary="Public: list animals for sale")
async def public_list_animals(
    db: db_dependency,
    species_id: Optional[int] = None,
    genus_id: Optional[int] = None,
    group_id: Optional[int] = None,
    pagination: PaginationParams = Depends(),
):
    # ponytail: reutiliza el listado interno; response_model recorta lo privado
    return await list_animals(
        db=db, species_id=species_id, genus_id=genus_id, group_id=group_id,
        animal_status=AnimalStatusEnum.AVAILABLE, pagination=pagination,
    )


@router.get("/{animal_id}", response_model=PublicAnimalResponse,
            summary="Public: animal detail")
async def public_get_animal(animal_id: int, db: db_dependency):
    animal = _query_with_relations(db).filter(Animal.id == animal_id).first()
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found.")
    return animal
