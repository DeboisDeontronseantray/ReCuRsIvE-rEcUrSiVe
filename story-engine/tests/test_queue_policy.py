# Offline sim of comment_prompt_slots rules. No ErsatzTV, no network.
# Delegates to the live queue writer so the policy is not reimplemented here.
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "engine"))
from queue_writer import empty_queue, load_policy, place_comment_clip, record_slot_miss

P = load_policy()
M = P["render_lead_time"]["margin_min"]
D = P["render_lead_time"]["render_eta_default_min"]
W = P["max_wait_breaks"]
MISS = P["slot_miss_limit"]
AIR = P["placement"]["owner_air_yes_key"]


def _clip(cid, **extra):
    row = {"id": cid, "moves": 0, "misses": 0, AIR: True}
    row.update(extra)
    return row


def run():
    L = []
    slots = empty_queue()
    assert place_comment_clip(_clip("p1"), slots, now=0, hist=[]) == "s5"          # 15+10=25 -> slot 5
    assert place_comment_clip(_clip("p2"), slots, now=0, hist=[]) == "s6"          # slot5 protected -> next
    assert place_comment_clip(_clip("p3"), slots, now=0, hist=[10, 12, 30]) == "s8"  # p90=30 ->40
    assert place_comment_clip(_clip("bad", flags=["kids"]), slots, now=0, hist=[]) is None
    assert (None, None, "bad", "reject_hard_limit") in slots["lineage"]
    late = _clip("late")
    assert place_comment_clip(late, slots, now=0, hist=[]) == "s7"
    assert record_slot_miss(late, slots, now=0) == "s7"
    assert record_slot_miss(late, slots, now=0) == "s7"
    assert record_slot_miss(late, slots, now=0) == "s9"  # s8 holds unaired p3
    assert all(len(r) == 4 for r in slots["lineage"])
    assert W == 3 and MISS == 3 and P["render_not_ready_at_slot_start"]["play"] == "scheduled_clip"
    L.extend(slots["lineage"])
    print("queue-policy writer tests OK; lineage rows:", len(L))


if __name__ == "__main__":
    run()
