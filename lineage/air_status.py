"""Detect when a LINEAGE row's source fields indicate AIRED status."""

from __future__ import annotations

from typing import Any

# Comment-prompt queue terminal + read_aliases (bible-v2.fixture.yaml prompt_queue_rule).
_AIRED_STATUS_TOKENS = frozenset({"AIRED", "aired"})


def normalize_status_token(value: str) -> str:
    return value.strip().upper()


def source_indicates_aired(row: dict[str, Any]) -> bool:
    """True when row source state says the clip has reached AIRED (before derived ``aired``)."""
    if row.get("air_yes") is True:
        return True

    status = row.get("status")
    if isinstance(status, str) and normalize_status_token(status) in _AIRED_STATUS_TOKENS:
        return True

    playout_status = row.get("playout_status")
    if isinstance(playout_status, str) and normalize_status_token(playout_status) in _AIRED_STATUS_TOKENS:
        return True

    queue_state = row.get("queue_state")
    if isinstance(queue_state, str) and normalize_status_token(queue_state) in _AIRED_STATUS_TOKENS:
        return True

    return False


def aired_derivation_source_label(row: dict[str, Any]) -> str:
    if row.get("air_yes") is True:
        return "air_yes:true"
    for key in ("status", "playout_status", "queue_state"):
        value = row.get(key)
        if isinstance(value, str) and normalize_status_token(value) in _AIRED_STATUS_TOKENS:
            return f"{key}:{value.strip()}"
    return "unknown"
