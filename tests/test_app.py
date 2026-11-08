"""Pages, health check and migrations."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.db import Base
from scripts.migrate import upgrade_to_head


@pytest.mark.parametrize("path", ["/", "/home", "/content", "/login", "/register", "/profile", "/upload"])
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "/static/js/safe.js" in response.text


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_openapi_schema_lists_the_api(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/api/auth/token", "/api/digests", "/api/papers", "/api/papers/{paper_id}/chat"} <= set(paths)


def test_migrations_match_the_models(tmp_path):
    url = f"sqlite:///{tmp_path}/migrated.db"
    upgrade_to_head(url)
    engine = create_engine(url)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()
    assert diff == []


def test_timestamps_are_returned_with_a_timezone(client):
    client.post(
        "/api/auth/register", json={"email": "t@example.com", "username": "tz_user", "password": "password-123"}
    )
    token = client.post("/api/auth/token", data={"username": "tz_user", "password": "password-123"}).json()
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"}).json()
    assert me["created_at"].endswith(("Z", "+00:00"))
