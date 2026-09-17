"""
Day 1 tests: application imports, health endpoint, config loading,
and basic error handling (invalid route -> 404).
"""
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_app_imports():
    assert app is not None


def test_config_loads():
    assert settings.app_name == "Employee AI Assistant"


def test_health_endpoint_status_code():
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_body_shape():
    response = client.get("/api/health")
    body = response.json()
    assert body == {"status": "ok", "service": settings.app_name}


def test_invalid_route_returns_404():
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404


def test_chat_endpoint_returns_stub_not_fake_answer():
    response = client.post(
        "/api/chat",
        json={"employee_id": "EMP001", "message": "What is the leave policy?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "not implemented" in body["answer"].lower()
    assert body["sources"] == []
    assert body["tools_used"] == []
