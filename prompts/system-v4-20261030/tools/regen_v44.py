#!/usr/bin/env python3
"""prompts_v44 = prompts_v43 copied unchanged + the 16 exempt ads promoted from BLOCKED (draft_args copied unchanged). Gate v4.4. prompts_v43 untouched."""
import os,sys,json,glob,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import apply_check_v44 as G
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SRC=f"{H}/prompts_v43"; OUT=f"{H}/prompts_v44"
assert not os.path.exists(OUT),"prompts_v44 exists; refusing to overwrite"
EX=G.exempt_ids()
shutil.copytree(SRC,OUT,ignore=lambda d,n:[x for x in n if d.endswith("BLOCKED") and x[:-5] in EX])
res=[]
for cid in sorted(EX):
    b=json.load(open(f"{SRC}/BLOCKED/{cid}.json")); a=b["draft_args"]
    json.dump(a,open(f"{OUT}/commercials/{cid}.args.json","w"),indent=1)
    json.dump({"clip_id":cid,"clip_type":"ad","ref_exemption":"trundle 11:10 PM CT Oct 30 (relayed): \"These specific ads can run without an image\"","source":f"prompts_v43/BLOCKED/{cid}.json draft_args, copied unchanged","notes":b.get("notes",[])},open(f"{OUT}/commercials/{cid}.meta.json","w"),indent=1)
for f in sorted(glob.glob(f"{OUT}/*/*.args.json")):
    if "/BLOCKED/" in f: continue
    cid=os.path.basename(f)[:-10]; a=json.load(open(f)); r=G.check(a["prompt"],a,clip_id=cid)
    res.append({"id":cid,"status":"FAIL" if any(v[0]=="FAIL" for v in r.values()) else "PASS","fails":[k for k,v in r.items() if v[0]=="FAIL"],"exempt":cid in EX})
held=[{"id":os.path.basename(f)[:-5],"why":json.load(open(f))["why"]} for f in sorted(glob.glob(f"{OUT}/BLOCKED/*.json"))]
json.dump({"results":res,"held":held},open(f"{H}/out/gate-v44.json","w"),indent=1)
P=sum(x["status"]=="PASS" for x in res); print(P,"PASS /",len(res)-P,"FAIL /",len(held),"HELD")
for x in res:
    if x["status"]=="FAIL": print("FAIL",x)
for h in held: print("HELD",h["id"],h["why"])
