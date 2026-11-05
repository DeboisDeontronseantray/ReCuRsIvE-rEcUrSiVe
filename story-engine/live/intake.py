"""Commenter-prompt intake: queue (JSONL FIFO) -> header wrap (verbatim) -> moderation -> checker -> pending-approval clip JSON.
Local only. Never renders, never sends, never touches ErsatzTV. Usage:
  python live/intake.py enqueue --handle @x --text "..."    (X Live Stream's job in production)
  python live/intake.py process                              (Story Bot)"""
import argparse, json, re, sys, time, uuid
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import checker, random, yaml

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "data/live"
QUEUE, DONE, REJECTED, PENDING = LIVE / "queue.jsonl", LIVE / "processed.jsonl", LIVE / "rejected.jsonl", LIVE / "pending-approval"
RATE_15, RATE_REF, RATE_LITE = 0.08, 0.01, 0.02
CAST = ["Osmund", "Tim", "Lt. Mira S'mirin'", "Commander Bill D'bears"]
OOC = re.compile(r"\b(dance|danc\w+|sing|singing|rap|twerk|backflip|juggle|moonwalk|propose|kiss|cosplay|break the fourth wall|talk to (the )?camera|say my name|shout ?out)\b", re.I)
REAL_PEOPLE = re.compile(r"\b(president|senator|governor|elon|musk|trump|biden|obama|taylor swift|kanye|drake|mrbeast|celebrity)\b", re.I)
DEFAME = re.compile(r"\b(is a (fraud|criminal|pedo\w*|rapist|thief|liar)|scam(mer)?s? (people|everyone))\b", re.I)
SPAM = re.compile(r"(https?://|www\.|\bfollow me\b|\bfree (crypto|money|giveaway)\b|\bdm me\b|(.)\2{7,})", re.I)

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def _append(p, rec):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
def _read(p): return [json.loads(l) for l in open(p)] if p.exists() else []

def enqueue(handle, text, source="x-live-chat"):
    rec = {"id": uuid.uuid4().hex[:10], "received_at": now(), "handle": handle, "text": text, "source": source}
    _append(QUEUE, rec); return rec

XINBOX = Path("out-of-scope/shared/streaming/x-intake/queue/storybot-inbox")

LIVE_CONFIG = Path(__file__).parent / "live-config.yaml"
def auto_approve_enabled(path=None):
    p = Path(path or LIVE_CONFIG)
    return bool((yaml.safe_load(open(p)) or {}).get("auto_approve_enabled", False)) if p.exists() else False

def import_xintake(inbox=XINBOX, require_status=None, config=None):
    """Read X Live Stream's x-intake/v1 items (read-only). Only trundle-APPROVED items enter the queue; sha256 must match verbatim text."""
    import hashlib
    have = {r.get("source_id") for r in _read(QUEUE)}
    if require_status is None:
        require_status = ("APPROVED", "AUTO_APPROVED") if auto_approve_enabled(config) else ("APPROVED",)
    added, skipped = [], []
    for f in sorted(Path(inbox).glob("*.json"), key=lambda p: p.stat().st_mtime):
        it = json.load(open(f)); txt = it.get("commenter_text_verbatim", "")
        sid = f"{it.get('commenter', {}).get('source')}-{it.get('commenter', {}).get('message_id')}"
        if it.get("schema") != "x-intake/v1" or it.get("status") not in require_status or sid in have:
            if it.get("status") == "AUTO_APPROVED" and "AUTO_APPROVED" not in require_status:
                _append(LIVE / "held-auto-approved.jsonl", {"ts": now(), "file": f.name, "id": sid, "reason": "auto_approve_enabled=false"})
                skipped.append((f.name, "AUTO_APPROVED held (auto_approve off)")); continue
            skipped.append((f.name, it.get("status"))); continue
        if hashlib.sha256(txt.encode()).hexdigest() != it.get("commenter_text_sha256"):
            skipped.append((f.name, "sha256 mismatch")); continue
        rec = {"id": uuid.uuid4().hex[:10], "received_at": it["commenter"].get("ts") or now(), "handle": it["commenter"]["handle"],
               "text": txt, "source": "x-intake/v1", "source_id": sid, "credit_line": it.get("credit_line"),
               "xintake_path": str(Path(f).resolve())}
        _append(QUEUE, rec); added.append(rec)
    return added, skipped

