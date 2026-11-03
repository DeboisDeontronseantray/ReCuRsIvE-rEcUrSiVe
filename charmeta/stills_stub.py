"""Map stills-to-meta JSON into trait observation rows (log append only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from charmeta.observations import append_observations, partition_observations
from lineage.aired import load_lineage_jsonl
from lineage.eligibility import (
    is_forward_supply_row,
    is_show_master_row,
    row_index_by_clip_id,
)

# Shape aligned with stills_meta scaffold (PR cursor/stills-meta-scaffold-plan-a5c4):
# { "description": str, "meta": { "tangible": [str], "intangible": [str], "source": {...} } }


def _strings_from_meta(meta: dict[str, Any], key: str) -> list[str]:
    values = meta.get(key)
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for item in values:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def observations_from_stills_meta(
    stills_payload: dict[str, Any],
    *,
    clip_id: str,
    character: str,
) -> list[dict[str, Any]]:
    """Build observation dicts; does not write files or companion YAML."""
    meta = stills_payload.get("meta")
    if not isinstance(meta, dict):
        return []
    rows: list[dict[str, Any]] = []
    for text in _strings_from_meta(meta, "tangible"):
        rows.append(
            {
                "clip_id": clip_id,
                "character": character,
                "field": "traits.tangible",
                "extracted_text": text,
                "method": "still_analysis",
            }
        )
    for text in _strings_from_meta(meta, "intangible"):
        rows.append(
            {
                "clip_id": clip_id,
                "character": character,
                "field": "traits.intangible",
                "extracted_text": text,
                "method": "still_analysis",
            }
        )
    return rows


def load_stills_meta_json(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("stills meta JSON root must be an object")
    return data


def extract(
    image_path: str | Path,
    clip_id: str,
    character: str,
    *,
    stills_meta_json: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Interface stub: returns observation dicts when meta JSON is provided, else []."""
    _ = Path(image_path)
    if stills_meta_json is None:
        return []
    payload = load_stills_meta_json(stills_meta_json)
    return observations_from_stills_meta(
        payload, clip_id=str(clip_id), character=character
    )


def ingest_stills_meta_to_log(
    *,
    observations_path: Path | str,
    stills_meta_path: Path | str,
    clip_id: str,
    character: str,
    image_path: str | Path | None = None,
    apply: bool = True,
    lineage_path: Path | str | None = None,
    slots_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Append stills-derived observations to trait_observations.jsonl only. Ad and break stills write nothing."""
    if lineage_path is not None:
        rows = load_lineage_jsonl(lineage_path)
        clip_row = row_index_by_clip_id(rows).get(clip_id)
        if clip_row is None or not is_show_master_row(clip_row) or is_forward_supply_row(
            clip_row
        ):
            return []
    payload = load_stills_meta_json(stills_meta_path)
    rows = observations_from_stills_meta(payload, clip_id=clip_id, character=character)
    if image_path is not None:
        extract(image_path, clip_id, character, stills_meta_json=stills_meta_path)
    if not apply:
        kept, _skipped = partition_observations(
            rows, lineage_path=lineage_path, slots_path=slots_path
        )
        return kept
    written, _skipped = append_observations(
        observations_path, rows, lineage_path=lineage_path, slots_path=slots_path
    )
    return written
