"""
Tests for app.services.rag_service.answer_question — the core Day-2
orchestration logic, including the required no-answer / hallucination
control (assessment's central requirement).

search_company_documents and get_llm_service are monkeypatched on the
rag_service module (imported by name), so these tests never touch a real
embedding model, real Chroma index, or a live LLM API call.
"""
from dataclasses import dataclass
from typing import List, Optional

import pytest

import app.services.rag_service as rag_service
from app.rag.prompts import NO_ANSWER_RESPONSE
from app.services.llm_service import LLMProviderError


@dataclass
class _FakeChunk:
    chunk_id: str
    content: str
    source: str
    document_type: str
    page: Optional[int]
    distance: float


class _FakeLLM:
    def __init__(self, response_text="Employees get 18 days of annual leave."):
        self.response_text = response_text
        self.received = None

    def generate(self, system_prompt, user_message):
        self.received = (system_prompt, user_message)
        return self.response_text


class _FailingLLM:
    def generate(self, system_prompt, user_message):
        raise LLMProviderError("LLM_API_KEY is not configured.")


def _relevant_chunks() -> List[_FakeChunk]:
    return [
        _FakeChunk(
            chunk_id="leave_policy.txt::0000",
            content="Employees get 18 days of annual leave per year.",
            source="leave_policy.txt",
            document_type="leave_policy",
            page=None,
            distance=0.2,  # well under the default 0.8 threshold
        )
    ]


def test_empty_question_returns_clarifying_message_without_searching(monkeypatch):
    called = {"search": False}
    monkeypatch.setattr(
        rag_service, "search_company_documents", lambda q, top_k=None: called.__setitem__("search", True) or []
    )

    result = rag_service.answer_question("   ")

    assert called["search"] is False
    assert result.sources == []
    assert result.tools_used == []


def test_relevant_question_returns_grounded_answer_with_sources(monkeypatch):
    monkeypatch.setattr(
        rag_service, "search_company_documents", lambda q, top_k=None: _relevant_chunks()
    )
    fake_llm = _FakeLLM()
    monkeypatch.setattr(rag_service, "get_llm_service", lambda provider, model, key: fake_llm)

    result = rag_service.answer_question("How many annual leaves are allowed?")

    assert result.answer == fake_llm.response_text
    assert result.sources == ["leave_policy.txt"]
    assert result.tools_used == ["search_company_documents"]
    assert fake_llm.received is not None  # LLM was actually called with context


def test_no_relevant_chunks_returns_required_no_answer_response(monkeypatch):
    monkeypatch.setattr(rag_service, "search_company_documents", lambda q, top_k=None: [])

    result = rag_service.answer_question("Does the company provide pet insurance?")

    assert result.answer == NO_ANSWER_RESPONSE
    assert result.sources == []
    assert result.tools_used == ["search_company_documents"]


def test_chunks_beyond_threshold_return_no_answer_response(monkeypatch):
    far_chunk = _relevant_chunks()[0]
    far_chunk.distance = 1.5  # far beyond the default 0.8 threshold
    monkeypatch.setattr(rag_service, "search_company_documents", lambda q, top_k=None: [far_chunk])

    result = rag_service.answer_question("Does the company provide pet insurance?")

    assert result.answer == NO_ANSWER_RESPONSE
    assert result.sources == []


def test_llm_failure_returns_clear_message_without_fake_sources(monkeypatch):
    monkeypatch.setattr(
        rag_service, "search_company_documents", lambda q, top_k=None: _relevant_chunks()
    )
    monkeypatch.setattr(rag_service, "get_llm_service", lambda provider, model, key: _FailingLLM())

    result = rag_service.answer_question("How many annual leaves are allowed?")

    assert "unavailable" in result.answer.lower()
    assert result.sources == []  # never attach sources to an ungenerated answer
    assert result.tools_used == ["search_company_documents"]


def test_duplicate_sources_across_chunks_are_deduplicated(monkeypatch):
    chunk_a = _relevant_chunks()[0]
    chunk_b = _FakeChunk(
        chunk_id="leave_policy.txt::0001",
        content="Sick leave is 10 days.",
        source="leave_policy.txt",  # same source as chunk_a
        document_type="leave_policy",
        page=None,
        distance=0.25,
    )
    monkeypatch.setattr(
        rag_service, "search_company_documents", lambda q, top_k=None: [chunk_a, chunk_b]
    )
    monkeypatch.setattr(rag_service, "get_llm_service", lambda provider, model, key: _FakeLLM())

    result = rag_service.answer_question("What is the leave policy?")

    assert result.sources == ["leave_policy.txt"]  # deduplicated, not ["leave_policy.txt", "leave_policy.txt"]
