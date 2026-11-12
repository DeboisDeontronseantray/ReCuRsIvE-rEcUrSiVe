#!/usr/bin/env python3
"""audiolevel.py - audio QA gate (trundle standing rule 2026-10-27 17:36 CT). $0, ffmpeg only.
Targets: -16 LUFS I (+/-1), TP <= -1.5 dBTP, LRA <= 7 LU, sub-120Hz share low, no 60Hz-series hum,
block neighbours within 2 LU. Fix = NEW copy <src>_audiofix_parody.mp4 (video copied, AAC 128k/44.1k).
Never overwrites; never touches sources.
CLI: audiolevel.py measure F... | check F... [--report-only] | fix F... [--roomtone] | block F1 F2 ... (play order)
"""
import json,subprocess,sys,os,re,numpy as np
T_I,T_TP,T_LRA,TOL,SUB_MAX,HUM_DB,BLOCK_LU=-16.0,-1.5,7.0,1.0,0.35,10.0,2.0
HUM_F=tuple(60*k for k in range(1,11)); HUM_REL_MAX=-20.0  # a mains harmonic may not hold >1% of band energy
LRA_MIN_DUR=15.0  # EBU LRA is unreliable on clips <15 s (3 s windows); only gated on longer clips
def _run(a): return subprocess.run(a,capture_output=True,text=True)
def has_audio(f): return bool(_run(["ffprobe","-v","error","-select_streams","a","-show_entries","stream=index","-of","csv=p=0",f]).stdout.strip())
def loud(f,af=""):
    r=_run(["ffmpeg","-hide_banner","-nostats","-i",f,"-vn","-af",(af+"," if af else "")+"loudnorm=I=%s:TP=%s:LRA=%s:print_format=json"%(T_I,T_TP,T_LRA),"-f","null","-"])
    j=json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}")+1]); return j
