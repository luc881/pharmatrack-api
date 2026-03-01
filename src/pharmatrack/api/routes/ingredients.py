from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from ...db.session import get_db
from starlette import status
from ...models.ingredients.orm import Ingredient
from ...models.ingredients.schemas import (
    IngredientCreate,
    IngredientResponse,
    IngredientUpdate,
    PaginatedResponse,
    PaginationParams,
)
from ...utils.permissions import CAN_READ_INGREDIENTS, CAN_CREATE_INGREDIENTS, CAN_UPDATE_INGREDIENTS, CAN_DELETE_INGREDIENTS
from pharmatrack.utils.pagination import paginate

db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/ingredients",
    tags=["Ingredients"]
)


@router.get("/",
            response_model=PaginatedResponse[IngredientResponse],
            summary="List all ingredients",
            description="Retrieve all ingredients currently stored in the database.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_READ_INGREDIENTS)
async def read_all(db: db_dependency, pagination: PaginationParams = Depends()):
    query = db.query(Ingredient).order_by(Ingredient.name.asc())
    return paginate(query, pagination)


@router.post("/",
            response_model=IngredientResponse,
            summary="Create a new ingredient",
            description="Create a new ingredient with the provided details.",
            status_code=status.HTTP_201_CREATED,
            dependencies=CAN_CREATE_INGREDIENTS)
async def create(ingredient: IngredientCreate, db: db_dependency):
    # Check duplicates by slug (handles accent/case variants)
    existing = db.query(Ingredient).filter(Ingredient.slug == ingredient.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ingredient with this name already exists."
        )

    # model_dump includes slug because we need to persist it
    db_ingredient = Ingredient(**ingredient.model_dump())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


@router.put("/{ingredient_id}",
            response_model=IngredientResponse,
            summary="Update an existing ingredient",
            description="Update the details of an existing ingredient by its ID.",
            status_code=status.HTTP_200_OK,
            dependencies=CAN_UPDATE_INGREDIENTS)
async def update(ingredient_id: int, ingredient: IngredientUpdate, db: db_dependency):
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found."
        )

    # If name changed, check slug conflict against other records
    if ingredient.slug and ingredient.slug != db_ingredient.slug:
        existing = db.query(Ingredient).filter(
            Ingredient.slug == ingredient.slug,
            Ingredient.id != ingredient_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ingredient with this name already exists."
            )

    for key, value in ingredient.model_dump(exclude_unset=True).items():
        setattr(db_ingredient, key, value)

    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient


@router.delete("/{ingredient_id}",
            summary="Delete an ingredient",
            description="Delete an existing ingredient by its ID.",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=CAN_DELETE_INGREDIENTS)
async def delete(ingredient_id: int, db: db_dependency):
    db_ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found."
        )

    db.delete(db_ingredient)
    db.commit()
    return None