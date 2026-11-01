"""Short season bible + episode beats + ad pipeline (Grok / xAI)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.config_layers import (
    ENGINE_ROOT,
    load_continuity,
    merge_configs,
    save_continuity,
)
from app.model_routing import DEFAULTS, call_model
from app.tv.prompts import AD_USER, BIBLE_USER, EPISODE_BEATS_USER, SYSTEM_TV_SAFE

EXPORT_ROOT = ENGINE_ROOT / "data" / "exports"


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _j(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def generate_bible(merged: dict, model_alias: str | None = None) -> dict:
    alias = model_alias or DEFAULTS.get("bible", "grok-cheap")
    cont = load_continuity(merged["continuity_key"])
    raw = call_model(
        alias,
        SYSTEM_TV_SAFE,
        BIBLE_USER.format(
            channel_json=_j(merged["channel"]),
            show_json=_j(merged["show"]),
            slot_json=_j(merged["slot"]),
            continuity_json=_j(cont),
        ),
        json_mode=True,
        max_tokens=2500,
        step="bible",
        show_id=merged["show"].get("id"),
    )
    return _extract_json(raw)


def generate_episode_beats(
    merged: dict, bible: dict, model_alias: str | None = None
) -> dict:
    alias = model_alias or DEFAULTS.get("episode_beats", "grok-cheap")
    ep_count = int(merged["slot"].get("episode_count") or 3)
    length = int(merged["slot"].get("length_minutes") or 6)
    raw = call_model(
        alias,
        SYSTEM_TV_SAFE,
        EPISODE_BEATS_USER.format(
            episode_count=ep_count,
            length_minutes=length,
            bible_json=_j(bible),
            slot_json=_j(merged["slot"]),
        ),
        json_mode=True,
        max_tokens=4500,
        step="episode_beats",
        show_id=merged["show"].get("id"),
    )
    data = _extract_json(raw)
    eps = data.get("episodes") or []
    if len(eps) != ep_count:
        # keep what we got; caller can inspect
        data["_warning"] = f"expected {ep_count} episodes, got {len(eps)}"
    return data


def generate_ad(merged: dict, model_alias: str | None = None) -> dict:
    alias = model_alias or DEFAULTS.get("ad", "grok-cheap")
    ad = merged["slot"].get("ad") or {}
    duration = int(ad.get("duration_seconds") or 15)
    duration = max(10, min(30, duration))
    raw = call_model(
        alias,
        SYSTEM_TV_SAFE,
        AD_USER.format(
            channel_json=_j(merged["channel"]),
            show_json=_j(merged["show"]),
            ad_json=_j(ad),
            duration_seconds=duration,
        ),
        json_mode=True,
        max_tokens=2000,
        step="ad",
        show_id=merged["show"].get("id"),
    )
    data = _extract_json(raw)
    data["duration_seconds"] = duration
    return data


def run_smoke(
    channel_id: str = "4",
    show_id: str = "forward-supply",
    slot_id: str = "smoke-outline",
    model_alias: str = "grok-cheap",
    out_dir: Path | None = None,
) -> dict:
    merged = merge_configs(channel_id, show_id, slot_id)
    out = out_dir or (ENGINE_ROOT / "data" / "smoke" / f"{show_id}-{slot_id}")
    out.mkdir(parents=True, exist_ok=True)

    bible = generate_bible(merged, model_alias=model_alias)
    (out / "bible.json").write_text(_j(bible) + "\n")

    episodes = generate_episode_beats(merged, bible, model_alias=model_alias)
    (out / "episode_beats.json").write_text(_j(episodes) + "\n")

    ad = generate_ad(merged, model_alias=model_alias)
    (out / "ad.json").write_text(_j(ad) + "\n")

    from app.tv.export_cnb import export_cnb_prompts

    export_paths = export_cnb_prompts(
        channel=merged["channel"],
        show=merged["show"],
        bible=bible,
        episodes=episodes,
        ad=ad,
        out_dir=out / "cnb_export",
    )

    cont = load_continuity(merged["continuity_key"])
    cont["episodes_done"] = int(cont.get("episodes_done") or 0) + len(
        episodes.get("episodes") or []
    )
    cont["notes"] = (cont.get("notes") or []) + [
        f"smoke {slot_id}: {len(episodes.get('episodes') or [])} episodes"
    ]
    cont["last_export"] = str(out)
    save_continuity(merged["continuity_key"], cont)

    result = {
        "out_dir": str(out),
        "bible_path": str(out / "bible.json"),
        "episode_beats_path": str(out / "episode_beats.json"),
        "ad_path": str(out / "ad.json"),
        "cnb_export": export_paths,
        "continuity_key": merged["continuity_key"],
    }
    (out / "run_manifest.json").write_text(_j(result) + "\n")
    return result
