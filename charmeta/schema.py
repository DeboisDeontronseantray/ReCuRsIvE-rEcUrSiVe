"""Load CHARACTER-META schema and validation constants."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = (
    REPO_ROOT / "docs" / "spec" / "character-meta" / "CHARACTER-META-SCHEMA-v1.yaml"
)

OBSERVATION_FIELDS = frozenset(
    {
        "traits.tangible",
        "traits.intangible",
        "abilities",
        "relationships",
    }
)

OBSERVATION_METHODS = frozenset(
    {
        "still_analysis",
        "aired_event",
        "human_note",
    }
)

STATES = frozenset({"proposed", "approved", "locked", "retired"})


@lru_cache(maxsize=1)
def load_schema(path: Path | None = None) -> dict[str, Any]:
    schema_path = path or DEFAULT_SCHEMA_PATH
    data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"schema root must be a mapping: {schema_path}")
    return data


def proposal_threshold(schema: dict[str, Any] | None = None) -> int:
    doc = schema or load_schema()
    rules = doc.get("rules") or {}
    n_value = rules.get("N", 3)
    if not isinstance(n_value, int) or n_value < 1:
        raise ValueError("schema rules.N must be a positive integer")
    return n_value


def empty_meta_prompt() -> dict[str, Any]:
    return {"text": "", "built_from": [], "version": 0}


def empty_cast_additions() -> dict[str, Any]:
    return {
        "traits": {"tangible": [], "intangible": []},
        "abilities": [],
        "relationships": [],
        "meta_prompt": empty_meta_prompt(),
    }
