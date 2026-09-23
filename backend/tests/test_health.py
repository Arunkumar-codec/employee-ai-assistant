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


# NOTE: the Day-1 stub test that lived here ("chat endpoint returns stub,
# not a fake answer") no longer applies — Day 2 replaced the stub with a
# real RAG implementation in app/services/rag_service.py, wired through
# app/api/routes/chat.py. That behavior now has its own, more thorough
# Day-2 test module: backend/tests/test_chat_rag.py (response shape,
# no-answer shape, validation errors, exception safety net). Keeping a
# stub-specific assertion here would simply fail against the real
# implementation without adding coverage beyond what test_chat_rag.py
# already provides.
