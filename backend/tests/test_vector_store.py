"""
Tests for app.rag.vector_store.

The real chromadb client is NOT used here — VectorStore._get_client is
monkeypatched to return a small in-memory fake client/collection, so these
tests verify VectorStore's own logic (upsert vs. add, cosine space
configuration, empty-collection query handling) independent of the real
Chroma package.
"""
import pytest

from app.rag.vector_store import VectorStore, VectorStoreError


class _FakeCollection:
    def __init__(self):
        self.upsert_calls = []
        self._store = {}  # id -> (embedding, document, metadata)

    def upsert(self, ids, embeddings, documents, metadatas):
        self.upsert_calls.append(ids)
        for i, emb, doc, meta in zip(ids, embeddings, documents, metadatas):
            self._store[i] = (emb, doc, meta)  # overwrite on repeat id = upsert semantics

    def count(self):
        return len(self._store)

    def query(self, query_embeddings, n_results):
        ids = list(self._store.keys())[:n_results]
        return {
            "ids": [ids],
            "documents": [[self._store[i][1] for i in ids]],
            "metadatas": [[self._store[i][2] for i in ids]],
            "distances": [[0.1 * (idx + 1) for idx in range(len(ids))]],
        }


class _FakeClient:
    def __init__(self):
        self.created_with_metadata = None
        self._collection = _FakeCollection()
        self.deleted = False

    def get_or_create_collection(self, name, metadata=None):
        self.created_with_metadata = metadata
        return self._collection

    def delete_collection(self, name):
        self.deleted = True
        self._collection = _FakeCollection()


def _store_with_fake_client():
    store = VectorStore(persist_directory="/tmp/fake", collection_name="test_collection")
    fake_client = _FakeClient()
    store._get_client = lambda: fake_client
    return store, fake_client


def test_collection_created_with_cosine_space():
    store, fake_client = _store_with_fake_client()
    store.get_or_create_collection()
    assert fake_client.created_with_metadata == {"hnsw:space": "cosine"}


def test_upsert_chunks_uses_upsert_not_add():
    store, fake_client = _store_with_fake_client()
    store.upsert_chunks(
        ids=["doc.txt::0000"],
        embeddings=[[0.1, 0.2]],
        documents=["some content"],
        metadatas=[{"source": "doc.txt"}],
    )
    assert fake_client._collection.upsert_calls == [["doc.txt::0000"]]


def test_repeated_upsert_with_same_id_does_not_duplicate():
    store, fake_client = _store_with_fake_client()
    store.upsert_chunks(
        ids=["doc.txt::0000"],
        embeddings=[[0.1, 0.2]],
        documents=["v1"],
        metadatas=[{"source": "doc.txt"}],
    )
    store.upsert_chunks(
        ids=["doc.txt::0000"],
        embeddings=[[0.9, 0.9]],
        documents=["v2 updated"],
        metadatas=[{"source": "doc.txt"}],
    )
    assert store.count() == 1  # same ID -> overwritten, not duplicated


def test_upsert_chunks_mismatched_lengths_raises():
    store, _ = _store_with_fake_client()
    with pytest.raises(VectorStoreError):
        store.upsert_chunks(
            ids=["a", "b"],
            embeddings=[[0.1, 0.2]],
            documents=["only one"],
            metadatas=[{"source": "a.txt"}],
        )


def test_query_on_empty_collection_returns_empty_result():
    store, _ = _store_with_fake_client()
    result = store.query(query_embedding=[0.1, 0.2], top_k=4)
    assert result == {"ids": [], "documents": [], "metadatas": [], "distances": []}


def test_query_returns_shaped_result_after_upsert():
    store, _ = _store_with_fake_client()
    store.upsert_chunks(
        ids=["doc.txt::0000"],
        embeddings=[[0.1, 0.2]],
        documents=["content"],
        metadatas=[{"source": "doc.txt"}],
    )
    result = store.query(query_embedding=[0.1, 0.2], top_k=4)
    assert result["ids"] == ["doc.txt::0000"]
    assert result["documents"] == ["content"]
    assert result["distances"] == [0.1]


def test_rebuild_collection_clears_existing_data():
    store, fake_client = _store_with_fake_client()
    store.upsert_chunks(
        ids=["doc.txt::0000"],
        embeddings=[[0.1, 0.2]],
        documents=["content"],
        metadatas=[{"source": "doc.txt"}],
    )
    assert store.count() == 1
    store.rebuild_collection()
    assert fake_client.deleted is True
    assert store.count() == 0
