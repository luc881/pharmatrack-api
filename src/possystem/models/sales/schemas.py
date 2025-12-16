from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# -----------------------
# Base schema (shared fields)
# -----------------------
class SaleBase(BaseModel):
    user_id: int = Field(..., gt=0, description="ID del usuario que realizó la venta")
    branch_id: int = Field(..., gt=0, description="ID de la sucursal")

    subtotal: Decimal = Field(..., ge=0, description="Subtotal de la venta")
    tax: Decimal = Field(0, ge=0, description="Impuestos aplicados")
    discount: Decimal = Field(0, ge=0, description="Descuento aplicado")
    total: Decimal = Field(..., ge=0, description="Total de la venta")

    status: str = Field(
        "completed",
        description="Estado de la venta (completed | cancelled | refunded)"
    )

    description: Optional[str] = Field(None, description="Descripción de la venta")


# -----------------------
# Create schema
# -----------------------
class SaleCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    branch_id: int = Field(..., gt=0)
    description: Optional[str] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "branch_id": 2,
                "description": "Venta de medicamentos varios"
            }
        }
    }


# -----------------------
# Update schema (all optional)
# -----------------------
class SaleUpdate(BaseModel):
    user_id: Optional[int] = Field(None, gt=0)
    branch_id: Optional[int] = Field(None, gt=0)

    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax: Optional[Decimal] = Field(None, ge=0)
    discount: Optional[Decimal] = Field(None, ge=0)
    total: Optional[Decimal] = Field(None, ge=0)

    status: Optional[str] = Field(
        None, description="completed | cancelled | refunded"
    )

    description: Optional[str] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "status": "cancelled",
                "description": "Venta cancelada por error"
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class SaleResponse(SaleBase):
    id: int
    date_sale: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 15,
                "user_id": 1,
                "branch_id": 2,
                "subtotal": "100.00",
                "tax": "16.00",
                "discount": "5.00",
                "total": "111.00",
                "status": "completed",
                "description": "Venta de medicamentos varios",
                "date_sale": "2025-02-10T14:30:00",
                "created_at": "2025-02-10T14:30:00",
                "updated_at": "2025-02-10T14:30:00"
            }
        }
    }


# -----------------------
# Response with relations
# -----------------------
class SaleDetailResponse(SaleResponse):
    user: Optional["UserResponse"] = None
    branch: Optional["BranchResponse"] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 15,
                "total": "111.00",
                "status": "completed",
                "branch": {
                    "id": 2,
                    "name": "Sucursal Centro"
                },
                "user": {
                    "id": 1,
                    "name": "Juan Pérez"
                }
            }
        }
    }


# -----------------------
# Search params
# -----------------------
class SaleSearchParams(BaseModel):
    user_id: Optional[int] = Field(None, gt=0, description="Filtrar por usuario")
    branch_id: Optional[int] = Field(None, gt=0, description="Filtrar por sucursal")
    status: Optional[str] = Field(
        None, description="completed | cancelled | refunded"
    )
    date_from: Optional[datetime] = Field(None, description="Fecha inicio")
    date_to: Optional[datetime] = Field(None, description="Fecha fin")


# -----------------------
# Forward references
# -----------------------
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..users.schemas import UserResponse
    from ..branches.schemas import BranchResponse
