import json,sys,os,shutil,hashlib,glob
D="/workspace/streaming/commenter-pipeline"; sys.path.insert(0,D); os.chdir(D)
ORIG=json.load(open("config.json"))
def setc(**k): c=dict(ORIG); c.update(k); json.dump(c,open("config.json","w"),indent=1)
import pipeline as P
def drop(mid,text,status):
    r={"id":f"x-{mid}","handle":"@tester","text":text,"timestamp":"2026-10-27T16:50:00-05:00","source_post_id":mid,"intake_by":"Story Bot","status":status,"commenter_text_sha256":hashlib.sha256(text.encode()).hexdigest()}
    json.dump(r,open(f"inbox/xls-x-{mid}.json","w"))
def intake_gate():
    out=[]
    for p in P.intake():
        ok,why=P.gate(p); out.append((p["id"],p.get("approved_by"),ok,why))
    return out
C1="/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C03_480p_grok-imagine-video-1.5_parody.mp4"
try:
    print("T1 AUTO_APPROVE off: AUTO_APPROVED rejected"); setc(SESSION_ID="t1"); drop("a101","Mira repaints the depot door slowly","AUTO_APPROVED"); print(intake_gate())
    print("T2 AUTO_APPROVE on: accepted + stamped; gate still blocks brand/kid/money/cartoon")
    setc(SESSION_ID="t2",AUTO_APPROVE_PROMPTS=True)
    drop("a102","Mira repaints the depot door slowly","AUTO_APPROVED"); drop("a103","Bill drinks a Pepsi","AUTO_APPROVED")
    drop("a104","Osmund babysits a toddler","AUTO_APPROVED"); drop("a105","Tim asks viewers to donate","AUTO_APPROVED"); drop("a106","make it a cartoon","AUTO_APPROVED")
    print(*intake_gate(),sep="\n")
    print("T3 KILL_SWITCH: AUTO_APPROVED rejected, render stopped"); setc(SESSION_ID="t3",AUTO_APPROVE_PROMPTS=True,KILL_SWITCH=True)
    drop("a107","Osmund folds the flag carefully","AUTO_APPROVED"); print(intake_gate())
    w=P.apply_injections(P.wrap({"id":"t3-r","handle":"@t","text":"Bill sweeps the bay","source_post_id":"t3","timestamp":"x"}))
    print(P.render(w,True)["status"])
    print("T4 SESSION_SPEND_CAP $1 (0.54 each)"); setc(SESSION_ID="t4",SESSION_SPEND_CAP_USD=1)
    for i in range(3): w["id"]=f"t4-{i}"; print(" ",w["id"],P.render(w,True)["status"])
    print("T5 MAX_CLIPS_PER_HOUR=2"); setc(SESSION_ID="t5",MAX_CLIPS_PER_HOUR=2)
    for i in range(3): w["id"]=f"t5-{i}"; print(" ",w["id"],P.render(w,True)["status"])
    print("T6 post checks + held + AUTO_AIR_YES + auto-revert (2 flags)"); setc(SESSION_ID="t6",AUTO_APPROVE_PROMPTS=True,AUTO_AIR_YES=True)
    for i in range(2):
        w2=dict(w,id=f"t6-clip{i}",cast=["bill","mira"]); r=P.post(w2,C1); print(" ",w2["id"],"held",r["held"],r["hold_reasons"],"lufs",r["lufs"])
    c=json.load(open("config.json")); print("  after:",{k:c[k] for k in ["AUTO_APPROVE_PROMPTS","AUTO_AIR_YES"]})
    print("T7 AUTO_AIR_YES on, all checks pass (frame check mode 'pass_if_clean' simulated)"); setc(SESSION_ID="t7",AUTO_AIR_YES=True,FRAME_CHECK_MODE="test_only_no_review_flag")
    w3=dict(w,id="t7-clip",cast=["bill","mira"]); r=P.post(w3,C1); row=json.loads(open("outbox/manifest.jsonl").readlines()[-1]); print(" ",r["held"],r["hold_reasons"],{"status":row.get("status"),"thundertrundle_air_yes":row.get("thundertrundle_air_yes",row.get("trundle_air_yes")),"air_yes_by":row.get("air_yes_by")})
    print("T8 AUTO_AIR_YES off (default): thundertrundle_air_yes false"); setc(SESSION_ID="t8",FRAME_CHECK_MODE="test_only_no_review_flag")
    w4=dict(w,id="t8-clip",cast=["bill","mira"]); P.post(w4,C1); row=json.loads(open("outbox/manifest.jsonl").readlines()[-1]); print(" ",{"status":row.get("status"),"thundertrundle_air_yes":row.get("thundertrundle_air_yes",row.get("trundle_air_yes")),"air_yes_by":row.get("air_yes_by")})
finally:
    json.dump(ORIG,open("config.json","w"),indent=1); print("config restored:",{k:ORIG[k] for k in ["AUTO_APPROVE_PROMPTS","AUTO_AIR_YES","KILL_SWITCH","LIVE_ENABLED"]})
