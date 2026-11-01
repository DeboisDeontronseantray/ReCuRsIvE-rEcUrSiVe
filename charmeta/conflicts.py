"""Flag conflicts with locked canon; never auto-apply."""

from __future__ import annotations

import re
from typing import Any

from charmeta.normalize import normalize_trait_text

_NEGATION = re.compile(r"\b(no|without|missing|lacks?|never)\b", re.IGNORECASE)


def _iter_approved_or_locked_items(entry: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Yield (field_label, item_id, text) for approved/locked list entries."""
    found: list[tuple[str, str, str]] = []
    traits = entry.get("traits") or {}
    for bucket in ("tangible", "intangible"):
        items = traits.get(bucket) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if status not in ("approved", "locked"):
                continue
            text = item.get("text")
            item_id = item.get("id", "")
            if isinstance(text, str) and text.strip():
                found.append((f"traits.{bucket}", str(item_id), text))
    for key in ("abilities", "relationships"):
        items = entry.get(key) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if status not in ("approved", "locked"):
                continue
            text = item.get("text")
            item_id = item.get("id", "")
            if isinstance(text, str) and text.strip():
                found.append((key, str(item_id), text))
    return found


def _contradicts_qualities_locked(
    qualities_locked: list[Any], proposed_text: str
) -> list[str]:
    flags: list[str] = []
    if not qualities_locked:
        return flags
    normalized = normalize_trait_text(proposed_text)
    if not _NEGATION.search(proposed_text):
        return flags
    for quality in qualities_locked:
        if not isinstance(quality, str):
            continue
        q_norm = normalize_trait_text(quality)
        if not q_norm:
            continue
        if q_norm in normalized or any(
            token in normalized for token in q_norm.split() if len(token) > 3
        ):
            flags.append(
                f"proposed text negates locked quality {quality!r}: {proposed_text!r}"
            )
    return flags


def _contradicts_locked_description(
    locked_description: str | None, proposed_text: str
) -> list[str]:
    if not isinstance(locked_description, str) or not locked_description.strip():
        return []
    if not _NEGATION.search(proposed_text):
        return []
    normalized = normalize_trait_text(proposed_text)
    desc_norm = normalize_trait_text(locked_description)
    for phrase in ("brass tag", "amber", "braid", "clipboard"):
        if phrase in desc_norm and f"no {phrase}" in normalized:
            return [
                f"proposed text contradicts locked_description ({phrase!r}): {proposed_text!r}"
            ]
    return []


def check_proposal_conflicts(
    cast_entry: dict[str, Any],
    field: str,
    extracted_text: str,
) -> list[str]:
    """Return human-readable conflict messages; empty list means no conflict flagged."""
    flags: list[str] = []
    flags.extend(
        _contradicts_locked_description(
            cast_entry.get("locked_description"), extracted_text
        )
    )
    qualities = cast_entry.get("qualities_locked")
    if isinstance(qualities, list):
        flags.extend(_contradicts_qualities_locked(qualities, extracted_text))

    proposed_norm = normalize_trait_text(extracted_text)
    for item_field, item_id, text in _iter_approved_or_locked_items(cast_entry):
        if normalize_trait_text(text) == proposed_norm:
            continue
        if item_field != field and field.startswith("traits") and item_field.startswith(
            "traits"
        ):
            continue
        if _NEGATION.search(extracted_text) and normalize_trait_text(text) in proposed_norm:
            flags.append(
                f"conflicts with {item_field} item {item_id!r} ({text!r})"
            )
    return flags
