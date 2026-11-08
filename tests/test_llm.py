import asyncio

import pytest
from google.genai import errors

from app import llm
from app.config import settings


def api_error(code: int) -> errors.APIError:
    return errors.ClientError(code, {"error": {"code": code, "message": "error"}})


def run(coro):
    return asyncio.run(coro)


def test_falls_back_to_the_free_model_when_rate_limited(monkeypatch):
    calls = []

    async def fake_call(model, prompt, json_output):
        calls.append(model)
        if model == settings.gemini_model:
            raise api_error(429)
        return f"answer from {model}"

    monkeypatch.setattr(llm, "_call", fake_call)
    assert run(llm.generate("hi")) == f"answer from {settings.gemini_fallback_model}"
    assert calls == [settings.gemini_model, settings.gemini_fallback_model]


def test_other_errors_raise_llm_error_without_fallback(monkeypatch):
    calls = []

    async def fake_call(model, prompt, json_output):
        calls.append(model)
        raise api_error(400)

    monkeypatch.setattr(llm, "_call", fake_call)
    with pytest.raises(llm.LLMError):
        run(llm.generate("hi"))
    assert calls == [settings.gemini_model]


def test_fallback_can_be_disabled(monkeypatch):
    async def fake_call(model, prompt, json_output):
        raise api_error(429)

    monkeypatch.setattr(llm, "_call", fake_call)
    monkeypatch.setattr(settings, "gemini_fallback_model", "")
    with pytest.raises(llm.LLMError):
        run(llm.generate("hi"))


def test_missing_api_key_is_an_llm_error(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(llm, "_client", None)
    with pytest.raises(llm.LLMError, match="GEMINI_API_KEY"):
        llm.get_client()
