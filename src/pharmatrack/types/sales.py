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


class MexicanBankEnum(str, Enum):
    BBVA          = "BBVA"
    SANTANDER     = "Santander"
    BANAMEX       = "Banamex"
    BANORTE       = "Banorte"
    HSBC          = "HSBC"
    SCOTIABANK    = "Scotiabank"
    INBURSA       = "Inbursa"
    BAJIO         = "Bajío"
    AFIRME        = "Afirme"
    BX_PLUS       = "Bx+"
    MIFEL         = "Mifel"
    MONEXCB       = "Monexcb"
    AZTECA        = "Azteca"
    SPIN          = "Spin by OXXO"
    MERCADOPAGO   = "Mercado Pago"
    CLIP          = "Clip"
    OTHER         = "Otro"
