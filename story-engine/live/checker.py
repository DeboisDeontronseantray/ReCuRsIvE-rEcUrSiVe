"""Hybrid continuity checker: humans write the soul, this checks it against bible-v2.
Usage: python live/checker.py <clip-prompts.json> [bible.yaml]   (local only, no API calls)"""
import json, re, sys, yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import legacy_names
ROOT = Path(__file__).resolve().parents[1]
BIBLE = ROOT / "continuity/ch04-military-boutique/bible-v2.yaml"
CONT = ROOT / "data/continuity/forward-supply.json"
CAST_NAMES = {"Osmund": "osmund", "Tim": "tim", "Lt. Mira S'mirin'": "mira_smirin", "Mira": "mira_smirin",
              "Commander Bill D'bears": "bill_dbears", "Bill": "bill_dbears"}
CAST_KEYS = {"osmund": ["olive coveralls", "buzz cut"], "mira_smirin": ["braid", "clipboard"],
             "bill_dbears": ["muscular", "name tag"], "tim": ["glass dome", "cyan optic"]}
REAL_BRANDS = ["american hostage", "lockheed", "raytheon", "boeing", "northrop", "general dynamics", "colt", "glock",
    "sig sauer", "remington", "smith & wesson", "beretta", "oakley", "nike", "adidas", "apple", "iphone", "samsung",
    "google", "amazon", "coca-cola", "coke", "pepsi", "red bull", "monster energy", "juul", "vuse", "elf bar",
    "marlboro", "playstation", "xbox", "nintendo", "call of duty", "fortnite", "halo", "minecraft", "tesla",
    "walmart", "target", "mcdonald", "starbucks", "disney", "marvel", "youtube", "tiktok", "kalshi"]
UNSAFE = [r"\bkill(ed|ing)?\b", r"\bgore\b", r"\bblood(y)?\b", r"\btorture\b", r"\bnude|naked|sex(ual)?\b",
    r"\bhow to (make|build) (a )?(bomb|explosive|gun)\b", r"\bbomb\b", r"\bsuicide\b", r"\bslur\b",
    r"\bvap(e|ing|or)\s+(cloud|smoke|puff)|\bsmok(e|ing) (the|a|his) vape|\bpuff(s|ing)? on\b",
    r"\bcall (now|1-?800)|\bdial\b|\bphone number\b", r"\bslapstick|pratfall|pie in the face\b"]

def load_bible(path=BIBLE):
    return yaml.safe_load(open(path))

def registry(b):
    return {p["name"].lower() for p in b["product_registry"]["products"] if p.get("name")}

NEG = re.compile(r"\b(no|never|not|without|avoid|zero)\b[^.;:\n\"]*", re.I)

def strip_negated(text):
    """Drop 'no gore, never slapstick' style guard phrases so they don't trip the scan."""
    return NEG.sub(" ", text)

def brand_hits(text):
    t = text.lower()
    return [w for w in REAL_BRANDS if re.search(r"\b" + re.escape(w) + r"\b", t)]

def unsafe_hits(text):
    return [p for p in UNSAFE if re.search(p, text, re.I)]

MONEY = re.compile(r"(\$|[£€¥]|\b\d[\d,.]*\s*(usd|dollars?|bucks|cents?)\b|\bdonat\w*|\btip(s|ping|ped)?\b|\bpa(y|ys|id|ying|yment)\b|\bmoney\b|\bfund\w*|\bsupport (us|the (channel|show|stream))\b|\bgive (us|back)\b|\bsponsor\w*|\bcash\b|\bsuper ?chat\b|\bpatreon\b|\bvenmo\b|\bcrowdfund\w*|\bchip in\b)", re.I)
def money_hits(text):
    return [m.group(0) for m in MONEY.finditer(text or "")]

CAM = re.compile(r"(\blooks? (straight |directly )?(at|into) (the )?(camera|lens)\b|\blooking (straight |directly )?(at|into) (the )?(camera|lens)\b|\bto[- ]camera\b|\b(address|talk|speak)\w* (to )?(the )?(viewers?|audience|camera|us)\b|\btalks? to us\b|\bbreaks? the fourth wall\b|\beyes? (on|to) (the )?(camera|lens)\b|\bstares? (out )?(at|into) (the )?(camera|lens|us)\b)", re.I)
def camera_hits(text):
    text = re.sub(r"\bCAMERA\s*:", ". Shot:", text or "")   # prompt section labels are not wording
    return [m.group(0) for m in CAM.finditer(strip_negated(text))]

# ---- clean-source guard (trundle 2026-10-27): mutations never inherit on-screen text ----
MB_DIR = Path("out-of-scope/fakenews/channel-ready/thunder-trundle/4_Military-Boutique")
LINEAGE = MB_DIR / "LINEAGE.jsonl"
TAINT = re.compile(r"lineage-tagged|ch4badge|salesad|sales-overlay|_tagged", re.I)
RAW_SHORT = {"armored-showroom-cruiser": "rover", "exo-gauntlet-vitrine": "gauntlet", "modular-field-pack": "pack",
             "scout-drone-jewelry": "drone", "tactical-helmet-pedestal": "helmet", "field-binoculars-velvet": "binoculars",
             "graphite-cloak-torso": "cloak"}

