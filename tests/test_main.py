from fastapi.testclient import TestClient
from pharmatrack import main
from fastapi import status

client = TestClient(main.app)


def test_return_health_check():
    response = client.get("/healthcheck")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "API is running"


def test_health_check_reports_integrations_without_leaking_secrets():
    body = client.get("/healthcheck").json()
    integrations = body["integrations"]
    # solo banderas: nunca el valor de las credenciales
    assert set(integrations) == {"google_sign_in", "payments", "payments_mode", "email"}
    assert all(isinstance(v, bool) for k, v in integrations.items() if k != "payments_mode")
    assert integrations["payments_mode"] in {"test", "live", "off"}
    assert "TEST-" not in response_text(body)


def response_text(body) -> str:
    import json
    return json.dumps(body)