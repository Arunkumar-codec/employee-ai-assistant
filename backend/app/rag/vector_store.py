"""
Vector database abstraction (ChromaDB).

WHAT: A vector database stores embeddings alongside their original text and
      metadata, and can efficiently answer "which stored vectors are
      closest to this query vector?" — that's the operation retrieval needs.
WHY CHROMADB: it runs embedded in-process (no separate server to deploy for
      a small assessment), persists to a local directory out of the box,
      and has a small, direct Python API — appropriate for this project's
      "plain Python where practical" and "understand every line" goals,
      compared to a managed service (Pinecone) or a heavier standalone
      server (Qdrant).
HOW:  This module wraps a single ChromaDB PersistentClient + collection.
      Embeddings are computed OURSELVES via embedder.py and passed in
      explicitly (rather than letting Chroma call an embedding function
      internally) — this keeps the embedding step visible, swappable, and
      testable independently of Chroma.

DISTANCE METRIC: the collection is created with `hnsw:space="cosine"`.
      ChromaDB's default (unset) space is squared L2 (Euclidean) distance,
      which is NOT the similarity concept all-MiniLM-L6-v2 was trained for
      (see embedder.py). Verified from Chroma's own collection
      configuration API: for `hnsw:space="cosine"`, `collection.query()`
      returns `distances` as `1 - cosine_similarity`, so:
        - 0.0 means identical direction (most similar)
        - 1.0 means orthogonal (unrelated)
        - up to 2.0 means opposite direction (most dissimilar)
      i.e. SMALLER distance = MORE relevant. This is the opposite of a
      "score" where bigger is better — retriever.py and rag_service.py
      compare distances with `<=` against a threshold, never `>=`.

DEDUPLICATION STRATEGY: deterministic chunk IDs (source::index, see
      chunker.py) + `collection.upsert()` instead of `collection.add()`.
      WHY upsert over "always rebuild the collection from scratch": upsert
      is idempotent and cheap — re-running the ingestion script after
      editing one document only touches the chunks whose IDs changed,
      rather than deleting and re-embedding the entire corpus every time.
      The trade-off is that if a document is deleted from documents/, its
      old chunk IDs remain in Chroma until a full rebuild. `rebuild=True`
      (used by `scripts/ingest_documents.py --rebuild`) covers that case by
      deleting the collection before upserting.
"""
from __future__ import annotations

from typing import Dict, List, Optional, TypedDict


class VectorStoreError(Exception):
    """Raised when the vector store cannot be opened or queried."""


class QueryResult(TypedDict):
    ids: List[str]
    documents: List[str]
    metadatas: List[Dict]
    distances: List[float]


class VectorStore:
    def __init__(self, persist_directory: str, collection_name: str):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
            except ImportError as exc:
                raise VectorStoreError(
                    "chromadb is not installed. Run "
                    "`pip install -r backend/requirements.txt`."
                ) from exc
            try:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            except Exception as exc:  # pragma: no cover - disk/permission issue
                raise VectorStoreError(
                    f"Failed to open Chroma persistence at "
                    f"'{self.persist_directory}': {exc}"
                ) from exc
        return self._client

    def get_or_create_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def rebuild_collection(self):
        """Delete and recreate the collection empty (full re-index path)."""
        client = self._get_client()
        try:
            client.delete_collection(name=self.collection_name)
        except Exception:
            pass  # collection may not exist yet — fine
        self._collection = None
        return self.get_or_create_collection()

    def upsert_chunks(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict],
    ) -> None:
        if not ids:
            return
        if not (len(ids) == len(embeddings) == len(documents) == len(metadatas)):
            raise VectorStoreError("upsert_chunks: mismatched list lengths")
        collection = self.get_or_create_collection()
        try:
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise VectorStoreError(f"Failed to upsert chunks into Chroma: {exc}") from exc

    def count(self) -> int:
        return self.get_or_create_collection().count()

    def query(self, query_embedding: List[float], top_k: int) -> QueryResult:
        collection = self.get_or_create_collection()
        if collection.count() == 0:
            return QueryResult(ids=[], documents=[], metadatas=[], distances=[])
        try:
            raw = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count()),
            )
        except Exception as exc:
            raise VectorStoreError(f"Chroma query failed: {exc}") from exc

        return QueryResult(
            ids=raw["ids"][0],
            documents=raw["documents"][0],
            metadatas=raw["metadatas"][0],
            distances=raw["distances"][0],
        )


_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(persist_directory: str, collection_name: str) -> VectorStore:
    """Process-wide cached VectorStore instance.

    A plain module-level singleton (not lru_cache) because VectorStore
    holds a live Chroma client connection that should not be duplicated per
    unique argument combination the way a pure function's cache would.
    """
    global _vector_store_instance
    if (
        _vector_store_instance is None
        or _vector_store_instance.persist_directory != persist_directory
        or _vector_store_instance.collection_name != collection_name
    ):
        _vector_store_instance = VectorStore(persist_directory, collection_name)
    return _vector_store_instance
