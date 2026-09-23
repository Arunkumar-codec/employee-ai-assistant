"""
Central application configuration.

WHAT: A single Pydantic settings object loaded from environment variables
      (via a local .env file in development).
WHY:  The assessment requires configuration via environment variables and
      no hard-coded secrets. Centralizing config avoids scattering
      os.getenv() calls throughout the codebase.
HOW:  pydantic-settings reads .env once at import time and validates types.
ALTERNATIVE: plain os.getenv() calls per-module — rejected, harder to test
      and document required variables in one place.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# WHAT: absolute path to the project root (the directory containing
#       documents/, vector_store/, backend/, docs/, frontend/).
# WHY:  backend/app/core/config.py lives 3 levels below the project root
#       (core -> app -> backend -> root). Computing this once, from
#       __file__, means documents_directory and chroma_persist_directory
#       resolve correctly regardless of the process's current working
#       directory (uvicorn is typically launched from backend/, while
#       pytest and scripts/ingest_documents.py are typically launched
#       from the project root).
# ALTERNATIVE: leave these as bare relative strings ("./documents"). This
#       was the Day-1 approach for chroma_persist_directory and works only
#       if every command is run from the exact same cwd — fragile across
#       "run backend" vs "run tests" vs "run ingestion script". Fixed here.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "Employee AI Assistant"
    app_env: str = "development"
    debug: bool = True

    # --- API server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Frontend / CORS ---
    frontend_origin: str = "http://localhost:5500"
    cors_origins: str = "http://localhost:5500,http://localhost:8000,http://127.0.0.1:8000"

    # --- LLM (Day 2+: used by the RAG service to generate grounded answers) ---
    # Kept behind a small provider interface (app/services/llm_service.py) so
    # a different provider can be substituted without touching the RAG service.
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""

    # --- Documents (Day 2) ---
    documents_directory: str = str(PROJECT_ROOT / "documents")

    # --- Embeddings / vector store (Day 2) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_directory: str = str(PROJECT_ROOT / "vector_store")
    chroma_collection_name: str = "company_documents"

    # --- Chunking (Day 2) ---
    # See docs/ARCHITECTURE.md "Chunking Strategy" for the documented
    # reasoning behind these specific numbers.
    chunk_size: int = 500
    chunk_overlap: int = 50

    # --- Retrieval (Day 2) ---
    top_k: int = 3
    # Chroma is configured to use cosine distance (see vector_store.py),
    # where SMALLER is MORE similar (0 = identical, up to 2 = opposite).
    # A question is only answered if the best (smallest) retrieved
    # distance is <= this threshold; otherwise the assistant returns the
    # assessment-required no-answer response. This default is a
    # documented STARTING POINT, not a value verified against the real
    # embedding model in this sandbox (no network access here to download
    # it) — calibrate it locally with scripts/inspect_retrieval.py and
    # adjust via this setting. See README "No-Answer / Confidence
    # Strategy" for the calibration procedure.
    retrieval_score_threshold: float = 1.2

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the .env file is parsed only once."""
    return Settings()


settings = get_settings()