class CleanSourceError(ValueError):
    pass

def is_tainted(path):
    return bool(TAINT.search(str(path or "")))

def _norm(p):
    return str(p).replace("/4_Military-Boutique/", "/4_1_Military-Boutique/")

def load_lineage(path=None):
    p = Path(path or LINEAGE)
    if not p.is_file(): return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return [r for r in rows if r.get("row_type") != "correction"]   # CNB correction rows carry no file

# ---- shared watchlist (trundle 2026-10-27 17:13: rare slips OK if caught and filtered next time) ----
# CNB is the ONLY writer of WATCHLIST. Story Bot only reads it, re-reading on every check. Missing -> built-in TAINT only.
WATCHLIST = Path("out-of-scope/shared/streaming/tag-slip-watchlist.jsonl")
PHASH_MAX_DIST = 6
_sha_cache, _phash_cache = {}, {}

def load_watchlist(path=None):
    p = Path(path or WATCHLIST)
    if not p.is_file(): return []
    out = []
    for l in p.read_text().splitlines():
        try: out.append(json.loads(l)) if l.strip() else None
        except ValueError: pass
    return out

def file_sha256(path):
    import hashlib, os
    p = Path(path)
    if not p.is_file(): return None
    k = (str(p), os.path.getmtime(p), os.path.getsize(p))
    if k not in _sha_cache:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
        _sha_cache[k] = h.hexdigest()
    return _sha_cache[k]

def file_phash(path):
    """64-bit dHash (hex) of the middle frame (video) or the image itself, via ffmpeg. None if unavailable."""
    import subprocess, os
    p = Path(path)
    if not p.is_file(): return None
    k = (str(p), os.path.getmtime(p))
    if k in _phash_cache: return _phash_cache[k]
    try:
        pre = []
        if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv"):
            d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                               capture_output=True, text=True, timeout=20).stdout.strip()
            pre = ["-ss", str(max(float(d or 0) / 2, 0))]
        raw = subprocess.run(["ffmpeg", "-v", "error", *pre, "-i", str(p), "-frames:v", "1", "-vf", "scale=9:8,format=gray",
                              "-f", "rawvideo", "-"], capture_output=True, timeout=30).stdout
        if len(raw) < 72: h = None
        else:
            bits = "".join("1" if raw[r * 9 + c] > raw[r * 9 + c + 1] else "0" for r in range(8) for c in range(8))
            h = f"{int(bits, 2):016x}"
    except Exception: h = None
    _phash_cache[k] = h
    return h

def _hamming(a, b):
    try: return bin(int(a, 16) ^ int(b, 16)).count("1")
    except (TypeError, ValueError): return 99

def watchlist_hit(path, watchlist=None):
    """Return the matching watchlist row (re-read every call) or None. Matches sha256, name_pattern, regex, phash."""
    import fnmatch
    rows = load_watchlist() if watchlist is None else watchlist
    if not rows or not path: return None
    sp, name = str(path), Path(str(path)).name
    sha = None; ph = None
    allow = [r for r in rows if r.get("row_type") == "clean_master_allow"]
    if allow:   # exact-sha allow beats any name/phash deny (CNB 2026-10-27)
        sha = file_sha256(sp)
        if sha and any(r.get("sha256") == sha for r in allow): return None
    rows = [r for r in rows if r.get("row_type") != "clean_master_allow"]
    for r in rows:
        np_ = r.get("name_pattern")
        if np_:
            if any(ch in np_ for ch in "*?[") and (fnmatch.fnmatch(name, np_) or fnmatch.fnmatch(sp, np_)): return r
            if np_ in sp: return r
            try:
                if re.search(np_, sp, re.I): return r
            except re.error: pass
        if r.get("regex"):
            try:
                if re.search(r["regex"], sp, re.I): return r
            except re.error: pass
        if r.get("sha256"):
            sha = sha or file_sha256(sp)
            if sha and sha == r["sha256"]: return r
    for r in rows:
        if r.get("phash"):
            ph = ph or file_phash(sp)
            if ph and _hamming(ph, r["phash"]) <= PHASH_MAX_DIST: return r
    return None

NON_NODE_ROWS = {"pulled", "unpull", "correction", "clean_master_allow", "duplicate_premise"}

