from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List

from app.core.config import settings
from app.rag.context_builder import build_context
from app.rag.prompts import NO_ANSWER_RESPONSE, SYSTEM_PROMPT, build_user_message
from app.rag.retriever import search_company_documents
from app.services.llm_service import LLMProviderError, get_llm_service

_SEARCH_TOOL_NAME = "search_company_documents"
_EMPTY_QUESTION_RESPONSE = "Please ask a question so I can look it up in the company documents."
_LLM_UNAVAILABLE_RESPONSE = "I found relevant company documents, but the AI answer-generation service is currently unavailable. Please try again later."
_RETRIEVAL_UNAVAILABLE_RESPONSE = "I couldn't access the company knowledge base right now. Please try again later."


@dataclass
class RAGAnswer:
    answer: str
    sources: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))


_SOURCE_STOPWORDS = {
    "about", "after", "also", "and", "are", "company", "does", "for", "from",
    "have", "into", "only", "provided", "the", "their", "this", "under", "using",
    "what", "when", "which", "with", "your",
}


def _content_terms(text: str) -> set[str]:
    terms = set()
    for raw in re.findall(r"[a-zA-Z]{3,}", text.lower()):
        term = raw[:-1] if raw.endswith("s") and len(raw) > 4 else raw
        if term not in _SOURCE_STOPWORDS:
            terms.add(term)
    return terms


def _answer_supporting_sources(chunks, answer_text: str) -> List[str]:
    answer_terms = _content_terms(answer_text)
    supported = []
    for chunk in chunks:
        overlap = answer_terms & _content_terms(chunk.content)
        if len(overlap) >= 2:
            supported.append(chunk.source)
    return _dedupe_preserve_order(supported) or _dedupe_preserve_order([c.source for c in chunks])


def answer_question(question: str) -> RAGAnswer:
    if not question or not question.strip():
        return RAGAnswer(answer=_EMPTY_QUESTION_RESPONSE)

    try:
        chunks = search_company_documents(question, top_k=settings.top_k)
    except Exception:
        return RAGAnswer(answer=_RETRIEVAL_UNAVAILABLE_RESPONSE, tools_used=[_SEARCH_TOOL_NAME])

    relevant_chunks = [
        chunk for chunk in chunks
        if chunk.distance <= settings.retrieval_score_threshold
    ]
    if not relevant_chunks:
        return RAGAnswer(answer=NO_ANSWER_RESPONSE, tools_used=[_SEARCH_TOOL_NAME])

    context = build_context(relevant_chunks)
    user_message = build_user_message(context, question)

    try:
        llm = get_llm_service(
            settings.llm_provider,
            settings.llm_model,
            settings.llm_api_key,
            settings.llm_fallback_api_key,
        )
        answer_text = llm.generate(SYSTEM_PROMPT, user_message)
    except LLMProviderError:
        return RAGAnswer(answer=_LLM_UNAVAILABLE_RESPONSE, tools_used=[_SEARCH_TOOL_NAME])

    if NO_ANSWER_RESPONSE.lower() in answer_text.strip().lower():
        return RAGAnswer(answer=NO_ANSWER_RESPONSE, tools_used=[_SEARCH_TOOL_NAME])

    sources = _answer_supporting_sources(relevant_chunks, answer_text)
    return RAGAnswer(answer=answer_text, sources=sources, tools_used=[_SEARCH_TOOL_NAME])
