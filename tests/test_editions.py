import asyncio
import json
from datetime import date

import pytest

from app.config import settings
from app.llm import LLMError
from app.models import Edition, EditionEntry, Paper
from app.services import editions as editions_service
from app.services.chat import AUDIENCE
from app.services.editions import ArxivPaper, build_edition
from tests.conftest import auth_headers

EXPLANATIONS = {"plain": "Like a highlighter.", "student": "Self-attention explained.", "expert": "softmax(QK^T)V."}


def make_paper(n: int, **extra) -> Paper:
    return Paper(
        title=f"Paper {n}",
        authors=["A. Author"],
        origin="arxiv",
        arxiv_id=f"2611.0000{n}",
        what_changed=f"Paper {n} changes thing {n}.",
        change_type="new-method",
        explanations=EXPLANATIONS,
        **extra,
    )


@pytest.fixture
def editions(db):
    made = []
    for day, n in ((date(2026, 11, 3), 2), (date(2026, 11, 4), 3), (date(2026, 11, 5), 1)):
        papers = [make_paper(day.day * 10 + i) for i in range(n)]
        db.add_all(papers)
        db.flush()
        edition = Edition(edition_date=day, headline=f"Headline {day}", overview="What moved.", papers_scanned=400)
        edition.entries = [EditionEntry(paper_id=p.id, rank=i) for i, p in enumerate(papers, 1)]
        edition.themes = [{"name": "Agents", "summary": "About agents.", "papers": [papers[0].id]}]
        db.add(edition)
        made.append(edition)
    db.commit()
    return made


def test_list_is_newest_first_with_entry_counts(client, editions):
    body = client.get("/api/editions").json()
    assert [(e["edition_date"], e["entry_count"]) for e in body] == [
        ("2026-11-05", 1),
        ("2026-11-04", 3),
        ("2026-11-03", 2),
    ]
    assert client.get("/api/editions", params={"limit": 1, "offset": 1}).json()[0]["edition_date"] == "2026-11-04"


def test_latest_and_by_date_link_to_neighbours(client, editions):
    latest = client.get("/api/editions/latest").json()
    assert latest["edition_date"] == "2026-11-05"
    assert (latest["previous_date"], latest["next_date"]) == ("2026-11-04", None)

    middle = client.get("/api/editions/2026-11-04").json()
    assert (middle["previous_date"], middle["next_date"]) == ("2026-11-03", "2026-11-05")
    assert [e["rank"] for e in middle["entries"]] == [1, 2, 3]
    entry = middle["entries"][0]["paper"]
    assert entry["what_changed"] and entry["change_type"] == "new-method"
    assert "explanations" not in entry  # depth texts load with the paper, not the edition
    assert middle["themes"][0]["name"] == "Agents"


def test_missing_edition_is_404(client, editions):
    assert client.get("/api/editions/2026-01-01").status_code == 404
    assert client.get("/api/editions/not-a-date").status_code == 422


def test_no_editions_yet(client):
    assert client.get("/api/editions").json() == []
    assert client.get("/api/editions/latest").status_code == 404


def test_chat_about_an_edition_at_a_chosen_depth(client, editions, fake_llm):
    url = "/api/editions/2026-11-05/chat"
    assert client.post(url, json={"message": "What moved?"}).status_code == 401

    headers = auth_headers(client)
    fake_llm.default = "Agents got faster."
    response = client.post(url, json={"message": "What moved?", "level": "plain"}, headers=headers)
    assert response.json() == {"reply": "Agents got faster."}
    prompt = fake_llm.calls[0]["prompt"]
    assert AUDIENCE["plain"] in prompt
    assert "Paper 50 changes thing 50." in prompt
    assert fake_llm.calls[0]["model"] == settings.gemini_fast_model

    assert client.post(url, json={"message": "Hi", "level": "genius"}, headers=headers).status_code == 422


def test_chat_reports_model_outage_as_503(client, editions, fake_llm):
    fake_llm.replies.append(LLMError("quota exhausted"))
    response = client.post("/api/editions/2026-11-05/chat", json={"message": "Hi"}, headers=auth_headers(client))
    assert response.status_code == 503
    assert "quota" not in response.json()["detail"]


