"""Comment intake (D4): raw collection from the live comment spool, with no semantic parsing.

Only the configured timestamp and text fields of each spool row are read; every other field (handle, user id,
account, avatar, ...) is discarded here and never stored. The window is the last N minutes before `now`, capped
at the most recent M comments."""
import datetime
import hashlib
import json
import pathlib

import contracts
import paths


def _aware(ts):
    t = datetime.datetime.fromisoformat(ts) if isinstance(ts, str) else ts
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def comment_key(row):
    """Stable id for a spool comment, from its timestamp and raw text only (no handle or account field)."""
    return hashlib.sha256(f"{row['ts']}\n{row['text']}".encode()).hexdigest()[:16]


def _ledger(path):
    p = pathlib.Path(path)
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.is_file() else []


def load_consumed(path, *, clip_id):
    """Keys placed in other clips. Rebuilding the same clip id may place its own comments again."""
    return {r["key"] for r in _ledger(path) if r["clip_id"] != clip_id}


def mark_consumed(path, keys, *, clip_id):
    """Append-only: each placed comment is recorded once, with the clip it went into."""
    seen = {r["key"] for r in _ledger(path)}
    new = [k for k in dict.fromkeys(keys) if k not in seen]
    if new:
        with pathlib.Path(path).open("a") as f:
            f.writelines(json.dumps({"key": k, "clip_id": clip_id}) + "\n" for k in new)


def collect(spool_path, *, now, cfg=None, consumed=frozenset()):
    cfg = cfg or paths.config("assembly")
    ts_key, text_key = cfg["spool_fields"]["ts"], cfg["spool_fields"]["text"]
    now = _aware(now)
    start = now - datetime.timedelta(minutes=cfg["comment_window_minutes"])
    stats = {"read": 0, "unreadable": 0, "outside_window": 0, "already_placed": 0, "over_cap": 0}
    rows = []
    for line in pathlib.Path(spool_path).read_text().splitlines():
        if not line.strip():
            continue
        stats["read"] += 1
        try:
            raw = json.loads(line)
            ts, text = raw[ts_key], raw[text_key]
            t = _aware(ts)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            stats["unreadable"] += 1
            continue
        if not isinstance(text, str) or not text.strip():
            stats["unreadable"] += 1
            continue
        if not start <= t <= now:
            stats["outside_window"] += 1
            continue
        row = {"ts": t.isoformat(), "text": text}
        if comment_key(row) in consumed:
            stats["already_placed"] += 1
            continue
        rows.append((t, row))
    rows.sort(key=lambda r: r[0])
    cap = cfg["comment_cap"]
    if len(rows) > cap:
        stats["over_cap"] = len(rows) - cap
        rows = rows[-cap:]
    return [contracts.validate_comment_row(r) for _, r in rows], stats
