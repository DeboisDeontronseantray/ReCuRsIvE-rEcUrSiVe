import json
import tempfile
import unittest
from pathlib import Path

from charmeta.observations import load_observations
from charmeta.stills_stub import extract, ingest_stills_meta_to_log, observations_from_stills_meta
from tests.test_support import FIXTURES, LINEAGE_LEGACY


class TestStillsStub(unittest.TestCase):
    def test_extract_without_meta_returns_empty(self) -> None:
        self.assertEqual(extract("still.png", "clip-1", "mira_smirin"), [])

    def test_maps_stills_meta_json_to_observations(self) -> None:
        payload = json.loads(
            (FIXTURES / "stills-meta-sample.json").read_text(encoding="utf-8")
        )
        rows = observations_from_stills_meta(
            payload, clip_id="fixture-clip", character="mira_smirin"
        )
        self.assertEqual(len(rows), 3)
        fields = {row["field"] for row in rows}
        self.assertIn("traits.tangible", fields)
        self.assertIn("traits.intangible", fields)
        self.assertTrue(all(row["method"] == "still_analysis" for row in rows))

    def test_ingest_appends_only_to_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            obs = Path(tmp) / "trait_observations.jsonl"
            written = ingest_stills_meta_to_log(
                observations_path=obs,
                stills_meta_path=FIXTURES / "stills-meta-sample.json",
                clip_id="fixture-clip",
                character="mira_smirin",
                apply=True,
            )
            self.assertEqual(len(written), 3)
            self.assertEqual(len(load_observations(obs)), 3)

    def test_ingest_skips_forward_supply_lineage_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            obs = Path(tmp) / "trait_observations.jsonl"
            written = ingest_stills_meta_to_log(
                observations_path=obs,
                stills_meta_path=FIXTURES / "stills-meta-sample.json",
                clip_id="ch4-fs-run2-pocket-taupe",
                character="mira_smirin",
                lineage_path=LINEAGE_LEGACY,
                apply=True,
            )
            self.assertEqual(written, [])
            self.assertFalse(obs.exists())


if __name__ == "__main__":
    unittest.main()
