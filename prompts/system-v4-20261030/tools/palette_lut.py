#!/usr/bin/env python3
"""palette_lut.py REF.png OUT.cube [size=17] [strength=0.6] — 3D LUT that moves a clip's colour statistics toward a reference (per-channel mean/std in Lab),
for ffmpeg lut3d (post-only, zero gen risk; IMAGE-DISTILL rank 2). Apply: ffmpeg -i in.mp4 -vf lut3d=OUT.cube out.mp4
Optional SRC.png (3rd arg via --src) = a frame of the clip to match FROM (default neutral stats)."""
import sys,numpy as np,cv2
def stats(p):
    lab=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32); return lab.mean(0),lab.std(0)+1e-3
def make(ref,out,size=17,strength=0.6,src=None):
    rm,rs=stats(ref); sm,ss=stats(src) if src else (np.array([128,128,128],np.float32),np.array([60,12,12],np.float32))
    g=np.linspace(0,1,size); lines=[f"LUT_3D_SIZE {size}"]
    for b in g:
        for gg in g:
            for r in g:
                px=np.uint8([[[b*255,gg*255,r*255]]]); lab=cv2.cvtColor(px,cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
                t=(lab-sm)/ss*rs+rm; lab2=np.clip(lab+(t-lab)*strength,0,255).astype(np.uint8)
                o=cv2.cvtColor(np.uint8([[lab2]]),cv2.COLOR_LAB2BGR)[0,0]/255.0
                lines.append(f"{o[2]:.5f} {o[1]:.5f} {o[0]:.5f}")
    open(out,"w").write("\n".join(lines)+"\n"); return out
if __name__=="__main__":
    a=[x for x in sys.argv[1:] if not x.startswith("--")]; src=next((x.split("=",1)[1] for x in sys.argv if x.startswith("--src=")),None)
    make(a[0],a[1],int(a[2]) if len(a)>2 else 17,float(a[3]) if len(a)>3 else 0.6,src)
