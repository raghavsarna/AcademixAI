"""Alembic environment. The database URL and models come from the app itself."""

from logging.config import fileConfig

from alembic import context

import app.models  # noqa: F401  (registers the models on Base.metadata)
from app.config import settings
from app.db import Base, build_engine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Tests and scripts can pass a URL explicitly; otherwise use the app's settings
DATABASE_URL = config.attributes.get("database_url") or settings.sqlalchemy_url


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=DATABASE_URL.startswith("sqlite"),
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_with(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _run_with(connection)
        return
    engine = build_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            _run_with(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
