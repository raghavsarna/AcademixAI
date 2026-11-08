import asyncio

import pytest
from google.genai import errors

from app import llm
from app.config import settings


def api_error(code: int) -> errors.APIError:
    error = errors.ClientError if code < 500 else errors.ServerError
    return error(code, {"error": {"code": code, "message": "error"}})


def run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize("code", [429, 503])
def test_falls_back_to_the_free_model_when_rate_limited_or_overloaded(monkeypatch, code):
    calls = []

    async def fake_call(model, prompt, json_output):
        calls.append(model)
        if model == settings.gemini_model:
            raise api_error(code)
        return f"answer from {model}"

    async def no_sleep(_):
        pass

    monkeypatch.setattr(llm.asyncio, "sleep", no_sleep)

    monkeypatch.setattr(llm, "_call", fake_call)
    assert run(llm.generate("hi")) == f"answer from {settings.gemini_fallback_model}"
    # A 503 is retried once on the same model before falling back
    expected = [settings.gemini_model] * (2 if code >= 500 else 1) + [settings.gemini_fallback_model]
    assert calls == expected


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


def test_server_errors_and_dropped_connections_are_retried_once(monkeypatch):
    monkeypatch.setattr(llm, "RETRY_DELAY_SECONDS", 0)
    calls = []

    async def flaky(model, prompt, json_output):
        calls.append(model)
        if len(calls) == 1:
            raise ConnectionError("reset by peer")
        return "ok"

    monkeypatch.setattr(llm, "_call", flaky)
    assert run(llm.generate("hi")) == "ok"
    assert calls == [settings.gemini_model, settings.gemini_model]


def test_repeated_network_failure_becomes_llm_error(monkeypatch):
    monkeypatch.setattr(llm, "RETRY_DELAY_SECONDS", 0)

    async def down(model, prompt, json_output):
        raise errors.ServerError(503, {"error": {"code": 503, "message": "unavailable"}})

    monkeypatch.setattr(llm, "_call", down)
    with pytest.raises(llm.LLMError):
        run(llm.generate("hi"))
