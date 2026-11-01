import unittest
from pathlib import Path

from charmeta.cli import main
from charmeta.paths import refuse_charmeta_path
from lineage.paths import LivePathRefusalError


class TestCharmetaLivePaths(unittest.TestCase):
    def test_refuses_live_bible_marker(self) -> None:
        blocked = Path("streaming/story-engine/continuity/ch04-military-boutique/bible-v2.yaml")
        with self.assertRaises(LivePathRefusalError):
            refuse_charmeta_path(blocked, allow_live_paths=False)

    def test_cli_dry_run_append_on_fixture_path(self) -> None:
        obs = Path("tests/fixtures/character-meta/_cli-dry-run.jsonl")
        if obs.exists():
            obs.unlink()
        code = main(
            [
                "append-obs",
                "--observations",
                str(obs),
                "--clip-id",
                "cli-test",
                "--character",
                "tim",
                "--field",
                "traits.intangible",
                "--text",
                "servo chirps",
            ]
        )
        self.assertEqual(code, 0)
        self.assertFalse(obs.exists())


if __name__ == "__main__":
    unittest.main()
