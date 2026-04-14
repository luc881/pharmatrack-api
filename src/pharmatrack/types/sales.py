"""
Tipos y enumeraciones para el dominio de ventas y pagos.
"""
from enum import Enum


class SaleStatusEnum(str, Enum):
    DRAFT             = "draft"
    COMPLETED         = "completed"
    CANCELLED         = "cancelled"
    REFUNDED          = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethodEnum(str, Enum):
    CASH     = "cash"
    CARD     = "card"
    TRANSFER = "transfer"
