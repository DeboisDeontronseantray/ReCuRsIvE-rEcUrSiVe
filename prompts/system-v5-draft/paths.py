"""Path resolution for system-v5-draft.

Order: environment variable, then the git-ignored `tt_paths.json` next to this file, then the repo-relative
default below. Keys without a default (the live comment spool, the character-meta folder, the clip folder, the
playout slot sheet, LINEAGE) must be configured on the live box; they are never guessed."""
import json
import os
import pathlib

V5 = pathlib.Path(__file__).resolve().parent
REPO = V5.parents[1]
LOCAL_CONFIG = V5 / "tt_paths.json"
CONFIG_DIR = V5 / "config"

DEFAULTS = {
    "TT_PROMPTS_V4": REPO / "prompts" / "system-v4-20261030",
    "TT_STORY_ENGINE": REPO / "story-engine",
    "TT_CLIPS": None,
    "TT_COMMENT_SPOOL": None,
    "TT_COMMENT_CONSUMED": None,
    "TT_CHARACTER_META": None,
    "TT_SLOTS": None,
    "TT_LINEAGE": None,
}


class PathNotConfigured(LookupError):
    pass


def _local():
    return json.loads(LOCAL_CONFIG.read_text()) if LOCAL_CONFIG.is_file() else {}


def get(key, *, required=False):
    if key not in DEFAULTS:
        raise KeyError(f"unknown path key {key!r}")
    val = os.environ.get(key) or _local().get(key) or DEFAULTS[key]
    if val is None and required:
        raise PathNotConfigured(f"{key} is not set; set the env var or add it to {LOCAL_CONFIG.name}")
    return pathlib.Path(val) if val is not None else None


def config(name):
    return json.loads((CONFIG_DIR / f"{name}.json").read_text())
