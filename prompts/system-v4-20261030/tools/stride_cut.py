#!/usr/bin/env python3
"""stride_cut.py OUT.mp4 A.mp4 B.mp4 ... — suit-up join: trim each clip at the frame where the leading foot plants
(minimum of the moving subject's bbox bottom velocity in the lower third, via frame differencing), 0.1 s crossfade max, no labels.
Audio is dropped from clips; lay one continuous bed in post (SUIT-UP-TRACKING). --dry prints cut points only."""
import sys,subprocess,json,numpy as np,cv2
def plants(mp4):
    cap=cv2.VideoCapture(mp4); fps=cap.get(cv2.CAP_PROP_FPS) or 24; prev=None; bottoms=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        g=cv2.GaussianBlur(cv2.cvtColor(f,cv2.COLOR_BGR2GRAY),(5,5),0)
        if prev is None: bottoms.append(np.nan)
        else:
            m=(cv2.absdiff(g,prev)>18); h=m.shape[0]; low=m[int(h*0.55):]
            ys=np.where(low.any(1))[0]; bottoms.append(float(ys.max()) if len(ys) else np.nan)
        prev=g
    b=np.array(bottoms); n=len(b)
    if n<3: return fps,[],n
    v=np.abs(np.diff(np.nan_to_num(b,nan=np.nanmean(b) if np.isfinite(b).any() else 0)))
    cand=[i for i in range(1,len(v)-1) if v[i]<=v[i-1] and v[i]<=v[i+1]]
    return fps,cand,n
def cut_points(mp4,head_win=0.6,tail_win=0.6):
    fps,c,n=plants(mp4); dur=n/fps
    ins=[i/fps for i in c if i/fps<=head_win] or [0.0]; outs=[i/fps for i in c if i/fps>=dur-tail_win] or [dur]
    return {"in":round(ins[-1],3),"out":round(outs[0],3),"dur":round(dur,3),"fps":fps}
def main(out,clips,dry=False,xf=0.1):
    cp=[cut_points(c) for c in clips]
    if dry: print(json.dumps(cp,indent=1)); return cp
    inputs=[];fl=[];prev="v0"
    for i,(c,p) in enumerate(zip(clips,cp)):
        inputs+=["-i",c]; fl.append(f"[{i}:v]trim={p['in']}:{p['out']},setpts=PTS-STARTPTS,fps=24,scale=854:480,setsar=1,format=yuv420p[t{i}]")
    acc="t0"; off=cp[0]['out']-cp[0]['in']
    for i in range(1,len(clips)):
        o=f"x{i}"; fl.append(f"[{acc}][t{i}]xfade=transition=fade:duration={xf}:offset={max(0,off-xf):.3f}[{o}]"); acc=o; off+=cp[i]['out']-cp[i]['in']-xf
    subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-filter_complex",";".join(fl),"-map",f"[{acc}]","-an","-c:v","libx264","-crf","19",out],check=True); return cp
if __name__=="__main__":
    a=[x for x in sys.argv[1:] if x!="--dry"]; main(a[0],a[1:],"--dry" in sys.argv)