def write_back(path, fields):
    """Single path with X Live Stream: add Story Bot fields to the SAME storybot-inbox item, atomically.
    Existing fields are never changed (only new keys added). Never writes commenter-pipeline/inbox/ (x-intake/export_cnb.py is the only writer)."""
    import os, tempfile
    path = Path(path)
    assert "commenter-pipeline" not in str(path), "never write commenter-pipeline/inbox/"
    it = json.load(open(path))
    clash = [k for k in fields if k not in STORYBOT_KEYS or (k != "status" and k in it and k not in it.get("storybot_fields", []) and it[k] != fields[k])]
    if fields.get("status") not in (None, "IN_STORY") or ("status" in fields and it.get("status") not in ("APPROVED", "AUTO_APPROVED", "IN_STORY")):
        clash.append("status")
    if clash: raise ValueError(f"refusing to overwrite existing fields {clash} in {path.name}")
    it.update(fields); it["storybot_fields"] = sorted(set(it.get("storybot_fields", [])) | set(fields) - {"status"})
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".", suffix=".tmp")
    with os.fdopen(fd, "w") as fh: json.dump(it, fh, indent=1, ensure_ascii=False); fh.flush(); os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path

STORYBOT_KEYS = {"storybot_fields", "storybot_clip", "status", "wrapped_prompt", "story_slot", "end_frame", "end_frame_source", "out_of_character", "injections", "storybot_check", "storybot_ts"}

EXPORT_CNB = Path("out-of-scope/shared/streaming/x-intake/export_cnb.py")
CNB_INBOX = None      # None = export_cnb's default; tests set a temp dir
EXPORT_DRY_RUN = False

def export_item(item_path):
    """Option A: hand ONE item to x-intake/export_cnb.py (the only writer to CNB inbox). Story Bot never writes that inbox itself."""
    import importlib.util, shutil, tempfile
    spec = importlib.util.spec_from_file_location("export_cnb", EXPORT_CNB); ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)
    q = Path(tempfile.mkdtemp(prefix="sb-export-")); shutil.copy(item_path, q / Path(item_path).name)
    try:
        w, s, e = ex.export(queue=str(q), inbox=CNB_INBOX or ex.CNB_INBOX, dry_run=EXPORT_DRY_RUN)
    finally: shutil.rmtree(q)
    return {"written": w, "skipped": [x[1] for x in s], "errors": [str(x[1]) for x in e], "dry_run": EXPORT_DRY_RUN}

def moderate(text):
    reasons = []
    if SPAM.search(text) or len(text.strip()) < 4: reasons.append("spam/empty")
    if checker.unsafe_hits(checker.strip_negated(text)): reasons.append("not TV-safe")
    if checker.brand_hits(text): reasons.append("real brand: " + ", ".join(checker.brand_hits(text)))
    if REAL_PEOPLE.search(text): reasons.append("real person")
    if DEFAME.search(text): reasons.append("defamation")
    if checker.creator_name_hits(text): reasons.append("no_creator_name_on_screen")
    return reasons

PERFORMER = [("Commander Bill D'bears", r"\b(bill|commander|d'bears)\b"), ("Lt. Mira S'mirin'", r"\b(mira|lieutenant|lt\.?|s'mirin')\b"),
             ("Osmund", r"\bosmund\b"), ("Tim", r"\btim\b")]

def find_performer(text, ooc_pos=0):
    """Cast member doing the out-of-character action: nearest name before the action verb, else first name after, else Osmund."""
    hits = sorted((mm.start(), name) for name, rx in PERFORMER for mm in re.finditer(rx, text, re.I))
    before = [h for h in hits if h[0] <= ooc_pos]
    if before: return before[-1][1]
    return hits[0][1] if hits else "Osmund"

