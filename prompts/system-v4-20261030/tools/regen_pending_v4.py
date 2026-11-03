#!/usr/bin/env python3
"""Regenerate every pending (unrendered) prompt through build_prompt_v4 + hard gate. Old files are READ ONLY.
Writes ../prompts_v4/<group>/<id>.args.json + .meta.json, blocked ones to ../prompts_v4/BLOCKED/<id>.json with reasons, and ../out/DIFF.md + diff.jsonl."""
import json,os,re,sys,glob,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import build_prompt_v4 as B
import canon as C
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); E="/workspace/thunder-trundle/prompts/experiments"
OD=f"{E}/odyssey-design-20261030/ODYSSEY"; R9=f"{E}/round9-20261030"
SIDE=f"{H}/refs_side"
# Keys are canon-mapped source paths (tools/canon.py runs first); refs_side files renamed GIDEON_QUILL_* on Nov 2 2026.
REF_SWAP={f"{OD}/refs/GIDEON_QUILL_face.png":f"{SIDE}/GIDEON_QUILL_threequarter_face.png",f"{OD}/refs/GIDEON_QUILL_front.png":f"{SIDE}/GIDEON_QUILL_side_full.png",
          f"{OD}/refs/CONCIERGE_face.png":f"{SIDE}/CONCIERGE_threequarter_face.png",f"{OD}/refs/CONCIERGE_front.png":f"{SIDE}/CONCIERGE_side_full.png",
          "/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_WREN_v1.jpg":f"{SIDE}/WREN_side_full.png",
          "/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_GRAVES_ARCHIVIST_GUARD_v1.jpg":f"{SIDE}/GRAVES_guard_side_full.png",
          "TBD:ODYSSEY/refs/GIDEON_QUILL_face.png (look sheet needs trundle yes)":f"{SIDE}/GIDEON_QUILL_threequarter_face.png","TBD:ODYSSEY/refs/CONCIERGE_face.png":f"{SIDE}/CONCIERGE_threequarter_face.png"}
SENT=re.compile(r'(?<=[.!?\]"])\s+(?=[A-Z\[<(])')
INK=re.compile(r"(hand-?inked|ink outlines|crosshatch|comic|flat 2D|Never 3D|never 3D|Effects are drawn)",re.I)
CUE={"Ch2 News":"crisp anchor cadence, measured pace","Ch11 Fist Theater":"dry, deadpan","Ch8 Sitcom":"sitcom timing, slight laugh","default":"natural, conversational"}
def split_s(p):
    out=[];buf=""
    for part in SENT.split(p):
        buf=(buf+" "+part).strip() if buf else part
        if buf.count('"')%2==0 and buf.count("[")<=buf.count("]"): out.append(buf); buf=""
    if buf: out.append(buf)
    return out
def cue_dialogue(s,ch):
    c=CUE.get(ch,CUE["default"])
    return re.sub(r'(\b(?:says?|saying|said|yells?|shouts?)\b[^"]{0,40}?,? ")(?!\[)',lambda m:m.group(1)+f"[{c}] ",s)
def simplify_camera(s):
    s=re.sub(r",? then (hold|cut)[^.]*","",s); return s
