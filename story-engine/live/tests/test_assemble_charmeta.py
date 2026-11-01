import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "story-engine" / "engine"))

from charmeta.channels import companion_path_for_channel, namespaced_cast_id
from charmeta.store import build_companion_from_bible, save_companion
from charmeta_hook import apply_character_meta_to_body, charmeta_enabled
from tests.test_support import BIBLE_FIXTURE, CAST_IDS


class TestAssembleCharmetaHook(unittest.TestCase):
    def test_disabled_by_default(self) -> None:
        os.environ.pop("CHARMETA_ENABLED", None)
        body = {"characters": "[Characters] baseline"}
        out = apply_character_meta_to_body(body, channel=4, sidecar={"show": "black-ice"})
        self.assertEqual(out, body)

    def test_injects_when_enabled_and_companion_present(self) -> None:
        os.environ["CHARMETA_ENABLED"] = "1"
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["CHARMETA_STORE_ROOT"] = tmp
            doc = build_companion_from_bible(BIBLE_FIXTURE, ["mira_smirin"], channel=4)
            entry = doc["cast"][namespaced_cast_id(4, "mira_smirin")]
            entry["meta_prompt"] = {
                "text": "slate-gray duty tunic",
                "built_from": ["t1"],
                "version": 1,
            }
            save_companion(companion_path_for_channel(4), doc)
            body = {"characters": "[Characters] CHR-mira baseline"}
            out = apply_character_meta_to_body(
                body,
                channel=4,
                sidecar={"show": "black-ice", "locks": {"chr": ["CHR-mira_smirin"]}},
            )
            self.assertIn("canon meta", out["characters"])
            self.assertIn("slate-gray", out["characters"])

    def test_skips_forward_supply_show(self) -> None:
        os.environ["CHARMETA_ENABLED"] = "1"
        body = {"characters": "[Characters] baseline"}
        out = apply_character_meta_to_body(
            body, channel=4, sidecar={"show": "forward-supply"}
        )
        self.assertEqual(out["characters"], body["characters"])

    def tearDown(self) -> None:
        os.environ.pop("CHARMETA_ENABLED", None)
        os.environ.pop("CHARMETA_STORE_ROOT", None)


if __name__ == "__main__":
    unittest.main()
