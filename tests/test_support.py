"""Shared paths for character-meta tests."""

from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "character-meta"
BIBLE_FIXTURE = FIXTURES / "bible-v2.fixture.yaml"
LINEAGE_AIRED = FIXTURES / "lineage-with-aired.jsonl"
LINEAGE_STATUS = FIXTURES / "lineage-with-status-aired.jsonl"
LINEAGE_LEGACY = FIXTURES / "lineage-sample.jsonl"
CAST_IDS = ["bill_dbears", "mira_smirin", "osmund", "tim"]
