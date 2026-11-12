"""Synthetic tag-slip test: simulate i2v output that inherited the corner tag. $0, ffmpeg only."""
import sys,os,json,subprocess,glob
sys.path.insert(0,"/workspace/streaming/commenter-pipeline"); import slipcheck as s
H=os.path.dirname(os.path.abspath(__file__)); air=sorted(glob.glob(s.CH4+"/lineage-tagged-20261027/*_salesad_tagged_parody.mp4"))[0]
fr=f"{H}/inherited_frame.png"; clip=f"{H}/synthetic_i2v_slip_parody.mp4"
subprocess.run(["ffmpeg","-y","-v","error","-ss","2","-i",air,"-frames:v","1",fr],check=True)
# renamed clean-looking input + slow zoom/blur like an i2v smear
subprocess.run(["ffmpeg","-y","-v","error","-loop","1","-i",fr,"-t","4","-vf","zoompan=z='1+0.0008*on':d=1:s=1280x720:fps=24,gblur=sigma=0.8","-pix_fmt","yuv420p","-metadata","comment=synthetic slip parody "+str(os.getpid()),clip],check=True)
ren=f"{H}/clean_looking_ref.png"; subprocess.run(["cp",fr,ren])
wl0=len(s.wl_rows()); log0=sum(1 for _ in open(s.SLIPLOG)); lin0=sum(1 for _ in open(s.LINEAGE))
r=s.slipcheck(clip,inputs=[{"path":ren,"sha256":s.sha(ren)}],parent="#9",clip_id="synthetic-slip-1713")
res={"verdict":r["verdict"],"flag":r["flag"],"prov_hits":[h["why"] for h in r["prov_hits"]],"badge_frames":r["visual"]["badge_frames"],"ocr_frames":r["visual"]["ocr_frames"],"near_air":r["visual"]["near_air"],
 "watchlist_added":r.get("watchlist_added"),"watchlist_rows":[wl0,len(s.wl_rows())],"sliplog_rows":[log0,sum(1 for _ in open(s.SLIPLOG))],"lineage_rows":[lin0,sum(1 for _ in open(s.LINEAGE))],
 "held_copy_exists":os.path.isfile(r.get("held_copy","")),"slip_report":os.path.isfile(s.P+"/outbox/held/SLIP_synthetic-slip-1713.json")}
# second pass: an input guard on a fresh re-save of the inherited frame (new sha, no name hint) should now be caught by the watchlist pHash
re2=f"{H}/resaved_ref.jpg"; subprocess.run(["ffmpeg","-y","-v","error","-i",fr,"-q:v","4",re2],check=True)
res["guard_on_resaved_after_learning"]=s.watch_guard(re2)
res["raw_masters_guard"]=[s.watch_guard(f) for f in sorted(glob.glob(s.CH4+"/raw/*.mp4"))]
ok=r["flag"] and res["held_copy_exists"] and res["slip_report"] and res["watchlist_rows"][1]>wl0 and res["sliplog_rows"][1]==log0+1 and res["lineage_rows"][1]==lin0+1 and res["guard_on_resaved_after_learning"] and not any(res["raw_masters_guard"])
res["PASS"]=bool(ok); json.dump(res,open(f"{H}/results.json","w"),indent=1); print(json.dumps(res,indent=1))
