"""Character-meta companion store and promotion (YAML + trait_observations.jsonl)."""

from charmeta.meta_prompt import rebuild_meta_prompt_for_character
from charmeta.observations import append_observation
from charmeta.promote import promote
from charmeta.stills_stub import extract, ingest_stills_meta_to_log
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
    "extract",
    "ingest_stills_meta_to_log",
    "load_companion",
    "load_schema",
    "missing_cast_ids",
    "promote",
    "rebuild_meta_prompt_for_character",
    "save_companion",
]
