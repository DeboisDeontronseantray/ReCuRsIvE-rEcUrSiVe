"""Tests for shared name filter module."""

import base64
import unittest

from name_filters import NEVER_WORDS, find_blocked_name_tokens


class TestNameFilters(unittest.TestCase):
    def test_never_words_blocks_legacy_owner_name(self) -> None:
        legacy = base64.b64decode("ZHJldw==").decode()
        self.assertTrue(NEVER_WORDS.search(f"hello {legacy}"))
        self.assertEqual(
            find_blocked_name_tokens(f"HELLO {legacy.upper()}"),
            [legacy.upper()],
        )

    def test_trundle_allowed(self) -> None:
        self.assertIsNone(NEVER_WORDS.search("trundle's yes"))


if __name__ == "__main__":
    unittest.main()
