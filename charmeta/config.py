"""Environment-backed defaults for charmeta CLI (explicit paths only)."""

from __future__ import annotations

import os
from pathlib import Path


def allow_live_paths() -> bool:
    return os.environ.get("CHARMETA_ALLOW_LIVE_PATHS", "").strip() in {
        "1",
        "true",
        "yes",
    }


def env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return Path(raw)


def resolve_path(explicit: Path | None, env_name: str) -> Path | None:
    if explicit is not None:
        return explicit
    return env_path(env_name)
