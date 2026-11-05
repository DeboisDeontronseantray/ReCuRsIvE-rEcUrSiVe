#!/usr/bin/env python3
"""Post-generation clean-source audit (trundle 2026-10-27 17:13 CT: rare slips are OK if caught after the fact
and added to a filter/watchlist so they don't repeat). Home-only: never renders, routes or posts.

For every LINEAGE row that is a generation (remake/mutation/etc.), checks refs, end frame and parent media.
Clean = CNB's CLEAN-SOURCES.json (global_no -> path), else the row's inline clean_source, plus starter stills in ref-index.
Tainted = built-in TAINT pattern, on the shared watchlist (re-read every check), or not in the clean map.
Slip -> clip held locally (status "held", never routed), row in live/slips.jsonl, proposal in live/watchlist-proposals.jsonl.
CNB is the ONLY writer of out-of-scope/shared/streaming/tag-slip-watchlist.jsonl and tag-slip-log.jsonl; we never touch them.
"""
import argparse, json, sys
from datetime import datetime
from pathlib import Path
import checker, yaml

HERE = Path(__file__).resolve().parent
SLIPS = HERE / "slips.jsonl"
PROPOSALS = HERE / "watchlist-proposals.jsonl"
REF_INDEX = HERE / "ref-index.yaml"
NON_GENERATIVE = {"first_render", "clean_master", "overlay_edit"}   # overlay_edit inputs are burned on purpose
END_KEYS = ("end_frame", "end_frame_source", "end_frame_mp4")

def now(): return datetime.now().astimezone().isoformat(timespec="seconds")
def _mb(): return Path(checker._norm(str(checker.MB_DIR)))

def _nodes(rows, keep_audio_post=False):
    """Lineage nodes only: drop rows with no clip_id or a non-node row_type (pulled/unpull/correction/...)."""
    return [r for r in rows if r.get("clip_id") and r.get("row_type") not in checker.NON_NODE_ROWS
            and (keep_audio_post or r.get("row_type") != "audio_post")]

def clean_map(mb=None, lineage=None):
    mb = Path(mb or _mb()); out = {}
    p = mb / "CLEAN-SOURCES.json"
    if p.is_file():
        for k, v in (json.loads(p.read_text()).get("clean_source") or {}).items(): out[int(k)] = v
    for r in _nodes(lineage if lineage is not None else checker.load_lineage(mb / "LINEAGE.jsonl")):
        if r.get("clean_source") and r["global_no"] not in out: out[r["global_no"]] = r["clean_source"]
    return out

def starter_stills(path=None):
    p = Path(path or REF_INDEX)
    if not p.is_file(): return set()
    found = set()
    def walk(x):
        if isinstance(x, dict): [walk(v) for v in x.values()]
        elif isinstance(x, list): [walk(v) for v in x]
        elif isinstance(x, str) and x.startswith("/"): found.add(checker._norm(x))
    walk(yaml.safe_load(p.read_text())); return found

def classify(path, clean, watchlist=None):
    """Return a reason string if path is tainted, else None."""
    if checker.is_tainted(path): return "built-in taint pattern (tagged/salesad/ch4badge/sales-overlay/lineage-tagged)"
    w = checker.watchlist_hit(path, watchlist)
    if w: return f"on watchlist: {w.get('reason')}"
    if checker._norm(path) not in clean: return "not in clean map"
    return None

def inputs_of(row, by_tag, by_no):
    out = [("ref", p) for p in row.get("refs") or []]
    out += [("end_frame", row[k]) for k in END_KEYS if row.get(k)]
    par = by_tag.get(row.get("parent_id")) or by_no.get(row.get("parent_global_no")) or by_no.get(row.get("parent_id"))
    if par: out.append(("parent_media", par["file"]))
    elif row.get("parent_id") is not None: out.append(("parent_media", str(row["parent_id"])))
    return out

def proposal(path, reason, found_in):
    return {"sha256": checker.file_sha256(path), "name_pattern": Path(path).name, "phash": checker.file_phash(path),
            "regex": None, "reason": reason, "found_in": found_in, "date": now(), "added_by": "story-bot (proposal; CNB to append)"}

def _append_unique(p, recs, key):
    p = Path(p); have = set()
    if p.is_file(): have = {key(json.loads(l)) for l in p.read_text().splitlines() if l.strip()}
    n = 0
    with open(p, "a") as f:
        for r in recs:
            if key(r) in have: continue
            have.add(key(r)); f.write(json.dumps(r) + "\n"); n += 1
    return n

