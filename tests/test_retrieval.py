import asyncio
import json

from app.llm import LLMError
from app.models import Paper, PaperChunk
from app.services import retrieval
from app.services.retrieval import MAX_CHARS, bm25_rank, fuse, split_into_passages
from tests.conftest import auth_headers, make_pdf
from tests.test_papers import ANALYSIS, explain


def para(topic: str, n: int = 24) -> str:
    """A paragraph of n sentences about one topic, split over PDF-style short lines."""
    sentence = f"The {topic} result is discussed here in some detail for the reader."
    return "\n".join([sentence] * n)


PAPER_TEXT = "\f".join(
    [
        # Page 1
        "A Study of Things\nAda Lovelace\nAbstract\n" + para("summary", 3) + "\n1\nIntroduction\n" + para("motivation"),
        # Page 2: a table full of numbers must not be read as headings
        "2\nMethod\n"
        + para("attention")
        + "\n91.7\nTransformer (4 layers)\n3.0\nValidation Loss\n2.1\nTraining Setup\n"
        + para("optimizer"),
        # Page 3: results, then the reference list (skipped), then an appendix (kept)
        "3\nResults\n"
        + para("bleu")
        + "\nReferences\n[1] A. Author. A cited paper. 2017.\n[2] B. Author. Another. 2018.\n"
        + "A\nExtra Experiments\n"
        + para("appendix"),
    ]
)


def test_passages_follow_sections_and_pages():
    passages = split_into_passages(PAPER_TEXT)
    sections = list(dict.fromkeys(p.section for p in passages))
    assert sections == [
        "Abstract",
        "1 Introduction",
        "2 Method",
        "2.1 Training Setup",
        "3 Results",
        "A Extra Experiments",
    ]
    pages = {p.section: p.page for p in passages}
    assert pages["1 Introduction"] == 1 and pages["2 Method"] == 2 and pages["3 Results"] == 3
    assert not any("cited paper" in p.text for p in passages)  # the reference list is left out
    assert all(len(p.text) <= MAX_CHARS + 200 for p in passages)
    # Long sections are split, with a little overlap so a point across the split is still found
    intro = [p for p in passages if p.section == "1 Introduction"]
    assert len(intro) >= 2


def test_lines_rejoin_into_prose():
    [passage] = split_into_passages("A short note about trans-\nformers and how they\nwork.")
    assert passage.text == "A short note about transformers and how they work."


def test_ranking_by_keywords_and_fusion():
    docs = ["The model reaches 28.4 BLEU on translation.", "We train with Adam.", "Dropout of 0.1 is used."]
    assert bm25_rank("What BLEU score did it reach?", docs)[0] == 0
    assert bm25_rank("the and of", docs) == []
    assert fuse([[0, 1, 2], [2, 0]])[:2] == [0, 2]


def make_paper(db, **fields) -> Paper:
    paper = Paper(title="A Study of Things", origin="upload", **fields)
    db.add(paper)
    db.commit()
    return paper


def test_indexing_stores_embedded_passages_and_retrieval_finds_the_right_one(db, fake_llm):
    paper = make_paper(db, full_text=PAPER_TEXT)
    assert asyncio.run(retrieval.ensure_index(db, paper)) is True
    chunks = db.query(PaperChunk).filter_by(paper_id=paper.id).all()
    assert chunks and all(c.embedding for c in chunks)
    assert fake_llm.embed_calls[0]["task"] == "RETRIEVAL_DOCUMENT"

    # Indexing again does nothing
    asyncio.run(retrieval.ensure_index(db, paper))
    assert db.query(PaperChunk).filter_by(paper_id=paper.id).count() == len(chunks)

    top = asyncio.run(retrieval.retrieve(db, paper, "What was the bleu result?"))
    assert top[0].section == "3 Results"
    assert fake_llm.embed_calls[-1]["task"] == "RETRIEVAL_QUERY"


def test_without_embeddings_retrieval_falls_back_to_keywords(db, fake_llm):
    fake_llm.embed_error = LLMError("quota")
    paper = make_paper(db, full_text=PAPER_TEXT)
    assert asyncio.run(retrieval.ensure_index(db, paper)) is True
    assert all(c.embedding is None for c in db.query(PaperChunk).filter_by(paper_id=paper.id))
    top = asyncio.run(retrieval.retrieve(db, paper, "Which optimizer was used?"))
    assert top[0].section == "2.1 Training Setup"


