# v43 variants of test_v42 glob tests: prompts_v43 (rebuilt with v48 sync bracket) vs prompts_v42. Originals untouched.
import sys,os,json,glob;sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
import apply_check_v42 as G, canon as C
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KH="R-NOHANDLES no contributor handles in prompt (10:48 PM)"; KB="R-BRANDS parody brands, no names on screen (CR L34)"
FS=lambda: glob.glob(f"{H}/prompts_v43/*/*.args.json")
def test_v43_np08_passes():
    p=json.load(open(f"{H}/prompts_v43/odyssey/NP08.args.json"))["prompt"]
    assert G.check(p)["R-REFDESC no restated looks when an image is attached (t371u)"][0]=="PASS"
    assert "GIDEON QUILL (<IMAGE_2>); THE CONCIERGE (<IMAGE_3>)" in p and "burgundy" not in p
def test_all_v43_ok_pass_full_gate():
    assert len(FS())==37
    for f in FS():
        a=json.load(open(f)); r=G.check(a["prompt"],a)
        assert not [k for k,x in r.items() if x[0]=="FAIL"], f
        assert r[KB][0]=="PASS" and r[KH][0]=="PASS", f
def test_v43_vs_v42_structure_kept():
    for f in FS():
        p=json.load(open(f))["prompt"]; o=f.replace("prompts_v43","prompts_v42"); assert os.path.exists(o), f
        q=json.load(open(o))["prompt"]
        # canon fix Nov 2 2026: prompts_v42 is superseded; compare after the same canon layer the generator now applies
        ch="Ch11 Fist Theater" if "/odyssey/" in f else None
        if ch: q=C.text(q,ch)
        q=q.replace("Monster: the giant mechanical bear (","Monster: Cyborg Bear (")
        assert p.split("]")[0]==q.split("]")[0], f          # [Look] identical
        assert p[:p.index("[Adults")]==q[:q.index("[Adults")], f   # everything before rules bracket identical
def test_v43_holds_same_as_v42():
    b=lambda v:{os.path.basename(x) for x in glob.glob(f"{H}/{v}/BLOCKED/*.json")}
    assert b("prompts_v43")==b("prompts_v42") and {"P10-2.json","P10-3.json","P14-1.json","P14-2.json","P14-3.json"}<=b("prompts_v43")
