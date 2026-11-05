"""LINEAGE aired status — shared contract for charmeta promotion and lineage validators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def clip_id_aired(row: dict[str, Any], *, lifecycle=None) -> bool:
    """Read canonical receipt-backed state; row booleans confer no authority."""
    from astra_lifecycle.repo import aired_projection
    return aired_projection([row], lifecycle).get(row.get("clip_id"), False)


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


def build_aired_index(rows: list[dict[str, Any]], *, lifecycle=None) -> dict[str, bool]:
    """Project canonical state for the requested clip IDs, including unknown IDs as false."""
    from astra_lifecycle.repo import aired_projection
    return aired_projection(rows, lifecycle)
