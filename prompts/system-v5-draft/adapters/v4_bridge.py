"""Read-only access to the live v4.2/v4.4 builder, gates and layer model. Nothing here writes or patches them."""
import sys

import paths

_TOOLS = str(paths.get("TT_PROMPTS_V4") / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

import apply_check_v42  # noqa: E402
import apply_check_v44  # noqa: E402
import build_prompt_v42  # noqa: E402
import layers_v4  # noqa: E402

V4_CONFIG = paths.get("TT_PROMPTS_V4") / "config"

__all__ = ["apply_check_v42", "apply_check_v44", "build_prompt_v42", "layers_v4", "V4_CONFIG"]
