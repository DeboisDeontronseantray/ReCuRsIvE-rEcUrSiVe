"""Character memory (D5): one companion YAML per channel at character-meta/<NN-channel>.yaml, keyed by cast id,
plus an add-only trait_observations.jsonl. Write-in levels cap how many memory beats enter a single prompt.

Proposals go through D15; only verified receipt reduction commits counters.
Trait observations remain append-only evidence."""
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


def summon(cast_meta, *, lifecycle=None, clip_id=None, proposals=None):
    """Propose reviewed character changes; receipt reduction owns counters."""
    from astra_lifecycle.contracts import require
    from astra_lifecycle.repo import propose_changes
    require(clip_id is not None and proposals is not None,
            "direct summon counters disabled; clip_id and canonical proposals required")
    return propose_changes("D15", clip_id, lifecycle=lifecycle, proposals=proposals)


def memory_beats(cast_meta, *, episode, season, clip_index, lifecycle=None, character_id=None):
    from astra_lifecycle.repo import lifecycle_store
    life = lifecycle_store(lifecycle, required=False)
    if life is not None:
        state = life.snapshot()
        card = state["cards"].get(character_id)
        if card is None:
            return []
        memories = [state["consequences"][cid] for cid in card["plastic"]["carried_consequences"]]
        cap = WRITEIN_CAP[card["writein_level"]]
        name = card["name"]
    else:
        # Pure wording preview; never writes counters or consequence clocks.
        memories = cast_meta["memories"]
        cap = WRITEIN_CAP[cast_meta["writein_level"]]
        name = cast_meta["name"]
    alive = [m for m in memories
             if layers_v4.tier_alive(m, episode, season, clip_index, lifecycle=life) and not LOOK.search(m["text"])]
    alive.sort(key=lambda m: -m["since_index"])
    return [f"{name} remembers: {m['text'].strip().rstrip('.')}" for m in alive[:cap]]


def present_cast(channel_meta, spec):
    text = " ".join([c.get("name", "") for c in spec.get("cast", [])] + list(spec.get("extra", []))
                    + [b.get("text", "") for b in spec.get("beats", [])])
    return [cid for cid, cm in channel_meta["cast"].items() if re.search(r"\b" + re.escape(cm["name"]) + r"\b", text)]


def proposed_update(channel_meta, summoned, *, lifecycle=None, clip_id=None, proposals=None):
    """Persist canonical proposals only; never predict or commit summon counters."""
    from astra_lifecycle.contracts import require
    require(clip_id is not None and proposals is not None,
            "canonical proposals and planned clip required; legacy counter updates disabled")
    return summon(channel_meta, lifecycle=lifecycle, clip_id=clip_id, proposals=proposals)


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
