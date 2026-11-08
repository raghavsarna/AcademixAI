from datetime import UTC, datetime, timedelta

import pytest

from app.config import settings
from app.llm import LLMError
from app.models import Digest
from tests.conftest import auth_headers


@pytest.fixture
def digests(db):
    now = datetime.now(UTC)
    items = [
        Digest(
            title=f"Digest {i}",
            description=f"About day {i}",
            content=f"Content of digest {i}",
            published_at=now - timedelta(days=i),
        )
        for i in range(3)
    ]
    db.add_all(items)
    db.commit()
    return items


def test_list_is_newest_first_and_paginated(client, digests):
    response = client.get("/api/digests")
    assert response.status_code == 200
    assert [d["title"] for d in response.json()] == ["Digest 0", "Digest 1", "Digest 2"]
    assert "content" not in response.json()[0]

    page = client.get("/api/digests", params={"limit": 1, "offset": 1}).json()
    assert [d["title"] for d in page] == ["Digest 1"]
    assert client.get("/api/digests", params={"limit": 0}).status_code == 422


def test_get_digest(client, digests):
    response = client.get(f"/api/digests/{digests[1].id}")
    assert response.status_code == 200
    assert response.json()["content"] == "Content of digest 1"
    assert client.get("/api/digests/9999").status_code == 404


def test_chat_requires_login(client, digests, fake_llm):
    response = client.post(f"/api/digests/{digests[0].id}/chat", json={"message": "Hi"})
    assert response.status_code == 401
    assert fake_llm.calls == []


def test_chat_answers_from_the_digest(client, digests, fake_llm):
    headers = auth_headers(client)
    fake_llm.default = "  The main trend is efficiency.  "
    response = client.post(f"/api/digests/{digests[0].id}/chat", json={"message": "What's the trend?"}, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"reply": "The main trend is efficiency."}
    prompt = fake_llm.calls[0]["prompt"]
    assert "Content of digest 0" in prompt
    assert "What's the trend?" in prompt
    assert fake_llm.calls[0]["model"] == settings.gemini_fast_model


def test_chat_validates_message(client, digests, fake_llm):
    headers = auth_headers(client)
    url = f"/api/digests/{digests[0].id}/chat"
    assert client.post(url, json={"message": ""}, headers=headers).status_code == 422
    assert client.post(url, json={"message": "x" * 2001}, headers=headers).status_code == 422


def test_chat_reports_model_outage_as_503(client, digests, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies.append(LLMError("quota exhausted"))
    response = client.post(f"/api/digests/{digests[0].id}/chat", json={"message": "Hi"}, headers=headers)
    assert response.status_code == 503
    assert "quota" not in response.json()["detail"]


def test_chat_is_rate_limited_per_user(client, digests, fake_llm, monkeypatch):
    monkeypatch.setattr(settings, "chat_requests_per_minute", 2)
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bobby")
    url = f"/api/digests/{digests[0].id}/chat"
    codes = [client.post(url, json={"message": "Hi"}, headers=alice).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
    assert client.post(url, json={"message": "Hi"}, headers=bob).status_code == 200
