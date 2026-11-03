#!/usr/bin/env python3
"""build_prompt_v4 — fluid-meta builder with a hard apply_check gate. Add-only successor to round8 build_prompt_v3 (untouched).
build(spec) -> {"args":GenerateVideo args, "sidecar":tt-clipmeta/v2, "report":gate results}; raises GateFail if any check FAILs.
Spec keys: clip_id parent_clip channel show episode season clip_index duration clip_type(fight|suit_up|breather|beat|news|ad|dialogue|transform)
 look_override setting camera cast[{name,keys[],ref,ref_view(side|threequarter|state|prop),eyeline,look_changed,want}] beats[{t,text|who/move/landing/result|who/line/cue,requester,kind}]
 arc_stage act_goal show_goal consequences[{id,text,short,tier,still,still_since_index,since_index}] hints_planted hints_paid saga depth world_rule
 start_frame set_plate state_stills[{char,path,trait}] commenter_refs[{path,purpose,filtered}] pinned detectors{arc_goal_missing_clips} serious meta_version seed"""
import json,os,re,sys,hashlib
def _cimg_on():
    import json as _j,os as _o
    try: return bool(_j.load(open(_o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),"config","commenter_images.json"))).get("enabled"))
    except Exception: return False
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from layers_v4 import POOLS,SAFETY_POOL,rng,fixed_threads,tier_alive,carry_text
import apply_check_v4 as gate
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER={"name":"build_prompt_v4","version":"4.0.0"}
LOCKS=json.load(open(f"{H}/config/channel_locks.json"))
META_VERSION_DEFAULT="system-v4-20261030"
class GateFail(Exception): pass
NEWS_COMEDY_MAP=[ "the meteorologist sweeps his whole arm across the wrong half of the giant map, freezes mid-gesture, then shuffles three big steps to the right side"]
NEWS_COMEDY=[  # r9: subtle beats (papers, wink) did not read; the map gag did -> visible, physical, sized up
 "behind the anchors a floor director in a headset trips over a cable and catches a falling studio light with both arms, in full view",
 "a huge inflatable pumpkin on the set slowly deflates and folds over onto the desk, and the anchor lifts it off her papers with both hands without missing a word",
 "the co-anchor's chair sinks slowly all the way down while he keeps reading, ending with his chin at desk height"]
DIALOGUE_CUE={"Ch2 News":"crisp anchor cadence, measured pace","default":"natural, conversational"}
def fight_sentence(b):
    # FC2/FC3 (scored 4) won: lens-axis travel + visible jolt reaction + prop/coat contact; FC4/FC5 (3) were generic "every blow lands"/result-only
    s=f"At {b['t']:g} s, {b['who']}'s {b['move']} travels toward the lens and lands on {b['landing']}; {b['result']}"
    if not re.search(r"jolt|snap|fold|stagger|rock|clang|boom|burst",b['result'],re.I): s+=", with a visible jolt"
    return s+"."
def dialogue_sentence(b,channel):
    cue=b.get("cue") or DIALOGUE_CUE.get(channel,DIALOGUE_CUE["default"])
    return f"At {b['t']:g} s, {b['who']} says, \"[{cue}] {b['line']}\""
def beat_sentence(b,channel):
    if b.get("move"): return fight_sentence(b)
    if b.get("line"): return dialogue_sentence(b,channel)
    t=b["text"].strip().rstrip(".")
    end="" if t.endswith('"') else "."
    return t+end if t.startswith("At ") else f"At {b['t']:g} s, {t}{end}"
def ref_list(spec):
    if spec.get("refs_raw") is not None:   # converted legacy prompt: keep its <IMAGE_n> numbering
        return list(spec["refs_raw"]),{},(1 if spec.get("start_frame") else 0)
    """REF-POLICY v4: order = set plate, per-char ref (state still REPLACES identity crop), prop/commenter. Start frame goes in image_path."""
    refs=[]; labels={}
    if spec.get("set_plate"): refs.append(spec["set_plate"])
    stills={s["char"]:s for s in spec.get("state_stills",[])}
    for c in spec.get("cast",[]):
        p=stills[c["name"]]["path"] if c["name"] in stills else c.get("ref")
        if p: refs.append(p); labels[c["name"]]=len(refs)-1
    for cr in (spec.get("commenter_refs",[]) if _cimg_on() else []):   # NOT YET (trundle 10:48 PM)
        if cr.get("filtered") and cr.get("purpose") in ("prop","pattern","color","wardrobe","screen-insert","weather-hint","animal"):
            refs.append(cr["path"]); labels["__c_"+cr["path"]]=len(refs)-1
    off=1 if spec.get("start_frame") else 0
    return refs,{k:v+off for k,v in labels.items()},off
