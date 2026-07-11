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
