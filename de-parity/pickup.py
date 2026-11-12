#!/usr/bin/env python3
"""Commenter clip pickup for Channel 4 (Device Engineer, 2026-10-27). MANUAL ONLY: no watcher, no launchd.
DISABLED unless ~/smart-office/media_server/commenter-pickup/ENABLED exists (created only after trundle says yes)
or --test is given (test mode only accepts ids starting with DUMMY-).
Input: ~/fakenews_out/commenter-staged/<id>/{<id>_ch04_commenter_parody.mp4, approval.json} (copied from the box).
  pickup.py check            -> list staged bundles and gate result (read-only)
  pickup.py insert [--test]  -> ONE clip: re-gate, sha256, ffprobe, copy into the 'Channel 4 Approved Inserts' library,
                                scan, add the marked INSERTS block at the next HOUSE break in military-boutique-v1.yml,
                                reset Channel 4 playout. Uses the shared one-clip lock media_server/.ingest.lock.
  pickup.py retire ID [--test] -> move the clip to commenter-aired/, rescan, restore YAML block to empty, reset.
Never touches ch1, channel1-testcuts.yml, ~/fakenews_out/held/, American Hostage or norm24.
Status -> media_server/clip_status.jsonl ; ledger (id+sha256, add-only) -> commenter-pickup/ledger.jsonl"""
import datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, time, urllib.request
H = os.path.expanduser("~"); MS = f"{H}/smart-office/media_server"; HERE = f"{MS}/commenter-pickup"
STAGED = os.environ.get("PICKUP_STAGED", f"{H}/fakenews_out/commenter-staged"); LIB_DIR = os.environ.get("PICKUP_LIBDIR", f"{MS}/thunder-trundle/commenter-approved")
AIRED = os.environ.get("PICKUP_AIRED", f"{MS}/thunder-trundle/commenter-aired"); LIB_NAME = "Channel 4 Approved Inserts"
YML = os.environ.get("PICKUP_YML", f"{MS}/ersatztv/military-boutique-v1.yml"); STATUS = os.environ.get("PICKUP_STATUS", f"{MS}/clip_status.jsonl")
LEDGER = os.environ.get("PICKUP_LEDGER", f"{HERE}/ledger.jsonl"); LOCK = os.environ.get("PICKUP_LOCK", f"{MS}/.ingest.lock"); ETV = f"{H}/Library/Application Support/ersatztv"
BASE = "http://127.0.0.1:8409"; CH = "4"
# Lineage (final, trundle locked 2026-10-27 17:01 CT via Story Bot). CNB is the ONLY writer; pickup only reads. Missing file => refuse all.
LINEAGE = os.environ.get("PICKUP_LINEAGE", f"{MS}/thunder-trundle/4_Military-Boutique/LINEAGE.jsonl")
TAG_RE = re.compile(r"^4\.[1-9][0-9]* g[1-9][0-9]* #[1-9][0-9]*$")
NAME = re.compile(r"^[A-Za-z0-9._-]+_ch04_commenter_parody\.mp4$")
BANNED = ("held", "american hostage", "american_hostage", "americanhostage", "norm24", "testcuts", "channel1")
B0, B1 = "# >>> COMMENTER_INSERTS (pickup.py; empty = off)", "# <<< COMMENTER_INSERTS"
def now(): return dt.datetime.now().astimezone().isoformat(timespec="seconds")
def log(o): o = {"ts": now(), "by": "commenter-pickup", **o}; open(STATUS, "a").write(json.dumps(o) + "\n"); print(json.dumps(o))
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def ledger():
    return [json.loads(l) for l in open(LEDGER)] if os.path.exists(LEDGER) else []
def key():
    env = os.environ.get("ETV_API_KEY")
    if env:
        return env
    return json.load(open(f"{ETV}/api-secrets.json"))["ApiKey"]   # never printed; prefer ETV_API_KEY
def api(m, path):
    r = urllib.request.Request(BASE + path, method=m, headers={"X-Etv-Api-Key": key(), "Content-Type": "application/json"}, data=b"{}" if m == "POST" else None)
    with urllib.request.urlopen(r, timeout=60) as x: return x.status
def db(sql, a=()):
    import sqlite3; cwd = os.getcwd(); os.chdir(ETV)
    try:
        c = sqlite3.connect("file:" + os.environ.get("PICKUP_DB", "ersatztv.sqlite3") + "?mode=ro", uri=True); return c.execute(sql, a).fetchall()
    finally: os.chdir(cwd)
def lib_id():
    r = db("select Id from Library where Name=?", (LIB_NAME,)); return r[0][0] if r else None
def lib_titles(lid):
    return [r[0] for r in db("select mf.Path from MediaFile mf join MediaVersion mv on mv.Id=mf.MediaVersionId "
        "join MediaItem mi on mi.Id=coalesce(mv.OtherVideoId,mv.MovieId) join LibraryPath lp on lp.Id=mi.LibraryPathId "
        "where lp.LibraryId=? and mi.State=0", (lid,))]
def probe(p):
    o = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", p], capture_output=True, text=True).stdout or "{}")
    v = [s for s in o.get("streams", []) if s.get("codec_type") == "video"]; a = [s for s in o.get("streams", []) if s.get("codec_type") == "audio"]
    if not v or not a: return "missing video or audio stream"
    if (v[0].get("codec_name"), v[0].get("width"), v[0].get("height")) != ("h264", 848, 480): return f"video not h264 848x480: {v[0].get('codec_name')} {v[0].get('width')}x{v[0].get('height')}"
    if a[0].get("codec_name") != "aac": return "audio not aac"
    return None
