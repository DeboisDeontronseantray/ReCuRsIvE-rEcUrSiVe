#!/usr/bin/env python3
"""Made-up commenter-clip path (CNB, 2026-10-27 17:45 CT; trundle 17:25 CT: 'make more up if you have to. Auto approval from the start').
Prompts written by CNB (origin made_up), not by a commenter, so they skip Story Bot XLS intake but run every other filter:
auto-approve check (AUTO_APPROVE_PROMPTS true, KILL_SWITCH false) -> dedupe -> gate (blocklists) -> wrap (locked CH4 rules, observational) ->
injections -> input_guard on all refs -> month cap/warn, 2-try limit, session cap, clips/hour -> render (one try, no retry) ->
post (OCR, frame check, LUFS) -> slipcheck/manifest/provenance (pipeline wrappers) -> LINEAGE row in lineage 4.3.
LIVE_ENABLED is not required here (it gates live commenter intake/air); thundertrundle_air_yes is always false.
Usage: made_up.py prompts.json [--dry-run] [--only ID]"""
import sys,json,os,datetime
sys.argv_saved=sys.argv; import pipeline as P
D=P.D; CH4="/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/"
def render_made_up(w,dry):
    e=P.est(w); spent=P.xai_month_spend(); proj=round(spent+e,2); cfg=P.CFG
    r={"id":w["id"],"model":w["model"],"est_usd":e,"xai_month_spent":spent,"projected":proj,"dry_run":dry,"api_called":False,"path":"made_up","authorized_by":"pt240u"}
    if proj>cfg["xai_monthly_cap_usd"]: r["status"]="STOP: would pass xAI cap"; P.log("render",r); return r
    if proj>=cfg["xai_warn_usd"]: r["warn"]=f"projected ${proj} >= warn"
    if P.tries(w["id"])>=cfg["max_tries_per_clip"]: r["status"]="STOP: max 2 tries used"; P.log("render",r); return r
    if w.get("status")=="HELD": r["status"]="HELD: "+w.get("hold_reason",""); P.log("render",r); return r
    h=[]; P.guard_list(list(w.get("reference_images") or []),h)
    if h: r["status"]="HELD: input_guard"; r["held_inputs"]=h; P.log("render",r); return r
    stop=P.safety_stop(e)
    if stop: r["status"]=stop; P.log("render",r); return r
    if dry: r["status"]="dry-run: no API call (not counted in session)"; P.log("render",r); return r
    import requests,base64,time
    imgs=[]
    for p in w["reference_images"]:
        mt="image/png" if p.endswith(".png") else "image/jpeg"
        imgs.append({"url":f"data:{mt};base64,"+base64.b64encode(open(p,"rb").read()).decode()})
    body={"model":w["model"],"prompt":w["prompt"]+" Avoid: "+w["negative_prompt"],"duration":w["duration_s"],"resolution":cfg["resolution"],"aspect_ratio":"16:9"}
    if imgs: body["reference_images"]=imgs
    H={"Authorization":"Bearer "+os.environ["XAI_API_KEY"],"Content-Type":"application/json"}
    r["api_called"]=True; P.log("render",{**r,"status":"submitting"})
    q=requests.post("https://api.x.ai/v1/videos/generations",headers=H,json=body,timeout=180)
    if q.status_code>=300: r["status"]=f"submit failed {q.status_code}: {q.text[:300]}"; P.log("render",r); return r
    rid=q.json()["request_id"]; t0=time.time()
    while True:
        time.sleep(6); j=requests.get("https://api.x.ai/v1/videos/"+rid,headers=H,timeout=60).json()
        if j.get("status") in("done","failed","expired") or time.time()-t0>900: break
    usd=e if j.get("status")=="done" else 0.0
    if j.get("status")=="done":
        fn=f"{D}/renders/{w['id']}_480p_{w['model']}_parody.mp4"; open(fn,"wb").write(requests.get(j["video"]["url"],timeout=300).content); r["file"]=fn
    r.update(status=j.get("status","timeout"),request_id=rid,cost_usd=usd)
    open(cfg["spend_log"],"a").write(json.dumps({"time":P.now(),"prompt_id":"ch04-commenter-made-up","provider":"xai_imagine","model":w["model"],"cost_usd":usd,"clip":w["id"],"task":f"ch04 made-up commenter clip {w['id']}","request_id":rid,"source":"list-price estimate (480p)","channel":4})+"\n")
    P.sess_add("render",id=w["id"],usd=usd,dry=False); P.log("render",r); return r
