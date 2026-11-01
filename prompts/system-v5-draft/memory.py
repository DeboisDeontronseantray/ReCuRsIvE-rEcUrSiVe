"""Character memory (D5): one companion YAML per channel at character-meta/<NN-channel>.yaml, keyed by cast id,
plus an add-only trait_observations.jsonl. Write-in levels cap how many memory beats enter a single prompt.

Everything here is pure except append_trait_observation, which only ever appends."""
import copy
import json
import pathlib
import re

import contracts
import paths
from adapters.v4_bridge import apply_check_v42, layers_v4

_CFG = paths.config("assembly")
WRITEIN_CAP = {int(k): v for k, v in _CFG["writein_cap"].items()}
WRITEIN_MAX = _CFG["writein_max"]
LOOK = re.compile(r"\b" + apply_check_v42.VIS + r"\b", re.I)


def channel_file(character_meta_dir, channel):
    return pathlib.Path(character_meta_dir) / f"{contracts.channel_slug(channel)}.yaml"


def load_channel_meta(character_meta_dir, channel):
    p = channel_file(character_meta_dir, channel)
    doc = contracts.load_character_meta(p)
    if doc["channel"] != channel:
        raise contracts.ContractError(f"{p.name} is for {doc['channel']!r}, not {channel!r}")
    return doc


def summon(cast_meta):
    n = copy.deepcopy(cast_meta)
    n["summon_count"] = cast_meta["summon_count"] + 1
    n["writein_level"] = min(cast_meta["writein_level"] + 1, WRITEIN_MAX)
    return n


def memory_beats(cast_meta, *, episode, season, clip_index):
    alive = [m for m in cast_meta["memories"]
             if layers_v4.tier_alive(m, episode, season, clip_index) and not LOOK.search(m["text"])]
    alive.sort(key=lambda m: -m["since_index"])
    cap = WRITEIN_CAP[cast_meta["writein_level"]]
    return [f"{cast_meta['name']} remembers: {m['text'].strip().rstrip('.')}" for m in alive[:cap]]


def present_cast(channel_meta, spec):
    text = " ".join([c.get("name", "") for c in spec.get("cast", [])] + list(spec.get("extra", []))
                    + [b.get("text", "") for b in spec.get("beats", [])])
    return [cid for cid, cm in channel_meta["cast"].items() if re.search(r"\b" + re.escape(cm["name"]) + r"\b", text)]


def proposed_update(channel_meta, summoned):
    return {"file": f"{contracts.channel_slug(channel_meta['channel'])}.yaml", "channel": channel_meta["channel"],
            "cast": {cid: {k: summon(channel_meta["cast"][cid])[k] for k in ("summon_count", "writein_level")} for cid in summoned}}


def read_trait_observations(path, *, skip_clips=frozenset()):
    """skip_clips (aired.not_trait_evidence) drops ad and break rows already in the add-only log."""
    rows = [contracts.validate_trait_observation(r) for r in contracts.read_jsonl(path)]
    return [r for r in rows if r["clip_id"] not in skip_clips]


def append_trait_observation(path, row, *, skip_clips=frozenset()):
    """Appends one row; returns False without writing when its clip is an ad or break item (skip_clips)."""
    contracts.validate_trait_observation(row)
    if row["clip_id"] in skip_clips:
        return False
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")
    return True
