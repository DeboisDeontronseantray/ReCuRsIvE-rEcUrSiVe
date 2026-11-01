#!/usr/bin/env python3
"""REF-POLICY v4 tools (free).
 state_stills(mp4, out_dir, clip_id, boxes={char:(x,y,w,h)}, details={name:(x,y,w,h)}) -> real last frame (-sseof) + crops; returns state_stills[] for the sidecar
 side_crop(sheet, box, out)    -> side / three-quarter crop from a look sheet (never the front view; SU1 pilot)
 commenter_filter(path)        -> {"filtered":bool,"reasons":[...],"fingerprint"} ; fail-closed: no face detector installed => needs manual clear
 distill(path)                 -> post-only uses FIRST: palette (k-means), LUT via palette_lut.py, mean colour; never likeness"""
import subprocess,os,json,hashlib
import numpy as np, cv2
SEEN=set()
CFG=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config","commenter_images.json")
def commenter_images_enabled():
    """NOT YET (Trundle 10:48 PM CT Oct 30): commenter-image option is switched off. config/commenter_images.json enabled=false."""
    try: return bool(json.load(open(CFG)).get("enabled"))
    except Exception: return False
def last_frame(mp4,out):
    subprocess.run(["ffmpeg","-v","error","-y","-sseof","-0.1","-i",mp4,"-frames:v","1","-update","1",out],check=True); return out
def state_stills(mp4,out_dir,clip_id,boxes,details=None,traits=None):
    os.makedirs(out_dir,exist_ok=True); lf=last_frame(mp4,f"{out_dir}/{clip_id}_last.png"); im=cv2.imread(lf); res=[]
    for ch,(x,y,w,h) in boxes.items():
        p=f"{out_dir}/{ch}_{clip_id}.png"; cv2.imwrite(p,im[y:y+h,x:x+w]); res.append({"char":ch,"path":p,"trait":(traits or {}).get(ch,"as now"),"from":lf})
    for n,(x,y,w,h) in (details or {}).items():
        p=f"{out_dir}/{n}_detail_{clip_id}.png"; cv2.imwrite(p,im[y:y+h,x:x+w]); res.append({"char":n,"path":p,"trait":"detail","from":lf,"detail":True})
    return res
def side_crop(sheet,box,out):
    im=cv2.imread(sheet); x,y,w,h=box; cv2.imwrite(out,im[y:y+h,x:x+w]); return out
def fingerprint(path):
    im=cv2.imread(path,cv2.IMREAD_GRAYSCALE); s=cv2.resize(im,(9,8)); return "".join("1" if a>b else "0" for a,b in zip(s[:,1:].flat,s[:,:-1].flat))
def commenter_filter(path,manual_clear=None,enabled=None):
    r=[]; fp=fingerprint(path)
    if not (commenter_images_enabled() if enabled is None else enabled):
        return {"filtered":False,"reasons":["commenter images disabled: NOT YET (Trundle 10:48 PM CT Oct 30)"],"fingerprint":fp,"disabled":True}
    if fp in SEEN: r.append("duplicate")
    SEEN.add(fp)
    im=cv2.imread(path)
    if im is None: return {"filtered":False,"reasons":["unreadable"],"fingerprint":fp}
    if not (manual_clear or {}).get("no_face"): r.append("face check unavailable on box (no detector model) -> needs manual clear")
    if not (manual_clear or {}).get("no_text"): r.append("OCR unavailable (no tesseract) -> needs manual clear")
    return {"filtered":not r,"reasons":r,"fingerprint":fp,"allowed_purposes":["prop","pattern","color","wardrobe","screen-insert","weather-hint","animal"]}
def distill(path,k=5):
    im=cv2.imread(path); Z=cv2.resize(im,(64,64)).reshape(-1,3).astype(np.float32)
    _,lab,cen=cv2.kmeans(Z,k,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,20,1.0),3,cv2.KMEANS_PP_CENTERS)
    cnt=np.bincount(lab.flatten(),minlength=k); order=np.argsort(-cnt)
    pal=["#%02x%02x%02x"%tuple(int(c) for c in cen[i][::-1]) for i in order]
    return {"palette":pal,"weights":[round(float(cnt[i]/cnt.sum()),3) for i in order],"use_order":["LUT/grade (post)","seam colour match (post)","palette words in Look line","prop/pattern ref (gen)"]}
