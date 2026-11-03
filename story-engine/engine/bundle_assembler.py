#!/usr/bin/env python3
"""Full-density comment bundler/assembler (Director, Oct 29 2026, trundle-approved spec v2 11:35 AM CT).
Add-only companion to assemble_prompt.py (that file and its one-change path are untouched).
- Bundles comments per channel per 30-min window (MUTATION-SPEC-v2 s4).
- Every comment detail kept verbatim; conflicts are placed in a different beat or clip, or carried to
  the next window -- never dropped. Rule-breakers are bent (logged with both texts); only hard-limit
  hits that cannot be bent are held (never deleted).
- Prompt = trundle's JW skeleton verbatim (minus "Extend this video:"), full action block with comments
  woven into beats, canon carry-over layers with 100/50/25/0 fade + persistent after-effects (<=80 words),
  "Only weapon: X", one camera sentence, night/rain/wardrobe restated.
"""
import datetime, hashlib, json, re

SKELETON = ("Create a fight sequence in this setting. They will use weapons that are present in img. "
            "Fight sequence should be realistic and technical like a John Wick movie but more intense. ")
SKELETON_CAM_ORIG = ("Camera pov changes from this images perspective to a security feed, showing timestamp "
                     "and everything present on security camera recording.")
CAM_FIXED = ("The camera is a fixed security camera mounted high in the corner; it never moves, "
             "and the action plays out below it.")
WINDOW_MIN = 30
FADE = [1.0, 0.5, 0.25, 0.0]           # g+0..g+3
CANON_WORD_CAP = 80
LAYERS = ["global", "network", "channel", "show", "branch", "episode", "scene", "clip"]
COMMENT_LAYERS = {"branch", "episode", "scene", "clip"}   # comments may change 5-8 only
BEND = [(r"\b(should |will )?stab(s|bed|bing)? (him|her|them)( in the \w+)?", "pins \\3 sleeve with a blade that never touches skin, then lands a pommel strike"),
        (r"\b(blood|bleed(s|ing)?|gore|gory)\b", "a hard impact"),
        (r"\b(kill|kills|killed)\b", "drops (he stays down)"),
        (r"\blooks? (in|into|at) (the )?camera\b", "looks past the lens"),
        (r"\bwinks? (in|into|at) (the )?camera\b", "glances aside")]
HARD = [r"\b(kid|kids|child|children|toddler|minor)\b", r"\bKTVM\b"]
CATS = {"weapon": r"\b(extinguisher|knife|blade|gun|pistol|gauntlet|bat|chain|canister|weapon|pipe|crowbar|grenade|frost)\b",
        "weather": r"\b(rain|snow|fog|storm|sleet|ice storm|hail)\b",
        "fate": r"\b(loses|wins|dies|dead|escapes|captured)\b",
        "power": r"\b(summon|summons|power|teleport|fireball|kombat|tekken)\b"}