def wrap(rec, data_slots=None):
    """Header wrapper: commenter text stays VERBATIM inside; levers added around it, never replacing intent."""
    m = OOC.search(rec["text"]); ooc = bool(m)
    performer = find_performer(rec["text"], m.start() if m else 0) if ooc else None
    speaker = performer if performer != "Tim" else "Lt. Mira S'mirin'"   # Tim chirps only; Mira voices it for him
    reflect = None
    if ooc:
        reflect = (f"idk why I'm doing this but {rec['handle']} thinks it's a good idea" if performer != "Tim"
                   else f"idk why Tim's doing this but {rec['handle']} thinks it's a good idea")
    return {
        "header": {"network": "thunder trundle", "channel": "Ch 4 Military Boutique", "show": "Forward Supply",
                   "bible": "continuity/ch04-military-boutique/bible-v2.yaml",
                   "rules": ["home-only until trundle's yes", "TV-safe", "no real brands or people", "no dial/phone CTA",
                             "no slapstick", "fog never lifts", "Tim chirps only", "cast: " + ", ".join(CAST)]},
        "commenter": {"handle": rec["handle"], "text_verbatim": rec["text"], "received_at": rec["received_at"]},
        "levers": {"realtime_data_slots": data_slots or {"local_time_ct": None, "weather_line": None, "vote_leader": None},
                   "out_of_character": ooc, "ooc_performer": performer, "self_reflection_speaker": speaker if ooc else None,
                   "self_reflection_line": reflect},
    }

SNIPPETS = Path(__file__).parent / "snippets.yaml"
CAST_WORDS = re.compile(r"\b(osmund|tim|mira|bill|commander|lieutenant|lt\.?|crew|everyone|somebody|someone|they|he|she|people|guy|team)\b", re.I)
LOC_WORDS = re.compile(r"\b(outpost|mess hall|command hut|supply bay|bunk\w*|hatch|showroom|depot|porthole|fog)\b", re.I)
VERB = re.compile(r"(\w+(s|ed|ing)|do|does|make|find|go|look|say|eat|run|fly|sing|dance|check|show|lead|give|get|take|build|try|play|open|fix|search|cook|hide|throw|grab|wear|use|cry|laugh|sleep|jump)", re.I)
STOP_S = {"is","as","has","was","this","his","its","yes","us","always","bus","less","gas","glass","boss","plus","thus","nothing","something","everything","red","bed","need","lots","things","stuff","vibes","fries","news"}

def load_snippets(path=None):
    path = Path(path or SNIPPETS)
    lib = yaml.safe_load(open(path)) if path.exists() else {"config": {"enabled": False}, "snippets": []}
    lib["snippets"] = [s for s in (lib.get("snippets") or []) if not checker.creator_name_hits(str(s.get("text", "")))]   # no creator name on screen
    return lib

def prompt_features(text):
    words = re.findall(r"[\w']+", text)
    verb = any(VERB.fullmatch(w) and w.lower() not in STOP_S for w in words)
    people = bool(CAST_WORDS.search(text))
    loc = bool(LOC_WORDS.search(text))
    reasons = [r for r, bad in (("<6 words", len(words) < 6), ("no verb", not verb), ("no cast/location", not (people or loc))) if bad]
    return {"weak": bool(reasons), "weak_reasons": reasons, "people_on_screen": people, "words": len(words)}

