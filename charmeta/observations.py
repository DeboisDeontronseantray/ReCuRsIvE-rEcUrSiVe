"""Add-only trait_observations.jsonl writer."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from charmeta.schema import OBSERVATION_FIELDS, OBSERVATION_METHODS
from lineage.eligibility import (
    ad_or_break_clip_ids,
    clip_id_looks_break,
    clip_id_looks_commercial,
    clip_id_looks_forward_supply,
    is_show_master_row,
    row_index_by_clip_id,
)
from lineage.aired import load_lineage_jsonl


class ObservationValidationError(ValueError):
    pass


def _require_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ObservationValidationError(f"{key} must be a non-empty string")
    return value.strip()


def validate_observation_row(row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ObservationValidationError("observation must be a mapping")

    field = _require_str(row, "field")
    if field not in OBSERVATION_FIELDS:
        raise ObservationValidationError(
            f"field must be one of {sorted(OBSERVATION_FIELDS)}"
        )
    if "generation_quirk" in field or field == "generation_quirks":
        raise ObservationValidationError(
            "generation quirks must not be written as trait observations"
        )

    method = _require_str(row, "method")
    if method not in OBSERVATION_METHODS:
        raise ObservationValidationError(
            f"method must be one of {sorted(OBSERVATION_METHODS)}"
        )
    if method == "generation_quirk":
        raise ObservationValidationError(
            "generation quirks must not use trait observation methods"
        )

    extracted = _require_str(row, "extracted_text")
    character = _require_str(row, "character")
    clip_id = _require_str(row, "clip_id")
    if (
        clip_id_looks_commercial(clip_id)
        or clip_id_looks_break(clip_id)
        or clip_id_looks_forward_supply(clip_id)
    ):
        raise ObservationValidationError(
            "commercial/ad, break, and Forward Supply clips must not produce trait observations"
        )

    seen_count = row.get("seen_count", 1)
    if not isinstance(seen_count, int) or seen_count < 1:
        raise ObservationValidationError("seen_count must be a positive integer")

    obs_id = row.get("obs_id")
    if obs_id is None:
        obs_id = uuid.uuid4().hex
    elif not isinstance(obs_id, str) or not obs_id.strip():
        raise ObservationValidationError("obs_id must be a non-empty string when provided")

    normalized: dict[str, Any] = {
        "obs_id": obs_id.strip(),
        "clip_id": clip_id,
        "character": character,
        "field": field,
        "extracted_text": extracted,
        "method": method,
        "seen_count": seen_count,
        "proposed_status": row.get("proposed_status"),
        "decision": row.get("decision"),
        "decided_by": row.get("decided_by"),
        "decided_at": row.get("decided_at"),
    }
    return normalized


def append_observation(
    path: Path | str,
    row: dict[str, Any],
    *,
    lineage_path: Path | str | None = None,
) -> dict[str, Any]:
    """Validate and append one observation row. No update or delete API."""
    normalized = validate_observation_row(row)
    if lineage_path is not None:
        lineage_rows = load_lineage_jsonl(lineage_path)
        by_id = row_index_by_clip_id(lineage_rows)
        clip_row = by_id.get(normalized["clip_id"])
        if clip_row is None or not is_show_master_row(clip_row):
            raise ObservationValidationError(
                f"clip_id {normalized['clip_id']!r} is not a show-master row in lineage"
            )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return normalized


def partition_observations(
    rows: list[dict[str, Any]],
    *,
    lineage_path: Path | str | None = None,
    slots_path: Path | str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split rows into trait-evidence candidates vs ad/break items that are never trait evidence."""
    lineage_rows = load_lineage_jsonl(lineage_path) if lineage_path is not None else []
    slot_rows = load_lineage_jsonl(slots_path) if slots_path is not None else []
    not_evidence = ad_or_break_clip_ids(lineage_rows, slot_rows)
    kept: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        clip_id = row.get("clip_id") if isinstance(row, dict) else None
        if isinstance(clip_id, str) and (
            clip_id.strip() in not_evidence
            or clip_id_looks_commercial(clip_id)
            or clip_id_looks_break(clip_id)
        ):
            skipped.append(row)
            continue
        kept.append(row)
    return kept, skipped


def append_observations(
    path: Path | str,
    rows: list[dict[str, Any]],
    *,
    lineage_path: Path | str | None = None,
    slots_path: Path | str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Append a batch, skipping ad and break items instead of failing the batch.

    Ads and breaks may show cast, but they are never trait evidence. Returns (written, skipped)."""
    kept, skipped = partition_observations(
        rows, lineage_path=lineage_path, slots_path=slots_path
    )
    written = [
        append_observation(path, row, lineage_path=lineage_path) for row in kept
    ]
    return written, skipped


def load_observations(path: Path | str) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(
        target.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"observation line {line_no} is not an object")
        rows.append(obj)
    return rows
