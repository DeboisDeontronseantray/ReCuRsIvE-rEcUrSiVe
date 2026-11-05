#!/usr/bin/env python3
"""meta_check.py <dir-or-meta.json ...> [--bundle current_meta_version] [--episode-passed] — stale-meta detector (META-REPLACEMENT §6).
STALE: sidecar meta_version/builder older than current and an episode boundary has passed. DEPRECATED: old field present (config/meta_aliases.jsonl).
CARD_DRIFT: card_versions differ from latest CHARACTERS rows. NO_VERSION: v1 sidecar without schema_version/meta_version."""
import sys,os,json,glob
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES=[json.loads(l) for l in open(f"{H}/config/meta_aliases.jsonl") if l.strip()]
FIELD_ALIASES={a["old"]:a["new"] for a in ALIASES if a["kind"]=="field"}
def latest_cards(path="fixtures/thunder-trundle/prompts/experiments/round8-prep-20261030/CHARACTERS.jsonl"):
    d={}
    if os.path.exists(path):
        for l in open(path):
            if l.strip(): r=json.loads(l); d[r["char_id"]]=r.get("card_version")
    return d
def check(side,current="system-v4-20261030",episode_passed=False,cards=None):
    f=[]; cards=cards if cards is not None else latest_cards()
    if not side.get("schema_version") or not side.get("meta_version"): f.append(("NO_VERSION",side.get("schema") or None))
    if side.get("meta_version") and side["meta_version"]!=current: f.append(("STALE" if episode_passed else "OLDER_OK_UNTIL_BOUNDARY",side["meta_version"]))
    for old,new in FIELD_ALIASES.items():
        if old in side and new not in side: f.append(("DEPRECATED",f"{old}->{new}"))
    for ch,v in (side.get("card_versions") or {}).items():
        if ch in cards and cards[ch]!=v: f.append(("CARD_DRIFT",f"{ch} {v}!={cards[ch]} -> retake state stills"))
    if "held still" in (side.get("prompt") or "") : f.append(("SUPERSEDED_WORDING","held still"))
    return f
def migrate(side):
    """read-time migration only (never rewrites the file)"""
    s=dict(side)
    for old,new in FIELD_ALIASES.items():
        if old in s and new not in s: s[new]=s.pop(old)
    return s
if __name__=="__main__":
    a=[x for x in sys.argv[1:] if not x.startswith("--")]; cur=next((x.split("=")[1] for x in sys.argv if x.startswith("--bundle=")),"system-v4-20261030")
    files=[]
    for x in a: files+=glob.glob(f"{x}/**/*.meta.json",recursive=True) if os.path.isdir(x) else [x]
    out={}
    for p in files:
        r=check(json.load(open(p)),cur,"--episode-passed" in sys.argv)
        if r: out[p]=r
    print(json.dumps({"files":len(files),"flagged":len(out),"by_kind":{k:sum(1 for v in out.values() for x in v if x[0]==k) for k in {x[0] for v in out.values() for x in v}}},indent=1))
