"""Tidy up markdown produced by the model before it is stored."""

import re
from typing import Any


def to_markdown(value: Any) -> str | None:
    """Turn a model-produced field into a clean markdown string.

    Lists (which the model sometimes returns instead of bullet points) become
    bullet lists. Empty values become None.
    """
    if value is None:
        return None
    if isinstance(value, list):
        text = "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
    else:
        text = str(value)

    # Undo escaping the model sometimes adds
    for escaped, plain in (("\\*", "*"), ("\\#", "#"), ("\\[", "["), ("\\]", "]")):
        text = text.replace(escaped, plain)
    # Normalise bullets written as "•" or "* " at the start of a line
    text = re.sub(r"^\s*[•●]\s*", "- ", text, flags=re.MULTILINE)
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None


def strip_leading_title(markdown: str, title: str) -> str:
    """Remove a leading '# Title' line when the title is shown separately."""
    lines = markdown.lstrip().splitlines()
    if lines and lines[0].startswith("# ") and lines[0][2:].strip().strip("*") == title.strip():
        return "\n".join(lines[1:]).lstrip()
    return markdown
