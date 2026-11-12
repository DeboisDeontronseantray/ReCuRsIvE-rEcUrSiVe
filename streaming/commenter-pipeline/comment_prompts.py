"""comment_prompts.py - append-only comment-prompt store (trundle plastic queue 2026-10-27 18:05 CT; owner CNB).
Store: /workspace/shared/streaming/COMMENT-PROMPTS.jsonl, one JSON row per (global_no, prompt_id) link.
Never rewritten or deleted; corrections are new rows. Children inherit prompts via LINEAGE parent chain (not copied)."""
import json,os,datetime,fcntl
STORE="/workspace/shared/streaming/COMMENT-PROMPTS.jsonl"
LINEAGE="/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl"
def _now(): return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def rows():
    if not os.path.exists(STORE): return []
    return [json.loads(l) for l in open(STORE) if l.strip()]
STATUSES=("WAITING","PARKED","AIRED","MERGED","WITHDRAWN")  # 18:09 CT unified states (replaces 18:07)
TERMINAL=("AIRED","MERGED","WITHDRAWN"); SKIP_CAP=3
def append(global_no,prompt_id,prompt_text=None,source=None,handle=None,link="origin",writer="CNB",status="WAITING",merged_into=None,skipped_breaks=None,park_reason=None,**extra):
    if status=="MERGED" and merged_into is None: raise ValueError("MERGED needs merged_into")
    if status=="WITHDRAWN":
        if extra.get("by") not in ("trundle", "thundertrundle"): raise ValueError("WITHDRAWN is trundle only (pass by='trundle')")
        if not str(extra.get("thundertrundle_quote",extra.get("trundle_quote")) or "").strip(): raise ValueError("WITHDRAWN needs non-empty thundertrundle_quote")
        try: _ts=datetime.datetime.fromisoformat(str(extra.get("thundertrundle_ts",extra.get("trundle_ts")) or ""))
        except ValueError: raise ValueError("WITHDRAWN needs thundertrundle_ts as CT ISO timestamp")
        if _ts.utcoffset() not in (datetime.timedelta(hours=-5),datetime.timedelta(hours=-6)): raise ValueError("thundertrundle_ts must carry a CT offset (-05:00/-06:00)")
    if skipped_breaks is None:  # always written: prior value for this prompt, else 0
        _prev=[r for r in rows() if r.get('prompt_id')==prompt_id and r.get('skipped_breaks') is not None]
        skipped_breaks=_prev[-1]['skipped_breaks'] if _prev else 0
    skipped_breaks=min(int(skipped_breaks),SKIP_CAP)
    if status not in STATUSES: raise ValueError("status must be one of %s"%(STATUSES,))
    if status=="PARKED" and not park_reason: raise ValueError("PARKED needs park_reason")
    if global_no is None and link not in ("unassigned","status_update"): raise ValueError("global_no required")
    if link=="origin" and any(r.get("global_no")==global_no and r.get("prompt_id")==prompt_id and r.get("link")=="origin" for r in rows()): return None  # idempotent
    r={"global_no":global_no,"prompt_id":prompt_id,"prompt_text":prompt_text,"source":source,"handle":handle,
       "link":link,"status":status,"merged_into":merged_into,"skipped_breaks":skipped_breaks,"park_reason":park_reason,"written":_now(),"writer":writer,**extra}
    with open(STORE,"a") as f:
        fcntl.flock(f,fcntl.LOCK_EX); f.write(json.dumps(r,ensure_ascii=False)+"\n"); fcntl.flock(f,fcntl.LOCK_UN)
    return r
_SKIP_TYPES={"pulled","unpull","correction","clean_master_allow","duplicate_premise","audio_post"}
def _parents():
    p={}
    for l in open(LINEAGE):
        try: r=json.loads(l)
        except Exception: continue
        if r.get("row_type") in _SKIP_TYPES: continue  # status/annotation rows are not clip nodes
        g=r.get("global_no")
        if g is None or not (r.get("clip_id") or r.get("row_type")): continue  # need clip_id, or a non-excluded node row_type keyed on global_no
        if g not in p: p[g]=r.get("parent_global_no", r.get("parent_no"))
    return p
def own(global_no):
    out=[]
    for r in rows():
        if r.get("global_no")==global_no and r.get("link") in ("origin","combined_source") and r["prompt_id"] not in out: out.append(r["prompt_id"])
    return out
def current(prompt_id):
    """latest row for a prompt (status changes are appended rows; last one wins)."""
    c=[r for r in rows() if r.get("prompt_id")==prompt_id]; return c[-1] if c else None
def set_status(prompt_id,status,merged_into=None,skipped_breaks=None,park_reason=None,writer="CNB",note=None,**extra):
    cur=current(prompt_id) or {}
    return append(cur.get("global_no"),prompt_id,cur.get("prompt_text"),cur.get("source"),cur.get("handle"),
                  link="status_update",writer=writer,status=status,merged_into=merged_into,
                  skipped_breaks=cur.get("skipped_breaks",0) if skipped_breaks is None else skipped_breaks,park_reason=park_reason,note=note,**extra)
def bump_skip(prompt_id):
    cur=current(prompt_id); return set_status(prompt_id,"WAITING",skipped_breaks=(cur.get("skipped_breaks") or 0)+1,note="skipped one break")
def comment_prompt_ids(global_no): return inherited(global_no)  # value for LINEAGE comment_prompt_ids[]
def unterminated(global_no):
    """linked prompts lacking a terminal state; DE pickup refuses preempt/retire if non-empty."""
    return [p for p in inherited(global_no) if (current(p) or {}).get("status") not in TERMINAL]
def log_duplicate(prompt_id,outcome,existing_lineage=None,existing_global_no=None,new_global_no=None,note=None,writer="CNB"):
    """outcome: sibling (same 4.N lineage)|exact_copy_extra|join_lineage|combined|twist|move_channel|hold_spare. Appends a LINEAGE row_type=duplicate_premise (never drops)."""
    assert outcome in ("sibling","exact_copy_extra","join_lineage","combined","twist","move_channel","hold_spare")
    r={"row_type":"duplicate_premise","prompt_id":prompt_id,"outcome":outcome,"existing_lineage":existing_lineage,"existing_global_no":existing_global_no,
       "global_no":new_global_no,"note":note,"date":_now(),"writer":writer,"thundertrundle_air_yes":False}
    with open(LINEAGE,"a") as f:
        fcntl.flock(f,fcntl.LOCK_EX); f.write(json.dumps(r)+"\n"); fcntl.flock(f,fcntl.LOCK_UN)
    return r
def inherited(global_no):
    """prompt ids for this clip plus every ancestor (self first), via LINEAGE parent chain."""
    par=_parents(); out=[]; g=global_no; seen=set()
    while g is not None and g not in seen:
        seen.add(g); out+= [x for x in own(g) if x not in out]; g=par.get(g)
    return out
if __name__=="__main__":
    import sys
    if len(sys.argv)>2 and sys.argv[1]=="inherited": print(inherited(int(sys.argv[2])))
# 18:35 CT add-only: text-overlay split (spec 18:29). Stores gen_prompt + overlay[] on the prompt row, linked to prompt_id.
def append_split(global_no,prompt_id,prompt_text,**kw):
    import text_overlay as _to
    s=_to.split(prompt_text)
    return append(global_no,prompt_id,prompt_text,gen_prompt=s["gen_prompt"],overlay=s["overlay"],text_detected=s["text_detected"],overlay_unsure=s["unsure"],**kw)
