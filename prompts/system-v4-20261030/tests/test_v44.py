# R-REF exemption for exactly 16 ads (Trundle 11:09 PM "Ref image: yes, hard rule." / 11:10 PM "These specific ads can run without an image").
import sys,os,json,glob,shutil,pytest;sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
import apply_check_v44 as G
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); KREF=G.KREF
EX=json.load(open(f"{H}/config/ref_image_exemptions.json"))["ids"]
def test_exactly_16():
    assert len(EX)==16==len(set(EX)) and len(G.exempt_ids())==16
def test_16_ads_pass_full_gate():
    for cid in EX:
        a=json.load(open(f"{H}/prompts_v44/commercials/{cid}.args.json")); r=G.check(a["prompt"],a,clip_id=cid)
        assert not [k for k,v in r.items() if v[0]=="FAIL"], cid
        assert r[KREF][1].startswith("EXEMPT"), cid
        for k in ("R-BRANDS parody brands, no names on screen (CR L34)","R-NOHANDLES no contributor handles in prompt (10:48 PM)"): assert r[k][0]=="PASS", cid
def test_exempt_ads_still_get_other_checks():
    a=json.load(open(f"{H}/prompts_v44/commercials/{EX[0]}.args.json"))
    bad=a["prompt"].replace("no real brands or personal names on screen","")+" Shout-out to @someone."
    r=G.check(bad,a,clip_id=EX[0]); assert r["R-BRANDS parody brands, no names on screen (CR L34)"][0]=="FAIL" and r["R-NOHANDLES no contributor handles in prompt (10:48 PM)"][0]=="FAIL"
def test_nonexempt_no_ref_fails():
    a=json.load(open(f"{H}/prompts_v44/commercials/{EX[0]}.args.json"))
    for cid in ("AD-Some-New-Ad","P99-1",None,EX[0].lower(),EX[0]+"-v2"): assert G.check(a["prompt"],a,clip_id=cid)[KREF][0]=="FAIL", cid
def test_cannot_extend_to_17(tmp_path,monkeypatch):
    d=json.load(open(G.CFG)); d["ids"].append("AD-Seventeenth"); d["count"]=17
    p=tmp_path/"x.json"; p.write_text(json.dumps(d)); monkeypatch.setattr(G,"CFG",str(p))
    with pytest.raises(ValueError): G.exempt_ids()
    d["count"]=16; p.write_text(json.dumps(d))
    with pytest.raises(ValueError): G.exempt_ids()
def test_norefstart_still_applies_to_exempt():
    a={"prompt":"x","image_path":"/r.png","reference_image_paths":["/r.png"]}
    assert G.check("[x] [Parody brands only; no real brands or personal names on screen.]",a,clip_id=EX[0])["R-NOREFSTART ref never start frame (t121u)"][0]=="FAIL"
def test_v44_contents():
    held={os.path.basename(f)[:-5] for f in glob.glob(f"{H}/prompts_v44/BLOCKED/*.json")}
    assert held=={"P10-2","P10-3","P14-1","P14-2","P14-3"}
    assert len([f for f in glob.glob(f"{H}/prompts_v44/*/*.args.json") if "/BLOCKED/" not in f])==53
    for f in glob.glob(f"{H}/prompts_v43/*/*.args.json"):
        if "/BLOCKED/" not in f: assert open(f).read()==open(f.replace("prompts_v43","prompts_v44")).read(), f
