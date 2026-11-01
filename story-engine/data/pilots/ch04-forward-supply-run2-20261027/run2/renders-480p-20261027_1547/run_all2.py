import json,subprocess,sys,os
s=json.load(open('../../clip-prompts.json'))['shots'];spent=0.36
for c in s:
    fn=f"{c['id']}_480p_{c['model']}_parody.mp4"
    if os.path.exists(fn): continue
    est=(0.02*c['duration_s']) if 'lite' in c['model'] else 0.08*c['duration_s']+0.01*len(c.get('reference_images',[]))
    if spent+est>30: print('HARD STOP before',c['id'],spent,flush=True);sys.exit(3)
    for t in range(2):
        r=subprocess.run(['python3','render_clip_v2.py',c['id'],c['model']],capture_output=True,text=True)
        last=(r.stdout.strip().splitlines() or [''])[-1]
        print(c['id'],'try',t+1,r.returncode,last[:200],r.stderr[-300:],flush=True)
        if r.returncode==0 and last.startswith('done'): spent+=est;break
        if r.returncode==0: break  # generated but not done (moderation/expired): no auto retry
print('TOTAL est',spent)