def inject(wrapped, rec_id="", lib=None, log=None, now_ts=None):
    """Optional flair snippets under levers.injections. Never touches commenter.text_verbatim."""
    lib = lib or load_snippets(); cfg = lib.get("config", {}); log = Path(log or LIVE / "injections.jsonl")
    text = wrapped["commenter"]["text_verbatim"]; f = prompt_features(text)
    lv = wrapped["levers"]; lv["prompt_features"] = f; lv["injections"] = []
    if not cfg.get("enabled", True): return wrapped
    t = now_ts or time.time(); hist = [r for r in _read(log) if t - r["ts"] < 3600]
    used = lambda sid: sum(1 for r in hist if r["id"] == sid)
    every = cfg.get("disclosure_every_n", 3)
    disclose_ok = every > 0 and len({r["rec"] for r in hist}) % every == 0
    rng = random.Random(rec_id or text)
    def ok(s):
        if not s.get("tv_safe") or s.get("speaker") == "Tim": return False
        if checker.money_hits(s.get("text", "")): return False   # trundle 4:35 PM CT: no donation/money asks, ever
        if (s.get("requires", {}).get("people_on_screen") or s["kind"] == "spoken_line") and not f["people_on_screen"]: return False
        if s.get("disclosure") and not disclose_ok: return False
        if used(s["id"]) >= s.get("max_per_hour", 99): return False
        w = s.get("when")
        return (w == "always" or (w == "weak_prompt" and f["weak"]) or (w == "ooc" and bool(lv.get("out_of_character")))
                or (w == "random" and f["weak"] and rng.random() < cfg.get("random_chance", 0.25)))
    def pick(pool, n):
        pool = [s for s in pool if ok(s)]
        return [rng.choices(pool, weights=[s.get("weight", 1) for s in pool])[0]] if pool and n > 0 else []
    sn = lib.get("snippets", [])
    chosen = pick([s for s in sn if s["kind"] == "spoken_line"], cfg.get("max_spoken", 1))
    chosen += pick([s for s in sn if s["kind"] != "spoken_line"], cfg.get("max_visual", 1))
    lv["injections"] = [{"id": s["id"], "kind": s["kind"], "speaker": s.get("speaker"), "text": s["text"], "when": s["when"]} for s in chosen]
    for s in chosen: _append(log, {"ts": t, "id": s["id"], "rec": rec_id})
    return wrapped

REF_INDEX = Path(__file__).parent / "ref-index.yaml"
AIRED = LIVE / "aired.jsonl"   # optional: {"ts","mp4","status":"aired|approved"} lines; newest wins over the S7D default
REF_CAP_DEFAULT, REF_CAP_MAX = 4, 14
TIM_IMPLIED = re.compile(r"\b(optic|brain|dome|drone buddy|floating)\b", re.I)
def load_ref_index(path=None): return yaml.safe_load(open(path or REF_INDEX))

def _has(text, aliases): return any(re.search(r"(?<![\w'])" + re.escape(a) + r"(?![\w])", text, re.I) for a in aliases)

def pick_refs(wrapped, cap=REF_CAP_DEFAULT, idx=None):
    """Real reference stills: location first, then named/implied cast, then named products, then default crew. Only existing files."""
    idx = idx or load_ref_index(); cap = max(1, min(int(cap), REF_CAP_MAX))
    text = wrapped["commenter"]["text_verbatim"]
    loc = next((k for k, v in idx["locations"].items() if _has(text, v["aliases"])), idx.get("default_location"))
    cast = [k for k, v in idx["cast"].items() if _has(text, v["aliases"])]
    if "tim" not in cast and TIM_IMPLIED.search(text): cast.append("tim")
    prods = [k for k, v in idx["products"].items() if _has(text, v["aliases"])]
    picks = []   # (kind, key, path)
    lp = idx["locations"].get(loc, {}).get("still")
    if lp: picks.append(("location", loc, lp))
    picks += [("cast", k, idx["cast"][k]["primary"]) for k in cast]
    picks += [("product", k, idx["products"][k]["still"]) for k in prods if idx["products"][k].get("still")]
    picks += [("crew", k, idx["cast"][k]["primary"]) for k in idx.get("default_crew", []) if k not in cast]
    picks += [("turnaround", k, p) for k in (cast or idx.get("default_crew", [])) for p in idx["cast"][k]["stills"][1:]]
    seen, out, rejected = set(), [], []
    for kind, key, p in picks:
        if not p: continue
        try: p = checker.resolve_clean(p)   # clean-source guard: never feed overlay/tag/badge copies
        except checker.CleanSourceError as e: rejected.append({"kind": kind, "key": key, "path": p, "reason": str(e)}); continue
        if p not in seen and Path(p).is_file(): seen.add(p); out.append({"kind": kind, "key": key, "path": p})
    out = out[:cap]
    missing = [k for k in prods if not idx["products"][k].get("still")]
    return {"paths": [r["path"] for r in out], "picks": out, "location": loc, "cast_keys": cast, "products": prods,
            "products_without_still": missing, "cap": cap, "rejected_tainted": rejected}

