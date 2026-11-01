"""Pure symbols from the story engine: the never-words pattern, protected layer names, the comment bend and hard limits.
`cats()` is deliberately not re-exported: comment intake is raw collection plus insertion, with no semantic parsing (D4)."""
import sys

import paths

_ENGINE = str(paths.get("TT_STORY_ENGINE") / "engine")
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)

from assemble_prompt import NEVER_WORDS, PROTECTED  # noqa: E402
from bundle_assembler import HARD, bend  # noqa: E402

__all__ = ["NEVER_WORDS", "PROTECTED", "HARD", "bend"]
