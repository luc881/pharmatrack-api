"""Tipos y enumeraciones para el dominio de animales."""
from enum import Enum


class AnimalSexEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class AnimalStatusEnum(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"


class SaleFormatEnum(str, Enum):
    INDIVIDUAL = "individual"   # ejemplar único con folio
    PACKAGE = "package"         # paquete de N (p. ej. isópodos x6)
    COLONY = "colony"           # cepa/colonia sin cantidad definida
