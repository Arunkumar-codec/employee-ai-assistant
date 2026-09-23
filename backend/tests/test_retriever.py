"""
Tests for app.rag.retriever.search_company_documents.

app.rag.retriever.get_embedder and .get_vector_store are monkeypatched
(they are imported by name into retriever.py, so patching the names on the
retriever module is what takes effect) with small fakes, so these tests
check retrieval's own shaping/validation logic independent of real
embeddings or a real Chroma index.
"""
import app.rag.retriever as retriever


class _FakeEmbedder:
    def embed_query(self, text):
        return [0.42, 0.13]


class _FakeVectorStore:
    def query(self, query_embedding, top_k):
        return {
            "ids": ["leave_policy.txt::0000", "leave_policy.txt::0001"],
            "documents": ["Annual leave is 18 days.", "Sick leave is 10 days."],
            "metadatas": [
                {"source": "leave_policy.txt", "document_type": "leave_policy"},
                {"source": "leave_policy.txt", "document_type": "leave_policy"},
            ],
            "distances": [0.21, 0.35],
        }


def test_search_returns_empty_list_for_blank_query(monkeypatch):
    assert retriever.search_company_documents("   ") == []
    assert retriever.search_company_documents("") == []


def test_search_returns_shaped_retrieved_chunks(monkeypatch):
    monkeypatch.setattr(retriever, "get_embedder", lambda model_name: _FakeEmbedder())
    monkeypatch.setattr(
        retriever, "get_vector_store", lambda persist_dir, collection: _FakeVectorStore()
    )

    results = retriever.search_company_documents("How many annual leaves are allowed?")

    assert len(results) == 2
    assert results[0].source == "leave_policy.txt"
    assert results[0].distance == 0.21
    assert results[0].content == "Annual leave is 18 days."


def test_search_respects_explicit_top_k(monkeypatch):
    captured = {}

    class _CapturingVectorStore:
        def query(self, query_embedding, top_k):
            captured["top_k"] = top_k
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    monkeypatch.setattr(retriever, "get_embedder", lambda model_name: _FakeEmbedder())
    monkeypatch.setattr(
        retriever, "get_vector_store", lambda persist_dir, collection: _CapturingVectorStore()
    )

    retriever.search_company_documents("some question", top_k=2)

    assert captured["top_k"] == 2
