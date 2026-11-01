"""Promote trait observations to proposed companion entries (dry-run default)."""

from __future__ import annotations

import argparse
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from charmeta.conflicts import check_proposal_conflicts
from charmeta.config import allow_live_paths as env_allow_live_paths
from charmeta.normalize import normalize_trait_text
from charmeta.observations import load_observations
from charmeta.paths import refuse_charmeta_path
from charmeta.schema import proposal_threshold
from charmeta.store import load_companion, save_companion
from lineage.aired import build_aired_index, load_lineage_jsonl


@dataclass
class PromoteReport:
    dry_run: bool
    threshold: int
    proposals: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _observation_groups(
    observations: list[dict[str, Any]],
    aired_index: dict[str, bool],
) -> dict[tuple[str, str, str], set[str]]:
    groups: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in observations:
        character = row.get("character")
        field_name = row.get("field")
        text = row.get("extracted_text")
        clip_id = row.get("clip_id")
        if not all(isinstance(v, str) for v in (character, field_name, text, clip_id)):
            continue
        if not aired_index.get(clip_id, False):
            continue
        key = (character, field_name, normalize_trait_text(text))
        groups[key].add(clip_id)
    return groups


def _has_proposed_duplicate(
    cast_entry: dict[str, Any], field_name: str, normalized_text: str
) -> bool:
    if field_name == "traits.tangible":
        items = (cast_entry.get("traits") or {}).get("tangible") or []
    elif field_name == "traits.intangible":
        items = (cast_entry.get("traits") or {}).get("intangible") or []
    elif field_name in ("abilities", "relationships"):
        items = cast_entry.get(field_name) or []
    else:
        return False
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") != "proposed":
            continue
        text = item.get("text")
        if isinstance(text, str) and normalize_trait_text(text) == normalized_text:
            return True
    return False


def _append_proposed_item(
    cast_entry: dict[str, Any],
    field_name: str,
    extracted_text: str,
    source_clip: str,
) -> str:
    item_id = f"{field_name.replace('.', '-')}-{uuid.uuid4().hex[:8]}"
    if field_name == "traits.tangible":
        cast_entry.setdefault("traits", {}).setdefault("tangible", []).append(
            {
                "id": item_id,
                "text": extracted_text,
                "source_clip": source_clip,
                "confidence": None,
                "status": "proposed",
            }
        )
    elif field_name == "traits.intangible":
        cast_entry.setdefault("traits", {}).setdefault("intangible", []).append(
            {
                "id": item_id,
                "text": extracted_text,
                "source_clip": source_clip,
                "status": "proposed",
            }
        )
    elif field_name == "abilities":
        cast_entry.setdefault("abilities", []).append(
            {
                "id": item_id,
                "text": extracted_text,
                "first_seen_clip": source_clip,
                "times_seen": 1,
                "status": "proposed",
            }
        )
    elif field_name == "relationships":
        cast_entry.setdefault("relationships", []).append(
            {
                "id": item_id,
                "with": "",
                "kind": "observed",
                "text": extracted_text,
                "first_seen_clip": source_clip,
                "status": "proposed",
            }
        )
    else:
        raise ValueError(f"unsupported field {field_name}")
    return item_id


def promote(
    *,
    companion_path: Path | str,
    observations_path: Path | str,
    lineage_path: Path | str,
    apply: bool = False,
    allow_live_paths: bool | None = None,
) -> PromoteReport:
    live_ok = env_allow_live_paths() if allow_live_paths is None else allow_live_paths
    refuse_charmeta_path(companion_path, allow_live_paths=live_ok)
    refuse_charmeta_path(observations_path, allow_live_paths=live_ok)
    refuse_charmeta_path(lineage_path, allow_live_paths=live_ok)
    threshold = proposal_threshold()
    companion = load_companion(companion_path)
    observations = load_observations(observations_path)
    lineage_rows = load_lineage_jsonl(lineage_path)
    aired_index = build_aired_index(lineage_rows)
    cast = companion.get("cast")
    if not isinstance(cast, dict):
        raise ValueError("companion missing cast mapping")

    groups = _observation_groups(observations, aired_index)
    report = PromoteReport(dry_run=not apply, threshold=threshold)

    for (character, field_name, norm_text), clip_ids in sorted(groups.items()):
        if len(clip_ids) < threshold:
            report.skipped.append(
                f"{character}/{field_name}/{norm_text!r}: only {len(clip_ids)} aired clip(s)"
            )
            continue
        if character not in cast:
            report.skipped.append(f"unknown character {character!r}")
            continue
        entry = cast[character]
        sample_text = next(
            (
                row["extracted_text"]
                for row in observations
                if row.get("character") == character
                and row.get("field") == field_name
                and normalize_trait_text(str(row.get("extracted_text", ""))) == norm_text
            ),
            norm_text,
        )
        conflict_messages = check_proposal_conflicts(entry, field_name, sample_text)
        if conflict_messages:
            report.conflicts.append(
                {
                    "character": character,
                    "field": field_name,
                    "text": sample_text,
                    "clip_ids": sorted(clip_ids),
                    "messages": conflict_messages,
                }
            )
            continue
        if _has_proposed_duplicate(entry, field_name, norm_text):
            report.skipped.append(
                f"duplicate proposed {character}/{field_name}/{norm_text!r}"
            )
            continue

        proposal = {
            "character": character,
            "field": field_name,
            "text": sample_text,
            "aired_clip_ids": sorted(clip_ids),
            "status": "proposed",
        }
        report.proposals.append(proposal)
        if apply:
            source_clip = sorted(clip_ids)[0]
            item_id = _append_proposed_item(entry, field_name, sample_text, source_clip)
            report.applied.append(item_id)

    if apply and report.applied:
        save_companion(companion_path, companion)

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote trait observations (dry-run default)")
    parser.add_argument("--companion", required=True, type=Path)
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--lineage", required=True, type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write proposed entries to companion YAML (never sets approved/locked)",
    )
    args = parser.parse_args(argv)
    report = promote(
        companion_path=args.companion,
        observations_path=args.observations,
        lineage_path=args.lineage,
        apply=args.apply,
    )
    print(yaml.safe_dump(report.__dict__, sort_keys=False))
    if report.conflicts:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
