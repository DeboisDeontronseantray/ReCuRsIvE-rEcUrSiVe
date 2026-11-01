"""Which LINEAGE rows may feed character-meta promotion (show masters only)."""

from __future__ import annotations

from typing import Any

FORWARD_SUPPLY_SHOW_SLUGS = frozenset(
    {"forward-supply", "forward_supply", "forward supply"}
)
BLACK_ICE_SHOW_SLUGS = frozenset(
    {"black-ice", "black_ice", "black ice", "military-boutique"}
)
_COMMERCIAL_KINDS = frozenset(
    {"commercial", "ad", "house_ad", "commercial_break", "sales_ad"}
)


def _slug(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("_", "-")


def clip_id_looks_commercial(clip_id: str) -> bool:
    lowered = clip_id.lower()
    if "-ad-" in lowered or lowered.startswith("ch4-ad-"):
        return True
    if lowered.endswith("-ad") or "-salesad" in lowered:
        return True
    return False


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


def is_show_master_row(row: dict[str, Any]) -> bool:
    """Show episode masters only — not ads, embeds, or Forward Supply filler."""
    if is_commercial_or_ad_row(row):
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


def build_trait_promotion_aired_index(rows: list[dict[str, Any]]) -> dict[str, bool]:
    """Map clip_id → counts toward the N aired-clip promotion threshold."""
    from lineage.aired import build_aired_index

    aired = build_aired_index(rows)
    by_id = row_index_by_clip_id(rows)
    return {
        clip_id: bool(aired.get(clip_id)) and is_show_master_row(by_id[clip_id])
        for clip_id in by_id
        if clip_id in aired
    }
