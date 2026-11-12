"""On-screen owner-name denylist.

The owner's real first and last names are stored only as base64 so they never
sit in source. The public name "trundle" is allowed and is not in this list.
"""
from __future__ import annotations

import base64
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
_FIRST = base64.b64decode("ZHJldw==").decode()
_LAST = base64.b64decode("bXVzZWxtYW4=").decode()


def real_first() -> str:
    return _FIRST


def real_last() -> str:
    return _LAST


def real_name_tokens() -> list[str]:
    first, last = _FIRST, _LAST
    return [first, first + "s", first + "'s", first + " m", last, first + " " + last]


def script_name_pattern() -> re.Pattern[str]:
    first, last = _FIRST, _LAST
    return re.compile(
        rf"(?<![a-z])({re.escape(first)}|{re.escape(first + 's')}|{re.escape(last)})(?![a-z])",
        re.I,
    )


def ocr_fragment_pattern() -> re.Pattern[str]:
    return re.compile(rf"\S*(?:{re.escape(_FIRST)}|{re.escape(_LAST)})\S*", re.I)


def overlay_name_pattern() -> re.Pattern[str]:
    return re.compile(re.escape(_FIRST), re.I)


def load_blocklists(path: str | None = None) -> dict:
    raw = json.load(open(path or os.path.join(HERE, "blocklists.json")))
    encoded = raw.pop("owner_name_b64", None)
    if encoded:
        raw["owner_name"] = [base64.b64decode(item).decode() for item in encoded]
    else:
        raw.setdefault("owner_name", real_name_tokens())
    return raw
