"""Stock para especies en cepa/paquete: un registro con N unidades idénticas.

Los individuales conservan lote de 1 (folio único). Las cepas descuentan
por venta y pasan a sold solo al llegar a 0; resurtir las reactiva.
"""
from decimal import Decimal

from fastapi import status

from .utils import client, route_client_factory
from .test_animals import _make_taxonomy, _create_animal, animals_get, animals_put, animals_post

_, species_post, _, _, _ = route_client_factory(client, "species")


def _make_colony_species(auth_headers, sp_base):
    """Especie hermana en formato colonia (cepa) dentro de la misma taxonomía."""
    return species_post(
        json={
            "genus_id": sp_base["genus_id"],
            "name": "Candida",
            "common_name": "Colémbolos",
            "sale_format": "colony",
        },
        headers=auth_headers,
    ).json()


def _draft_sale(db_session, user, branch, animal, quantity):
    from pharmatrack.models.sales.orm import Sale
    from pharmatrack.models.sale_details.orm import SaleDetail

    sale = Sale(user_id=user.id, branch_id=branch.id, status="draft",
                subtotal=0, tax=0, discount=0, total=0)
    db_session.add(sale)
    db_session.commit()
    db_session.add(SaleDetail(
        sale_id=sale.id,
        product_id=animal["product_id"],
        quantity=Decimal(quantity),
        price_unit=Decimal(str(animal["price"])),
        discount=Decimal("0"),
        tax=Decimal("0"),
        total=Decimal(str(animal["price"])) * quantity,
    ))
    db_session.commit()
    return sale


def test_stock_only_for_colony_or_package(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)

    # individual: stock > 1 rechazado
    res = animals_post(
        json={"species_id": sp["id"], "sex": "female", "price": 100.0,
              "price_cost": 10.0, "morph_ids": [], "stock": 3},
        headers=auth_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    # colonia: stock N aceptado y expuesto en la respuesta
    colony = _make_colony_species(auth_headers, sp)
    animal = _create_animal(auth_headers, colony["id"], stock=5)
    assert animal["stock"] == 5
    assert animal["status"] == "available"


def test_partial_sale_keeps_available_and_zero_marks_sold(
    auth_headers, db_session, test_user_with_role_permissions_branch_auth, test_branch
):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    colony = _make_colony_species(auth_headers, sp)
    animal = _create_animal(auth_headers, colony["id"], stock=5)

    # Venta parcial (2 de 5): sigue disponible con 3
    sale = _draft_sale(db_session, test_user_with_role_permissions_branch_auth,
                       test_branch, animal, 2)
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200
    refreshed = animals_get(str(animal["id"]), headers=auth_headers).json()
    assert refreshed["status"] == "available"
    assert refreshed["stock"] == 3

    # Venta del resto (3): se agota y pasa a sold
    sale = _draft_sale(db_session, test_user_with_role_permissions_branch_auth,
                       test_branch, animal, 3)
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200
    refreshed = animals_get(str(animal["id"]), headers=auth_headers).json()
    assert refreshed["status"] == "sold"
    assert refreshed["stock"] == 0

    # Resurtir la cepa la regresa a la venta
    res = animals_put(str(animal["id"]), json={"stock": 10}, headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["status"] == "available"
    assert res.json()["stock"] == 10
