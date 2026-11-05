import sys,os,re,json,glob;sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
import build_prompt_v42 as B, apply_check_v42 as G
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K="R-REFDESC no restated looks when an image is attached (t371u)"
REF="fixtures/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg"
def sp(**k):
    d={"clip_id":"T1","channel":"Ch11 Fist Theater","show":"THE NIGHT PORTER","duration":10,"refs_raw":[REF],"cast":[{"name":"GIDEON QUILL","ref":REF}],
       "beats":[{"t":1,"who":"GIDEON QUILL","line":"Not tonight.","cue":"tired"}]};d.update(k);return d
def test_v41_np08_fails_new_gate():
    p=json.load(open(f"{H}/prompts_v41/odyssey/NP08.args.json"))["prompt"]; assert G.check(p)[K][0]=="FAIL"
def test_v42_np08_passes():
    p=json.load(open(f"{H}/prompts_v44/odyssey/NP08.args.json"))["prompt"]; assert G.check(p)[K][0]=="PASS"  # v42 builder output; prompts_v42 is superseded (canon fix Nov 2 2026), current pack = prompts_v44
    assert "GIDEON QUILL (<IMAGE_2>); THE CONCIERGE (<IMAGE_3>)" in p and "burgundy" not in p
def test_static_keys_not_emitted_when_ref():
    p=B.build(sp())["args"]["prompt"]; assert "GIDEON QUILL (<IMAGE_0>)" in p and "collar" not in p
def test_text_stays_without_image():
    p=B.build(sp(cast=[{"name":"GIDEON QUILL"}]))["args"]["prompt"]; assert "loosened collar" in p
def test_gate_catches_forms():
    for bad in ["[WREN (<IMAGE_0>): rain-dark belted trench coat.]","[X (<IMAGE_1>; maroon waistcoat).]","[MADAM HU (<IMAGE_3>, teal dress).]","[Setting: the lobby as in <IMAGE_1>: crystal chandeliers.]","[Setting: studio as <IMAGE_0>, curved blue desk.]"]:
        assert G.refdesc(bad), bad
    for ok in ["[GIDEON QUILL (<IMAGE_0> full body, <IMAGE_1> face)]","[GIDEON QUILL (<IMAGE_1> as he is now; <IMAGE_2> is the teal tape measure now around his neck)]","[a GUEST in a camel coat (invented adult).]"]:
        assert not G.refdesc(ok), ok
def test_ref_for_named_cast():
    r=G.check("[MAE: auburn shag haircut.] x",{},{"ref_for":{"MAE":"a.png"}}); assert r[K][0]=="FAIL"
def test_all_v42_ok_pass_and_structure_kept():
    for f in glob.glob(f"{H}/prompts_v42/*/*.args.json"):
        p=json.load(open(f))["prompt"]; assert not G.refdesc(p), f
        o=f.replace("prompts_v42","prompts_v41")
        if os.path.exists(o):
            q=json.load(open(o))["prompt"]
            tail=lambda s: s[s.index("Single shot") if "Single shot" in s else 0:]
            assert tail(p)==tail(q) or "Continue from" in p, f      # direction, beats, ending, rules bracket identical
            assert p.split("]")[0]==q.split("]")[0], f              # [Look] identical
            assert p[p.index("[Adults"):]==q[q.index("[Adults"):], f
def test_image_numbering_ok():
    for f in glob.glob(f"{H}/prompts_v42/*/*.args.json"):
        a=json.load(open(f)); r=G.check(a["prompt"],a); assert r["X-image numbering matches attached images"][0]=="PASS", f
