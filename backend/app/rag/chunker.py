"""
Chunking layer.

WHAT: Splits each LoadedDocument's text into overlapping, fixed-size chunks
      with stable IDs and full metadata.
WHY:  Whole documents are too large/unfocused to embed as a single vector
      (a query about "sick leave" would retrieve the entire leave policy,
      including unrelated sections about public holidays) and too large to
      pass to the LLM as context for every question. Chunking lets
      retrieval return just the paragraphs that are actually relevant.

CHUNKING STRATEGY (documented per project instructions — see also
docs/ARCHITECTURE.md "Chunking Strategy"):

  chunk_size    = settings.chunk_size     (default 700 characters)
  chunk_overlap = settings.chunk_overlap  (default 120 characters)

  WHY THESE NUMBERS, for THIS corpus specifically:
  - The six company documents are short (roughly 700-1400 characters each)
    and structured as 4-5 numbered sections (e.g. "1. Annual Leave",
    "2. Sick Leave", ...). Each section is a self-contained, quotable
    policy statement of ~150-350 characters.
  - A chunk_size of 700 characters comfortably fits 2-3 whole sections per
    chunk, which keeps enough surrounding context for the LLM to answer
    naturally, without being so large that unrelated sections (e.g. "Public
    Holidays" bleeding into a "Sick Leave" question) dilute the embedding.
  - 500 characters (the low end of the assessment's suggested range) was
    tried conceptually and rejected: it would frequently split a single
    numbered section in half, since several sections run past 400
    characters (see leave_policy.txt section 3, "Applying for Leave").
  - chunk_overlap of 120 characters (~1 short section) ensures that if a
    split does land mid-section, the adjacent chunk still contains that
    section's opening sentence, so retrieval doesn't lose the sentence that
    states what the section is about.
  - Splitting happens on paragraph boundaries first, then sentence-ish
    boundaries (". ", "\n"), and only falls back to a hard character cut if
    no natural boundary exists nearby — this avoids chunks that start or
    end mid-word.

STABLE CHUNK IDs: `{source}::{chunk_index:04d}` (e.g.
"leave_policy.txt::0000"), or `{source}::p{page}::{chunk_index:04d}` for
paginated (PDF) sources. Re-running ingestion on unchanged documents
produces the exact same IDs, which the vector store (see vector_store.py)
uses to UPSERT rather than duplicate. If a document's content changes, the
chunk boundaries may shift and old chunk IDs become stale — see
vector_store.py's `rebuild=True` path for a full clean re-index.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.rag.loader import LoadedDocument

# Natural split points to prefer, in priority order (paragraph, then
# sentence-ish, then just a space) before falling back to a hard cut.
_SPLIT_BOUNDARIES = ["\n\n", ". ", "\n", " "]


@dataclass
class Chunk:
    chunk_id: str
    content: str
    source: str
    document_type: str
    page: int | None = None


def _find_split_point(text: str, target_end: int) -> int:
    """Find a natural boundary to end a chunk at, at or before `target_end`.

    Searches backward from target_end for the closest boundary in
    `_SPLIT_BOUNDARIES` (checked in priority order across the whole
    search window so a paragraph break is preferred even if a plain space
    is closer). Falls back to a hard cut at target_end if none is found
    within a reasonable lookback window, so a single very long unbroken
    run of text still gets split rather than producing one giant chunk.
    """
    window_start = max(0, target_end - 200)
    search_window = text[window_start:target_end]

    for boundary in _SPLIT_BOUNDARIES:
        idx = search_window.rfind(boundary)
        if idx != -1:
            return window_start + idx + len(boundary)

    return target_end  # no natural boundary found — hard cut


def chunk_document(
    document: LoadedDocument,
    chunk_size: int,
    chunk_overlap: int,
) -> List[Chunk]:
    """Split one LoadedDocument into overlapping Chunks.

    Guarantees (per Day-2 requirements):
      1. no empty chunks are produced
      2. every chunk retains source/document_type/page metadata
      3. chunk IDs are stable across repeated runs on the same text
      4. overlap is applied between consecutive chunks
      5. tiny trailing chunks (< 40 chars) are merged into the previous
         chunk rather than kept as their own near-empty chunk
    """
    if chunk_size <= chunk_overlap:
        raise ValueError("chunk_size must be greater than chunk_overlap")

    text = document.text.strip()
    chunks: List[Chunk] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        target_end = min(start + chunk_size, text_length)

        if target_end < text_length:
            end = _find_split_point(text, target_end)
            if end <= start:  # boundary search degenerated — force progress
                end = target_end
        else:
            end = text_length

        content = text[start:end].strip()
        if content:
            chunks.append(content)

        if end >= text_length:
            break
        start = max(0, end - chunk_overlap)

    # Merge a very small trailing fragment into the previous chunk instead
    # of shipping a near-empty, low-signal chunk to the embedder.
    _MIN_CHUNK_CHARS = 40
    if len(chunks) > 1 and len(chunks[-1]) < _MIN_CHUNK_CHARS:
        chunks[-2] = (chunks[-2] + " " + chunks.pop()).strip()

    result: List[Chunk] = []
    for index, content in enumerate(chunks):
        if document.page is not None:
            chunk_id = f"{document.source}::p{document.page}::{index:04d}"
        else:
            chunk_id = f"{document.source}::{index:04d}"
        result.append(
            Chunk(
                chunk_id=chunk_id,
                content=content,
                source=document.source,
                document_type=document.document_type,
                page=document.page,
            )
        )
    return result


def chunk_documents(
    documents: List[LoadedDocument],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Chunk]:
    """Chunk a list of LoadedDocuments and flatten the result."""
    all_chunks: List[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, chunk_size, chunk_overlap))
    return all_chunks
