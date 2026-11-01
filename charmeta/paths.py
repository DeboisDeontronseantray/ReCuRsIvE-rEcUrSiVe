"""Live-path refusal for character-meta reads and writes."""

from __future__ import annotations

from pathlib import Path

from lineage.paths import (
    GENEALOGY_PATH_MARKER,
    LIVE_LINEAGE_FILE,
    LivePathRefusalError,
    refuse_live_path,
)

LIVE_BIBLE_MARKER = "story-engine/continuity/"
LIVE_BIBLE_FILE_SUFFIX = "bible-v2.yaml"
THUNDER_TRUNDLE_MARKER = "thunder-trundle/"


def _matches_charmeta_live_policy(path: Path) -> bool:
    posix = path.as_posix()
    resolved = str(path.resolve()) if path.exists() or path.is_absolute() else posix
    if THUNDER_TRUNDLE_MARKER in posix or THUNDER_TRUNDLE_MARKER in resolved:
        return True
    if LIVE_BIBLE_MARKER in posix or LIVE_BIBLE_MARKER in resolved:
        return True
    if path.name == LIVE_BIBLE_FILE_SUFFIX and "continuity" in posix:
        return True
    try:
        if path.resolve() == LIVE_LINEAGE_FILE.resolve():
            return True
    except OSError:
        pass
    if GENEALOGY_PATH_MARKER in posix or GENEALOGY_PATH_MARKER in resolved:
        return True
    return False


def refuse_charmeta_path(path: Path | str, *, allow_live_paths: bool) -> Path:
    """Refuse known live bible/ledger paths unless explicitly allowed."""
    target = Path(path)
    if allow_live_paths:
        return target
    if _matches_charmeta_live_policy(target):
        raise LivePathRefusalError(
            f"refusing live character-meta path {target!s}; set CHARMETA_ALLOW_LIVE_PATHS=1 only with Trundle's yes"
        )
    refuse_live_path(target, allow_live_paths=False)
    return target
