import pytest
import unittest

from lineage.aired import build_aired_index, clip_id_aired, load_lineage_jsonl
from tests.test_support import FIXTURES, LINEAGE_AIRED, LINEAGE_LEGACY


@pytest.mark.usefixtures("canonical_history")
class TestLineageAired(unittest.TestCase):
    def test_missing_aired_is_false(self) -> None:
        self.assertFalse(clip_id_aired({"clip_id": "x"}))

    def test_aired_true(self) -> None:
        self.assertFalse(clip_id_aired({"clip_id": "x", "aired": True}))

    def test_legacy_air_yes(self) -> None:
        self.assertFalse(clip_id_aired({"clip_id": "x", "air_yes": True}))

    def test_legacy_sample_rows_not_aired(self) -> None:
        rows = load_lineage_jsonl(LINEAGE_LEGACY)
        index = build_aired_index(rows)
        self.assertTrue(all(not aired for aired in index.values()))

    def test_aired_fixture_mixed(self) -> None:
        index = build_aired_index(load_lineage_jsonl(LINEAGE_AIRED))
        self.assertTrue(index["test-aired-1"])
        self.assertFalse(index["test-unaired-1"])
        self.assertFalse(index["test-missing-aired"])


if __name__ == "__main__":
    unittest.main()
