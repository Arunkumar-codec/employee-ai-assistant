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

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Employee AI Assistant"
    app_env: str = "development"
    debug: bool = True

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    frontend_origin: str = "http://localhost:5500"
    cors_origins: str = "http://localhost:5500,http://localhost:8000,http://127.0.0.1:8000"

    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    llm_api_key: str = ""
    llm_fallback_api_key: str = ""

    documents_directory: str = str(PROJECT_ROOT / "documents")

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chroma_persist_directory: str = str(PROJECT_ROOT / "vector_store")
    chroma_collection_name: str = "company_documents"

    chunk_size: int = 500
    chunk_overlap: int = 50

    top_k: int = 3
    retrieval_score_threshold: float = 1.2

    @field_validator("documents_directory", "chroma_persist_directory", mode="after")
    @classmethod
    def resolve_project_path(cls, value: str) -> str:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return str(path.resolve())

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
