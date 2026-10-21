from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_is_dependency_free() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-api"}


def test_version_endpoint() -> None:
    response = client.get("/api/version")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"
