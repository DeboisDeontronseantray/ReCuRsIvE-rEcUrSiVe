"""Layered static configs: channel < show < slot (later wins)."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ENGINE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = ENGINE_ROOT / "configs"
CONTINUITY_ROOT = ENGINE_ROOT / "data" / "continuity"


def _load_yaml(path: Path) -> dict:
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {path}")
    return data


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = deepcopy(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        elif k in out and isinstance(out[k], list) and isinstance(v, list):
            # slot/show lists replace rather than append (explicit override)
            out[k] = deepcopy(v)
        else:
            out[k] = deepcopy(v)
    return out


def load_channel(channel_id: str) -> dict:
    # accept "4", "04", or "04-military-boutique" (whole-number channels 2–22)
    matches = sorted((CONFIG_ROOT / "channels").glob("*.yaml"))
    cid = str(channel_id).strip()
    # 1) exact id match
    for path in matches:
        data = _load_yaml(path)
        if str(data.get("id")) == cid:
            data["_source"] = str(path)
            return data
    # 2) zero-padded number ("04") or stem prefix ("04-military-boutique")
    pad = cid.zfill(2) if cid.isdigit() else cid
    for path in matches:
        data = _load_yaml(path)
        stem = path.stem
        if stem == cid or stem.startswith(f"{cid}-") or stem.startswith(f"{pad}-") or stem == pad:
            data["_source"] = str(path)
            return data
    raise FileNotFoundError(f"No channel config for {channel_id!r} in {CONFIG_ROOT/'channels'}")


def load_show(show_id: str) -> dict:
    path = CONFIG_ROOT / "shows" / f"{show_id}.yaml"
    if not path.exists():
        # also allow matching title-ish stems
        for p in (CONFIG_ROOT / "shows").glob("*.yaml"):
            data = _load_yaml(p)
            if data.get("id") == show_id:
                data["_source"] = str(p)
                return data
        raise FileNotFoundError(path)
    data = _load_yaml(path)
    data["_source"] = str(path)
    return data


def load_slot(slot_id: str) -> dict:
    path = CONFIG_ROOT / "slots" / f"{slot_id}.yaml"
    if not path.exists():
        for p in (CONFIG_ROOT / "slots").glob("*.yaml"):
            data = _load_yaml(p)
            if data.get("id") == slot_id:
                data["_source"] = str(p)
                return data
        raise FileNotFoundError(path)
    data = _load_yaml(path)
    data["_source"] = str(path)
    return data


def merge_configs(channel_id: str, show_id: str, slot_id: str) -> dict[str, Any]:
    channel = load_channel(channel_id)
    show = load_show(show_id)
    slot = load_slot(slot_id)
    if show.get("channel") and str(show["channel"]) != str(channel.get("id")):
        raise ValueError(
            f"Show {show_id} belongs to channel {show.get('channel')}, not {channel_id}"
        )
    merged = {
        "channel": channel,
        "show": show,
        "slot": slot,
    }
    # Flattened overlay for prompt convenience: channel < show < slot
    flat = {}
    flat = _deep_merge(flat, {k: v for k, v in channel.items() if not k.startswith("_")})
    flat = _deep_merge(flat, {k: v for k, v in show.items() if not k.startswith("_")})
    flat = _deep_merge(flat, {k: v for k, v in slot.items() if not k.startswith("_")})
    merged["flat"] = flat
    merged["continuity_key"] = show.get("continuity_key") or show.get("id")
    return merged


def load_continuity(continuity_key: str) -> dict:
    path = CONTINUITY_ROOT / f"{continuity_key}.json"
    if not path.exists():
        return {"show_id": continuity_key, "episodes_done": 0, "notes": [], "last_export": None}
    return json_load(path)


def save_continuity(continuity_key: str, state: dict) -> Path:
    CONTINUITY_ROOT.mkdir(parents=True, exist_ok=True)
    path = CONTINUITY_ROOT / f"{continuity_key}.json"
    path.write_text(json_dumps(state))
    return path


def json_load(path: Path) -> dict:
    import json
    return json.loads(path.read_text())


def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