def resolve_clean(path, lineage=None, mb_dir=None):
    """Return a clean (no burned text) source for path, or raise CleanSourceError.
    LINEAGE rows only store the output 'file'; walk parent_id (tag or global_no) to the gen-1 root,
    then use CNB's clean masters: masters/<global_no>_<slug>_master_parody.mp4, else raw/mb_<short>.mp4.
    Catalog (ch4-ad-*) first renders carry the burned band/badge, so they also resolve to the master."""
    w = watchlist_hit(path)
    if w: raise CleanSourceError(f"watchlisted source ({w.get('reason', 'watchlist')}): {path}")
    mb = Path(mb_dir or MB_DIR); rows = load_lineage(mb / "LINEAGE.jsonl") if lineage is None else lineage
    ap = [r for r in rows if r.get("row_type") == "audio_post"]   # leveled copies: never walked as lineage nodes
    rows = [r for r in rows if r.get("row_type") != "audio_post"]
    # status/annotation rows (pulled, unpull, correction, ...) reuse a node's file/global_no but are not lineage nodes;
    # letting them into by_file/by_no shadowed the real row (18:15 pull broke cruiser -> raw/mb_rover). Skip them.
    rows = [r for r in rows if r.get("clip_id") and r.get("row_type") not in NON_NODE_ROWS]
    by_file = {_norm(r["file"]): r for r in rows if r.get("file")}
    row = by_file.get(_norm(path))
    if row is None:   # audio_post output -> resolve as its source clip (same picture, leveled audio)
        a = next((r for r in ap if r.get("file") and _norm(r["file"]) == _norm(path)), None)
        if a:
            row = next((r for r in rows if a.get("source_sha256") and r.get("sha256") == a["source_sha256"]), None) or \
                  next((r for r in rows if a.get("source_global_no") is not None and r.get("global_no") == a["source_global_no"]), None)
            if row is None: raise CleanSourceError(f"audio_post copy with no matching source row: {path}")
    if row is None:
        if is_tainted(path): raise CleanSourceError(f"tainted path (overlay/tag/badge copy) with no LINEAGE row: {path}")
        return str(path)
    by_tag = {r["tag"]: r for r in rows if r.get("tag")}; by_no = {r["global_no"]: r for r in rows if r.get("global_no") is not None}; seen = set()   # render_provenance rows may lack tag/global_no
    while row.get("parent_id") is not None or row.get("parent_global_no") is not None:
        key = row.get("global_no", row.get("clip_id"))
        if key in seen: raise CleanSourceError(f"LINEAGE loop at {row.get('tag', key)}")
        seen.add(key)
        par = by_tag.get(row.get("parent_id")) or by_no.get(row.get("parent_global_no")) or by_no.get(row.get("parent_id"))
        if par is None: raise CleanSourceError(f"LINEAGE parent missing for {row['tag']} ({path})")
        row = par
    cid = row["clip_id"]
    if not cid.startswith("ch4-ad-") and not is_tainted(row["file"]) and Path(row["file"]).is_file():
        return _not_watchlisted(row["file"])
    slug = cid.removeprefix("ch4-ad-")
    for c in (mb / "masters" / f"{row['global_no']}_{slug}_master_parody.mp4", mb / "raw" / f"mb_{RAW_SHORT.get(slug, slug)}.mp4"):
        if c.is_file(): return _not_watchlisted(str(c))
    raise CleanSourceError(f"no clean master for {cid} (root {row['tag']}); refusing burned-text source {path}")

def _not_watchlisted(p):
    w = watchlist_hit(p)
    if w: raise CleanSourceError(f"clean master is watchlisted ({w.get('reason', 'watchlist')}): {p}")
    return p

def clean_source_fails(s):
    out = []
    for p in list(s.get("reference_images") or []) + ([s["end_frame_source"]] if s.get("end_frame_source") else []):
        if is_tainted(p): out.append(f"clean-source: on-screen-text copy used as source: {p}")
        else:
            try:
                r = resolve_clean(p)
                if _norm(r) != _norm(p): out.append(f"clean-source: {p} has burned text; use clean master {r}")
            except CleanSourceError as e: out.append(f"clean-source: {e}")
    return out

# ---- audio leveling gate (trundle 2026-10-27 17:33 hum note): a clip is not finished until audio_leveled is true ----
def _audio_posts(lineage=None):
    rows = load_lineage() if lineage is None else lineage
    return [r for r in rows if r.get("row_type") == "audio_post" and r.get("audio_leveled") is True]

def audio_finished(rec, lineage=None):
    """Return (finished, warning). Finished if audio_leveled is true, the clip is itself an audio_post output, or a CNB
    audio_post row levels it (join: source_sha256, backup source_global_no). Missing field -> not finished + warning."""
    rec = rec or {}
    v = rec.get("audio_leveled")
    if v is True: return True, None
    aps = _audio_posts(lineage)
    if aps:
        f = rec.get("file") or rec.get("mp4")
        sha = rec.get("sha256") or (file_sha256(f) if f and Path(str(f)).is_file() else None)
        gno = rec.get("global_no")
        for a in aps:
            if sha and sha in (a.get("source_sha256"), a.get("out_sha256")): return True, None
            if f and a.get("file") and _norm(f) == _norm(a["file"]): return True, None
            if gno is not None and a.get("source_global_no") == gno and not a.get("source_sha256"): return True, None
            if gno is not None and a.get("source_global_no") == gno and not sha: return True, None
    name = (rec or {}).get("clip_id") or (rec or {}).get("id") or "clip"
    if v is None: return False, f"audio_leveled missing on {name}: not finished until audio is leveled"
    return False, f"audio_leveled={v!r} on {name}: not finished until audio is leveled"

# ---- no creator name on screen (trundle hard rule 2026-10-27 17:43 CT) ----
CREATOR_NAME = legacy_names.LEGACY_OWNER
CREATOR = re.compile(rf"\b{re.escape(CREATOR_NAME)}\b", re.I)
SCREEN_FIELDS = ("visual_prompt", "action", "background_business", "location", "lighting_fog", "camera", "props_products", "match",
                 "on_screen_text", "on_screen_text_post", "post_insert", "overlay", "overlay_text", "caption", "captions", "super",
                 "supers", "subtitle", "drawtext", "text", "prompt", "tagline", "vo_lines", "dialogue", "flair")
