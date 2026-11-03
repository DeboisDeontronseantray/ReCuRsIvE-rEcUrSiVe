#!/usr/bin/env python3
"""build_prompt_v42 = build_prompt_v41 (fixed slot order, [Look], beats, dialogue format, rules bracket all UNCHANGED) + trundle t371u:
an item with an attached image is named and pointed at its tag only, e.g. 'GIDEON QUILL (<IMAGE_2>)'. Text descriptions stay only for items with no image.
Supersedes round9 REF-POLICY.md (b) 'ref present -> name + 2-3 visual keys' (Director's invention, never trundle's).
spec['ref_for'] = {NAME: image_path}: attach that image and point NAME at it (placeholder <REF:NAME> in extra text is resolved to its tag)."""
import re,hashlib,os,sys,copy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import build_prompt_v41 as B41, apply_check_v42 as gate
H=B41.H; STATIC=B41.STATIC; LOCKS=B41.LOCKS; GateFail=B41.GateFail
META="system-v4.2-20261030"; BUILDER={"name":"build_prompt_v42","version":"4.2.0"}
def strip_desc(p):
    def paren(m):
        segs=[]
        for seg in m.group(1).split(";"):
            seg=seg.strip()
            if not seg.startswith("<IMAGE_"): continue
            parts=re.split(r",\s*",seg); keep=[parts[0]]+[x for x in parts[1:] if x.startswith("<IMAGE_")]
            segs.append(", ".join(keep))
        return "("+"; ".join(segs)+")" if segs else m.group(0)
    p=re.sub(r"\(([^()]*<IMAGE_\d+>[^()]*)\)",lambda m: paren(m) if re.search(gate.VIS,m.group(1),re.I) else m.group(0),p)
    p=re.sub(r"(\(<IMAGE_\d+>\))\s*:\s*[^\]]+\]",r"\1.]",p)
    p=re.sub(r"(as (?:in |seen in )?<IMAGE_\d+>)\s*[:,]\s*[^\]]+\]",r"\1.]",p)
    return p
def build(spec,strict=True):
    spec=copy.deepcopy(spec); rf=spec.get("ref_for") or {}
    refs=list(spec.get("refs_raw") or [])
    for n,path in rf.items():
        if path!="<START>" and path not in refs: refs.append(path)
    spec["refs_raw"]=refs; off=1 if spec.get("start_frame") else 0
    for c in spec.get("cast",[]):
        if c.get("ref"): c["keys"]=[]
    def tag(n): return "<IMAGE_0>" if rf[n]=="<START>" else f"<IMAGE_{refs.index(rf[n])+off}>"
    spec["extra"]=[re.sub(r"<REF:([^>]+)>",lambda m:tag(m.group(1)),x) for x in spec.get("extra",[])]
    r=B41.build(spec,strict=False)
    p=strip_desc(r["args"]["prompt"]); p=re.sub(r"\s+"," ",p).replace(" .",".").replace("..",".")
    r["args"]["prompt"]=p
    s=r["sidecar"]; s.update(meta_version=META,builder=BUILDER|{"sha":hashlib.sha256(open(__file__,"rb").read()).hexdigest()[:12]},
        prompt_sha256=hashlib.sha256(p.encode()).hexdigest(),prompt_words=len(p.split()),ref_for={k:os.path.basename(v) for k,v in rf.items()},
        contributors=list(spec.get("contributors") or []), contributors_rule="data follows the image/clip; never in prompt (trundle 10:48 PM CT Oct 30)")
    rep=gate.check(p,r["args"],spec,s); r["report"]=rep
    fails={k:v for k,v in rep.items() if v[0]=="FAIL"}
    if fails and strict: raise GateFail(f"{spec['clip_id']}: {fails}")
    return r
def write(spec,outdir):
    import json; r=build(spec); os.makedirs(outdir,exist_ok=True)
    json.dump(r["args"],open(f"{outdir}/{spec['clip_id']}.args.json","w"),indent=1); json.dump(r["sidecar"],open(f"{outdir}/{spec['clip_id']}.meta.json","w"),indent=1); return r
