"""The one place that talks to Gemini."""
import logging
from typing import Optional

from google import genai
from google.genai import errors, types

from config import settings

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _call(model: str, prompt: str, json_output: bool = False) -> str:
    config = types.GenerateContentConfig(response_mime_type="application/json") if json_output else None
    response = get_client().models.generate_content(model=model, contents=prompt, config=config)
    return response.text or ""


def generate(prompt: str, model: Optional[str] = None, json_output: bool = False) -> str:
    """Send a prompt to Gemini and return the response text.

    json_output=True asks the model to reply with a valid JSON document.
    If the model is rate limited (HTTP 429), retry once on the fallback model.
    """
    model = model or settings.gemini_model
    try:
        return _call(model, prompt, json_output)
    except errors.APIError as e:
        fallback = settings.gemini_fallback_model
        if e.code != 429 or not fallback or fallback == model:
            raise
        logger.warning("%s is rate limited, falling back to %s", model, fallback)
        return _call(fallback, prompt, json_output)