NAME_NEGATIVES = ["no names", "no signatures", "no watermarks"]
def _strings(v):
    if isinstance(v, str): yield v
    elif isinstance(v, dict):
        for x in v.values(): yield from _strings(x)
    elif isinstance(v, (list, tuple)):
        for x in v: yield from _strings(x)
def creator_name_hits(obj, fields=SCREEN_FIELDS):
    """CREATOR_NAME (whole word, any case) in anything that can reach the screen. Notes/status/approval fields are not scanned."""
    vals = [obj] if isinstance(obj, str) else [obj.get(k) for k in fields if isinstance(obj, dict) and k in obj]
    return [m.group(0) for v in vals for s in _strings(v) for m in CREATOR.finditer(s)]

# ---- no kids + no "Military Boutique" burned text (trundle hard rules 2026-10-27 17:44 CT) ----
KIDS = re.compile(r"\b(kids?|child(ren)?|toddlers?|bab(y|ies))\b", re.I)
def kid_hits(obj, fields=SCREEN_FIELDS):
    """kid words in prompt/overlay/spoken text. Negated phrases ('no children, no kids') are ignored."""
    vals = [obj] if isinstance(obj, str) else [obj.get(k) for k in fields if isinstance(obj, dict) and k in obj]
    return [m.group(0) for v in vals for s in _strings(v) for m in KIDS.finditer(strip_negated(s))]
MB = re.compile(r"military\s*boutique", re.I)
BURN_FIELDS = ("on_screen_text", "on_screen_text_post", "post_insert", "overlay", "overlay_text", "caption", "captions",
               "super", "supers", "subtitle", "drawtext", "burned_text", "tagline")
def mb_text_hits(obj, fields=BURN_FIELDS):
    """'Military Boutique' as visible clip text. Channel-name metadata (channel, channel_name, header, visual_prompt) is not scanned."""
    vals = [obj] if isinstance(obj, str) else [obj.get(k) for k in fields if isinstance(obj, dict) and k in obj]
    return [m.group(0) for v in vals for s in _strings(v) for m in MB.finditer(s)]
KID_NEGATIVES = ["no children", "no kids"]
CREATOR_NEGATIVES = ["no on-screen names", f"no text reading {CREATOR_NAME.capitalize()}"]

def check_shot(s, b, reg, cont):
    fails, warns = [], []
    blob = json.dumps(s, ensure_ascii=False)
    # strip negative prompt before scanning (it legitimately names banned things)
    scan = strip_negated(json.dumps({k: v for k, v in s.items() if k not in ("negative_prompt",)}, ensure_ascii=False).replace("\\n", " "))
    for c in s.get("cast", []):
        key = CAST_NAMES.get(c)
        if not key:
            fails.append(f"unknown cast '{c}'")
        elif s.get("visual_prompt") and not all(k in s["visual_prompt"].lower() for k in CAST_KEYS[key]):
            warns.append(f"{c}: locked look cues {CAST_KEYS[key]} missing from visual_prompt")
    for p in s.get("props_products", []):
        name = p.split(":")[0].strip()
        if name.lower() not in reg and not name.lower().startswith(("prop", "mira's", "bill's", "osmund's", "tim's")):
            warns.append(f"product '{name}' not in product_registry (add DRAFT or treat as prop)")
    for h in brand_hits(scan):
        fails.append(f"real brand / banned name: {h}")
    for h in unsafe_hits(scan):
        fails.append(f"TV-safe rule hit: {h}")
    loc = (s.get("location") or "").lower()
    if loc and not any(w in loc for w in ("outpost", "mess hall", "command hut", "supply bay", "bunk", "hatch", "showroom", "depot")):
        warns.append("location not one of bible-v2 locations")
    visual = strip_negated(" ".join(str(s.get(k, "")) for k in ("visual_prompt", "action", "location", "lighting_fog")))
    if re.search(r"fog (lifts|clears|burns off|is gone)|clear (blue )?sky|sunrise visible", visual, re.I):
        fails.append("continuity: fog never lifts at Outpost Quiet (visuals)")
    if True:
        for d in s.get("dialogue", []):
            if d.get("speaker") == "Tim" and not re.search(r"chirp", d.get("line", ""), re.I):
                fails.append("continuity: Tim speaks in chirps only")
    for d in s.get("dialogue", []):
        for h in money_hits(d.get("line", "")):
            fails.append(f"no money asks in spoken lines: '{h}'")
    fails += clean_source_fails(s)
    for h in creator_name_hits(s):
        fails.append(f"no_creator_name_on_screen: '{h}' in on-screen/prompt text")
    for h in kid_hits(s):
        fails.append(f"no_kids: '{h}' in prompt/overlay/spoken text")
    for h in mb_text_hits(s):
        fails.append(f"mb_text: '{h}' as visible clip text (older-version branding)")
    cam_scan = " ".join(str(s.get(k, "")) for k in ("visual_prompt", "action", "camera")) + " " + " ".join(d.get("line", "") for d in s.get("dialogue", []))
    for h in camera_hits(cam_scan):
        fails.append(f"observational rule: direct-to-camera wording '{h}'")
    if str(s.get("id", "")).startswith("LIVE-"):   # live commenter clips must carry real refs
        ri = s.get("reference_images")
        if not isinstance(ri, list) or not ri: fails.append("reference_images: none found (live clips need real stills)")
        else:
            bad = [p for p in ri if not Path(str(p)).is_file()]
            if bad: fails.append(f"reference_images missing on disk: {bad}")
            if len(ri) > 14: fails.append("reference_images over 14")
    if s.get("queued_for_render") or s.get("file") or s.get("mp4"):   # a render being queued / finished clip
        done, w = audio_finished(s)
        if not done: warns.append(w)
    if not s.get("continues_from"):
        warns.append("no continues_from (linked-shot rule)")
    status = "fail" if fails else "warn" if warns else "pass"
    return {"id": s.get("id"), "status": status, "fails": fails, "warns": warns}

