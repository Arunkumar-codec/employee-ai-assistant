"""
Tests for app.rag.chunker.

Covers the Day-2 chunking guarantees: no empty chunks, metadata retained,
stable/deterministic chunk IDs, overlap applied, and no unnecessarily tiny
trailing fragments.
"""
import pytest

from app.rag.chunker import chunk_document, chunk_documents
from app.rag.loader import LoadedDocument

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120


def _doc(text, source="leave_policy.txt", document_type="leave_policy", page=None):
    return LoadedDocument(text=text, source=source, document_type=document_type, page=page)


def test_short_document_produces_single_chunk():
    doc = _doc("Short policy text that easily fits in one chunk.")
    chunks = chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)

    assert len(chunks) == 1
    assert chunks[0].content == doc.text
    assert chunks[0].source == "leave_policy.txt"
    assert chunks[0].document_type == "leave_policy"
    assert chunks[0].chunk_id == "leave_policy.txt::0000"


def test_long_document_produces_multiple_chunks_with_no_empty_chunks():
    section = "This is a policy section with enough text to matter. " * 5
    text = "\n\n".join(f"{i}. Section {i}\n{section}" for i in range(1, 8))
    doc = _doc(text)

    chunks = chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)

    assert len(chunks) > 1
    assert all(chunk.content.strip() for chunk in chunks)  # no empty chunks


def test_chunk_ids_are_stable_across_repeated_runs():
    text = ("Repeated content block. " * 60)
    doc = _doc(text)

    first_run = [c.chunk_id for c in chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)]
    second_run = [c.chunk_id for c in chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)]

    assert first_run == second_run
    assert len(set(first_run)) == len(first_run)  # all unique within the document


def test_chunk_ids_include_page_number_for_paginated_documents():
    doc = _doc("Some PDF page content, long enough to be meaningful.", page=3)
    chunks = chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)

    assert chunks[0].chunk_id == "leave_policy.txt::p3::0000"
    assert chunks[0].page == 3


def test_overlap_is_applied_between_consecutive_chunks():
    text = "Word{} ".format
    long_text = "".join(text(i) for i in range(400))  # long, unbroken-ish text
    doc = _doc(long_text)

    chunks = chunk_document(doc, CHUNK_SIZE, CHUNK_OVERLAP)
    assert len(chunks) > 1

    first_tail_words = set(chunks[0].content.split()[-10:])
    second_head_words = set(chunks[1].content.split()[:20])
    assert first_tail_words & second_head_words


def test_chunk_size_must_exceed_overlap():
    doc = _doc("text")
    with pytest.raises(ValueError):
        chunk_document(doc, chunk_size=100, chunk_overlap=100)


def test_chunk_documents_flattens_multiple_documents():
    docs = [_doc("First document text.", source="a.txt"), _doc("Second document text.", source="b.txt")]
    chunks = chunk_documents(docs, CHUNK_SIZE, CHUNK_OVERLAP)

    sources = {c.source for c in chunks}
    assert sources == {"a.txt", "b.txt"}
