"""Alta de registros de animal y reglas de stock/unicidad, compartidas por
el CRUD de animales y el movimiento de destino."""
import uuid

from sqlalchemy.orm import Session

from ..models.animals.orm import Species, Morph, Animal, AnimalPhoto
from ..models.product_batch.orm import ProductBatch
from ..models.product_categories.orm import ProductCategory
from ..models.products.orm import Product
from ..types.animals import AnimalStatusEnum, AnimalPurposeEnum
from .slugify import slugify

ANIMALS_CATEGORY_SLUG = "animales"


def _animals_category_id(db: Session) -> int:
    """Categoría 'Animales' para los productos gemelos (se crea si no existe)."""
    cat = db.query(ProductCategory).filter(ProductCategory.slug == ANIMALS_CATEGORY_SLUG).first()
    if not cat:
        cat = ProductCategory(name="Animales", slug=ANIMALS_CATEGORY_SLUG, is_active=True)
        db.add(cat)
        db.flush()
    return cat.id


def _animal_title(species: Species, code: str, morphs: list[Morph] | None = None) -> str:
    # El morph en el título distingue gemelos de la misma especie en el POS
    # y en el buscador de paquetes ("Murina Glacier AN-X" vs "Murina Papaya AN-Y")
    parts = [species.common_name or species.name]
    parts.extend(m.name for m in (morphs or []))
    parts.append(code)
    return " ".join(parts)


def new_animal(db: Session, species: Species, morphs: list[Morph], *, purpose: str, stock: int,
               price, price_cost, compare_at_price=None, code: str | None = None,
               sex="unknown", birth_date=None, description=None, image=None,
               photos: list[str] = (), requires_legal_doc=False, legal_doc=None,
               legal_doc_url=None) -> Animal:
    """Crea el animal con su producto gemelo y su lote. Hace flush, no commit."""
    code = code or f"AN-{uuid.uuid4().hex[:8].upper()}"
    # Sin image explícita, la primera foto es la principal
    main_image = image or (photos[0] if photos else None)

    title = _animal_title(species, code, morphs)
    product = Product(
        title=title,
        slug=slugify(title),
        sku=code,
        price_retail=price,
        price_cost=price_cost,
        compare_at_price=compare_at_price,
        product_category_id=_animals_category_id(db),
        is_unit_sale=True,
        unit_name="pieza",
        tracks_batches=True,
        image=main_image,
        description=description,
    )
    db.add(product)
    db.flush()

    # Lote único sin caducidad: el FIFO existente descuenta cada venta.
    # Individuales: 1 (imposible vender el mismo folio dos veces);
    # cepas/paquetes: N unidades idénticas bajo un solo registro.
    db.add(ProductBatch(product_id=product.id, quantity=stock, purchase_price=price_cost))

    animal = Animal(
        species_id=species.id,
        product_id=product.id,
        code=code,
        purpose=purpose,
        sex=sex,
        birth_date=birth_date,
        price=price,
        compare_at_price=compare_at_price,
        price_cost=price_cost,
        description=description,
        image=main_image,
        requires_legal_doc=requires_legal_doc,
        legal_doc=legal_doc,
        legal_doc_url=legal_doc_url,
    )
    animal.morphs = morphs
    animal.photos = [AnimalPhoto(url=u) for u in photos]
    db.add(animal)
    db.flush()
    return animal


def set_animal_stock(db: Session, animal: Animal, quantity: int, closing: bool = True) -> None:
    """Reescribe el lote del producto gemelo y ajusta el estado. No hace commit.

    closing=False (movimientos de destino): llegar a 0 no marca el registro vendido.
    """
    batches = (
        db.query(ProductBatch)
        .filter(ProductBatch.product_id == animal.product_id)
        .order_by(ProductBatch.id)
        .all()
    )
    if batches:
        batches[0].quantity = quantity
        for extra in batches[1:]:
            extra.quantity = 0
    else:
        db.add(ProductBatch(
            product_id=animal.product_id,
            quantity=quantity,
            purchase_price=animal.price_cost,
        ))
    # Stock en 0 = agotado, pero solo un animal en venta se "vende"; un pie de
    # cría o una colonia en crianza vacía sigue activa. Si murió se queda como
    # murió; resurtir una cepa vendida o muerta la reactiva.
    if quantity == 0:
        if (closing and animal.purpose == AnimalPurposeEnum.SALE.value
                and animal.status != AnimalStatusEnum.DECEASED.value):
            animal.status = AnimalStatusEnum.SOLD.value
    elif animal.status in (AnimalStatusEnum.SOLD.value, AnimalStatusEnum.DECEASED.value):
        animal.status = AnimalStatusEnum.AVAILABLE.value


def find_bulk_sibling(db: Session, animal_or_key, purpose: str,
                      exclude_id: int | None = None) -> Animal | None:
    """Registro disponible de la misma especie, mismos morphs (como conjunto) y destino.

    animal_or_key: un Animal o la tupla (species_id, frozenset(morph_ids)).
    """
    if isinstance(animal_or_key, Animal):
        species_id = animal_or_key.species_id
        morph_ids = frozenset(m.id for m in animal_or_key.morphs)
    else:
        species_id, morph_ids = animal_or_key
        morph_ids = frozenset(morph_ids)
    query = db.query(Animal).filter(
        Animal.species_id == species_id,
        Animal.purpose == purpose,
        Animal.status == AnimalStatusEnum.AVAILABLE.value,
    )
    if exclude_id is not None:
        query = query.filter(Animal.id != exclude_id)
    for candidate in query.all():
        if frozenset(m.id for m in candidate.morphs) == morph_ids:
            return candidate
    return None
