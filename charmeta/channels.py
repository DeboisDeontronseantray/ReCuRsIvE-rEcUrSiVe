"""Channel-aware cast ids and per-channel companion store paths (channels 2–22)."""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE_ROOT = REPO_ROOT / "character-meta"

_CHANNEL_SLUGS = {
    2: "02-news",
    4: "04-military-boutique",
    6: "06-shopping",
    8: "08-sitcom",
    10: "10-action",
    12: "12-90s",
    14: "14-music",
    16: "16-dossier",
}


def channel_slug(channel: int | str) -> str:
    if isinstance(channel, str) and channel.isdigit():
        channel = int(channel)
    if not isinstance(channel, int) or channel < 2 or channel > 22:
        raise ValueError(f"unsupported channel {channel!r}; expected 2–22")
    slug = _CHANNEL_SLUGS.get(channel)
    if slug is None:
        slug = f"{channel:02d}-channel"
    return slug


def namespaced_cast_id(channel: int | str, local_id: str) -> str:
    local = local_id.strip()
    if re.match(r"^ch\d{2}\.", local, re.I):
        return local.lower()
    ch = int(channel) if isinstance(channel, str) and channel.isdigit() else channel
    return f"ch{int(ch):02d}.{local}"


def local_cast_id(cast_id: str) -> str:
    if "." in cast_id and cast_id.lower().startswith("ch"):
        return cast_id.split(".", 1)[1]
    return cast_id


def parse_channel_from_cast_id(cast_id: str) -> int | None:
    match = re.match(r"^ch(\d{2})\.", cast_id, re.I)
    if not match:
        return None
    return int(match.group(1))


def store_root() -> Path:
    raw = os.environ.get("CHARMETA_STORE_ROOT", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_STORE_ROOT


def companion_path_for_channel(channel: int | str) -> Path:
    return store_root() / channel_slug(channel) / "companion.yaml"


def observations_path_for_channel(channel: int | str) -> Path:
    return store_root() / channel_slug(channel) / "trait_observations.jsonl"
