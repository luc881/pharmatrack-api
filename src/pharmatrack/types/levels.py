"""Dificultad y rareza con opciones fijas.

Antes eran texto libre y se acumulaban variantes ("Fácil", "sencilla",
"Principiante"…) que el filtro de dificultad del catálogo mostraba como
opciones distintas. Ahora el API solo guarda estas opciones; los sinónimos
conocidos se traducen solos y cualquier otra cosa es un 422 que dice cuáles
valen.
"""
import unicodedata
from typing import Annotated, Optional

from pydantic import BeforeValidator

DIFFICULTIES = ["Fácil", "Intermedia", "Difícil"]
RARITIES = ["Común", "Poco común", "Rara", "Muy rara"]


def _plain(text: str) -> str:
    text = unicodedata.normalize("NFD", text.strip().lower())
    return " ".join("".join(c for c in text if unicodedata.category(c) != "Mn").split())


_DIFFICULTY_SYNONYMS = {
    "Fácil": ["facil", "muy facil", "sencilla", "sencillo", "principiante", "baja", "basica", "basico"],
    "Intermedia": ["intermedia", "intermedio", "media", "medio", "moderada", "moderado", "regular"],
    "Difícil": ["dificil", "muy dificil", "avanzada", "avanzado", "experto", "experta", "alta", "exigente"],
}
_RARITY_SYNONYMS = {
    "Común": ["comun", "muy comun", "frecuente", "abundante"],
    "Poco común": ["poco comun", "poco", "inusual", "no tan comun"],
    "Rara": ["rara", "raro", "escasa", "escaso"],
    "Muy rara": ["muy rara", "muy raro", "rarisima", "rarisimo", "excepcional"],
}


def _lookup(synonyms: dict[str, list[str]]) -> dict[str, str]:
    table = {}
    for canonical, words in synonyms.items():
        table[_plain(canonical)] = canonical
        for word in words:
            table[word] = canonical
    return table


_DIFFICULTY = _lookup(_DIFFICULTY_SYNONYMS)
_RARITY = _lookup(_RARITY_SYNONYMS)


def normalize_difficulty(value: Optional[str]) -> Optional[str]:
    """La opción fija que corresponde; None si viene vacío o no se reconoce."""
    if value is None or not str(value).strip():
        return None
    return _DIFFICULTY.get(_plain(str(value)))


def normalize_rarity(value: Optional[str]) -> Optional[str]:
    if value is None or not str(value).strip():
        return None
    return _RARITY.get(_plain(str(value)))


def _validator(normalize, options):
    def check(value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        canonical = normalize(value)
        if canonical is None:
            raise ValueError(f"Usa una de estas opciones: {', '.join(options)}")
        return canonical
    return check


DifficultyStr = Annotated[Optional[str], BeforeValidator(_validator(normalize_difficulty, DIFFICULTIES))]
RarityStr = Annotated[Optional[str], BeforeValidator(_validator(normalize_rarity, RARITIES))]
