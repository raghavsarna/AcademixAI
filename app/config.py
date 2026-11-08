"""Application settings, loaded from environment variables or a local .env file.

Never hardcode secrets in source files. Copy .env.example to .env and fill it in.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"

    # Secrets
    gemini_api_key: str = ""
    secret_key: str  # signs login tokens; the app refuses to start without it

    # Gemini models. 3.1 Flash-Lite is the cheapest Gemini model open to new
    # projects (Nov 2026). It shuts down on May 7, 2027; the recommended
    # replacement is gemini-3.5-flash-lite.
    gemini_model: str = "gemini-3.1-flash-lite"  # paper analysis and daily editions
    gemini_fast_model: str = "gemini-3.1-flash-lite"  # chat replies
    # Used automatically when the main model hits its rate limit.
    # Gemma is free of charge on the Gemini API. Set to "" to disable.
    gemini_fallback_model: str = "gemma-4-26b-a4b-it"
    # Embeds chunks of each paper for retrieval-based chat. Free on the Gemini API.
    gemini_embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    # Database: SQLite locally, Postgres in production
    # (e.g. postgresql://user:pass@host/db)
    database_url: str = "sqlite:///db/academixai.db"

    # Auth
    access_token_expire_minutes: int = 60

    # Uploads
    upload_dir: str = "uploads"
    max_upload_mb: int = 20
    max_pdf_chars: int = 150_000  # text sent to the model per paper
    max_arxiv_pdf_mb: int = 30  # full text fetched from arXiv when a reader first asks about a paper

    # Rate limits (per user, or per IP address for login and sign-up)
    chat_requests_per_minute: int = 10
    uploads_per_hour: int = 10
    login_attempts_per_minute: int = 10
    signups_per_hour: int = 10

    # Origins allowed to call the API from a browser (the future web frontend)
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def sqlalchemy_url(self) -> str:
        """Database URL with the right driver for SQLAlchemy."""
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


settings = Settings()
