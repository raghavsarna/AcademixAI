"""Application settings, loaded from environment variables or a local .env file.

Never hardcode secrets in source files. Copy .env.example to .env and fill it in.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Secrets
    gemini_api_key: str = ""
    secret_key: str  # used to sign JWTs; required, the app refuses to start without it

    # Gemini models. 3.1 Flash-Lite is the cheapest Gemini model open to new
    # projects (Nov 2026). It is scheduled to shut down on May 7, 2027; the
    # recommended replacement is gemini-3.5-flash-lite.
    gemini_model: str = "gemini-3.1-flash-lite"  # paper analysis and digest generation
    gemini_fast_model: str = "gemini-3.1-flash-lite"  # chat replies
    # Used automatically when the main model hits its rate limit.
    # Gemma is free of charge on the Gemini API. Set to "" to disable.
    gemini_fallback_model: str = "gemma-4-26b-a4b-it"

    # Database / auth
    database_url: str = "sqlite:///db/research.db"
    access_token_expire_minutes: int = 30


settings = Settings()
