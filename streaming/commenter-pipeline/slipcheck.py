"""Tag-slip watchlist + post-render slip check (CNB, trundle 2026-10-27 17:13 CT). Home-only, $0, ffmpeg/tesseract only.
Shared watchlist: /workspace/shared/streaming/tag-slip-watchlist.jsonl (append-only, CNB sole writer, Story Bot reads).
Slip log: /workspace/shared/streaming/tag-slip-log.jsonl. Never deletes; held copies are copies."""
import json,os,re,glob,uuid,shutil,subprocess,hashlib,datetime,zoneinfo
import numpy as np
from PIL import Image
CT=zoneinfo.ZoneInfo("America/Chicago"); now=lambda: datetime.datetime.now(CT).isoformat(timespec="seconds")
P=os.path.dirname(os.path.abspath(__file__))
WL="/workspace/shared/streaming/tag-slip-watchlist.jsonl"; SLIPLOG="/workspace/shared/streaming/tag-slip-log.jsonl"
CH4="/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique"; LINEAGE=f"{CH4}/LINEAGE.jsonl"
TAG_RE=r"\b4\.\d+\s*g\d+|#\d+|from #|4\.1"
BADGE=(1078,12,1268,74)  # on 1280x720
PH_DIST=10  # dHash hamming threshold (64-bit)
def sha(f):
    h=hashlib.sha256()
    with open(f,"rb") as fh:
        for b in iter(lambda: fh.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def wl_rows():
    if not os.path.isfile(WL): return []
    out=[]
    for l in open(WL):
        try: out.append(json.loads(l))
        except Exception: pass
    return out
def wl_add(found_in,reason,sha256=None,name_pattern=None,phash=None,regex=None):
    os.makedirs(os.path.dirname(WL),exist_ok=True)
    have={(r.get("sha256"),r.get("name_pattern"),r.get("phash")) for r in wl_rows()}
    k=(sha256,name_pattern,phash)
    if k in have: return False
    open(WL,"a").write(json.dumps({"sha256":sha256,"name_pattern":name_pattern,"phash":phash,"regex":regex,"reason":reason,"found_in":found_in,"date":now(),"added_by":"CNB"})+"\n"); return True
def lineage_rows():
    out=[]
    for l in open(LINEAGE):
        try: out.append(json.loads(l))
        except Exception: pass
    return out
def tainted_lineage():
    return {r["sha256"]:r for r in lineage_rows() if r.get("sha256") and (r.get("origin")=="overlay_edit" or r.get("role")=="air_copy" or r.get("air_copy"))}
def allow_shas(rows=None):
    """Exact-sha clean-master allowlist (row_type clean_master_allow). Wins over watchlist hash/name hits (1730)."""
    return {r["sha256"] for r in (rows if rows is not None else wl_rows()) if r.get("row_type")=="clean_master_allow" and r.get("sha256")}
def hit_rows(rows): return [r for r in rows if r.get("row_type")!="clean_master_allow"]
def watch_guard(path):
    """Extra input_guard check: watchlist sha / name pattern. Returns reason or None."""
    name=os.path.basename(path); allrows=wl_rows(); rows=hit_rows(allrows)
    if os.path.isfile(path) and sha(path) in allow_shas(allrows): return None
    for r in rows:
        if r.get("name_pattern") and re.search(r["name_pattern"],name,re.I): return f"watchlist name pattern {r['name_pattern']!r}: {name}"
    if os.path.isfile(path):
        s=sha(path)
        if any(r.get("sha256")==s for r in rows): return f"watchlist sha256 match: {name}"
        if path.lower().endswith((".png",".jpg",".jpeg",".mp4",".mov")):
            hs=[r["phash"] for r in rows if r.get("phash") and "badge-region" in (r.get("reason") or "")]  # full-frame pHash would match clean masters of badged clips
            if hs:
                for fp in frame_hashes(path,n=3):
                    for h in hs:
                        if ham(fp["badge"],h)<=PH_DIST: return f"watchlist perceptual match ({h}): {name}"
    return None
# ---- frames / hashes
def frames(src,n=6):
    tmp=f"/tmp/sc_{uuid.uuid4().hex[:6]}"; os.makedirs(tmp)
    if src.lower().endswith((".png",".jpg",".jpeg")):
        shutil.copy(src,f"{tmp}/f001.png")
    else:
        d=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",src],capture_output=True,text=True).stdout or 1)
        for i in range(n):
            subprocess.run(["ffmpeg","-v","error","-ss",f"{d*(i+0.5)/n:.2f}","-i",src,"-frames:v","1","-vf","scale=1280:720",f"{tmp}/f{i:03d}.png"])
    ims=[Image.open(f).convert("RGB").resize((1280,720)) for f in sorted(glob.glob(f"{tmp}/*.png"))]
    shutil.rmtree(tmp); return ims
def dhash(im):
    g=np.asarray(im.convert("L").resize((9,8),Image.LANCZOS),dtype=np.int16)
    return "%016x"%int("".join("1" if b else "0" for b in (g[:,1:]>g[:,:-1]).flatten()),2)
def ham(a,b): return bin(int(a,16)^int(b,16)).count("1")
def frame_hashes(src,n=6):
    return [{"full":dhash(im),"badge":dhash(im.crop(BADGE))} for im in frames(src,n)]
def badge_box(im):
    """Dark box with bright text in badge region, darker than the area just below/left. Returns (bool,stats)."""
    a=np.asarray(im.convert("L"),dtype=np.float32)
    x0,y0,x1,y1=BADGE; reg=a[y0:y1,x0:x1]
    ring=np.concatenate([a[y1+6:y1+40,x0:x1].ravel(),a[y0:y1,x0-60:x0-6].ravel()])
    dark=(reg<45).mean(); bright=(reg>170).mean()
    st={"dark_frac":round(float(dark),3),"bright_frac":round(float(bright),3),"reg_mean":round(float(reg.mean()),1),"ring_mean":round(float(ring.mean()),1)}
    hit=dark>0.55 and 0.02<bright<0.35 and ring.mean()-reg.mean()>12
    d=reg[reg<45]; st["dark_std"]=round(float(d.std()),1) if d.size else None
    st["strong"]=bool(hit and dark>0.85 and d.size and d.std()<4)  # flat drawtext box; dark scenery is textured
    return hit,st
def ocr_badge(im):
    tmp=f"/tmp/ocrb_{uuid.uuid4().hex[:6]}.png"
    im.crop((BADGE[0]-10,BADGE[1]-6,1280,BADGE[3]+8)).resize((4*(1280-BADGE[0]+10),4*(BADGE[3]-BADGE[1]+14))).save(tmp)
    o=subprocess.run(["tesseract",tmp,"-","--psm","6"],capture_output=True,text=True).stdout; os.remove(tmp)
    return o.strip(), bool(re.search(TAG_RE,o))
_AIR=None
def air_hashes():
    global _AIR
    if _AIR is None:
        _AIR=[]
        for s,r in tainted_lineage().items():
            if os.path.isfile(r.get("file","")): _AIR.append((r.get("tag"),r["file"],frame_hashes(r["file"],4)))
    return _AIR
def visual(src):
    out={"badge_frames":0,"ocr_frames":0,"ocr_text":[],"near_air":[],"n":0}
    ims=frames(src,6); out["n"]=len(ims); box_hits=0; stats=[]
    for im in ims:
        hit,st=badge_box(im); stats.append(st)
        if hit: out["badge_frames"]+=1
        if st.get("strong"): out["strong_badge_frames"]=out.get("strong_badge_frames",0)+1
        t,m=ocr_badge(im)
        if m: out["ocr_frames"]+=1; out["ocr_text"].append(t[:40])
    out["badge_stats"]=stats
    mine=[{"full":dhash(im),"badge":dhash(im.crop(BADGE))} for im in ims]
    for tag,f,hs in air_hashes():
        if os.path.realpath(f)==os.path.realpath(src): continue
        best=min(min(ham(a["full"],b["full"]),ham(a["badge"],b["badge"])+0) for a in mine for b in hs)
        bfull=min(ham(a["full"],b["full"]) for a in mine for b in hs); bbad=min(ham(a["badge"],b["badge"]) for a in mine for b in hs)
        if bfull<=PH_DIST and bbad<=PH_DIST+4: out["near_air"].append({"tag":tag,"file":os.path.basename(f),"full_ham":bfull,"badge_ham":bbad})
    out["near_air"]=[x for x in out["near_air"] if out["badge_frames"]+out["ocr_frames"]>0 or (x["full_ham"]<=3 and x["badge_ham"]<=3)]  # clean masters share content with their air copies; need corner evidence too
    out["tagged"]=out.get("strong_badge_frames",0)>=max(2,out["n"]//2) or out["ocr_frames"]>=2
    out["review_only"]=(not out["tagged"]) and out["badge_frames"]>=max(2,out["n"]//2)  # weak dark-corner hit: note, don't hold
    out["_hashes"]=mine; return out
# ---- main check
def slipcheck(mp4,inputs=None,parent=None,act=True,clip_id=None):
    """inputs: list of {path,sha256} recorded at render. Returns report dict. Flags => held copy + SLIP report + watchlist + lineage correction + slip log."""
    taint=tainted_lineage(); wl=hit_rows(wl_rows()); wsh={r["sha256"] for r in wl if r.get("sha256")}; allow=allow_shas()
    own=sha(mp4); lrow=next((r for r in lineage_rows() if r.get("sha256")==own),None)
    is_air=own in taint or own in wsh
    rep={"file":mp4,"sha256":own,"time":now(),"lineage_tag":(lrow or {}).get("tag"),"parent":parent,"inputs":inputs or [],"prov_hits":[]}
    for i in inputs or []:
        s=i.get("sha256") or (sha(i["path"]) if os.path.isfile(i.get("path","")) else None)
        if s in allow: continue  # exact clean-master sha wins
        if s in taint: rep["prov_hits"].append({**i,"why":f"input sha is lineage {taint[s].get('origin') or taint[s].get('role')} {taint[s].get('tag')}"})
        elif s in wsh: rep["prov_hits"].append({**i,"why":"input sha on watchlist"})
        elif i.get("path") and watch_guard(i["path"]): rep["prov_hits"].append({**i,"why":watch_guard(i["path"])})
        elif i.get("path") and os.path.isfile(i["path"]) and i["path"].lower().endswith((".png",".jpg",".jpeg",".mp4",".mov")):
            ims=frames(i["path"],3)
            if any(badge_box(im)[0] or ocr_badge(im)[1] for im in ims): rep["prov_hits"].append({**i,"why":"input frame carries corner tag/badge (visual)"})
    v=visual(mp4); hashes=v.pop("_hashes"); rep["visual"]=v
    if is_air:
        rep["verdict"]="AIR_COPY (tag is intended; not a slip)" if own in taint or "air copy" in str([r.get("reason") for r in wl if r.get("sha256")==own]) else "KNOWN_TAINTED (on watchlist; badged/overlay copy, never a parent)"; rep["flag"]=False; return rep
    rep["flag"]=bool(rep["prov_hits"] or v["tagged"] or v["near_air"])
    rep["verdict"]="SLIP" if rep["flag"] else "CLEAN"
    if rep["flag"] and act: _act(mp4,rep,hashes,clip_id)
    return rep
def _act(mp4,rep,hashes,clip_id):
    cid=clip_id or os.path.basename(mp4)[:-4]; held=f"{P}/outbox/held"; os.makedirs(held,exist_ok=True)
    hc=f"{held}/{os.path.basename(mp4)}"
    if os.path.realpath(mp4)!=os.path.realpath(hc): shutil.copy2(mp4,hc)
    rep["held_copy"]=hc
    json.dump({"id":cid,"status":"held-tag-slip","file":hc,"report":f"SLIP_{cid}.json","time":now()},open(f"{held}/{os.path.basename(mp4)[:-4]}_SLIP_manifest.json","w"),indent=1)
    added=[]
    for h in rep["prov_hits"]:
        if wl_add(cid,"input of slipped render: "+h["why"],sha256=h.get("sha256")): added.append("input sha")
        if h.get("path"):
            for fh in frame_hashes(h["path"],3)[:1]:
                if wl_add(cid,"pHash of slipped input",phash=fh["full"]): added.append("input phash")
                if wl_add(cid,"badge-region dHash of slipped input",phash=fh["badge"]): added.append("input badge phash")
    if hashes:
        if wl_add(cid,"dHash of slipped output frame",phash=hashes[0]["full"]): added.append("output phash")
        if wl_add(cid,"badge-region dHash of slipped output",phash=hashes[0]["badge"]): added.append("output badge phash")
    if wl_add(cid,"slipped output sha (never use as input)",sha256=rep["sha256"]): added.append("output sha")
    for h in rep["prov_hits"]:
        n=os.path.basename(h.get("path",""))
        m=re.search(r"(_[a-z]+tagged|_ch4badge|_salesad\w*)",n,re.I)
        if m and not any(r.get("name_pattern") and re.search(r["name_pattern"],n,re.I) for r in wl_rows()):
            wl_add(cid,"new name pattern from slip",name_pattern=re.escape(m.group(1))); added.append("name pattern")
    rep["watchlist_added"]=added
    json.dump(rep,open(f"{held}/SLIP_{cid}.json","w"),indent=1)
    open(LINEAGE,"a").write(json.dumps({"correction_for_sha256":rep["sha256"],"correction_for_tag":rep.get("lineage_tag"),"clip_id":cid,"slip":True,"reason":rep["verdict"]+": "+"; ".join([h["why"] for h in rep["prov_hits"]]+(["visual tag/badge in output"] if rep["visual"]["tagged"] else [])+(["near air copy "+x["tag"] for x in rep["visual"]["near_air"] if x.get("tag")])),"date":now(),"writer":"CNB","row_type":"correction"})+"\n")
    os.makedirs(os.path.dirname(SLIPLOG),exist_ok=True)
    open(SLIPLOG,"a").write(json.dumps({"time":now(),"clip_id":cid,"file":mp4,"sha256":rep["sha256"],"held_copy":hc,"prov_hits":[h["why"] for h in rep["prov_hits"]],"visual_tagged":rep["visual"]["tagged"],"near_air":rep["visual"]["near_air"],"watchlist_added":added,"by":"CNB"})+"\n")
def seed():
    n=0
    for f in sorted(glob.glob(f"{CH4}/lineage-tagged-20261027/*.mp4")):
        n+=wl_add(os.path.relpath(f,CH4),"seed: lineage-tagged air copy",sha256=sha(f))
    for f in sorted(glob.glob(f"{CH4}/ch4badge-20261027/**/*.mp4",recursive=True)):
        n+=wl_add(os.path.relpath(f,CH4),"seed: held ch4badge copy",sha256=sha(f))
    for pat,why in [(r"_tagged","lineage-tagged air copy name"),(r"_ch4badge","ch4badge copy name"),(r"salesad","sales-overlay copy name"),(r"(^|/)lineage-tagged-","tagged folder")]:
        n+=wl_add("seed",why,name_pattern=pat)
    n+=wl_add("seed","on-screen genealogy/badge text",regex=TAG_RE)
    return n
