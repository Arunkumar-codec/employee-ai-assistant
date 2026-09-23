"""
LLM service — provider abstraction.

WHAT: A small interface (`LLMProvider`) with one real implementation
      (`GeminiProvider`) so the RAG service calls `llm.generate(...)`
      without knowing which vendor is behind it.
WHY:  The assessment asks for a "configurable provider abstraction" and
      explicitly says not to hard-code a vendor. Keeping route/RAG-service
      code free of any Gemini-specific import means swapping providers
      later (Day 3+ or post-assessment) means adding one new class here,
      not touching rag_service.py or chat.py.
WHICH SDK: `google-genai` (`pip install google-genai`, `from google import
      genai`). This is Google's current, actively maintained SDK for the
      Gemini API. The older `google-generativeai` package is Google's
      legacy library — deliberately NOT used here per the instruction to
      use the current supported SDK rather than an obsolete package.
LAZY CLIENT CREATION: the Gemini client is constructed on first `generate()`
      call, not at import time or app startup. This is what lets the
      FastAPI app import and the `/api/health` endpoint work even when
      LLM_API_KEY is missing/unset — only a RAG question actually needs the
      key, and it fails with a clear `LLMProviderError` at that point
      instead of crashing the whole application at import.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
import time


class LLMProviderError(Exception):
    """Raised when the LLM provider is unconfigured or a call fails."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """Return the model's text response, or raise LLMProviderError."""


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self.api_key:
            raise LLMProviderError(
                "LLM_API_KEY is not configured. Set it in your .env file "
                "(get a free Gemini API key from https://aistudio.google.com/apikey)."
            )
        if self._client is None:
            try:
                from google import genai
            except ImportError as exc:
                raise LLMProviderError(
                    "google-genai is not installed. Run "
                    "`pip install -r backend/requirements.txt`."
                ) from exc
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as exc:  # pragma: no cover - invalid key format etc.
                raise LLMProviderError(f"Failed to create Gemini client: {exc}") from exc
        return self._client

    def generate(self, system_prompt: str, user_message: str) -> str:
        client = self._get_client()
        from google.genai import types
        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=user_message,
                    config=types.GenerateContentConfig(system_instruction=system_prompt),
                )
                break
            except Exception as exc:
                status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
                transient = status in {429, 500, 502, 503, 504} or any(
                    token in str(exc) for token in ("429", "500", "502", "503", "504")
                )
                if transient and attempt < 2:
                    time.sleep(min(2 ** attempt, 4))
                    continue
                raise LLMProviderError("Gemini request failed after bounded retry attempts") from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMProviderError("Gemini returned an empty response")
        return text


_PROVIDERS = {
    "gemini": GeminiProvider,
}


@lru_cache
def get_llm_service(provider_name: str, model: str, api_key: str) -> LLMProvider:
    """Process-wide cached LLMProvider instance for the given config.

    Cached (not re-instantiated per request) so the underlying SDK client
    is reused across requests, matching the embedder/vector-store pattern.
    """
    provider_cls = _PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise LLMProviderError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Supported: {sorted(_PROVIDERS)}"
        )
    return provider_cls(api_key=api_key, model=model)
