from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["environment"] == "test"


def test_openapi_available_in_test():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "paths" in response.json()