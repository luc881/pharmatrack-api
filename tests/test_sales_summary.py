"""Corte de caja: resumen de ventas completadas."""
from .utils import client
from .test_animals import _make_taxonomy, _create_animal, _draft_sale_for_animal


def test_sales_summary(auth_headers, db_session,
                       test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    sale, _ = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, animal
    )
    assert client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers).status_code == 200

    res = client.get("/api/v1/sales/summary", headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["count"] >= 1
    assert float(data["total"]) > 0
    assert any(animal["code"] in p["title"] for p in data["top_products"])
