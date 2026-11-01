"""Screen-name filters shared with the story-engine prompt path.

Keep ``NEVER_WORDS`` aligned with ``story-engine/engine/assemble_prompt.py`` and
``story-engine/live/checker.py`` (CREATOR / overlay name regex).
"""

from __future__ import annotations

import base64
import re

CREATOR_NAME = base64.b64decode("ZHJldw==").decode()
NEVER_WORDS = re.compile(rf"\b{re.escape(CREATOR_NAME)}\b", re.I)


def find_blocked_name_tokens(text: str) -> list[str]:
    return [match.group(0) for match in NEVER_WORDS.finditer(text)]


def reject_if_blocked(text: str, *, context: str = "prompt text") -> None:
    hits = find_blocked_name_tokens(text)
    if hits:
        raise ValueError(f"{context} contains blocked real-name token(s): {hits!r}")
