"""The one place that talks to Gemini."""

import asyncio
import logging
from collections.abc import AsyncIterator

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


async def generate_stream(prompt: str, model: str | None = None) -> AsyncIterator[str]:
    """Stream the model's reply as it is written.

    Opening the stream falls back like generate() does: a rate-limited or overloaded model
    hands over to the fallback model before any text has been sent. An error part-way through
    raises LLMError.
    """
    model = model or settings.gemini_model

    async def open_stream(name: str):
        return await get_client().aio.models.generate_content_stream(model=name, contents=prompt)

    try:
        try:
            stream = await open_stream(model)
        except errors.APIError as e:
            fallback = settings.gemini_fallback_model
            if e.code not in FALLBACK_CODES or not fallback or fallback == model:
                raise
            logger.warning("%s answered %s, streaming from %s instead", model, e.code, fallback)
            model = fallback
            stream = await open_stream(fallback)
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"{model} failed: {e}") from e


EMBED_BATCH = 100  # the most texts the embedding endpoint takes in one call


async def embed(texts: list[str], task: str) -> list[list[float]]:
    """Embed texts for retrieval. task is "RETRIEVAL_DOCUMENT" for chunks or "RETRIEVAL_QUERY" for a question."""
    config = types.EmbedContentConfig(task_type=task, output_dimensionality=settings.embedding_dimensions)
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), EMBED_BATCH):
            batch = texts[start : start + EMBED_BATCH]
            response = await get_client().aio.models.embed_content(
                model=settings.gemini_embedding_model, contents=batch, config=config
            )
            vectors += [list(e.values or []) for e in response.embeddings or []]
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"Embedding failed: {e}") from e
    if len(vectors) != len(texts):
        raise LLMError(f"Embedding returned {len(vectors)} vectors for {len(texts)} texts")
    return vectors