def check_file(path, bible_path=BIBLE):
    b = load_bible(bible_path); reg = registry(b)
    cont = json.load(open(CONT)) if CONT.exists() else {}
    d = json.load(open(path))
    shots = d.get("shots") or d.get("clips") or []
    res = [check_shot(s, b, reg, cont) for s in shots]
    overall = "fail" if any(r["status"] == "fail" for r in res) else "warn" if any(r["status"] == "warn" for r in res) else "pass"
    return {"file": str(path), "overall": overall, "counts": {k: sum(r["status"] == k for r in res) for k in ("pass", "warn", "fail")}, "shots": res}

if __name__ == "__main__":
    r = check_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else BIBLE)
    print(json.dumps(r, indent=1, ensure_ascii=False))
    sys.exit(1 if r["overall"] == "fail" else 0)


# --- Preemption (trundle 2026-10-27 18:01 CT): slots point to a lineage head; never delete ---
COMMENT_PROMPTS = Path('out-of-scope/streaming/queues/COMMENT-PROMPTS.jsonl')

def add_comment_prompt(text, handle=None, path=None):
    """Append-only; returns permanent cp- id."""
    import hashlib, datetime
    p = Path(path or COMMENT_PROMPTS); p.parent.mkdir(parents=True, exist_ok=True)
    pid = 'cp-' + hashlib.sha256(f"{handle}|{text}".encode()).hexdigest()[:12]
    rows = [json.loads(l) for l in p.open()] if p.exists() else []
    if not any(r['id'] == pid for r in rows):
        with p.open('a') as f: f.write(json.dumps({'id': pid, 'handle': handle, 'text': text, 'date': datetime.datetime.now().astimezone().isoformat()}) + '\n')
    return pid

def slot_head(slot, versions):
    """Newest READY+APPROVED version at or below the slot's head pointer."""
    by = {v['global_no']: v for v in versions if v.get('lineage') == slot['lineage']}
    no = slot['head']
    while no is not None:
        v = by.get(no)
        if v and v.get('ready') and v.get('approved'): return v
        no = v.get('parent_global_no') if v else None
    return None

def new_version(parent, global_no, slot_id, own_prompt_ids=()):
    return {'lineage': parent['lineage'], 'gen': parent['gen'] + 1, 'global_no': global_no,
            'parent_global_no': parent['global_no'], 'supersedes': parent['global_no'], 'slot_id': slot_id,
            'prompt_ids': list(parent.get('prompt_ids', [])) + [p for p in own_prompt_ids if p not in parent.get('prompt_ids', [])],
            'ready': False, 'approved': False, 'status': 'candidate'}

def approve(slot, versions, new, when):
    """Move head to new; mark old superseded (kept)."""
    import copy
    new.update(ready=True, approved=True, status='head')
    for v in versions:
        if v['global_no'] == new['supersedes']: v.update(status='superseded', superseded_by=new['global_no'], superseded_at=when)
    if new not in versions: versions.append(new)
    slot.setdefault('head_history', []).append(slot['head']); slot['head'] = new['global_no']
    return slot

def rollback(slot, versions):
    if not slot.get('head_history'): return slot
    slot['head'] = slot['head_history'].pop()
    return slot

def preemption_fails(slot, versions, prompts_path=None):
    """Checks: no version deleted, prompt ids inherited, every prompt id exists, same anchors per slot."""
    errs = []
    p = Path(prompts_path or COMMENT_PROMPTS)
    known = {json.loads(l)['id'] for l in p.open()} if p.exists() else set()
    by = {v['global_no']: v for v in versions}
    for v in versions:
        par = by.get(v.get('parent_global_no'))
        if par and not set(par.get('prompt_ids', [])) <= set(v.get('prompt_ids', [])): errs.append(f"#{v['global_no']} dropped parent prompt_ids")
        for pid in v.get('prompt_ids', []):
            if pid not in known: errs.append(f"#{v['global_no']} unknown prompt id {pid}")
        if v.get('slot_id') and v['slot_id'] == slot.get('slot_id') and v.get('anchors') and slot.get('anchors') and v['anchors'] != slot['anchors']:
            errs.append(f"#{v['global_no']} anchors differ from slot")
        if v.get('supersedes') is not None and v['supersedes'] not in by: errs.append(f"#{v['global_no']} superseded version missing (never delete)")
    return errs


# --- Prompt queue + duplicates (trundle 2026-10-27 18:05 CT); add-only state rows ---
PROMPT_STATES = ('waiting', 'combined', 'aired', 'held')
MAX_WAIT_LOOPS = 3  # configurable

