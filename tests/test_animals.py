"""Tests del módulo de animales: taxonomía, producto gemelo y ciclo de venta."""
from decimal import Decimal

from fastapi import status
from .utils import client, route_client_factory

groups_get, groups_post, groups_put, _, groups_delete = route_client_factory(client, "animal-groups")
genera_get, genera_post, _, _, genera_delete = route_client_factory(client, "genera")
species_get, species_post, _, _, species_delete = route_client_factory(client, "species")
morphs_get, morphs_post, _, _, morphs_delete = route_client_factory(client, "morphs")
animals_get, animals_post, animals_put, _, animals_delete = route_client_factory(client, "animals")


# =========================================================
# Helpers
# =========================================================
def _make_taxonomy(auth_headers, group_name="Arácnidos", subgroup_name="Tarántulas",
                   genus_name="Brachypelma", species_name="Hamorii", morph_name="Albino"):
    root = groups_post(json={"name": group_name}, headers=auth_headers).json()
    sub = groups_post(json={"name": subgroup_name, "parent_id": root["id"]}, headers=auth_headers).json()
    genus = genera_post(json={"name": genus_name, "group_id": sub["id"]}, headers=auth_headers).json()
    sp = species_post(
        json={"genus_id": genus["id"], "name": species_name, "common_name": f"{genus_name} común"},
        headers=auth_headers,
    ).json()
    morph = morphs_post(json={"species_id": sp["id"], "name": morph_name}, headers=auth_headers).json()
    return root, sub, genus, sp, morph


def _create_animal(auth_headers, species_id, morph_ids=None, **overrides):
    payload = {"species_id": species_id, "sex": "female", "price": 3500.0,
               "price_cost": 1200.0, "morph_ids": morph_ids or []}
    payload.update(overrides)
    response = animals_post(json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    return response.json()


def _draft_sale_for_animal(db_session, user, branch, animal):
    from pharmatrack.models.sales.orm import Sale
    from pharmatrack.models.sale_details.orm import SaleDetail

    sale = Sale(user_id=user.id, branch_id=branch.id, status="draft",
                subtotal=0, tax=0, discount=0, total=0)
    db_session.add(sale)
    db_session.commit()

    detail = SaleDetail(
        sale_id=sale.id,
        product_id=animal["product_id"],
        quantity=Decimal("1"),
        price_unit=Decimal(str(animal["price"])),
        discount=Decimal("0"),
        tax=Decimal("0"),
        total=Decimal(str(animal["price"])),
    )
    db_session.add(detail)
    db_session.commit()
    db_session.refresh(detail)
    return sale, detail


# =========================================================
# Taxonomía
# =========================================================
def test_taxonomy_chain_and_tree(auth_headers):
    root, sub, genus, sp, morph = _make_taxonomy(auth_headers)

    tree = groups_get("tree", headers=auth_headers).json()
    root_node = next(n for n in tree if n["id"] == root["id"])
    assert any(c["id"] == sub["id"] for c in root_node["children"])

    assert genus["group"]["id"] == sub["id"]
    assert sp["genus_id"] == genus["id"]
    assert morph["species_id"] == sp["id"]


def test_duplicate_names_rejected(auth_headers):
    root, sub, genus, sp, morph = _make_taxonomy(auth_headers)

    assert groups_post(json={"name": root["name"]}, headers=auth_headers).status_code == 400
    assert genera_post(json={"name": genus["name"]}, headers=auth_headers).status_code == 400
    assert species_post(json={"genus_id": genus["id"], "name": sp["name"]},
                        headers=auth_headers).status_code == 400
    assert morphs_post(json={"species_id": sp["id"], "name": morph["name"]},
                       headers=auth_headers).status_code == 400


def test_delete_guards(auth_headers):
    root, sub, genus, sp, morph = _make_taxonomy(auth_headers)

    # Todos tienen dependencias → 400
    assert groups_delete(str(root["id"]), headers=auth_headers).status_code == 400
    assert groups_delete(str(sub["id"]), headers=auth_headers).status_code == 400
    assert genera_delete(str(genus["id"]), headers=auth_headers).status_code == 400
    assert species_delete(str(sp["id"]), headers=auth_headers).status_code == 400

    # En orden inverso sí se puede
    assert morphs_delete(str(morph["id"]), headers=auth_headers).status_code == 204
    assert species_delete(str(sp["id"]), headers=auth_headers).status_code == 204
    assert genera_delete(str(genus["id"]), headers=auth_headers).status_code == 204
    assert groups_delete(str(sub["id"]), headers=auth_headers).status_code == 204
    assert groups_delete(str(root["id"]), headers=auth_headers).status_code == 204


# =========================================================
# Animales: producto gemelo
# =========================================================
def test_create_animal_creates_twin_product(auth_headers, db_session):
    _, _, _, sp, morph = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]], code="BP-001")

    assert animal["status"] == "available"
    assert [m["id"] for m in animal["morphs"]] == [morph["id"]]

    from pharmatrack.models.products.orm import Product
    from pharmatrack.models.product_batch.orm import ProductBatch

    product = db_session.get(Product, animal["product_id"])
    assert product is not None
    assert product.is_unit_sale is True
    assert product.sku == "BP-001"
    assert float(product.price_retail) == 3500.0

    batches = db_session.query(ProductBatch).filter_by(product_id=product.id).all()
    assert len(batches) == 1
    assert batches[0].quantity == 1
    assert batches[0].expiration_date is None


