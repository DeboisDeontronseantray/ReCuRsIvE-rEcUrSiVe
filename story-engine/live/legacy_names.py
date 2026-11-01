"""Pre-scrub spellings that the live box and its data still use, read through aliases.

The owner's real first name was replaced with lowercase `trundle` in this repo. Live folders, files, rule ids, data keys
and WITHDRAWN callers may still carry the old spelling, so reads accept both forms; new writes use the trundle form.
The legacy name is base64 so the literal never sits in the source."""
import base64
import re
from pathlib import Path

OWNER = "trundle"
LEGACY_OWNER = base64.b64decode("ZHJldw==").decode()
WITHDRAW_BY = (OWNER, LEGACY_OWNER.capitalize())
_LEGACY = re.compile(rf"(?<![A-Za-z]){re.escape(LEGACY_OWNER)}", re.I)


def canonical(text):
    """The trundle form of a key, id, status or path segment (the same rule the scrub applied)."""
    return _LEGACY.sub(OWNER, text) if isinstance(text, str) else text


def same(a, b):
    return canonical(a) == canonical(b)


def get(d, key, default=None):
    """d[key], else the value under any legacy spelling of key."""
    if key in d:
        return d[key]
    want = canonical(key)
    return next((v for k, v in d.items() if canonical(k) == want), default)


def resolve_path(path):
    """The path as given if it exists, else the same path with legacy-spelled segments that exist on disk."""
    p = Path(path).expanduser()
    if p.exists():
        return p
    cur = Path(p.anchor) if p.is_absolute() else Path(".")
    for part in p.relative_to(p.anchor).parts if p.is_absolute() else p.parts:
        nxt = cur / part
        if not nxt.exists() and cur.is_dir():
            nxt = next((c for c in cur.iterdir() if canonical(c.name) == canonical(part)), nxt)
        cur = nxt
    return cur if cur.exists() else p


def is_owner_withdraw(by):
    return by in WITHDRAW_BY


def never_on_screen(hard_limits):
    """Words that may never be shown or spoken: the base64 list in rules/hard-limits.yaml plus any plain legacy list."""
    words = [base64.b64decode(w).decode() for w in hard_limits.get("never_on_screen_or_spoken_b64", [])]
    return words + [w for w in hard_limits.get("never_on_screen_or_spoken", []) if w not in words]
