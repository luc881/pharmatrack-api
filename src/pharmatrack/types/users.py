import re
from enum import Enum
from typing import Union, Annotated
from pydantic import AfterValidator, StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumberValidator
import phonenumbers

# Avatar: una URL http(s) (foto subida) o uno de los predefinidos del dashboard.
# Los predefinidos se guardan como ruta, sin dominio: así sirven en cualquier
# dominio o instalación (con dominio se rompieron al dejar farmaciaselene).
PRESET_AVATAR = re.compile(r"^(?:https?://[^/]+)?(/assets/images/mock/avatar/avatar-\d+\.webp)$")


def _avatar(v: str) -> str:
    preset = PRESET_AVATAR.match(v)
    if preset:
        return preset.group(1)
    if not re.match(r"^https?://\S+$", v):
        raise ValueError("Debe ser un link https:// o un avatar predefinido")
    return v


AvatarStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255), AfterValidator(_avatar)]

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