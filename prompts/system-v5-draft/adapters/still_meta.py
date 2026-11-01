"""Previous-clip still meta (D3). v1 only has the stub analyzer: the pinned vision model is recorded, never called."""
import re

import paths
from adapters.v4_bridge import apply_check_v42

LOOK = re.compile(r"\b" + apply_check_v42.VIS + r"\b", re.I)
IMAGED_NAME = re.compile(r"([A-Z][A-Z'.]+(?: [A-Z][A-Z'.]+)*) \(<(?:IMAGE_\d+|REF:[^>]+)>")


class StubAnalyzer:
    def __init__(self, descriptors):
        self._descriptors = list(descriptors)

    def analyze_still(self, path):
        return list(self._descriptors)


def pinned_vision_model():
    vm = paths.config("vision_model")
    return {k: vm[k] for k in ("provider", "model", "source", "looked_up_utc", "called")}


def imaged_names(spec):
    names = set(spec.get("ref_for") or {})
    names |= {c["name"] for c in spec.get("cast", []) if c.get("ref")}
    for x in spec.get("extra", []):
        names |= set(IMAGED_NAME.findall(x))
    return names | {n.split()[0] for n in names}


def filter_descriptors(descs, imaged_names):
    kept, dropped = [], []
    for d in descs:
        names_imaged = any(re.search(r"\b" + re.escape(n) + r"\b", d) for n in imaged_names)
        (dropped if names_imaged and LOOK.search(d) else kept).append(d)
    return kept, dropped


def next_start_frame(prev_clip_id, clips_root=None):
    return f"{clips_root}/{prev_clip_id}_last.png" if clips_root else f"<TT_CLIPS>/{prev_clip_id}_last.png"
