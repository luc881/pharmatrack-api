from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status

from ...db.session import get_db
from ...models.sales.schemas import SaleCreate, SaleResponse, SaleUpdate
from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...utils.permissions import (
    CAN_READ_SALES,
    CAN_CREATE_SALES,
    CAN_UPDATE_SALES,
    CAN_DELETE_SALES,
)

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)

VALID_SALE_STATUS = {"draft", "completed", "cancelled", "refunded"}


# -----------------------
# GET ALL
# -----------------------
@router.get(
    "/",
    response_model=list[SaleResponse],
    summary="List all sales",
    description="Retrieve all sales currently stored in the database.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
async def read_all(db: db_dependency):
    return db.query(Sale).all()


# -----------------------
# CREATE
# -----------------------
@router.post(
    "/",
    response_model=SaleResponse,
    summary="Create a new sale",
    description="Create a new sale with the provided details.",
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALES,
)
async def create(
    sale: SaleCreate,
    db: db_dependency,
):
    # Validate user exists
    if not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID does not exist.",
        )

    # Validate branch exists
    if not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch ID does not exist.",
        )

    # Validate status
    if sale.status not in VALID_SALE_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sale status.",
        )

    new_sale = Sale(**sale.model_dump())
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    return new_sale


# -----------------------
# UPDATE
# -----------------------
@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Update a sale",
    description="Update an existing sale with the provided details.",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
async def update(
    sale_id: int,
    sale: SaleUpdate,
    db: db_dependency,
):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found.",
        )

    # Validate user exists
    if sale.user_id and not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID does not exist.",
        )

    # Validate branch exists
    if sale.branch_id and not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch ID does not exist.",
        )

    # Validate status if provided
    if sale.status and sale.status not in VALID_SALE_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sale status.",
        )

    for key, value in sale.model_dump(exclude_unset=True).items():
        setattr(existing_sale, key, value)

    db.commit()
    db.refresh(existing_sale)

    return existing_sale


# -----------------------
# DELETE (HARD DELETE)
# -----------------------
@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale",
    description="Permanently delete a sale by its ID.",
    dependencies=CAN_DELETE_SALES,
)
async def delete(
    sale_id: int,
    db: db_dependency,
):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found.",
        )

    db.delete(existing_sale)
    db.commit()

    return