def convert(cid,p,channel,start=None,refs=(),lastf=None,clip_type="beat",meta=None,eyeline=None,extra_notes=None):
    notes=[]; sp=split_s(p); look=[];setting=[];camera=[];beats=[];extra=[]
    for s in sp:
        if s.startswith("[") and s.endswith("]"): notes.append("safety bracket regenerated from pool"); continue
        if re.search(r"settles into a held still|motion carries on|no held still|clip ends exactly|eases",s,re.I): notes.append(f"ending replaced: '{s[:60]}'"); continue
        if re.match(r"(Continue|Pick up|Start exactly)",s): continue
        if channel=="Ch4 Military Boutique / BLACK ICE" and INK.search(s): notes.append("Ch4 ink lock removed -> photoreal 1971 pool"); continue
        if s.startswith("Look:") or (not look and not beats and sp.index(s)==0 and re.search(r"look|film|TV|style|video|ad\b|commercial|promo",s,re.I)): look.append(s); continue
        if s.startswith("Setting:"): setting.append(s); continue
        if re.match(r"(Single shot|Camera|Slow push-in|Tracking shot)",s) or (re.search(B.gate.ac1.CAM,s,re.I) and not s.startswith("At ")):
            c=simplify_camera(s)
            if c!=s: notes.append("camera simplified to one move (r9: multi-stage camera -> model cuts)")
            camera.append(c); continue
        if s.startswith("At "): 
            s2=cue_dialogue(s,channel)
            if s2!=s: notes.append("delivery cue added to dialogue")
            beats.append({"text":s2.rstrip(".")});continue
        if re.search(r"never (at|into) the camera|eyes (never|off)",s,re.I) and not re.search(r"<IMAGE_|\(",s):
            notes.append("bare 'never at camera' replaced by named eyeline target"); continue
        s2=cue_dialogue(s,channel)
        if s2!=s: notes.append("delivery cue added to dialogue")
        extra.append(s2)
    lock_pool=B.LOCKS.get(channel,{}).get("look_pool")
    look_override=None if lock_pool and (channel.startswith("Ch4") or not look) else (" ".join(look) if look else None)
    if channel.startswith("Ch4"): notes.append("look = Ch4 photoreal 1971 lock pool")
    elif look and lock_pool: look_override=" ".join(look)
    new_refs=[]
    for r in refs:
        if r in REF_SWAP: new_refs.append(REF_SWAP[r]); notes.append(f"ref swapped to side/3-4 crop: {os.path.basename(REF_SWAP[r])}")
        else: new_refs.append(r)
    tgt=eyeline or ("each other and the desk monitor" if channel=="Ch2 News" else "the product and each other" if clip_type=="ad" else "each other and the props in front of them")
    m=meta or {}
    spec={"clip_id":cid,"channel":channel,"duration":m.get("duration",10),"clip_type":clip_type,"look_override":look_override,
          "setting":" ".join(setting) or None,"camera":" ".join(camera) or None,"extra":extra,"beats":beats,"refs_raw":new_refs,"start_frame":start,"last_frame":lastf,
          "pinned":bool(lastf) or m.get("pinned",False),"eyeline_sentence":f"Eyelines: everyone looks at {tgt}, never into the lens; faces in profile or three-quarter.",
          "parent_clip":m.get("parent_clip"),"consequences":m.get("tier",[]),"hints_planted":m.get("hp",[]),"hints_paid":m.get("hpaid",[]),"saga":m.get("saga"),"depth":m.get("depth","D0"),
          "arc_stage":m.get("arc"),"serious":m.get("serious",False),"show":m.get("show"),"comedy_t":m.get("comedy_t")}
    if spec["start_frame"] is None and spec["refs_raw"] and "<IMAGE_0>" not in p and re.search(r"<IMAGE_1>",p) and not start: pass
    return spec,notes+(extra_notes or [])
def run_one(group,cid,old,spec,notes,log):
    out=f"{H}/prompts_v4/{group}"
    try:
        r=B.write(spec,out); new=r["args"]["prompt"]; status="OK"
    except B.GateFail as e:
        os.makedirs(f"{H}/prompts_v4/BLOCKED",exist_ok=True); r=B.build(spec,strict=False); new=r["args"]["prompt"]; status="BLOCKED"
        json.dump({"id":cid,"why":{k:v for k,v in r["report"].items() if v[0]=="FAIL"},"draft_args":r["args"],"notes":notes},open(f"{H}/prompts_v4/BLOCKED/{cid}.json","w"),indent=1)
    log.append({"group":group,"id":cid,"status":status,"old_words":len(old.split()),"new_words":len(new.split()),"changes":sorted(set(notes)),
                "fails":[k for k,v in r["report"].items() if v[0]=="FAIL"],"old":old,"new":new})
