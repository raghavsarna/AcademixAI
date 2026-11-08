"""Shared pieces of paper analysis: what changed, what it builds on, and three explanation depths."""

import json
import re
from typing import Any

from app.services.markdown import to_markdown

DEPTHS = ("plain", "student", "expert")

CHANGE_TYPES = {
    "new-method": "New method",
    "new-result": "New result",
    "benchmark": "New benchmark",
    "dataset": "New dataset",
    "analysis": "Analysis",
    "challenge": "Challenges prior work",
    "tool": "Tool or system",
    "survey": "Survey",
}

RELATIONS = ("extends", "challenges", "compares-with", "applies", "replaces")

CHANGE_FIELDS_SPEC = f"""  "what_changed": "one or two sentences: what this paper claims is new compared with earlier
    work. Be concrete: name the method, finding or number. Only what the text states.",
  "change_type": one of {json.dumps(list(CHANGE_TYPES))},
  "why_it_matters": "one or two sentences on who should care and why",
  "builds_on": [{{"work": "an earlier method, model, paper or dataset the text itself names",
                 "relation": one of {json.dumps(list(RELATIONS))}}}],
  "explanations": {{
    "plain": "about 120 words of markdown for a curious non-expert: no jargon, one everyday analogy, no equations",
    "student": "about 200 words of markdown for a computer-science student: define key terms briefly inline,
      explain the idea and how it works",
    "expert": "about 200 words of markdown for an ML practitioner: precise terms, method and setup details,
      results with the numbers the text reports, and limitations"
  }}"""

CHANGE_RULES = """Rules:
- Never invent results, numbers, comparisons or prior work that the text does not state.
- builds_on lists at most 4 items and is an empty list when the text names no earlier work.
- Write plainly. Do not use em dashes."""


INVALID_ESCAPE = re.compile(r'\\(?!["\\/bfnrtu])')


class AnalysisError(Exception):
    """The model's reply could not be turned into an analysis."""


def parse_json_reply(reply: str) -> dict[str, Any]:
    """Parse the model's JSON reply, tolerating code fences or text around the object."""
    candidates = [reply.strip()]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", reply, re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1).strip())
    braces = re.search(r"\{.*\}", reply, re.DOTALL)
    if braces:
        candidates.append(braces.group(0))
    for candidate in candidates:
        # Second try: LaTeX in a paper often leaves backslashes that are not valid JSON escapes
        for text in (candidate, INVALID_ESCAPE.sub(r"\\\\", candidate)):
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                return data
    raise AnalysisError("The model's reply was not valid JSON")


def as_text(value: Any, max_length: int | None = None) -> str | None:
    if value is None or isinstance(value, dict | list):
        return None
    text = str(value).strip()
    if text.lower() in ("", "null", "none", "n/a", "not available"):
        return None
    return text[:max_length] if max_length else text


def as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r",|;| and ", value) if part.strip()]
    return []


def strip_em_dashes(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r"\s*—\s*", ", ", text)


def normalize_change_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the what-changed, builds-on and explanation fields of a model reply."""
    change_type = as_text(data.get("change_type"))
    change_type = change_type.lower().replace(" ", "-") if change_type else None

    builds_on = []
    for item in data.get("builds_on") or []:
        if isinstance(item, dict):
            work = as_text(item.get("work"), 200)
            relation = (as_text(item.get("relation")) or "extends").lower()
        else:
            work, relation = as_text(item, 200), "extends"
        if work:
            builds_on.append({"work": work, "relation": relation if relation in RELATIONS else "extends"})

    raw = data.get("explanations") if isinstance(data.get("explanations"), dict) else {}
    explanations = {}
    for depth in DEPTHS:
        text = strip_em_dashes(to_markdown(raw.get(depth)))
        if text:
            explanations[depth] = text

    return {
        "what_changed": strip_em_dashes(as_text(data.get("what_changed"))),
        "change_type": change_type if change_type in CHANGE_TYPES else None,
        "why_it_matters": strip_em_dashes(as_text(data.get("why_it_matters"))),
        "builds_on": builds_on[:4],
        "explanations": explanations,
    }
