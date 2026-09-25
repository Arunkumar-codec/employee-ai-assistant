from app.services.llm_service import GeminiProvider


class TransientError(Exception):
    status_code = 429


def test_secondary_key_used_after_primary_rate_limit(monkeypatch):
    provider = GeminiProvider("primary", "model", "secondary")
    calls = []

    def fake_generate(key, system_prompt, user_message):
        calls.append(key)
        if key == "primary":
            raise TransientError("429 RESOURCE_EXHAUSTED")
        return "fallback answer"

    monkeypatch.setattr(provider, "_generate_with_key", fake_generate)
    assert provider.generate("system", "user") == "fallback answer"
    assert calls == ["primary", "secondary"]