def prompt_state(pid, rows):
    """Latest state from add-only rows [{id, state, ...}]; prompts never deleted."""
    st = None
    for r in rows:
        if r.get('id') == pid and r.get('state') in PROMPT_STATES: st = r['state']
    return st or 'waiting'

def set_state(rows, pid, state, **kw):
    assert state in PROMPT_STATES
    rows.append(dict(id=pid, state=state, **kw)); return rows

def priority(p, loops_waited, max_wait=MAX_WAIT_LOOPS):
    """Higher sorts first. Max-wait prompts outrank everything new."""
    return (1 if loops_waited >= max_wait else 0, loops_waited, -p.get('seq', 0))

def next_for_break(prompts, waits, rows, max_wait=MAX_WAIT_LOOPS):
    cand = [p for p in prompts if prompt_state(p['id'], rows) == 'waiting']
    return max(cand, key=lambda p: priority(p, waits.get(p['id'], 0), max_wait)) if cand else None

def fingerprint(p):
    kw = sorted({w for w in re.findall(r'[a-z]{4,}', (p.get('premise') or p.get('text', '')).lower())})
    return (p.get('show', ''), tuple(kw))

def similarity(a, b):
    fa, fb = fingerprint(a), fingerprint(b)
    if fa[0] != fb[0]: return 0.0
    A, B = set(fa[1]), set(fb[1]); return len(A & B) / max(1, len(A | B))

def combine(prompts, rows, clip_id):
    """Merge fitting prompts (same show and character/premise overlap) into one clip; all count as used."""
    ids = [p['id'] for p in prompts]
    for pid in ids: set_state(rows, pid, 'combined', clip_id=clip_id)
    return {'clip_id': clip_id, 'prompt_ids': ids}

def hold_prompt(rows, pid, reason, rewrite=None):
    set_state(rows, pid, 'held', reason=reason, rewrite=rewrite); return rows

def classify_duplicate(new, existing, same=0.8, spin=0.3):
    """Near-dupes become siblings: rotate (same idea), next_take (episode/callback), spinoff (new lineage, link back)."""
    s = similarity(new, existing)
    if s >= same: return 'rotate'
    if s >= spin: return 'next_take'
    return 'spinoff'

def register_clip(library, clip):
    """Exact copies (sha or phash) air once; extra copies kept as linked duplicates, never dropped."""
    for c in library:
        if (clip.get('sha256') and c.get('sha256') == clip['sha256']) or (clip.get('phash') and c.get('phash') == clip['phash']):
            clip.update(duplicate_of=c.get('clip_id'), airable=False); library.append(clip); return clip
    clip.setdefault('airable', True); library.append(clip); return clip


# --- 18:09 CT unified prompt states (CLIP-PROMOTION-PROCESS-20261027.md); supersedes 18:05 names ---
OPEN_STATES = ('WAITING', 'PARKED')
TERMINAL_STATES = ('AIRED', 'MERGED', 'WITHDRAWN')  # WITHDRAWN = trundle only
STATE_ALIASES = {'waiting': 'WAITING', 'combined': 'MERGED', 'held': 'PARKED', 'aired': 'AIRED', 'parked': 'PARKED', 'merged': 'MERGED', 'withdrawn': 'WITHDRAWN'}
PROMPT_STATES = OPEN_STATES + TERMINAL_STATES
SKIPPED_BREAKS_CAP = 3  # configurable

def canon_state(s):
    return STATE_ALIASES.get(s, s) if s else s

def prompt_state(pid, rows):
    st = None
    for r in rows:
        c = canon_state(r.get('state'))
        if r.get('id') == pid and c in PROMPT_STATES: st = c
    return st or 'WAITING'

def set_state(rows, pid, state, **kw):
    state = canon_state(state); assert state in PROMPT_STATES, state
    if state == 'WITHDRAWN': assert legacy_names.is_owner_withdraw(kw.get('by')), 'WITHDRAWN is trundle only'
    if state == 'MERGED': assert kw.get('merged_into') or kw.get('clip_id'), 'MERGED needs merged_into'
    if state == 'PARKED': assert kw.get('park_reason') or kw.get('reason'), 'PARKED needs park_reason'
    rows.append(dict(id=pid, state=state, **kw)); return rows

def combine(prompts, rows, clip_id):
    ids = [p['id'] for p in prompts]
    for pid in ids: set_state(rows, pid, 'MERGED', merged_into=clip_id)
    return {'clip_id': clip_id, 'prompt_ids': ids, 'comment_prompt_ids': ids}

def hold_prompt(rows, pid, reason, rewrite=None):
    set_state(rows, pid, 'PARKED', park_reason=reason, reason=reason, rewrite=rewrite); return rows

def next_for_break(prompts, waits, rows, max_wait=SKIPPED_BREAKS_CAP):
    """waits = skipped_breaks per prompt (capped). At the cap the prompt is guaranteed the next break."""
    cand = [p for p in prompts if prompt_state(p['id'], rows) == 'WAITING']
    if not cand: return None
    sk = lambda p: min(waits.get(p['id'], 0), max_wait)
    capped = [p for p in cand if sk(p) >= max_wait]
    pool = capped or cand
    return max(pool, key=lambda p: (sk(p), -p.get('seq', 0)))

