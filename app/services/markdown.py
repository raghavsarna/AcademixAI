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
    # Normalise "•" bullets at the start of a line to markdown "- "
    text = re.sub(r"^[ \t]*[•●][ \t]*", "- ", text, flags=re.MULTILINE)
    # Collapse runs of blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None
