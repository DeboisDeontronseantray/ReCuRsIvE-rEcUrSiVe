"""text_overlay.py - split comment prompts into gen_prompt + overlay[]; burn overlay onto a clean master (CNB, 2026-10-27 18:29 CT spec).
Offline only: ffmpeg drawtext + tesseract. No paid API. Never writes over an input; output must be a new path."""
import re,json,os,subprocess,tempfile,datetime,sys
import owner_denylist
HERE=os.path.dirname(os.path.abspath(__file__))
NO_TEXT="no on-screen text, no lettering"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def _kids():
    try: return json.load(open(os.path.join(HERE,"blocklists.json"))).get("kids",[])
    except Exception: return []
KID_WORDS=set(_kids())|{"kid","kids","child","children","baby","toddler","teen","minor","infant","kiddo","tween"}
QUOTE=re.compile(r'"([^"]+)"|\u201c([^\u201d]+)\u201d|(?<![A-Za-z])\'([^\']+)\'(?![A-Za-z])')
PRICE=re.compile(r'(?:\$\s?\d[\d,]*(?:\.\d{2})?|\d+(?:\.\d+)?\s?%\s?off|\b\d+(?:\.\d{2})\s?(?:dollars|bucks)\b)',re.I)
# trigger phrase -> role; captures unquoted text after it up to punctuation/connector
TRIG=[(r'(?i:put|stamp|slap|write|add)\s+(?i:the\s+word\s+)?([A-Z][A-Z0-9!\- ]{1,30}?)\s+(?:on|over|across)\b','caption'),
      (r'\bcaption(?:\s+(?:that\s+)?(?:says|reads|saying))?\s*[:\-]?\s*','caption'),
      (r'\btitle(?:\s+(?:that\s+)?(?:says|reads|saying))?\s*[:\-]?\s*','title'),
      (r'\btagline(?:\s+(?:says|reads))?\s*[:\-]?\s*','tagline'),
      (r'\b(?:sign|banner|label|text|headline|words?)\s+(?:that\s+)?(?:says|reads|saying)\s*[:\-]?\s*','caption'),
      (r'\btext\s+that\s+reads\s*','caption'),(r'\bwith\s+the\s+words\s*','caption'),
      (r'\b(?:have\s+it|make\s+it)\s+say\s*','caption')]
TEXT_HINT=re.compile(r'\b(say|says|saying|caption|title|tagline|headline|text|reads|words?|sign|banner|label|lettering|font|on[- ]screen)\b',re.I)
POS={"title":"top","caption":"bottom","price":"bottom_right","tagline":"bottom"}
def _role_near(prompt,start):
    pre=prompt[max(0,start-40):start].lower()
    for k in ("title","tagline","price","caption"):
        if k in pre: return k
    return "caption"
def split(prompt):
    """-> dict(gen_prompt, overlay[], text_detected, unsure). Non-text prompts: gen_prompt==prompt (no suffix), overlay==[]."""
    p=prompt or ""; ov=[]; spans=[]
    def add(t,role,s,e):
        t=t.strip(" .,;:!?") if role!="caption" or not t.strip().endswith("!") else t.strip(" .,;:")
        if t and not any(o["text"]==t for o in ov): ov.append({"text":t,"role":role,"position":POS[role]})
        spans.append((s,e))
    for m in QUOTE.finditer(p):
        t=next(g for g in m.groups() if g); add(t,_role_near(p,m.start()),m.start(),m.end())
    for m in PRICE.finditer(p):
        if any(s<=m.start()<e for s,e in spans): continue
        add(m.group(0),"price",m.start(),m.end())
    for rx,role in TRIG:
        for m in re.finditer(rx,p,re.I if not rx.startswith('(?i:put') else 0):
            if m.groups():
                add(m.group(1),role,m.start(1),m.end(1)); continue
            rest=p[m.end():]
            if any(s<=m.end()<e for s,e in spans) or rest[:1] in ('"',"'","\u201c","$"): continue
            mm=re.match(r'([^.,;\n]{1,40}?)(?=\s+(?:on|over|in|at|with|and)\b|[.,;\n]|$)',rest)
            if mm and mm.group(1).strip(): add(mm.group(1),role,m.end(),m.end()+mm.end())
    gen=p
    for s,e in sorted(set(spans),reverse=True): gen=gen[:s]+gen[e:]
    # strip leftover text-request verbs
    gen=re.sub(r'\b(?:put|stamp|slap|write|add)\s+(?:the\s+word\s+)?(?:on|over|across)\s+(?:it|the\s+\w+)\b','',gen,flags=re.I)
    gen=re.sub(r'\b(?:with\s+)?(?:a\s+|the\s+)?(?:caption|title|tagline|headline|sign|banner|label|text)\s+(?:that\s+)?(?:says|reads|saying)?\s*[:\-]?\s*(?=[.,;]|$|\s(?:and|on|in)\b)','',gen,flags=re.I)
    gen=re.sub(r'\b(?:with\s+the\s+words|text\s+that\s+reads|(?:have|make)\s+it\s+say|priced\s+at|for)\s*(?=[.,;]|$)','',gen,flags=re.I)
    gen=re.sub(r'\s{2,}',' ',re.sub(r'\s+([.,;])',r'\1',gen)).strip(" ,;:-")
    unsure=not ov and bool(TEXT_HINT.search(p))
    detected=bool(ov) or unsure
    if detected: gen=(gen+"; " if gen else "")+NO_TEXT
    return {"gen_prompt":gen if detected else p,"overlay":ov,"text_detected":detected,"unsure":unsure}