def unterminated_prompts(clip, rows):
    """DE pickup refuses preempt/retire while a linked prompt lacks a terminal state."""
    ids = clip.get('comment_prompt_ids') or clip.get('prompt_ids') or []
    return [pid for pid in ids if prompt_state(pid, rows) not in TERMINAL_STATES]


# --- 18:29 CT overlay text rule: requested on-screen text never baked into generation ---
import re as _re
NO_TEXT_CONSTRAINT = 'no readable text, no signage lettering'
_Q = r'["\u201c\u2018\']([^"\u201d\u2019\']+)["\u201d\u2019\']'
_OVERLAY_PATTERNS = [
    ('caption', _re.compile(r'\b(?:that|which)?\s*(?:says|say|reads|read|reading|saying|with the words?|with the text|labell?ed|captioned|titled)\s*:?\s*' + _Q, _re.I)),
    ('caption', _re.compile(r'\b(?:caption|label|sign|banner|title|subtitle|text|price tag|tag)\s*(?:of|:)\s*' + _Q, _re.I)),
    ('price', _re.compile(r'(?:\bprice(?:d)?\s*(?:of|at|tag)?\s*:?\s*)?(\$\s?\d[\d,]*(?:\.\d\d)?)', _re.I)),
]
_TEXT_REQUEST = _re.compile(r'\b(says|reads|reading|saying|with the words?|with the text|caption(?:ed)?|label(?:l?ed)?|signage|sign that|subtitle|price tag|lettering|written|spell(?:s|ed|ing)?)\b|\$\s?\d', _re.I)
OVERLAY_BLOCK = [
    ('name', CREATOR),
    ('kids', _re.compile(r'\b(kids?|child(?:ren)?|toddlers?|babies|baby|drawbridge)\b', _re.I)),
    ('brand', _re.compile(r'\b(nike|adidas|apple|coca[- ]?cola|pepsi|amazon|walmart|target|disney|mcdonald\'?s|starbucks|google|tesla|ford|lego)\b', _re.I)),
    ('money', _re.compile(r'\b(donat\w*|tips?|tip jar|venmo|cash ?app|paypal|patreon|send money|support us)\b', _re.I)),
    ('mb_text', _re.compile(r'military\s*boutique', _re.I)),
]

def overlay_blocked(text):
    return [k for k, rx in OVERLAY_BLOCK if rx.search(text or '')]

def split_overlay_text(prompt, duration=None, position='lower_third', style='default'):
    """Returns (gen_prompt, overlay_specs). Extracted text never reaches the generator."""
    gen, specs, seen = prompt, [], set()
    for kind, rx in _OVERLAY_PATTERNS:
        for m in list(rx.finditer(gen)):
            t = m.group(1).strip()
            if t.lower() in seen: continue
            seen.add(t.lower())
            specs.append({'text': t, 'kind': kind, 'position': 'top_right' if kind == 'price' else position,
                          'start_s': 0.0, 'end_s': duration, 'style': style,
                          'blocked': overlay_blocked(t), 'airable': not overlay_blocked(t)})
        gen = rx.sub('', gen)
    gen = _re.sub(r'\s+([,.;!?])', r'\1', _re.sub(r'\s{2,}', ' ', gen)).strip(' ,;')
    if specs or _TEXT_REQUEST.search(gen):
        gen = _TEXT_REQUEST.sub('', gen) if not specs else gen
        gen = _re.sub(r'\s{2,}', ' ', gen).strip(' ,;')
    if NO_TEXT_CONSTRAINT not in gen:
        gen = (gen + ('; ' if gen else '') + NO_TEXT_CONSTRAINT)
    return gen, specs

def gen_prompt_requests_text(gen_prompt):
    """Flag: gen prompt still asks for readable text (ignores the no-text constraint itself)."""
    body = (gen_prompt or '').replace(NO_TEXT_CONSTRAINT, '')
    hits = [m.group(0) for m in _TEXT_REQUEST.finditer(body)] + [m.group(0) for m in _re.finditer(_Q, body)]
    return hits

def add_comment_prompt(text, handle=None, path=None, duration=None):
    """Append-only; returns permanent cp- id. Row: id, handle, text, gen_prompt, overlay_specs[], date.
    Overlay specs are editable later (new add-only row with same id + overlay_specs) without re-render;
    burn-in happens on a separate copy; the clean text-free master is the mutation parent and anchor source."""
    import hashlib, datetime
    p = Path(path or COMMENT_PROMPTS); p.parent.mkdir(parents=True, exist_ok=True)
    pid = 'cp-' + hashlib.sha256(f"{handle}|{text}".encode()).hexdigest()[:12]
    rows = [json.loads(l) for l in p.open()] if p.exists() else []
    if not any(r['id'] == pid for r in rows):
        gen, specs = split_overlay_text(text, duration)
        for s in specs: s['prompt_id'] = pid
        with p.open('a') as f: f.write(json.dumps({'id': pid, 'handle': handle, 'text': text, 'gen_prompt': gen,
            'overlay_specs': specs, 'date': datetime.datetime.now().astimezone().isoformat()}) + '\n')
    return pid

