#!/usr/bin/env python3
"""build_prompt_v41 — replaces v4's fluid shuffle (rule conflicts: see RULE-CONFLICTS-FIXED.md).
FIXED SLOT ORDER, never shuffled:
  [Look] [Setting] [Cast] -> Continue -> Shot -> Eyelines -> timed beats -> ending line -> [Rules]
Non-direction text sits inside [brackets]; direction (action, camera, timing) sits outside (Trundle t155u).
Dialogue: speaker named, what they say inside brackets with a brief delivery note (t134u, t139u).
Static (tangible + intangible) comes from config/static_v41.json word for word (t370u). Fluid: only the
thread-expression beat and commenter content. Rules bracket uses Trundle's own wording (no gore; bloodstains
on clothing fine; JW level on Ch4)."""
import json,os,re,hashlib,random,sys
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import apply_check_v41 as gate
STATIC=json.load(open(f"{H}/config/static_v41.json"))
LOCKS={k:{"look_pool":[v["look"]]} for k,v in STATIC["channels"].items()}   # one fixed look per channel (regen compat)
META="system-v4.1-20261030"; BUILDER={"name":"build_prompt_v41","version":"4.1.0"}
class GateFail(Exception): pass
def rules_bracket(ch,fight=False,spec_ad=False):
    s="[Adults only, no kids. Invented characters; a named real person becomes only their moves and attitude, never their likeness. No gore; bloodstains on clothing are fine, no blood draining out. Nobody looks into the camera."
    s+=" Parody brands only; no real brands or personal names on screen."   # CURRENT-RULES v48 L34 hard limit, all clips (was ads only)
    if ch.startswith("Ch4") and fight: s+=" John Wick level: hard hits and some blood, but no gore."
    return s+"]"
def br(s): s=s.strip(); return s if s.startswith("[") else f"[{s.rstrip('.')}.]"
def dialogue(b):
    cue=b.get("cue","clear, natural"); return f"At {b['t']:g} s, {b['who']} speaks [{cue}: \"{b['line']}\"]."
def beat(b):
    if b.get("line"): return dialogue(b)
    if b.get("move"): return f"At {b['t']:g} s, {b['who']}'s {b['move']} lands on {b['landing']}; {b['result']}."
    t=b["text"].strip().rstrip(".")
    # bracket any quoted speech inside a free-text beat
    t=re.sub(r'(says|saying|said|yells|shouts|whispers|reporting|reports|asks|calls)[^"\[]*,?\s*"(\[([^\]]*)\]\s*)?([^"]+)"',lambda m:f'speaks [{(m.group(3) or "clear, natural")}: "{m.group(4).strip()}"]',t)
    return t+"." if t.startswith("At ") else f"At {b['t']:g} s, {t}."
