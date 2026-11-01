"""LINEAGE aired status — shared contract for charmeta promotion and lineage validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def clip_id_aired(row: dict[str, Any]) -> bool:
    """Return True only when the row is explicitly aired.

    Media Librarian New (or the lineage validator) sets derived boolean ``aired``
    when a clip reaches AIRED status. Missing or falsey values mean not aired.
    Legacy ``air_yes: true`` is accepted until rows are normalized.
    """
    aired = row.get("aired")
    if aired is True:
        return True
    legacy = row.get("air_yes")
    if legacy is True:
        return True
    return False


def load_lineage_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """Parse one JSON object per line; skip blank lines."""
    text = Path(path).read_text(encoding="utf-8")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at line {line_no} in {path}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"line {line_no} in {path} is not a JSON object")
        rows.append(obj)
    return rows


def build_aired_index(rows: list[dict[str, Any]]) -> dict[str, bool]:
    """Map clip_id → aired (missing clip_id rows are skipped)."""
    index: dict[str, bool] = {}
    for row in rows:
        clip_id = row.get("clip_id")
        if not isinstance(clip_id, str) or not clip_id:
            continue
        index[clip_id] = clip_id_aired(row)
    return index
