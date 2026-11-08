"""Unit tests for the pure helper functions."""

import pytest

from app.rate_limit import RateLimiter
from app.services.analysis import AnalysisError, normalize_change_fields, parse_json_reply
from app.services.markdown import to_markdown
from app.services.papers import normalize_analysis, normalize_arxiv_id, normalize_doi
from app.storage import LocalStorage


@pytest.mark.parametrize(
    "reply",
    [
        '{"title": "T"}',
        '```json\n{"title": "T"}\n```',
        'Here you go:\n{"title": "T"}\nHope that helps!',
    ],
)
def test_parse_json_reply_accepts_common_shapes(reply):
    assert parse_json_reply(reply) == {"title": "T"}


@pytest.mark.parametrize("reply", ["no json here", "[1, 2, 3]", "{broken"])
def test_parse_json_reply_rejects_non_objects(reply):
    with pytest.raises(AnalysisError):
        parse_json_reply(reply)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("10.1145/3292500.3330701", "10.1145/3292500.3330701"),
        ("https://doi.org/10.48550/arXiv.1706.03762", "10.48550/arXiv.1706.03762"),
        ("DOI: 10.1000/xyz", "10.1000/xyz"),
        ("not available", None),
        ("attention-is-all-you-need", None),
        (None, None),
        (42, None),
    ],
)
def test_normalize_doi(value, expected):
    assert normalize_doi(value) == expected


def test_normalize_analysis_fixes_types_and_placeholders():
    fields = normalize_analysis(
        {
            "title": "",
            "authors": "Ada Lovelace, Alan Turing and Grace Hopper",
            "doi": "n/a",
            "source": "null",
            "keywords": "ai; ml",
            "main_findings": ["One", "", "Two"],
        }
    )
    assert fields["title"] == "Untitled paper"
    assert fields["authors"] == ["Ada Lovelace", "Alan Turing", "Grace Hopper"]
    assert fields["doi"] is None
    assert fields["source"] is None
    assert fields["keywords"] == ["ai", "ml"]
    assert fields["main_findings"] == "- One\n- Two"
    assert fields["explanations"] == {}
    assert fields["what_changed"] is None


def test_to_markdown_cleans_model_output():
    assert to_markdown("\\*\\*Bold\\*\\*\n\n\n\n• point") == "**Bold**\n\n- point"
    assert to_markdown("   ") is None
    assert to_markdown(None) is None


def test_parse_json_reply_repairs_latex_backslashes():
    reply = r'{"expert": "scaled by \sqrt{d_k}, keeps \n newlines"}'
    value = parse_json_reply(reply)["expert"]
    assert value == "scaled by \\sqrt{d_k}, keeps \n newlines"


@pytest.mark.parametrize(
    ("value", "doi", "expected"),
    [
        ("2310.06825", None, "2310.06825"),
        ("arXiv:2310.06825v2", None, "2310.06825"),
        (None, "10.48550/arXiv.1706.03762", "1706.03762"),
        ("not an id", "10.1145/123", None),
    ],
)
def test_normalize_arxiv_id(value, doi, expected):
    assert normalize_arxiv_id(value, doi) == expected


def test_normalize_change_fields():
    fields = normalize_change_fields(
        {
            "what_changed": "A new optimiser \u2014 twice as fast.",
            "change_type": "New Method",
            "builds_on": [{"work": "Adam", "relation": "extends"}, {"work": "SGD", "relation": "beats"}, "Lion", {}],
            "explanations": {"plain": "Simple.", "student": ["A", "B"], "expert": None, "genius": "x"},
        }
    )
    assert fields["what_changed"] == "A new optimiser, twice as fast."
    assert fields["change_type"] == "new-method"
    assert fields["builds_on"] == [
        {"work": "Adam", "relation": "extends"},
        {"work": "SGD", "relation": "extends"},
        {"work": "Lion", "relation": "extends"},
    ]
    assert fields["explanations"] == {"plain": "Simple.", "student": "- A\n- B"}
    assert normalize_change_fields({"change_type": "vibes"})["change_type"] is None


def test_rate_limiter_window(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.rate_limit.time.monotonic", lambda: now[0])
    limiter = RateLimiter()
    assert limiter.hit("k", limit=2, window_seconds=60) is None
    assert limiter.hit("k", limit=2, window_seconds=60) is None
    assert limiter.hit("k", limit=2, window_seconds=60) == pytest.approx(60)
    now[0] += 61
    assert limiter.hit("k", limit=2, window_seconds=60) is None


def test_storage_round_trip_and_rejects_path_traversal(tmp_path):
    storage = LocalStorage(tmp_path)
    key = storage.save(b"%PDF-data")
    assert storage.read(key) == b"%PDF-data"
    storage.delete(key)
    assert not (tmp_path / key).exists()
    with pytest.raises(ValueError):
        storage.read("../../etc/passwd")
