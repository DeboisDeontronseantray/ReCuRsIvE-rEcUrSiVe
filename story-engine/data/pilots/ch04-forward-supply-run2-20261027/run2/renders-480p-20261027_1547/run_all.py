import json,subprocess,sys
s=json.load(open('../../clip-prompts.json'))['shots'];spent=0
for c in s:
    est=(0.02*c['duration_s']) if 'lite' in c['model'] else 0.08*c['duration_s']+0.01*len(c.get('reference_images',[]))
    if spent+est>30: print('HARD STOP before',c['id'],spent,flush=True);sys.exit(3)
    for t in range(2):
        r=subprocess.run(['python3','render_clip_v2.py',c['id'],c['model']],capture_output=True,text=True)
        print(c['id'],'try',t+1,r.returncode,r.stdout[-300:],r.stderr[-300:],flush=True)
        if r.returncode==0 and ' done ' in r.stdout.splitlines()[-1]+' ' or r.stdout.splitlines()[-1:][0:1] and r.stdout.splitlines()[-1].startswith('done'): spent+=est;break
print('TOTAL est',spent)
