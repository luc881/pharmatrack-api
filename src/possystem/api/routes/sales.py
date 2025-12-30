from fastapi import Depends, HTTPException, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session
from starlette import status
from sqlalchemy import func

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
from ...utils.sales_stock import allocate_batches_for_sale_detail
from sqlalchemy.orm import joinedload
from ...utils.sales_calculations import recalc_sale_totals

db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)

# ACTUALIZAR ESTADOS VÁLIDOS PARA INCLUIR LOS NUEVOS
VALID_SALE_STATUS = {"draft", "completed", "cancelled", "refunded", "partially_refunded"}


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

    new_sale = Sale(
        user_id=sale.user_id,
        branch_id=sale.branch_id,
        description=sale.description,
        status="draft",  # 👈 SIEMPRE draft al crear
        subtotal=0,
        tax=0,
        discount=0,
        total=0,
    )

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    return new_sale


@router.post(
    "/{sale_id}/complete",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
def complete_sale(sale_id: int, db: db_dependency):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.sale_details))
        .filter(Sale.id == sale_id)
        .first()
    )

    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")

    if sale.status != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft sales can be completed",
        )

    if not sale.sale_details:
        raise HTTPException(
            status_code=400,
            detail="Cannot complete an empty sale",
        )

    for detail in sale.sale_details:
        allocate_batches_for_sale_detail(db, detail)

    recalc_sale_totals(db, sale)
    sale.status = "completed"

    db.commit()
    db.refresh(sale)

    return sale


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

    # Solo permitir cambiar estado manualmente si no es un estado relacionado con refunds
    if sale.status in ["refunded", "partially_refunded"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund statuses can only be set automatically by the refund system.",
        )

    if existing_sale.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft sales can be modified.",
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

    # Prevenir borrado de ventas que tienen refunds
    from ...models.refund_products.orm import RefundProduct
    from ...models.sale_details.orm import SaleDetail

    # Verificar si alguno de los sale_details de esta venta tiene refunds
    sale_details = db.query(SaleDetail.id).filter(SaleDetail.sale_id == sale_id).all()
    sale_detail_ids = [sd.id for sd in sale_details]

    if sale_detail_ids:
        refund_count = db.query(func.count(RefundProduct.id)).filter(
            RefundProduct.sale_detail_id.in_(sale_detail_ids)
        ).scalar() or 0

        if refund_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a sale that has refunds. Cancel the refunds first.",
            )

    db.delete(existing_sale)
    db.commit()

    return