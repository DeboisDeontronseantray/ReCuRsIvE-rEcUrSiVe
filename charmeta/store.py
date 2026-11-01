"""Companion YAML store: init from bible (read-only), save, cast id checks."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from charmeta.schema import empty_cast_additions, load_schema
from charmeta.channels import local_cast_id, namespaced_cast_id, parse_channel_from_cast_id


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
    bible_locals = [local_cast_id(c) for c in cast_ids]
    missing = missing_cast_ids(cast, bible_locals)
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
    ch_num = channel_value
    if ch_num is None and cast_ids:
        ch_num = parse_channel_from_cast_id(cast_ids[0])
    for cast_id in cast_ids:
        local = local_cast_id(cast_id)
        storage_key = (
            namespaced_cast_id(ch_num, local)
            if ch_num is not None and parse_channel_from_cast_id(cast_id) is None
            else cast_id
        )
        entry = copy.deepcopy(cast[local])
        additions = empty_cast_additions()
        entry.update(additions)
        companion_cast[storage_key] = entry

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
