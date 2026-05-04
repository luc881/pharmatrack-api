import re


def norm_title(v: str) -> str:
    v = re.sub(r'\s+', ' ', v.strip())
    def _cap(w):
        if not w or not w[0].isalpha():
            return w
        # Abreviatura tipo s.a., a.c., c.v. → S.A., A.C., C.V.
        if re.fullmatch(r'([A-Za-záéíóúüñÁÉÍÓÚÜÑ]\.)+', w):
            return w.upper()
        # Acrónimo todo mayúsculas → preservar (ABC, BBVA)
        if w.isupper() and len(w) > 1:
            return w
        return w[0].upper() + w[1:].lower()
    return ' '.join(_cap(w) for w in v.split(' '))


def norm_lower(v: str) -> str:
    """Nombres científicos/técnicos en minúsculas: 'Paracetamol' → 'paracetamol'."""
    return re.sub(r'\s+', ' ', v.strip()).lower()


def norm_sku(v: str) -> str:
    """Códigos SKU/lote en MAYÚSCULAS: 'abc-123' → 'ABC-123'."""
    return re.sub(r'\s+', ' ', v.strip()).upper()


def norm_unit(v: str) -> str:
    """Unidades en minúsculas: 'MG' → 'mg', 'PIEZA' → 'pieza'."""
    return re.sub(r'\s+', ' ', v.strip()).lower()