def lineage_row(w,res,r):
    rows=[json.loads(l) for l in open(CH4+"LINEAGE.jsonl")]; no=max(x["global_no"] for x in rows if isinstance(x.get("global_no"),int))+1
    l1=f"4.3 g1 #{no}"
    row={"clip_id":f"ch4-comment-{w['id']}","tag":l1,"tag_2line":f"{l1} / original","tag_3line":f"{l1} / #{no} / original","lineage":"4.3","gen":1,"global_no":no,
         "parent_id":None,"parent_global_no":None,"origin":"made_up","role":"clean_master","prompt_sha":P._sha_text(w["prompt"]) if hasattr(P,"_sha_text") else __import__("hashlib").sha256(w["prompt"].encode()).hexdigest(),
         "refs":w["reference_images"],"file":r.get("file"),"sha256":P._sha(r["file"]),"clean_source":r.get("file"),"air_copy_file":res["out"],
         "date":P.now(),"cost_usd":r.get("cost_usd"),"writer":"CNB","intake_by":"CNB made_up path","approved_by":"auto-gate","thundertrundle_air_yes":False,
         "note":"raw render = clean master (untagged); outbox file = post copy; air needs trundle's per-clip OK"}
    open(CH4+"LINEAGE.jsonl","a").write(json.dumps(row)+"\n"); return row
def main():
    a=sys.argv[1:]; dry="--dry-run" in a; only=a[a.index("--only")+1] if "--only" in a else None
    c=json.load(open(f"{D}/config.json"))
    if not c.get("AUTO_APPROVE_PROMPTS") or c.get("KILL_SWITCH"): print("STOP: AUTO_APPROVE_PROMPTS off or KILL_SWITCH on"); return
    seen=P._ids_in(f"{D}/logs/seen.jsonl",["id"])|P._ids_in(f"{D}/outbox/manifest.jsonl",["id"])
    for p in json.load(open(a[0])):
        if only and p["id"]!=only: continue
        if p["id"] in seen and not dry: print("DUP skip",p["id"]); continue
        p={**p,"handle":"@made_up","source_post_id":"made_up-"+p["id"],"timestamp":P.now(),"origin":"made_up","status":"AUTO_APPROVED","approved_by":"auto-gate","credit_line_resolved":None,"lineage":"4.3","parent_id":None}
        ok,why=P.gate(p); P.log("gate",{"id":p["id"],"handle":p["handle"],"text":p["text"],"pass":ok,"reason":why,"origin":"made_up"})
        if not ok: print("REJECT",p["id"],why); continue
        w=P.apply_injections(P.wrap(p),1); w["post_tts_cues"]=[]; w["injections"]=[i for i in w.get("injections",[]) if i.get("kind")!="spoken_line"]
        json.dump(w,open(f"{D}/wrapped/{p['id']}.json","w"),indent=1)
        r=render_made_up(w,dry); print(p["id"],w["model"],"refs",len(w["reference_images"]),"|",r["status"],"est $",r["est_usd"],"month $",r["xai_month_spent"],flush=True)
        if dry or not r.get("file"): continue
        open(f"{D}/logs/seen.jsonl","a").write(json.dumps({"time":P.now(),"id":p["id"],"source_post_id":p["source_post_id"],"file":"made_up"})+"\n")
        w["provenance"]=P._provenance(w); w["file"]=r["file"]
        res=P.post(w,r["file"]); lr=lineage_row(w,res,r)
        print("  post:",res["out"],"held",res["held"],res["hold_reasons"][:3],"slip",res.get("slipcheck"),"tag",lr["tag"],flush=True)
if __name__=="__main__": main()