def test_a_paper_from_an_edition_is_read_from_arxiv(db, fake_llm, monkeypatch):
    fetched = []

    async def fetch(arxiv_id: str):
        fetched.append(arxiv_id)
        return PAPER_TEXT

    monkeypatch.setattr(retrieval, "fetch_arxiv_text", fetch)
    paper = make_paper(db, arxiv_id="2611.00001")
    assert asyncio.run(retrieval.ensure_index(db, paper)) is True
    assert fetched == ["2611.00001"]
    db.refresh(paper)
    assert paper.full_text == PAPER_TEXT


def test_chat_falls_back_to_the_summary_without_full_text(client, db, fake_llm):
    paper = make_paper(db, arxiv_id="2611.00002", what_changed="Things got better.")
    headers = auth_headers(client)
    fake_llm.default = "From the summary."
    response = client.post(f"/api/papers/{paper.id}/chat", json={"message": "What changed?"}, headers=headers)
    assert response.json() == {"reply": "From the summary.", "sources": []}
    assert "Things got better." in fake_llm.calls[-1]["prompt"]


def test_chat_cites_numbered_passages(client, db, fake_llm):
    paper = make_paper(db, full_text=PAPER_TEXT)
    headers = auth_headers(client)
    fake_llm.default = "It reports a BLEU result [1]."
    body = client.post(f"/api/papers/{paper.id}/chat", json={"message": "What bleu result?"}, headers=headers).json()
    assert body["reply"] == "It reports a BLEU result [1]."
    assert [s["number"] for s in body["sources"]] == list(range(1, len(body["sources"]) + 1))
    assert body["sources"][0]["section"] == "3 Results"
    assert body["sources"][0]["page"] == 3
    prompt = fake_llm.calls[-1]["prompt"]
    assert "[1] (3 Results, page 3)" in prompt
    assert "cite it with its number" in prompt


def events(response) -> list[tuple[str, dict]]:
    parsed = []
    for block in response.text.strip().split("\n\n"):
        name = block.split("\n")[0].removeprefix("event: ")
        data = json.loads(block.split("\n")[1].removeprefix("data: "))
        parsed.append((name, data))
    return parsed


def test_streaming_chat_sends_sources_then_the_answer(client, db, fake_llm):
    paper = make_paper(db, full_text=PAPER_TEXT)
    headers = auth_headers(client)
    url = f"/api/papers/{paper.id}/chat/stream"
    assert client.post(url, json={"message": "Hi"}).status_code == 401
    assert client.post("/api/papers/nope/chat/stream", json={"message": "Hi"}, headers=headers).status_code == 404

    fake_llm.default = "It uses attention [2]."
    response = client.post(url, json={"message": "How does attention work?", "level": "plain"}, headers=headers)
    assert response.headers["content-type"].startswith("text/event-stream")
    stream = events(response)
    names = [name for name, _ in stream]
    # The first question reads the paper; the answer arrives in pieces after its sources
    assert names[0] == "status" and names[1] == "sources" and names[-1] == "done"
    assert "".join(data["text"] for name, data in stream if name == "delta") == "It uses attention [2]."
    assert stream[1][1][0]["section"] == "2 Method"

    second = [name for name, _ in events(client.post(url, json={"message": "And results?"}, headers=headers))]
    assert "status" not in second


def test_streaming_chat_reports_a_model_outage_as_an_event(client, db, fake_llm):
    paper = make_paper(db, full_text=PAPER_TEXT)
    fake_llm.replies.append(LLMError("down"))
    response = client.post(f"/api/papers/{paper.id}/chat/stream", json={"message": "Hi"}, headers=auth_headers(client))
    name, data = events(response)[-1]
    assert name == "error"
    assert "unavailable" in data["detail"]


def test_an_upload_is_indexed_when_it_is_explained(client, db, fake_llm):
    fake_llm.replies.append(json.dumps(ANALYSIS))
    job = explain(client, auth_headers(client), make_pdf())
    assert db.query(PaperChunk).filter_by(paper_id=job["paper_id"]).count() == 1
