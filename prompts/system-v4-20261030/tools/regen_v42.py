#!/usr/bin/env python3
"""Rebuild every pending prompt with build_prompt_v42 (t371u: attached image => name + tag only). v4.1 files untouched.
Output prompts_v42/, out/DIFF-v42.md, out/diff-v42.json. No renders, no paid calls."""
import os,sys,json,re,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import regen_v41 as R41, build_prompt_v42 as B42, regen_pending_v4 as RG
H=R41.H; OUT=f"{H}/prompts_v42"; SS=f"{H}/state_stills_v42"
R41.B41=B42; R41.OUT=OUT; R41.LOG.clear()
# Channel cast sheets auto-attached in v4.1 that do NOT show the character the prompt names (checked by eye, Oct 30 8:15 PM CT):
SHEET_MISMATCH={3,7,8,9,10,12,14}
# state stills cut free from the parent clip's real last frame (Trundle t362u state-still rule). Pending = cut at file time from the parent render.
def still(name,parent):
    p=f"{SS}/{name}_{parent}.png"; return p if os.path.exists(p) else f"{SS}/PENDING/{name}_{parent}.png"
BLOCK={"P10-2":"P10-1's rendered JACE closely resembles a real, famous actor (no-real-likeness rule). Needs Trundle's call before chaining off that frame.",
       "P10-3":"Chains off P10-2 (blocked: JACE likeness).",
       "P14-1":"Attached Ch14 sheet v2 does not show KILO (red tracksuit, bucket hat); no KILO image exists. Needs a KILO ref (look sheet = GenerateImage, needs Trundle's yes) or his OK to use a sheet character.",
       "P14-2":"Chains off P14-1 (blocked: no KILO image).","P14-3":"Chains off P14-1 (blocked: no KILO image)."}
def sub(x,pat,rep): return re.sub(pat,rep,x)
def fix(cid,spec,notes):
    ex=spec.get("extra",[]); rf={}
    parent=os.path.basename(spec.get("start_frame") or "").replace("_last.png","") or None
    chn=int(cid[1:3]) if cid.startswith("P") else (2 if cid.startswith("LS") else None)
    if chn in SHEET_MISMATCH and spec.get("refs_raw") and "SHEET_" in spec["refs_raw"][0]:
        notes.append(f"v4.2: channel sheet {os.path.basename(spec['refs_raw'][0])} removed from refs: it does not show the named cast, so it contradicted the start frame")
        spec["refs_raw"]=[]
    def name_only(name,pat,img):
        nonlocal ex
        rf[name]=img; ex=[sub(x,pat,f"{name} (<REF:{name}>)") for x in ex]
    if cid=="P03-3": name_only("MAE",r"MAE: [^\]]*",still("MAE",parent))
    if cid in("P07-2","P07-3"):
        name_only("RITA",r"RITA: [^\]]*",still("RITA",parent)); rf["BEAR"]=still("BEAR",parent)
        ex=[sub(x,r"Monster: a giant mechanical bear[^\]]*","Monster: the giant mechanical bear (<REF:BEAR>)") for x in ex]
    if cid in("P08-2","P08-3"):
        name_only("DEV",r"DEV: [^\]]*",still("DEV",parent)); name_only("OSCAR",r"OSCAR: [^\]]*",still("OSCAR",parent))
    if cid in("P09-2","P09-3"):
        name_only("VIK",r"VIK: [^\]]*",still("VIK",parent)); name_only("SABLE",r"SABLE: [^\]]*",still("SABLE",parent))
    if cid in("P12-2","P12-3"):
        name_only("DALE",r"DALE: [^\]]*",still("DALE",parent))
        ex=[sub(x,r"Van: white news van","Van: the news van (<IMAGE_0>)") for x in ex]
    if cid=="P06-3":
        name_only("CANDY",r"Host CANDY: [^\]]*","<START>"); ex=[x.replace("Host CANDY (","Host CANDY (").replace(", a chunky orange cooler"," (<IMAGE_0>)") for x in ex]
    if cid=="P02-3": name_only("TESS",r"Field reporter TESS: [^\]]*",spec["refs_raw"][0]); ex=[x.replace("TESS (","Field reporter TESS (",1) if x.startswith("TESS") else x for x in ex]
    if cid=="P02-4":
        rf["MARLA DEAN"]=rf["RON PIKE"]=spec["refs_raw"][0]
        ex=[x.replace("MARLA DEAN (silver bob, plum blazer)","MARLA DEAN (<REF:MARLA DEAN>)").replace("RON PIKE (grey suit, red tie)","RON PIKE (<REF:RON PIKE>)").replace("Same studio desk look: the two","The two") for x in ex]
    if cid.startswith("LS"):
        rf["MARLA DEAN"]=rf["RON PIKE"]=spec["refs_raw"][0] if spec.get("refs_raw") else "<START>"
        ex=[x.replace("MARLA DEAN (silver bob, plum blazer)","MARLA DEAN (<REF:MARLA DEAN>)").replace("RON PIKE (grey suit, red tie)","RON PIKE (<REF:RON PIKE>)") for x in ex]
    if cid=="AD-Steve-Cold-Blooded-promo":
        rf["STEVE"]=spec["refs_raw"][0]
        ex=[x.replace("<IMAGE_0> is STEVE as he is now (lizard man, same red bowling shirt and khakis)","STEVE (<REF:STEVE>), now in his red bowling shirt and khakis (not in <REF:STEVE>)") for x in ex]
    if cid=="P02-4":
        rf["TESS"]=R41.SHEETS[2]; ex=[sub(x,r"Field reporter TESS: [^\]]*","Field reporter TESS (<REF:TESS>)") for x in ex]
    if chn in SHEET_MISMATCH and not spec.get("refs_raw"): spec["refs_raw"]=[p for p in rf.values() if p!="<START>"]
    spec["extra"]=ex; spec["ref_for"]={**(spec.get("ref_for") or {}),**rf}
    return notes
