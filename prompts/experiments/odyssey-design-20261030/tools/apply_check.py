#!/usr/bin/env python3
"""APPLY-FROM-HERE checks (REASSESSMENT.md). New file; does not modify followability_check.py.
usage: apply_check.py <args.json> [sidecar.json]  -> prints PASS/FAIL/WARN per check."""
import json,re,sys
CAM=r"\b(push[- ]in|dolly|tracking|whip pan|handheld|crane|tilt|pan\b|static camera|locked|overhead hold|pull[- ]?back|orbit)"
def check(p,side=None,pinned=False,skills=()):
    r={};w=len(p.split())
    r["A1_words"]=("PASS" if w<=330 else "FAIL",w)
    n=len(re.findall(CAM,p,re.I)); r["A2_one_move"]=("PASS" if 1<=n<=2 else "WARN",n)
    r["A3_no_hold"]=("FAIL" if re.search(r"held still|settles",p,re.I) and not pinned else "PASS",)
    r["A4_ref_no_restate"]=("WARN" if re.search(r"<IMAGE_\d>",p) and re.search(r"\b(eyes (?!on|off|fixed|ahead)\w+|nose shape|cheekbones|jawline|skin tone)\b",p,re.I) else "PASS",)
    for s in skills: r[f"A5_skill_{s}"]=("PASS" if re.search(rf"At [\d.]+ s,[^.]*{s}",p,re.I) else "FAIL",)
    r["A6_behaviour"]=("WARN" if re.search(r"At [\d.]+ s, \w+ (dances|cries|feels|thinks)\.",p) else "PASS",)
    r["A7_literal"]=("WARN" if re.search(r"\b(angels?|raining cats|break a leg)\b",p,re.I) else "PASS",)
    r["A8_digits_state"]=("FAIL" if re.search(r"\b(health|hp|energy)\b[^.]{0,20}\d",p,re.I) else "PASS",)
    fights=re.findall(r"At [\d.]+ s,[^.]*\b(strike|punch|kick|hook|palm|tackle|swing|parr)\w*[^.]*\.",p,re.I)
    bad=[f for f in re.findall(r"At [\d.]+ s,[^.]*\b(?:strike|punch|kick|hook|tackle)\w*[^.]*\.",p,re.I) if not re.search(r"\b(lands?|hits?|catch|stagger|stumbl|spins|folds|drops|slides|tumbl|knock)",f,re.I)]
    r["A9_contact"]=("PASS" if not bad else "FAIL",len(bad))
    if side is not None: r["A10_versions"]=("PASS" if side.get("schema_version") and side.get("meta_version") else "FAIL",)
    r["A11_eyes"]=("PASS" if re.search(r"(never|not) (look\w* )?(at|into) the (camera|lens)|eyes off lens|never at (the )?camera|nobody looks into the camera",p,re.I) else "FAIL",)
    r["A12_safety"]=("PASS" if re.search(r"adults",p,re.I) else "FAIL",)
    beats=len(re.findall(r"At [\d.]+ s,",p)); r["A13_beats"]=("PASS" if beats<=4 else "FAIL",beats)
    r["A15_ch4"]=("FAIL" if re.search(r"\bCh ?4\b(?! Military Boutique / BLACK ICE)",p) else "PASS",)
    return r
if __name__=="__main__":
    a=json.load(open(sys.argv[1])); s=json.load(open(sys.argv[2])) if len(sys.argv)>2 else None
    m=a.get("_odyssey",{})
    res=check(a["prompt"],s,m.get("pinned",False),m.get("skills_used",[]))
    for k,v in res.items(): print(k,*v)
    sys.exit(1 if any(v[0]=="FAIL" for v in res.values()) else 0)
