#!/usr/bin/env python3
"""Layer model v4 (trundle t368u correction): META IS FLUID BY DEFAULT.
Every layer has a persistence kind:
  durable    - hardlines, eyeline rule, fixed threads (config/fixed_threads.json), card fixed parts, look lock (episode-boundary swap only)
  tier       - consequences/gifts/world rules carried while their tier lives (FLASH 1 clip, SCAR episode, MARK season, LEGEND permanent),
               decaying: once a state still carries the trait, text shrinks to <=3 words, then drops after DECAY_CLIPS clips with a still
  clip       - headline, beats, comments, camera move, gags, news comedy device (this clip only)
  triggered  - chaos resolver / steering / style re-lock / re-description: fire only when a detector says so
Fluid mechanics (seeded, reproducible): phrasing pools per layer, word-order permutation of the movable block, conditional inclusion.
Only FIXED THREADS keep their MEANING invariant (phrasing may still vary)."""
import random,hashlib,json,os
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIER_LIFE={"FLASH":1,"SCAR":"episode","MARK":"season","LEGEND":"permanent"}
DECAY_CLIPS=3
def rng(clip_id,meta_version,salt=""):
    return random.Random(int(hashlib.sha256(f"{clip_id}|{meta_version}|{salt}".encode()).hexdigest()[:12],16))
POOLS={
 "end":["Motion carries on through the last half second.","Motion carries on through the last half second, nothing freezes.","Everyone keeps moving; motion carries on through the last half second."],
 "seam":["Continue from <IMAGE_0>, same positions and light, mid-motion.","Pick up from <IMAGE_0> mid-movement, same positions, same light.","Start exactly where <IMAGE_0> leaves off, same light, already moving."],
 "eyeline":["Eyelines: {who} {verb} {target}; faces in profile or three-quarter.","{who} {verb} {target}, profile or three-quarter to us.","Faces stay profile or three-quarter; {who} {verb} {target}."],
 "arc":["Story beat ({stage}): {goal}.","This clip's story beat is {stage} - {goal}.","({stage}) {goal}."],
 "want":["{name} wants {want}.","{name}'s want: {want}."],
 "goal":["Show goal: {goal}.","Everything here serves one goal: {goal}."],
 "carry":["Still visible: {items}.","Carried over: {items}.","{items} stay as before."],
 "resolver":["Story pull: {push}.","Underneath it all, {push}."],
}
# SUPERSEDED (v4 only; not used by v4.1/v4.2): this pool's "no blood on skin", "No on-screen text", "Theatrical props" wording is replaced by build_prompt_v41.rules_bracket (CURRENT-RULES v48 L497). Kept for regen compatibility.
SAFETY_POOL=["[Adults only. Original invented characters, no real people or lookalikes; parody brands only. Nobody looks into the camera. No gore, no blood on skin; stains on clothing only. No on-screen text, no logos. Theatrical props only. One continuous {d} s take.]",
 "[Adults only; original invented characters, no lookalikes; parody brands. Nobody looks into the camera. Stage-combat hits land on coats and props; no wounds or blood on skin, stains on clothing only. No on-screen text or logos. Theatrical props. One continuous {d} s take.]"]
def fixed_threads():
    return json.load(open(f"{H}/config/fixed_threads.json"))
def tier_alive(c,episode,season,clip_index, *, lifecycle=None, channel=None):
    """Read consequence lifetime through the canonical clock and pure predicate."""
    from astra_lifecycle.characters import alive
    from astra_lifecycle.repo import lifecycle_store
    life = lifecycle_store(lifecycle, required=False)
    if life is not None:
        state = life.snapshot()
        stored = state["consequences"].get(c.get("id"))
        if stored is None or not stored["active"]:
            return False
        clock = state["clocks"].get(channel or stored["channel"])
        if clock is None:
            return False
        return alive(stored, clock["index"], clock["episode"], clock["season"])
    # Pure formatting callers may preview lifetime. This does not advance a
    # clock or persist a tier; all actual changes use D16/propose below.
    preview = dict(c)
    preview.setdefault("since_index", clip_index)
    preview.setdefault("episode", episode)
    preview.setdefault("season", season)
    return alive(preview, clip_index, episode, season)


def carry_text(c,clip_index, *, lifecycle=None):
    """Read canonical carry text, or preview wording without persisting it."""
    from astra_lifecycle.repo import lifecycle_store
    life = lifecycle_store(lifecycle, required=False)
    if life is None:
        # Read-only wording preview; accepted still persistence uses D17.
        if not c.get("still"):
            return c["text"]
        if clip_index - c.get("still_since_index", clip_index) >= DECAY_CLIPS:
            return None
        return " ".join(c.get("short", c["text"]).split()[:3])
    stored = life.snapshot()["consequences"].get(c.get("id"))
    return stored["text"] if stored and tier_alive(stored, 0, 0, 0, lifecycle=life) else None


def propose_consequences(clip_id, *, lifecycle=None, consequences=None, reuses=None, proposals=None):
    from astra_lifecycle.repo import propose_changes
    return propose_changes("D16", clip_id, lifecycle=lifecycle,
                           consequences=consequences, reuses=reuses, proposals=proposals)


def propose_still(clip_id, *, lifecycle=None, proposals=None, consequences=None, reuses=None):
    from astra_lifecycle.repo import propose_changes
    return propose_changes("D17", clip_id, lifecycle=lifecycle,
                           proposals=proposals, consequences=consequences, reuses=reuses)
