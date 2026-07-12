"""Seed de animales de ejemplo con su cadena completa (género → especie →
morphs → animal + producto gemelo). Solo corre si la tabla animals está vacía,
para no mezclarse con datos reales."""
from sqlalchemy.orm import Session

from pharmatrack.db.session import SessionLocal
from pharmatrack.models.animals.orm import (
    AnimalGroup, Genus, Species, Morph, Animal, AnimalPhoto,
)
from pharmatrack.models.products.orm import Product
from pharmatrack.models.product_batch.orm import ProductBatch
from pharmatrack.models.product_categories.orm import ProductCategory
from pharmatrack.utils.slugify import slugify


CATALOG = [
    {
        "group": "Tarántulas",
        "genus": "Brachypelma",
        "species": ("Hamorii", "Tarántula Rodillas Rojas"),
        "morphs": [],
        "animals": [
            dict(code="BH-001", sex="female", price=1800, price_cost=500,
                 requires_legal_doc=True, legal_doc="SEMARNAT-UMA-MOR-0421",
                 photos=["https://picsum.photos/seed/bh001/600/400"]),
            dict(code="BH-002", sex="male", price=900, price_cost=300,
                 requires_legal_doc=True),
        ],
    },
    {
        "group": "Serpientes",
        "genus": "Python",
        "species": ("Regius", "Ball Python"),
        "morphs": ["Normal", "Banana", "Pastel", "Albino"],
        "animals": [
            dict(code="BP-001", sex="female", price=3500, price_cost=1200,
                 morphs=["Banana", "Pastel"],
                 photos=["https://picsum.photos/seed/bp001a/600/400",
                         "https://picsum.photos/seed/bp001b/600/400"]),
            dict(code="BP-002", sex="male", price=2200, price_cost=800,
                 morphs=["Albino"]),
            dict(code="BP-003", sex="unknown", price=1200, price_cost=500,
                 morphs=["Normal"], status="reserved"),
        ],
    },
    {
        "group": "Geckos",
        "genus": "Correlophus",
        "species": ("Ciliatus", "Gecko Crestado"),
        "morphs": ["Flame", "Harlequin"],
        "animals": [
            dict(code="CC-001", sex="female", price=1500, price_cost=600,
                 morphs=["Flame"],
                 photos=["https://picsum.photos/seed/cc001/600/400"]),
        ],
    },
    {
        "group": "Escorpiones",
        "genus": "Hadrurus",
        "species": ("Arizonensis", "Escorpión Del Desierto"),
        "morphs": [],
        "animals": [
            dict(code="HA-001", sex="unknown", price=650, price_cost=200),
        ],
    },
]


def _animals_category(db: Session) -> ProductCategory:
    cat = db.query(ProductCategory).filter(ProductCategory.slug == "animales").first()
    if not cat:
        cat = ProductCategory(name="Animales", slug="animales", is_active=True)
        db.add(cat)
        db.flush()
    return cat


def _get_or_create(db: Session, model, defaults=None, **filters):
    obj = db.query(model).filter_by(**filters).first()
    if obj:
        return obj
    obj = model(**filters, **(defaults or {}))
    db.add(obj)
    db.flush()
    return obj


def seed_animals(db: Session):
    if db.query(Animal.id).first() is not None:
        print("🦎 Ya hay animales — seed de ejemplo omitido")
        return

    category = _animals_category(db)
    created = 0

    for entry in CATALOG:
        group = db.query(AnimalGroup).filter_by(name=entry["group"]).first()
        genus = _get_or_create(
            db, Genus, name=entry["genus"],
            defaults={"group_id": group.id if group else None},
        )
        sp_name, sp_common = entry["species"]
        species = _get_or_create(
            db, Species, genus_id=genus.id, name=sp_name,
            defaults={"common_name": sp_common},
        )
        morph_map = {
            name: _get_or_create(db, Morph, species_id=species.id, name=name)
            for name in entry["morphs"]
        }

        for a in entry["animals"]:
            photos = a.get("photos", [])
            image = photos[0] if photos else None
            title = f"{sp_common} {a['code']}"

            product = Product(
                title=title,
                slug=slugify(title),
                sku=a["code"],
                price_retail=a["price"],
                price_cost=a["price_cost"],
                product_category_id=category.id,
                is_unit_sale=True,
                unit_name="pieza",
                tracks_batches=True,
                image=image,
            )
            db.add(product)
            db.flush()
            db.add(ProductBatch(product_id=product.id, quantity=1,
                                purchase_price=a["price_cost"]))

            animal = Animal(
                species_id=species.id,
                product_id=product.id,
                code=a["code"],
                sex=a["sex"],
                status=a.get("status", "available"),
                price=a["price"],
                price_cost=a["price_cost"],
                image=image,
                requires_legal_doc=a.get("requires_legal_doc", False),
                legal_doc=a.get("legal_doc"),
            )
            animal.morphs = [morph_map[m] for m in a.get("morphs", [])]
            animal.photos = [AnimalPhoto(url=u) for u in photos]
            db.add(animal)
            created += 1

    db.commit()
    print(f"✅ Seeding completado: {created} animales de ejemplo creados.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_animals(db)
    finally:
        db.close()