def pick_end_frame(idx=None, aired=None):
    """Continuity anchor: newest aired/approved Forward Supply clip, else Run 2 S7D. CNB extracts last_frame at render time."""
    idx = idx or load_ref_index(); a = Path(aired or AIRED)
    for r in reversed(_read(a)):
        if r.get("status") in ("aired", "approved") and r.get("mp4") and Path(r["mp4"]).is_file():
            try: src = checker.resolve_clean(r["mp4"])
            except checker.CleanSourceError as e: raise checker.CleanSourceError(f"end frame: {e}")
            return {"source_mp4": src, "aired_mp4": r["mp4"], "frame": "last_frame", "from": f"{r['status']} {r.get('ts', '')}".strip(), "extract": "CNB at render time"}
    anc = idx["continuity_anchor"]
    try: src = checker.resolve_clean(anc["source_mp4"])
    except checker.CleanSourceError as e: raise checker.CleanSourceError(f"end frame anchor: {e}")
    return {"source_mp4": src, "frame": "last_frame", "from": "default: run2 " + anc["shot"], "extract": "CNB at render time"}

# negatives policy: "no personal names" is enforced via "no names" + checker.creator_name_hits (the literal name must not reach any prompt)
CAMERA_RULE = ("Camera rule (2026-10-27): characters never look at or address the camera; candid observational fly-on-the-wall framing; "
               "eyelines on each other, their task, or off-frame; no direct-to-camera dialogue.")

def to_clip(wrapped, duration=6, refs=REF_CAP_DEFAULT, model="grok-imagine-video-1.5"):
    c, lv = wrapped["commenter"], wrapped["levers"]
    rp = pick_refs(wrapped, refs); ef = pick_end_frame(); refs = len(rp["paths"])
    rate = RATE_LITE if model.endswith("lite") else RATE_15
    est = round(duration * rate + (0 if model.endswith("lite") else refs * RATE_REF), 2)
    action = f"Viewer request, kept as written: \"{c['text_verbatim']}\". The crew of Outpost Quiet carries it out deadpan, procedural, inside the fog."
    dialogue = [{"speaker": lv.get("self_reflection_speaker") or "Osmund", "line": lv["self_reflection_line"]}] if lv["self_reflection_line"] else []
    inj = lv.get("injections", [])
    dialogue += [{"speaker": i["speaker"], "line": i["text"], "injected": i["id"]} for i in inj if i["kind"] == "spoken_line"]
    flair = " ".join(i["text"] for i in inj if i["kind"] != "spoken_line")
    shot = {"id": "LIVE-" + datetime.now().strftime("%H%M%S"), "scene": "LIVE viewer request", "duration_s": duration, "model": model,
            "camera": "medium locked", "cast": ["Osmund", "Lt. Mira S'mirin'", "Tim", "Commander Bill D'bears"],
            "location": "Outpost Quiet mess hall, fog never lifts outside the porthole",
            "lighting_fog": "Warm overhead practicals, cyan edge light, grey fog glow.", "props_products": [],
            "continues_from": f"last frame of {ef['source_mp4']} ({ef['from']})", "action": action, "dialogue": dialogue,
            "visual_prompt": ("Photoreal grounded near-future outpost, Ch 4 Military Boutique, late-90s broadcast polish, 4:3-safe. "
                              "Osmund in olive coveralls, buzz cut; Mira with long dark braid and clipboard; Bill muscular with blank name tag; "
                              "Tim floating brain under glass dome with cyan optic. " + action + (" Flair (added, not from viewer): " + flair if flair else "") + " " + CAMERA_RULE),
            "camera_rule": CAMERA_RULE,
            "negative_prompt": "no names, no signatures, no watermarks, no on-screen text, no logos, no brand names, no real people, no slapstick, no looking into the camera, no addressing the viewer, no on-screen names, no children, no kids",
            "reference_images": rp["paths"], "reference_picks": rp, "end_frame": ef, "end_frame_source": ef["source_mp4"], "est_usd": est,
            "status": "PENDING trundle APPROVAL - not sent to CNB", "live_wrapper": wrapped}
    return shot

