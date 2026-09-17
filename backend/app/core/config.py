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

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # --- LLM (not used yet — Day 3+) ---
    llm_provider: str = "not_configured"
    llm_model: str = "not_configured"
    llm_api_key: str = ""

    # --- Embeddings / vector store (not used yet — Day 2+) ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_directory: str = "./vector_store"

    # --- Retrieval (not used yet — Day 2+) ---
    top_k: int = 4
    retrieval_score_threshold: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the .env file is parsed only once."""
    return Settings()


settings = get_settings()
