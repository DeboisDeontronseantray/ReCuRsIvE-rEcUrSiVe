import sys,json,glob,hashlib,os,datetime
sys.path.insert(0,"/workspace/streaming/commenter-pipeline"); import audiolevel as A
def sha(f): return hashlib.sha256(open(f,"rb").read()).hexdigest()
def now(): return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def run(files,lineage,levels,roomtone,label):
    rows=[json.loads(l) for l in open(lineage)] if lineage and os.path.exists(lineage) else []
    v4=json.load(open(os.path.dirname(lineage)+"/TAG-V404B.json"))["tag_v404b"] if lineage and os.path.exists(os.path.dirname(lineage)+"/TAG-V404B.json") else {}
    res=[]
    for f in files:
        s=sha(f); src=next((r for r in rows if r.get("sha256")==s and r.get("global_no") is not None),None) or next((r for r in rows if r.get("file")==f and r.get("global_no") is not None),{})
        r=A.fix(f,roomtone=roomtone)
        if "after" not in r: print("SKIP/ERR",f,r); res.append({"src":f,**r}); continue
        a,b=r["after"],r["before"]; o=r["out"]; os_=sha(o)
        lv={"file":o,"source_file":f,"source_sha256":s,"out_sha256":os_,"lufs_i":a["lufs_i"],"true_peak":a["true_peak"],"lra":a["lra"],"sub120_share":a.get("sub120_share"),"hum_prom_db":a.get("hum_prom_db"),"audio_leveled":not r["fails_after"],"before":{k:b.get(k) for k in("lufs_i","true_peak","lra","sub120_share","hum_prom_db")},"filter":r["filter"],"roomtone":roomtone,"date":now(),"writer":"CNB","batch":label}
        open(levels,"a").write(json.dumps(lv)+"\n")
        if lineage:
            g=src.get("global_no"); row={"clip_id":(src.get("clip_id") or os.path.basename(f))+"-audiofix","row_type":"audio_post","role":"air_copy","file":o,"out_sha256":os_,"sha256":os_,"source_file":f,"source_sha256":s,"source_global_no":g,"parent_id":src.get("tag"),
              "tag":src.get("tag"),"tag_2line":src.get("tag_2line"),"tag_3line":src.get("tag_3line"),"tag_v404b":src.get("tag_v404b") or v4.get(str(g)),"lineage":src.get("lineage"),"gen":src.get("gen"),"global_no":None,
              "audio_leveled":lv["audio_leveled"],"lufs_i":a["lufs_i"],"true_peak":a["true_peak"],"lra":a["lra"],"before":lv["before"],"origin":"audio_post","cost_usd":0.0,"date":now(),"writer":"CNB","thundertrundle_air_yes":False,
              "note":"audio-only post (same picture, same tag); no new global_no/gen per README audio_post convention"}
            open(lineage,"a").write(json.dumps(row)+"\n")
        res.append({"src":f,**{k:r[k] for k in("out","filter","fails_after")},"before":lv["before"],"after":{k:a.get(k) for k in("lufs_i","true_peak","lra","sub120_share","hum_prom_db")},"global_no":src.get("global_no"),"tag":src.get("tag")})
        print("OK" if not r["fails_after"] else "FAIL",src.get("tag"),round(b["lufs_i"],1),"->",a["lufs_i"],a["true_peak"],a["lra"],b.get("sub120_share"),"->",a.get("sub120_share"),os.path.basename(o))
    return res