def odyssey(log):
    for f in sorted(glob.glob(f"{OD}/prompts/*.args.json")):
        cid=os.path.basename(f)[:-10]; a=json.load(open(f)); m=json.load(open(f[:-10]+".meta.json"))
        a=C.deep(a,"Ch11 Fist Theater"); m=C.deep(m,"Ch11 Fist Theater")  # canon: ch11.gideon_quill
        start=a.get("image_path"); extra=[]; plate=False
        if start and not os.path.exists(start) and not start.startswith("/"): start=f"{OD}/{start}"
        if start and not os.path.exists(start): extra.append(f"start frame pending render: {os.path.basename(start)}")
        if not start and re.search(r"tracking|dolly",a["prompt"]) and cid!="SU1" and a.get("reference_image_paths"):
            start=a["reference_image_paths"][0]; plate=True; extra.append("still-prep: set plate passed as START frame (tracking needs a real start image); also fixes old off-by-one <IMAGE_n> numbering (no start frame but slots counted from 1)")
        ct="suit_up" if cid.startswith("SU") else "fight" if cid=="NP16" else "beat" if m.get("big_change") else "breather"
        tiers=[{"id":t.split()[0] if t.startswith("CQ") else None,"text":" ".join(w for w in t.split() if not w.startswith("CQ-") and w not in ("FLASH","SCAR","MARK","LEGEND","gift")),"tier":t.split()[-1],"created_here":True} for t in m.get("tier_consequences",[])]
        refs0=[]
        for x in a.get("reference_image_paths",[]):
            if x.startswith("state_stills/"): x=f"{OD}/{x}"; extra.append(f"state still pending (made from the real last frame by ref_policy_v4.state_stills after the parent renders): {os.path.basename(x)}")
            refs0.append(x)
        a["reference_image_paths"]=refs0
        meta={"duration":a["duration"],"parent_clip":m.get("parent_clip"),"tier":tiers,
              "hp":m.get("hints_planted",[]),"hpaid":m.get("hints_paid",[]),"saga":m.get("saga"),"arc":m.get("beat"),"pinned":a.get("_odyssey",{}).get("pinned",False),"show":"THE NIGHT PORTER"}
        eye="the far end of the corridor" if cid.startswith("SU") else None
        spec,notes=convert(cid,a["prompt"],"Ch11 Fist Theater",start,a.get("reference_image_paths",[]),None,ct,meta,eye,extra)
        spec["start_is_plate"]=plate
        if cid=="SU1": notes.append("SU1: no side-on corridor start frame exists -> BLOCKED until still-prep (NP40 frame or side-on corridor plate); SU1 is at its 2-gen max, retry needs trundle's yes as new shot version")
        run_one("odyssey",cid,a["prompt"],spec,notes,log)
def round9(log):
    sys.path.insert(0,R9); import shots
    for i,s in shots.S.items():
        if not i.startswith("P"): continue
        if glob.glob(f"{R9}/clips/{i}/*.mp4"): continue
        st=s["start"]; st=shots.last(st[1:]) if st and st.startswith("@") else st
        refs=[shots.last(r[1:]) if r.startswith("@") else r for r in s["refs"]]
        lf=s["last_frame"]; lf=shots.last(lf[1:]) if lf and lf.startswith("@") else lf
        p=s["prompt"]
        if not st: p=re.sub(r"<IMAGE_(\d+)>",lambda m:f"<IMAGE_{int(m.group(1))-1}>",p)
        ch=s["channel_show"].split(" (")[0]; ch={"Ch11 Jade Hotel":"Ch11 Fist Theater"}.get(ch,ch)
        p=C.text(p,ch)  # canon layer (e.g. Ch14 cast = Vee/Onyx/Pixel)
        ct="news" if ch=="Ch2 News" and "desk" in p else "beat"
        extra=[]
        if st and not os.path.exists(st): extra.append(f"start frame pending parent render: {os.path.basename(st)}")
        if re.search(r"dashcam|helicopter|from above|gimbal",p,re.I): extra.append("special POV: must come from the start frame (r9: dashcam/aerial text ignored)")
        spec,notes=convert(i,p,ch,st,refs,lf,ct,{"parent_clip":s.get("parent")},None,extra)
        run_one("round9-starters",i,p,spec,notes,log)
def commercials(log):
    t=open(f"{E}/odyssey-design-20261030/COMMERCIALS.md").read()
    for row in re.findall(r"^\| ([0-9]+) [^|]*\| \*\*([^*]+)\*\*[^|]*\| (\d|—) \| (.*) \|$",t,re.M):
        n,name,k,body=row
        if k=="—": continue
        cid="AD-"+re.sub(r"[^A-Za-z0-9]+","-",name).strip("-")[:28]
        ch={"2":"Ch2 News","3":"Ch3 Clean Job","4":"Ch4 Military Boutique / BLACK ICE","5":"Ch5 Night Patrol","6":"Ch6 Shopping","7":"Ch7 Monster Hour","8":"Ch8 Sitcom","9":"Ch9 Iron League","10":"Ch10 Action","11":"Ch11 Fist Theater","12":"Ch12 90s","14":"Ch14 Music","16":"Ch16 DOSSIER"}[n]
        m=re.search(r'"(.*)"',body); p=m.group(1) if m else body
        notes=[]
        if "Dynapage" in name: 
            log.append({"group":"commercials","id":cid,"status":"BLOCKED","changes":["approved remake text uses @Image1/@Image2 refs not on the box + a burned super; needs its source refs (kept verbatim, not rewritten)"],"fails":["refs missing"],"old":p,"new":"","old_words":len(p.split()),"new_words":0}); continue
        if "STEVE" in p:
            p="Parody network promo, 1990s multi-camera sitcom look, a heat-lamp-lit apartment. <IMAGE_0> is STEVE as he is now (lizard man, same red bowling shirt and khakis). At 0 s STEVE walks toward the apartment door, seen from behind. At 4 s he turns side-on and slides on sunglasses, eyes on the door."
            notes+=["title card moved to post (no on-screen text rule)","costume must be carried by a state still of lizard+shirt (r9 E1 lost the shirt) - current STATE_STEVE_E1 shows no shirt -> needs a costume still"]
            refs=[f"{R9}/refs/STATE_STEVE_E1_lizard.png"]
        else: refs=[]
        p=p.replace("'","'")
        spec,n2=convert(cid,p,ch,None,refs,None,"ad",{"duration":10},None,notes)
        spec["clip_type"]="ad"
        run_one("commercials",cid,p,spec,n2,log)
