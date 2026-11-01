"""The previous clip's v42 spec: the base every next-clip assembly starts from (D2: wrap the v42 builder)."""
import copy
import json
import pathlib
import re

from adapters.v4_bridge import build_prompt_v42

REQUIRED = ("clip_id", "channel", "duration", "clip_type")
CLIP_ID = re.compile(r"^([A-Za-z]+)(\d+)$")


class BaseSpecError(ValueError):
    pass


def load(path):
    spec = json.loads(pathlib.Path(path).read_text())
    missing = [k for k in REQUIRED if k not in spec]
    if missing:
        raise BaseSpecError(f"{path}: base spec missing {missing}")
    CLIP_ID.match(spec["clip_id"]) or _bad(spec["clip_id"])
    return copy.deepcopy(spec)


def _bad(cid):
    raise BaseSpecError(f"clip id {cid!r} must be letters followed by digits, e.g. NP16")


def clip_index(cid):
    m = CLIP_ID.match(cid) or _bad(cid)
    return int(m.group(2))


def next_clip_id(cid):
    m = CLIP_ID.match(cid) or _bad(cid)
    return f"{m.group(1)}{int(m.group(2)) + 1:0{len(m.group(2))}d}"


def verify_parity(spec, args_path, meta_path):
    r = build_prompt_v42.build(copy.deepcopy(spec), strict=True)
    live_args = json.loads(pathlib.Path(args_path).read_text())
    live_meta = json.loads(pathlib.Path(meta_path).read_text())
    return r["args"] == live_args and r["sidecar"] == live_meta
