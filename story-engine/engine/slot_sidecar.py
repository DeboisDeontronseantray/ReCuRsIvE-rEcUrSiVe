#!/usr/bin/env python3
"""tt-slot/v1 sidecar adapter (Director, Oct 29 2026). Writes <clip>.slot.json NEXT TO a clip; never touches
queue files (those are Playout Engineer's). Fields follow coordination/QUEUE-SLOT-FORMAT-PROPOSAL-v1.md
(itself a proposal awaiting Trundle). slot_id/start_ct/daypart stay null: Playout's scheduler assigns them.
Usage: slot_sidecar.py <clip.mp4> --lineage-tag "4.13 g1 #119" [--parent-tag ..] [--branch-id ..] [--window-id ..]
       [--prompt-ids a,b] [--kind commenter-branch|show] [--first f.png --last l.png] [--channel 4]"""
import argparse, hashlib, json, os, subprocess
def probe(p):
    o = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout
    return round(float(o.strip()), 3)
def lufs(p):
    e = subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",p,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    if "Summary" not in e: return None, None
    s = e.split("Summary")[-1]; i = tp = None
    for l in s.splitlines():
        l = l.strip()
        if l.startswith("I:"): i = float(l.split()[1])
        if l.startswith("Peak:"): tp = float(l.split()[1])
    return i, tp
def build(a):
    d = probe(a.clip); i, tp = lufs(a.clip)
    sc = {"fmt": "tt-slot/v1", "fmt_status": "sidecar; proposal not yet approved", "slot_id": None, "channel": a.channel,
          "daypart": None, "start_ct": None, "dur_s": d, "dur_ok_5_8s": 5.0 <= d <= 8.2, "kind": a.kind,
          "ledger_row": None, "sha256": hashlib.sha256(open(a.clip,"rb").read()).hexdigest(), "path": os.path.abspath(a.clip),
          "lineage_tag": a.lineage_tag, "parent_tag": a.parent_tag,
          "cut_in": {"t_s": 0.0, "frame": a.first and os.path.abspath(a.first), "match_prev": None},
          "cut_out": {"t_s": d, "frame": a.last and os.path.abspath(a.last), "match_next": None, "clean_handoff": True},
          "branch": {"branch_id": a.branch_id, "parent_branch": None, "batch_window_id": a.window_id,
                     "prompt_ids": [x for x in (a.prompt_ids or "").split(",") if x]},
          "audio": {"lufs_i": i, "true_peak": tp, "pass": None if i is None else (-17 <= i <= -15 and (tp or 0) <= -1.5)},
          "status": "HELD", "protected_unaired_prompt": False, "history": []}
    out = os.path.splitext(a.clip)[0] + ".slot.json"; json.dump(sc, open(out, "w"), indent=1); return out
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for f in ["clip"]: p.add_argument(f)
    for f in ["--lineage-tag","--parent-tag","--branch-id","--window-id","--prompt-ids","--first","--last"]: p.add_argument(f)
    p.add_argument("--kind", default="show"); p.add_argument("--channel", type=int, default=4)
    print(build(p.parse_args()))
