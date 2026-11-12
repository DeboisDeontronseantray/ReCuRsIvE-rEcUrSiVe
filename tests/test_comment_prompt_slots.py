"""Comment-slot placement honors queue-policy.yaml comment_prompt_slots.

Covers placement time (now + p90 ETA + margin), protect-unaired, and
slide-after-N-misses. Placement is not air: the owner air-yes flag is required.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "story-engine" / "engine"))

from queue_writer import (
    empty_queue,
    load_policy,
    p90_eta,
    place_comment_clip,
    record_slot_miss,
    write_queue,
)

POLICY = load_policy()
LEAD = POLICY["render_lead_time"]
MARGIN = LEAD["margin_min"]
DEFAULT_ETA = LEAD["render_eta_default_min"]
P90 = POLICY["p90_percentile"]
MISS_LIMIT = POLICY["slot_miss_limit"]
AIR_KEY = POLICY["placement"]["owner_air_yes_key"]


def _clip(cid: str, **extra) -> dict:
    row = {"id": cid, "moves": 0, "misses": 0, AIR_KEY: True}
    row.update(extra)
    return row


def test_policy_values_come_from_yaml():
    assert MARGIN == 10
    assert DEFAULT_ETA == 15
    assert MISS_LIMIT == 3
    assert POLICY["protect_unaired_prompt_video"] is True
    assert POLICY["placement"]["requires_owner_air_yes"] is True
    assert AIR_KEY == "trundle_air_yes"


def test_placement_is_now_plus_p90_plus_margin():
    queue = empty_queue()
    assert place_comment_clip(_clip("p1"), queue, now=0, hist=[]) == "s5"
    assert queue["slots"][5]["clip"] == "p1"
    assert queue["slots"][5]["unaired"] is True
    need = 0 + p90_eta([], DEFAULT_ETA, P90) + MARGIN
    assert queue["slots"][5]["start"] == need


def test_placement_uses_logged_p90_not_the_default():
    queue = empty_queue()
    assert place_comment_clip(_clip("p3"), queue, now=0, hist=[10, 12, 30]) == "s8"
    assert queue["slots"][8]["start"] >= 0 + 30 + MARGIN


def test_protect_unaired_never_displaces_or_reorders():
    queue = empty_queue()
    first = place_comment_clip(_clip("p1"), queue, now=0, hist=[])
    before = [slot["clip"] for slot in queue["slots"]]
    second = place_comment_clip(_clip("p2"), queue, now=0, hist=[])
    after = [slot["clip"] for slot in queue["slots"]]
    assert first == "s5"
    assert second == "s6"
    assert after[5] == "p1"
    assert after[6] == "p2"
    assert after[:6] == before[:6]


def test_unapproved_clip_is_not_placed():
    queue = empty_queue()
    clip = {"id": "raw", "moves": 0, AIR_KEY: False}
    assert place_comment_clip(clip, queue, now=0, hist=[]) is None
    assert all(slot.get("clip") is None for slot in queue["slots"])
    assert (None, None, "raw", "reject_no_owner_air_yes") in queue["lineage"]


def test_slide_after_three_misses_to_next_eligible():
    queue = empty_queue()
    clip = _clip("late")
    assert place_comment_clip(clip, queue, now=0, hist=[]) == "s5"
    assert record_slot_miss(clip, queue, now=0, hist=[]) == "s5"
    assert record_slot_miss(clip, queue, now=0, hist=[]) == "s5"
    assert clip["misses"] == 2
    assert queue["slots"][5]["clip"] == "late"
    slid = record_slot_miss(clip, queue, now=0, hist=[])
    assert slid == "s6"
    assert clip["misses"] == MISS_LIMIT
    assert queue["slots"][5]["clip"] is None
    assert queue["slots"][5]["unaired"] is False
    assert queue["slots"][6]["clip"] == "late"
    assert queue["slots"][6]["unaired"] is True
    assert any(row[-1] == "slide_after_misses" for row in queue["lineage"])


def test_slide_skips_unaired_occupant():
    queue = empty_queue()
    keep = _clip("keep")
    mover = _clip("mover")
    assert place_comment_clip(keep, queue, now=0, hist=[]) == "s5"
    assert place_comment_clip(mover, queue, now=0, hist=[]) == "s6"
    for _ in range(MISS_LIMIT):
        record_slot_miss(mover, queue, now=0, hist=[])
    assert queue["slots"][5]["clip"] == "keep"
    assert queue["slots"][6]["clip"] is None
    assert queue["slots"][7]["clip"] == "mover"


def test_write_queue_does_not_mark_aired(tmp_path):
    queue = empty_queue()
    place_comment_clip(_clip("p1"), queue, now=0, hist=[])
    path = write_queue(queue, tmp_path / "slots.json")
    saved = json.loads(path.read_text())
    held = next(slot for slot in saved["slots"] if slot.get("clip") == "p1")
    assert held["unaired"] is True
    assert held.get("aired") is not True
