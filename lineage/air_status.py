"""Compatibility readers for canonical, receipt-backed air state."""
from lineage.aired import clip_id_aired


def normalize_status_token(value: str) -> str:
    return value.strip().upper()


def source_indicates_aired(row, *, lifecycle=None):
    return clip_id_aired(row, lifecycle=lifecycle)


def aired_derivation_source_label(row, *, lifecycle=None):
    return "verified-lifecycle-receipt" if clip_id_aired(row, lifecycle=lifecycle) else "unknown"
