import sys,os,re;sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
import build_prompt_v41 as B, apply_check_v41 as G
REF="/workspace/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg"
def sp(**k):
    d={"clip_id":"T1","channel":"Ch11 Fist Theater","duration":10,"refs_raw":[REF],"cast":[{"name":"GIDEON QUILL","ref":REF}],
       "beats":[{"t":1,"who":"GIDEON QUILL","line":"Not tonight.","cue":"tired"},{"t":4,"text":"GIDEON rings the desk bell"}]};d.update(k);return d
def test_order_fixed_and_no_shuffle():
    a=[B.build(sp(clip_id=f"T{i}"))["args"]["prompt"] for i in range(5)]; assert len(set(a))==1
    p=a[0]; assert p.index("[Look")<p.index("[Cast")<p.index("Single shot")<p.index("At 1 s")<p.index("Motion carries")<p.index("[Adults")
def test_bracket_his_words():
    p=B.build(sp())["args"]["prompt"]; assert "No gore; bloodstains on clothing are fine, no blood draining out." in p
    assert not re.search(r"no blood on skin|no wounds|stage-combat|theatrical props|no on-screen text",p,re.I)
def test_ch4_jw_line():
    p=B.build(sp(channel="Ch4 Military Boutique / BLACK ICE",clip_type="fight"))["args"]["prompt"]; assert "hard hits and some blood, but no gore" in p and "Photoreal" in p
def test_ref_required():
    r=B.build(sp(refs_raw=[],cast=[{"name":"GIDEON QUILL"}]),strict=False)["report"]; assert r["R-REF required (t132u)"][0]=="FAIL"
def test_speaker_bracketed():
    p=B.build(sp())["args"]["prompt"]; assert 'GIDEON QUILL speaks [tired: "Not tonight."]' in p
    assert G.check('[Look: x] At 1 s, he says "hi". Motion carries on through the last half second. [Adults only, no kids. No gore. Nobody looks into the camera.]')["R-SPEAKER named + bracketed (t134u,t139u)"][0]=="FAIL"
def test_static_look_one_per_channel():
    assert all(len(v["look_pool"])==1 for v in B.LOCKS.values())
def test_no_transform_check_and_density_not_blocking():
    r=B.build(sp(beats=[{"t":i,"text":f"GIDEON does thing {i} "+"word "*60} for i in range(9)]))["report"]
    assert r["W-words"][0]=="WARN" and r["W-beats"][0]=="WARN" and not any("transform" in k.lower() for k in r)
def test_cuts_not_failed():
    r=B.build(sp(camera="Quick cuts: whip pan to a high mounted security camera view"))["report"]; assert not [k for k,v in r.items() if v[0]=="FAIL"]
def test_image_index():
    r=G.check("[Look: a] [Cast: X (<IMAGE_2>)] At 1 s x. Motion carries on through the last half second. [Adults only, no kids. No gore. Nobody looks into the camera.]",{"reference_image_paths":[REF]})
    assert r["X-image numbering matches attached images"][0]=="FAIL"
def test_remake_blocked():
    assert B.build(sp(remake_of="Dynapage"),strict=False)["report"]["R-REMAKE no remakes of completed ads (Oct 29 12:00 PM)"][0]=="FAIL"
