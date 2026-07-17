"""Seed de animales de ejemplo con su cadena completa (género → especie →
morphs → animal + producto gemelo). Idempotente por código: los animales
cuyo code ya existe se omiten, así puede correr sobre una base con datos."""
from datetime import date

from sqlalchemy.orm import Session

from pharmatrack.db.session import SessionLocal
from pharmatrack.models.animals.orm import (
    AnimalGroup, Genus, Species, Morph, Animal, AnimalPhoto,
)
from pharmatrack.models.products.orm import Product
from pharmatrack.models.product_batch.orm import ProductBatch
from pharmatrack.models.product_categories.orm import ProductCategory
from pharmatrack.utils.slugify import slugify


def _gen(prefix, count, base_price, *, start=1, morphs=(), legal=False):
    """Genera animales con variedad determinística (sexo, precio, fotos, fechas)."""
    sexes = ["female", "male", "unknown"]
    out = []
    for i in range(start, start + count):
        code = f"{prefix}-{i:03d}"
        price = base_price + (i % 4) * max(50, round(base_price * 0.15 / 50) * 50)
        n_photos = (i % 3) + 1
        photos = [
            f"https://picsum.photos/seed/{code.lower()}{'abc'[j]}/600/400"
            for j in range(n_photos)
        ]
        animal = dict(
            code=code,
            sex=sexes[i % 3],
            price=price,
            price_cost=round(price * 0.35 / 10) * 10,
            photos=photos,
            requires_legal_doc=legal,
        )
        if legal:
            animal["legal_doc"] = f"SEMARNAT-UMA-{code}"
        if i % 4 != 0:
            animal["birth_date"] = date(2024 + (i % 3), (i * 3) % 12 + 1, (i * 7) % 28 + 1)
        if morphs:
            picked = [morphs[i % len(morphs)]]
            if i % 3 == 0:
                picked.append(morphs[(i + 1) % len(morphs)])
            animal["morphs"] = sorted(set(picked))
        out.append(animal)
    return out


