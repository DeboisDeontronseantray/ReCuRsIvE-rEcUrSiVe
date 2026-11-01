"""Shared paths for character-meta tests."""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "character-meta"
BIBLE_FIXTURE = FIXTURES / "bible-v2.fixture.yaml"
LINEAGE_AIRED = FIXTURES / "lineage-with-aired.jsonl"
LINEAGE_STATUS = FIXTURES / "lineage-with-status-aired.jsonl"
LINEAGE_LEGACY = FIXTURES / "lineage-sample.jsonl"
CAST_IDS = ["bill_dbears", "mira_smirin", "osmund", "tim"]


def companion_cast_entry(companion: dict, local_id: str) -> dict:
    """Resolve a cast entry by local id (handles chNN. namespaced keys)."""
    from charmeta.channels import local_cast_id, namespaced_cast_id

    cast = companion.get("cast") or {}
    if local_id in cast:
        return cast[local_id]
    meta = companion.get("meta") or {}
    channel = meta.get("channel")
    if channel is not None:
        key = namespaced_cast_id(int(channel), local_id)
        if key in cast:
            return cast[key]
    for key, entry in cast.items():
        if isinstance(key, str) and local_cast_id(key) == local_id:
            return entry
    raise KeyError(local_id)