ORIGINS = ("first_render", "remake", "comment_branch", "overlay_edit")
def _num(v):  # int in the file (or a digit string); bools and anything else -> None (fail closed)
    if isinstance(v, bool): return None
    if isinstance(v, int): return v if v >= 1 else None
    if isinstance(v, str) and re.fullmatch(r"[1-9][0-9]*", v): return int(v)
    return None
# CNB story-engine/live/checker.py: audio_post copies + NON_NODE_ROWS are never lineage nodes; a node needs a clip_id.
NON_NODE_ROWS = {"pulled", "unpull", "correction", "clean_master_allow", "duplicate_premise"}
# Lead 18:34 CT: a row with global_no null is a superseded placeholder (e.g. the 4.4 tagfade rows replaced by #30-36), never a node.
# Lead 18:37 CT option (A): a newer row whose supersedes.global_no equals an older row's global_no wins; the older row is not a node.
def node_rows(rows):
    rs = [r for r in rows if isinstance(r, dict) and r.get("clip_id") and r.get("row_type") not in NON_NODE_ROWS and r.get("row_type") != "audio_post"
          and r.get("global_no") is not None]
    drop = set()
    for j, r in enumerate(rs):
        sup = r.get("supersedes")
        g = _num(sup.get("global_no")) if isinstance(sup, dict) else None
        if g is None: continue
        for i in range(j):
            if i not in drop and _num(rs[i].get("global_no")) == g: drop.add(i)
    return [r for i, r in enumerate(rs) if i not in drop]
def lineage_check(cid):
    if not os.path.isfile(LINEAGE): return "LINEAGE.jsonl missing (fail closed)"
    try: rows = [json.loads(l) for l in open(LINEAGE) if l.strip()]
    except Exception as e: return f"LINEAGE.jsonl unreadable: {type(e).__name__}"
    if not all(isinstance(y, dict) for y in rows): return "LINEAGE row not an object"
    rows = node_rows(rows)
    mine = [x for x in rows if x.get("clip_id") == cid]
    if not mine: return "no LINEAGE row for clip_id"
    if len(mine) > 1: return "multiple LINEAGE rows for clip_id"
    x = mine[0]
    for k in ("clip_id", "tag", "lineage", "origin"):
        if not isinstance(x.get(k), str): return f"lineage field {k} not a string"
    if not re.fullmatch(r"4\.[1-9][0-9]*", x["lineage"]): return "lineage not '4.N'"  # 4.10+ allowed (Lead 18:34: lineages 4.5-4.11)
    gen, gno = _num(x.get("gen")), _num(x.get("global_no"))
    if gen is None: return "gen not a positive int"
    if gno is None: return "global_no not a positive int"
    if not TAG_RE.match(x["tag"]): return "lineage tag fails regex"
    if x["tag"] != f"{x['lineage']} g{gen} #{gno}":
        # Lead 18:34 CT: burned tag may keep an older lineage (trundle no-rework rule) when the row says burned_tag_matches false;
        # LINEAGE lineage is the source of truth, but gen and global_no in the tag must still match.
        m = re.fullmatch(r"4\.[1-9][0-9]* g([0-9]+) #([0-9]+)", x["tag"])
        if not (x.get("burned_tag_matches") is False and m and int(m.group(1)) == gen and int(m.group(2)) == gno):
            return "tag != '{lineage} g{gen} #{global_no}'"
    if sum(1 for y in rows if _num(y.get("global_no")) == gno) != 1: return "duplicate global_no in LINEAGE"
    if "parent_tag" in x and x["parent_tag"] is not None and not isinstance(x["parent_tag"], str): return "parent_tag not a string"
    if x["origin"] not in ORIGINS: return f"unknown origin {x['origin']!r}"
    if x["origin"] == "first_render":
        if x.get("parent_global_no") is not None or x.get("parent_id") is not None: return "first_render must have null parent_global_no/parent_id"
        return None
    pg = _num(x.get("parent_global_no"))
    if pg is None: return "parent_global_no missing for non-original"
    if pg == gno: return "parent_global_no points at itself"
    if not any(_num(y.get("global_no")) == pg for y in rows): return "parent_global_no not found in LINEAGE"
    pid = x.get("parent_id")
    if not isinstance(pid, str) or not pid: return "parent_id missing for non-original"
    hit = [y for y in rows if y is not x and (y.get("clip_id") == pid or y.get("tag") == pid)]
    if len(hit) != 1: return f"parent_id resolves to {len(hit)} rows (need exactly 1)"
    if _num(hit[0].get("global_no")) != pg: return "parent_id row's global_no != parent_global_no"
    return None
def audio_check(r):  # trundle 17:36 CT (COMMENTER-CLIP-PATH 17:36): leveled to -16 LUFS +/-1 LU, values in the manifest row
    if r.get("audio_leveled") is not True: return "audio_leveled not true"
    v = r.get("lufs_i")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v: return "lufs_i missing or not a number"
    if not (-17.0 <= v <= -15.0): return f"lufs_i {v} outside -17..-15"
    tp = r.get("true_peak_dbtp")
    if isinstance(tp, bool) or not isinstance(tp, (int, float)) or tp != tp: return "true_peak_dbtp missing or not a number"
    if tp > -1.5: return f"true_peak_dbtp {tp} above -1.5"
    return None