def spectrum(f):
    x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",f,"-vn","-ac","1","-ar","4000","-f","f32le","-"],capture_output=True).stdout,dtype=np.float32)
    if x.size<4000: return None
    n=8192; segs=[x[i:i+n]*np.hanning(n) for i in range(0,x.size-n,n//2)] or [np.pad(x,(0,n-x.size))*np.hanning(n)]
    P=np.mean([np.abs(np.fft.rfft(s))**2 for s in segs],axis=0); fr=np.fft.rfftfreq(n,1/4000)
    tot=P[(fr>20)].sum()+1e-20; sub=P[(fr>20)&(fr<120)].sum()/tot
    def prom(h):
        i=np.argmin(abs(fr-h)); pk=P[i-2:i+3].max(); nb=np.median(np.r_[P[i-25:i-6],P[i+6:i+25]])+1e-20; return 10*np.log10(pk/nb)
    def rel(h):
        i=np.argmin(abs(fr-h)); return 10*np.log10(P[i-2:i+3].sum()/tot)
    hum={h:round(float(prom(h)),1) for h in HUM_F}
    humrel={h:round(float(rel(h)),1) for h in HUM_F}
    lo=(fr>40)&(fr<400); i=np.argmax(P*lo); return {"sub120_share":round(float(sub),3),"hum_prom_db":hum,"hum_rel_db":humrel,"duration_s":round(x.size/4000,1),"low_peak_hz":round(float(fr[i]),1)}
def measure(f):
    if not has_audio(f): return {"file":f,"audio":False}
    j=loud(f); s=spectrum(f) or {}
    return {"file":f,"audio":True,"lufs_i":float(j["input_i"]),"true_peak":float(j["input_tp"]),"lra":float(j["input_lra"]),**s}
def verdict(m):
    if not m.get("audio"): return ["no_audio_stream"]
    if m["lufs_i"]<-60: return ["silent"]
    p=[]
    if abs(m["lufs_i"]-T_I)>TOL: p.append("lufs %.1f"%m["lufs_i"])
    if m["true_peak"]>T_TP+0.05: p.append("tp %.1f"%m["true_peak"])
    if m["lra"]>T_LRA+0.5 and m.get("duration_s",99)>=LRA_MIN_DUR: p.append("lra %.1f"%m["lra"])
    if m.get("sub120_share",0)>SUB_MAX: p.append("sub120 %.2f"%m["sub120_share"])
    h=[k for k,v in (m.get("hum_prom_db") or {}).items() if v>=HUM_DB and (m.get("hum_rel_db") or {}).get(k,0)>HUM_REL_MAX]
    if h: p.append("hum %s"%h)
    return p
def chain(m,roomtone=False):
    f=["highpass=f=85:poles=2"]
    for h in HUM_F:
        if (m.get("hum_prom_db") or {}).get(h,0)>=6: f.append("equalizer=f=%d:t=q:w=8:g=%d"%(h,-30 if h<=120 else -24))
    lp=m.get("low_peak_hz",0)
    if 85<lp<200 and all(abs(lp-h)>8 for h in (120,180)): f.append("equalizer=f=%.0f:t=q:w=6:g=-18"%lp)
    f.append("lowshelf=f=200:g=-4"); return ",".join(f)
def outname(src): b,_=os.path.splitext(src); return (b[:-7] if b.endswith("_parody") else b)+"_audiofix_parody.mp4"
def fix(src,dst=None,roomtone=False,m=None):
    m=m or measure(src); dst=dst or outname(src)
    if os.path.exists(dst): return {"skipped":"exists","out":dst}
    pre=chain(m,roomtone); j=loud(src,pre)
    ln="loudnorm=I=%s:TP=%s:LRA=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"%(T_I,T_TP,T_LRA,j["input_i"],j["input_tp"],j["input_lra"],j["input_thresh"],j["target_offset"])
    if roomtone:
        fc="[0:a]%s[a];anoisesrc=c=brown:a=0.004:r=44100,highpass=f=150,lowpass=f=2500[n];[a][n]amix=inputs=2:duration=first:normalize=0,%s,aresample=44100[o]"%(pre,ln)
    else: fc="[0:a]%s,%s,aresample=44100[o]"%(pre,ln)
    r=_run(["ffmpeg","-hide_banner","-v","error","-n","-i",src,"-filter_complex",fc,"-map","0:v?","-map","[o]","-c:v","copy","-c:a","aac","-b:a","128k","-ar","44100","-movflags","+faststart",dst])
    if r.returncode: return {"error":r.stderr[-400:],"out":dst}
    a=measure(dst)
    if abs(a["lufs_i"]-T_I)>0.5 or a["true_peak"]>T_TP:   # trim pass: loudnorm undershoots when TP-limited; re-encode from SOURCE with fixed gain + limiter
        g=T_I-a["lufs_i"]; tmp=dst+".trim.mp4"
        for _ in range(3):
            fc2=fc.replace(",aresample=44100[o]",",volume=%.2fdB,alimiter=limit=0.75:level=false:attack=2:release=60,aresample=44100[o]"%g)
            _run(["ffmpeg","-hide_banner","-v","error","-y","-i",src,"-filter_complex",fc2,"-map","0:v?","-map","[o]","-c:v","copy","-c:a","aac","-b:a","128k","-ar","44100","-movflags","+faststart",tmp])
            b=measure(tmp); b["file"]=dst
            if abs(b["lufs_i"]-T_I)<=0.5 and b["true_peak"]<=T_TP: break
            g+=T_I-b["lufs_i"]
        os.replace(tmp,dst); a=b; fc=fc2
    return {"out":dst,"filter":fc,"roomtone":roomtone,"before":m,"after":a,"fails_after":verdict(a)}
def block(ms):
    out=[]
    for a,b in zip(ms,ms[1:]):
        if a.get("audio") and b.get("audio") and abs(a["lufs_i"]-b["lufs_i"])>BLOCK_LU: out.append({"from":a["file"],"to":b["file"],"jump_lu":round(b["lufs_i"]-a["lufs_i"],1)})
    return out
def gate(f,act=True,roomtone=False):
    """post-render QA: returns {pass, queue_file, ...}. On fail (and act) writes fixed copy and queues it."""
    m=measure(f); p=verdict(m)
    if not p or p==["no_audio_stream"]: return {"pass":True,"queue_file":f,"measure":m,"fails":p,"audio_leveled":not p}
    if not act or p==["silent"]: return {"pass":False,"queue_file":None,"measure":m,"fails":p}
    r=fix(f,roomtone=roomtone,m=m); ok="after" in r and not r["fails_after"]
    return {"pass":ok,"queue_file":r["out"] if ok else None,"measure":m,"fails":p,"fix":r,"audio_leveled":ok}
if __name__=="__main__":
    a=sys.argv[1:]; cmd=a[0] if a else ""; fs=[x for x in a[1:] if not x.startswith("--")]
    if cmd=="measure": [print(json.dumps(measure(f))) for f in fs]
    elif cmd=="check":
        for f in fs: g=gate(f,act="--report-only" not in a); print(("PASS" if g["pass"] else "FAIL"),"; ".join(g["fails"]),f)
    elif cmd=="fix": [print(json.dumps(fix(f,roomtone="--roomtone" in a),default=str)) for f in fs]
    elif cmd=="block": print(json.dumps(block([measure(f) for f in fs]),indent=1))
    else: print(__doc__)