def build(spec,strict=True):
    ch=spec["channel"]; d=spec.get("duration",10); cid=spec["clip_id"]
    show=STATIC["shows"].get(spec.get("show") or "",{})
    look=STATIC["channels"].get(ch,{}).get("look") or spec.get("look_override")
    if spec.get("look_override") and not ch.startswith("Ch4") and (spec.get("clip_type")=="ad" or ch not in STATIC["channels"]): look=spec["look_override"]
    slots=[]
    if look: slots.append(br("Look: "+re.sub(r"^Look:\s*","",look)))
    setting=spec.get("setting")
    if setting: slots.append(br(re.sub(r"^\[|\]$","",setting)))
    elif show.get("tangible",{}).get("setting"): slots.append(br("Setting: "+show["tangible"]["setting"]))
    refs=list(spec.get("refs_raw") or []); off=1 if spec.get("start_frame") else 0
    cast=[]
    for c in spec.get("cast",[]):
        keys=show.get("tangible",{}).get("cast",{}).get(c["name"]) or c.get("keys",[])
        r=c.get("ref"); slot=""
        if r: 
            if r not in refs: refs.append(r)
            slot=f"<IMAGE_{refs.index(r)+off}>; "
        cast.append(f"{c['name']} ({slot}{', '.join(keys[:3])})".replace("; )",")"))
    for x in spec.get("extra",[]):
        if look and x.strip("[] ")[:20].lower() in look.lower(): continue   # legacy look line duplicated by static look
        # legacy cast/props sentences from older prompts: non-direction -> bracket
        x=re.sub(r'\b([A-Z][A-Z]+) (says|yells|shouts|whispers),\s*"\[([^\]]*)\]\s*([^"]+)"',lambda m:f'{m.group(1)} speaks [{m.group(3)}: "{m.group(4).strip().rstrip(",")}"]',x)
        slots.append(br(x)) if not re.match(r"^At \d",x) else None
    if cast: slots.append(br("Cast: "+"; ".join(cast)))
    if spec.get("thread") : slots.append(br("Thread: "+spec["thread"]))
    direction=[]
    if spec.get("start_frame"): direction.append("Continue from <IMAGE_0>, same positions and light, already moving.")
    cam=(spec.get("camera") or "Single shot: medium shot, 35mm, eye level, static camera.").rstrip(".")
    cam=cam+"." if "continuous" in cam else cam+f", one continuous {d:g} s take."
    direction.append(cam)
    direction.append(spec.get("eyeline_sentence") or "Everyone looks at each other and the props in front of them, never into the lens.")
    bs=[beat(b) for b in spec.get("beats",[])]
    if spec.get("thread_beat"): bs.append(beat(spec["thread_beat"]))
    direction+=bs
    direction.append("The last 0.4 s eases into the planned end image." if spec.get("pinned") else "Motion carries on through the last half second.")
    fight=spec.get("clip_type")=="fight" or any(b.get("move") for b in spec.get("beats",[]))
    prompt=re.sub(r"\s+"," "," ".join(slots+direction+[rules_bracket(ch,fight,spec.get("clip_type")=="ad")])).strip()
    if spec.get("img_shift"): prompt=re.sub(r"<IMAGE_(\d+)>",lambda m:f"<IMAGE_{int(m.group(1))-spec['img_shift']}>",prompt)
    args={"prompt":prompt,"duration":d,"resolution":spec.get("resolution","480p"),"filename":f"{cid}.mp4"}
    if spec.get("start_frame"): args["image_path"]=spec["start_frame"]
    if refs: args["reference_image_paths"]=refs
    if spec.get("last_frame"): args["last_frame_path"]=spec["last_frame"]
    side={"schema_version":"tt-clipmeta/v2","meta_version":META,"builder":BUILDER|{"sha":hashlib.sha256(open(__file__,"rb").read()).hexdigest()[:12]},
          "static_version":STATIC["version"],"clip_id":cid,"parent_clip":spec.get("parent_clip"),"channel_show":ch+(f" / {spec['show']}" if spec.get("show") else ""),
          "clip_type":spec.get("clip_type"),"arc_stage":spec.get("arc_stage"),"static_intangible":show.get("intangible"),
          "beats":[{"t":b.get("t"),"requester":b.get("requester","story")} for b in spec.get("beats",[])],
          "tier_consequences":spec.get("consequences",[]),"hints_planted":spec.get("hints_planted",[]),"hints_paid":spec.get("hints_paid",[]),
          "threads_followed":spec.get("threads_followed",[]),"saga":spec.get("saga"),"depth":spec.get("depth","D0"),
          "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"prompt_words":len(prompt.split()),"air_status":"design-not-rendered"}
    rep=gate.check(prompt,args,spec,side)
    fails={k:v for k,v in rep.items() if v[0]=="FAIL"}
    if fails and strict: raise GateFail(f"{cid}: {fails}")
    return {"args":args,"sidecar":side,"report":rep}
def write(spec,outdir):
    r=build(spec); os.makedirs(outdir,exist_ok=True)
    json.dump(r["args"],open(f"{outdir}/{spec['clip_id']}.args.json","w"),indent=1); json.dump(r["sidecar"],open(f"{outdir}/{spec['clip_id']}.meta.json","w"),indent=1); return r