def gate(d, test):
    aj = os.path.join(d, "approval.json")
    if not os.path.isfile(aj): return None, "no approval.json"
    r = json.load(open(aj)); cid = str(r.get("id")); f = os.path.join(d, os.path.basename(r.get("file") or ""))
    if test and not cid.startswith("DUMMY-"): return r, "test mode accepts DUMMY- ids only"
    if not test and cid.startswith("DUMMY-"): return r, "DUMMY id outside test mode"
    if cid.upper().startswith("TEST-ONLY"): return r, "TEST-ONLY id"
    if r.get("trundle_air_yes") is not True and r.get("thundertrundle_air_yes") is not True: return r, "no trundle_air_yes"
    if any(w in str(r.get("status", "")).lower() for w in ("auto", "revoked", "held")): return r, f"status {r.get('status')}"
    if r.get("ocr_pass") is not True: return r, "ocr_pass not true"
    aw = audio_check(r)
    if aw: return r, aw
    if not (r.get("trundle_air_yes_at") or r.get("thundertrundle_air_yes_at")) or not (r.get("trundle_air_yes_source") or r.get("thundertrundle_air_yes_source")): return r, "approval time/source missing"
    if r.get("injections_status") in ("draft-needs-trundle-ok", "draft-needs-thundertrundle-ok"): return r, "injections draft"
    if any((c.get("voice") or "") == "TBD-trundle" for c in r.get("post_tts_cues") or []): return r, "TTS voice TBD-trundle"
    if any(b in (d + f).lower() for b in BANNED): return r, "banned path/name"
    lw = lineage_check(cid)
    if lw: return r, lw
    if not NAME.match(os.path.basename(f)) or not os.path.basename(f).startswith(cid + "_"): return r, "bad file name"
    if not os.path.isfile(f): return r, "clip missing"
    s = sha(f)
    if s != (r.get("trundle_air_yes_sha256") or r.get("thundertrundle_air_yes_sha256")): return r, "sha256 does not match the approved file"
    if any(l.get("id") == cid and l.get("sha256") == s for l in ledger()): return r, "already in ledger (done)"
    p = probe(f)
    if p: return r, p
    r["_file"], r["_sha"] = f, s; return r, None
# v2 (2026-10-27 16:55 CT): never cut a House Ad; play the clip ONCE at the break; auto-retire after its first airing.
# How: the marked block sits at the TOP of `playout:` (a one-shot `content: INSERTS, count: 1` that runs before the LOOP).
# The reset is fired at the END time of the House Ad currently on air (read from PlayoutItem.Finish), so the ad
# finishes, the rebuilt playout starts with the clip, then LOOP resumes. No change to the sequence, so no repeats.
DRY = os.environ.get("PICKUP_DRY") == "1"          # offline: no API calls, simulated clock
CLOCK = [dt.datetime.fromisoformat(os.environ["PICKUP_NOW"]) if os.environ.get("PICKUP_NOW") else None]                                       # simulated UTC 'now' for DRY runs
def utcnow(): return CLOCK[0] or dt.datetime.utcnow()
def sleep_until(t):
    if DRY: CLOCK[0] = max(utcnow(), t); return
    while utcnow() < t: time.sleep(min(1.0, max(0.05, (t - utcnow()).total_seconds())))
def P(s):  # py3.9 fromisoformat needs 0/3/6 fraction digits; ErsatzTV can write 1-7
    s = str(s); m = re.match(r"^(\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d)(?:\.(\d+))?", s)
    return dt.datetime.fromisoformat(m.group(1) + ("." + (m.group(2) + "000000")[:6] if m.group(2) else ""))
def reset():
    if DRY: print("DRY reset Channel 4 at", utcnow().isoformat(" ")); return "dry"
    return api("POST", f"/api/channels/{CH}/playout/reset")
def set_block(body):
    """body None = empty (off). Otherwise the one-shot INSERTS content + playout item."""
    t = open(YML).read(); shutil.copy2(YML, f"{YML}.bak-{dt.datetime.now():%Y%m%d-%H%M%S}-pickup")
    # migrate v1 markers out of the sequence (v1 put one after the first HOUSE midroll -> repeated every loop)
    t = re.sub(r"      # >>> COMMENTER_INSERTS[^\n]*\n(?:.*\n)*?      # <<< COMMENTER_INSERTS\n", "", t)
    if B0 not in t: t = t.replace("sequence:\n", f"  {B0}\n  {B1}\nsequence:\n", 1)
    if t.count(B0) < 2: t = t.replace("playout:\n", f"playout:\n  {B0}\n  {B1}\n", 1)
    blocks = [] if body is None else [
        f'- search:\n  key: "INSERTS"\n  query: "library_id:{body}"\n  order: "chronological"',
        f'- content: "PROG"\n  count: {LEAD_PROG}\n- content: "INSERTS"\n  count: 1\n- sequence: "LOOP"\n  repeat: 100000']
    parts = t.split(B0); out = parts[0]
    for i, p in enumerate(parts[1:]):
        rest = p.split(B1, 1)[1]; blk = blocks[i] if blocks else ""
        out += B0 + "\n" + "".join("  " + l + "\n" for l in blk.splitlines()) + "  " + B1 + rest
    open(YML, "w").write(out)
Q_NOW = ("select c.Name, pi.Start, pi.Finish from PlayoutItem pi join Playout p on p.Id=pi.PlayoutId join Channel ch on ch.Id=p.ChannelId "
         "left join CollectionItem ci on ci.MediaItemId=pi.MediaItemId left join Collection c on c.Id=ci.CollectionId "
         "where ch.Number=? and pi.Start<=? and pi.Finish>? order by pi.Start limit 1")
Q_NEXT_AD = ("select pi.Start, pi.Finish from PlayoutItem pi join Playout p on p.Id=pi.PlayoutId join Channel ch on ch.Id=p.ChannelId "
             "join CollectionItem ci on ci.MediaItemId=pi.MediaItemId join Collection c on c.Id=ci.CollectionId "
             "where ch.Number=? and c.Name='House Ads' and pi.Finish>? order by pi.Start limit 1")
