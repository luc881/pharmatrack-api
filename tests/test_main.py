from fastapi.testclient import TestClient
from pharmatrack import main
from fastapi import status

client = TestClient(main.app)


def test_return_health_check():
    response = client.get("/healthcheck")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "message": "API is running"}