def audit(lineage=None, mb=None, watchlist=None, dry_run=True, slips_path=None, proposals_path=None):
    mb = Path(mb or _mb()); rows = checker.load_lineage(mb / "LINEAGE.jsonl") if lineage is None else lineage
    rows = _nodes(rows, keep_audio_post=True)   # same filter as checker.resolve_clean (CNB 18:16): skip status/annotation rows
    wl = checker.load_watchlist() if watchlist is None else watchlist     # re-read on every audit
    clean = {checker._norm(v) for v in clean_map(mb, rows).values()} | starter_stills()
    by_tag = {r["tag"]: r for r in rows if r.get("tag")}; by_no = {r["global_no"]: r for r in rows if r.get("global_no") is not None}
    slips, expected, checked = [], [], 0
    for r in rows:
        if r.get("row_type") == "audio_post": continue   # leveled copies, not generative inputs
        if r.get("origin") in NON_GENERATIVE:
            if r.get("origin") == "overlay_edit": expected.append(r.get("tag"))
            continue
        for kind, p in inputs_of(r, by_tag, by_no):
            checked += 1; why = classify(p, clean, wl)
            if why: slips.append({"clip_id": r["clip_id"], "tag": r.get("tag"), "global_no": r.get("global_no"), "file": r["file"],
                                  "bad_input": p, "input_kind": kind, "reason": why, "status": "held", "ts": now()})
    unleveled = [{"clip_id": r.get("clip_id"), "tag": r.get("tag"), "warning": checker.audio_finished(r, rows)[1]}
                 for r in rows if r.get("file") and r.get("row_type") is None and not checker.audio_finished(r, rows)[0]]
    props = [proposal(s["bad_input"], f"slip: {s['reason']}", f"{s['tag']} {s['input_kind']}") for s in slips]
    res = {"rows": len(rows), "generative_rows": len(rows) - sum(r.get("origin") in NON_GENERATIVE or r.get("row_type") == "audio_post" for r in rows),
           "inputs_checked": checked, "overlay_edit_rows_skipped": len(expected), "watchlist_rows": len(wl),
           "watchlist_present": checker.WATCHLIST.is_file(), "slips": slips, "dry_run": dry_run,
           "not_finished_audio": len(unleveled), "audio_warnings": unleveled}
    if not dry_run and slips:
        res["slips_written"] = _append_unique(slips_path or SLIPS, slips, lambda x: (x["clip_id"], x["bad_input"]))
        res["proposals_written"] = _append_unique(proposals_path or PROPOSALS, props, lambda x: x["sha256"] or x["name_pattern"])
    return res

def is_held(clip_file, slips_path=None):
    """Routing must call this: a clip with a logged slip is held and never routed."""
    p = Path(slips_path or SLIPS)
    return p.is_file() and any(json.loads(l).get("file") == clip_file and json.loads(l).get("status") == "held"
                               for l in p.read_text().splitlines() if l.strip())

BAKED_DIRS = ["", "ad-overlay", "sales-overlay-20261027", "sales-overlay-B-20261027", "sales-overlay-B-in-A-layout-20261027",
              "lineage-tagged-20261027", "ch4badge-20261027"]

def baked_badge_proposals(mb=None, watchlist=None):
    """First-gen catalog clips (old badge burned in) and their overlay/tagged/ch4badge copies not already on the watchlist."""
    mb = Path(mb or _mb()); wl = checker.load_watchlist() if watchlist is None else watchlist
    have = {w.get("sha256") for w in wl if w.get("sha256")}; out = []
    for d in BAKED_DIRS:
        base = mb / d
        files = sorted(base.glob("*_parody.mp4")) if d == "" else sorted(base.rglob("*.mp4"))
        for f in files:
            sha = checker.file_sha256(f)
            if sha in have: continue
            have.add(sha)
            out.append(proposal(f, "baked old badge/overlay text (first-gen catalog clip or copy)", str(f.relative_to(mb))))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true", help="write slips/proposals (default dry-run)")
    ap.add_argument("--propose-baked", action="store_true", help="write baked-badge proposals to live/watchlist-proposals.jsonl")
    a = ap.parse_args()
    if a.propose_baked:
        props = baked_badge_proposals()
        n = _append_unique(PROPOSALS, props, lambda x: x["sha256"] or x["name_pattern"])
        print(json.dumps({"baked_candidates": len(props), "proposals_written": n}))
        sys.exit(0)
    print(json.dumps(audit(dry_run=not a.apply), indent=1))
