# TEST ONLY: stub frame_check to [] to exercise the AUTO_AIR_YES manifest branch. Not a real pass.
import json,sys,os; D="/workspace/streaming/commenter-pipeline"; sys.path.insert(0,D); os.chdir(D)
O=json.load(open("config.json")); c=dict(O,AUTO_AIR_YES=True,SESSION_ID="t9"); json.dump(c,open("config.json","w"))
import pipeline as P; P.frame_check=lambda *a:[]
try:
    w=P.apply_injections(P.wrap({"id":"t9-stub","handle":"@t","text":"Bill sweeps the bay","source_post_id":"t9","timestamp":"x"}))
    r=P.post(w,"/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C03_480p_grok-imagine-video-1.5_parody.mp4")
    row=json.loads(open("outbox/manifest.jsonl").readlines()[-1]); print("T9 stubbed frame check, AUTO_AIR_YES on:",r["held"],{"status":row.get("status"),"thundertrundle_air_yes":row.get("thundertrundle_air_yes",row.get("trundle_air_yes")),"air_yes_by":row.get("air_yes_by")})
finally: json.dump(O,open("config.json","w"),indent=1)
