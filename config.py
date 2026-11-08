"""Application settings, loaded from environment variables or a local .env file.

Never hardcode secrets in source files. Copy .env.example to .env and fill it in.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Secrets
    gemini_api_key: str = ""
    secret_key: str  # used to sign JWTs; required, the app refuses to start without it

    # Gemini models
    gemini_model: str = "gemini-2.5-flash"  # paper analysis and digest generation
    gemini_fast_model: str = "gemini-2.5-flash-lite"  # chat replies

    # Database / auth
    database_url: str = "sqlite:///db/research.db"
    access_token_expire_minutes: int = 30


settings = Settings()
