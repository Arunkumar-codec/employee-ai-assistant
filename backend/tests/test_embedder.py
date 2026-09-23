"""
Tests for app.rag.embedder.

The real sentence-transformers model is NOT loaded in these tests (it's a
~80MB download and would make unit tests slow/network-dependent). Instead,
Embedder._get_model is monkeypatched to return a small fake model object,
so these tests verify Embedder's own logic (batching, empty-input handling,
dimension pass-through, lazy loading) independent of the real model.
"""
import pytest

from app.rag.embedder import Embedder, EmbeddingError, get_embedder


class _FakeModel:
    """Deterministic stand-in for a SentenceTransformer model."""

    def get_sentence_embedding_dimension(self):
        return 384

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        class _FakeVectors:
            def __init__(self, texts):
                self._texts = texts

            def tolist(self):
                # one short deterministic "vector" per text, based on length
                return [[float(len(t)), 0.0, 1.0] for t in self._texts]

        return _FakeVectors(texts)


def test_embed_texts_returns_one_vector_per_text(monkeypatch):
    embedder = Embedder("fake-model")
    monkeypatch.setattr(embedder, "_get_model", lambda: _FakeModel())

    vectors = embedder.embed_texts(["hello", "a longer piece of text"])

    assert len(vectors) == 2
    assert vectors[0] != vectors[1]


def test_embed_texts_empty_list_returns_empty_list(monkeypatch):
    embedder = Embedder("fake-model")
    monkeypatch.setattr(embedder, "_get_model", lambda: _FakeModel())

    assert embedder.embed_texts([]) == []


def test_embed_query_rejects_empty_string(monkeypatch):
    embedder = Embedder("fake-model")
    monkeypatch.setattr(embedder, "_get_model", lambda: _FakeModel())

    with pytest.raises(EmbeddingError):
        embedder.embed_query("   ")


def test_dimension_reads_from_model_not_hardcoded(monkeypatch):
    embedder = Embedder("fake-model")
    monkeypatch.setattr(embedder, "_get_model", lambda: _FakeModel())

    assert embedder.dimension == 384


def test_get_embedder_returns_same_cached_instance_per_model_name():
    first = get_embedder("sentence-transformers/all-MiniLM-L6-v2")
    second = get_embedder("sentence-transformers/all-MiniLM-L6-v2")
    assert first is second


def test_model_load_failure_raises_embedding_error(monkeypatch):
    embedder = Embedder("fake-model")

    def _boom():
        raise EmbeddingError("sentence-transformers is not installed. Run pip install.")

    monkeypatch.setattr(embedder, "_get_model", _boom)

    with pytest.raises(EmbeddingError):
        embedder.embed_texts(["hi"])
