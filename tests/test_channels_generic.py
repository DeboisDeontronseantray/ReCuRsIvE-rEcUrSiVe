import tempfile
import unittest
from pathlib import Path

from charmeta.channels import (
    channel_slug,
    companion_path_for_channel,
    namespaced_cast_id,
    parse_channel_from_cast_id,
    store_root,
)
from charmeta.store import build_companion_from_bible, save_companion
from tests.test_support import BIBLE_FIXTURE, CAST_IDS, FIXTURES


class TestChannelGeneric(unittest.TestCase):
    def test_namespaced_cast_ids(self) -> None:
        self.assertEqual(namespaced_cast_id(12, "marla"), "ch12.marla")
        self.assertEqual(parse_channel_from_cast_id("ch04.bill_dbears"), 4)

    def test_channel_slugs_2_22(self) -> None:
        self.assertEqual(channel_slug(2), "02-news")
        self.assertEqual(channel_slug(16), "16-dossier")
        self.assertTrue(channel_slug(20).endswith("-channel"))

    def test_per_channel_store_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            import os

            os.environ["CHARMETA_STORE_ROOT"] = tmp
            p4 = companion_path_for_channel(4)
            p12 = companion_path_for_channel(12)
            self.assertIn("04-military-boutique", str(p4))
            self.assertIn("12-90s", str(p12))
            doc = build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS[:1], channel=4)
            save_companion(p4, doc)
            self.assertIn("ch04.bill_dbears", doc["cast"])
            self.assertTrue(p4.is_file())

    def test_ch2_ch12_ch16_fixture_companions(self) -> None:
        for name in ("ch02-companion.yaml", "ch12-companion.yaml", "ch16-companion.yaml"):
            path = FIXTURES / name
            self.assertTrue(path.is_file(), name)
            text = path.read_text(encoding="utf-8")
            self.assertIn("meta_prompt:", text)

    def tearDown(self) -> None:
        import os

        os.environ.pop("CHARMETA_STORE_ROOT", None)


if __name__ == "__main__":
    unittest.main()
