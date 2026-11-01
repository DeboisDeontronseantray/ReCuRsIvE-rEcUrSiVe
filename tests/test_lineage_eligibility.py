import json
import os
import tempfile
import unittest
from pathlib import Path

from charmeta.config import proposal_threshold
from charmeta.observations import ObservationValidationError, append_observation
from charmeta.promote import promote
from charmeta.store import build_companion_from_bible, save_companion
from lineage.eligibility import (
    build_trait_promotion_aired_index,
    is_commercial_or_ad_row,
    is_forward_supply_row,
    is_show_master_row,
)
from lineage.aired import load_lineage_jsonl
from tests.test_support import BIBLE_FIXTURE, CAST_IDS, FIXTURES, LINEAGE_AIRED, LINEAGE_LEGACY


class TestLineageEligibility(unittest.TestCase):
    def test_ads_are_not_show_masters(self) -> None:
        rows = load_lineage_jsonl(LINEAGE_LEGACY)
        ad = next(r for r in rows if r["clip_id"] == "ch4-ad-armored-showroom-cruiser")
        self.assertTrue(is_commercial_or_ad_row(ad))
        self.assertFalse(is_show_master_row(ad))

    def test_forward_supply_row_excluded(self) -> None:
        rows = load_lineage_jsonl(LINEAGE_LEGACY)
        fs = next(r for r in rows if r["clip_id"] == "ch4-fs-run2-pocket-taupe")
        self.assertTrue(is_forward_supply_row(fs))
        self.assertFalse(is_show_master_row(fs))

    def test_aired_ads_do_not_count_for_promotion(self) -> None:
        index = build_trait_promotion_aired_index(load_lineage_jsonl(LINEAGE_AIRED))
        self.assertFalse(index.get("ch4-ad-armored-showroom-cruiser", True))
        self.assertTrue(index.get("test-aired-1", False))

    def test_observation_rejects_commercial_clip_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "obs.jsonl"
            with self.assertRaises(ObservationValidationError):
                append_observation(
                    path,
                    {
                        "clip_id": "ch4-ad-armored-showroom-cruiser",
                        "character": "mira_smirin",
                        "field": "traits.tangible",
                        "extracted_text": "brass tag",
                        "method": "aired_event",
                    },
                )


class TestPromoteUsesShowMastersOnly(unittest.TestCase):
    def test_three_aired_ads_do_not_propose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion_path = root / "companion.yaml"
            save_companion(
                companion_path,
                build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS),
            )
            observations_path = root / "observations.jsonl"
            trait = "sales floor gleam"
            lines = []
            for clip_id in (
                "ch4-ad-armored-showroom-cruiser",
                "ch4-ad-exo-gauntlet-vitrine",
                "ch4-ad-modular-field-pack",
            ):
                lines.append(
                    json.dumps(
                        {
                            "obs_id": f"obs-{clip_id}",
                            "clip_id": clip_id,
                            "character": "mira_smirin",
                            "field": "traits.tangible",
                            "extracted_text": trait,
                            "method": "aired_event",
                            "seen_count": 1,
                        }
                    )
                )
            observations_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            report = promote(
                companion_path=companion_path,
                observations_path=observations_path,
                lineage_path=LINEAGE_AIRED,
                apply=True,
            )
            self.assertEqual(report.proposals, [])


if __name__ == "__main__":
    unittest.main()
