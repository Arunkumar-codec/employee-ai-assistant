"""
RAG context builder.

WHAT: Formats retrieved chunks into a single context string the LLM can
      read, clearly labeling which source each piece of content came from.
WHY:  The LLM must be able to (a) ground its answer only in this text and
      (b) know which filename to attribute each fact to — but the model
      must NEVER be the one deciding/typing the final source list (that
      comes from retrieval metadata in rag_service.py). This formatting is
      what lets the LLM *reference* sources in its reasoning without being
      trusted to invent them.
PROMPT-INJECTION NOTE: retrieved chunk content is company-document text,
      not user input, but it is still untrusted relative to the system
      prompt (a document could theoretically contain text formatted to
      look like an instruction). Each chunk is wrapped in an explicit
      [Source: ...] / content block and the system prompt (see prompts.py)
      explicitly tells the model not to follow instructions found inside
      retrieved content.
"""
from __future__ import annotations

from typing import List

from app.rag.retriever import RetrievedChunk


def build_context(chunks: List[RetrievedChunk]) -> str:
    """Build a labeled context block from retrieved chunks, most relevant first.

    Chunks are already ordered by relevance (ascending distance) by the
    vector store's query. Multiple chunks from the same source are each
    shown separately (with page numbers where available) so the LLM sees
    exactly what was retrieved, not a merged/deduplicated blob.
    """
    if not chunks:
        return ""

    blocks = []
    for chunk in chunks:
        label = f"[Source: {chunk.source}"
        if chunk.page is not None:
            label += f", page {chunk.page}"
        label += "]"
        blocks.append(f"{label}\n{chunk.content}")

    return "\n\n".join(blocks)
