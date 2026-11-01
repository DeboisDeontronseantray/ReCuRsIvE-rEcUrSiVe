"""Environment-backed defaults for charmeta CLI (explicit paths only)."""

from __future__ import annotations

import os
from pathlib import Path

from charmeta.schema import proposal_threshold as schema_proposal_threshold


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


def proposal_threshold() -> int:
    """Default from CHARACTER-META-SCHEMA rules.N; override with CHARMETA_PROPOSAL_THRESHOLD_N."""
    raw = os.environ.get("CHARMETA_PROPOSAL_THRESHOLD_N", "").strip()
    if raw:
        value = int(raw)
        if value < 1:
            raise ValueError("CHARMETA_PROPOSAL_THRESHOLD_N must be a positive integer")
        return value
    return schema_proposal_threshold()
