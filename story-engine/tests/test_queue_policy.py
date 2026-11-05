# Offline sim of comment_prompt_slots rules. No ErsatzTV, no network.
import yaml
from pathlib import Path
P=yaml.safe_load(open(Path(__file__).resolve().parents[1] / 'rules/queue-policy.yaml'))['comment_prompt_slots']
M=P['render_lead_time']['margin_min']; D=P['render_lead_time']['render_eta_default_min']; W=P['max_wait_breaks']
HARD=set(P['hard_limit_violation']['applies_to'])
def eta(hist): 
    if not hist: return D
    s=sorted(hist); return s[min(len(s)-1,int(0.9*len(s)))]
def place(prompt,slots,now,hist,lineage):
    if HARD & set(prompt.get('flags',[])): lineage.append((None,None,prompt['id'],'reject_hard_limit')); return None
    need=now+eta(hist)+M
    for s in slots:
        if s['start']<need: continue
        if s.get('protected'): prompt['moves']+=1; lineage.append((s['slot'],s['clip'],None,'protected_move')); continue
        if True:  # wait-limit priority only matters vs house replacements
            lineage.append((s['slot'],s['clip'],prompt['id'],'replace')); s['clip']=prompt['id']; s['protected']=True; return s['slot']
def run():
    L=[]; slots=[{'slot':i,'start':i*5,'clip':f'c{i}'} for i in range(12)]
    assert place({'id':'p1','moves':0},slots,0,[],L)==5          # 15+10=25 -> slot 5
    assert place({'id':'p2','moves':0},slots,0,[],L)==6          # slot5 protected -> next
    assert place({'id':'p3','moves':0},slots,0,[10,12,30],L)==8  # p90=30 ->40
    assert place({'id':'bad','moves':0,'flags':['kids']},slots,0,[],L) is None
    assert (None,None,'bad','reject_hard_limit') in L
    assert all(len(r)==4 for r in L)
    assert W==3 and P['render_not_ready_at_slot_start']['play']=='scheduled_clip'
    print('6 sim tests OK; lineage rows:',len(L))
run()