def sha(t): return hashlib.sha256(t.encode()).hexdigest()
def window_id(ts, ch):
    t = datetime.datetime.fromisoformat(ts)
    m = (t.minute // WINDOW_MIN) * WINDOW_MIN
    return f"ch{ch:02d}-{t:%Y%m%d}-{t.hour:02d}{m:02d}-w{WINDOW_MIN}"

def bend(text):
    for h in HARD:
        if re.search(h, text, re.I): return None, f"hard_limit:{h}"
    out = text
    for pat, rep in BEND: out = re.sub(pat, rep, out, flags=re.I)
    return out, None

def cats(text): return {c for c, p in CATS.items() if re.search(p, text, re.I)}

def fade_text(text, gen_age):
    f = FADE[min(gen_age, 3)]
    if f == 0: return ""
    words = text.split()
    n = max(3, round(len(words) * f)) if f < 1 else len(words)
    return " ".join(words[:n]) + ("..." if n < len(words) else "")

def bundle(comments, clips, channel):
    """Place every comment. clips: ordered list of clip dicts with 'beats'. Returns placements + carry."""
    by_win = {}
    for c in comments: by_win.setdefault(window_id(c["ts"], channel), []).append(c)
    placements, carry, held = [], [], []
    for wid in sorted(by_win):
        used = {}   # (clip_idx, beat_idx) -> set(categories)
        for c in sorted(by_win[wid], key=lambda c: (c.get("tier") != "paid", c["ts"])):
            text, err = bend(c["text"])
            if err:
                held.append({**c, "window_id": wid, "status": "HELD", "reason": err, "retention": "never_delete"}); continue
            cs = cats(text)
            start = next((i for i, k in enumerate(clips) if k["clip_id"] == c.get("target_clip")), 0)
            spot = None
            for ci in range(start, len(clips)):
                for bi in range(len(clips[ci]["beats"])):
                    if not (used.get((ci, bi), set()) & cs) or not cs:
                        spot = (ci, bi); break
                if spot: break
            row = {"prompt_id": c["prompt_id"], "window_id": wid, "tier": c.get("tier", "unpaid"),
                   "verbatim": c["text"], "verbatim_sha": sha(c["text"]), "woven_text": text,
                   "bent_from": c["text"] if text != c["text"] else None, "categories": sorted(cs)}
            if not spot:
                carry.append({**row, "status": "CARRY_NEXT_WINDOW", "priority_aging": "rises_with_wait"}); continue
            ci, bi = spot
            used.setdefault(spot, set()).update(cs)
            moved = ci != start or bi != 0
            row.update({"landed_in": {"clip_id": clips[ci]["clip_id"], "beat": bi},
                        "moved_for_conflict": moved,
                        "merged_with": [p["prompt_id"] for p in placements if p.get("landed_in", {}).get("clip_id") == clips[ci]["clip_id"] and p["window_id"] == wid]})
            placements.append(row)
    return placements, carry, held

def canon_block(canon):
    """canon: {layer: [facts]} for branch/episode/scene/clip, plus 'faded_comments':[{text,gen_age}], 'after_effects':[]"""
    lines = []
    for e in canon.get("after_effects", []): lines.append(e)          # never fade
    for lay in ["branch", "episode", "scene"]:
        lines += canon.get(lay, [])
    for fc in canon.get("faded_comments", []):
        t = fade_text(fc["text"], fc["gen_age"])
        if t: lines.append(f"(earlier viewer change) {t}")
    out, n = [], 0
    for l in lines:
        w = len(l.split())
        if n + w > CANON_WORD_CAP: out.append("[canon summarized: older facts kept in branch canon file]"); break
        out.append(l); n += w
    return " ".join(x.rstrip(".") + "." for x in out)

def assemble_clip(clip, placed, canon):
    beats = list(clip["beats"])
    for p in placed:
        b = p["landed_in"]["beat"]
        beats[b] = beats[b].rstrip(".") + "; " + p["woven_text"].rstrip(".")
    env = clip["env"]  # night/rain/wardrobe restated
    cam = CAM_FIXED if clip.get("mount", "").startswith("high fixed") else clip["camera"]
    action = (f"From the start frame, {'. Then '.join(b.rstrip('.') for b in beats)}, "
              f"ending on a steady held frame: {clip['end_state']}.")
    parts = [SKELETON + ("" if cam == CAM_FIXED else ""),
             env, action,
             ("Canon: " + canon_block(canon)) if canon else "",
             f"Only weapon: {clip['only_weapon']}.",
             cam,
             "Nobody looks into the camera. No blood, blades never touch skin. Parody brands only."]
    extra = sorted({m.group(0).lower() for p in placed for m in re.finditer(CATS["weapon"], p["woven_text"], re.I)}
                   - set(re.findall(r"[a-z-]+", clip["only_weapon"].lower())))
    if extra:  # comment-introduced gear joins the weapon line (still channel-arsenal names)
        parts[4] = f"Only weapon: {clip['only_weapon']}, plus viewer-added: {', '.join(extra)}."
    prompt = re.sub(r"\s+", " ", " ".join(x for x in parts if x))
    return {"clip_id": clip["clip_id"], "prompt": prompt, "prompt_sha": sha(prompt),
            "prompt_ids": [p["prompt_id"] for p in placed], "words": len(prompt.split())}

def assemble_bundle(clips, comments, canon_by_clip=None, channel=4):
    placements, carry, held = bundle(comments, clips, channel)
    out = []
    for k in clips:
        mine = [p for p in placements if p["landed_in"]["clip_id"] == k["clip_id"]]
        out.append(assemble_clip(k, mine, (canon_by_clip or {}).get(k["clip_id"], {})))
    return {"clips": out, "placements": placements, "carry_next_window": carry, "held": held,
            "dropped": [], "window_min": WINDOW_MIN, "fade": FADE, "canon_word_cap": CANON_WORD_CAP}
