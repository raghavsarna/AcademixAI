"""The one place that talks to Gemini."""

import asyncio
import logging

from google import genai
from google.genai import errors, types

from app.config import settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

RETRY_DELAY_SECONDS = 2.0

# Rate limited or overloaded: worth trying the fallback model
FALLBACK_CODES = (429, 503)


class LLMError(Exception):
    """The model could not produce an answer (not configured, rate limited or failing)."""


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise LLMError("GEMINI_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def _call(model: str, prompt: str, json_output: bool) -> str:
    config = types.GenerateContentConfig(response_mime_type="application/json") if json_output else None
    response = await get_client().aio.models.generate_content(model=model, contents=prompt, config=config)
    return response.text or ""


async def _call_with_retry(model: str, prompt: str, json_output: bool) -> str:
    """One retry for server errors and dropped connections; client errors (4xx) are not retried."""
    try:
        return await _call(model, prompt, json_output)
    except errors.ClientError:
        raise
    except Exception as e:
        logger.warning("%s call failed (%s), retrying once", model, type(e).__name__)
        await asyncio.sleep(RETRY_DELAY_SECONDS)
        return await _call(model, prompt, json_output)


async def generate(prompt: str, model: str | None = None, json_output: bool = False) -> str:
    """Send a prompt to the model and return its text reply.

    json_output=True asks the model to reply with a JSON document.
    Server errors and dropped connections are retried once. If the model is rate limited
    (HTTP 429) or overloaded (HTTP 503), the request moves to the fallback model. Raises LLMError if no answer
    could be produced.
    """
    model = model or settings.gemini_model
    try:
        return await _call_with_retry(model, prompt, json_output)
    except errors.APIError as e:
        fallback = settings.gemini_fallback_model
        if e.code in FALLBACK_CODES and fallback and fallback != model:
            logger.warning("%s answered %s, falling back to %s", model, e.code, fallback)
            try:
                return await _call_with_retry(fallback, prompt, json_output)
            except Exception as fallback_error:
                raise LLMError(f"{fallback} failed: {fallback_error}") from fallback_error
        raise LLMError(f"{model} failed: {e}") from e
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"{model} failed: {e}") from e
