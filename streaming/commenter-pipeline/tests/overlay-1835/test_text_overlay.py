import sys,os,subprocess,pytest
sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")))
import owner_denylist
import text_overlay as T
_OWNER = owner_denylist.real_first()
def texts(p): return [o["text"] for o in T.split(p)["overlay"]]
def test_put_sale_on_it():
    s=T.split("Put SALE on it"); assert texts("Put SALE on it")==["SALE"]; assert "SALE" not in s["gen_prompt"]; assert s["gen_prompt"].endswith(T.NO_TEXT)
def test_caption_says():
    s=T.split("a rainy tank yard at night, caption says Rust Never Sleeps"); assert "Rust Never Sleeps" in texts(s and "a rainy tank yard at night, caption says Rust Never Sleeps")
    assert "Rust" not in s["gen_prompt"] and "tank yard" in s["gen_prompt"]
def test_double_quotes_title():
    s=T.split('a helmet on a crate with the title "Brain Bucket Pro"'); o=s["overlay"][0]
    assert o["text"]=="Brain Bucket Pro" and o["role"]=="title" and o["position"]=="top"; assert "Brain" not in s["gen_prompt"]
def test_single_and_smart_quotes():
    assert texts("a banner reads 'Open Late'")==["Open Late"]; assert texts("sign \u201cNo Refunds\u201d over the door")==["No Refunds"]
def test_price():
    s=T.split("a field pack on a table priced at $49.99"); o=s["overlay"]
    assert o[0]["text"]=="$49.99" and o[0]["role"]=="price"; assert "49" not in s["gen_prompt"]
def test_percent_off():
    assert "30% off" in texts("binoculars in fog, 30% off")
def test_multi():
    t=texts('title "Night Cruiser" and a sign that says Low Low Prices for $19.99'); assert set(t)>={"Night Cruiser","$19.99"}
def test_apostrophe_not_quote():
    s=T.split("the soldier's drone hovers over a dock"); assert s["overlay"]==[] and not s["text_detected"]
@pytest.mark.parametrize("p",["a cloak flapping on a windy ridge at dusk","slow pan across a gauntlet on velvet","more fog and dramatic lighting please"])
def test_non_text_unchanged(p):
    s=T.split(p); assert s["gen_prompt"]==p and s["overlay"]==[] and not s["text_detected"]
def test_unsure_treated_as_text():
    s=T.split("add some lettering in a fun font"); assert s["unsure"] and s["gen_prompt"].endswith(T.NO_TEXT)
@pytest.mark.parametrize("t",[f"{_OWNER}'s Deals",f"for {_OWNER.upper()}","Kids love it","great for children","toddler tested","Military Boutique Sale","MILITARY  BOUTIQUE"])
def test_filter_blocks(t):
    with pytest.raises(T.Blocked): T.check_text([{"text":t,"role":"caption","position":"bottom"}])
def test_public_owner_name_allowed():
    assert T.check_text([{"text":"trundle yes","role":"caption","position":"bottom"}])
def test_filter_allow_mb_and_clean():
    assert T.check_text([{"text":"Military Boutique","role":"title","position":"top"}],allow_mb=True)
    with pytest.raises(T.Blocked): T.check_text([{"text":"Military Boutique for kids","role":"title","position":"top"}],allow_mb=True)
    assert T.check_text([{"text":"SALE","role":"caption","position":"bottom"},{"text":"$19.99","role":"price","position":"bottom_right"}])
def test_burn_and_ocr(tmp_path):
    m="/tmp/ov_master_test.mp4"
    if os.path.exists(m): os.remove(m)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","color=c=0x335577:s=640x360:d=2","-f","lavfi","-i","sine=d=2","-shortest","-c:v","libx264","-c:a","aac",m],check=True)
    before=os.path.getmtime(m); out=str(tmp_path/"v2_parody.mp4")
    ov=T.split('title "STORM SALE" priced at $19.99')["overlay"]
    r=T.burn(m,out,ov); assert r["ocr_ok"],r; assert os.path.getmtime(m)==before
    with pytest.raises(FileExistsError): T.burn(m,out,ov)
    with pytest.raises(ValueError): T.burn(m,m,ov)
    row=T.lineage_row(70,71,"4.7",3,ov,["cp-1"],m,out,r["ocr_ok"]); assert row["paid_render"] is False and row["parent_no"]==70 and row["change_kind"]=="text_only"
def test_burn_blocked_before_render(tmp_path):
    out=str(tmp_path/"x.mp4")
    with pytest.raises(T.Blocked): T.burn("/tmp/nonexistent.mp4",out,[{"text":_OWNER,"role":"caption","position":"bottom"}])
    assert not os.path.exists(out)
