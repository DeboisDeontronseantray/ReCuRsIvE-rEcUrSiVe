"""Shared on-screen name blocking for prompt assembly (DEC-16 / PR #20 legacy_names)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_LIVE_DIR = Path(__file__).resolve().parents[1] / "live"
if str(_LIVE_DIR) not in sys.path:
    sys.path.insert(0, str(_LIVE_DIR))

import legacy_names as _legacy_names  # noqa: E402

NEVER_WORDS = re.compile(
    rf"(?<![A-Za-z]){re.escape(_legacy_names.LEGACY_OWNER)}", re.I
)


def find_blocked_name_tokens(text: str) -> list[str]:
    return [match.group(0) for match in NEVER_WORDS.finditer(text)]
