import pytest
import json
import tempfile
import unittest
from pathlib import Path

from lineage.derive_aired import (
    derive_aired_append_patches,
    derive_aired_enriched_copy,
)
from lineage.paths import LivePathRefusalError, refuse_live_path
from tests.test_support import LINEAGE_STATUS


@pytest.mark.usefixtures("canonical_history")
class TestDeriveAiredEnrich(unittest.TestCase):
    def test_dry_run_lists_aired_status_clips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "derived.jsonl"
            report = derive_aired_enriched_copy(
                input_path=LINEAGE_STATUS,
                output_path=out,
                apply=False,
            )
            clip_ids = {item["clip_id"] for item in report.would_mark}
            self.assertEqual(
                clip_ids,
                {"e2e-aired-1", "e2e-aired-2", "e2e-aired-3"},
            )
            self.assertFalse(out.exists())

    def test_apply_writes_aired_without_touching_input(self) -> None:
        before = LINEAGE_STATUS.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "derived.jsonl"
            derive_aired_enriched_copy(
                input_path=LINEAGE_STATUS,
                output_path=out,
                apply=True,
            )
            rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
            aired_true = [r for r in rows if r.get("aired") is True]
            self.assertEqual(len(aired_true), 3)  # only the three canonical receipt-backed clips
        self.assertEqual(LINEAGE_STATUS.read_bytes(), before)


@pytest.mark.usefixtures("canonical_history")
class TestDeriveAiredAppendIdempotent(unittest.TestCase):
    def test_second_run_skips_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "patches.jsonl"
            first = derive_aired_append_patches(
                input_path=LINEAGE_STATUS,
                output_path=out,
                apply=True,
            )
            self.assertEqual(len(first.appended), 3)
            second = derive_aired_append_patches(
                input_path=LINEAGE_STATUS,
                output_path=out,
                apply=True,
            )
            self.assertEqual(second.appended, [])
            self.assertGreaterEqual(len(second.skipped_existing), 3)


class TestLivePathRefusal(unittest.TestCase):
    def test_refuses_genealogy_marker(self) -> None:
        blocked = Path("streaming/story-engine/genealogy/LINEAGE.jsonl")
        with self.assertRaises(LivePathRefusalError):
            refuse_live_path(blocked, allow_live_paths=False)

    def test_allows_with_flag(self) -> None:
        blocked = Path("streaming/story-engine/genealogy/LINEAGE.jsonl")
        refuse_live_path(blocked, allow_live_paths=True)


if __name__ == "__main__":
    unittest.main()
