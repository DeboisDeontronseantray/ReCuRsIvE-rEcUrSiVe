#!/usr/bin/env python3
"""Gate v4.4 = gate v4.2 + closed R-REF exemption list (config/ref_image_exemptions.json).
Trundle 11:09 PM CT Oct 30: "Ref image: yes, hard rule." / 11:10 PM (relayed): "I didn't know they were ads. These specific ads can run without an image".
Only R-REF is skipped, only for the exact listed IDs. R-REFDESC already applies only when an image tag is attached, so written looks are fine for these no-image ads."""
import os,json,apply_check_v42 as G42
CFG=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config","ref_image_exemptions.json")
KREF="R-REF required (t132u)"
def exempt_ids():
    d=json.load(open(CFG)); ids=d["ids"]
    if len(ids)!=16 or d.get("count")!=16 or len(set(ids))!=16: raise ValueError("ref_image_exemptions.json must list exactly the 16 approved ads")
    return frozenset(ids)
def check(p,args=None,spec=None,side=None,clip_id=None):
    r=G42.check(p,args,spec,side)
    if clip_id in exempt_ids() and r[KREF][0]=="FAIL" and not (args or {}).get("reference_image_paths"):
        r[KREF]=("PASS","EXEMPT (Trundle 11:10 PM CT Oct 30)")
    return r
