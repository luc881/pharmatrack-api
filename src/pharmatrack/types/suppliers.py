from typing import Annotated, Optional
from pydantic import StringConstraints
from pharmatrack.types.users import MXPhoneNumber

SupplierNameStr = Annotated[
    str,
    StringConstraints(min_length=1, max_length=255),
]

# RFC mexicano: 3-4 letras/& + 6 dígitos fecha + 3 homoclave
SupplierRFCStr = Annotated[
    str,
    StringConstraints(
        pattern=r"^[A-ZÑ&]{3,4}\d{6}[A-V0-9]{3}$",
        min_length=12,
        max_length=13,
    ),
]

# Reutiliza el validador de teléfono mexicano de types/users.py
SupplierPhoneStr = Optional[MXPhoneNumber]
