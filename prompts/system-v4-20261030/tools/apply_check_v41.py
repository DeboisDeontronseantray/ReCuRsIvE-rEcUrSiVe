#!/usr/bin/env python3
"""Gate v4.1. FAIL only on Trundle's own rules (RULES-OF-RECORD.md ids). Our inventions are WARN (never block).
Dropped from v4: V14 transform still (Steve misread, t370u), A1 word cap / A13 beat cap as FAILs (t212u 'pack more'; weird dense = plus),
V16 cut words / 'no on-screen text' (t38u prefers in-video text; t143u 'Quick cuts'), V4/V5 as FAILs (our finding, not his rule)."""
import re
CAM=r"\b(dolly|tracking|pan|tilt|crane|zoom|push-in|pull-back|whip|orbit|handheld|static camera)\b"
ORDER=["[Look","[Setting|[Cast|[","Continue|Single shot|Camera|Tracking|Shot","At ","Motion carries on|The last 0.4 s","[Adults"]
def check(p,args=None,spec=None,side=None):
    args=args or {}; spec=spec or {}; r={}; ch=spec.get("channel","")
    # --- Trundle rules (FAIL) ---
    r["R-REF required (t132u)"]=("PASS" if args.get("reference_image_paths") else "FAIL",)
    r["R-NOREFSTART ref never start frame (t121u)"]=("FAIL" if args.get("image_path") and args.get("image_path") in (args.get("reference_image_paths") or []) else "PASS",)
    r["R-EYES nobody into camera (Oct 29 rule)"]=("PASS" if re.search(r"Nobody looks into the camera",p) else "FAIL",)
    r["R-GORE his wording (t212u, Oct 29 7:05 PM, Oct 30 4:42 PM)"]=("FAIL" if re.search(r"no (wounds|blood) on skin|no wounds or blood|stage-combat|theatrical props only",p,re.I) or "No gore" not in p else "PASS",)
    r["R-KIDS no kids"]=("PASS" if re.search(r"no kids",p,re.I) else "FAIL",)
    r["R-CH4 photoreal 1971 (Oct 30 7:13 PM)"]=("FAIL" if ch.startswith("Ch4") and (re.search(r"hand-?inked|ink outlines|crosshatch|flat 2D|comic",p,re.I) or not re.search(r"photoreal|live-action|live action",p,re.I) or any(re.search(r"shinkawa|_ink|SHEET_HERON|SHEET_WOLFHOUND",x,re.I) for x in args.get("reference_image_paths") or [])) else "PASS",)
    r["R-CH4NAME 'Ch4 Military Boutique / BLACK ICE'"]=("FAIL" if re.search(r"\b(Ch ?4(?! Military Boutique / BLACK ICE)|Channel 4\.\d|4\.1 )",p) else "PASS",)
    r["R-JUMPS no held still (F4 'jumps')"]=("FAIL" if re.search(r"held still|settles into",p,re.I) and not spec.get("pinned") else "PASS",)
    r["R-END ending line"]=("PASS" if re.search(r"Motion carries on through the last half second|eases into the planned end image",p) else "FAIL",)
    r["R-OVERLAY no tags/state digits in prompt (overlays post)"]=("FAIL" if re.search(r"\b(health|hp)\b[^.]{0,20}\d|genealogy tag|g\d+ #\d+",p,re.I) else "PASS",)
    r["R-SECCAM high mounted (t171u)"]=("FAIL" if re.search(r"security[- ](cam|feed|camera)",p,re.I) and not re.search(r"high|mounted|ceiling|above|corner",p,re.I) else "PASS",)
    q=re.findall(r'"[^"]+"',p); spk=re.findall(r'\b[A-Z][A-Z .\']{1,30} speaks \[',p)
    bad=[]
    pm=re.sub(r'"[^"]*"',lambda m:'"'+"x"*(len(m.group(0))-2)+'"',p)
    for sent in re.split(r"(?<=[.\]])\s+(?=[A-Z\[])",pm):
        if '"' in sent and not (re.search(r'speaks \[[^\]]*"',sent) and re.search(r"\b[A-Z]{2,}",sent.split("speaks")[0])): bad.append(sent[:60])
    r["R-SPEAKER named + bracketed (t134u,t139u)"]=("FAIL" if bad else "PASS",bad)
    r["R-BRACKETS non-direction in brackets (t155u)"]=("PASS" if p.startswith("[") and p.rstrip().endswith("]") else "FAIL",)
    pos=[]; 
    for k in ["[Look","Motion carries on|The last 0.4 s","[Adults"]:
        m=re.search(re.escape(k) if "|" not in k else k,p); pos.append(m.start() if m else -1)
    r["R-ORDER fixed slots"]=("PASS" if -1 not in pos and pos==sorted(pos) else "FAIL",pos)
    if ch.startswith("Ch4"): r["R-PINK no pink/yellow on Ch4 (working reading)"]=("WARN" if re.search(r"\b(pink|yellow)\b",p,re.I) else "PASS",)
    r["R-REMAKE no remakes of completed ads (Oct 29 12:00 PM)"]=("FAIL" if spec.get("remake_of") else "PASS",)
    # --- our learnings (WARN only) ---
    w=len(p.split()); r["W-words"]=("WARN" if w>330 else "PASS",w)
    n=len(re.findall(r"At [\d.]+ s,",p)); r["W-beats"]=("WARN" if n>6 else "PASS",n)
    m=len(re.findall(CAM,p,re.I)); r["W-one-move (r9: big camera change -> model adds cuts)"]=("WARN" if m>2 else "PASS",m)
    r["W-start-frame-for-tracking (SU1)"]=("WARN" if re.search(r"tracking|dolly|dashcam|aerial",p,re.I) and not args.get("image_path") else "PASS",)
    r["W-eyeline target"]=("PASS" if re.search(r"looks? at",p) else "WARN",)
    r["W-front refs (SU1)"]=("WARN" if any(re.search(r"_front|SHEET_",x) for x in args.get("reference_image_paths") or []) else "PASS",)
    r["X-missing ref file (TBD)"]=("FAIL" if any("TBD" in x for x in args.get("reference_image_paths") or []) else "PASS",)
    nimg=(1 if args.get("image_path") else 0)+len(args.get("reference_image_paths") or [])
    ix=[int(x) for x in re.findall(r"<IMAGE_(\d+)>",p)]
    r["X-image numbering matches attached images"]=("FAIL" if ix and (max(ix)>=nimg or min(ix)<0) else "PASS",ix,nimg)
    return r