def prompt_probe(movable,spec): return " ".join(movable+[b.get("text","") for b in spec.get("beats",[])])
def build(spec,strict=True):
    cid=spec["clip_id"]; mv=spec.get("meta_version",META_VERSION_DEFAULT); R=rng(cid,mv,spec.get("seed",""))
    ch=spec["channel"]; lock=LOCKS.get(ch,{}); d=spec.get("duration",10); idx=spec.get("clip_index",0)
    refs,lab,off=ref_list(spec); stills={s["char"]:s for s in spec.get("state_stills",[])}
    parts_fixed_head=[]; movable=[]; parts_tail=[]; layers_on=[]
    # durable: look lock (compact; full lock only when no start frame - r9 (5): lock text weaker than refs/start frame)
    look=spec.get("look_override") or (R.choice(lock["look_pool"]) if lock.get("look_pool") else None)
    if look: parts_fixed_head.append(look); layers_on.append(("look","durable"))
    if spec.get("setting"): movable.append(spec["setting"]); layers_on.append(("setting","clip"))
    # cast: ref present -> name + <=3 keys; full text only if no ref or look changed
    cast_txt=[]
    for c in spec.get("cast",[]):
        k=c.get("keys",[])
        if c["name"] in lab:
            slot=f"<IMAGE_{lab[c['name']]}>"
            if c["name"] in stills: cast_txt.append(f"{c["name"]} ({slot} as they are now; {', '.join(k[:3])})" if k else f"{c['name']} ({slot} as they are now)")
            else: cast_txt.append(f"{c['name']} ({slot}; {', '.join(k[:3])})" if k else f"{c['name']} ({slot})")
        else: cast_txt.append(f"{c['name']} ({', '.join(k)})" if k else c["name"])
        if c.get("look_changed") and c.get("full"): cast_txt[-1]=f"{c['name']} ({'<IMAGE_%d>; '%lab[c['name']] if c['name'] in lab else ''}{c['full']})"
    movable+=spec.get("extra",[])
    if cast_txt: movable.append("; ".join(cast_txt)+"."); layers_on.append(("cast","durable-keys"))
    for cr in spec.get("commenter_refs",[]):
        k="__c_"+cr["path"]
        if k in lab: movable.append(f"<IMAGE_{lab[k]}> is only a {cr['purpose']} reference ({cr.get('what','commenter image')}), never a person.")
    # fixed threads (meaning invariant, phrasing fluid) - only on beat clips or when the arc detector fires
    ft={t["id"]:t for t in fixed_threads()["threads"]}
    if spec.get("arc_stage") and (spec.get("clip_type") in ("beat","fight","transform") or (spec.get("detectors",{}).get("arc_goal_missing_clips",0)>=2)):
        movable.append(R.choice(POOLS["arc"]).format(stage=spec["arc_stage"],goal=spec.get("act_goal","")).replace(" .",".")); layers_on.append(("FT1 arc","fixed-thread"))
    for c in spec.get("cast",[]):
        if c.get("want") and spec.get("clip_type") in ("beat","transform"): movable.append(R.choice(POOLS["want"]).format(name=c["name"],want=c["want"])); layers_on.append(("FT2 want","fixed-thread"))
    if spec.get("show_goal") and spec.get("clip_index",0)%4==0: movable.append(R.choice(POOLS["goal"]).format(goal=spec["show_goal"])); layers_on.append(("FT4 goal","fixed-thread (sampled 1 in 4)"))
    # tier layer with decay; state stills default carrier (r9 A/B: stills 4 vs text 3 in all 3 pairs)
    items=[]
    for c in spec.get("consequences",[]):
        if c.get("created_here"): continue   # the clip that creates a consequence shows it as action, carries start next clip
        if not tier_alive(c,spec.get("episode"),spec.get("season"),idx): continue
        t=carry_text(c,idx)
        if t: items.append(t)
    if items: movable.append(R.choice(POOLS["carry"]).format(items="; ".join(items))); layers_on.append(("carry","tier"))
    if spec.get("world_rule"): movable.append(f"World rule: {spec['world_rule']}."); layers_on.append(("world","tier/triggered"))
    # triggered: chaos resolver
    if spec.get("detectors",{}).get("arc_goal_missing_clips",0)>=2 and spec.get("resolver_push"):
        movable.append(R.choice(POOLS["resolver"]).format(push=spec["resolver_push"])); layers_on.append(("resolver","triggered"))
    R.shuffle(movable)   # word-order permutation of the movable block
    seam=([f"The shot opens on the set exactly as in <IMAGE_0> (empty plate, same light); the cast enters it." ] if spec.get("start_is_plate") else [R.choice(POOLS["seam"])]) if spec.get("start_frame") else []
    cam=[spec["camera"]] if spec.get("camera") else []
    eyes=[]
    if spec.get("clip_type")=="fight": cam=cam+["Every strike travels toward the lens and lands with a visible jolt; the camera jerks slightly on each impact."]
    names=[c["name"] for c in spec.get("cast",[])]
    tgts={c.get("eyeline") for c in spec.get("cast",[]) if c.get("eyeline")}
    if spec.get("eyeline_sentence"): eyes=[spec["eyeline_sentence"]]
    elif names:
        tgt=spec.get("eyeline") or (" and ".join(sorted(tgts)) if tgts else "each other and the props in front of them")
        eyes=[R.choice(POOLS["eyeline"]).format(who=" and ".join(names),verb="look at" if len(names)>1 else "looks at",target=tgt)]
    beats=[beat_sentence(b,ch) for b in spec.get("beats",[])]
    if ch=="Ch2 News" and spec.get("clip_type")=="news" and not spec.get("serious"):
        tt=spec.get("comedy_t") or max(1,d-3); beats.append(f"At {tt:g} s, {R.choice(NEWS_COMEDY_MAP if re.search(r"map|meteorolog|weather",prompt_probe(movable,spec),re.I) else NEWS_COMEDY)}, clearly visible in frame."); layers_on.append(("news comedy","clip"))
    end=[] if spec.get("pinned") else [R.choice(POOLS["end"])]
    if spec.get("pinned"): end=["The last 0.4 s eases into the planned end image."]
    safety=[R.choice(SAFETY_POOL).format(d=d)]
    movable=[m for m in movable if not re.search(r"\):\.?$|:\s*\.?$",m.strip())]
    prompt=re.sub(r"\s+"," "," ".join(parts_fixed_head+movable+seam+cam+eyes+beats+end+safety)).strip()
    args={"prompt":prompt,"duration":d,"resolution":spec.get("resolution","480p"),"filename":f"{cid}.mp4"}
    if spec.get("start_frame"): args["image_path"]=spec["start_frame"]
    if refs: args["reference_image_paths"]=refs
    if spec.get("last_frame"): args["last_frame_path"]=spec["last_frame"]
    side=sidecar(spec,args,layers_on,mv)
    rep=gate.check_v4(prompt,args,spec,side)
    fails={k:v for k,v in rep.items() if v[0]=="FAIL"}
    if fails and strict: raise GateFail(f"{cid}: {fails}")
    return {"args":args,"sidecar":side,"report":rep}
