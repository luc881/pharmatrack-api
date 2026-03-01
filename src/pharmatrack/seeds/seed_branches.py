"""
Seed inicial para la tabla branches.
Datos dummy, normalizados a minusculas y sin tildes.
"""

from sqlalchemy.orm import Session
from pharmatrack.db.session import SessionLocal
from pharmatrack.models.branches.orm import Branch


# ---------------------------
# Datos dummy
# ---------------------------
BRANCHES = [
    {
        "name": "sucursal principal",
        "address": "av principal 123, colonia centro, cdmx",
    }
]

# ---------------------------
# Seed function
# ---------------------------
def seed_branches(db: Session) -> None:
    """
    Inserta sucursales iniciales si no existen.
    Evita duplicados usando el nombre como referencia.
    """
    for branch_data in BRANCHES:
        exists = (
            db.query(Branch)
            .filter(Branch.name.ilike(branch_data["name"]))
            .first()
        )

        if not exists:
            branch = Branch(**branch_data)
            db.add(branch)

    db.commit()


# ---------------------------
# Script entrypoint
# ---------------------------
if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_branches(db)
        print("✔ Branches seeded successfully")
    finally:
        db.close()
