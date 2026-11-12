#!/usr/bin/env python3
"""Ch4 commenter-prompt pipeline (Commercial News Break). Home-only.
Stages: intake -> gate -> wrap -> render (guarded) -> post -> outbox manifest.
Usage: pipeline.py intake|gate|wrap|render [--dry-run] [--id ID]|post --id ID --src MP4|run-all --dry-run
"""
import json,os,re,sys,glob,uuid,base64,subprocess,datetime,zoneinfo,argparse,shutil,time
import owner_denylist
D=os.path.dirname(os.path.abspath(__file__)); CT=zoneinfo.ZoneInfo("America/Chicago")
CFG=json.load(open(f"{D}/config.json")); BL=owner_denylist.load_blocklists(f"{D}/blocklists.json")
now=lambda: datetime.datetime.now(CT).isoformat(timespec="seconds")
def log(name,obj): open(f"{D}/logs/{name}.jsonl","a").write(json.dumps({"time":now(),**obj})+"\n")
CAST={"bill":("Bill","bill-B2","calm, dry, slow visible fuse (fidgets, stretches, forehead veins); sleeves on, glasses on; rare eruptions are post audio only"),
 "mira":("Mira","mira-C","locked look C"),"osmund":("Osmund","osmund-B","locked look B"),
 "tim":("Tim","tim-E5","locked look E5; always carries his cargo pack")}
OOC=r"\b(dance|dances|dancing|sing|sings|singing|rap|raps|cry|cries|crying|scream|screams|tantrum|juggle|juggles|twerk|cartwheel|flirt|flirts|giggle|giggles|hug everyone|ballet|yodel)\b"
def refs_for(k):
    base=CAST[k][1]; r=CFG["refs_dir"]
    return [p for p in [f"{r}/{base}.png",f"{r}/{base}-full.png",f"{r}/{base}-side.png",f"{r}/{base}-sideback.png"] if os.path.exists(p)]
