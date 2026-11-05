import pytest
import tempfile
import unittest
from pathlib import Path

from charmeta.observations import append_observation
from charmeta.promote import promote
from charmeta.store import build_companion_from_bible, save_companion
from lineage.derive_aired import derive_aired_enriched_copy
from tests.test_support import BIBLE_FIXTURE, CAST_IDS, LINEAGE_STATUS


@pytest.mark.usefixtures("canonical_history")
class TestEndToEndDerivePromote(unittest.TestCase):
    def test_status_fixture_derive_then_promote_proposes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            derived_lineage = root / "lineage-derived.jsonl"
            derive_aired_enriched_copy(
                input_path=LINEAGE_STATUS,
                output_path=derived_lineage,
                apply=True,
            )

            companion_path = root / "companion.yaml"
            save_companion(
                companion_path,
                build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS),
            )
            observations_path = root / "observations.jsonl"
            trait = "cyan rim light on cheek"
            for clip_id in ("e2e-aired-1", "e2e-aired-2", "e2e-aired-3"):
                append_observation(
                    observations_path,
                    {
                        "clip_id": clip_id,
                        "character": "mira_smirin",
                        "field": "traits.tangible",
                        "extracted_text": trait,
                        "method": "aired_event",
                    },
                )

            report = promote(
                companion_path=companion_path,
                observations_path=observations_path,
                lineage_path=derived_lineage,
                apply=False,
            )
            self.assertEqual(len(report.proposals), 1)
            self.assertEqual(report.proposals[0]["status"], "proposed")
            self.assertNotIn(trait, companion_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
