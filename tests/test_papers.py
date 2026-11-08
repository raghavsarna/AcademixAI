import json
from pathlib import Path

import pytest

from app.config import settings
from app.llm import LLMError
from app.models import Paper, Upload
from tests.conftest import UPLOAD_DIR, auth_headers, make_pdf

ANALYSIS = {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "doi": "https://doi.org/10.48550/arXiv.1706.03762",
    "publication_date": "2017-06-12",
    "source": "NeurIPS 2017",
    "abstract": "We propose the Transformer.",
    "keywords": ["attention", "transformer"],
    "summary": "A **new** architecture.",
    "main_findings": ["Faster training", "Better BLEU"],
    "methodology": "Self-attention only.",
}


def upload(client, headers, data: bytes, filename: str = "paper.pdf"):
    return client.post("/api/papers", files={"file": (filename, data, "application/pdf")}, headers=headers)


def test_upload_requires_login(client, fake_llm):
    assert upload(client, {}, make_pdf()).status_code == 401


def test_upload_analyses_and_stores_paper(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies.append(json.dumps(ANALYSIS))
    response = upload(client, headers, make_pdf())

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["created"] is True
    assert body["url"] == f"/papers/{body['paper']['id']}"
    assert body["paper"]["doi"] == "10.48550/arXiv.1706.03762"  # URL prefix removed
    assert fake_llm.calls[0]["json_output"] is True
    assert "We propose the Transformer" in fake_llm.calls[0]["prompt"]

    paper = db.get(Paper, body["paper"]["id"])
    assert len(paper.id) == 32
    assert paper.main_findings == "- Faster training\n- Better BLEU"  # list turned into markdown
    assert "Transformer" in paper.full_text
    upload_row = db.query(Upload).one()
    assert upload_row.filename == "paper.pdf"
    assert (Path(UPLOAD_DIR) / upload_row.pdf_key).read_bytes()[:5] == b"%PDF-"


def test_same_file_is_not_analysed_twice(client, db, fake_llm):
    fake_llm.replies.append(json.dumps(ANALYSIS))
    data = make_pdf()
    first = upload(client, auth_headers(client, "alice"), data).json()
    second = upload(client, auth_headers(client, "bobby"), data)

    assert second.status_code == 200
    assert second.json()["created"] is False
    assert second.json()["paper"]["id"] == first["paper"]["id"]
    assert len(fake_llm.calls) == 1
    assert db.query(Upload).count() == 2


def test_same_doi_in_a_different_file_reuses_the_paper(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [json.dumps(ANALYSIS), json.dumps(ANALYSIS)]
    first = upload(client, headers, make_pdf("Version one of the paper")).json()
    second = upload(client, headers, make_pdf("Version two, with a different layout")).json()
    assert second["created"] is False
    assert second["paper"]["id"] == first["paper"]["id"]
    assert db.query(Paper).count() == 1
    assert db.query(Upload).count() == 1  # the same user isn't linked twice


def test_my_papers_only_lists_own_uploads(client, fake_llm):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bobby")
    fake_llm.replies.append(json.dumps(ANALYSIS))
    upload(client, alice, make_pdf(), filename="attention.pdf")

    mine = client.get("/api/papers", headers=alice).json()
    assert [(p["title"], p["filename"]) for p in mine] == [("Attention Is All You Need", "attention.pdf")]
    assert client.get("/api/papers", headers=bob).json() == []
    assert client.get("/api/papers").status_code == 401


def test_paper_detail_and_page(client, fake_llm):
    fake_llm.replies.append(json.dumps({**ANALYSIS, "title": "Attention <script>alert(1)</script>"}))
    paper_id = upload(client, auth_headers(client), make_pdf()).json()["paper"]["id"]

    detail = client.get(f"/api/papers/{paper_id}")
    assert detail.status_code == 200
    assert detail.json()["keywords"] == ["attention", "transformer"]
    assert "full_text" not in detail.json()

    page = client.get(f"/papers/{paper_id}")
    assert page.status_code == 200
    assert "<script>alert(1)</script>" not in page.text
    assert "Attention &lt;script&gt;" in page.text

    assert client.get("/api/papers/does-not-exist").status_code == 404


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "empty"),
        (b"not a pdf at all", "Only PDF files"),
        (make_pdf(""), "No text was found"),
        (b"%PDF-1.7 broken", "couldn't be read"),
    ],
)
def test_upload_rejects_unusable_files(client, fake_llm, data, message):
    response = upload(client, auth_headers(client), data)
    assert response.status_code == 422
    assert message in response.json()["detail"]
    assert fake_llm.calls == []


def test_upload_size_limit(client, fake_llm, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    response = upload(client, auth_headers(client), b"%PDF-" + b"0" * (1024 * 1024 + 10))
    assert response.status_code == 422
    assert "too large" in response.json()["detail"]


def test_unparseable_model_reply_is_a_502(client, db, fake_llm):
    fake_llm.replies.append("Sorry, I can't help with that.")
    response = upload(client, auth_headers(client), make_pdf())
    assert response.status_code == 502
    assert db.query(Paper).count() == 0


def test_model_outage_during_upload_is_a_503(client, fake_llm):
    fake_llm.replies.append(LLMError("down"))
    assert upload(client, auth_headers(client), make_pdf()).status_code == 503


def test_uploads_are_rate_limited(client, fake_llm, monkeypatch):
    monkeypatch.setattr(settings, "uploads_per_hour", 1)
    headers = auth_headers(client)
    fake_llm.default = json.dumps(ANALYSIS)
    assert upload(client, headers, make_pdf("one")).status_code == 201
    assert upload(client, headers, make_pdf("two")).status_code == 429


def test_chat_about_a_paper(client, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [json.dumps(ANALYSIS), "It uses self-attention."]
    paper_id = upload(client, headers, make_pdf()).json()["paper"]["id"]

    assert client.post(f"/api/papers/{paper_id}/chat", json={"message": "How?"}).status_code == 401
    response = client.post(f"/api/papers/{paper_id}/chat", json={"message": "How?"}, headers=headers)
    assert response.json() == {"reply": "It uses self-attention."}
    assert "Self-attention only." in fake_llm.calls[-1]["prompt"]
    assert client.post("/api/papers/nope/chat", json={"message": "How?"}, headers=headers).status_code == 404
