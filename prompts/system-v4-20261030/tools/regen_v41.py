#!/usr/bin/env python3
"""Rebuild every pending prompt with build_prompt_v41 (fixed order, static look, his rules bracket). Output prompts_v41/, out/DIFF-v41.md."""
import os,sys,json,re,types
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import build_prompt_v41 as B41, apply_check_v41 as G41, regen_pending_v4 as RG
H=RG.H; B41.gate.ac1=types.SimpleNamespace(CAM=G41.CAM); RG.B=B41
OUT=f"{H}/prompts_v41"; LOG=[]
import glob
SHEETS={}
for f in sorted(glob.glob("/workspace/thunder-trundle/channels/*/refs/sheets/SHEET_*.jpg")):
    if "REJECTED" in f: continue
    n=int(os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(f))))[:2]); SHEETS.setdefault(n,f)
SHOW={"Ch11 Fist Theater":"THE NIGHT PORTER"}
def run_one(group,cid,old,spec,notes,log):
    notes=list(notes)
    if spec.get("start_is_plate"): spec["start_frame"]=None; spec["img_shift"]=1; notes.append("v4.1: set plate removed as start frame (trundle t121u: refs are reference only, not the output/start)")
    if cid=="AD-Dynapage": spec["remake_of"]="Dynapage (completed ad)"
    spec.setdefault("show",SHOW.get(spec["channel"]))
    for b in spec.get("beats",[]):
        if "text" in b: b["text"]=b["text"].replace("he keeps reporting,","DALE keeps reporting,").replace("At 5 s she opens it below","At 5 s CANDY opens it below")
    m=re.match(r"(?:P|LS)\D*(\d+)",cid); chn=None
    if group=="round9-starters": chn=int(cid[1:3])
    if group=="lipsync": chn=2
    if not spec.get("refs_raw") and chn and chn!=4 and chn in SHEETS:
        spec["refs_raw"]=[SHEETS[chn]]; notes.append(f"v4.1: no ref on file -> approved channel cast sheet {os.path.basename(SHEETS[chn])} as reference (t132u refs required)")
    v4=f"{H}/prompts_v4/{group}/{cid}.args.json"; v4p=json.load(open(v4))["prompt"] if os.path.exists(v4) else None
    try: r=B41.write(spec,f"{OUT}/{group}"); st="OK"
    except B41.GateFail:
        r=B41.build(spec,strict=False); st="BLOCKED"; os.makedirs(f"{OUT}/BLOCKED",exist_ok=True)
        json.dump({"id":cid,"why":{k:v for k,v in r["report"].items() if v[0]=="FAIL"},"draft_args":r["args"],"notes":notes},open(f"{OUT}/BLOCKED/{cid}.json","w"),indent=1)
    LOG.append({"group":group,"id":cid,"status":st,"fails":[k for k,v in r["report"].items() if v[0]=="FAIL"],"warns":[k for k,v in r["report"].items() if v[0]=="WARN"],"v4":v4p,"v41":r["args"]["prompt"],"notes":sorted(set(notes))})
RG.run_one=run_one
if __name__=="__main__":
    for fn in (RG.odyssey,RG.round9,RG.commercials,RG.lipsync):
        try: fn([])
        except Exception as e: print("ERR",fn.__name__,repr(e)); raise
    os.makedirs(f"{H}/out",exist_ok=True)
    json.dump(LOG,open(f"{H}/out/diff-v41.json","w"),indent=1)
    with open(f"{H}/out/DIFF-v41.md","w") as f:
        f.write("# v4 -> v4.1 prompt diff (full text)\n")
        for x in LOG: f.write(f"\n## {x['id']} ({x['group']}) {x['status']} fails={x['fails']} warns={x['warns']}\nnotes: {x['notes']}\n\n**v4:** {x['v4']}\n\n**v4.1:** {x['v41']}\n")
    ok=sum(x["status"]=="OK" for x in LOG); print(ok,"OK /",len(LOG))
    for x in LOG:
        if x["status"]!="OK": print(x["id"],x["fails"])
