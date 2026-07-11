"""Seed de la taxonomía inicial de grupos de animales (idempotente)."""
from sqlalchemy.orm import Session

from pharmatrack.models.animals.orm import AnimalGroup
from pharmatrack.db.session import SessionLocal


# raíz → subgrupos
GROUPS: dict[str, list[str]] = {
    "Arácnidos": ["Tarántulas", "Arañas", "Escorpiones"],
    "Miriápodos": ["Ciempiés", "Milpiés"],
    "Crustáceos": ["Cangrejos Ermitaños", "Isópodos"],
    "Insectos": ["Mantis", "Insectos Palo", "Escarabajos"],
    "Reptiles": ["Serpientes", "Geckos", "Lagartos", "Tortugas"],
    "Anfibios": ["Ranas", "Salamandras Y Ajolotes"],
}


def _get_or_create(db: Session, name: str, parent_id: int | None) -> tuple[AnimalGroup, bool]:
    group = db.query(AnimalGroup).filter(
        AnimalGroup.name == name, AnimalGroup.parent_id == parent_id
    ).first()
    if group:
        return group, False
    group = AnimalGroup(name=name, parent_id=parent_id)
    db.add(group)
    db.flush()
    return group, True


def seed_animal_groups(db: Session):
    created = 0
    for root_name, children in GROUPS.items():
        root, was_created = _get_or_create(db, root_name, None)
        created += was_created
        for child_name in children:
            _, was_created = _get_or_create(db, child_name, root.id)
            created += was_created

    db.commit()
    print(f"✅ Seeding completado: {created} grupos de animales creados.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_animal_groups(db)
    finally:
        db.close()