def next_break(max_wait_s=3600):
    """End time (UTC) of the House Ad on air now, or of the next one. Never earlier than the ad's own Finish."""
    n = utcnow().isoformat(" ")
    r = db(Q_NEXT_AD, (CH, n))
    if not r: return None
    fin = P(r[0][1])
    return fin if (fin - utcnow()).total_seconds() <= max_wait_s else None
# v3 (2026-10-27 17:5x CT, Lead pick a'): ErsatzTV Next keeps a running channel session on its old playout after a reset.
# So: reset at a clean break -> wait until Next writes the new chunk -> DELETE /api/session/4 (new session reads the new build).
# The clip sits LEAD_PROG programme items (~6 s each, ~36 s) after the break to cover rebuild + session restart.
# The block ends with LOOP repeat 100000 so `repeat: true` can never re-emit the one-shot inside the build horizon (seen: 2nd copy on day 3).
LEAD_PROG = 6
NEXT = os.environ.get("PICKUP_NEXT", f"{H}/Library/Application Support/ersatztv/next/playouts/{CH}")
def next_target():
    try: return os.readlink(os.path.join(NEXT, "current"))
    except OSError: return None
def next_entries(pred, folder=None):
    """[(start, finish, path)] for items in the current Next chunks whose source path matches pred."""
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(folder or os.path.join(NEXT, "current"), "*.json"))):
        try: items = json.load(open(f)).get("items", [])
        except Exception: continue
        for i in items:
            pth = str((i.get("source") or {}).get("path", ""))
            if pred(pth): out.append((PN(i.get("start") or ""), PN(i["finish"]), pth))
    return out
def PN(s):  # Next times carry an offset -> naive UTC (the rest of pickup uses naive UTC)
    s = str(s); m = re.match(r"^(\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d)(?:\.(\d+))?(.*)$", s)
    if not m: return None
    v = dt.datetime.fromisoformat(m.group(1) + ("." + (m.group(2) + "000000")[:6] if m.group(2) else "") + m.group(3))
    return v.astimezone(dt.timezone.utc).replace(tzinfo=None) if v.tzinfo else v
def is_insert_path(pth): return ("/commenter-approved/" in pth) or ("DUMMY-" in os.path.basename(pth))
def wait_new_build(prev, timeout=15):
    if DRY: return True
    for _ in range(timeout * 2):
        if next_target() and next_target() != prev: time.sleep(1); return True
        time.sleep(0.5)
    return False
def restart_session(tag):
    if DRY: return "dry"
    try: st = api("DELETE", f"/api/session/{CH}")
    except Exception as e: st = f"err {type(e).__name__}"
    log({"state": tag, "channel": CH, "session_delete": st}); return st
def cleanup_orphans(lid, why):
    """Startup / post-retire: no insert may remain in LIB_DIR, the YAML block or the Next chunks."""
    moved = []
    for f in os.listdir(LIB_DIR):
        if f.endswith(".mp4") or f.endswith(".part"):
            shutil.move(os.path.join(LIB_DIR, f), os.path.join(AIRED, f)); moved.append(f)
    t = open(YML).read(); blk = B0 in t and any(l.strip() and not l.strip().startswith("#") for seg in t.split(B0)[1:] for l in seg.split(B1, 1)[0].splitlines())
    if blk: set_block(None)
    orphans = next_entries(is_insert_path)
    if moved or blk or orphans:
        log({"state": "orphan_cleanup", "why": why, "moved": moved, "yaml_block": blk, "chunk_entries": len(orphans)})
        if moved and not DRY: scan(lid, lambda ts: not any(m in t for t in ts for m in moved))
        if orphans and not DRY:
            prev = next_target(); reset(); wait_new_build(prev); restart_session("orphan_session_restart")
            left = next_entries(is_insert_path)
            if left: log({"state": "orphan_cleanup_incomplete", "chunk_entries": len(left)}); return False
    return True
def reset_at_break(tag):
    b = next_break()
    if not b: return None, None
    sleep_until(b + dt.timedelta(milliseconds=300))   # 0.3 s after the ad's last frame, so the ad is never cut
    on = db(Q_NOW, (CH, utcnow().isoformat(" "), utcnow().isoformat(" ")))
    prev = next_target(); st = reset()
    built = wait_new_build(prev)
    log({"state": tag, "channel": CH, "break_utc": b.isoformat(" "), "on_air_at_reset": on[0][0] if on else None, "reset": st, "next_build": next_target(), "built": built})
    return b, st
def clip_airing(lid, after):
    """First playout item from the inserts library that starts at/after the break."""
    r = db("select pi.Start, pi.Finish from PlayoutItem pi join Playout p on p.Id=pi.PlayoutId join Channel ch on ch.Id=p.ChannelId "
           "join MediaItem mi on mi.Id=pi.MediaItemId join LibraryPath lp on lp.Id=mi.LibraryPathId "
           "where ch.Number=? and lp.LibraryId=? and pi.Finish>? order by pi.Start limit 1", (CH, lid, (after - dt.timedelta(seconds=5)).isoformat(" ")))
    return (P(r[0][0]), P(r[0][1])) if r else None
def retire(cid, lid, test, aired_end=None):
    pb = retire_prompt_check(cid)
    if pb:
        set_block(None)
        if not DRY: reset_at_break("retire_reset_at_break"); restart_session("retire_session_restart")
        log({"state": "retire_refused_open_prompts", "id": cid, "reason": pb, "note": "playout block cleared; file + ledger left for CNB to close prompts", "test": test})
        return False
    hit = [f for f in os.listdir(LIB_DIR) if f.startswith(cid + "_")]
    for f in hit: shutil.move(os.path.join(LIB_DIR, f), os.path.join(AIRED, f))
    set_block(None)
    if not DRY: scan(lid, lambda ts: not any(cid in t for t in ts))
    b, st = reset_at_break("retire_reset_at_break")   # clean the playout at the NEXT ad end; one-shot block already gone
    if not DRY: restart_session("retire_session_restart"); cleanup_orphans(lid, "after_retire")
    open(LEDGER, "a").write(json.dumps({"ts": now(), "id": cid, "state": "retired", "aired_end_utc": aired_end, "test": test}) + "\n")
    log({"state": "retired", "id": cid, "moved": hit, "aired_end_utc": aired_end, "reset": st, "test": test})
