#!/usr/bin/env python3
"""lipcorr.py CLIP.mp4 x,y,w,h [audio.wav] — lip-sync fit score (free). Mouth-region motion energy per frame (box = mouth area, set by hand
from the contact sheet) vs audio RMS envelope; returns Pearson r at best lag within +-0.2 s. Higher r = better fit. Used for LS1-LS4."""
import sys,subprocess,json,numpy as np,cv2,tempfile,wave
def mouth_energy(mp4,box):
    x,y,w,h=box; cap=cv2.VideoCapture(mp4); fps=cap.get(cv2.CAP_PROP_FPS) or 24; prev=None; e=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        g=cv2.cvtColor(f[y:y+h,x:x+w],cv2.COLOR_BGR2GRAY).astype(np.float32)
        e.append(0.0 if prev is None else float(np.mean(np.abs(g-prev)))); prev=g
    return np.array(e),fps
def audio_env(src,fps,n):
    t=tempfile.mktemp(suffix=".wav"); subprocess.run(["ffmpeg","-v","error","-y","-i",src,"-ac","1","-ar","16000",t],check=True)
    w=wave.open(t); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32); hop=int(16000/fps)
    env=np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop]**2)) if (i+1)*hop<=len(a) else 0 for i in range(n)]); return env
def score(mp4,box,audio=None):
    m,fps=mouth_energy(mp4,box); a=audio_env(audio or mp4,fps,len(m)); best=(-2,0)
    for lag in range(-int(0.2*fps),int(0.2*fps)+1):
        x=m[max(0,lag):len(m)+min(0,lag)]; y=a[max(0,-lag):len(a)-max(0,lag)]; k=min(len(x),len(y))
        if k>5 and x[:k].std()>0 and y[:k].std()>0: best=max(best,(float(np.corrcoef(x[:k],y[:k])[0,1]),lag))
    return {"r":round(best[0],3),"lag_frames":best[1],"fps":fps,"frames":len(m)}
if __name__=="__main__":
    print(json.dumps(score(sys.argv[1],tuple(map(int,sys.argv[2].split(","))),sys.argv[3] if len(sys.argv)>3 else None)))