def lipsync(log):
    D1L=f"{R9}/clips/D1/D1_last.png"; line="Good evening, Austin. Here is what we know tonight."
    arms=[("LS1",f'At 1 s, MARLA DEAN turns three-quarter toward RON PIKE and says, "{line}"',"plain line (cue added by v4 rule -> LS1 keeps the cue-free control via raw)"),
          ("LS2",f'At 1 s, MARLA DEAN turns three-quarter toward RON PIKE and says, "[crisp anchor cadence, slight smile, measured pace] {line}"',"native + bracket cues"),
          ("LS3",f'At 1 s, MARLA DEAN turns three-quarter toward RON PIKE and says, "[crisp anchor cadence, slight smile, measured pace] {line}" Close lavalier mic sound, quiet studio, no music',"native + cues + mic/room words"),
          ("LS4","At 1 s, MARLA DEAN turns three-quarter toward RON PIKE and speaks one short sentence, mouth clearly moving; no audio needed","muted gen for Kokoro dub")]
    for cid,beat,why in arms:
        old=f"(new in v4; NEWS-VOICE §2 {why})"
        spec={"clip_id":cid,"channel":"Ch2 News","duration":8,"clip_type":"news","serious":True,"setting":"Setting: the same bright parody news studio as <IMAGE_0>, curved blue desk.",
              "camera":"Single shot: medium two-shot, static camera, eye level.","start_frame":D1L,"refs_raw":[],"extra":["Two invented anchors: MARLA DEAN (silver bob, plum blazer) and RON PIKE (grey suit, red tie)."],
              "eyeline_sentence":"Eyelines: MARLA looks at RON, RON looks at his papers; faces three-quarter, never into the lens.","beats":[{"text":beat}],"parent_clip":"r9-D1"}
        if cid=="LS1": spec["beats"]=[{"t":1,"who":"MARLA DEAN","line":line,"cue":"neutral read"}]
        run_one("lipsync",cid,old,spec,["comedy layer OFF (serious=True) so the test isolates voice; LS1 uses a neutral cue because v4 requires a cue on every line - NEEDS TRUNDLE if he wants a true cue-free control"],log)
if __name__=="__main__":
    log=[]; odyssey(log); round9(log); commercials(log); lipsync(log)
    os.makedirs(f"{H}/out",exist_ok=True)
    with open(f"{H}/out/diff.jsonl","w") as f:
        for r in log: f.write(json.dumps(r)+"\n")
    md=["# DIFF old vs v4 (generated by tools/regen_pending_v4.py)\n",f"{sum(r['status']=='OK' for r in log)} OK, {sum(r['status']=='BLOCKED' for r in log)} BLOCKED of {len(log)}\n","| group | id | status | words old→new | what changed | gate fails |","|---|---|---|---|---|---|"]
    for r in log: md.append(f"| {r['group']} | {r['id']} | {r['status']} | {r['old_words']}→{r['new_words']} | {'; '.join(r['changes'])[:400]} | {', '.join(r['fails'])} |")
    md.append("\n## Unified word diffs\n")
    for r in log:
        if r["new"]:
            md.append(f"### {r['id']}\n```diff\n"+"\n".join(difflib.unified_diff(split_s(r['old']),split_s(r['new']),lineterm="",n=0))+"\n```")
    open(f"{H}/out/DIFF.md","w").write("\n".join(md)); print(md[1]); 
    for r in log: print(r["id"],r["status"],r["fails"])
