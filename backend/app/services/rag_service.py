"""
RAG service — high-level orchestration.

WHAT: `answer_question(question)` ties together retrieval, confidence
      evaluation, context building, and LLM generation into the single
      call the chat route needs.
WHY A SEPARATE LAYER FROM THE ROUTE: `api/routes/chat.py` should stay a
      thin HTTP adapter (parse request, call service, return response) —
      keeping orchestration here means it can be unit-tested directly
      (see tests/test_rag_service.py) without going through FastAPI at all,
      and it is exactly what Day 4's agent will call for the "RAG only"
      and "multiple tools" scenarios.

FLOW (per assessment):
  1. validate the question
  2. retrieve chunks (search_company_documents)
  3. evaluate retrieval relevance (distance vs. threshold)
  4. if insufficient -> return the required no-answer result
  5. build grounded context
  6. call the LLM
  7. return answer + deduplicated sources + tools_used

SOURCES ARE NEVER THE MODEL'S TO INVENT: `sources` below is built directly
from `RetrievedChunk.source` values, deduplicated while preserving
first-seen order — the LLM's text output is never parsed for filenames.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.core.config import settings
from app.rag.context_builder import build_context
from app.rag.prompts import NO_ANSWER_RESPONSE, SYSTEM_PROMPT, build_user_message
from app.rag.retriever import search_company_documents
from app.services.llm_service import LLMProviderError, get_llm_service

_SEARCH_TOOL_NAME = "search_company_documents"

_EMPTY_QUESTION_RESPONSE = "Please ask a question so I can look it up in the company documents."

_LLM_UNAVAILABLE_RESPONSE = (
    "I found relevant company documents, but the AI answer-generation "
    "service is currently unavailable. Please try again later."
)


@dataclass
class RAGAnswer:
    answer: str
    sources: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def answer_question(question: str) -> RAGAnswer:
    # 1. validate the question
    if not question or not question.strip():
        return RAGAnswer(answer=_EMPTY_QUESTION_RESPONSE, sources=[], tools_used=[])

    # 2. retrieve chunks
    chunks = search_company_documents(question, top_k=settings.top_k)

    # 3. evaluate retrieval relevance — smaller cosine distance = more
    #    relevant (see vector_store.py). No chunks at all, or the single
    #    best chunk still farther than the configured threshold, both mean
    #    "not confidently supported by the documents".
    best_distance = min((chunk.distance for chunk in chunks), default=None)
    is_sufficiently_relevant = (
        best_distance is not None and best_distance <= settings.retrieval_score_threshold
    )

    # 4. insufficient relevance -> required no-answer response.
    #    tools_used still records the search — we DID search, we just
    #    didn't find grounded support. sources stays empty: never attach
    #    fake/weak sources to a no-answer response.
    if not is_sufficiently_relevant:
        return RAGAnswer(
            answer=NO_ANSWER_RESPONSE, sources=[], tools_used=[_SEARCH_TOOL_NAME]
        )

    # 5. build grounded context
    context = build_context(chunks)
    user_message = build_user_message(context, question)

    # 6. call the LLM
    try:
        llm = get_llm_service(settings.llm_provider, settings.llm_model, settings.llm_api_key)
        answer_text = llm.generate(SYSTEM_PROMPT, user_message)
    except LLMProviderError as exc:
        # Retrieval succeeded but generation failed/unconfigured — say so
        # plainly rather than pretending we produced a grounded answer.
        # No sources are attached since no answer was actually generated.
        return RAGAnswer(
            answer=_LLM_UNAVAILABLE_RESPONSE,
            sources=[],
            tools_used=[_SEARCH_TOOL_NAME],
        )

    # 7. sources come from retrieval metadata only, deduplicated in
    #    relevance order — never parsed out of the model's own text.
    if NO_ANSWER_RESPONSE.lower() in answer_text.strip().lower():
        return RAGAnswer(answer=NO_ANSWER_RESPONSE, sources=[], tools_used=[_SEARCH_TOOL_NAME])

    sources = _dedupe_preserve_order([chunk.source for chunk in chunks])

    return RAGAnswer(answer=answer_text, sources=sources, tools_used=[_SEARCH_TOOL_NAME])
