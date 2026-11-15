"""Dificultad y rareza a opciones fijas

Revision ID: levels01
Revises: visphotos01

Traduce lo ya guardado (texto libre) a las opciones fijas de
pharmatrack/types/levels.py. Lo que no se reconozca queda vacío. La tabla de
sinónimos va copiada aquí a propósito: una migración no debe cambiar si
mañana cambia el código.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "levels01"
down_revision: Union[str, Sequence[str], None] = "visphotos01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DIFFICULTY = {
    "Fácil": ["facil", "muy facil", "sencilla", "sencillo", "principiante", "baja", "basica", "basico"],
    "Intermedia": ["intermedia", "intermedio", "media", "medio", "moderada", "moderado", "regular"],
    "Difícil": ["dificil", "muy dificil", "avanzada", "avanzado", "experto", "experta", "alta", "exigente"],
}
RARITY = {
    "Común": ["comun", "muy comun", "frecuente", "abundante"],
    "Poco común": ["poco comun", "poco", "inusual", "no tan comun"],
    "Rara": ["rara", "raro", "escasa", "escaso"],
    "Muy rara": ["muy rara", "muy raro", "rarisima", "rarisimo", "excepcional"],
}


def _plain(text):
    text = unicodedata.normalize("NFD", text.strip().lower())
    return " ".join("".join(c for c in text if unicodedata.category(c) != "Mn").split())


def _table(synonyms):
    table = {}
    for canonical, words in synonyms.items():
        table[_plain(canonical)] = canonical
        for word in words:
            table[word] = canonical
    return table


def _normalize(conn, table, column, lookup):
    rows = conn.execute(sa.text(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL")).all()
    for (value,) in rows:
        canonical = lookup.get(_plain(value)) if value.strip() else None
        if canonical != value:
            conn.execute(
                sa.text(f"UPDATE {table} SET {column} = :new WHERE {column} = :old"),
                {"new": canonical, "old": value},
            )


def upgrade() -> None:
    conn = op.get_bind()
    _normalize(conn, "species", "difficulty", _table(DIFFICULTY))
    _normalize(conn, "species", "rarity", _table(RARITY))
    _normalize(conn, "care_sheets", "difficulty", _table(DIFFICULTY))


def downgrade() -> None:
    # Los valores originales no se guardan: no hay vuelta atrás que hacer
    pass
