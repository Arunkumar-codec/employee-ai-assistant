"""
Embedding component.

WHAT: An embedding is a fixed-length vector of numbers that represents the
      *meaning* of a piece of text, produced by a neural network trained so
      that texts with similar meaning end up as nearby vectors. This module
      turns chunk text (and later, user questions) into such vectors.
WHY:  Keyword search only matches literal words. A question like "Can I
      work remotely?" should still retrieve the "Work From Home Policy"
      document even though it never says the word "remotely". Embeddings
      capture that semantic similarity so retrieval works on meaning, not
      exact wording.
WHAT MODEL: sentence-transformers/all-MiniLM-L6-v2.
WHY THIS MODEL:
  - It runs entirely locally (no API key, no per-call cost, fully
    reproducible — the same text always produces the same vector).
  - It is one of the smallest well-supported sentence-embedding models
    (~80MB), which matters for a small assessment corpus and fast local
    iteration, while still being a standard, widely-used choice for
    semantic search over short documents.
  - It deliberately keeps the embedding model independent of the LLM
    provider (see services/llm_service.py) — swapping the LLM (e.g.
    Gemini -> another provider) never requires re-embedding the corpus,
    and vice versa.
VECTOR DIMENSIONALITY: 384. This is a property of the model itself
      (`SentenceTransformer.get_sentence_embedding_dimension()`), not a
      number chosen or assumed by this code — see `dimension` below, which
      reads it from the loaded model rather than hard-coding 384.
SIMILARITY CONCEPT: cosine similarity — the cosine of the angle between two
      vectors, ranging from -1 (opposite meaning) to 1 (identical meaning),
      independent of vector length/magnitude. all-MiniLM-L6-v2 is trained
      specifically so that cosine similarity between its output vectors
      correlates with semantic similarity, which is why the vector store
      (vector_store.py) is explicitly configured to use cosine distance
      rather than Chroma's default (squared L2/Euclidean) distance.

HOW: The model is loaded exactly once per process, on first use, and reused
     for every subsequent call (see `get_embedder`). Loading a
     transformer model is relatively slow (reading weights from disk); doing
     it once and caching it avoids paying that cost on every request.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List


class EmbeddingError(Exception):
    """Raised when the embedding model fails to load or embed text."""


class Embedder:
    """Wraps a single sentence-transformers model instance."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None  # lazy-loaded on first use, not at import time

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise EmbeddingError(
                    "sentence-transformers is not installed. Run "
                    "`pip install -r backend/requirements.txt`."
                ) from exc
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:  # pragma: no cover - network/disk issue
                raise EmbeddingError(
                    f"Failed to load embedding model '{self.model_name}': {exc}"
                ) from exc
        return self._model

    @property
    def dimension(self) -> int:
        """Vector dimensionality, read from the loaded model (not assumed)."""
        return self._get_model().get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts (e.g. chunk contents during ingestion)."""
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single user query."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed an empty query")
        return self.embed_texts([text])[0]


@lru_cache
def get_embedder(model_name: str) -> Embedder:
    """Process-wide cached Embedder instance, one per model name.

    WHY lru_cache here rather than a bare module-level singleton: it keeps
    the embedder trivially testable (a test can construct its own Embedder
    with a mock model) while still guaranteeing the real application only
    ever loads the configured model once.
    """
    return Embedder(model_name)
