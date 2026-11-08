import json
from pathlib import Path

import pytest

from app.config import settings
from app.llm import LLMError
from app.models import Paper, Upload, UploadJob
from app.services import jobs
from tests.conftest import UPLOAD_DIR, auth_headers, make_pdf

ANALYSIS = {
    "title": "Attention Is All You Need",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "doi": "https://doi.org/10.48550/arXiv.1706.03762",
    "publication_date": "2017-06-12",
    "source": "NeurIPS 2017",
    "abstract": "We propose the Transformer.",
    "keywords": ["attention", "transformer"],
    "what_changed": "Replaces recurrence with self-attention.",
    "change_type": "new-method",
    "why_it_matters": "Trains much faster.",
    "builds_on": [{"work": "RNN encoder-decoders", "relation": "replaces"}],
    "explanations": {
        "plain": "Reads everything at once.",
        "student": "Self-attention.",
        "expert": "Scaled dot-product.",
    },
    "main_findings": ["Faster training", "Better BLEU"],
    "methodology": "Self-attention only.",
}


def upload(client, headers, data: bytes, filename: str = "paper.pdf"):
    return client.post("/api/papers", files={"file": (filename, data, "application/pdf")}, headers=headers)


def explain(client, headers, data: bytes, filename: str = "paper.pdf") -> dict:
    """Upload a PDF and return its job once the background analysis has run.

    The test client runs background tasks before it returns, so the job is finished here.
    """
    response = upload(client, headers, data, filename)
    assert response.status_code in (200, 202), response.text
    return client.get(f"/api/papers/jobs/{response.json()['id']}", headers=headers).json()


def test_upload_requires_login(client, fake_llm):
    assert upload(client, {}, make_pdf()).status_code == 401