class Blocked(ValueError): pass
def check_text(overlay,allow_mb=False):
    """pre-burn filter; raises Blocked. owner real name, kid words, Military Boutique (unless allow_mb)."""
    for o in overlay:
        t=o["text"]; low=t.lower()
        if owner_denylist.overlay_name_pattern().search(low): raise Blocked("overlay names owner: blocked")
        words=set(re.findall(r"[a-z]+",low))
        hit=[k for k in KID_WORDS if (k in words if " " not in k and not k[0].isdigit() else k in low)]
        if hit: raise Blocked("overlay has kid word(s) %s"%hit)
        if not allow_mb and re.search(r'military\s*boutique',low): raise Blocked("overlay has Military Boutique without allow flag")
    return True
def _esc(t): return t.replace("\\","\\\\").replace(":","\\:").replace("'","\u2019").replace("%","\\%")
_XY={"top":("(w-text_w)/2","h*0.08"),"bottom":("(w-text_w)/2","h-text_h-h*0.08"),"bottom_right":("w-text_w-w*0.05","h-text_h-h*0.08"),"center":("(w-text_w)/2","(h-text_h)/2")}
def build_filter(overlay,fontsize=None):
    fs=[]
    for i,o in enumerate(overlay):
        x,y=_XY.get(o.get("position","bottom"),_XY["bottom"])
        if o.get("position")=="bottom" and i and overlay[i-1].get("position")=="bottom": y=y+"-text_h*1.6"
        size=fontsize or ("h/9" if o["role"] in ("title","price") else "h/12")
        en=":enable='between(t,%s,%s)'"%(o["start"],o["end"]) if "start" in o and "end" in o else ""
        fs.append(f"drawtext=fontfile={FONT}:text='{_esc(o['text'])}':fontsize={size}:fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=12:x={x}:y={y}{en}")
    return ",".join(fs) or "null"
def ocr_frame(video,t=0.5):
    d=tempfile.mkdtemp(prefix="ovocr_"); png=os.path.join(d,"f.png")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(t),"-i",video,"-frames:v","1","-vf","scale=iw*2:ih*2,format=gray,negate",png],check=True)
    env=dict(os.environ,OMP_THREAD_LIMIT="1")
    return subprocess.run(["tesseract",png,"-","--psm","11"],capture_output=True,text=True,env=env).stdout
def _norm(s): return re.sub(r'[^a-z0-9$]','',s.lower())
def burn(master,out,overlay,allow_mb=False,ocr_t=0.5):
    """Burn overlay onto master -> NEW file out. Returns report incl. OCR re-check. Refuses to overwrite."""
    if os.path.abspath(master)==os.path.abspath(out): raise ValueError("out must differ from master")
    if os.path.exists(out): raise FileExistsError(out+" exists; never overwrite")
    check_text(overlay,allow_mb)
    subprocess.run(["ffmpeg","-n","-loglevel","error","-i",master,"-vf",build_filter(overlay),"-c:a","copy","-c:v","libx264","-preset","veryfast","-crf","18",out],check=True)
    txt=ocr_frame(out,ocr_t); n=_norm(txt)
    found={o["text"]:_norm(o["text"]) in n for o in overlay}
    bad=[w for w in (owner_denylist.real_first(),"kid","child") if w in n]+([] if allow_mb else (["militaryboutique"] if "militaryboutique" in n else []))
    return {"out":out,"ocr_text":txt,"found":found,"ocr_ok":all(found.values()) and not bad,"ocr_blocked_hits":bad}
def lineage_row(parent_no,new_no,lineage,gen,overlay,prompt_ids,master,out,ocr_ok,**extra):
    """LINEAGE row for a text-only version (not written here; caller appends after trundle-approved flow)."""
    return {"row_type":"text_overlay_version","lineage":lineage,"gen":gen,"global_no":new_no,"parent_no":parent_no,"supersedes_no":None,
            "comment_prompt_ids":list(prompt_ids),"clean_master":master,"clip_path":out,"overlay":overlay,"paid_render":False,"render_cost_usd":0.0,
            "change_kind":"text_only","ocr_ok":ocr_ok,"thundertrundle_air_yes":False,"date":datetime.datetime.now().astimezone().isoformat(timespec="seconds"),"writer":"CNB",**extra}
# --- 18:40 CT add-only: delegate to the ONE shared splitter when present (local defs above stay as fallback) ---
sys.path.insert(0, os.environ.get("TT_SHARED_LIB", "/workspace/streaming/shared_lib"))
try:
    import overlay_split as _OS
except ImportError:
    _OS = None
else:
    NO_TEXT=_OS.NO_TEXT
    def split(prompt):
        r=_OS.split(prompt)
        return {"gen_prompt":r["gen_prompt"],"overlay":[{"text":i["text"],"role":i["role"],"position":POS.get(i["role"],"bottom")} for i in r["items"]],
                "text_detected":r["text_detected"],"unsure":r["unsure"]}
    def check_text(overlay,allow_mb=False):
        for o in overlay:
            b=_OS.blocked(o["text"],allow_mb)
            if b: raise Blocked("overlay %r blocked: %s"%(o["text"],b))
        return True