# 15 animales por grupo raíz (ver test_seed_animals.py); los primeros
# conservan los datos originales del seed para no cambiar en bases existentes.
CATALOG = [
    # ── Arácnidos (4 + 3 + 2 + 3 + 1 + 2 = 15) ──────────────────────────
    {
        "group": "Tarántulas",
        "genus": "Brachypelma",
        "species": ("Hamorii", "Tarántula Rodillas Rojas"),
        "morphs": [],
        "care": dict(
            origin="México (cría en cautiverio)", temperature="24-28 °C", humidity="60-70 %",
            adult_size="14 cm", difficulty="Principiante", rarity="Común",
            description=(
                "Tarántula terrestre mexicana, icónica por sus rodillas rojas. Muy dócil y "
                "longeva: las hembras superan los 20 años.\n\n"
                "Requiere sustrato seco con un bebedero y un refugio. Come grillos una o dos "
                "veces por semana."
            ),
        ),
        "animals": [
            dict(code="BH-001", sex="female", price=1800, price_cost=500,
                 requires_legal_doc=True, legal_doc="SEMARNAT-UMA-MOR-0421",
                 photos=["https://picsum.photos/seed/bh001/600/400"]),
            dict(code="BH-002", sex="male", price=900, price_cost=300,
                 requires_legal_doc=True),
            *_gen("BH", 2, 1500, start=3, legal=True),
        ],
    },
    {
        "group": "Tarántulas",
        "genus": "Tliltocatl",
        "species": ("Albopilosus", "Tarántula Rizada"),
        "morphs": ["Nicaragua", "Hobby Form"],
        "animals": _gen("TA", 3, 800, morphs=["Nicaragua", "Hobby Form"]),
    },
    {
        "group": "Tarántulas",
        "genus": "Caribena",
        "species": ("Versicolor", "Tarántula Azul De Martinica"),
        "morphs": [],
        "animals": _gen("CV", 2, 1300),
    },
    {
        "group": "Arañas",
        "genus": "Phidippus",
        "species": ("Regius", "Araña Saltarina Regia"),
        "morphs": [],
        "animals": _gen("PR", 3, 450),
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
    {
        "group": "Escorpiones",
        "genus": "Pandinus",
        "species": ("Imperator", "Escorpión Emperador"),
        "morphs": [],
        "animals": _gen("PI", 2, 750),
    },
    # ── Reptiles (5 + 3 + 3 + 2 + 1 + 1 = 15) ───────────────────────────
    {
        "group": "Serpientes",
        "genus": "Python",
        "species": ("Regius", "Ball Python"),
        "morphs": ["Normal", "Banana", "Pastel", "Albino"],
        "care": dict(
            origin="África occidental (cría en cautiverio)", temperature="26-32 °C",
            humidity="55-65 %", adult_size="1.5 m", difficulty="Principiante", rarity="Común",
            description=(
                "La serpiente más popular como mascota: tranquila, de tamaño manejable y con "
                "una enorme variedad de morphs.\n\n"
                "Necesita un gradiente de temperatura, un escondite en cada zona y comer un "
                "roedor cada 1-2 semanas."
            ),
        ),
        "animals": [
            dict(code="BP-001", sex="female", price=3500, price_cost=1200,
                 morphs=["Banana", "Pastel"],
                 photos=["https://picsum.photos/seed/bp001a/600/400",
                         "https://picsum.photos/seed/bp001b/600/400"]),
            dict(code="BP-002", sex="male", price=2200, price_cost=800,
                 morphs=["Albino"]),
            dict(code="BP-003", sex="unknown", price=1200, price_cost=500,
                 morphs=["Normal"], status="reserved"),
            *_gen("BP", 2, 2500, start=4, morphs=["Normal", "Banana", "Pastel", "Albino"]),
        ],
    },
    {
        "group": "Serpientes",
        "genus": "Pantherophis",
        "species": ("Guttatus", "Serpiente Del Maíz"),
        "morphs": ["Normal", "Anery", "Amel"],
        "animals": _gen("PG", 3, 1400, morphs=["Normal", "Anery", "Amel"]),
    },
    {
        "group": "Geckos",
        "genus": "Correlophus",
        "species": ("Ciliatus", "Gecko Crestado"),
        "morphs": ["Flame", "Harlequin"],
        "care": dict(
            origin="Nueva Caledonia (cría en cautiverio)", temperature="22-26 °C",
            humidity="60-80 %", adult_size="20 cm", difficulty="Principiante", rarity="Común",
            description=(
                "Gecko arborícola nocturno, ideal para empezar: no necesita calor extra ni "
                "insectos vivos si se alimenta con papilla comercial.\n\n"
                "Terrario vertical con ramas y plantas, rociado diario."
            ),
        ),
        "animals": [
            dict(code="CC-001", sex="female", price=1500, price_cost=600,
                 morphs=["Flame"],
                 photos=["https://picsum.photos/seed/cc001/600/400"]),
            *_gen("CC", 2, 1500, start=2, morphs=["Flame", "Harlequin"]),
        ],
    },
    {
        "group": "Geckos",
        "genus": "Eublepharis",
        "species": ("Macularius", "Gecko Leopardo"),
        "morphs": ["Normal", "Tangerine", "Mack Snow"],
        "animals": _gen("EM", 2, 950, morphs=["Normal", "Tangerine", "Mack Snow"]),
    },
    {
        "group": "Lagartos",
        "genus": "Pogona",
        "species": ("Vitticeps", "Dragón Barbudo"),
        "morphs": [],
        "animals": _gen("PV", 1, 1600),
    },
    {
        "group": "Tortugas",
        "genus": "Testudo",
        "species": ("Hermanni", "Tortuga Mediterránea"),
        "morphs": [],
        "animals": _gen("TH", 1, 2800, legal=True),
    },
    # ── Anfibios (6 + 4 + 5 = 15) ───────────────────────────────────────
    {
        "group": "Ranas",
        "genus": "Ceratophrys",
        "species": ("Cranwelli", "Rana Pacman"),
        "morphs": ["Green", "Albino", "Strawberry"],
        "animals": _gen("RC", 6, 600, morphs=["Green", "Albino", "Strawberry"]),
    },
    {
        "group": "Ranas",
        "genus": "Litoria",
        "species": ("Caerulea", "Rana Arborícola Australiana"),
        "morphs": [],
        "animals": _gen("LC", 4, 850),
    },
    {
        "group": "Salamandras Y Ajolotes",
        "genus": "Ambystoma",
        "species": ("Mexicanum", "Ajolote"),
        "morphs": ["Leucístico", "Wild", "Golden"],
        "animals": _gen("AM", 5, 500, legal=True, morphs=["Leucístico", "Wild", "Golden"]),
    },
    # ── Insectos (5 + 4 + 3 + 3 + 3 cepas = 18) ─────────────────────────
    {
        "group": "Mantis",
        "genus": "Hierodula",
        "species": ("Membranacea", "Mantis Gigante Asiática"),
        "morphs": [],
        "animals": _gen("HM", 5, 350),
    },
    {
        "group": "Mantis",
        "genus": "Phyllocrania",
        "species": ("Paradoxa", "Mantis Fantasma"),
        "morphs": [],
        "animals": _gen("PP", 4, 400),
    },
    {
        "group": "Insectos Palo",
        "genus": "Extatosoma",
        "species": ("Tiaratum", "Insecto Palo Espinoso"),
        "morphs": [],
        "animals": _gen("ET", 3, 250),
    },
    {
        "group": "Escarabajos",
        "genus": "Dynastes",
        "species": ("Hyllus", "Escarabajo Hércules Mexicano"),
        "morphs": [],
        "animals": _gen("DH", 3, 550),
    },
    {
        "group": "Colémbolos",
        "genus": "Folsomia",
        "species": ("Candida", "Colémbolos"),
        "morphs": [],
        "sale_format": "colony",
        "care": dict(
            origin="Cosmopolita (cría en cautiverio)", temperature="18-24 °C", humidity="80-90 %",
            adult_size="2 mm", difficulty="Principiante", rarity="Común",
            description=(
                "Microfauna indispensable: consume moho y restos orgánicos, manteniendo limpio "
                "el terrario de cualquier invertebrado o reptil.\n\n"
                "Se vende como cepa establecida en su sustrato, lista para sembrar."
            ),
        ),
        "animals": _gen("FC", 3, 150),
    },
    # ── Crustáceos (8 + 4 + 3 = 15) ─────────────────────────────────────
    {
        "group": "Cangrejos Ermitaños",
        "genus": "Coenobita",
        "species": ("Clypeatus", "Cangrejo Ermitaño Del Caribe"),
        "morphs": [],
        "animals": _gen("CE", 8, 300),
    },
    {
        "group": "Isópodos",
        "genus": "Porcellio",
        "species": ("Laevis", "Isópodo Dairy Cow"),
        "morphs": [],
        "sale_format": "package",
        "package_size": 6,
        "price_tiers": [
            {"quantity": 6, "price": 150},
            {"quantity": 12, "price": 270},
            {"quantity": 18, "price": 380},
        ],
        "care": dict(
            origin="Europa (cría en cautiverio)", temperature="20-26 °C", humidity="70-80 %",
            adult_size="18 mm", difficulty="Principiante", rarity="Común",
            description=(
                "Isópodo muy prolífico con patrón blanco y negro. Excelente equipo de limpieza "
                "para terrarios y fácil de reproducir.\n\n"
                "Se vende en paquetes de 6 ejemplares surtidos."
            ),
        ),
        "animals": _gen("PL", 4, 150),
    },
    {
        "group": "Isópodos",
        "genus": "Armadillidium",
        "species": ("Klugii", "Isópodo Payaso"),
        "morphs": [],
        "sale_format": "package",
        "package_size": 6,
        "price_tiers": [
            {"quantity": 6, "price": 450},
            {"quantity": 12, "price": 820},
            {"quantity": 18, "price": 1150},
        ],
        "animals": _gen("AK", 3, 450),
    },
    # ── Miriápodos (8 + 7 = 15) ─────────────────────────────────────────
    {
        "group": "Milpiés",
        "genus": "Archispirostreptus",
        "species": ("Gigas", "Milpiés Gigante Africano"),
        "morphs": [],
        "animals": _gen("AG", 8, 400),
    },
    {
        "group": "Ciempiés",
        "genus": "Scolopendra",
        "species": ("Polymorpha", "Ciempiés Tigre"),
        "morphs": [],
        "animals": _gen("SP", 7, 500),
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
    existing_codes = {code for (code,) in db.query(Animal.code)}

    category = _animals_category(db)
    created = 0

    for entry in CATALOG:
        group = db.query(AnimalGroup).filter_by(name=entry["group"]).first()
        genus = _get_or_create(
            db, Genus, name=entry["genus"],
            defaults={"group_id": group.id if group else None},
        )
        sp_name, sp_common = entry["species"]
        sale_format = entry.get("sale_format", "individual")
        care = entry.get("care", {})
        species = _get_or_create(
            db, Species, genus_id=genus.id, name=sp_name,
            defaults={
                "common_name": sp_common,
                "sale_format": sale_format,
                "package_size": entry.get("package_size"),
                "price_tiers": entry.get("price_tiers"),
                **care,
            },
        )
        # migra una sola vez las especies que ya existían con el default,
        # sin pisar cambios manuales hechos desde el dashboard
        if sale_format != "individual" and species.sale_format == "individual":
            species.sale_format = sale_format
            species.package_size = entry.get("package_size")
        if care and species.description is None:
            for field, value in care.items():
                setattr(species, field, value)
        if entry.get("price_tiers") and species.price_tiers is None:
            species.price_tiers = entry["price_tiers"]
        morph_map = {
            name: _get_or_create(db, Morph, species_id=species.id, name=name)
            for name in entry["morphs"]
        }

        for a in entry["animals"]:
            if a["code"] in existing_codes:
                continue

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
                birth_date=a.get("birth_date"),
                requires_legal_doc=a.get("requires_legal_doc", False),
                legal_doc=a.get("legal_doc"),
            )
            animal.morphs = [morph_map[m] for m in a.get("morphs", [])]
            animal.photos = [AnimalPhoto(url=u) for u in photos]
            db.add(animal)
            created += 1

    db.commit()
    if created:
        print(f"✅ Seeding completado: {created} animales de ejemplo creados.")
    else:
        print("🦎 Todos los animales de ejemplo ya existen — nada que crear.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_animals(db)
    finally:
        db.close()
