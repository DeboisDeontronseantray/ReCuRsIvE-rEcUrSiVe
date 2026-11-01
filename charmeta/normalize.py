"""Normalize trait text for cross-clip matching."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def normalize_trait_text(text: str) -> str:
    collapsed = _WS.sub(" ", text.strip().lower())
    return collapsed