def scan(lid, want, timeout=60):
    if DRY: return True
    api("POST", f"/api/libraries/{lid}/scan")
    for _ in range(timeout):
        if want(lib_titles(lid)): return True
        time.sleep(1)
    return False
def lock():
    if not os.path.isdir(HERE): sys.exit("no pickup dir")
    try: os.mkdir(LOCK)
    except FileExistsError: sys.exit("one-clip lock held (media_server/.ingest.lock); try after the current clip")

# ===== Plastic queue (CLIP-PROMOTION-PROCESS-20261027.md 18:03 + 18:05). pickup only READS Lead's QUEUE-LOAD sheet,
# LINEAGE.jsonl and CNB's comment-prompt store; every change is written as a NEW sheet version (old kept), never in place.
# default = the Mac copy kept by sync_queue.py (one-way box -> Mac; the box file is the source of truth)
QUEUE = os.environ.get("PICKUP_QUEUE", os.path.join(os.path.dirname(os.path.abspath(__file__)), f"QUEUE-LOAD-{dt.date.today():%Y%m%d}.json"))
RESERVE_TTL_MIN = 60   # 18:02 CT: a reserved slot expires 60 min after the candidate is READY (not after the reserve)
def _ts(v):
    try: x = dt.datetime.fromisoformat(str(v)); return x if x.tzinfo else x.astimezone()
    except Exception: return None
def reserve_expired(appr, at=None):
    """None = still inside the window; else reason. Counted from the candidate's ready_at (READY time)."""
    r = _ts(appr.get("ready_at"))
    if r is None: return "ready_at missing or not a timestamp (expiry is counted from READY)"
    at = at or dt.datetime.now().astimezone()
    if at - r > dt.timedelta(minutes=RESERVE_TTL_MIN): return f"reserve expired: READY at {r.isoformat(timespec='seconds')}, over {RESERVE_TTL_MIN} min ago"
    return None
SLOT_STATUS = ("RESERVED", "READY", "APPROVED", "AIRED", "MISSED", "SUPERSEDED")
SLOT_REQ = ("slot_id", "channel", "slot_lineage", "occupant_global_no", "occupant_gen", "status", "prev_id", "next_id", "prev_last_frame", "next_first_frame")
def frame_ok(v, ch): return v is None or (isinstance(v, str) and v.startswith(f"continuity/{ch}/") and len(v) > len(f"continuity/{ch}/"))
def slot_errors(sl):
    e = [f"missing {k}" for k in SLOT_REQ if k not in sl]
    if e: return e
    ch = sl["channel"]
    if isinstance(ch, bool) or not isinstance(ch, int) or ch < 1: e.append("channel not a positive int")
    if not (isinstance(sl["slot_lineage"], str) and re.match(r"^4\.[1-9][0-9]*$", sl["slot_lineage"])): e.append("slot_lineage not '4.N'")
    for k in ("occupant_global_no", "occupant_gen"):
        v = sl[k]
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 1): e.append(f"{k} not a positive int/null")
    if (sl["occupant_global_no"] is None) != (sl["occupant_gen"] is None): e.append("occupant_global_no/gen must both be set or both null")
    if sl["status"] not in SLOT_STATUS: e.append(f"status {sl['status']!r} invalid")
    if sl["status"] != "RESERVED" and sl["occupant_global_no"] is None: e.append("only a RESERVED slot may be empty")
    for k in ("prev_last_frame", "next_first_frame"):
        if not frame_ok(sl[k], ch): e.append(f"{k} not under continuity/{ch}/")
    for h in sl.get("history", []):
        if h.get("status") != "SUPERSEDED" or _num(h.get("global_no")) is None: e.append("bad history entry")
    return e
def sheet_errors(sh):
    sl = sh.get("slots")
    if not isinstance(sl, list): return ["sheet has no slots list"]
    e, ids = [], [x.get("slot_id") for x in sl if isinstance(x, dict)]
    if len(ids) != len(set(ids)) or len(ids) != len(sl): e.append("slot_id missing or duplicate")
    for x in sl:
        if not isinstance(x, dict): continue
        e += [f"{x.get('slot_id')}: {m}" for m in slot_errors(x)]
        for k in ("prev_id", "next_id"):
            if x.get(k) is not None and x[k] not in ids: e.append(f"{x.get('slot_id')}: {k} {x[k]} not a slot")
    return e
def sheet_versions(path=None):
    import glob
    base = (path or QUEUE)[:-5]
    vs = sorted(((int(m.group(1)), f) for f in glob.glob(base + ".v*.json") for m in [re.search(r"\.v(\d+)\.json$", f)] if m))
    return vs
def load_sheet(path=None):
    vs = sheet_versions(path)
    f = vs[-1][1] if vs else (path or QUEUE)
    return json.load(open(f)), f
def write_sheet(sh, why, path=None):
    """New version file next to Lead's sheet; never overwrites an existing one."""
    vs = sheet_versions(path); n = (vs[-1][0] if vs else 0) + 1
    f = (path or QUEUE)[:-5] + f".v{n}.json"
    sh = dict(sh, version=n, version_note=why, version_at=now(), version_by="commenter-pickup")
    e = sheet_errors(sh)
    if e: raise ValueError("refusing to write invalid sheet: " + "; ".join(e))
    with open(f, "x") as o: json.dump(sh, o, indent=1)
    return f
