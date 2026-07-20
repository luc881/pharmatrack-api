from fastapi import Depends, HTTPException, APIRouter, Request
from typing import Annotated, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from ...db.session import get_db, db_dependency
from starlette import status

from ...models.sales.orm import Sale
from ...models.users.orm import User
from ...models.branches.orm import Branch
from ...models.sales.schemas import (
    SaleCreate,
    SaleUpdate,
    SaleResponse,
    PaginatedResponse,
    PaginationParams,
)
from pharmatrack.types.sales import SaleStatusEnum
from ...utils.permissions import (
    CAN_READ_SALES, CAN_CREATE_SALES, CAN_UPDATE_SALES, CAN_DELETE_SALES
)
from pharmatrack.utils.pagination import paginate
from pharmatrack.utils.sales_stock import allocate_batches_for_sale_detail
from pharmatrack.utils.sales_calculations import recalc_sale_totals
from ...utils.rate_limit import limiter, LIMIT_READ, LIMIT_WRITE
from ...utils.logger import get_logger

logger = get_logger(__name__)



router = APIRouter(
    prefix="/sales",
    tags=["Sales"],
)


# =========================================================
# GET /
# =========================================================
_SALE_ORDERING_MAP = {
    "date_sale":  Sale.date_sale.asc(),
    "-date_sale": Sale.date_sale.desc(),
    "total":      Sale.total.asc(),
    "-total":     Sale.total.desc(),
}


@router.get(
    "",
    response_model=PaginatedResponse[SaleResponse],
    summary="List all sales",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
@limiter.limit(LIMIT_READ)
async def read_all(
    request: Request,
    db: db_dependency,
    pagination: PaginationParams = Depends(),
    status_filter: Optional[SaleStatusEnum] = None,
    user_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    ordering: Optional[str] = None,
):
    query = db.query(Sale)

    if status_filter is not None:
        query = query.filter(Sale.status == status_filter)
    if user_id is not None:
        query = query.filter(Sale.user_id == user_id)
    if branch_id is not None:
        query = query.filter(Sale.branch_id == branch_id)
    if date_from is not None:
        query = query.filter(Sale.date_sale >= date_from)
    if date_to is not None:
        query = query.filter(Sale.date_sale <= date_to)

    order_clause = _SALE_ORDERING_MAP.get(ordering) if ordering else None
    query = query.order_by(order_clause if order_clause is not None else Sale.date_sale.desc())

    return paginate(query, pagination)


# =========================================================
# GET /{sale_id}
# =========================================================
@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get sale by ID",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_READ_SALES,
)
async def read_by_id(sale_id: int, db: db_dependency):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")
    return sale


# =========================================================
# POST /
# =========================================================
@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=CAN_CREATE_SALES,
)
@limiter.limit(LIMIT_WRITE)
async def create(request: Request, sale: SaleCreate, db: db_dependency):
    if not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    new_sale = Sale(
        user_id=sale.user_id,
        branch_id=sale.branch_id,
        description=sale.description,
        status=SaleStatusEnum.DRAFT,
        subtotal=0,
        tax=0,
        discount=0,
        total=0,
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    logger.info("Sale created id=%s user_id=%s branch_id=%s", new_sale.id, sale.user_id, sale.branch_id)
    return new_sale


# =========================================================
# POST /{sale_id}/complete
# =========================================================
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

    if sale.status != SaleStatusEnum.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft sales can be completed")

    if not sale.sale_details:
        raise HTTPException(status_code=400, detail="Cannot complete an empty sale")

    from ...models.animals.orm import Animal
    from pharmatrack.types.animals import AnimalStatusEnum

    product_ids = [d.product_id for d in sale.sale_details]
    # Los paquetes se sustituyen por sus componentes: un animal dentro de un
    # paquete cuenta igual que uno vendido directo
    from ...utils.sales_stock import expand_bundle_product_ids
    effective_ids = expand_bundle_product_ids(db, product_ids)

    # Un animal reservado no puede venderse: hay que liberar la reserva primero
    reserved = db.query(Animal.code).filter(
        Animal.product_id.in_(effective_ids),
        Animal.status == AnimalStatusEnum.RESERVED.value,
    ).all()
    if reserved:
        codes = ", ".join(r.code for r in reserved)
        raise HTTPException(
            status_code=400,
            detail=f"Animal(es) reservado(s): {codes}. Libera la reserva antes de completar la venta.",
        )

    for detail in sale.sale_details:
        allocate_batches_for_sale_detail(db, detail)

    recalc_sale_totals(db, sale)
    sale.status = SaleStatusEnum.COMPLETED

    # Los animales pasan a "sold" solo cuando su stock llega a 0.
    # Individuales (lote de 1): igual que siempre. Cepas/paquetes con
    # unidades restantes siguen disponibles.
    from sqlalchemy import func
    from ...models.product_batch.orm import ProductBatch

    # La sesión corre con autoflush=False: sin esto la suma leería las
    # cantidades de ANTES del descuento de lotes
    db.flush()

    remaining = dict(
        db.query(ProductBatch.product_id, func.coalesce(func.sum(ProductBatch.quantity), 0))
        .filter(ProductBatch.product_id.in_(effective_ids))
        .group_by(ProductBatch.product_id)
        .all()
    )
    sold_out = [pid for pid in effective_ids if remaining.get(pid, 0) <= 0]
    if sold_out:
        db.query(Animal).filter(
            Animal.product_id.in_(sold_out)
        ).update({Animal.status: AnimalStatusEnum.SOLD.value}, synchronize_session=False)

    db.commit()
    db.refresh(sale)

    logger.info("Sale completed id=%s total=%s", sale.id, sale.total)
    return sale


# =========================================================
# PUT /{sale_id}
# =========================================================
@router.put(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Update a sale",
    status_code=status.HTTP_200_OK,
    dependencies=CAN_UPDATE_SALES,
)
async def update(sale_id: int, sale: SaleUpdate, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    if sale.user_id and not db.query(User).filter_by(id=sale.user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User ID does not exist.")

    if sale.branch_id and not db.query(Branch).filter_by(id=sale.branch_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Branch ID does not exist.")

    if sale.status in (SaleStatusEnum.REFUNDED, SaleStatusEnum.PARTIALLY_REFUNDED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund statuses can only be set automatically by the refund system.")

    if existing_sale.status != SaleStatusEnum.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft sales can be modified.")

    for key, value in sale.model_dump(exclude_unset=True).items():
        setattr(existing_sale, key, value)

    db.commit()
    db.refresh(existing_sale)
    logger.info("Sale updated id=%s", sale_id)
    return existing_sale


# =========================================================
# DELETE /{sale_id}
# =========================================================
@router.delete(
    "/{sale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale",
    dependencies=CAN_DELETE_SALES,
)
async def delete(sale_id: int, db: db_dependency):
    existing_sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if not existing_sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found.")

    from ...models.refund_products.orm import RefundProduct
    from ...models.sale_details.orm import SaleDetail

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
    logger.info("Sale deleted id=%s", sale_id)
    return