def process(limit=None):
    q = _read(QUEUE); done_ids = {r["id"] for r in _read(DONE) + _read(REJECTED)}
    out = []
    for rec in [r for r in q if r["id"] not in done_ids][:limit]:   # FIFO by file order
        reasons = moderate(rec["text"])
        if reasons:
            if rec.get("xintake_path"): write_back(rec["xintake_path"], {"storybot_check": {"status": "fail", "fails": reasons, "stage": "moderation"}, "storybot_ts": now()})
            _append(REJECTED, {**rec, "rejected_at": now(), "reasons": reasons}); out.append((rec, "rejected", reasons)); continue
        shot = to_clip(inject(wrap(rec), rec['id']))
        chk = checker.check_shot(shot, None, checker.registry(checker.load_bible()), {})
        if chk["status"] == "fail":
            if rec.get("xintake_path"): write_back(rec["xintake_path"], {"storybot_check": chk, "storybot_ts": now()})
            _append(REJECTED, {**rec, "rejected_at": now(), "reasons": chk["fails"]}); out.append((rec, "rejected", chk["fails"])); continue
        if rec.get("xintake_path"):   # X item: write back to the same storybot-inbox file, NOT pending-approval
            lv = shot["live_wrapper"]["levers"]
            write_back(rec["xintake_path"], {"wrapped_prompt": json.dumps(shot, ensure_ascii=False), "storybot_clip": shot,
                       "story_slot": shot.get("story_slot"),
                       "end_frame": shot.get("end_frame"), "end_frame_source": shot.get("end_frame_source"), "out_of_character": lv["out_of_character"],
                       "injections": lv.get("injections", []), "storybot_check": chk, "storybot_ts": now(), "status": "IN_STORY"})
            exp = export_item(rec["xintake_path"])
            _append(DONE, {**rec, "processed_at": now(), "written_back": rec["xintake_path"], "check": chk["status"], "export": exp})
            out.append((rec, "written_back", rec["xintake_path"])); continue
        PENDING.mkdir(parents=True, exist_ok=True)
        doc = {"channel_id": "ch04", "channel_name": "Ch 4 Military Boutique", "show_id": "forward-supply", "show_title": "Forward Supply",
               "note": "LOCAL ONLY - do not hand to CNB until trundle reviews", "check": chk, "shots": [shot]}
        path = PENDING / f"{rec['received_at'][:19].replace(':','')}_{rec['id']}.json"
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
        _append(DONE, {**rec, "processed_at": now(), "pending": str(path), "check": chk["status"]})
        out.append((rec, "pending", str(path)))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd")
    e = sp.add_parser("enqueue"); e.add_argument("--handle", required=True); e.add_argument("--text", required=True)
    sp.add_parser("process"); sp.add_parser("import-xintake")
    a = ap.parse_args()
    if a.cmd == "import-xintake":
        added, skipped = import_xintake(); print("imported", len(added), "skipped", skipped)
        for rec, st, info in process(): print(st, rec["handle"], info)
    elif a.cmd == "enqueue": print(json.dumps(enqueue(a.handle, a.text)))
    else:
        for rec, st, info in process(): print(st, rec["handle"], info)
