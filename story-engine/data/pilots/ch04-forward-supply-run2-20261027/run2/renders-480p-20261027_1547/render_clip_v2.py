import json,os,sys,time,base64,subprocess,datetime,zoneinfo,requests
P="/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027"
OUT=os.path.dirname(os.path.abspath(__file__))
cid,model=sys.argv[1],sys.argv[2]
PRICE={"grok-imagine-video-1.5-lite":(0.02,0.01),"grok-imagine-video-1.5":(0.08,0.01),"grok-imagine-video":(0.05,0.002)}
clip=[c for c in json.load(open(P+"/clip-prompts.json"))["shots"] if c["id"]==cid][0]
refs=clip.get("reference_images",[])
imgs=[]
for r in refs:
    s=f"{OUT}/refs_small/{os.path.basename(r)[:-4]}.jpg"
    if not os.path.exists(s): subprocess.run(["ffmpeg","-y","-v","error","-i",r,"-vf","scale='min(768,iw)':-2","-q:v","3",s],check=True)
    imgs.append({"url":"data:image/jpeg;base64,"+base64.b64encode(open(s,"rb").read()).decode()})
tag=""
if refs:
    names=[os.path.basename(r)[:-4] for r in refs]
    tag="Character references: "+"; ".join(f"<IMAGE_{i}> = {n} (match face, build, hair, wardrobe exactly)" for i,n in enumerate(names))+". "
dl=" ".join(f'{d["speaker"]} says: "{d["line"]}".' if not d["line"].startswith("*") else f'{d["speaker"]}: {d["line"].strip("*")} sound.' for d in clip.get("dialogue",[]))
prompt=tag+clip["visual_prompt"]+(" Dialogue, calm natural delivery, adult voices: "+dl if dl else "")+" Avoid: "+", ".join(clip["negative_prompt"])+", no children, no on-screen text."
dur=clip["duration_s"]
body={"model":model,"prompt":prompt,"duration":dur,"resolution":"480p","aspect_ratio":"16:9"}
if imgs: body["reference_images"]=imgs
H={"Authorization":"Bearer "+os.environ["XAI_API_KEY"],"Content-Type":"application/json"}
r=requests.post("https://api.x.ai/v1/videos/generations",headers=H,json=body,timeout=180)
print("submit",r.status_code,r.text[:500],flush=True)
if r.status_code>=300: sys.exit(2)
rid=r.json()["request_id"]
while True:
    time.sleep(6);j=requests.get("https://api.x.ai/v1/videos/"+rid,headers=H,timeout=60).json()
    st=j.get("status")
    if st in("done","failed","expired"): break
fn=f"{OUT}/{cid}_480p_{model}_parody.mp4"
ps,pi=PRICE[model];usd=round(ps*dur+pi*len(imgs),4)
info={k:v for k,v in j.items() if k!="video"};info["video_meta"]={k:v for k,v in (j.get("video") or {}).items() if k!="url"}
if st=="done":
    v=requests.get(j["video"]["url"],timeout=300).content;open(fn,"wb").write(v)
    if (j.get("video") or {}).get("duration"): usd=round(ps*float(j["video"]["duration"])+pi*len(imgs),4)
else: fn=None; usd=0.0  # failed jobs assumed unbilled; flagged
line={"time":datetime.datetime.now(zoneinfo.ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),"prompt_id":"ch04-fs-run2-pocket-taupe-480p","provider":"xai_imagine","model":model,"cost_usd":usd,"clip":cid,"task":f"ch04 Forward Supply run2 Pocket Taupe 480p {cid} refs={len(imgs)} status={st}","request_id":rid,"source":"list-price estimate (480p)","channel":4}
open("/workspace/fakenews/spend.jsonl","a").write(json.dumps(line)+"\n")
open(f"{OUT}/log.jsonl","a").write(json.dumps({**line,"file":fn,"resp":info,"prompt_chars":len(prompt)})+"\n")
print(st,fn,usd,json.dumps(info)[:600])
