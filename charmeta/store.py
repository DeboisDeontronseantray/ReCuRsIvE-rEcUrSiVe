"""Companion YAML store: init from bible (read-only), save, cast id checks."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from charmeta.schema import empty_cast_additions, load_schema


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping at root of {path}")
    return data


def load_bible_cast(bible_path: Path | str) -> dict[str, Any]:
    """Read cast entries from a continuity bible (read-only)."""
    doc = _read_yaml(Path(bible_path))
    cast = doc.get("cast")
    if not isinstance(cast, dict):
        raise ValueError("bible missing cast mapping")
    return cast


def missing_cast_ids(cast: dict[str, Any], expected_ids: list[str]) -> list[str]:
    return [cast_id for cast_id in expected_ids if cast_id not in cast]


def build_companion_from_bible(
    bible_path: Path | str,
    cast_ids: list[str],
    *,
    channel: str | None = None,
) -> dict[str, Any]:
    """Build an in-memory companion document; does not write the bible."""
    bible = _read_yaml(Path(bible_path))
    cast = load_bible_cast(bible_path)
    missing = missing_cast_ids(cast, cast_ids)
    if missing:
        raise ValueError(f"missing cast ids in bible: {', '.join(missing)}")

    schema = load_schema()
    meta_block = schema.get("meta") or {}
    channel_value = channel
    if channel_value is None:
        bible_meta = bible.get("meta") or {}
        if isinstance(bible_meta.get("channel"), str):
            channel_value = bible_meta["channel"]

    companion_cast: dict[str, Any] = {}
    for cast_id in cast_ids:
        entry = copy.deepcopy(cast[cast_id])
        additions = empty_cast_additions()
        entry.update(additions)
        companion_cast[cast_id] = entry

    return {
        "meta": {
            "schema": meta_block.get("schema", "character-meta"),
            "version": meta_block.get("version", 1),
            "channel": channel_value,
            "source_bible": str(Path(bible_path).name),
        },
        "cast": companion_cast,
    }


def load_companion(path: Path | str) -> dict[str, Any]:
    return _read_yaml(Path(path))


def save_companion(path: Path | str, document: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    target.write_text(text, encoding="utf-8")
