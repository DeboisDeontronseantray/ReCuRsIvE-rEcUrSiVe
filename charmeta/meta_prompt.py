"""Rebuild meta_prompt from approved/locked entries only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from charmeta.channels import local_cast_id
from charmeta.prompt_injection import trim_meta_for_injection
from charmeta.schema import empty_meta_prompt

_CANON_STATES = frozenset({"approved", "locked"})


@dataclass
class MetaPromptReport:
    dry_run: bool
    character: str
    previous_version: int
    new_version: int
    built_from: list[str] = field(default_factory=list)
    text: str = ""


def _trait_items(entry: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    items: list[tuple[str, dict[str, Any]]] = []
    traits = entry.get("traits") or {}
    for bucket in ("tangible", "intangible"):
        for item in traits.get(bucket) or []:
            if isinstance(item, dict):
                items.append((f"traits.{bucket}", item))
    for key in ("abilities", "relationships"):
        for item in entry.get(key) or []:
            if isinstance(item, dict):
                items.append((key, item))
    return items


def approved_entries_for_prompt(entry: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return canon entries eligible for meta_prompt (never proposed or retired-only)."""
    eligible: list[tuple[str, dict[str, Any]]] = []
    for field_name, item in _trait_items(entry):
        status = item.get("status")
        if status not in _CANON_STATES:
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        eligible.append((field_name, item))
    return eligible


def build_meta_prompt_text(entry: dict[str, Any]) -> tuple[str, list[str]]:
    """Compose prompt description text and source entry ids."""
    parts: list[str] = []
    built_from: list[str] = []
    for field_name, item in sorted(
        approved_entries_for_prompt(entry),
        key=lambda pair: (pair[0], str(pair[1].get("id", ""))),
    ):
        item_id = item.get("id")
        text = str(item.get("text", "")).strip()
        if isinstance(item_id, str) and item_id:
            built_from.append(item_id)
        prefix = field_name.replace(".", " ")
        parts.append(f"{prefix}: {text}")
    raw = "\n".join(parts)
    return trim_meta_for_injection(raw), built_from


def _resolve_cast_entry(
    cast: dict[str, Any], character_id: str
) -> tuple[str, dict[str, Any] | None]:
    if character_id in cast and isinstance(cast[character_id], dict):
        return character_id, cast[character_id]
    for key, entry in cast.items():
        if isinstance(key, str) and local_cast_id(key) == character_id and isinstance(entry, dict):
            return key, entry
    return character_id, None


def rebuild_meta_prompt_for_character(
    companion: dict[str, Any],
    character_id: str,
    *,
    apply: bool = False,
) -> MetaPromptReport:
    cast = companion.get("cast")
    if not isinstance(cast, dict):
        raise ValueError("companion missing cast mapping")
    storage_key, entry = _resolve_cast_entry(cast, character_id)
    if entry is None:
        raise ValueError(f"unknown character {character_id!r}")
    meta = entry.get("meta_prompt")
    if not isinstance(meta, dict):
        meta = empty_meta_prompt()
        entry["meta_prompt"] = meta
    previous_version = int(meta.get("version") or 0)
    text, built_from = build_meta_prompt_text(entry)
    report = MetaPromptReport(
        dry_run=not apply,
        character=storage_key,
        previous_version=previous_version,
        new_version=previous_version + 1 if apply else previous_version,
        built_from=built_from,
        text=text,
    )
    if apply:
        meta["text"] = text
        meta["built_from"] = built_from
        meta["version"] = previous_version + 1
        report.new_version = meta["version"]
    return report
