"""
Retrieval layer.

WHAT: `search_company_documents(query)` — the function the assessment
      explicitly requires by name. Embeds the query, asks the vector store
      for the top-K closest chunks, and returns them with their source
      metadata and distance.
WHY A SEPARATE MODULE FROM vector_store.py: vector_store.py knows about
      Chroma; this module knows about "what does the RAG pipeline need for
      one query" (embed -> search -> shape the result). Day 4's agent will
      import this function directly as the "Company Knowledge Search" tool
      without needing to know anything about Chroma or embeddings.
TOP_K: configurable via `settings.top_k` (assessment requirement — "Do not
      blindly send every document to the LLM").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.rag.embedder import get_embedder
from app.rag.vector_store import get_vector_store


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    source: str
    document_type: str
    page: Optional[int]
    distance: float


def search_company_documents(
    query: str, top_k: Optional[int] = None
) -> List[RetrievedChunk]:
    """Retrieve the top-K chunks most semantically similar to `query`.

    Returns an empty list for an empty/whitespace-only query or when the
    vector store has not been indexed yet (count 0) — callers (rag_service)
    are responsible for turning "no results" into the no-answer response.
    """
    if not query or not query.strip():
        return []

    resolved_top_k = top_k if top_k is not None else settings.top_k

    embedder = get_embedder(settings.embedding_model)
    query_embedding = embedder.embed_query(query)

    store = get_vector_store(
        settings.chroma_persist_directory, settings.chroma_collection_name
    )
    result = store.query(query_embedding, resolved_top_k)

    chunks: List[RetrievedChunk] = []
    for chunk_id, content, metadata, distance in zip(
        result["ids"], result["documents"], result["metadatas"], result["distances"]
    ):
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                content=content,
                source=metadata.get("source", "unknown"),
                document_type=metadata.get("document_type", "unknown"),
                page=metadata.get("page"),
                distance=distance,
            )
        )
    return chunks
