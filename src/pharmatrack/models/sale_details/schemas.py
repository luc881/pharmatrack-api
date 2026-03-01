from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from pharmatrack.models.products.schemas import PaginatedResponse, PaginationParams


# =========================================================
# 🔹 Base
# =========================================================
class SaleDetailBase(BaseModel):
    product_id: int = Field(..., gt=0, description="ID del producto vendido")
    quantity: Decimal = Field(..., gt=0, description="Cantidad vendida")
    price_unit: Decimal = Field(..., ge=0, description="Precio unitario del producto (snapshot)")
    discount: Decimal = Field(0, ge=0, description="Descuento aplicado al producto")
    tax: Decimal = Field(0, ge=0, description="Impuesto aplicado al producto")
    total: Decimal = Field(..., ge=0, description="Total del detalle (quantity * price_unit - discount + tax)")
    description: Optional[str] = Field(None, description="Descripción del detalle de venta")


# =========================================================
# 🟢 Create
# =========================================================
class SaleDetailCreate(BaseModel):
    sale_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: Decimal = Field(..., gt=0)
    discount: Decimal = Field(0, ge=0)
    description: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "sale_id": 10,
                "product_id": 5,
                "quantity": "3.00",
                "discount": "5.00",
                "description": "Caja de paracetamol 500mg"
            }
        }
    )


# =========================================================
# 🟡 Update
# =========================================================
class SaleDetailUpdate(BaseModel):
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[Decimal] = Field(None, gt=0)
    discount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "product_id": 12,
                "quantity": "2.00"
            }
        }
    )


# =========================================================
# 🔵 Response
# =========================================================
class SaleDetailResponse(BaseModel):
    id: int
    sale_id: int
    product_id: int
    quantity: Decimal
    price_unit: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 100,
                "sale_id": 10,
                "product_id": 5,
                "quantity": "3.00",
                "price_unit": "50.00",
                "discount": "5.00",
                "tax": "0.00",
                "total": "145.00",
                "description": "Caja de paracetamol 500mg",
                "created_at": "2025-02-10T14:30:00",
                "updated_at": "2025-02-10T14:30:00"
            }
        }
    )


# =========================================================
# 🧩 Response con relaciones
# =========================================================
class SaleDetailWithRelations(SaleDetailResponse):
    product: Optional["ProductResponse"] = None
    sale: Optional["SaleResponse"] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 100,
                "quantity": "3.00",
                "total": "145.00",
                "product": {
                    "id": 5,
                    "name": "Paracetamol 500mg",
                    "price": "50.00"
                },
                "sale": {
                    "id": 10,
                    "total": "111.00",
                    "status": "completed"
                }
            }
        }
    )


# =========================================================
# 🔍 Search params
# =========================================================
class SaleDetailSearchParams(BaseModel):
    sale_id: Optional[int] = Field(None, gt=0, description="Filtrar por ID de venta")
    product_id: Optional[int] = Field(None, gt=0, description="Filtrar por ID de producto")


# =========================================================
# 🔁 Forward references
# =========================================================
if TYPE_CHECKING:
    from ..products.schemas import ProductResponse
    from ..sales.schemas import SaleResponse


# =========================================================
# 🔁 Re-exportar para uso en el router
# =========================================================
__all__ = [
    "SaleDetailBase",
    "SaleDetailCreate",
    "SaleDetailUpdate",
    "SaleDetailResponse",
    "SaleDetailWithRelations",
    "SaleDetailSearchParams",
    "PaginatedResponse",
    "PaginationParams",
]