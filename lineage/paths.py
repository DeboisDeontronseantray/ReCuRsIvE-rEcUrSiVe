"""Refuse known live LINEAGE paths unless explicitly overridden."""

from __future__ import annotations

from pathlib import Path

LIVE_LINEAGE_FILE = Path(__file__).resolve().parents[1] / "live" / "LINEAGE.jsonl"
GENEALOGY_PATH_MARKER = "streaming/story-engine/genealogy"


class LivePathRefusalError(PermissionError):
    pass


def _path_matches_live_policy(path: Path) -> bool:
    resolved = path.resolve()
    try:
        if resolved == LIVE_LINEAGE_FILE.resolve():
            return True
    except OSError:
        if str(path) == str(LIVE_LINEAGE_FILE):
            return True
    posix = path.as_posix()
    resolved_str = str(resolved)
    if GENEALOGY_PATH_MARKER in posix or GENEALOGY_PATH_MARKER in resolved_str:
        return True
    return False


def refuse_live_path(path: Path | str, *, allow_live_paths: bool) -> Path:
    """Return resolved path or raise if it matches the live-path policy."""
    target = Path(path)
    if allow_live_paths:
        return target
    if _path_matches_live_policy(target):
        raise LivePathRefusalError(
            f"refusing live LINEAGE path {target!s}; pass --allow-live-paths only with Trundle's yes"
        )
    return target
