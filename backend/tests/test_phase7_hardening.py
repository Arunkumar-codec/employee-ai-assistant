import inspect
from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import app
from app.schemas.chat import ChatRequest
from app.services.session_service import session_manager
from app.tools.employee_tools import apply_leave

client = TestClient(app)


def test_phase7_rag_defaults():
    assert settings.chunk_size == 500
    assert settings.chunk_overlap == 50
    assert settings.top_k == 3
    assert settings.retrieval_score_threshold == 1.2


def test_apply_leave_public_contract_has_four_parameters():
    assert list(inspect.signature(apply_leave).parameters) == ["employee_id", "start_date", "end_date", "reason"]


def test_employee_id_is_required():
    with pytest.raises(Exception):
        ChatRequest(message="hello")


def test_whitespace_employee_id_rejected():
    with pytest.raises(Exception):
        ChatRequest(employee_id="   ", message="hello")


def test_unknown_employee_returns_404_before_orchestration():
    response = client.post("/api/chat", json={"employee_id": "EMP999", "message": "How many leaves do I have?"})
    assert response.status_code == 404


def test_conversation_employee_mismatch_returns_403(monkeypatch):
    session_manager.clear_all()
    monkeypatch.setattr(
        "app.api.routes.chat.orchestrator.process_request",
        lambda message, employee_id, history=None: type("R", (), {"answer":"ok","sources":[],"tools_used":[]})(),
    )
    first = client.post("/api/chat", json={"employee_id":"EMP001", "message":"hello"})
    cid = first.json()["conversation_id"]
    second = client.post("/api/chat", json={"employee_id":"EMP002", "conversation_id":cid, "message":"hello"})
    assert second.status_code == 403


def test_relative_vector_store_path_resolves_from_project_root(monkeypatch):
    from pathlib import Path
    from app.core.config import PROJECT_ROOT, Settings

    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", "./vector_store")
    configured = Settings(_env_file=None)
    assert Path(configured.chroma_persist_directory) == (PROJECT_ROOT / "vector_store").resolve()
