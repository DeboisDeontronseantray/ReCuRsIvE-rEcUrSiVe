#!/usr/bin/env python3
"""Live queue writer for comment clips.

Reads story-engine/rules/queue-policy.yaml ``comment_prompt_slots`` and writes
story-engine/queues/slots/<channel>.json. Placement is scheduling only: nothing
airs from this module. An explicit owner air-yes flag is required before a
comment clip is written into the queue.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parent
POLICY_PATH = ENGINE_ROOT / "rules" / "queue-policy.yaml"
QUEUE_SLOTS_DIR = ENGINE_ROOT / "queues" / "slots"

AIR_YES_ALIASES = ("trundle_air_yes", "thundertrundle_air_yes")


def load_policy(path: str | Path | None = None) -> dict:
    raw = yaml.safe_load(Path(path or POLICY_PATH).read_text()) or {}
    slots = raw.get("comment_prompt_slots") or {}
    if not isinstance(slots, dict):
        raise ValueError("comment_prompt_slots must be a mapping")
    return slots


def p90_eta(hist: list[float] | None, default: float, percentile: float) -> float:
    if not hist:
        return float(default)
    ordered = sorted(float(x) for x in hist)
    idx = min(len(ordered) - 1, int(percentile * len(ordered)))
    return ordered[idx]


def owner_air_yes(clip: dict, key: str) -> bool:
    if clip.get(key) is True:
        return True
    return any(clip.get(alias) is True for alias in AIR_YES_ALIASES)


def empty_queue(channel: int = 4, n_slots: int = 12, slot_len: float = 5.0) -> dict:
    """Synthetic future slots used by tests and offline placement."""
    return {
        "channel": channel,
        "slots": [
            {
                "slot_id": f"s{i}",
                "start": i * slot_len,
                "clip": None,
                "unaired": False,
                "protected": False,
                "kind": "open",
                "misses": 0,
            }
            for i in range(n_slots)
        ],
        "lineage": [],
    }


def _protected(slot: dict, policy: dict) -> bool:
    if not policy.get("protect_unaired_prompt_video", True):
        return False
    if slot.get("protected"):
        return True
    if slot.get("clip") and slot.get("unaired"):
        return True
    return False


def _eligible(slot: dict, need: float, policy: dict) -> bool:
    if slot.get("start") < need:
        return False
    if _protected(slot, policy):
        return False
    return True


def _lineage(queue: dict, row: tuple) -> None:
    queue.setdefault("lineage", []).append(tuple(row))


def place_comment_clip(
    clip: dict,
    queue: dict,
    *,
    now: float,
    hist: list[float] | None = None,
    policy: dict | None = None,
) -> str | None:
    """Place a comment clip at the first slot at or after now + p90 ETA + margin.

    Never displaces or reorders an unaired already-queued item. Refuses placement
    unless the owner air-yes flag is set. Does not air.
    """
    policy = policy or load_policy()
    lead = policy.get("render_lead_time") or {}
    placement = policy.get("placement") or {}
    hard = set(policy.get("hard_limit_violation", {}).get("applies_to") or [])
    cid = clip["id"]
    if hard & set(clip.get("flags") or []):
        _lineage(queue, (None, None, cid, "reject_hard_limit"))
        return None
    if placement.get("requires_owner_air_yes", True) and not owner_air_yes(
        clip, placement.get("owner_air_yes_key", "trundle_air_yes")
    ):
        _lineage(queue, (None, None, cid, "reject_no_owner_air_yes"))
        return None
    eta = p90_eta(
        hist,
        float(lead.get("render_eta_default_min", 15)),
        float(policy.get("p90_percentile", 0.9)),
    )
    need = now + eta + float(lead.get("margin_min", 10))
    for slot in queue["slots"]:
        if slot.get("start") < need:
            continue
        if _protected(slot, policy):
            clip["moves"] = clip.get("moves", 0) + 1
            _lineage(queue, (slot["slot_id"], slot.get("clip"), None, "protected_move"))
            continue
        if not _eligible(slot, need, policy):
            continue
        prev = slot.get("clip")
        slot["clip"] = cid
        slot["unaired"] = True
        slot["protected"] = True
        slot["kind"] = "comment"
        slot["misses"] = int(clip.get("misses") or 0)
        clip["slot_id"] = slot["slot_id"]
        _lineage(queue, (slot["slot_id"], prev, cid, "place"))
        return slot["slot_id"]
    _lineage(queue, (None, None, cid, "no_eligible_slot"))
    return None


def record_slot_miss(
    clip: dict,
    queue: dict,
    *,
    now: float,
    hist: list[float] | None = None,
    policy: dict | None = None,
) -> str | None:
    """Count a missed slot. After slot_miss_limit misses, slide to the next eligible slot."""
    policy = policy or load_policy()
    cid = clip["id"]
    current = None
    for slot in queue["slots"]:
        if slot.get("clip") == cid:
            current = slot
            break
    if current is None:
        _lineage(queue, (None, None, cid, "miss_unplaced"))
        return None
    current["misses"] = int(current.get("misses") or 0) + 1
    clip["misses"] = current["misses"]
    limit = int(policy.get("slot_miss_limit", 3))
    _lineage(queue, (current["slot_id"], cid, cid, "miss"))
    if current["misses"] < limit:
        return current["slot_id"]
    missed_id = current["slot_id"]
    missed_start = current["start"]
    current["clip"] = None
    current["unaired"] = False
    current["protected"] = False
    current["kind"] = "open"
    current["misses"] = 0
    clip.pop("slot_id", None)
    need = max(missed_start, now)
    for slot in queue["slots"]:
        if slot.get("start") <= need:
            continue
        if _protected(slot, policy):
            clip["moves"] = clip.get("moves", 0) + 1
            _lineage(queue, (slot["slot_id"], slot.get("clip"), None, "protected_move"))
            continue
        prev = slot.get("clip")
        slot["clip"] = cid
        slot["unaired"] = True
        slot["protected"] = True
        slot["kind"] = "comment"
        slot["misses"] = clip["misses"]
        clip["slot_id"] = slot["slot_id"]
        _lineage(queue, (slot["slot_id"], prev, cid, "slide_after_misses"))
        return slot["slot_id"]
    _lineage(queue, (missed_id, cid, None, "slide_no_eligible_slot"))
    return None


def slot_file(channel: int) -> Path:
    return QUEUE_SLOTS_DIR / f"{channel:02d}-military-boutique.json" if channel == 4 else QUEUE_SLOTS_DIR / f"{channel:02d}.json"


def write_queue(queue: dict, path: str | Path | None = None) -> Path:
    """Persist the live queue. Never marks a clip aired."""
    dest = Path(path) if path else slot_file(int(queue.get("channel") or 4))
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = deepcopy(queue)
    payload.setdefault("note", "comment_prompt_slots writer; unaired items are protected; air needs trundle_air_yes")
    dest.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    return dest


def load_queue(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
