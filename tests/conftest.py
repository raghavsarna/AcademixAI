"""Shared test setup.

Tests use their own database (a temporary SQLite file, or TEST_DATABASE_URL if set)
and never call the real model: the `fake_llm` fixture stands in for it.
"""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="academixai-tests-")
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_TMP}/test.db")
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256-signing"
os.environ["GEMINI_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = f"{_TMP}/uploads"

import pymupdf  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import llm  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.rate_limit import limiter  # noqa: E402

UPLOAD_DIR = os.environ["UPLOAD_DIR"]


@pytest.fixture(autouse=True)
def fresh_state():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    limiter.reset()
    yield


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


class FakeLLM:
    """Records prompts and returns queued replies (or raises queued exceptions)."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.replies: list = []
        self.default = "A helpful answer."

    async def __call__(self, prompt: str, model: str | None = None, json_output: bool = False) -> str:
        self.calls.append({"prompt": prompt, "model": model, "json_output": json_output})
        reply = self.replies.pop(0) if self.replies else self.default
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def fake_llm(monkeypatch) -> FakeLLM:
    fake = FakeLLM()
    monkeypatch.setattr(llm, "generate", fake)
    return fake


def register(client: TestClient, username: str = "alice", password: str = "correct-horse-1") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": f"{username}@example.com", "username": username, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(client: TestClient, username: str = "alice", password: str = "correct-horse-1") -> dict:
    register(client, username, password)
    response = client.post("/api/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def make_pdf(text: str = "Attention Is All You Need. We propose the Transformer.") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(72, 72, 540, 770), text)
    data = doc.tobytes()
    doc.close()
    return data
