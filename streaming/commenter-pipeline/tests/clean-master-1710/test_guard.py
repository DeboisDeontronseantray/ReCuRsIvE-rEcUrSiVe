import sys,os,json; sys.path.insert(0,"/workspace/streaming/commenter-pipeline"); import pipeline as P
L="/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique"; TG="/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagged-20261027/20261026_231528_4_1_Military-Boutique_armored-showroom-cruiser_parody_salesadBA_tagged_parody.mp4"; H=os.path.dirname(os.path.abspath(__file__)); res=[]
def t(name,cond): res.append((name,bool(cond))); print(("PASS " if cond else "FAIL ")+name)
t("tagged file rejected (name+folder)", P.input_guard(TG))
t("clean master raw/mb_rover accepted", P.input_guard(f"{L}/raw/mb_rover.mp4") is None)
t("Run2 raw render accepted", P.input_guard("/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1A_480p_grok-imagine-video-1.5_parody.mp4") is None)
st=P.refs_for("bill"); t("cast still accepted", st and P.input_guard(st[0]) is None)
r=P.input_guard(f"{H}/innocent_clip_parody.mp4"); t("renamed tagged copy caught by sha: "+str(r), r and "sha256" in r)
t("ch4badge name rejected", P.input_guard(f"{L}/ch4badge-20261027/x_ch4badge.mp4"))
p={"id":"cm1710-t1","handle":"@test","text":"bill finds a crate","reference_images":[],"end_frame_source":TG,"cast":["bill"]}
w=P.wrap(p); t("wrap: tagged end_frame -> HELD", w.get("status")=="HELD")
r=P.render(w,True); t("render refuses HELD (no API) "+r["status"], r["status"].startswith("HELD") and not r["api_called"])
p2={**p,"id":"cm1710-t2","end_frame_source":f"{L}/raw/mb_rover.mp4"}; w2=P.wrap(p2)
t("wrap: clean master end_frame accepted", w2.get("status")!="HELD" and any("endframe_cm1710-t2" in x for x in w2["reference_images"]))
r2=P.render(w2,True); t("dry-run clean: "+r2["status"], not r2["api_called"])
json.dump(res,open(f"{H}/results.json","w")); sys.exit(0 if all(c for _,c in res) else 1)