# ---------- clean-master input guard (trundle 2026-10-27 17:09 CT): tagged/air copies never feed a mutation
LINEAGE_FILES=["/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl"]
BAD_NAME=re.compile(r"(_tagged|_tagfade|salesad|ch4badge|preair|_HELD|overlay)",re.I)
BAD_DIR=re.compile(r"(^|/)(held|lineage-tag(?:ged|fade)-[^/]*)(/|$)",re.I)
import hashlib
def _sha(f):
    h=hashlib.sha256()
    with open(f,"rb") as fh:
        for b in iter(lambda: fh.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def _tainted_shas():
    out=set()
    for lf in LINEAGE_FILES:
        if not os.path.isfile(lf): continue
        for ln in open(lf):
            try: r=json.loads(ln)
            except Exception: continue
            if r.get("sha256") and (r.get("origin")=="overlay_edit" or r.get("role")=="air_copy" or r.get("air_copy")): out.add(r["sha256"])
    return out
def input_guard(path):
    """Return None if path is a clean source, else a reason string. Applies to refs, end frames, stills, i2v inputs."""
    ap=os.path.realpath(path); name=os.path.basename(path)
    for nm in {name,os.path.basename(ap)}:
        if BAD_NAME.search(nm): return f"tagged/air-copy filename: {nm}"
    for d in {os.path.dirname(os.path.abspath(path)),os.path.dirname(ap)}:
        if BAD_DIR.search(d+"/"): return f"held/tagged folder: {d}"
    if os.path.isfile(ap) and _sha(ap) in _tainted_shas(): return f"sha256 matches LINEAGE overlay_edit/air_copy row: {name}"
    return None
def guard_list(paths,held):
    ok=[]
    for x in paths:
        why=input_guard(x)
        if why: held.append({"path":x,"reason":why}); log("input_guard",{"path":x,"reason":why})
        else: ok.append(x)
    return ok
def extract_last_frame(src,out,held):
    why=input_guard(src)
    if why: held.append({"path":src,"reason":why}); log("input_guard",{"path":src,"reason":why}); return None
    subprocess.run(["ffmpeg","-y","-loglevel","error","-sseof","-0.1","-i",src,"-frames:v","1",out])
    return out if os.path.isfile(out) else None
# ---------- 1 intake
REQ=["handle","text","timestamp","source_post_id"]
def intake_legacy():  # RETIRED 2026-10-27 16:45 CT (raw comments); kept, gated by RAW_INTAKE_ENABLED
    out=[]
    files=sorted(glob.glob(f"{D}/inbox/*.json"))
    for f in files:
        try: items=json.load(open(f)); items=items if isinstance(items,list) else [items]
        except Exception as e: log("intake",{"file":f,"error":str(e)}); continue
        for it in items:
            miss=[k for k in REQ if not it.get(k)]
            if miss: log("intake",{"file":f,"error":"missing "+",".join(miss)}); continue
            it.setdefault("id","cp-"+uuid.uuid4().hex[:8]); it["handle"]="@"+it["handle"].lstrip("@"); out.append(it)
        os.makedirs(f"{D}/inbox/processed",exist_ok=True); shutil.move(f,f"{D}/inbox/processed/"+os.path.basename(f))  # move, never delete
    return out
import hashlib
def _ids_in(path,keys):
    out=set()
    if os.path.exists(path):
        for l in open(path):
            try: r=json.loads(l)
            except: continue
            for k in keys:
                if r.get(k): out.add(str(r[k]))
    return out
def credit_fallback():
    try:
        t=open(CFG["credit_fallback_file"]).read(); m=re.search(r"## Credit line[^\n]*\n`([^`]+)`",t); return m.group(1) if m else None
    except Exception: return None
def intake():
    cfg=json.load(open(f"{D}/config.json"))
    if cfg.get("RAW_INTAKE_ENABLED"): return intake_legacy()
    seen=_ids_in(f"{D}/logs/seen.jsonl",["id","source_post_id"])|_ids_in(f"{D}/outbox/manifest.jsonl",["id","source_post_id"])
    for f in glob.glob(f"{D}/inbox/processed/xls-*.json"):
        try: r=json.load(open(f)); seen|={str(r.get("id")),str(r.get("source_post_id"))}
        except Exception: pass
    out=[]; os.makedirs(f"{D}/inbox/processed",exist_ok=True)
    def reject(f,why,rec=None):
        dst=f"{D}/rejected/"+os.path.basename(f)
        if os.path.exists(dst): dst=dst[:-5]+"-"+uuid.uuid4().hex[:4]+".json"
        shutil.move(f,dst); log("intake",{"file":os.path.basename(f),"rejected":why,"moved_to":dst}); print("INTAKE-REJECT",os.path.basename(f),"->",why)
    for f in sorted(glob.glob(f"{D}/inbox/*.json")):
        b=os.path.basename(f)
        if not re.fullmatch(r"xls-[A-Za-z0-9_]+-[A-Za-z0-9_]+\.json",b): reject(f,"filename not xls-<source>-<message_id>.json"); continue
        try: r=json.load(open(f))
        except Exception as e: reject(f,"bad json: "+str(e)); continue
        miss=[k for k in REQ if not r.get(k)]
        if miss: reject(f,"missing "+",".join(miss)); continue
        if r.get("intake_by")!=cfg["required_intake_by"]: reject(f,f"intake_by={r.get('intake_by')!r}, need 'Story Bot'"); continue
        if not (r.get("approved_by") and r.get("approved_at")): reject(f,"missing approved_by/approved_at"); continue
        am=cfg["approved_markers"]
        if not (r.get("status") in am["status"] or r.get("thundertrundle_approved",r.get("trundle_approved")) is True or (r.get("status")=="AUTO_APPROVED" and cfg.get("AUTO_APPROVE_PROMPTS") is True and not cfg.get("KILL_SWITCH"))): reject(f,"no trundle-approved marker (status APPROVED/IN_STORY or thundertrundle_approved:true)"); continue
        if r.get("commenter_text_sha256") and hashlib.sha256(r["text"].encode()).hexdigest()!=r["commenter_text_sha256"]: reject(f,"verbatim text sha256 mismatch"); continue
        r["approved_by"]="auto-gate" if r.get("status")=="AUTO_APPROVED" else "trundle"
        r.setdefault("id",b[4:-5])
        if str(r["id"]) in seen or str(r["source_post_id"]) in seen:
            dst=f"{D}/inbox/processed/dup-"+uuid.uuid4().hex[:4]+"-"+b; shutil.move(f,dst); log("intake",{"file":b,"skipped":"duplicate","id":r["id"],"source_post_id":r["source_post_id"]}); print("INTAKE-DUP   ",b,"-> skipped (already seen)"); continue
        r["handle"]="@"+r["handle"].lstrip("@"); r["credit_line_resolved"]=(r["credit_line"].replace("@handle",r["handle"]) if r.get("credit_line") else None)
        seen|={str(r["id"]),str(r["source_post_id"])}
        open(f"{D}/logs/seen.jsonl","a").write(json.dumps({"time":now(),"id":r["id"],"source_post_id":r["source_post_id"],"file":b})+"\n")
        shutil.move(f,f"{D}/inbox/processed/"+b); out.append(r)
    return out
# ---------- 2 gate
def gate(p):
    t=" "+p["text"].lower()+" "
    for cat,words in BL.items():
        for w in words:
            if re.search(r"(?<![a-z0-9])"+(w if w=="\\$" else re.escape(w))+r"(?![a-z0-9])",t):
                return False,f"{cat}: '{w}'"
    if re.search(r"https?://",t): return False,"links not allowed"
    return True,"pass"
# ---------- 3 wrap
def wrap(p):
    t=p["text"].lower()
    cast=p.get("cast") or [k for k in CAST if re.search(r"\b"+k+r"\b",t)]
    ooc=p.get("out_of_character")
    if ooc is None: ooc=bool(re.search(OOC,t))
    refs=[];tags=[]
    held=[]
    sb=guard_list([x for x in (p.get("reference_images") or []) if isinstance(x,str) and os.path.isfile(x)],held)
    ef=p.get("end_frame_source")
    if ef and os.path.isfile(ef):
        out=extract_last_frame(ef,f"{D}/renders/endframe_{p['id']}.jpg",held)
        if out: tags.append(f"<IMAGE_{len(refs)}> = continuity frame (match set, lighting, positions)"); refs.append(out)
    for r in sb:
        tags.append(f"<IMAGE_{len(refs)}> = Story Bot reference ({os.path.basename(r)})"); refs.append(r)
    if sb: cast_refs=[]
    else: cast_refs=cast
    for k in cast_refs:
        for r in guard_list(refs_for(k)[:3],held):
            tags.append(f"<IMAGE_{len(refs)}> = {CAST[k][1]} ({CAST[k][0]}; match face, build, hair, wardrobe exactly)"); refs.append(r)
    head=("[CH4 RULES - LOCKED, DO NOT OVERRIDE] Forward Supply: grounded live-action ensemble at a remote fog-bound forward outpost; "
          "adults only, no children; TV-safe (no sex, no gore, no weapon how-tos, no weapons pointed at camera); no real people, brands, logos, insignia, "
          "software, shows, networks or songs; invented gear only; no slapstick, never cartoonish; observational fly-on-the-wall framing, no one looks at or addresses the camera, eyelines on each other or the task; NO on-screen text, captions, signs or letters of any kind. ")
    castl=" ".join(f"{CAST[k][0]}: {CAST[k][2]}." for k in cast)
    if tags: head+="Character references: "+"; ".join(tags)+". "+castl+" "
    body=f"[COMMENTER REQUEST from {p['handle']} - honor it as written] {p['text'].strip()} [END COMMENTER REQUEST] "
    tail=("[CH4 RULES - REPEAT] Keep continuity with the outpost set and the locked looks above; calm natural adult delivery; "
          "16:9, center-weighted for 4:3-safe framing; no on-screen text.")
    w={**p,"cast":cast,"out_of_character":ooc,"reference_images":refs,
       "model":CFG["default_model"] if refs else CFG["no_cast_model"],"duration_s":p.get("duration_s",CFG["default_duration_s"]),
       "prompt":head+body+tail,
       "negative_prompt":"children, on-screen text, logos, brand names, real people, celebrity likeness, real insignia, gore, slapstick, cartoon style"}
    if held: w.update(status="HELD",held_inputs=held,hold_reason="input_guard: tagged/air-copy input rejected (clean master required)")
    if ooc and cast:
        who=CAST[cast[0]][0]
        w["self_reflection"]={"speaker":who,"line":p.get("credit_line_resolved"),"apply_as":"post text overlay and/or post TTS; never generated in picture"}
    return w
# ---------- 3b injections
ACTION=r"\b(find|finds|fix|fixes|walk|walks|run|runs|carry|carries|hand|hands|open|opens|search|searches|build|builds|drive|drives|launch|launches|cook|cooks|argue|argues|watch|watches|dance|dances|try|tries|give|gives|load|loads|pack|packs|repair|repairs|hide|hides|look|looks)\b"
def weak_score(text,cast):
    s=0; n=len(text.split())
    if n<6: s+=1
    if n<3: s+=1
    if not cast: s+=1
    if not re.search(ACTION,text.lower()): s+=1
    return s
def pick_injections(w,clip_no):
    cfg=json.load(open(f"{D}/config.json"))
    if not cfg.get("INJECTIONS_ENABLED"): return []
    lib=json.load(open(f"{D}/injections.json"))["injections"]; cast=w["cast"]; sc=w["weak_score"]; out=[]
    def ok(i):
        if i["requires_people"] and not cast: return False
        if i["kind"]=="spoken_line" and i["speakers"]!=["voice_of_forward"] and not cast: return False
        if i["speakers"] and i["speakers"]!=["voice_of_forward"] and i["requires_people"] and not set(i["speakers"])&set(cast+(["osmund","tim"] if i["kind"]=="visual_beat" else [])): return False
        return True
    for i in w.get("manual_injections",[]):
        m=[x for x in lib if x["id"]==i and x["status"].startswith("draft") or x["id"]==i and x["status"]=="approved"]; out+= [x for x in m if ok(x)]
    if clip_no % cfg["inject_every_nth"]==0: out+=[x for x in lib if x["apply_when"]=="every_nth" and ok(x) and not x["status"].startswith("blocked")][:1]
    if sc>=cfg["weak_score_threshold"]:
        cands=[x for x in lib if x["apply_when"]=="weak_score" and ok(x) and not x["status"].startswith("blocked")]
        k=(sum(map(ord,w["id"])))%max(len(cands),1)  # deterministic rotation
        out+=cands[k:]+cands[:k]
    seen=[];res=[]
    for x in out:
        if x["id"] not in seen: seen.append(x["id"]); res.append(x)
    return res[:cfg["max_injections_per_clip"]]
def apply_injections(w,clip_no=1):
    w["weak_score"]=weak_score(w["text"],w["cast"]); inj=pick_injections(w,clip_no); w["injections"]=[]; w["post_tts_cues"]=[]; w["post_overlays"]=[]
    vis=[]
    for x in inj:
        rec={"id":x["id"],"kind":x["kind"],"delivery":x["delivery"],"status":x["status"]}
        if x["delivery"]=="in_prompt_soft": vis.append(x["text"])
        elif x["delivery"]=="post_tts":
            spk=next((c for c in x["speakers"] if c in w["cast"]),x["speakers"][0] if x["speakers"] else None)
            w["post_tts_cues"].append({"injection":x["id"],"character":spk,"line":x["text"],"timing":"last 2.5 s" if spk!="voice_of_forward" else "first 2 s","voice":"TBD-trundle"})
        else: w["post_overlays"].append({"injection":x["id"],"text":x["text"].replace("{handle}",w["handle"]),"timing":"1.0-3.5 s"})
        w["injections"].append(rec)
    if vis:
        w["prompt"]=w["prompt"].replace(" [CH4 RULES - REPEAT]"," [CHANNEL INJECTION - optional, in addition to the request, never replacing it] "+" ".join(vis)+" [END CHANNEL INJECTION] [CH4 RULES - REPEAT]")
    log("injections",{"id":w["id"],"weak_score":w["weak_score"],"injections":w["injections"],"post_tts_cues":w["post_tts_cues"],"post_overlays":w["post_overlays"]})
    return w
# ---------- 4 render (guards)
PRICE={"grok-imagine-video-1.5-lite":(0.02,0.0),"grok-imagine-video-1.5":(0.08,0.01),"grok-imagine-video":(0.05,0.002)}
def est(w): ps,pi=PRICE[w["model"]]; return round(ps*w["duration_s"]+pi*len(w["reference_images"]),4)
def xai_month_spend():
    m=datetime.datetime.now(CT).strftime("%Y-%m"); s=0.0
    for l in open(CFG["spend_log"]):
        try: j=json.loads(l)
        except: continue
        if str(j.get("provider","")).startswith("xai") and str(j.get("time","")).startswith(m): s+=float(j.get("cost_usd") or 0)
    return round(s,2)
def tries(cid): 
    f=f"{D}/logs/render.jsonl"
    return sum(1 for l in open(f) if json.loads(l).get("id")==cid and json.loads(l).get("api_called")) if os.path.exists(f) else 0
# ---------- auto-mode safety
SESS=f"{D}/logs/session.jsonl"
def sess_rows():
    sid=json.load(open(f"{D}/config.json"))["SESSION_ID"]
    return [j for j in (json.loads(l) for l in open(SESS)) if j.get("session")==sid] if os.path.exists(SESS) else []
def sess_add(kind,**k): open(SESS,"a").write(json.dumps({"time":now(),"session":json.load(open(f"{D}/config.json"))["SESSION_ID"],"kind":kind,**k})+"\n")
def safety_stop(e):
    c=json.load(open(f"{D}/config.json"))
    if c.get("KILL_SWITCH"): return "STOP: KILL_SWITCH on"
    rows=sess_rows(); spent=sum(x.get("usd",0) for x in rows if x["kind"]=="render")
    if spent+e>c["SESSION_SPEND_CAP_USD"]: return f"STOP: session spend ${spent:.2f}+${e} > cap ${c['SESSION_SPEND_CAP_USD']}"
    hr=datetime.datetime.now(CT)-datetime.timedelta(hours=1)
    n=sum(1 for x in rows if x["kind"]=="render" and datetime.datetime.fromisoformat(x["time"])>hr)
    if n>=c["MAX_CLIPS_PER_HOUR"]: return f"STOP: {n} clips in last hour >= MAX_CLIPS_PER_HOUR {c['MAX_CLIPS_PER_HOUR']}"
    return None
def auto_revert_check():
    c=json.load(open(f"{D}/config.json")); flags=sum(1 for x in sess_rows() if x["kind"]=="flag")
    if flags>=c["AUTO_REVERT_FLAG_LIMIT"] and (c.get("AUTO_APPROVE_PROMPTS") or c.get("AUTO_AIR_YES")):
        shutil.copy(f"{D}/config.json",f"{D}/config.json.bak-autorevert-"+datetime.datetime.now(CT).strftime("%Y%m%d-%H%M%S"))
        c["AUTO_APPROVE_PROMPTS"]=False; c["AUTO_AIR_YES"]=False; json.dump(c,open(f"{D}/config.json","w"),indent=1)
        log("auto_revert",{"flags":flags,"action":"AUTO_APPROVE_PROMPTS=false, AUTO_AIR_YES=false"}); print("AUTO-REVERT: %d flagged clips -> both auto switches set false"%flags)
def render(w,dry):
    e=est(w); spent=xai_month_spend(); proj=round(spent+e,2); cap=CFG["xai_monthly_cap_usd"]
    r={"id":w["id"],"model":w["model"],"est_usd":e,"xai_month_spent":spent,"projected":proj,"dry_run":dry,"api_called":False}
    if proj>cap: r["status"]="STOP: would pass xAI cap $%s"%cap; log("render",r); return r
    if proj>=CFG["xai_warn_usd"]: r["warn"]=f"projected ${proj} >= warn ${CFG['xai_warn_usd']}"
    if tries(w["id"])>=CFG["max_tries_per_clip"]: r["status"]="STOP: max 2 tries used"; log("render",r); return r
    if w.get("status")=="HELD": r["status"]="HELD: "+w.get("hold_reason","input guard"); r["held_inputs"]=w.get("held_inputs"); log("render",r); return r
    _h=[]; guard_list(list(w.get("reference_images") or [])+([w["i2v_input"]] if w.get("i2v_input") else []),_h)
    if _h: r["status"]="HELD: input_guard"; r["held_inputs"]=_h; log("render",r); return r
    stop=safety_stop(e)
    if stop: r["status"]=stop; log("render",r); return r
    if dry: r["status"]="dry-run: no API call"; sess_add("render",id=w["id"],usd=e,dry=True); log("render",r); return r
    if not json.load(open(f"{D}/config.json")).get("LIVE_ENABLED"): r["status"]="REFUSED: LIVE_ENABLED=false (trundle must flip it)"; log("render",r); return r
    import requests  # real path, same calls as render_clip_v2.py; one try, no auto retry
    imgs=[]
    for p in w["reference_images"]:
        s=f"{D}/renders/refs_small_{os.path.basename(p)[:-4]}.jpg"
        if not os.path.exists(s): subprocess.run(["ffmpeg","-y","-v","error","-i",p,"-vf","scale='min(768,iw)':-2","-q:v","3",s],check=True)
        imgs.append({"url":"data:image/jpeg;base64,"+base64.b64encode(open(s,"rb").read()).decode()})
    body={"model":w["model"],"prompt":w["prompt"]+" Avoid: "+w["negative_prompt"],"duration":w["duration_s"],"resolution":CFG["resolution"],"aspect_ratio":"16:9"}
    if imgs: body["reference_images"]=imgs
    H={"Authorization":"Bearer "+os.environ["XAI_API_KEY"],"Content-Type":"application/json"}
    r["api_called"]=True
    q=requests.post("https://api.x.ai/v1/videos/generations",headers=H,json=body,timeout=180)
    if q.status_code>=300: r["status"]=f"submit failed {q.status_code}"; log("render",r); return r
    rid=q.json()["request_id"]
    while True:
        time.sleep(6); j=requests.get("https://api.x.ai/v1/videos/"+rid,headers=H,timeout=60).json()
        if j.get("status") in("done","failed","expired"): break
    usd=e if j["status"]=="done" else 0.0
    if j["status"]=="done":
        fn=f"{D}/renders/{w['id']}_480p_{w['model']}_parody.mp4"; open(fn,"wb").write(requests.get(j["video"]["url"],timeout=300).content); r["file"]=fn
    r.update(status=j["status"],request_id=rid,cost_usd=usd)
    open(CFG["spend_log"],"a").write(json.dumps({"time":now(),"prompt_id":"ch04-commenter-pipeline","provider":"xai_imagine","model":w["model"],"cost_usd":usd,"clip":w["id"],"task":f"ch04 commenter clip {w['id']} {w['handle']}","request_id":rid,"source":"list-price estimate (480p)","channel":4})+"\n")
    sess_add("render",id=w["id"],usd=usd,dry=False); log("render",r); return r
# ---------- 5 post
def ocr_text(mp4):
    tmp=f"/tmp/ocr_{uuid.uuid4().hex[:6]}"; os.makedirs(tmp)
    subprocess.run(["ffmpeg","-v","error","-i",mp4,"-vf","fps=1","-q:v","2",f"{tmp}/f%03d.jpg"],check=True)
    hits=[]
    for f in sorted(glob.glob(f"{tmp}/*.jpg")):
        o=subprocess.run(["tesseract",f,"-","--psm","11"],capture_output=True,text=True).stdout
        words=[x for x in re.findall(r"[A-Za-z]{5,}",o)]
        if words: hits.append({"frame":os.path.basename(f),"words":words[:8]})
    shutil.rmtree(tmp); return hits
def name_ocr(mp4,fps=2):
    os.environ.setdefault("OMP_THREAD_LIMIT","1")
    """Owner-name OCR (any length word): returns frames whose text matches the denylisted real name."""
    tmp=f"/tmp/ocrn_{uuid.uuid4().hex[:6]}"; os.makedirs(tmp)
    subprocess.run(["ffmpeg","-v","error","-i",mp4,"-vf",f"fps={fps}","-q:v","2",f"{tmp}/f%03d.jpg"],check=True)
    hits=[]
    pat=owner_denylist.ocr_fragment_pattern()
    for f in sorted(glob.glob(f"{tmp}/*.jpg")):
        o=subprocess.run(["tesseract",f,"-","--psm","11"],capture_output=True,text=True).stdout
        m=pat.findall(o)
        if m: hits.append({"frame":os.path.basename(f),"words":m[:4]})
    shutil.rmtree(tmp); return hits
def frame_check(mp4,cast):
    """CPU heuristic. Haar face count vs cast; logo/kid detection NOT reliable locally -> flag for review, never pass silently."""
    import cv2
    tmp=f"/tmp/fc_{uuid.uuid4().hex[:6]}"; os.makedirs(tmp)
    subprocess.run(["ffmpeg","-v","error","-i",mp4,"-vf","fps=1","-q:v","2",f"{tmp}/f%03d.jpg"],check=True)
    mx=None
    if hasattr(cv2,"CascadeClassifier"):
        cc=cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml"); mx=0
        for f in sorted(glob.glob(f"{tmp}/*.jpg")):
            g=cv2.cvtColor(cv2.imread(f),cv2.COLOR_BGR2GRAY); fs=cc.detectMultiScale(g,1.1,6,minSize=(30,30)); mx=max(mx,len(fs))
    keep=f"{D}/outbox/held/frames_{os.path.basename(mp4)[:-4]}"; shutil.copytree(tmp,keep,dirs_exist_ok=True); shutil.rmtree(tmp)
    issues=[]
    if mx is None: issues.append("face counter unavailable (cv2 build lacks CascadeClassifier): extra-people check needs review")
    elif mx>max(len(cast),1): issues.append(f"extra people: {mx} faces > {len(cast)} cast")
    if json.load(open(f"{D}/config.json")).get("FRAME_CHECK_MODE")=="flag_for_review": issues.append("kids/logo check not reliable locally: frames need human review ("+keep+")")
    return issues
def post(w,src):
    base=f"{w['id']}_ch04_commenter_parody"; tmp=f"{D}/renders/{base}_norm.mp4"; out=f"{D}/outbox/{base}.mp4"
    has_audio=bool(subprocess.run(["ffprobe","-v","error","-select_streams","a","-show_entries","stream=index","-of","csv=p=0",src],capture_output=True,text=True).stdout.strip())
    ocr=ocr_text(src)  # check source picture BEFORE we add intended overlay
    vf="scale=848:480:force_original_aspect_ratio=decrease,pad=848:480:(ow-iw)/2:(oh-ih)/2"
    sr=w.get("self_reflection") or ({"line":w["credit_line_resolved"]} if w.get("credit_line_resolved") and json.load(open(f"{D}/config.json")).get("CREDIT_LINE_ENABLED",True) else None)
    if sr:
        txt=sr["line"].replace("'","\u2019").replace(":","\\:")
        vf+=f",drawtext=text='{txt}':fontcolor=white:fontsize=20:box=1:boxcolor=black@0.55:boxborderw=8:x=(w-text_w)/2:y=h-th-40:enable='gte(t,1)'"
    for o in w.get("post_overlays",[]):
        t=o["text"].replace("'","\u2019").replace(":","\\:")
        vf+=f",drawtext=text='{t}':fontcolor=white:fontsize=22:box=1:boxcolor=black@0.55:boxborderw=8:x=(w-text_w)/2:y=40:enable='between(t,1,3.5)'"
    cues=w.get("post_tts_cues",[])
    if cues: json.dump({"id":w["id"],"cues":cues,"note":"TTS not generated; placeholder only until trundle picks voices"},open(f"{D}/outbox/{w['id']}_tts_cues.json","w"),indent=1)
    cmd=["ffmpeg","-y","-v","error","-i",src]
    if not has_audio: cmd+=["-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-shortest"]
    cmd+=["-vf",vf,"-af",f"loudnorm=I={CFG['target_lufs']}:TP=-1.5:LRA=11","-c:v","libx264","-pix_fmt","yuv420p","-preset","veryfast","-crf","20","-c:a","aac","-b:a","160k","-ar","48000",
          "-metadata",f"title={w['id']} (parody)","-metadata",f"comment=parody; ch04 commenter clip from {w['handle']} post {w['source_post_id']}; home-only; not aired","-movflags","+faststart",out]
    subprocess.run(cmd,check=True)
    def meas(f):
        e=subprocess.run(["ffmpeg","-i",f,"-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
        m=re.findall(r"I:\s+(-?[\d.]+) LUFS",e); return float(m[-1]) if m else None
    lufs=meas(out)
    if lufs is not None and abs(lufs-CFG["target_lufs"])>0.5:  # short clips: loudnorm undershoots; apply linear gain pass
        g=CFG["target_lufs"]-lufs; fx=out[:-4]+"_gain.mp4"
        subprocess.run(["ffmpeg","-y","-v","error","-i",out,"-c:v","copy","-af",f"volume={g:.2f}dB,alimiter=limit=0.89","-c:a","aac","-b:a","160k","-map_metadata","0","-movflags","+faststart",fx],check=True)
        os.replace(fx,out); lufs=meas(out)
    fc=frame_check(src,w.get("cast",[]))
    name_hits=name_ocr(out)+name_ocr(src)  # trundle 2026-10-27 17:44 CT: owner name never on screen
    if owner_denylist.script_name_pattern().search(json.dumps([w.get("text",""),w.get("post_overlays",[]),w.get("post_tts_cues",[]),w.get("credit_line_resolved","")]).lower()): name_hits.append({"frame":"script/overlay/tts","words":["owner name in text"]})
    if name_hits: fc=fc+[f"OWNER NAME on screen/in script: {name_hits[:3]}"]
    fails=([f"OCR stray text {ocr}"] if ocr else [])+fc+([f"loudness {lufs} LUFS outside -14±{CFG.get('LUFS_TOLERANCE',1)}"] if lufs is None or abs(lufs-CFG["target_lufs"])>CFG.get("LUFS_TOLERANCE",1) else [])
    if fails:
        held=f"{D}/outbox/held/"+os.path.basename(out); shutil.move(out,held); out=held
        json.dump({"id":w["id"],"reasons":fails,"time":now()},open(held[:-4]+"_HELD.json","w"),indent=1)
        sess_add("flag",id=w["id"],reasons=fails)
    res={"id":w["id"],"src":src,"out":out,"lufs":lufs,"ocr_unintended_text":ocr,"ocr_pass":not ocr,"frame_issues":fc,"held":bool(fails),"hold_reasons":fails,"self_reflection_overlay":bool(sr),"had_audio":has_audio}
    log("post",res); manifest(w,res); auto_revert_check(); return res
# ---------- 6 outbox manifest
def manifest(w,res):
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",res["out"]],capture_output=True,text=True).stdout or 0)
    row={"id":w["id"],"file":res["out"],"duration_s":round(dur,2),"channel":4,"show":"Forward Supply","handle":w["handle"],"source_post_id":w["source_post_id"],
         "prompt_text":w["text"],"cast":w["cast"],"self_reflection":w.get("self_reflection"),"weak_score":w.get("weak_score"),"injections":w.get("injections",[]),"post_tts_cues":w.get("post_tts_cues",[]),"post_overlays":w.get("post_overlays",[]),"injections_status":"draft-needs-thundertrundle-ok","lufs":res["lufs"],"ocr_pass":res["ocr_pass"],
         "status":"held-not-for-air" if res.get("held") else "staged-needs-thundertrundle-yes","hold_reasons":res.get("hold_reasons",[]),"thundertrundle_air_yes":False,"approved_by":w.get("approved_by"),"story_wrapped_prompt":w.get("wrapped_prompt"),"credit_line":w.get("credit_line_resolved"),"insert_hint":"clean break or next story gap; never inside a scene","created":now()}
    c=json.load(open(f"{D}/config.json"))
    if c.get("AUTO_AIR_YES") and not c.get("KILL_SWITCH") and not res.get("held"): row.update(thundertrundle_air_yes=True,air_yes_by="auto-gate",status="auto-air-yes")
    open(f"{D}/outbox/manifest.jsonl","a").write(json.dumps(row)+"\n")
# ---------- driver
def main():
    a=argparse.ArgumentParser(); a.add_argument("cmd"); a.add_argument("--dry-run",action="store_true"); a.add_argument("--id"); a.add_argument("--src"); x=a.parse_args()
    if x.cmd=="run-all":
        n_ok=0
        for p in intake():
            ok,why=gate(p); log("gate",{"id":p["id"],"handle":p["handle"],"text":p["text"],"pass":ok,"reason":why})
            if not ok: json.dump({**p,"reject_reason":why},open(f"{D}/rejected/{p['id']}.json","w"),indent=1); print("REJECT",p["id"],p["handle"],"->",why); continue
            n_ok+=1; w=apply_injections(wrap(p),n_ok); json.dump(w,open(f"{D}/wrapped/{p['id']}.json","w"),indent=1)
            r=render(w,x.dry_run); print("PASS  ",p["id"],p["handle"],"model",w["model"],"refs",len(w["reference_images"]),"ooc",w["out_of_character"],"|",r["status"],"est $",r["est_usd"],"month $",r["xai_month_spent"])
    elif x.cmd=="render":
        w=json.load(open(f"{D}/wrapped/{x.id}.json")); print(json.dumps(render(w,x.dry_run),indent=1))
    elif x.cmd=="post":
        w=json.load(open(f"{D}/wrapped/{x.id}.json")); src=x.src or w.get("file"); print(json.dumps(post(w,src),indent=1))
    else: print(__doc__)
# ---------- 7 tag-slip watchlist + provenance + slipcheck (trundle 2026-10-27 17:13 CT; add-only)
import slipcheck as _SC
_input_guard_base=input_guard
def input_guard(path):
    return _input_guard_base(path) or _SC.watch_guard(path)
def _provenance(w):
    ins=[]
    for x in list(w.get("reference_images") or [])+([w["i2v_input"]] if w.get("i2v_input") else [])+([w["end_frame_source"]] if w.get("end_frame_source") else []):
        ins.append({"path":x,"sha256":_sha(x) if os.path.isfile(x) else None})
    return {"inputs":ins,"parent_id":w.get("parent_id"),"origin":w.get("origin"),"lineage":w.get("lineage")}
_render_base=render
def render(w,dry):
    w["provenance"]=_provenance(w); r=_render_base(w,dry); r["provenance"]=w["provenance"]
    if r.get("file"): w["file"]=r["file"]
    return r
_manifest_base=manifest
def manifest(w,res):
    prov=w.get("provenance") or _provenance(w)
    rep=_SC.slipcheck(res["src"],inputs=prov["inputs"],parent=prov.get("parent_id"),clip_id=w["id"])
    res["slipcheck"]={"verdict":rep["verdict"],"flag":rep["flag"]}
    if rep["flag"]:
        res["held"]=True; res.setdefault("hold_reasons",[]).append("tag slip: see outbox/held/SLIP_%s.json"%w["id"])
        if os.path.isfile(res["out"]) and "/held/" not in res["out"]:
            hc=f"{D}/outbox/held/"+os.path.basename(res["out"]); shutil.copy2(res["out"],hc); res["out"]=hc
    _manifest_base(w,res)
    open(f"{D}/outbox/manifest.jsonl","a").write(json.dumps({"provenance_for":w["id"],"file":res["out"],"inputs":prov["inputs"],"parent_id":prov.get("parent_id"),"slipcheck":res["slipcheck"],"time":now()})+"\n")
    open(LINEAGE_FILES[0],"a").write(json.dumps({"clip_id":w["id"],"row_type":"render_provenance","file":res["out"],"src":res["src"],"sha256":_sha(res["src"]) if os.path.isfile(res["src"]) else None,"parent_id":prov.get("parent_id"),"origin":prov.get("origin") or "comment_branch","inputs":prov["inputs"],"slip":rep["flag"],"date":now(),"writer":"CNB"})+"\n")
_main_base=main
def main():
    if len(sys.argv)>1 and sys.argv[1]=="slipcheck":
        arg=sys.argv[2] if len(sys.argv)>2 else "--all"; dry="--report-only" in sys.argv
        if arg=="--all":
            C=_SC.CH4; fs=sorted(set(glob.glob(f"{C}/*.mp4")+glob.glob(f"{C}/raw/*.mp4")+glob.glob(f"{C}/lineage-tagged-*/*.mp4")+glob.glob(f"{C}/sales-overlay*/*.mp4")+glob.glob(f"{C}/ch4badge-*/**/*.mp4",recursive=True)+glob.glob("/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-*/*.mp4")+glob.glob(f"{D}/renders/*.mp4")))
        else: fs=[arg]
        out=[]
        for f in fs:
            r=_SC.slipcheck(f,act=not dry); r.pop("visual",None) if False else None
            out.append({"file":f,"verdict":r["verdict"],"badge_frames":r["visual"]["badge_frames"],"ocr_frames":r["visual"]["ocr_frames"],"near_air":[x["tag"] for x in r["visual"]["near_air"]]}); print(out[-1]["verdict"].split(" ")[0],r["visual"]["badge_frames"],r["visual"]["ocr_frames"],len(r["visual"]["near_air"]),os.path.relpath(f,"/workspace"))
        json.dump(out,open(f"{D}/logs/slipcheck_scan_{datetime.datetime.now(CT).strftime('%Y%m%d-%H%M')}.json","w"),indent=1); return
    return _main_base()
# if __name__=="__main__": main()  # moved to end (section 8)
# ---------- 8 audio leveling gate (trundle standing rule 2026-10-27 17:36 CT; add-only, $0)
import audiolevel as _AL
_manifest_base2=manifest
def manifest(w,res):
    try:
        g=_AL.gate(res["out"],act=True) if os.path.isfile(res.get("out","")) else None
    except Exception as e: g={"pass":False,"queue_file":None,"fails":["audiolevel error: %s"%e]}
    if g:
        m=(g.get("fix") or {}).get("after") or g.get("measure") or {}
        res["audio"]={"pass":g["pass"],"fails":g.get("fails"),"queue_file":g.get("queue_file"),"lufs_i":m.get("lufs_i"),"true_peak":m.get("true_peak"),"lra":m.get("lra"),"audio_leveled":bool(g.get("audio_leveled"))}
        if g.get("queue_file") and g["queue_file"]!=res["out"]: res["out_original"]=res["out"]; res["out"]=g["queue_file"]
        if not g["pass"]: res["held"]=True; res.setdefault("hold_reasons",[]).append("audio not leveled: %s"%g.get("fails"))
        open(f"{D}/outbox/AUDIO-LEVELS.jsonl","a").write(json.dumps({"clip_id":w["id"],"file":res["out"],**res["audio"],"time":now()})+"\n")
    _manifest_base2(w,res)
_main_base2=main
def main():
    if len(sys.argv)>1 and sys.argv[1]=="audiolevel":
        a=sys.argv[2:]
        fs=[x for x in a if not x.startswith("--")]
        for f in fs: g=_AL.gate(f,act="--report-only" not in a); print("PASS" if g["pass"] else "FAIL","; ".join(g["fails"]),g.get("queue_file"),f)
        return
    return _main_base2()
# ---------- genealogy corner tag stamping (trundle 2026-10-27 17:41 CT): tag shows at clip start, full 0-3s,
# alpha fade 3-4s, gone >=4s. Opaque dark cover patch (x1078-1268,y12-74 @1280x720) stays FULL duration so the
# old burned-in 4.1 badge never reappears. Air copies only; input must be an UNTAGGED clean parent. $0 ffmpeg.
TAG_FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TAG_FULL_S,TAG_GONE_S=3.0,4.0
def _tag_esc(s): return s.replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace("#","\\#")
def tag_vf(l1,l2,full=TAG_FULL_S,gone=TAG_GONE_S):
    a=f"if(lt(t\\,{full})\\,1\\,if(lt(t\\,{gone})\\,({gone}-t)/({gone}-{full})\\,0))"
    return (f"drawbox=x=1078:y=12:w=190:h=62:color=0x0A0C10@1:t=fill,"
            f"drawtext=fontfile={TAG_FONT}:text='{_tag_esc(l1)}':fontsize=20:fontcolor=white:x=1258-tw:y=20:alpha='{a}',"
            f"drawtext=fontfile={TAG_FONT}:text='{_tag_esc(l2)}':fontsize=15:fontcolor=0xDCDCDC:x=1258-tw:y=48:alpha='{a}',format=yuv420p")
def stamp_lineage_tag(src,dst,l1,l2,band_png=None):
    """Write a NEW air copy with the fading genealogy tag. Refuses tagged/air-copy inputs and existing dst."""
    if BAD_NAME.search(os.path.basename(src)) and not re.search(r"salesad(B|BA)?_parody\.mp4$|salesad_parody\.mp4$",os.path.basename(src)):
        raise ValueError(f"stamp_lineage_tag: refusing tagged input {src}")
    if "_tagged" in src or "_tagfade" in src: raise ValueError(f"stamp_lineage_tag: refusing tagged input {src}")
    if os.path.exists(dst): raise FileExistsError(dst)
    ins=["-i",src]+(["-i",band_png] if band_png else [])
    flt=(["-filter_complex","[0:v][1:v]overlay=0:0,"+tag_vf(l1,l2)+"[v]","-map","[v]"] if band_png else ["-vf",tag_vf(l1,l2),"-map","0:v"])
    subprocess.run(["ffmpeg","-v","error","-n"]+ins+flt+["-map","0:a?","-c:v","libx264","-crf","18","-preset","medium","-c:a","copy",
                    "-metadata",f"comment=parody; CNB tagfade overlay_edit; {l1} {l2}","-movflags","+faststart",dst],check=True)
    return dst  # caller then runs audiolevel gate (fix -> *_audiofix copy) before queueing

# ---------- 9 comment-prompt store (trundle 2026-10-27 18:05 CT plastic queue; add-only). Store owned by CNB at
# /workspace/shared/streaming/COMMENT-PROMPTS.jsonl. Call record_prompts(global_no,[(prompt_id,text,source,handle)]) once a
# clip gets its global_no; LINEAGE rows take comment_prompt_ids[]=comment_prompts.comment_prompt_ids(global_no).
import comment_prompts as _CP
def record_prompts(global_no,prompts):
    for p in prompts: _CP.append(global_no,*p)
    return _CP.inherited(global_no)

if __name__=="__main__": main()