def test_upload_analyses_and_stores_paper(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies.append(json.dumps(ANALYSIS))
    response = upload(client, headers, make_pdf())

    # Answered at once with a queued job; the analysis runs after the response
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "queued"
    assert response.json()["url"] is None

    job = client.get(f"/api/papers/jobs/{response.json()['id']}", headers=headers).json()
    assert job["status"] == "ready"
    assert job["error"] is None
    assert job["url"] == f"/papers/{job['paper_id']}"
    assert job["paper_title"] == "Attention Is All You Need"
    assert fake_llm.calls[0]["json_output"] is True
    assert "We propose the Transformer" in fake_llm.calls[0]["prompt"]

    paper = db.get(Paper, job["paper_id"])
    assert len(paper.id) == 32
    assert paper.doi == "10.48550/arXiv.1706.03762"  # URL prefix removed
    assert paper.origin == "upload"
    assert paper.main_findings == "- Faster training\n- Better BLEU"  # list turned into markdown
    assert paper.arxiv_id == "1706.03762"  # read from the arXiv DOI
    assert paper.source_url == "https://arxiv.org/abs/1706.03762"
    assert paper.explanations["plain"] == "Reads everything at once."
    assert paper.builds_on == [{"work": "RNN encoder-decoders", "relation": "replaces"}]
    assert "Transformer" in paper.full_text
    upload_row = db.query(Upload).one()
    assert upload_row.filename == "paper.pdf"
    assert (Path(UPLOAD_DIR) / upload_row.pdf_key).read_bytes()[:5] == b"%PDF-"


def test_same_file_is_not_analysed_twice(client, db, fake_llm):
    fake_llm.replies.append(json.dumps(ANALYSIS))
    data = make_pdf()
    first = explain(client, auth_headers(client, "alice"), data)
    second = upload(client, auth_headers(client, "bobby"), data)

    # Ready at once, without a second analysis
    assert second.status_code == 200
    assert second.json()["status"] == "ready"
    assert second.json()["paper_id"] == first["paper_id"]
    assert len(fake_llm.calls) == 1
    assert db.query(Upload).count() == 2


def test_same_doi_in_a_different_file_reuses_the_paper(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [json.dumps(ANALYSIS), json.dumps(ANALYSIS)]
    first = explain(client, headers, make_pdf("Version one of the paper"))
    second = explain(client, headers, make_pdf("Version two, with a different layout"))
    assert second["status"] == "ready"
    assert second["paper_id"] == first["paper_id"]
    assert db.query(Paper).count() == 1
    assert db.query(Upload).count() == 1  # the same user isn't linked twice
    # The second PDF wasn't needed, so it isn't kept
    assert db.get(UploadJob, second["id"]).pdf_key is None
    assert len(list(Path(UPLOAD_DIR).iterdir())) == 1


def test_my_papers_only_lists_own_uploads(client, fake_llm):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bobby")
    fake_llm.replies.append(json.dumps(ANALYSIS))
    explain(client, alice, make_pdf(), filename="attention.pdf")

    mine = client.get("/api/papers", headers=alice).json()
    assert [(p["title"], p["filename"]) for p in mine] == [("Attention Is All You Need", "attention.pdf")]
    assert client.get("/api/papers", headers=bob).json() == []
    assert client.get("/api/papers").status_code == 401


def test_paper_detail(client, fake_llm):
    fake_llm.replies.append(json.dumps({**ANALYSIS, "title": "Attention <script>alert(1)</script>"}))
    paper_id = explain(client, auth_headers(client), make_pdf())["paper_id"]

    detail = client.get(f"/api/papers/{paper_id}")
    assert detail.status_code == 200
    assert detail.json()["keywords"] == ["attention", "transformer"]
    assert set(detail.json()["explanations"]) == {"plain", "student", "expert"}
    assert "full_text" not in detail.json()

    assert detail.json()["title"] == "Attention <script>alert(1)</script>"  # stored as text; the web app escapes it

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
    headers = auth_headers(client)
    response = upload(client, headers, data)
    assert response.status_code == 422
    assert message in response.json()["detail"]
    assert fake_llm.calls == []
    assert client.get("/api/papers/jobs", headers=headers).json() == []


def test_upload_size_limit(client, fake_llm, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    response = upload(client, auth_headers(client), b"%PDF-" + b"0" * (1024 * 1024 + 10))
    assert response.status_code == 422
    assert "too large" in response.json()["detail"]


def test_unparseable_model_reply_fails_the_job_and_it_can_be_retried(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += ["Sorry, I can't help with that.", "Still not JSON."]
    job = explain(client, headers, make_pdf())
    assert job["status"] == "failed"
    assert job["error"] == jobs.UNREADABLE
    assert db.query(Paper).count() == 0

    # The PDF was kept, so the same upload can be tried again
    fake_llm.replies.append(json.dumps(ANALYSIS))
    retried = client.post(f"/api/papers/jobs/{job['id']}/retry", headers=headers)
    assert retried.status_code == 200
    job = client.get(f"/api/papers/jobs/{job['id']}", headers=headers).json()
    assert job["status"] == "ready"
    assert db.get(Paper, job["paper_id"]).title == "Attention Is All You Need"

    assert client.post(f"/api/papers/jobs/{job['id']}/retry", headers=headers).status_code == 409


def test_model_outage_fails_the_job_with_a_busy_message(client, fake_llm):
    fake_llm.replies.append(LLMError("down"))
    job = explain(client, auth_headers(client), make_pdf())
    assert job["status"] == "failed"
    assert job["error"] == jobs.BUSY


def test_jobs_belong_to_their_uploader(client, fake_llm):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bobby")
    fake_llm.default = json.dumps(ANALYSIS)
    job = explain(client, alice, make_pdf(), filename="attention.pdf")

    assert [(j["filename"], j["status"]) for j in client.get("/api/papers/jobs", headers=alice).json()] == [
        ("attention.pdf", "ready")
    ]
    assert client.get("/api/papers/jobs", headers=bob).json() == []
    assert client.get(f"/api/papers/jobs/{job['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/papers/jobs/{job['id']}", headers=bob).status_code == 404
    assert client.get("/api/papers/jobs").status_code == 401


def test_dismissing_jobs(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [LLMError("down"), json.dumps(ANALYSIS)]
    failed = explain(client, headers, make_pdf("one"))
    ready = explain(client, headers, make_pdf("two"))

    # A failed job's PDF goes with it; a ready job's paper stays in the library
    assert client.delete(f"/api/papers/jobs/{failed['id']}", headers=headers).status_code == 204
    assert client.delete(f"/api/papers/jobs/{ready['id']}", headers=headers).status_code == 204
    assert client.get("/api/papers/jobs", headers=headers).json() == []
    assert len(client.get("/api/papers", headers=headers).json()) == 1
    assert len(list(Path(UPLOAD_DIR).iterdir())) == 1

    running = UploadJob(user_id=1, filename="x.pdf", file_hash="0" * 64, status="analysing")
    db.add(running)
    db.commit()
    assert client.delete(f"/api/papers/jobs/{running.id}", headers=headers).status_code == 409


def test_jobs_cut_short_by_a_restart_are_marked_failed(client, db):
    auth_headers(client)
    for status in ("queued", "reading", "analysing", "ready"):
        db.add(UploadJob(user_id=1, filename=f"{status}.pdf", file_hash="0" * 64, status=status))
    db.commit()

    assert jobs.fail_interrupted() == 3
    db.expire_all()
    statuses = {j.filename: (j.status, j.error) for j in db.query(UploadJob)}
    assert statuses["analysing.pdf"] == ("failed", jobs.INTERRUPTED)
    assert statuses["ready.pdf"] == ("ready", None)


def test_uploads_are_rate_limited(client, fake_llm, monkeypatch):
    monkeypatch.setattr(settings, "uploads_per_hour", 1)
    headers = auth_headers(client)
    fake_llm.default = json.dumps(ANALYSIS)
    assert upload(client, headers, make_pdf("one")).status_code == 202
    assert upload(client, headers, make_pdf("two")).status_code == 429


def test_chat_about_a_paper(client, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [json.dumps(ANALYSIS), "It uses self-attention."]
    paper_id = explain(client, headers, make_pdf())["paper_id"]

    assert client.post(f"/api/papers/{paper_id}/chat", json={"message": "How?"}).status_code == 401
    response = client.post(f"/api/papers/{paper_id}/chat", json={"message": "How?"}, headers=headers)
    assert response.json() == {"reply": "It uses self-attention."}
    assert "Self-attention only." in fake_llm.calls[-1]["prompt"]
    assert client.post("/api/papers/nope/chat", json={"message": "How?"}, headers=headers).status_code == 404


def test_uploading_a_paper_from_an_edition_enriches_it(client, db, fake_llm):
    edition_paper = Paper(
        title="Attention Is All You Need",
        origin="arxiv",
        arxiv_id="1706.03762",
        what_changed="From the abstract.",
        explanations={"plain": "Short."},
    )
    db.add(edition_paper)
    db.commit()
    fake_llm.replies.append(json.dumps(ANALYSIS))
    job = explain(client, auth_headers(client), make_pdf())

    assert job["paper_id"] == edition_paper.id
    db.refresh(edition_paper)
    assert edition_paper.main_findings == "- Faster training\n- Better BLEU"
    assert edition_paper.explanations["expert"] == "Scaled dot-product."
    assert db.query(Paper).count() == 1


def test_chat_about_a_paper_uses_the_chosen_depth(client, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies += [json.dumps(ANALYSIS), "Simply put, it reads everything at once."]
    paper_id = explain(client, headers, make_pdf())["paper_id"]
    response = client.post(f"/api/papers/{paper_id}/chat", json={"message": "How?", "level": "plain"}, headers=headers)
    assert response.status_code == 200
    assert "no technical background" in fake_llm.calls[-1]["prompt"]


def test_deleting_a_paper_removes_it_and_its_pdf(client, db, fake_llm):
    headers = auth_headers(client)
    fake_llm.replies.append(json.dumps(ANALYSIS))
    job = explain(client, headers, make_pdf())
    paper_id = job["paper_id"]
    assert len(list(Path(UPLOAD_DIR).iterdir())) == 1

    assert client.delete(f"/api/papers/{paper_id}").status_code == 401
    assert client.delete(f"/api/papers/{paper_id}", headers=headers).status_code == 204

    assert client.get("/api/papers", headers=headers).json() == []
    assert client.get("/api/papers/jobs", headers=headers).json() == []
    assert client.get(f"/api/papers/{paper_id}").status_code == 404
    assert list(Path(UPLOAD_DIR).iterdir()) == []
    assert client.delete(f"/api/papers/{paper_id}", headers=headers).status_code == 404


def test_deleting_a_shared_paper_keeps_it_for_the_other_reader(client, db, fake_llm):
    alice = auth_headers(client, "alice")
    bob = auth_headers(client, "bobby")
    fake_llm.replies.append(json.dumps(ANALYSIS))
    data = make_pdf()
    paper_id = explain(client, alice, data)["paper_id"]
    explain(client, bob, data)

    # Bob can't delete it from Alice's library, only from his own
    assert client.delete(f"/api/papers/{paper_id}", headers=bob).status_code == 204
    assert client.get("/api/papers", headers=bob).json() == []
    assert [p["id"] for p in client.get("/api/papers", headers=alice).json()] == [paper_id]
    assert client.get(f"/api/papers/{paper_id}").status_code == 200


def test_deleting_an_edition_paper_keeps_its_page(client, db, fake_llm):
    edition_paper = Paper(title="Attention Is All You Need", origin="arxiv", arxiv_id="1706.03762")
    db.add(edition_paper)
    db.commit()
    headers = auth_headers(client)
    fake_llm.replies.append(json.dumps(ANALYSIS))
    assert explain(client, headers, make_pdf())["paper_id"] == edition_paper.id

    assert client.delete(f"/api/papers/{edition_paper.id}", headers=headers).status_code == 204
    assert client.get("/api/papers", headers=headers).json() == []
    assert client.get(f"/api/papers/{edition_paper.id}").status_code == 200


def test_a_paper_outside_your_library_cant_be_deleted(client, db, fake_llm):
    fake_llm.replies.append(json.dumps(ANALYSIS))
    paper_id = explain(client, auth_headers(client, "alice"), make_pdf())["paper_id"]
    assert client.delete(f"/api/papers/{paper_id}", headers=auth_headers(client, "bobby")).status_code == 404
    assert client.get(f"/api/papers/{paper_id}").status_code == 200
