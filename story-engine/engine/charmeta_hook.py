"""Optional character-meta injection into assemble_prompt shot bodies."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from charmeta.channels import companion_path_for_channel, local_cast_id, namespaced_cast_id
from charmeta.prompt_injection import format_character_meta_block, inject_character_meta_into_shot_body
from charmeta.store import load_companion
from lineage.eligibility import is_forward_supply_row


def charmeta_enabled() -> bool:
    default = os.environ.get("CHARMETA_ENABLED_DEFAULT", "0").strip().lower()
    raw = os.environ.get("CHARMETA_ENABLED", default).strip().lower()
    return raw in ("1", "true", "yes")


def _show_slug_from_sidecar(sc: dict[str, Any]) -> str:
    show = sc.get("show") or sc.get("show_or_ad") or ""
    return str(show).strip().lower().replace("_", "-")


def apply_character_meta_to_body(
    body: dict[str, str],
    *,
    channel: int | str,
    sidecar: dict[str, Any],
) -> dict[str, str]:
    if not charmeta_enabled():
        return body
    show_slug = _show_slug_from_sidecar(sidecar)
    if show_slug in ("forward-supply", "forward_supply", "forward supply"):
        return body
    if is_forward_supply_row({"show": show_slug, "clip_id": sidecar.get("clip_id", "")}):
        return body

    companion_path = companion_path_for_channel(channel)
    if not companion_path.is_file():
        return body
    if "streaming/story-engine/continuity" in str(companion_path):
        return body

    doc = load_companion(companion_path)
    cast = doc.get("cast")
    if not isinstance(cast, dict):
        return body

    chr_locks = (sidecar.get("locks") or {}).get("chr") or []
    blocks: list[str] = []
    for lock_id in chr_locks:
        local = lock_id.split("-", 1)[-1] if isinstance(lock_id, str) else str(lock_id)
        for key in (namespaced_cast_id(channel, local), local):
            entry = cast.get(key)
            if not isinstance(entry, dict):
                continue
            meta = entry.get("meta_prompt") or {}
            text = meta.get("text") if isinstance(meta, dict) else ""
            if isinstance(text, str) and text.strip():
                blocks.append(
                    format_character_meta_block(
                        key,
                        text,
                        locked_description=entry.get("locked_description")
                        if isinstance(entry.get("locked_description"), str)
                        else None,
                    )
                )
            break

    if not blocks:
        return body
    shot_body = {k: v.replace("[Characters] ", "", 1) if k == "characters" and v.startswith("[Characters] ") else v for k, v in body.items()}
    merged = inject_character_meta_into_shot_body(shot_body, blocks)
    out = dict(body)
    out["characters"] = "[Characters] " + merged.get("characters", "")
    return out