# ---- Generation pipeline


def arxiv_paper(n: int) -> ArxivPaper:
    return ArxivPaper(
        arxiv_id=f"2611.1000{n}",
        title=f"New paper {n}",
        authors=["B. Writer"],
        abstract=f"We propose method {n}.",
        categories=["cs.LG"],
        published=date(2026, 11, 6),
        url=f"https://arxiv.org/abs/2611.1000{n}",
    )


def analysis(n: int) -> str:
    return json.dumps(
        {
            "keywords": ["k"],
            "what_changed": f"Method {n} beats the baseline — by 3 points.",
            "change_type": "new-result",
            "why_it_matters": "Faster models.",
            "builds_on": [{"work": "Baseline", "relation": "compares-with"}],
            "explanations": EXPLANATIONS,
        }
    )


def test_build_edition_end_to_end(db, fake_llm, monkeypatch):
    candidates = [arxiv_paper(n) for n in range(1, 5)]
    monkeypatch.setattr(editions_service, "fetch_papers", lambda day, max_results: (date(2026, 11, 6), candidates))
    triage = {"picks": [{"id": "2611.10003", "reason": "big"}, {"id": "2611.10001v2", "reason": "ok"}, {"id": "nope"}]}
    front = {
        "headline": "Method 3 beats the baseline",
        "overview": "Method 3 leads.",
        "themes": [{"name": "Results", "summary": "Two results.", "paper_ids": ["2611.10003", "2611.10001"]}],
    }
    fake_llm.replies += [json.dumps(triage), analysis(3), analysis(1), json.dumps(front)]

    edition = asyncio.run(build_edition(db, picks=5))

    assert edition.edition_date == date(2026, 11, 6)
    assert edition.papers_scanned == 4
    assert [e.paper.arxiv_id for e in edition.entries] == ["2611.10003", "2611.10001"]  # triage order, bad id dropped
    first = edition.entries[0].paper
    assert first.origin == "arxiv" and first.source_url == "https://arxiv.org/abs/2611.10003"
    assert "—" not in first.what_changed  # em dashes removed
    assert first.explanations == EXPLANATIONS
    assert edition.themes[0]["papers"] == [first.id, edition.entries[1].paper.id]
    assert len(fake_llm.calls) == 4

    # Running again for the same day reuses the edition instead of calling the model
    again = asyncio.run(build_edition(db, picks=5))
    assert again.id == edition.id
    assert len(fake_llm.calls) == 4


def test_build_edition_skips_failed_papers_and_reuses_known_ones(db, fake_llm, monkeypatch):
    known = make_paper(9, source_url="https://arxiv.org/abs/2611.10002")
    known.arxiv_id = "2611.10002"
    db.add(known)
    db.commit()
    candidates = [arxiv_paper(n) for n in range(1, 4)]
    monkeypatch.setattr(editions_service, "fetch_papers", lambda day, max_results: (date(2026, 11, 6), candidates))
    triage = {"picks": [{"id": "2611.10001"}, {"id": "2611.10002"}, {"id": "2611.10003"}]}
    front = {"headline": "", "overview": "Things moved.", "themes": []}
    # Paper 1 analyses fine, paper 2 is already known (no call), paper 3's analysis fails twice
    fake_llm.replies += [json.dumps(triage), analysis(1), LLMError("down"), json.dumps(front)]

    edition = asyncio.run(build_edition(db, picks=3))

    assert [e.paper.arxiv_id for e in edition.entries] == ["2611.10001", "2611.10002"]
    assert edition.headline == "What changed in AI research on November 6"  # empty headline falls back
    assert db.query(Paper).filter_by(arxiv_id="2611.10002").count() == 1


def test_build_edition_fails_when_nothing_could_be_analysed(db, fake_llm, monkeypatch):
    monkeypatch.setattr(
        editions_service, "fetch_papers", lambda day, max_results: (date(2026, 11, 6), [arxiv_paper(1)])
    )
    fake_llm.replies += [json.dumps({"picks": [{"id": "2611.10001"}]}), "not json"]
    with pytest.raises(RuntimeError, match="No paper could be analysed"):
        asyncio.run(build_edition(db))
    assert db.query(Edition).count() == 0
