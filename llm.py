"""The one place that talks to Gemini."""
from typing import Optional

from google import genai

from config import settings

_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def generate(prompt: str, model: Optional[str] = None) -> str:
    """Send a prompt to Gemini and return the response text."""
    response = get_client().models.generate_content(
        model=model or settings.gemini_model,
        contents=prompt,
    )
    return response.text or ""
