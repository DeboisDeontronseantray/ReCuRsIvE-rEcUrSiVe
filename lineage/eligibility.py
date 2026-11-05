"""Which LINEAGE rows may feed character-meta promotion (show masters only)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

FORWARD_SUPPLY_SHOW_SLUGS = frozenset(
    {"forward-supply", "forward_supply", "forward supply"}
)
BLACK_ICE_SHOW_SLUGS = frozenset(
    {"black-ice", "black_ice", "black ice", "military-boutique"}
)


def _slug(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("_", "-")


_COMMERCIAL_KINDS = frozenset(
    _slug(k) for k in ("commercial", "ad", "house_ad", "commercial_break", "sales_ad")
)
# Playout slot kinds other than `segment` (queue-mutation PLAN: breaks, IDs, bumpers).
_BREAK_KINDS = frozenset(
    _slug(k)
    for k in ("break", "station_break", "commercial_break", "bumper", "id", "ident", "interstitial")
)
_BREAK_CLIP_ID = re.compile(r"^(ch\d+-)?(break|bumper|ident|station-id)(-|$)")


def clip_id_looks_commercial(clip_id: str) -> bool:
    lowered = clip_id.lower()
    if "-ad-" in lowered or lowered.startswith("ch4-ad-"):
        return True
    if lowered.endswith("-ad") or "-salesad" in lowered:
        return True
    return False


def clip_id_looks_break(clip_id: str) -> bool:
    return bool(_BREAK_CLIP_ID.search(clip_id.lower().replace("_", "-")))


def clip_id_looks_forward_supply(clip_id: str) -> bool:
    lowered = clip_id.lower()
    return lowered.startswith("ch4-fs-") or "forward-supply" in lowered


def row_show_slug(row: dict[str, Any]) -> str:
    show = _slug(row.get("show"))
    if show:
        return show
    prompt_layers = row.get("prompt_layers")
    if isinstance(prompt_layers, dict):
        wrapper = prompt_layers.get("show_or_ad")
        if isinstance(wrapper, str) and wrapper.strip():
            return _slug(wrapper)
    return ""


def is_forward_supply_row(row: dict[str, Any]) -> bool:
    show = row_show_slug(row)
    if show in FORWARD_SUPPLY_SHOW_SLUGS:
        return True
    clip_id = row.get("clip_id")
    if isinstance(clip_id, str) and clip_id_looks_forward_supply(clip_id):
        return True
    file_path = row.get("file")
    if isinstance(file_path, str):
        lowered = file_path.lower()
        if "forward-supply" in lowered or "ch04_forward-supply" in lowered:
            return True
    return False


def is_commercial_or_ad_row(row: dict[str, Any]) -> bool:
    if row.get("row_type") == "embed" or row.get("origin") == "embed":
        return True
    kind = _slug(row.get("kind") or row.get("clip_kind"))
    if kind in _COMMERCIAL_KINDS:
        return True
    format_kind = _slug(row.get("format"))
    if format_kind in _COMMERCIAL_KINDS or format_kind == "commercial":
        return True
    clip_id = row.get("clip_id")
    if isinstance(clip_id, str) and clip_id_looks_commercial(clip_id):
        return True
    file_path = row.get("file")
    if isinstance(file_path, str):
        lowered = file_path.lower()
        if "salesad" in lowered or "/house-ads/" in lowered:
            return True
        if "sales-overlay" in lowered and "parody_salesad" in lowered:
            return True
    origin = _slug(row.get("origin"))
    if origin == "overlay-edit" and isinstance(clip_id, str) and clip_id_looks_commercial(
        clip_id
    ):
        return True
    return False


def is_break_row(row: dict[str, Any]) -> bool:
    for key in ("kind", "clip_kind", "slot_kind", "format"):
        if _slug(row.get(key)) in _BREAK_KINDS:
            return True
    clip_id = row.get("clip_id")
    return isinstance(clip_id, str) and clip_id_looks_break(clip_id)


def is_ad_or_break_row(row: dict[str, Any]) -> bool:
    """Ads and breaks may show cast, but they are never trait evidence."""
    return is_commercial_or_ad_row(row) or is_break_row(row)


def is_show_master_row(row: dict[str, Any]) -> bool:
    """Show episode masters only — not ads, breaks, embeds, or Forward Supply filler."""
    if is_ad_or_break_row(row):
        return False
    if is_forward_supply_row(row):
        return False
    if row.get("shot_id") or row.get("segment_sidecar"):
        return True
    show = row_show_slug(row)
    if show in BLACK_ICE_SHOW_SLUGS:
        return True
    clip_id = row.get("clip_id")
    if isinstance(clip_id, str):
        if clip_id.startswith(("test-aired-", "e2e-aired-")):
            return True
        if clip_id.startswith("bi-") or clip_id.startswith("ch4-bi-"):
            return True
    return False


def ad_or_break_clip_ids(
    lineage_rows: list[dict[str, Any]],
    slot_rows: Iterable[dict[str, Any]] = (),
) -> set[str]:
    """Clip ids that aired (or will air) as an ad or break item, from LINEAGE rows or playout slot `kind`.

    Slots join LINEAGE on `occupant_global_no == global_no`."""
    clip_by_global_no = {
        row["global_no"]: row["clip_id"]
        for row in lineage_rows
        if type(row.get("global_no")) is int and isinstance(row.get("clip_id"), str)
    }
    out = {
        row["clip_id"]
        for row in lineage_rows
        if isinstance(row.get("clip_id"), str) and is_ad_or_break_row(row)
    }
    for slot in slot_rows:
        clip_id = clip_by_global_no.get(slot.get("occupant_global_no"))
        if clip_id and (_slug(slot.get("kind")) in _BREAK_KINDS | _COMMERCIAL_KINDS):
            out.add(clip_id)
    return out


def row_index_by_clip_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        clip_id = row.get("clip_id")
        if isinstance(clip_id, str) and clip_id.strip():
            index[clip_id.strip()] = row
    return index


def clip_eligible_for_trait_promotion(
    clip_id: str,
    *,
    aired_index: dict[str, bool],
    row_by_clip_id: dict[str, dict[str, Any]],
) -> bool:
    if not aired_index.get(clip_id, False):
        return False
    row = row_by_clip_id.get(clip_id)
    if row is None:
        return False
    return is_show_master_row(row)


def build_trait_promotion_aired_index(rows: list[dict[str, Any]], *, lifecycle=None) -> dict[str, bool]:
    """Map clip_id → counts toward the N aired-clip promotion threshold."""
    from lineage.aired import build_aired_index

    aired = build_aired_index(rows, lifecycle=lifecycle)
    by_id = row_index_by_clip_id(rows)
    return {
        clip_id: bool(aired.get(clip_id)) and is_show_master_row(by_id[clip_id])
        for clip_id in by_id
        if clip_id in aired
    }
