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
def tier_alive(c,episode,season,clip_index):
    t=c.get("tier","FLASH")
    if t=="FLASH": return clip_index-c.get("since_index",clip_index)<1
    if t=="SCAR": return c.get("episode",episode)==episode
    if t=="MARK": return c.get("season",season)==season
    return True
def carry_text(c,clip_index):
    """decay: no still -> full clause; still present -> 3-word key, then nothing after DECAY_CLIPS clips with a still"""
    if not c.get("still"): return c["text"]
    age=clip_index-c.get("still_since_index",clip_index)
    if age>=DECAY_CLIPS: return None
    return " ".join(c.get("short",c["text"]).split()[:3])
