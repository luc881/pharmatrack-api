import re


def norm_title(v: str) -> str:
    """'PARACETAMOL 500mg' → 'Paracetamol 500mg'. No capitaliza tras dígitos."""
    v = re.sub(r'\s+', ' ', v.strip())
    return ' '.join(
        w[0].upper() + w[1:].lower() if w and w[0].isalpha() else w
        for w in v.split(' ')
    )


def norm_lower(v: str) -> str:
    """Nombres científicos/técnicos en minúsculas: 'Paracetamol' → 'paracetamol'."""
    return re.sub(r'\s+', ' ', v.strip()).lower()


def norm_sku(v: str) -> str:
    """Códigos SKU/lote en MAYÚSCULAS: 'abc-123' → 'ABC-123'."""
    return re.sub(r'\s+', ' ', v.strip()).upper()


def norm_unit(v: str) -> str:
    """Unidades en minúsculas: 'MG' → 'mg', 'PIEZA' → 'pieza'."""
    return re.sub(r'\s+', ' ', v.strip()).lower()
