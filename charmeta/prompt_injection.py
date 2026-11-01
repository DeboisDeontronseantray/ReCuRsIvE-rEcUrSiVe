"""Inject character meta_prompt text into shot bodies (LAYERS-BODY-ORDER)."""

from __future__ import annotations

import os
from typing import Any

from charmeta.name_guard import reject_if_blocked

# assemble_prompt.py BODY_ORDER (Director Oct 28 2026); meta belongs in characters.
SHOT_BODY_LAYER_ORDER = [
    "camera",
    "look",
    "location",
    "characters",
    "action",
    "in_scene_text",
    "physics",
    "audio",
    "sfx",
    "rules",
    "constraints",
]

# prompts/LAYERS.md system wrapper order (layers 1–6); character meta never replaces these.
PROMPT_WRAPPER_LAYER_ORDER = [
    "global",
    "channel",
    "format",
    "show_or_ad",
    "shot",
    "commenter",
]

DEFAULT_MAX_CHARACTER_META_CHARS = 512


def max_character_meta_chars() -> int:
    raw = os.environ.get("CHARMETA_META_PROMPT_MAX_CHARS", "").strip()
    if raw:
        value = int(raw)
        if value < 64:
            raise ValueError("CHARMETA_META_PROMPT_MAX_CHARS must be >= 64")
        return value
    return DEFAULT_MAX_CHARACTER_META_CHARS


def trim_meta_for_injection(text: str, *, max_chars: int | None = None) -> str:
    """Cap character injection so meta_prompt cannot bloat dense prompts (~4096 cap elsewhere)."""
    limit = max_chars if max_chars is not None else max_character_meta_chars()
    cleaned = text.strip()
    reject_if_blocked(cleaned, context="character meta_prompt")
    if len(cleaned) <= limit:
        return cleaned
    lines = cleaned.splitlines()
    kept: list[str] = []
    total = 0
    for line in lines:
        add_len = len(line) + (1 if kept else 0)
        if total + add_len > limit:
            break
        kept.append(line)
        total += add_len
    trimmed = "\n".join(kept).strip()
    if not trimmed and cleaned:
        trimmed = cleaned[:limit].rstrip()
    reject_if_blocked(trimmed, context="character meta_prompt (trimmed)")
    return trimmed


def format_character_meta_block(
    character_id: str,
    meta_text: str,
    *,
    locked_description: str | None = None,
    max_chars: int | None = None,
) -> str:
    """One character block for the [characters] shot layer (after location, before action)."""
    distilled = trim_meta_for_injection(meta_text, max_chars=max_chars)
    parts: list[str] = []
    if locked_description and locked_description.strip():
        parts.append(f"{character_id}: {locked_description.strip()}")
    if distilled:
        parts.append(f"{character_id} (canon meta): {distilled}")
    return "\n".join(parts)


def inject_character_meta_into_shot_body(
    shot_body: dict[str, Any],
    character_blocks: list[str],
) -> dict[str, Any]:
    """Return a copy with merged [characters] text; preserves other BODY_ORDER keys."""
    merged = dict(shot_body)
    existing = merged.get("characters")
    base = existing.strip() if isinstance(existing, str) else ""
    blocks = [block.strip() for block in character_blocks if block.strip()]
    if not blocks:
        return merged
    combined = "\n\n".join([base] + blocks if base else blocks)
    reject_if_blocked(combined, context="shot characters layer")
    merged["characters"] = combined
    return merged


def assert_shot_body_layer_order(keys: list[str]) -> None:
    """Raise if a caller tries to place character meta outside the characters slot."""
    if "characters" not in keys:
        raise ValueError("shot body must include a characters layer for meta injection")
