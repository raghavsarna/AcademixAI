"""Apply database migrations (same as running `alembic upgrade head`)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parent.parent


def alembic_config(database_url: str | None = None) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    if database_url:
        config.attributes["database_url"] = database_url
    return config


def upgrade_to_head(database_url: str | None = None) -> None:
    command.upgrade(alembic_config(database_url), "head")


if __name__ == "__main__":
    upgrade_to_head()
    print("Database is up to date.")
