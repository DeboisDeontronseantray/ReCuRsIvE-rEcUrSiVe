#!/usr/bin/env python3
"""static_flip_v3 (free) — closes the STATIC-FLIP v2 gaps, add-only (v2 untouched, imported):
  walk(out, A, [mid1, mid2, ...], B, seg=1.5, wtf_pool=[...], seed)  intermediate-channel walk: real-CRT snow (v2) between 1-2 s heads of each
                                                  intermediate channel's current clip (crt-v2 build_v3 walk timing 0.29 s snow + 1.5 s/channel), land on B
  wtf cut-in: 4-8 frames from a random other channel's buffer, inserted in 1 of 3 flips (seeded)
  collapse_dot(A, out): TRUE CRT power-off: picture squashes to a bright line (0.12 s), line shrinks to a dot (0.12 s), dot glows and fades (0.3 s)
Static is one option, not only a universe signal (t362u: "just as a running gag maybe")."""
import sys,os,subprocess,tempfile,random,importlib.util,numpy as np,cv2
_s=importlib.util.spec_from_file_location("sf2","fixtures/thunder-trundle/prompts/experiments/round9-design-20261030/tools/static_flip_v2.py")
sf2=importlib.util.module_from_spec(_s); _s.loader.exec_module(sf2)
V=sf2.V
def run(*a): subprocess.run(["ffmpeg","-v","error","-y",*a],check=True)
def snow(out,dur=0.29):
    run("-ss","0.8","-t",str(dur),"-i",sf2.REF,"-f","lavfi","-i","sine=f=1800:d=0.03:r=48000","-filter_complex",
        f"[0:v]crop=400:300:120:90,scale=854:480,hue=s=0,eq=contrast=1.3,fps=24,format=yuv420p[v];[0:a]aresample=48000,volume=1.4,atrim=0:{dur}[n];[1]volume=1.5,apad[c];[n][c]amix=2:normalize=0,atrim=0:{dur}[a]",
        "-map","[v]","-map","[a]",*V,out); return out
def seg(src,out,start,dur):
    run("-ss",str(start),"-t",str(dur),"-i",src,"-f","lavfi","-t",str(dur),"-i","anullsrc=r=48000:cl=stereo","-filter_complex",
        "[0:v]scale=854:480,setsar=1,fps=24,format=yuv420p[v]","-map","[v]","-map","1:a","-shortest",*V,out); return out
def collapse_dot(A,out,tail=1.5):
    T=tempfile.mkdtemp(); f=f"{T}/l.png"; subprocess.run(["ffmpeg","-v","error","-y","-sseof","-0.05","-i",A,"-frames:v","1","-update","1",f],check=True)
    im=cv2.resize(cv2.imread(f),(854,480)); fr=[]
    for i in range(3):   # squash to line
        h=max(4,int(480*(1-(i+1)/3))); c=np.zeros_like(im); s=cv2.resize(im,(854,h)); s=cv2.addWeighted(s,1.0,np.full_like(s,255),0.4*(i+1)/3,0)
        c[240-h//2:240-h//2+h]=s; fr.append(c)
    for i in range(3):   # line -> dot
        w=max(6,int(854*(1-(i+1)/3))); c=np.zeros_like(im); cv2.rectangle(c,(427-w//2,238),(427+w//2,242),(255,255,255),-1); fr.append(c)
    for i in range(7):   # dot glow fade
        c=np.zeros_like(im); a=1-i/7; cv2.circle(c,(427,240),int(6+4*a),(int(255*a),)*3,-1); fr.append(cv2.GaussianBlur(c,(9,9),0))
    for k,x in enumerate(fr): cv2.imwrite(f"{T}/d{k:03d}.png",x)
    run("-framerate","24","-i",f"{T}/d%03d.png","-f","lavfi","-t",str(len(fr)/24),"-i","sine=f=15700:r=48000","-filter_complex","[1]volume=0.05,afade=t=out:d=0.4[a]","-map","0:v","-map","[a]",*V,f"{T}/dot.mp4")
    seg(A,f"{T}/a.mp4",max(0,dur(A)-tail),tail)
    open(f"{T}/c.txt","w").write(f"file '{T}/a.mp4'\nfile '{T}/dot.mp4'\n"); run("-f","concat","-safe","0","-i",f"{T}/c.txt",*V,out); return out
def dur(p): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p]))
def plan(mids,wtf_pool=(),seed=0,seg_s=1.5):
    R=random.Random(seed); steps=[]
    for m in mids: steps+=[("snow",0.29),("head",m,seg_s)]
    if wtf_pool and R.random()<1/3:
        pos=R.randrange(0,len(steps)+1); steps.insert(pos,("wtf",R.choice(list(wtf_pool)),R.randint(4,8)/24))
    return steps+[("snow",0.29)]
def walk(out,A,mids,B,wtf_pool=(),seed=0,seg_s=1.5,tail=1.5,head=2.5):
    T=tempfile.mkdtemp(); parts=[seg(A,f"{T}/A.mp4",max(0,dur(A)-tail),tail)]; i=0; steps=plan(mids,wtf_pool,seed,seg_s)
    for s in steps:
        i+=1; p=f"{T}/{i:02d}.mp4"
        if s[0]=="snow": snow(p,s[1])
        elif s[0]=="head": seg(s[1],p,0,s[2])
        else: seg(s[1],p,R0(s[1],seed),s[2])
        parts.append(p)
    parts.append(seg(B,f"{T}/B.mp4",0,head))
    open(f"{T}/c.txt","w").write("".join(f"file '{p}'\n" for p in parts)); run("-f","concat","-safe","0","-i",f"{T}/c.txt",*V,"-movflags","+faststart",out)
    return steps
def R0(p,seed): return round(random.Random(seed+7).uniform(0,max(0,dur(p)-0.5)),2)
if __name__=="__main__":
    a=sys.argv[1:]
    if a[0]=="dot": collapse_dot(a[1],a[2])
    else: print(walk(a[1],a[2],a[3].split(","),a[4],a[5].split(",") if len(a)>5 else ()))