def overlay_specs_for(pid, path=None):
    """Latest overlay_specs for a prompt (later rows override = edit without re-render)."""
    p = Path(path or COMMENT_PROMPTS); out = []
    if p.exists():
        for l in p.open():
            r = json.loads(l)
            if r.get('id') == pid and 'overlay_specs' in r: out = r['overlay_specs']
    return out


# --- 18:40 CT add-only: delegate to the ONE shared splitter (defs above superseded, kept for history) ---
try:
    import overlay_split as _OS
except ImportError:
    sys.path.insert(0, 'out-of-scope/streaming/shared_lib')
    import overlay_split as _OS  # type: ignore[no-redef]
NO_TEXT_CONSTRAINT = _OS.NO_TEXT
_TEXT_REQUEST = _OS.TEXT_REQUEST

def overlay_blocked(text):
    return _OS.blocked(text)

def split_overlay_text(prompt, duration=None, position='lower_third', style='default'):
    """Returns (gen_prompt, overlay_specs) via the shared splitter. Always carries the no-text suffix (prior checker behavior)."""
    r = _OS.split(prompt)
    gen = r['gen_prompt']
    if NO_TEXT_CONSTRAINT not in gen:
        gen = (gen + ('; ' if gen else '') + NO_TEXT_CONSTRAINT)
    specs = []
    for i in r['items']:
        b = overlay_blocked(i['text'])
        specs.append({'text': i['text'], 'kind': 'price' if i['role'] == 'price' else 'caption', 'role': i['role'],
                      'position': 'top_right' if i['role'] == 'price' else position, 'start_s': 0.0, 'end_s': duration,
                      'style': style, 'blocked': b, 'airable': not b})
    return gen, specs

def gen_prompt_requests_text(gen_prompt):
    return _OS.requests_text(gen_prompt)


# --- 18:45 CT add-only: node rules matching Device Engineer out-of-scope/de-parity/pickup.py node_rows() ---
# (1) LINEAGE rows with global_no null/missing are superseded placeholders, never nodes.
# (2) a newer row whose supersedes (supersedes.global_no | supersedes_no | supersedes_global_no) equals an older
#     row's global_no wins; the older row is dropped as a node (kept in the file) and no duplicate is flagged.
def _gno(v):
    if isinstance(v, bool): return None
    if isinstance(v, int): return v if v >= 1 else None
    if isinstance(v, str) and _re.fullmatch(r'[1-9][0-9]*', v): return int(v)
    return None

def supersedes_no(r):
    s = r.get('supersedes')
    g = _gno(s.get('global_no')) if isinstance(s, dict) else None
    for k in ('supersedes_no', 'supersedes_global_no'):
        if g is None: g = _gno(r.get(k))
    return g

def node_rows(rows):
    rs = [r for r in rows if isinstance(r, dict) and r.get('clip_id') and r.get('row_type') not in NON_NODE_ROWS
          and r.get('row_type') != 'audio_post' and _gno(r.get('global_no')) is not None]
    drop = set()
    for j, r in enumerate(rs):
        g = supersedes_no(r)
        if g is None: continue
        for i in range(j):
            if i not in drop and _gno(rs[i].get('global_no')) == g: drop.add(i)
    return [r for i, r in enumerate(rs) if i not in drop]

def lineage_duplicates(rows):
    """global_no / clip_id values held by more than one node row after node_rows() -> {'global_no': [...], 'clip_id': [...]}."""
    from collections import Counter
    n = node_rows(rows)
    g = Counter(_gno(r['global_no']) for r in n); c = Counter(r['clip_id'] for r in n)
    return {'global_no': sorted(k for k, v in g.items() if v > 1), 'clip_id': sorted(k for k, v in c.items() if v > 1)}

_resolve_clean_1735 = resolve_clean
def resolve_clean(path, lineage=None, mb_dir=None):
    """Same as before, but over node_rows(): placeholders and superseded rows are not nodes.
    audio_post rows are passed through so leveled copies still resolve to their source."""
    mb = Path(mb_dir or MB_DIR); rows = load_lineage(mb / 'LINEAGE.jsonl') if lineage is None else lineage
    ap = [r for r in rows if isinstance(r, dict) and r.get('row_type') == 'audio_post']
    return _resolve_clean_1735(path, lineage=node_rows(rows) + ap, mb_dir=mb_dir)

# --- 18:48 CT add-only fix: superseded rows are not nodes, but their own files must still resolve to a clean master
# (e.g. the 4.4 BA-tagged #30-36 files). Superseded rows go FIRST so node rows win every by_no/by_tag lookup;
# only by_file for the superseded row's own file points at it. Null-global_no rows stay excluded.
def resolve_clean(path, lineage=None, mb_dir=None):
    mb = Path(mb_dir or MB_DIR); rows = load_lineage(mb / 'LINEAGE.jsonl') if lineage is None else lineage
    ap = [r for r in rows if isinstance(r, dict) and r.get('row_type') == 'audio_post']
    nodes = node_rows(rows); ids = {id(r) for r in nodes}
    sup = [r for r in rows if isinstance(r, dict) and id(r) not in ids and r.get('clip_id') and r.get('row_type') not in NON_NODE_ROWS
           and r.get('row_type') != 'audio_post' and _gno(r.get('global_no')) is not None]
    return _resolve_clean_1735(path, lineage=sup + nodes + ap, mb_dir=mb_dir)
