import os
import unittest

from charmeta.config import proposal_threshold
from charmeta.name_guard import find_blocked_name_tokens, reject_if_blocked
from charmeta.prompt_injection import (
    SHOT_BODY_LAYER_ORDER,
    inject_character_meta_into_shot_body,
    trim_meta_for_injection,
)


class TestNameGuard(unittest.TestCase):
    def test_blocks_real_first_name(self) -> None:
        self.assertEqual(find_blocked_name_tokens("hello Drew there"), ["Drew"])
        with self.assertRaises(ValueError):
            reject_if_blocked("Hi Drew")


class TestPromptInjection(unittest.TestCase):
    def test_characters_layer_before_action_in_order(self) -> None:
        self.assertLess(
            SHOT_BODY_LAYER_ORDER.index("characters"),
            SHOT_BODY_LAYER_ORDER.index("action"),
        )

    def test_trim_caps_meta_length(self) -> None:
        long_text = "\n".join(f"traits.tangible: detail line {i}" for i in range(40))
        trimmed = trim_meta_for_injection(long_text, max_chars=120)
        self.assertLessEqual(len(trimmed), 120)

    def test_inject_merges_into_characters_slot(self) -> None:
        body = {"camera": "wide", "characters": "Tim: baseline", "action": "walks"}
        out = inject_character_meta_into_shot_body(
            body,
            ["Tim (canon meta): hovers at shoulder height"],
        )
        self.assertIn("baseline", out["characters"])
        self.assertIn("canon meta", out["characters"])
        self.assertEqual(out["action"], "walks")


class TestProposalThresholdConfig(unittest.TestCase):
    def test_env_override(self) -> None:
        previous = os.environ.get("CHARMETA_PROPOSAL_THRESHOLD_N")
        try:
            os.environ["CHARMETA_PROPOSAL_THRESHOLD_N"] = "5"
            self.assertEqual(proposal_threshold(), 5)
        finally:
            if previous is None:
                os.environ.pop("CHARMETA_PROPOSAL_THRESHOLD_N", None)
            else:
                os.environ["CHARMETA_PROPOSAL_THRESHOLD_N"] = previous


if __name__ == "__main__":
    unittest.main()
