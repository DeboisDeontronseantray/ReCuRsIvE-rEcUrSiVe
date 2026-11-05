# Sync fixes vs CURRENT-RULES v48 (Oct 30 2026 ~11 PM CT): contributor handles never in prompt, commenter images NOT YET, brand/name bracket.
import sys,os,json;sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
import build_prompt_v42 as B, apply_check_v42 as G, ref_policy_v4 as RP
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF="fixtures/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg"
KH="R-NOHANDLES no contributor handles in prompt (10:48 PM)"; KC="R-NOCOMMENTERIMG commenter images NOT YET (10:48 PM)"; KB="R-BRANDS parody brands, no names on screen (CR L34)"
def sp(**k):
    d={"clip_id":"T48","channel":"Ch11 Fist Theater","show":"THE NIGHT PORTER","duration":10,"refs_raw":[REF],"cast":[{"name":"GIDEON QUILL","ref":REF}],
       "beats":[{"t":1,"who":"GIDEON QUILL","line":"Not tonight.","cue":"tired"}]};d.update(k);return d
def test_contributors_in_sidecar_not_prompt():
    r=B.build(sp(contributors=["@neonwolf77","quietfan"]))
    assert r["sidecar"]["contributors"]==["@neonwolf77","quietfan"]
    assert "neonwolf77" not in r["args"]["prompt"] and "quietfan" not in r["args"]["prompt"] and r["report"][KH][0]=="PASS"
def test_handle_in_prompt_fails():
    for extra in ["[A poster reads quietfan.]","[Shout-out to @neonwolf77.]"]:
        r=B.build(sp(contributors=["@neonwolf77","quietfan"],extra=[extra]),strict=False)["report"]; assert r[KH][0]=="FAIL", extra
def test_bare_at_handle_fails_without_list():
    assert G.check("[x] At 1 s, @someone waves. [no real brands or personal names on screen]")[KH][0]=="FAIL"
def test_email_like_not_handle():
    assert G.check("[x] the sign says help.desk@hotel at 1 s. [no real brands or personal names on screen]")[KH][0]=="PASS"
def test_commenter_images_not_yet():
    assert json.load(open(f"{H}/config/commenter_images.json"))["enabled"] is False
    assert not RP.commenter_images_enabled()
    r=B.build(sp(commenter_refs=[{"path":"/tmp/duck.png","purpose":"prop","filtered":True}]),strict=False)["report"]; assert r[KC][0]=="FAIL"
    assert B.build(sp())["report"][KC][0]=="PASS"
def test_bracket_brands_and_names_every_clip():
    p=B.build(sp())["args"]["prompt"]; assert "Parody brands only; no real brands or personal names on screen." in p
    assert G.check("[x] [Adults only, no kids.]")[KB][0]=="FAIL"
