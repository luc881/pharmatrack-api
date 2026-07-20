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


def test_email_ticket_sin_api_key(auth_headers, db_session,
                                  test_user_with_role_permissions_branch_auth, test_branch):
    _, _, _, sp, _ = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])
    sale, _ = _draft_sale_for_animal(
        db_session, test_user_with_role_permissions_branch_auth, test_branch, animal
    )
    client.post(f"/api/v1/sales/{sale.id}/complete", headers=auth_headers)

    res = client.post(f"/api/v1/sales/{sale.id}/email-ticket",
                      json={"email": "cliente@example.com"}, headers=auth_headers)
    # sin RESEND_API_KEY configurada el endpoint responde 503, no 500
    assert res.status_code == 503, res.text


def test_email_ticket_template_roundtrip(auth_headers):
    res = client.get("/api/v1/settings/email-ticket", headers=auth_headers)
    assert res.status_code == 200, res.text
    assert res.json()["business_name"]

    res = client.put("/api/v1/settings/email-ticket", headers=auth_headers, json={
        "business_name": "Opuntia Den",
        "intro_message": "Sigue los cuidados de tu animal en nuestra web.",
        "footer_message": "Gracias, vuelve pronto!",
    })
    assert res.status_code == 200, res.text
    data = client.get("/api/v1/settings/email-ticket", headers=auth_headers).json()
    assert data["business_name"] == "Opuntia Den"
    assert data["footer_message"] == "Gracias, vuelve pronto!"
