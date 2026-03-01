from enum import Enum
from typing import Union, Annotated
from pydantic import StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator
import phonenumbers

# Tipos especiales
NameStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$",
        min_length=1,
        max_length=255
    )
]

SurnameStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$",
        min_length=1,
        max_length=255
    )
]
MXPhoneNumber = Annotated[
    Union[str, phonenumbers.PhoneNumber],
    PhoneNumberValidator(
        default_region='MX',       # Si no tiene prefijo internacional, asume México
        number_format='E164',      # Formato estándar +521...
        supported_regions=['MX']   # Solo números mexicanos
    )
]

NumDocStr = Annotated[
    str,
    StringConstraints(
        to_upper=True,
        pattern=r"^[a-zA-Z0-9]+$",
        min_length=2,
        max_length=50)
]

class DocumentTypeEnum(str, Enum):
    INE = "INE"
    PASSPORT = "PASSPORT"
    LICENSE = "LICENSE"

class GenderEnum(str, Enum):
    M = "M"
    F = "F"