def lineage_rows(): return node_rows([json.loads(l) for l in open(LINEAGE) if l.strip()])
def chain_reaches(row, occ_gno, rows):
    by = {}
    for r in node_rows(rows):
        g = _num(r.get("global_no"))
        if g is not None: by.setdefault(g, []).append(r)
    seen, cur = set(), row
    while True:
        p = _num(cur.get("parent_global_no"))
        if p is None or p in seen: return False
        if p == occ_gno: return True
        seen.add(p)
        nxt = by.get(p, [])
        if len(nxt) != 1: return False
        cur = nxt[0]
def preempt_check(slot, row, appr, rows, at=None):
    """None = may preempt; else the refusal reason."""
    lin, gen, gno = row.get("lineage"), _num(row.get("gen")), _num(row.get("global_no"))
    for k in ("lineage", "gen", "global_no", "parent_global_no", "supersedes", "comment_prompt_ids"):
        if k not in row: return f"LINEAGE row missing {k} (18:03 requires it)"
    if not isinstance(row.get("comment_prompt_ids"), list): return "comment_prompt_ids not a list"
    if slot.get("occupant_global_no") is None: return "slot has no occupant; not a preemption (needs a RESERVED break)"
    if lin != slot.get("slot_lineage"): return f"lineage {lin} != slot {slot.get('slot_lineage')}; not a preemption, needs a new RESERVED break"
    if gen is None or gen <= slot["occupant_gen"]: return f"gen {gen} not above occupant gen {slot['occupant_gen']}"
    if gno == slot["occupant_global_no"]: return "candidate is the occupant"
    if not (_num(row.get("supersedes")) == slot["occupant_global_no"] or chain_reaches(row, slot["occupant_global_no"], rows)):
        return f"parent chain from #{gno} does not reach occupant #{slot['occupant_global_no']} and no supersedes link"
    if appr.get("status") not in ("READY", "APPROVED"): return f"candidate status {appr.get('status')!r} not READY"
    if appr.get("trundle_air_yes") is not True and appr.get("thundertrundle_air_yes") is not True: return "not APPROVED (no trundle air yes)"
    if appr.get("confirmed_clean") is not True: return "confirmed_clean not true"
    a = audio_check(appr)
    if a: return a
    return reserve_expired(appr, at)
def frame_refs(ch, gno): return f"continuity/{ch}/{gno}_first.png", f"continuity/{ch}/{gno}_last.png"
def preempt(slot_id, row, appr, insert_at_break, path=None):
    """insert_at_break() runs the (a') path (clean break, once-only, session restart, capture check) and returns
    (ok, aired_at_ct, proof). On a miss: slot -> MISSED then re-reserved for the next break (trundle's yes kept, 18:02)."""
    sh, src = load_sheet(path)
    e = sheet_errors(sh)
    if e: return False, "sheet invalid: " + "; ".join(e)
    S = {x["slot_id"]: x for x in sh["slots"]}
    if slot_id not in S: return False, f"no slot {slot_id}"
    sl = S[slot_id]
    rows = lineage_rows(); why = preempt_check(sl, row, appr, rows)
    if not why:
        P, warn = load_prompts()
        for w in warn: log({"state": "prompt_file_warning", "warn": w})
        why = prompts_block(linked_prompts(sl["occupant_global_no"], rows, P),
                            linked_prompts(_num(row["global_no"]), rows + [row], P, own=[str(x) for x in row["comment_prompt_ids"]]), P)
    if why: log({"state": "preempt_refused", "slot": slot_id, "candidate": row.get("global_no"), "reason": why}); return False, why
    ok, aired_at, proof = insert_at_break()
    if not ok:
        sl.update(status="MISSED"); write_sheet(sh, f"preempt #{row['global_no']} missed break", path)
        sl.update(status="RESERVED", reserved_at=now()); f = write_sheet(sh, f"re-reserve next break for #{row['global_no']} (trundle yes kept)", path)
        log({"state": "preempt_missed_rereserved", "slot": slot_id, "candidate": row["global_no"], "sheet": f}); return False, "missed break; re-reserved"
    g, gen = _num(row["global_no"]), _num(row["gen"])
    sl.setdefault("history", []).append({"global_no": sl["occupant_global_no"], "gen": sl["occupant_gen"], "status": "SUPERSEDED", "at": now(), "by": g,
                                          "prev_status": sl["status"], "aired_at": sl.get("aired_at"), "capture_proof": sl.get("capture_proof"),
                                          "nbr_prev_next_first": S[sl["prev_id"]]["next_first_frame"] if sl["prev_id"] in S else None,
                                          "nbr_next_prev_last": S[sl["next_id"]]["prev_last_frame"] if sl["next_id"] in S else None})
    sl.update(occupant_global_no=g, occupant_gen=gen, status="AIRED", aired_at=aired_at, capture_proof=proof,
              comment_prompt_ids=list(row["comment_prompt_ids"]))
    first, last = frame_refs(sl["channel"], g)
    if sl["prev_id"] in S: S[sl["prev_id"]]["next_first_frame"] = first
    if sl["next_id"] in S: S[sl["next_id"]]["prev_last_frame"] = last
    f = write_sheet(sh, f"preempt slot {slot_id}: #{sl['history'][-1]['global_no']} -> #{g}", path)
    log({"state": "preempted", "slot": slot_id, "old": sl["history"][-1]["global_no"], "new": g, "sheet": f}); return True, f