def sidecar(spec,args,layers_on,mv):
    p=args["prompt"]
    return {"schema_version":"tt-clipmeta/v2","meta_version":mv,"lexicon_version":"LEXICON v1","builder":BUILDER|{"sha":hashlib.sha256(open(__file__,"rb").read()).hexdigest()[:12]},
     "fixed_threads_version":fixed_threads()["version"],"card_versions":spec.get("card_versions",{}),
     "clip_id":spec["clip_id"],"parent_clip":spec.get("parent_clip"),"channel_show":spec["channel"]+(f" / {spec['show']}" if spec.get("show") and spec["show"] not in spec["channel"] else ""),
     "episode":spec.get("episode"),"clip_type":spec.get("clip_type"),"arc_stage":spec.get("arc_stage"),
     "beats":[{"t":b.get("t"),"requester":b.get("requester","story"),"kind":"fight" if b.get("move") else "dialogue" if b.get("line") else b.get("kind","action")} for b in spec.get("beats",[])],
     "tier_consequences":spec.get("consequences",[]),"hints_planted":spec.get("hints_planted",[]),"hints_paid":spec.get("hints_paid",[]),
     "saga":spec.get("saga"),"depth":spec.get("depth","D0"),"migration_bridge":spec.get("migration_bridge"),"state_stills":spec.get("state_stills",[]),
     "layers_on":[{"layer":a,"kind":b} for a,b in layers_on],"prompt_sha256":hashlib.sha256(p.encode()).hexdigest(),"prompt_words":len(p.split()),
     "air_status":"design-not-rendered","deprecated_fields":{}}
def write(spec,outdir):
    r=build(spec); os.makedirs(outdir,exist_ok=True); cid=spec["clip_id"]
    json.dump(r["args"],open(f"{outdir}/{cid}.args.json","w"),indent=1)
    json.dump(r["sidecar"],open(f"{outdir}/{cid}.meta.json","w"),indent=1)
    return r
