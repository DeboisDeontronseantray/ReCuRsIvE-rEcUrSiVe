"""Character-meta companion store and promotion (YAML + trait_observations.jsonl)."""

from charmeta.observations import append_observation
from charmeta.promote import promote
from charmeta.store import (
    build_companion_from_bible,
    load_companion,
    load_schema,
    missing_cast_ids,
    save_companion,
)

__all__ = [
    "append_observation",
    "build_companion_from_bible",
    "load_companion",
    "load_schema",
    "missing_cast_ids",
    "promote",
    "save_companion",
]
