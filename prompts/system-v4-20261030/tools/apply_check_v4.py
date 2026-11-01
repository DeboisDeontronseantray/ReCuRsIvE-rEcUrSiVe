#!/usr/bin/env python3
"""apply_check_v4 — HARD gate used inside build_prompt_v4 (build fails on any FAIL). Imports odyssey tools/apply_check.py A1-A15 read-only and adds V1-V16.
CLI: apply_check_v4.py args.json [meta.json]"""
import re,sys,os,json,importlib.util
def _cimg_on():
    import json as _j,os as _o
    try: return bool(_j.load(open(_o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),"config","commenter_images.json"))).get("enabled"))
    except Exception: return False
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AC1=os.environ.get("TT_ODYSSEY_APPLY_CHECK","/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py")
if not os.path.exists(_AC1): _AC1=os.path.join(os.path.dirname(H),"experiments","odyssey-design-20261030","tools","apply_check.py")
_s=importlib.util.spec_from_file_location("ac1",_AC1)
ac1=importlib.util.module_from_spec(_s); _s.loader.exec_module(ac1)
LOCKS=json.load(open(f"{H}/config/channel_locks.json"))
CH4="Ch4 Military Boutique / BLACK ICE"
TRACK=r"\b(tracking|dolly|leading the subject|matched pace|at (exactly )?his pace|at walking pace)\b"
SPECIAL_POV=r"\b(dashcam|dash-cam|helicopter|aerial|drone|security[- ]feed|cctv|bodycam|overhead view|from above)\b"
BIGCAM=r"\b(whip pan[^.]*then|cuts? to|camera (?:then )?switches|then (?:hold|cut)|from .* to a security feed)\b"
REQ_SIDE=["schema_version","meta_version","builder","clip_id","parent_clip","tier_consequences","beats","hints_planted","hints_paid","saga","depth"]
def check_v4(p,args=None,spec=None,side=None):
    args=args or {}; spec=spec or {}
    r=ac1.check(p,side,spec.get("pinned",False),spec.get("skills_used",()))
    r.pop("A2_one_move",None)
    refs=args.get("reference_image_paths",[]) or []
    ch=spec.get("channel","")
    # V1 ending rule
    r["V1_end_motion"]=("PASS" if spec.get("pinned") or "motion carries on through the last half second" in p.lower() else "FAIL",)
    # V2 channel lock (Ch4 = photoreal 1971; no ink words, no ink refs)
    if ch==CH4 or "BLACK ICE" in p:
        L=LOCKS[CH4]; bad_t=re.search(L["forbidden_regex"],p,re.I); bad_r=[x for x in refs+[args.get("image_path") or ""] if re.search(L["forbidden_ref_regex"],x)]
        r["V2_ch4_photoreal"]=("FAIL" if bad_t or not re.search(r"photoreal|live[- ]action|real photography|photographed",p,re.I) else "PASS",)
        r["V2b_ch4_refs"]=("FAIL" if bad_r else "PASS",len(bad_r))
    # V3 no viewer-facing front refs (SU1 pilot: front sheet pulled head-on, toward the lens)
    fr=[x for x in refs if re.search(r"(_front|front_|_sheet|SHEET_)",os.path.basename(x),re.I)]
    r["V3_no_front_refs"]=("FAIL" if fr else "PASS",len(fr))
    # V4 tracking / special POV needs a real start frame (SU1 pilot; r9 dashcam/aerial ignored)
    if re.search(TRACK,p,re.I) or re.search(SPECIAL_POV,p,re.I):
        r["V4_start_frame_for_camera"]=("PASS" if args.get("image_path") else "FAIL",)
    # V5 exactly one camera move, no multi-stage camera (r9: big camera changes -> model cuts)
    n=len(re.findall(ac1.CAM,p,re.I)); r["V5_one_move"]=("FAIL" if n>2 or re.search(BIGCAM,p,re.I) else "PASS",n)
    # V6 eyeline target named (never-at-camera alone failed in SU1)
    r["V6_eyeline_target"]=("PASS" if re.search(r"\b(look(s)? at|eyes on|eyelines?:)\s",p,re.I) else "FAIL",)
    # V7 dialogue has bracket delivery cue
    lines=re.findall(r"\b(?:says?|saying|said|yells?|shouts?)\b[^\"]{0,40}?,? \"([^\"]*)\"",p)
    r["V7_dialogue_cues"]=("FAIL" if any(not l.startswith("[") for l in lines) else "PASS",len(lines))
    # V8 sidecar v2 complete
    if side is not None:
        miss=[k for k in REQ_SIDE if k not in side]; r["V8_sidecar_v2"]=("FAIL" if miss or side.get("schema_version")!="tt-clipmeta/v2" else "PASS",miss)
    # V9 ref present -> <=3 keys per character
    over=[m for m in re.findall(r"\(<IMAGE_\d+>[^)]*\)",p) if m.count(",")>3]
    r["V9_keys_only"]=("FAIL" if over else "PASS",len(over))
    # V10 news comedy present on Ch2 news, sized up
    if ch=="Ch2 News" and spec.get("clip_type")=="news" and not spec.get("serious"):
        r["V10_news_comedy"]=("PASS" if "clearly visible in frame" in p else "FAIL",)
    # V11 FC labeling: Ch4 cast/refs must be labeled Ch4
    if re.search(r"\b(HERON|WOLFHOUND)\b",p) and ch!=CH4: r["V11_label"]=("FAIL","HERON/WOLFHOUND clip not labeled Ch4")
    # V12 fight beats use the FC2/FC3 contact grammar
    fb=[b for b in spec.get("beats",[]) if b.get("move")]
    if fb: r["V12_fight_grammar"]=("PASS" if p.count("travels toward the lens and lands")>=len(fb) else "FAIL",)
    # V13 commenter refs filtered, labeled non-likeness
    for cr in spec.get("commenter_refs",[]):
        if not cr.get("filtered") or cr.get("purpose") in ("identity","face","person"): r["V13_commenter_ref"]=("FAIL",cr.get("path"))
    # V17 commenter images NOT YET (Trundle 10:48 PM CT Oct 30, config/commenter_images.json)
    if spec.get("commenter_refs") and not _cimg_on(): r["V17_commenter_images_not_yet"]=("FAIL",len(spec["commenter_refs"]))
    # V14 transforms carry costume via state still (r9 E1 lizard lost his shirt)
    if spec.get("clip_type")=="transform_after":
        r["V14_transform_still"]=("PASS" if spec.get("state_stills") else "FAIL",)
    # V15 unpaid fixed-thread placeholders / no TBD refs
    r["V15_no_tbd"]=("FAIL" if any("TBD" in x for x in refs) else "PASS",)
    # V16 one take, no cut words
    r["V16_no_cut_words"]=("FAIL" if re.search(r"\b(montage|split screen|cut to|smash cut)\b",p,re.I) else "PASS",)
    return r
if __name__=="__main__":
    a=json.load(open(sys.argv[1])); s=json.load(open(sys.argv[2])) if len(sys.argv)>2 else None
    res=check_v4(a["prompt"],a,{"channel":(s or {}).get("channel_show","").split(" / ")[0] if s else ""},s)
    for k,v in res.items(): print(k,*v)
    sys.exit(1 if any(v[0]=="FAIL" for v in res.values()) else 0)
