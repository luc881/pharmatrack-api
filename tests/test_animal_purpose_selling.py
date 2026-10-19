"""Lo que no está en venta (pie de cría, crianza) no se anuncia ni se cobra."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal, _draft_sale_for_animal, animals_put
from .test_bundles import _make_product, _draft_sale, products_put
from .test_care_sheets import URL as SHEET_URL, PUB as SHEET_PUB, _sheet
from .test_shop import fake_google  # noqa: F401  (fixture)


def test_public_list_and_detail_hide_breeder(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    sale = _create_animal(auth_headers, sp["id"])
    breeder = _create_animal(auth_headers, sp["id"], purpose="breeder")
    items = client.get("/api/v1/public/animals").json()["data"]
    assert [i["id"] for i in items] == [sale["id"]]
    assert client.get(f"/api/v1/public/animals/{breeder['id']}").status_code == 404
    assert client.get(f"/api/v1/public/animals/{sale['id']}").status_code == 200


def test_shop_listing_ignores_growing(fake_google, auth_headers):  # noqa: F811
    _, _, _, sp, morph = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"], morph_ids=[morph["id"]], purpose="growing")
    res = client.post("/api/v1/shop/cart/validate", json={"items": [
        {"key": f"m{morph['id']}-u", "qty": 1},
    ]})
    assert res.status_code == 200, res.text
    assert res.json()["items"][0]["available"] is False


def test_pos_rejects_breeder(auth_headers, db_session,
                             test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="breeder", code="BRD-001")
    sale, _ = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, a)
    r = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert r.status_code == 400
    assert "BRD-001" in r.json()["detail"] and "no están en venta" in r.json()["detail"]


def test_pos_rejects_breeder_inside_bundle(
    auth_headers, test_product_category, db_session,
    test_user_with_role_permissions_branch_auth, test_branch,
):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    a = _create_animal(auth_headers, sp["id"], purpose="breeder", code="BRD-002")
    bundle = _make_product(auth_headers, test_product_category.id, sku="KIT-P",
                           title="Kit", tracks_batches=False, price_retail=3800)
    assert products_put(f"{bundle['id']}/bundle-items", headers=auth_headers, json=[
        {"component_product_id": a["product_id"], "quantity": 1}]).status_code == 200
    sale = _draft_sale(db_session, test_user_with_role_permissions_branch_auth, test_branch,
                       bundle["id"], 1, 3800)
    r = client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)
    assert r.status_code == 400 and "BRD-002" in r.json()["detail"]


def test_replacement_must_be_for_sale(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    dead = _create_animal(auth_headers, sp["id"])
    repl = _create_animal(auth_headers, sp["id"], purpose="breeder", code="BRD-003")
    animals_put(str(dead["id"]), json={"status": "reserved"}, headers=auth_headers)
    r = client.post("/api/v1/husbandry-logs", headers=auth_headers, json={
        "species_id": sp["id"], "log_date": "2026-10-12", "animal_id": dead["id"],
        "deaths": 1, "replacement_animal_id": repl["id"]})
    assert r.status_code == 400
    assert "no está en venta" in r.json()["detail"]


def test_care_sheet_count_only_for_sale(auth_headers):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    _create_animal(auth_headers, sp["id"])
    _create_animal(auth_headers, sp["id"], purpose="growing")
    res = client.post(SHEET_URL, json=_sheet(sp, published=True), headers=auth_headers)
    assert res.status_code == 201, res.text
    assert client.get(SHEET_PUB).json()[0]["available_count"] == 1
