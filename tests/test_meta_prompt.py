import tempfile
import unittest
from pathlib import Path

from charmeta.meta_prompt import build_meta_prompt_text, rebuild_meta_prompt_for_character
from charmeta.prompt_injection import max_character_meta_chars
from charmeta.store import build_companion_from_bible
from tests.test_support import BIBLE_FIXTURE, CAST_IDS


class TestMetaPrompt(unittest.TestCase):
    def test_ignores_proposed_entries(self) -> None:
        doc = build_companion_from_bible(BIBLE_FIXTURE, ["mira_smirin"])
        entry = doc["cast"]["mira_smirin"]
        entry["traits"]["tangible"].append(
            {
                "id": "trait-proposed",
                "text": "proposed-only braid",
                "source_clip": "x",
                "status": "proposed",
            }
        )
        entry["traits"]["tangible"].append(
            {
                "id": "trait-approved",
                "text": "slate-gray duty tunic",
                "source_clip": "y",
                "status": "approved",
            }
        )
        text, built_from = build_meta_prompt_text(entry)
        self.assertIn("slate-gray duty tunic", text)
        self.assertNotIn("proposed-only braid", text)
        self.assertIn("trait-approved", built_from)
        self.assertNotIn("trait-proposed", built_from)

    def test_rebuild_bumps_version_on_apply(self) -> None:
        doc = build_companion_from_bible(BIBLE_FIXTURE, ["tim"])
        entry = doc["cast"]["tim"]
        entry["abilities"].append(
            {
                "id": "ability-locked-1",
                "text": "hovers at shoulder height",
                "first_seen_clip": "z",
                "times_seen": 2,
                "status": "locked",
            }
        )
        dry = rebuild_meta_prompt_for_character(doc, "tim", apply=False)
        self.assertEqual(dry.previous_version, 0)
        self.assertEqual(dry.new_version, 0)
        applied = rebuild_meta_prompt_for_character(doc, "tim", apply=True)
        self.assertEqual(applied.new_version, 1)
        self.assertIn("hovers at shoulder height", entry["meta_prompt"]["text"])

    def test_rebuilt_text_respects_injection_cap(self) -> None:
        doc = build_companion_from_bible(BIBLE_FIXTURE, ["tim"])
        entry = doc["cast"]["tim"]
        for i in range(30):
            entry["traits"]["tangible"].append(
                {
                    "id": f"trait-{i}",
                    "text": f"visible detail number {i} with extra words",
                    "source_clip": "z",
                    "status": "approved",
                }
            )
        text, _ = build_meta_prompt_text(entry)
        self.assertLessEqual(len(text), max_character_meta_chars())


if __name__ == "__main__":
    unittest.main()
