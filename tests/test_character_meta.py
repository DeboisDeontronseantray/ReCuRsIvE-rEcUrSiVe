import pytest
import hashlib
import tempfile
import unittest
from pathlib import Path

from charmeta.observations import ObservationValidationError, append_observation
from charmeta.promote import promote
from charmeta.store import build_companion_from_bible, save_companion
from tests.test_support import BIBLE_FIXTURE, CAST_IDS, FIXTURES, LINEAGE_AIRED


class TestObservationsAddOnly(unittest.TestCase):
    def test_append_validates_and_appends(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trait_observations.jsonl"
            row = append_observation(
                path,
                {
                    "clip_id": "test-aired-1",
                    "character": "bill_dbears",
                    "field": "traits.tangible",
                    "extracted_text": "brass tag, blank",
                    "method": "still_analysis",
                },
            )
            self.assertIn("obs_id", row)
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("\n"), 1)
            append_observation(
                path,
                {
                    "obs_id": "second-row",
                    "clip_id": "test-aired-2",
                    "character": "bill_dbears",
                    "field": "traits.tangible",
                    "extracted_text": "brass tag, blank",
                    "method": "aired_event",
                },
            )
            self.assertEqual(path.read_text(encoding="utf-8").count("\n"), 2)


class TestQuirksNotTraits(unittest.TestCase):
    def test_rejects_generation_quirk_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trait_observations.jsonl"
            with self.assertRaises(ObservationValidationError):
                append_observation(
                    path,
                    {
                        "clip_id": "x",
                        "character": "bill_dbears",
                        "field": "generation_quirks",
                        "extracted_text": "extra fingers",
                        "method": "human_note",
                    },
                )


@pytest.mark.usefixtures("canonical_history")
class TestPromoteThreshold(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.companion_path = root / "04-companion.yaml"
        doc = build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS)
        save_companion(self.companion_path, doc)
        self.observations_path = root / "trait_observations.jsonl"
        self.trait_text = "left side braid visible"

    def _append(self, clip_id: str) -> None:
        append_observation(
            self.observations_path,
            {
                "clip_id": clip_id,
                "character": "mira_smirin",
                "field": "traits.tangible",
                "extracted_text": self.trait_text,
                "method": "aired_event",
            },
        )

    def test_two_aired_clips_do_not_propose(self) -> None:
        self._append("test-aired-1")
        self._append("test-aired-2")
        report = promote(
            companion_path=self.companion_path,
            observations_path=self.observations_path,
            lineage_path=LINEAGE_AIRED,
            apply=True,
        )
        self.assertEqual(report.proposals, [])
        self.assertEqual(report.applied, [])

    def test_three_verified_clips_propose_without_companion_mutation(self) -> None:
        for cid in ("test-aired-1", "test-aired-2", "test-aired-3"):
            self._append(cid)
        before = self.companion_path.read_bytes()
        report = promote(companion_path=self.companion_path,
                         observations_path=self.observations_path,
                         lineage_path=LINEAGE_AIRED, apply=False)
        self.assertEqual(len(report.proposals), 1)
        self.assertEqual(report.proposals[0]["status"], "proposed")
        self.assertEqual(report.applied, [])
        self.assertEqual(before, self.companion_path.read_bytes())


class TestUnairedIgnored(unittest.TestCase):
    def test_unaired_and_missing_aired_do_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion_path = root / "companion.yaml"
            save_companion(
                companion_path,
                build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS),
            )
            observations_path = root / "observations.jsonl"
            text = "unaired-only trait"
            for clip_id in ("test-unaired-1", "test-missing-aired", "test-unaired-1"):
                append_observation(
                    observations_path,
                    {
                        "clip_id": clip_id,
                        "character": "tim",
                        "field": "traits.intangible",
                        "extracted_text": text,
                        "method": "human_note",
                    },
                )
            report = promote(
                companion_path=companion_path,
                observations_path=observations_path,
                lineage_path=LINEAGE_AIRED,
                apply=True,
            )
            self.assertEqual(report.proposals, [])


@pytest.mark.usefixtures("canonical_history")
class TestLockedConflictFlagged(unittest.TestCase):
    def test_conflict_blocks_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion_path = root / "companion.yaml"
            doc = build_companion_from_bible(BIBLE_FIXTURE, ["bill_dbears"])
            save_companion(companion_path, doc)
            observations_path = root / "observations.jsonl"
            conflict_text = "no brass tag on chest"
            for clip_id in ("test-aired-1", "test-aired-2", "test-aired-3"):
                append_observation(
                    observations_path,
                    {
                        "clip_id": clip_id,
                        "character": "bill_dbears",
                        "field": "traits.tangible",
                        "extracted_text": conflict_text,
                        "method": "aired_event",
                    },
                )
            report = promote(
                companion_path=companion_path,
                observations_path=observations_path,
                lineage_path=LINEAGE_AIRED,
                apply=True,
            )
            self.assertGreaterEqual(len(report.conflicts), 1)
            self.assertEqual(report.applied, [])
            self.assertNotIn(conflict_text, companion_path.read_text(encoding="utf-8"))


class TestBibleFixtureUnchanged(unittest.TestCase):
    def test_bible_bytes_unchanged_after_workflow(self) -> None:
        before = hashlib.sha256(BIBLE_FIXTURE.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion_path = root / "companion.yaml"
            save_companion(
                companion_path,
                build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS),
            )
            observations_path = root / "observations.jsonl"
            append_observation(
                observations_path,
                {
                    "clip_id": "test-aired-1",
                    "character": "osmund",
                    "field": "abilities",
                    "extracted_text": "carries modular field pack",
                    "method": "aired_event",
                },
            )
            promote(
                companion_path=companion_path,
                observations_path=observations_path,
                lineage_path=LINEAGE_AIRED,
                apply=False,
            )
        after = hashlib.sha256(BIBLE_FIXTURE.read_bytes()).hexdigest()
        self.assertEqual(before, after)


class TestStore(unittest.TestCase):
    def test_missing_cast_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_companion_from_bible(BIBLE_FIXTURE, ["bill_dbears", "not_a_cast_id"])


if __name__ == "__main__":
    unittest.main()