_orig=R41.run_one
def run_one(group,cid,old,spec,notes,log):
    notes=list(notes)
    if group=="lipsync" and not spec.get("refs_raw"): spec["refs_raw"]=[R41.SHEETS[2]]
    if group=="round9-starters":
        chn=int(cid[1:3])
        if not spec.get("refs_raw") and chn!=4 and chn in R41.SHEETS: spec["refs_raw"]=[R41.SHEETS[chn]]
    fix(cid,spec,notes)
    if cid in BLOCK:
        r=B42.build(spec,strict=False); os.makedirs(f"{OUT}/BLOCKED",exist_ok=True)
        json.dump({"id":cid,"why":BLOCK[cid],"draft_args":r["args"],"notes":notes},open(f"{OUT}/BLOCKED/{cid}.json","w"),indent=1)
        R41.LOG.append({"group":group,"id":cid,"status":"BLOCKED","fails":["v4.2: "+BLOCK[cid]],"warns":[],"v4":None,"v41":r["args"]["prompt"],"notes":sorted(set(notes))}); return
    _orig(group,cid,old,spec,notes,log)
RG.run_one=run_one
if __name__=="__main__":
    for fn in (RG.odyssey,RG.round9,RG.commercials,RG.lipsync): fn([])
    v41={x["id"]:x for x in json.load(open(f"{H}/out/diff-v41.json"))}
    LOG=R41.LOG
    for x in LOG: x["v42"]=x.pop("v41"); x["v41"]=v41.get(x["id"],{}).get("v41"); x["v41_status"]=v41.get(x["id"],{}).get("status")
    json.dump(LOG,open(f"{H}/out/diff-v42.json","w"),indent=1)
    ok=[x for x in LOG if x["status"]=="OK"]
    with open(f"{H}/out/DIFF-v42.md","w") as f:
        f.write("# v4.1 -> v4.2 prompt diff (Trundle t371u: attached image => name + image tag only)\nGenerated by tools/regen_v42.py. No renders.\n\n")
        f.write(f"{len(ok)} OK / {len(LOG)} pending. Was 42 OK in v4.1.\n\n| id | v4.1 | v4.2 | why |\n|---|---|---|---|\n")
        for x in LOG: f.write(f"| {x['id']} | {x['v41_status']} | {x['status']} | {'; '.join(x['fails'])[:300]} |\n")
        for x in LOG:
            if x["v41_status"]=="OK" or x["status"]=="OK":
                f.write(f"\n## {x['id']} ({x['group']}) v4.1 {x['v41_status']} -> v4.2 {x['status']}\nnotes: {[n for n in x['notes'] if n.startswith('v4.2')]}\n\n**v4.1:** {x['v41']}\n\n**v4.2:** {x['v42']}\n")
    print(len(ok),"OK /",len(LOG))
    for x in LOG:
        if x["status"]!="OK" and x["v41_status"]=="OK": print("NEWLY BLOCKED",x["id"],x["fails"])
