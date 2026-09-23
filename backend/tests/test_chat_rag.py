"""API contract/regression tests for POST /api/chat after Phase 4 agent wiring."""
from fastapi.testclient import TestClient

import app.api.routes.chat as chat_route
from app.main import app
from app.schemas.chat import ChatResponse

client = TestClient(app)


def test_chat_returns_rag_answer_shape(monkeypatch):
    monkeypatch.setattr(chat_route.orchestrator, "process_request", lambda message, employee_id, history=None: ChatResponse(answer="Employees can work from home up to 2 days a week.", sources=["work_from_home_policy.txt"], tools_used=["search_company_documents"]))
    response = client.post("/api/chat", json={"employee_id":"EMP001","message":"What is the work from home policy?"})
    assert response.status_code == 200
    body=response.json(); assert body["answer"]=="Employees can work from home up to 2 days a week." and body["sources"]==["work_from_home_policy.txt"] and body["tools_used"]==["search_company_documents"] and body["conversation_id"]


def test_chat_no_answer_response_has_no_sources(monkeypatch):
    monkeypatch.setattr(chat_route.orchestrator, "process_request", lambda message, employee_id, history=None: ChatResponse(answer="I couldn't find this information in the provided documents.", sources=[], tools_used=["search_company_documents"]))
    response = client.post("/api/chat", json={"employee_id":"EMP001","message":"Does the company provide pet insurance?"})
    body=response.json(); assert body["sources"] == [] and "couldn't find" in body["answer"].lower()


def test_chat_missing_message_field_returns_422():
    assert client.post("/api/chat", json={"employee_id":"EMP001"}).status_code == 422


def test_chat_missing_employee_id_field_returns_422():
    assert client.post("/api/chat", json={"message":"What is the leave policy?"}).status_code == 422


def test_chat_route_never_leaks_raw_exception_details(monkeypatch):
    def _boom(message, employee_id, history=None):
        raise RuntimeError("some internal database connection string / secret detail")
    monkeypatch.setattr(chat_route.orchestrator, "process_request", _boom)
    response=client.post("/api/chat", json={"employee_id":"EMP001","message":"What is the leave policy?"})
    body=response.json(); assert response.status_code == 500 and "database connection string" not in str(body).lower() and "secret detail" not in str(body).lower()
