"""Minimal overlay splitter stub for live checker tests (no shared_lib dependency)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legacy_names  # noqa: E402

_CREATOR = re.compile(rf"\b{re.escape(legacy_names.LEGACY_OWNER)}\b", re.I)

NO_TEXT = "No readable text, captions, logos or UI on screen."
TEXT_REQUEST = re.compile(
    r"\b(subtitles?|caption|readable text|on-screen text|logo)\b",
    re.I,
)
_Q = r'"[^"]{3,}"'


def blocked(text: str) -> bool:
    return bool(_CREATOR.search(text))


def split(prompt: str) -> dict:
    return {"gen_prompt": (prompt or "").strip(), "items": []}


def requests_text(gen_prompt: str) -> list[str]:
    body = (gen_prompt or "").replace(NO_TEXT, "")
    hits = [m.group(0) for m in TEXT_REQUEST.finditer(body)]
    hits.extend(m.group(0) for m in re.finditer(_Q, body))
    return hits
