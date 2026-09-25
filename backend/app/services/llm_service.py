from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache
import time
from typing import Optional


class LLMProviderError(Exception):
    pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        pass


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, fallback_api_key: str = ""):
        self.api_key = api_key
        self.fallback_api_key = fallback_api_key
        self.model = model
        self._clients = {}

    def _get_client(self, api_key: str):
        if not api_key:
            raise LLMProviderError("LLM_API_KEY is not configured. Set it in your .env file.")
        if api_key not in self._clients:
            try:
                from google import genai
            except ImportError as exc:
                raise LLMProviderError("google-genai is not installed. Run `pip install -r backend/requirements.txt`.") from exc
            try:
                self._clients[api_key] = genai.Client(api_key=api_key)
            except Exception as exc:
                raise LLMProviderError("Failed to create Gemini client.") from exc
        return self._clients[api_key]

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        return status in {429, 500, 502, 503, 504} or any(
            token in str(exc) for token in ("429", "500", "502", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
        )

    def _generate_with_key(self, api_key: str, system_prompt: str, user_message: str) -> str:
        client = self._get_client(api_key)
        from google.genai import types
        response = client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(system_instruction=system_prompt),
        )
        text = getattr(response, "text", None)
        if not text:
            raise LLMProviderError("Gemini returned an empty response")
        return text

    def generate(self, system_prompt: str, user_message: str) -> str:
        try:
            return self._generate_with_key(self.api_key, system_prompt, user_message)
        except LLMProviderError:
            raise
        except Exception as primary_exc:
            if not self._is_transient(primary_exc):
                raise LLMProviderError("Gemini request failed") from primary_exc

            if self.fallback_api_key and self.fallback_api_key != self.api_key:
                try:
                    return self._generate_with_key(self.fallback_api_key, system_prompt, user_message)
                except LLMProviderError:
                    raise
                except Exception as fallback_exc:
                    if not self._is_transient(fallback_exc):
                        raise LLMProviderError("Gemini fallback request failed") from fallback_exc
                    primary_exc = fallback_exc

            for attempt in range(2):
                time.sleep(2 ** attempt)
                try:
                    return self._generate_with_key(self.api_key, system_prompt, user_message)
                except LLMProviderError:
                    raise
                except Exception as retry_exc:
                    primary_exc = retry_exc
                    if not self._is_transient(retry_exc):
                        break
            raise LLMProviderError("Gemini request failed after bounded retry attempts") from primary_exc


_PROVIDERS = {"gemini": GeminiProvider}


@lru_cache
def get_llm_service(provider_name: str, model: str, api_key: str, fallback_api_key: str = "") -> LLMProvider:
    provider_cls = _PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise LLMProviderError(f"Unknown LLM_PROVIDER '{provider_name}'. Supported: {sorted(_PROVIDERS)}")
    return provider_cls(api_key=api_key, model=model, fallback_api_key=fallback_api_key)