def test_animal_code_autogenerated(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    assert animal["code"].startswith("AN-")


def test_animal_morphs_must_match_species(auth_headers):
    _, _, genus, sp, _ = _make_taxonomy(auth_headers)
    other_sp = species_post(json={"genus_id": genus["id"], "name": "Smithi"},
                            headers=auth_headers).json()
    other_morph = morphs_post(json={"species_id": other_sp["id"], "name": "Melanistic"},
                              headers=auth_headers).json()

    response = animals_post(
        json={"species_id": sp["id"], "price": 100.0, "morph_ids": [other_morph["id"]]},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_manual_sold_status_forbidden(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    response = animals_put(str(animal["id"]), json={"status": "sold"}, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_animals_group_filter_includes_descendants(auth_headers):
    root, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    # El género cuelga del subgrupo, pero filtrar por la raíz debe incluirlo
    data = animals_get("", params={"group_id": root["id"]}, headers=auth_headers).json()
    assert any(a["id"] == animal["id"] for a in data["data"])


# =========================================================
# Ciclo de venta
# =========================================================
def test_sell_animal_marks_sold(auth_headers, db_session,
                                test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    sale, _ = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, animal
    )

    response = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK, response.text

    refreshed = animals_get(str(animal["id"]), headers=auth_headers).json()
    assert refreshed["status"] == "sold"

    from pharmatrack.models.product_batch.orm import ProductBatch
    batch = db_session.query(ProductBatch).filter_by(product_id=animal["product_id"]).one()
    db_session.refresh(batch)
    assert batch.quantity == 0

    # Vendido → no se puede borrar
    assert animals_delete(str(animal["id"]), headers=auth_headers).status_code == 400


def test_refund_restores_animal_availability(auth_headers, db_session,
                                             test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    sale, detail = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, animal
    )
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200

    response = client.post(
        "/api/v1/refundproducts",
        json={
            "product_id": animal["product_id"],
            "quantity": 1,
            "sale_detail_id": detail.id,
            "is_reintegrable": True,
            "user_id": test_user_with_role_permissions_branch_auth.id,
        },
        headers=auth_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED, response.text

    refreshed = animals_get(str(animal["id"]), headers=auth_headers).json()
    assert refreshed["status"] == "available"


def test_reserved_animal_cannot_be_sold(auth_headers, db_session,
                                        test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    response = animals_put(str(animal["id"]), json={"status": "reserved"}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    sale, _ = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, animal
    )
    response = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert animal["code"] in response.json()["detail"]

    # Liberar la reserva → ahora sí se vende
    animals_put(str(animal["id"]), json={"status": "available"}, headers=auth_headers)
    response = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


# =========================================================
# Fotos y documentación legal
# =========================================================
def test_animal_photos_and_legal_doc(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(
        auth_headers, sp["id"],
        photos=["http://example.com/1.jpg", "http://example.com/2.jpg"],
        requires_legal_doc=True,
        legal_doc="SEMARNAT-UMA-12345",
        legal_doc_url="http://example.com/doc.pdf",
    )

    assert animal["photos"] == ["http://example.com/1.jpg", "http://example.com/2.jpg"]
    # Sin image explícita, la primera foto es la principal
    assert animal["image"] == "http://example.com/1.jpg"
    assert animal["requires_legal_doc"] is True
    assert animal["legal_doc"] == "SEMARNAT-UMA-12345"

    # PUT photos reemplaza todas
    response = animals_put(str(animal["id"]),
                           json={"photos": ["http://example.com/3.jpg"]}, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["photos"] == ["http://example.com/3.jpg"]

    # PUT sin photos no las toca
    response = animals_put(str(animal["id"]), json={"price": 999.0}, headers=auth_headers)
    assert response.json()["photos"] == ["http://example.com/3.jpg"]


def test_animal_legal_doc_optional(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    assert animal["requires_legal_doc"] is False
    assert animal["legal_doc"] is None
    assert animal["photos"] == []


def test_delete_available_animal_removes_twin_product(auth_headers, db_session):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    assert animals_delete(str(animal["id"]), headers=auth_headers).status_code == 204

    from pharmatrack.models.products.orm import Product
    assert db_session.get(Product, animal["product_id"]) is None
