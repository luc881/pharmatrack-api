from typing import Optional, TYPE_CHECKING, Dict
from datetime import datetime
from pydantic import BaseModel, Field

# -----------------------
# Base schema
# -----------------------
class RefundProductBase(BaseModel):
    product_id: int = Field(..., gt=0, description="ID del producto")
    quantity: float = Field(..., gt=0, description="Cantidad a devolver")
    sale_detail_id: Optional[int] = Field(None, gt=0, description="Detalle de venta relacionado")
    is_reintegrable: Optional[bool] = Field(True, description="True si el producto se puede reintegrar al inventario")
    user_id: Optional[int] = Field(None, gt=0, description="Usuario que registró la devolución")


# -----------------------
# Create schema
# -----------------------
class RefundProductCreate(RefundProductBase):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "product_id": 12,
                "quantity": 3,
                "sale_detail_id": 100,
                "is_reintegrable": True,
                "user_id": 10,
            }
        }
    }


# -----------------------
# Update schema
# -----------------------
class RefundProductUpdate(BaseModel):
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[float] = Field(None, gt=0)
    sale_detail_id: Optional[int] = Field(None, gt=0)
    is_reintegrable: Optional[bool] = None
    user_id: Optional[int] = Field(None, gt=0)
    deleted_at: Optional[datetime] = None

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "quantity": 2,
                "is_reintegrable": False,
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class RefundProductResponse(RefundProductBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    reintegrated_batches: Optional[Dict[str, float]] = Field(default_factory=dict)


    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 200,
                "product_id": 12,
                "quantity": 3,
                "sale_detail_id": 100,
                "is_reintegrable": True,
                "user_id": 10,
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T11:00:00",
                "deleted_at": None
            }
        }
    }


# -----------------------
# With relations
# -----------------------
class RefundProductWithRelations(RefundProductResponse):
    product: Optional["ProductResponse"] = None
    sale_detail: Optional["SaleDetailResponse"] = None
    user: Optional["UserResponse"] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 200,
                "product_id": 12,
                "quantity": 3,
                "sale_detail_id": 100,
                "is_reintegrable": True,
                "user_id": 10,
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T11:00:00",
                "product": {"id": 12, "name": "Laptop X"},
                "sale_detail": {"id": 100, "total": 500.0},
                "user": {"id": 10, "username": "admin"}
            }
        }
    }


# -----------------------
# Search params
# -----------------------
class RefundProductSearchParams(BaseModel):
    product_id: Optional[int] = None
    sale_detail_id: Optional[int] = None
    user_id: Optional[int] = None
    is_reintegrable: Optional[bool] = None


# -----------------------
# Forward references
# -----------------------
if TYPE_CHECKING:
    from ..products.schemas import ProductResponse
    from ..sales.schemas import SaleDetailResponse
    from ..users.schemas import UserResponse
