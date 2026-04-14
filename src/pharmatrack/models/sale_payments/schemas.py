from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from pharmatrack.types.sales import PaymentMethodEnum


# -----------------------
# Base schema (shared fields)
# -----------------------
class SalePaymentBase(BaseModel):
    method_payment: PaymentMethodEnum = Field(
        ...,
        description="Método de pago"
    )
    transaction_number: Optional[str] = Field(
        None,
        max_length=100,
        description="Número de transacción"
    )
    bank: Optional[str] = Field(
        None,
        max_length=100,
        description="Banco emisor o receptor"
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Monto del pago"
    )


# -----------------------
# Create schema
# -----------------------
class SalePaymentCreate(SalePaymentBase):
    sale_id: int = Field(
        ...,
        gt=0,
        description="ID de la venta asociada"
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "sale_id": 10,
                "method_payment": "card",
                "transaction_number": "TX123456",
                "bank": "BBVA",
                "amount": "118.00"
            }
        }
    }


# -----------------------
# Update schema (all optional)
# -----------------------
class SalePaymentUpdate(BaseModel):
    sale_id: Optional[int] = Field(None, gt=0)
    method_payment: Optional[PaymentMethodEnum] = None
    transaction_number: Optional[str] = Field(None, max_length=100)
    bank: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0)

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "method_payment": "transfer",
                "bank": "Santander",
                "amount": "118.00"
            }
        }
    }


# -----------------------
# Response schema
# -----------------------
class SalePaymentResponse(SalePaymentBase):
    id: int
    sale_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 55,
                "sale_id": 10,
                "method_payment": "card",
                "transaction_number": "TX123456",
                "bank": "BBVA",
                "amount": "118.00",
                "created_at": "2025-02-10T14:30:00",
                "updated_at": "2025-02-10T14:30:00"
            }
        }
    }


# -----------------------
# Response with relation
# -----------------------
class SalePaymentDetailResponse(SalePaymentResponse):
    sale: Optional["SaleResponse"] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 55,
                "method_payment": "transfer",
                "bank": "Santander",
                "amount": "118.00",
                "sale": {
                    "id": 10,
                    "total": "118.00",
                    "status": "completed"
                }
            }
        }
    }


# -----------------------
# Search params
# -----------------------
class SalePaymentSearchParams(BaseModel):
    sale_id: Optional[int] = Field(None, gt=0, description="Filtrar por ID de venta")
    method_payment: Optional[PaymentMethodEnum] = Field(
        None,
        description="Filtrar por método de pago"
    )
    bank: Optional[str] = Field(
        None,
        max_length=100,
        description="Filtrar por banco"
    )
    date_from: Optional[datetime] = Field(None, description="Fecha inicio")
    date_to: Optional[datetime] = Field(None, description="Fecha fin")


# -----------------------
# Forward references
# -----------------------
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..sales.schemas import SaleResponse