def rollback(slot_id, path=None):
    sh, src = load_sheet(path)
    S = {x["slot_id"]: x for x in sh["slots"]}; sl = S[slot_id]
    if not sl.get("history"): return False, "nothing to roll back"
    h = sl["history"].pop(); bad = sl["occupant_global_no"]
    sl.update(occupant_global_no=h["global_no"], occupant_gen=h["gen"], status=h.get("prev_status", "AIRED"), aired_at=h.get("aired_at"), capture_proof=h.get("capture_proof"))
    sl.pop("comment_prompt_ids", None)
    if sl["prev_id"] in S: S[sl["prev_id"]]["next_first_frame"] = h.get("nbr_prev_next_first")
    if sl["next_id"] in S: S[sl["next_id"]]["prev_last_frame"] = h.get("nbr_next_prev_last")
    sl.setdefault("rolled_back", []).append({"global_no": bad, "at": now()})
    f = write_sheet(sh, f"rollback slot {slot_id}: #{bad} -> #{h['global_no']}", path)
    log({"state": "rolled_back", "slot": slot_id, "from": bad, "to": h["global_no"], "sheet": f}); return True, f

# ===== Comment prompts (CLIP-PROMOTION-PROCESS 18:09). CNB's append-only file, synced box -> Mac by sync_queue.py.
# pickup ONLY READS it (opened "r"; no write path exists). Latest row per prompt_id wins. Missing/partial file -> warnings.
PROMPTS = os.environ.get("PICKUP_PROMPTS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "COMMENT-PROMPTS.jsonl"))
PROMPT_OPEN, PROMPT_TERMINAL = ("WAITING", "PARKED"), ("AIRED", "MERGED", "WITHDRAWN")
PROMPT_CAP = int(os.environ.get("PICKUP_PROMPT_CAP", "3"))
PROMPT_ROWS = []   # every parsed row, file order (needed for own(): origin/combined_source links)
def load_prompts(path=None):
    """Mirrors CNB comment_prompts.rows()/current(): latest row per prompt_id wins. Read-only. Unlike CNB's reader,
    a missing file or a half-written line warns instead of raising."""
    global PROMPT_ROWS
    f, warn, P, R = path or PROMPTS, [], {}, []
    if not os.path.exists(f): PROMPT_ROWS = []; return P, [f"prompt file missing: {f} (treated as empty)"]
    with open(f, "r") as fh:
        for n, l in enumerate(fh, 1):
            if not l.strip(): continue
            try: r = json.loads(l)
            except Exception: warn.append(f"line {n} unparseable (partial write?) - skipped"); continue
            if not isinstance(r, dict) or not r.get("prompt_id"): warn.append(f"line {n} has no prompt_id - skipped"); continue
            R.append(r); P[str(r["prompt_id"])] = r
    PROMPT_ROWS = R
    return P, warn
def _parents(rows):
    """CNB _parents(): first LINEAGE row per global_no; parent_global_no, else parent_no."""
    p = {}
    for r in node_rows(rows):
        g = r.get("global_no")
        if g is not None and g not in p: p[g] = r.get("parent_global_no", r.get("parent_no"))
    return p
def own_prompts(g, prows=None):
    """CNB own(): prompt ids linked to #g by an origin/combined_source row, first-seen order."""
    out = []
    for r in (PROMPT_ROWS if prows is None else prows):
        if r.get("global_no") == g and r.get("link") in ("origin", "combined_source") and str(r["prompt_id"]) not in out: out.append(str(r["prompt_id"]))
    return out
def inherited_prompts(gno, rows, prows=None):
    """CNB inherited(): self first, then each ancestor via the LINEAGE parent chain."""
    par, out, g, seen = _parents(rows), [], gno, set()
    while g is not None and g not in seen:
        seen.add(g); out += [x for x in own_prompts(g, prows) if x not in out]; g = par.get(g)
    return out
def linked_prompts(gno, rows, P, own=None):
    """inherited_prompts() plus any ids a LINEAGE row lists in comment_prompt_ids[] (self or ancestors) and the
    candidate's own list - a superset of CNB inherited(), so nothing CNB links is ever missed."""
    out = list(dict.fromkeys([str(x) for x in (own or [])] + inherited_prompts(gno, rows)))
    par, g, seen = _parents(rows), gno, set()
    while g is not None and g not in seen:
        seen.add(g)
        for r in node_rows(rows):
            if r.get("global_no") == g:
                for x in (r.get("comment_prompt_ids") or []):
                    if str(x) not in out: out.append(str(x))
        g = par.get(g)
    return out
def _ct_ts(v):
    """CNB append() rule for trundle_ts: ISO timestamp with a CT offset (-05:00 / -06:00)."""
    try: t = dt.datetime.fromisoformat(str(v or ""))
    except ValueError: return None
    return t if t.utcoffset() in (dt.timedelta(hours=-5), dt.timedelta(hours=-6)) else None
def prompt_state(pid, P):
    """(terminal?, why) on the latest row (current())."""
    p = P.get(pid)
    if p is None: return False, f"{pid}: no record in prompt file"
    st = p.get("status")
    if st == "AIRED": return True, f"{pid}: AIRED"
    if st == "WITHDRAWN":   # Lead 18:10: trundle only -> by=="trundle" AND non-empty trundle_quote AND valid trundle_ts (CNB's append rule)
        if p.get("by") not in ("trundle", "thundertrundle"): return False, f"{pid}: WITHDRAWN not by trundle (treated as open)"
        if not str(p.get("trundle_quote") or p.get("thundertrundle_quote") or "").strip(): return False, f"{pid}: WITHDRAWN without trundle_quote (treated as open)"
        if _ct_ts(p.get("trundle_ts") or p.get("thundertrundle_ts")) is None: return False, f"{pid}: WITHDRAWN with missing/invalid trundle_ts (treated as open)"
        return True, f"{pid}: WITHDRAWN by trundle"
    if st == "MERGED": return (True, f"{pid}: MERGED into {p['merged_into']}") if p.get("merged_into") else (False, f"{pid}: MERGED without merged_into")
    if st in PROMPT_OPEN: return False, f"{pid}: {st}" + (f" ({p.get('park_reason')})" if st == "PARKED" else "")
    return False, f"{pid}: status {st!r} is not an 18:09 state (treated as open)"
def unterminated(gno, rows, P):
    """CNB unterminated(): inherited prompts whose latest row is not terminal (pickup's terminal test is stricter)."""
    return [x for x in inherited_prompts(gno, rows) if not prompt_state(x, P)[0]]
def prompts_block(out_ids, keep_ids, P):
    """Refusal reason if any prompt linked to the outgoing clip would be left non-terminal and not carried by the incoming clip."""
    bad = [w for i in out_ids if i not in set(keep_ids) for t, w in [prompt_state(i, P)] if not t]
    return ("open linked prompt(s): " + "; ".join(bad)) if bad else None
def prompt_report(P):
    """skipped_breaks per open prompt; at/over the cap -> owed the next break."""
    rep = []
    for pid, p in P.items():
        if p.get("status") in PROMPT_TERMINAL: continue
        sb = _num(p.get("skipped_breaks"))
        rep.append({"prompt_id": pid, "global_no": p.get("global_no"), "status": p.get("status"), "skipped_breaks": sb,
                    "owed_next_break": sb is not None and sb >= PROMPT_CAP})
    return rep
def retire_prompt_check(cid):
    P, warn = load_prompts()
    for w in warn: log({"state": "prompt_file_warning", "warn": w})
    try: rows = lineage_rows()
    except OSError: rows = []
    g = next((_num(r.get("global_no")) for r in rows if r.get("clip_id") == cid), None)
    if g is None: return None
    return prompts_block(linked_prompts(g, rows, P), [], P)
def main():
    a = sys.argv[1:]; test = "--test" in a; a = [x for x in a if x != "--test"]
    cmd = a[0] if a else "check"
    if cmd == "check":
        for n in sorted(os.listdir(STAGED)):
            d = os.path.join(STAGED, n)
            if os.path.isdir(d): r, w = gate(d, n.startswith("DUMMY-")); print(n, "PASS" if not w else f"SKIP: {w}")
        return
    if not test and not os.path.exists(f"{HERE}/ENABLED"): sys.exit("pickup DISABLED (no ENABLED flag; needs trundle's yes)")
    if not DRY and subprocess.run(["curl", "-s", "-o", "/dev/null", "-m", "3", BASE], capture_output=True).returncode != 0:
        sys.exit("ErsatzTV not running on :8409; this tool never starts it")
    lid = lib_id()
    if not lid: sys.exit(f"library '{LIB_NAME}' missing")
    lock()
    try:
        if cmd == "insert":
            if not cleanup_orphans(lid, "startup"): sys.exit("orphan cleanup incomplete; refusing to insert")
            for n in sorted(os.listdir(STAGED)):
                d = os.path.join(STAGED, n)
                if not os.path.isdir(d): continue
                r, w = gate(d, test)
                if w: print(n, "SKIP:", w); continue
                dst = os.path.join(LIB_DIR, os.path.basename(r["_file"])); tmp = os.path.join(LIB_DIR, "." + os.path.basename(dst) + ".part")
                shutil.copy2(r["_file"], tmp); os.replace(tmp, dst)
                if sha(dst) != r["_sha"]: os.remove(dst); sys.exit("copy sha mismatch")
                open(LEDGER, "a").write(json.dumps({"ts": now(), "id": r["id"], "sha256": r["_sha"], "state": "copied", "test": test}) + "\n")
                log({"state": "approved_copied", "id": r["id"], "sha256": r["_sha"], "approval": r.get("trundle_air_yes_source") or r.get("thundertrundle_air_yes_source"), "test": test})
                if not scan(lid, lambda ts: any(t.endswith(os.path.basename(dst)) for t in ts)): sys.exit("scan did not pick up clip")
                set_block(lid)
                b, st = reset_at_break("insert_reset_at_break")
                if not b:
                    set_block(None); os.replace(dst, os.path.join(AIRED, os.path.basename(dst)))
                    log({"state": "insert_aborted_no_break", "id": r["id"], "test": test}); sys.exit("no House Ad break within 1 h; undone")
                log({"state": "queued_at_clean_break", "id": r["id"], "channel": CH, "break_utc": b.isoformat(" "), "test": test})
                air = None
                if DRY: air = clip_airing(lid, b)
                else:
                    base = os.path.basename(dst); ent = []
                    for _ in range(30):
                        ent = next_entries(lambda pth: pth.endswith(base))
                        if ent: break
                        time.sleep(0.5)
                    if len(ent) != 1:
                        log({"state": "refused_copy_count", "id": r["id"], "copies": len(ent), "test": test}); retire(r["id"], lid, test); return
                    restart_session("insert_session_restart")
                    air = (ent[0][0], ent[0][1])
                if not air:
                    log({"state": "airing_not_found", "id": r["id"], "test": test}); retire(r["id"], lid, test); return
                log({"state": "airing_scheduled", "id": r["id"], "start_utc": air[0].isoformat(" "), "finish_utc": air[1].isoformat(" "), "test": test})
                sleep_until(air[1] + dt.timedelta(seconds=2))
                log({"state": "played", "id": r["id"], "finish_utc": air[1].isoformat(" "), "test": test})
                retire(r["id"], lid, test, air[1].isoformat(" "))
                return
            print("nothing eligible")
        elif cmd == "retire":
            retire(a[1], lid, test)
    finally:
        os.rmdir(LOCK)
if __name__ == "__main__": main()
