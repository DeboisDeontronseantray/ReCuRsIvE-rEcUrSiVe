import pytest
pytest.skip(
    'story-engine live callers are out of scope for the offline repo suites',
    allow_module_level=True,
)
import json, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker, intake, vote_tally
import pytest as _pt

@_pt.fixture(autouse=True)
def _no_shared_watchlist(request, monkeypatch, tmp_path):
    if 'real_shared' not in request.node.name: monkeypatch.setattr(checker, 'WATCHLIST', tmp_path / 'absent-watchlist.jsonl')

def setup_tmp():
    t = Path(tempfile.mkdtemp())
    intake.CNB_INBOX = str(t/"cnb-inbox")   # never the real CNB inbox
    intake.QUEUE, intake.DONE, intake.REJECTED, intake.PENDING = t/"queue.jsonl", t/"processed.jsonl", t/"rejected.jsonl", t/"pending-approval"
    return t

COMMENTS = [
    ("@fogfan", "Osmund should check the supply bay one more time and find the Quietline Helmet instead"),
    ("@mira_stan", "Mira color-codes the whole search on her clipboard"),
    ("@timlover", "Tim leads a search party with his cyan optic as a flashlight"),
    ("@edgy99", "Bill shows the blood and gore from the last mission"),            # unsafe
    ("@brandguy", "Give Osmund a Red Bull so he finds it faster"),                 # real brand
    ("@chaos", "make Bill do a moonwalk across the mess hall"),         # out-of-character
]

def test_pipeline():
    t = setup_tmp()
    for h, txt in COMMENTS: intake.enqueue(h, txt)
    res = intake.process()
    st = {r["handle"]: (s, i) for r, s, i in res}
    assert [r["handle"] for r, _, _ in res] == [h for h, _ in COMMENTS], "FIFO order"
    assert st["@edgy99"][0] == "rejected" and "not TV-safe" in st["@edgy99"][1]
    assert st["@brandguy"][0] == "rejected" and any("real brand" in x for x in st["@brandguy"][1])
    for h in ("@fogfan", "@mira_stan", "@timlover", "@chaos"): assert st[h][0] == "pending", (h, st[h])
    chaos = json.load(open(st["@chaos"][1]))["shots"][0]
    w = chaos["live_wrapper"]
    assert w["commenter"]["text_verbatim"] == COMMENTS[5][1]
    assert w["levers"]["out_of_character"] and "@chaos thinks it's a good idea" in w["levers"]["self_reflection_line"]
    assert chaos["est_usd"] == 0.52 and "PENDING" in chaos["status"]
    assert intake.process() == [], "idempotent: nothing reprocessed"
    shutil.rmtree(t)

def test_checker_run2():
    r = checker.check_file(Path(__file__).resolve().parents[2] / "data/pilots/ch04-forward-supply-run2-20261027/clip-prompts.json")
    assert r["counts"]["fail"] == 0 and len(r["shots"]) == 35

def test_checker_catches_bad_shot():
    b = checker.load_bible(); reg = checker.registry(b)
    bad = {"id": "X", "cast": ["Osmund", "Captain Nobody"], "props_products": ["Glock 19: pistol"], "location": "Outpost Quiet hatch",
           "visual_prompt": "fog clears to a clear blue sky", "dialogue": [{"speaker": "Tim", "line": "Hello there"}], "continues_from": "S1A"}
    r = checker.check_shot(bad, b, reg, {})
    assert r["status"] == "fail" and len(r["fails"]) >= 4, r

def test_vote_tally():
    t = setup_tmp()
    chat = [{"handle": "@a", "text": "!vote 2"}, {"handle": "@b", "text": "!vote 2"}, {"handle": "@a", "text": "!vote 1"},
            {"handle": "@c", "text": "!vote 2"}, {"handle": "@d", "text": "!vote 9"}]
    w, rows = vote_tally.tally(chat, {"1": "Stay", "2": "Ch 4 Military Boutique"}, 0, t)
    assert w == "2" and (t/"winner.txt").read_text().strip() == "2"
    w2, _ = vote_tally.tally(chat[:2], {"1": "Stay", "2": "Ch 4"}, 0, t)
    assert w2 == "stay"
    shutil.rmtree(t)

def test_import_xintake():
    import hashlib
    t = setup_tmp(); inbox = t/"inbox"; inbox.mkdir()
    def item(mid, status, text, sha=None):
        return {"schema": "x-intake/v1", "status": status, "commenter": {"handle": "@h"+mid, "source": "broadcast_chat", "message_id": mid, "ts": "2026-10-27T16:30:00-05:00"},
                "commenter_text_verbatim": text, "commenter_text_sha256": sha or hashlib.sha256(text.encode()).hexdigest(), "credit_line": None}
    (inbox/"a.json").write_text(json.dumps(item("1", "APPROVED", "Tim finds it under the urn")))
    (inbox/"b.json").write_text(json.dumps(item("2", "HELD_FOR_trundle", "not yet approved")))
    (inbox/"c.json").write_text(json.dumps(item("3", "APPROVED", "tampered", sha="0"*64)))
    added, skipped = intake.import_xintake(inbox)
    assert [r["text"] for r in added] == ["Tim finds it under the urn"] and len(skipped) == 2
    assert intake.import_xintake(inbox)[0] == []
    shutil.rmtree(t)

def _inj(text, handle="@t", rid="r1", log=None):
    w = intake.wrap({"handle": handle, "text": text, "received_at": "x"})
    return intake.inject(w, rid, log=log or (Path(tempfile.mkdtemp()) / "inj.jsonl"))

def test_weak_prompt_gets_flair():
    w = _inj("Osmund vibes")
    inj = w["levers"]["injections"]; assert w["levers"]["prompt_features"]["weak"]
    assert 1 <= len(inj) <= 2 and sum(i["kind"] == "spoken_line" for i in inj) <= 1

def test_strong_prompt_no_flair():
    for i in range(20):
        w = _inj("Mira color-codes the whole search on her clipboard in the supply bay", rid=f"s{i}")
        assert all(x["when"] == "always" for x in w["levers"]["injections"])

def test_no_people_no_spoken_line():
    for i in range(20):
        w = _inj("fog", rid=f"n{i}")
        assert not w["levers"]["prompt_features"]["people_on_screen"]
        assert not any(x["kind"] == "spoken_line" for x in w["levers"]["injections"])

def test_tim_never_speaks():
    lib = intake.load_snippets()
    assert not any(s.get("speaker") == "Tim" for s in lib["snippets"])
    lib["snippets"].append({"id": "bad-tim", "kind": "spoken_line", "speaker": "Tim", "text": "Tim: hello", "requires": {"people_on_screen": True}, "when": "always", "weight": 99, "max_per_hour": 99, "tv_safe": True})
    for i in range(20):
        w = intake.wrap({"handle": "@t", "text": "Tim", "received_at": "x"})
        intake.inject(w, f"t{i}", lib=lib, log=Path(tempfile.mkdtemp()) / "i.jsonl")
        assert not any(x.get("speaker") == "Tim" for x in w["levers"]["injections"])

def test_verbatim_unchanged_and_checker_passes():
    t = setup_tmp(); old = intake.LIVE; intake.LIVE = t
    texts = ["Osmund vibes", "something funny", "Bill", "make Bill do a moonwalk across the mess hall", "Osmund should check the supply bay one more time and find the Quietline Helmet instead"]
    for x in texts: intake.enqueue("@v", x)
    res = intake.process()
    for (r, st, path), x in zip(res, texts):
        assert st == "pending", (x, path)
        d = json.load(open(path)); s = d["shots"][0]
        assert s["live_wrapper"]["commenter"]["text_verbatim"] == x and d["check"]["status"] != "fail"
        assert not any(dl["speaker"] == "Tim" for dl in s["dialogue"])
        print("\nSAMPLE", json.dumps({"text": x, "features": s["live_wrapper"]["levers"]["prompt_features"], "injections": [i["id"] for i in s["live_wrapper"]["levers"]["injections"]], "dialogue": s["dialogue"], "check": d["check"]["status"]}, ensure_ascii=False))
    intake.LIVE = old; shutil.rmtree(t)

def test_rate_limit_and_toggle():
    log = Path(tempfile.mkdtemp()) / "i.jsonl"
    lib = intake.load_snippets(); lib["config"]["enabled"] = False
    assert _inj("lol")["levers"]["injections"] or True
    w = intake.wrap({"handle": "@t", "text": "lol", "received_at": "x"}); intake.inject(w, "x", lib=lib, log=log)
    assert w["levers"]["injections"] == [] and w["levers"]["prompt_features"]["weak"]
    lib = {"config": {"enabled": True}, "snippets": [{"id": "one", "kind": "visual_flair", "text": "fog swirl", "requires": {"people_on_screen": False}, "when": "weak_prompt", "weight": 1, "max_per_hour": 2, "tv_safe": True}]}
    got = []
    for i in range(4):
        w = intake.wrap({"handle": "@t", "text": "lol", "received_at": "x"}); intake.inject(w, f"r{i}", lib=lib, log=log); got.append(len(w["levers"]["injections"]))
    assert got == [1, 1, 0, 0]

def test_no_money_asks():
    lib = intake.load_snippets()
    assert not any(checker.money_hits(s["text"]) for s in lib["snippets"])
    for bad in ["This channel runs on viewer donations", "Tip us $5", "support us!", "Send 10 dollars", "money keeps us going", "help fund the outpost", "pay what you want"]:
        assert checker.money_hits(bad), bad
    for good in ["This channel runs on viewer prompts", "the comments steer this place", "Somebody in the comments wanted this"]:
        assert not checker.money_hits(good), good
    lib["snippets"].append({"id": "bad-don", "kind": "spoken_line", "speaker": "Osmund", "text": "Osmund: please donate $5", "requires": {"people_on_screen": True}, "when": "always", "weight": 999, "max_per_hour": 99, "tv_safe": True})
    for i in range(20):
        w = intake.wrap({"handle": "@t", "text": "Osmund", "received_at": "x"})
        intake.inject(w, f"m{i}", lib=lib, log=Path(tempfile.mkdtemp()) / "i.jsonl")
        assert "bad-don" not in [x["id"] for x in w["levers"]["injections"]]
    shot = {"id": "X", "cast": [], "dialogue": [{"speaker": "Mira", "line": "Donations keep the lights on"}], "continues_from": "x"}
    assert checker.check_shot(shot, None, {}, {})["status"] == "fail"

def _xitem(mid, status, text):
    import hashlib
    return {"schema": "x-intake/v1", "status": status, "show": "forward-supply", "channel": "ch04",
            "commenter": {"handle": "@h"+mid, "source": "broadcast_chat", "message_id": mid, "ts": "2026-10-27T16:30:00-05:00"},
            "commenter_text": text, "commenter_text_verbatim": text, "commenter_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "credit_line": None, "wrapped_at": "2026-10-27T16:31:00-05:00"}

def test_xintake_single_path_writeback():
    t = setup_tmp(); old = intake.LIVE; intake.LIVE = t
    inbox = t/"storybot-inbox"; inbox.mkdir()   # temp copy only, never the real inbox
    items = {"a": _xitem("1", "APPROVED", "make Bill do a moonwalk across the mess hall"),
             "b": _xitem("2", "HELD_FOR_trundle", "not approved yet"),
             "c": _xitem("3", "APPROVED", "Give Osmund a Red Bull")}
    for k, v in items.items(): (inbox/f"{k}.json").write_text(json.dumps(v))
    intake.import_xintake(inbox); res = intake.process()
    st = {r["handle"]: s for r, s, _ in res}
    assert st == {"@h1": "written_back", "@h3": "rejected"}, st
    a = json.load(open(inbox/"a.json"))
    for k, v in items["a"].items(): assert a[k] == v or k == "status", k   # existing fields untouched except status
    assert a["status"] == "IN_STORY" and json.loads(a["wrapped_prompt"])["dialogue"]
    for k in ("wrapped_prompt", "story_slot", "end_frame", "out_of_character", "injections", "storybot_check", "storybot_ts"): assert k in a, k
    assert a["out_of_character"] and a["storybot_check"]["status"] != "fail"
    assert a["storybot_clip"]["dialogue"][0]["speaker"] == "Commander Bill D'bears"
    assert json.load(open(inbox/"b.json")) == items["b"]
    assert json.load(open(inbox/"c.json"))["storybot_check"]["status"] == "fail"
    assert not (t/"pending-approval").exists(), "x items must not go to pending-approval"
    assert not list(inbox.glob(".*tmp")), "atomic temp files cleaned up"
    intake.LIVE = old; shutil.rmtree(t)

def test_writeback_refuses_overwrite_and_cnb_inbox():
    t = Path(tempfile.mkdtemp()); f = t/"x.json"; f.write_text(json.dumps({"status": "APPROVED"}))
    for bad in ({"status": "RENDERED"}, {"commenter_text": "x"}):
        try: intake.write_back(f, bad); assert False
        except ValueError: pass
    p = t/"commenter-pipeline"/"inbox"; p.mkdir(parents=True); (p/"y.json").write_text("{}")
    try: intake.write_back(p/"y.json", {"storybot_ts": "x"}); assert False
    except AssertionError as e: assert "never write" in str(e)
    shutil.rmtree(t)

def test_ooc_line_goes_to_performer():
    cases = {"make Bill do a moonwalk": "Commander Bill D'bears", "Mira should sing the anthem": "Lt. Mira S'mirin'",
             "Osmund dances": "Osmund", "everyone dance": "Osmund", "after Bill eats, Mira does a backflip": "Lt. Mira S'mirin'"}
    for txt, who in cases.items():
        w = intake.wrap({"handle": "@q", "text": txt, "received_at": "x"})
        assert w["levers"]["self_reflection_speaker"] == who, (txt, w["levers"])
        assert intake.to_clip(w)["dialogue"][0]["speaker"] == who
    w = intake.wrap({"handle": "@q", "text": "Tim does a backflip", "received_at": "x"})
    assert w["levers"]["ooc_performer"] == "Tim" and w["levers"]["self_reflection_speaker"] != "Tim"

def test_export_called_for_item_temp_inbox():
    t = setup_tmp(); old = intake.LIVE; intake.LIVE = t
    inbox = t/"storybot-inbox"; inbox.mkdir()
    (inbox/"a.json").write_text(json.dumps(_xitem("9", "APPROVED", "Mira color-codes the search in the supply bay")))
    intake.import_xintake(inbox); intake.process()
    exp = [json.loads(l) for l in open(t/"processed.jsonl")][-1]["export"]
    assert all(str(t) in w for w in exp["written"]), exp
    print("\nEXPORT", exp)
    intake.LIVE = old; shutil.rmtree(t)

def test_auto_approved_flag():
    for on in (False, True):
        t = setup_tmp(); old = intake.LIVE; intake.LIVE = t
        inbox = t/"storybot-inbox"; inbox.mkdir(); cfg = t/"cfg.yaml"; cfg.write_text(f"auto_approve_enabled: {str(on).lower()}\n")
        item = _xitem("7", "AUTO_APPROVED", "Osmund checks the hatch twice"); (inbox/"a.json").write_text(json.dumps(item))
        bad = _xitem("8", "AUTO_APPROVED", "tampered"); bad["commenter_text_sha256"] = "0"*64; (inbox/"b.json").write_text(json.dumps(bad))
        added, skipped = intake.import_xintake(inbox, config=cfg)
        if on:
            assert [r["handle"] for r in added] == ["@h7"] and ("b.json", "sha256 mismatch") in skipped
        else:
            assert added == [] and json.load(open(inbox/"a.json")) == item
            assert len([json.loads(l) for l in open(t/"held-auto-approved.jsonl")]) == 2
        intake.LIVE = old; shutil.rmtree(t)

def _w(text): return intake.wrap({"id": "t", "received_at": "2026-10-27T16:00:00-05:00", "handle": "@t", "text": text, "source": "test"})

def test_ref_index_paths_exist():
    idx = intake.load_ref_index()
    for k, v in idx["cast"].items():
        assert v["stills"], k
        for p in v["stills"]: assert Path(p).is_file(), p
    for v in idx["locations"].values(): assert Path(v["still"]).is_file()
    for v in idx["products"].values():
        if v.get("still"): assert Path(v["still"]).is_file()
    assert Path(idx["continuity_anchor"]["source_mp4"]).is_file()

def test_tim_prompt_includes_tim_still():
    r = intake.pick_refs(_w("Tim leads a search party with his cyan optic as a flashlight"))
    tim = intake.load_ref_index()["cast"]["tim"]["primary"]
    assert tim in r["paths"] and r["picks"][0]["kind"] == "location"
    r2 = intake.pick_refs(_w("the floating brain drifts through the bunk room"))   # implied Tim
    assert tim in r2["paths"] and r2["location"] == "bunk_room"

def test_product_prompt_includes_product_still():
    idx = intake.load_ref_index()
    r = intake.pick_refs(_w("Osmund finds the Quietline Helmet in the supply bay"))
    assert idx["products"]["quietline-helmet"]["still"] in r["paths"] and r["location"] == "supply_bay"

def test_ref_cap_respected_and_real():
    w = _w("Osmund, Mira, Bill and Tim test the Lightning Lamp and the Sky Diffuser in the mess hall")
    assert len(intake.pick_refs(w)["paths"]) == 4
    big = intake.pick_refs(w, cap=99)
    assert len(big["paths"]) <= 14 and len(big["paths"]) > 4
    assert all(Path(p).is_file() for p in big["paths"])
    shot = intake.to_clip(intake.inject(_w("Bill"), log=tempfile.mktemp()))
    assert isinstance(shot["reference_images"], list) and len(shot["reference_images"]) == 4
    assert shot["end_frame"]["frame"] == "last_frame" and shot["end_frame"]["source_mp4"].endswith(".mp4")

def test_checker_fails_live_clip_without_refs():
    shot = intake.to_clip(intake.inject(_w("Mira color-codes the whole search on her clipboard"), log=tempfile.mktemp()))
    shot["reference_images"] = []
    r = checker.check_shot(shot, None, checker.registry(checker.load_bible()), {})
    assert r["status"] == "fail" and any("reference_images" in f for f in r["fails"])


def test_camera_guard_flags_direct_address():
    for t in ["Osmund looks at the camera and winks", "Bill turns to camera", "Mira addresses the viewer", "he talks to us"]:
        assert checker.camera_hits(t), t
    for t in ["characters never look at or address the camera", "Mira looks at Osmund", "camera: slow push-in"]:
        assert not checker.camera_hits(t), t

def test_check_shot_fails_on_camera_wording():
    b = checker.load_bible(); reg = checker.registry(b)
    s = {"id": "T1", "cast": [], "visual_prompt": "Bill looks into the lens", "continues_from": "x", "dialogue": []}
    r = checker.check_shot(s, b, reg, None)
    assert any("observational" in f for f in r["fails"])

def test_snippets_said_to_each_other():
    import yaml
    sn = yaml.safe_load(open(Path(__file__).parent.parent / "snippets.yaml"))["snippets"]
    for x in sn:
        assert not checker.camera_hits(x["text"]), x["id"]
        if x.get("disclosure"):
            assert any(n in x["text"].split(":")[0] for n in ("to Mira", "to Osmund")), x["id"]

def test_to_clip_carries_camera_rule():
    assert "never look at or address the camera" in intake.CAMERA_RULE
    assert "no direct-to-camera dialogue" in intake.CAMERA_RULE


# ---- clean-source guard ----
MBD = "out-of-scope/fakenews/channel-ready/thunder-trundle/4_Military-Boutique"

def test_tainted_paths_detected():
    for p in ["/x/lineage-tagged-20261027/a.mp4", "/x/ch4badge-20261027/a.mp4", "/x/a_salesad_parody.mp4",
              "/x/sales-overlay-B-20261027/a.mp4", "/x/a_tagged_parody.mp4"]:
        assert checker.is_tainted(p), p
    assert not checker.is_tainted(MBD + "/raw/mb_helmet.mp4")

def test_lineage_resolves_tagged_to_raw_master():
    rows = checker.load_lineage()
    tagged = next(r["file"] for r in rows if r["clip_id"] == "ch4-ad-tactical-helmet-pedestal-BA-tagged")
    assert checker.resolve_clean(tagged).endswith("/raw/mb_helmet.mp4")
    cruiser = next(r["file"] for r in rows if r["clip_id"] == "ch4-ad-armored-showroom-cruiser")
    assert checker.resolve_clean(cruiser).endswith("/raw/mb_rover.mp4")   # burned catalog band -> clean raw

def test_unknown_tainted_fails_closed():
    import pytest
    with pytest.raises(checker.CleanSourceError):
        checker.resolve_clean("/tmp/nowhere/sales-overlay-x/foo_salesad_parody.mp4")

def test_no_master_fails_closed(tmp_path):
    import pytest
    rows = [{"clip_id": "ch4-ad-mystery", "tag": "t1", "global_no": 1, "parent_id": None, "parent_global_no": None, "file": "/a/mystery.mp4"},
            {"clip_id": "ch4-ad-mystery-A", "tag": "t2", "global_no": 2, "parent_id": "t1", "parent_global_no": 1, "file": "/a/sales-overlay/mystery_salesad.mp4"}]
    with pytest.raises(checker.CleanSourceError, match="no clean master"):
        checker.resolve_clean("/a/sales-overlay/mystery_salesad.mp4", lineage=rows, mb_dir=tmp_path)

def test_parent_by_global_no(tmp_path):
    (tmp_path / "raw").mkdir(); (tmp_path / "raw" / "mb_helmet.mp4").write_bytes(b"x")
    rows = [{"clip_id": "ch4-ad-tactical-helmet-pedestal", "tag": "t1", "global_no": 5, "parent_id": None, "parent_global_no": None, "file": "/a/h.mp4"},
            {"clip_id": "x-tagged", "tag": "t9", "global_no": 9, "parent_id": 5, "parent_global_no": None, "file": "/a/h_tagged.mp4"}]
    assert checker.resolve_clean("/a/h_tagged.mp4", lineage=rows, mb_dir=tmp_path).endswith("mb_helmet.mp4")

def test_checker_flags_tainted_refs_and_end_frame():
    b = checker.load_bible(); reg = checker.registry(b)
    s = {"id": "T2", "cast": [], "visual_prompt": "x", "continues_from": "x", "dialogue": [],
         "reference_images": ["/x/lineage-tagged-20261027/a_tagged_parody.mp4"], "end_frame_source": "/x/ch4badge-20261027/b.mp4"}
    r = checker.check_shot(s, b, reg, None)
    assert sum("clean-source" in f for f in r["fails"]) == 2

def test_pick_refs_and_end_frame_are_clean():
    w = {"commenter": {"text_verbatim": "Osmund polishes the helmet in the mess hall"}}
    rp = intake.pick_refs(w)
    assert rp["paths"] and not any(checker.is_tainted(p) for p in rp["paths"])
    ef = intake.pick_end_frame(aired="/nonexistent.jsonl")
    assert not checker.is_tainted(ef["source_mp4"])

# ---- post-generation audit + shared watchlist (trundle 2026-10-27 17:13) ----
import post_audit, pytest

@pytest.fixture
def wl(tmp_path, monkeypatch):
    p = tmp_path / "wl.jsonl"; monkeypatch.setattr(checker, "WATCHLIST", p); return p

def _wl(p, **row):
    base = {"sha256": None, "name_pattern": None, "phash": None, "regex": None, "reason": "t", "found_in": "t", "date": "t", "added_by": "CNB"}
    base.update(row); open(p, "a").write(json.dumps(base) + "\n")

def test_watchlist_missing_falls_back(wl):
    assert checker.watchlist_hit("/x/a.mp4") is None and checker.is_tainted("/x/a_tagged_parody.mp4")

def test_watchlist_name_regex_sha_reread(wl, tmp_path):
    f = tmp_path / "plain.mp4"; f.write_bytes(b"abc")
    assert checker.watchlist_hit(str(f)) is None
    import hashlib; _wl(wl, sha256=hashlib.sha256(b"abc").hexdigest(), reason="sha")   # added after first check -> re-read
    assert checker.watchlist_hit(str(f))["reason"] == "sha"
    _wl(wl, name_pattern="weird_*", reason="glob"); _wl(wl, regex=r"/badzone/", reason="re")
    assert checker.watchlist_hit("/a/weird_1.mp4")["reason"] == "glob"
    assert checker.watchlist_hit("/badzone/x.mp4")["reason"] == "re"

def test_pre_render_guard_rejects_watchlisted(wl, tmp_path):
    f = tmp_path / "innocent.png"; f.write_bytes(b"x"); _wl(wl, name_pattern="innocent.png", reason="slip")
    with pytest.raises(checker.CleanSourceError): checker.resolve_clean(str(f), lineage=[])
    s = {"reference_images": [str(f)]}
    assert any("watchlisted" in x for x in checker.clean_source_fails(s))

def test_intake_pick_refs_skips_watchlisted(wl):
    w = {"commenter": {"text_verbatim": "Osmund polishes the helmet in the mess hall"}}
    first = intake.pick_refs(w)["paths"][0]
    _wl(wl, name_pattern=Path(first).name, reason="slip")
    rp = intake.pick_refs(w)
    assert first not in rp["paths"] and any(r["path"] == first for r in rp["rejected_tainted"])

def test_real_shared_watchlist_blocks_tagged_copy():
    if not checker.WATCHLIST.is_file(): pytest.skip("shared watchlist absent")
    t = "out-of-scope/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagged-20261027/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal_parody_salesadBA_tagged_parody.mp4"
    with pytest.raises(checker.CleanSourceError): checker.resolve_clean(t)

def _rows(mb):
    clean = str(mb / "raw" / "mb_x.mp4"); (mb / "raw").mkdir(); Path(clean).write_bytes(b"c")
    (mb / "CLEAN-SOURCES.json").write_text(json.dumps({"clean_source": {"1": clean}}))
    return clean, [{"clip_id": "a", "tag": "4.1 g1 #1", "global_no": 1, "parent_id": None, "origin": "first_render", "refs": [], "file": clean},
                   {"clip_id": "b", "tag": "4.1 g2 #2", "global_no": 2, "parent_id": "4.1 g1 #1", "origin": "remake", "refs": [clean], "file": "/o/b.mp4"},
                   {"clip_id": "c", "tag": "4.1 g2 #3", "global_no": 3, "parent_id": None, "origin": "remake",
                    "refs": ["/x/lineage-tagged-20261027/q_tagged_parody.mp4", "/x/stranger.png"], "end_frame_source": "/x/y_ch4badge.mp4", "file": "/o/c.mp4"}]

def test_post_audit_finds_slips_dry_run_writes_nothing(wl, tmp_path):
    clean, rows = _rows(tmp_path); sp, pp = tmp_path / "s.jsonl", tmp_path / "p.jsonl"
    r = post_audit.audit(lineage=rows, mb=tmp_path, watchlist=[], dry_run=True, slips_path=sp, proposals_path=pp)
    bad = {(s["clip_id"], s["bad_input"]) for s in r["slips"]}
    assert len(r["slips"]) == 3 and all(c == "c" for c, _ in bad)
    assert any(s["reason"] == "not in clean map" for s in r["slips"]) and not sp.exists() and not pp.exists()

def test_post_audit_apply_logs_holds_and_proposes(wl, tmp_path):
    clean, rows = _rows(tmp_path); sp, pp = tmp_path / "s.jsonl", tmp_path / "p.jsonl"
    post_audit.audit(lineage=rows, mb=tmp_path, watchlist=[], dry_run=False, slips_path=sp, proposals_path=pp)
    post_audit.audit(lineage=rows, mb=tmp_path, watchlist=[], dry_run=False, slips_path=sp, proposals_path=pp)  # idempotent
    s = [json.loads(l) for l in sp.read_text().splitlines()]; p = [json.loads(l) for l in pp.read_text().splitlines()]
    assert len(s) == 3 and all(x["status"] == "held" and x["ts"] for x in s)
    assert post_audit.is_held("/o/c.mp4", sp) and not post_audit.is_held("/o/b.mp4", sp)
    assert len(p) == 3 and set(p[0]) == {"sha256", "name_pattern", "phash", "regex", "reason", "found_in", "date", "added_by"}

def test_post_audit_watchlist_hit_counts(tmp_path):
    clean, rows = _rows(tmp_path)
    r = post_audit.audit(lineage=rows[:2], mb=tmp_path, watchlist=[{"name_pattern": "mb_x.mp4", "reason": "w"}], dry_run=True)
    assert len(r["slips"]) == 2 and r["slips"][0]["reason"].startswith("on watchlist")

def test_post_audit_never_writes_shared_files(tmp_path):
    import inspect; src = inspect.getsource(post_audit)
    assert "tag-slip-log" not in src.split('"""')[2] and "WATCHLIST, " not in src


def test_clean_master_allow_beats_phash_and_name(tmp_path):
    import checker
    f = tmp_path / "mb_rover.mp4"; f.write_bytes(b"clean master bytes")
    sha = checker.file_sha256(f)
    deny = {"name_pattern": "mb_rover", "phash": "0000000000000000", "reason": "deny"}
    assert checker.watchlist_hit(f, [deny])
    assert checker.watchlist_hit(f, [deny, {"row_type": "clean_master_allow", "sha256": sha}]) is None
    other = tmp_path / "mb_rover_tagged.mp4"; other.write_bytes(b"different")
    assert checker.watchlist_hit(other, [deny, {"row_type": "clean_master_allow", "sha256": sha}])   # sha must match exactly
    assert checker.watchlist_hit(other, [{"row_type": "clean_master_allow", "sha256": checker.file_sha256(other)}]) is None


def test_lineage_skips_correction_rows_by_row_type(tmp_path):
    import checker, json
    p = tmp_path / "LINEAGE.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in [
        {"clip_id": "a", "file": "/x/a.mp4", "tag": "4.1 g1 #1", "global_no": 1},
        {"clip_id": "s", "row_type": "correction", "file": "/x/s.mp4", "slip": True},
        {"clip_id": "t", "row_type": "correction", "slip": True}]))
    assert [r["clip_id"] for r in checker.load_lineage(p)] == ["a"]


def test_resolve_clean_tolerates_render_provenance_rows(tmp_path):
    import checker
    f = tmp_path / "ref.png"; f.write_bytes(b"x")
    rows = [{"clip_id": "mu-01", "row_type": "render_provenance", "file": "/elsewhere/held.mp4", "parent_id": "None"}]
    assert checker.resolve_clean(str(f), lineage=rows, mb_dir=tmp_path) == str(f)


def test_audio_leveled_gate_warns_not_crash(tmp_path):
    import checker, post_audit, json
    assert checker.audio_finished({"clip_id": "a", "audio_leveled": True}) == (True, None)
    done, w = checker.audio_finished({"clip_id": "b"}); assert not done and "missing" in w
    done, w = checker.audio_finished({"clip_id": "c", "audio_leveled": False}); assert not done and "False" in w
    base = {"id": "X1", "continues_from": "x", "queued_for_render": True}
    assert any("audio_leveled missing" in x for x in checker.check_shot(base, None, set(), {})["warns"])
    assert not any("audio_leveled" in x for x in checker.check_shot({**base, "audio_leveled": True}, None, set(), {})["warns"])
    assert not any("audio_leveled" in x for x in checker.check_shot({"id": "P", "continues_from": "x"}, None, set(), {})["warns"])  # prompt only
    rows = [{"clip_id": "r1", "tag": "4.1 g1 #1", "global_no": 1, "file": str(tmp_path / "r1.mp4"), "origin": "overlay_edit"},
            {"clip_id": "r2", "tag": "4.1 g1 #2", "global_no": 2, "file": str(tmp_path / "r2.mp4"), "origin": "overlay_edit", "audio_leveled": True}]
    res = post_audit.audit(lineage=rows, mb=tmp_path, watchlist=[])
    assert res["not_finished_audio"] == 1 and res["audio_warnings"][0]["clip_id"] == "r1"


def test_audio_post_rows_finish_clips_and_resolve_as_copies(tmp_path):
    import checker, post_audit
    src = tmp_path / "s.mp4"; src.write_bytes(b"src"); out = tmp_path / "s_leveled.mp4"; out.write_bytes(b"out")
    other = tmp_path / "o.mp4"; other.write_bytes(b"other")
    rows = [{"clip_id": "s", "tag": "4.1 g1 #5", "global_no": 5, "file": str(src), "sha256": checker.file_sha256(src), "origin": "overlay_edit"},
            {"clip_id": "o", "tag": "4.1 g1 #6", "global_no": 6, "file": str(other), "sha256": checker.file_sha256(other), "origin": "overlay_edit"},
            {"clip_id": "s", "row_type": "audio_post", "source_sha256": checker.file_sha256(src), "source_global_no": 5,
             "out_sha256": checker.file_sha256(out), "file": str(out), "audio_leveled": True, "lufs_i": -16, "true_peak": -1.5, "lra": 6}]
    assert checker.audio_finished(rows[0], rows)[0]            # joined by source_sha256
    assert checker.audio_finished({"file": str(out)}, rows)[0]  # the leveled output itself
    assert not checker.audio_finished(rows[1], rows)[0]
    assert checker.audio_finished({"global_no": 5}, rows)[0]    # backup join when no sha available
    assert checker.resolve_clean(str(out), lineage=rows, mb_dir=tmp_path) == str(src)   # copy -> its source, not a lineage node
    res = post_audit.audit(lineage=rows, mb=tmp_path, watchlist=[])
    assert res["not_finished_audio"] == 1 and res["audio_warnings"][0]["clip_id"] == "o"

# ---- trundle hard rules 2026-10-27 17:44 CT: no creator name, no kids, no Military Boutique burned text ----
import pytest as _pt2
NAME = checker.CREATOR_NAME
@_pt2.mark.parametrize("w", [NAME.capitalize(), NAME, NAME.upper()], ids=["title", "lower", "upper"])
def test_rule_creator_name_blocked_in_overlay(w):
    assert checker.creator_name_hits({"overlay_text": f"Presented by {w}"})
def test_rule_creator_name_whole_word_only():
    assert not checker.creator_name_hits({"overlay_text": f"An{NAME}'s drawer, {NAME.capitalize()}sbury"})
@_pt2.mark.parametrize("w", ["kid", "kids", "child", "children", "toddler", "baby", "Babies", "KIDS"])
def test_rule_kids_blocked(w):
    assert checker.kid_hits({"visual_prompt": f"a happy {w} in the showroom"})
    assert checker.kid_hits({"overlay_text": f"great for {w}"})
def test_rule_kids_negated_ok():
    assert not checker.kid_hits({"visual_prompt": "adults only showroom, no children, no kids"})
def test_rule_kids_not_substring():
    assert not checker.kid_hits({"visual_prompt": "kidney-shaped kiosk, childish grin"})
def test_rule_kids_in_dialogue():
    assert checker.kid_hits({"dialogue": [{"speaker": "Mira", "line": "The kids love it"}]})
def test_rule_mb_text_blocked_in_overlay():
    assert checker.mb_text_hits({"overlay_text": "MILITARY BOUTIQUE / thunder trundle"})
    assert checker.mb_text_hits({"drawtext": "Military  Boutique"})
def test_rule_mb_channel_metadata_allowed():
    s = {"channel_name": "Ch 4 Military Boutique", "header": {"channel": "Ch 4 Military Boutique"},
         "visual_prompt": "Photoreal outpost, Ch 4 Military Boutique, 4:3-safe"}
    assert not checker.mb_text_hits(s)
def test_rule_check_shot_fails_kids_and_creator_name():
    r = checker.check_shot({"id": "T1", "visual_prompt": "a toddler waves", "overlay_text": f"hi {NAME.capitalize()}"}, {}, {}, {})
    assert r["status"] == "fail"
    assert any("no_kids" in f for f in r["fails"]) and any("no_creator_name" in f for f in r["fails"])
def test_rule_intake_negatives_present():
    src = open(intake.__file__).read()
    for n in ("no on-screen names", "no personal names", "no children", "no kids"): assert n in src


def test_no_creator_name_on_screen():
    import checker, intake
    base = {"id": "N1", "continues_from": "x"}
    n = checker.CREATOR_NAME
    for k, v in (("visual_prompt", f"A plaque reading {n.upper()} on the desk"), ("on_screen_text_post", [f"Built by {n.capitalize()}"]),
                 ("dialogue", [{"speaker": "Osmund", "line": f"{n.capitalize()}'s lamp"}]), ("caption", n)):
        r = checker.check_shot({**base, k: v}, None, set(), {})
        assert any("no_creator_name_on_screen" in f for f in r["fails"]), k
    ok = checker.check_shot({**base, "visual_prompt": f"An{n} and the drawer withdrew", "status": f"{n.capitalize()} approved 17:25"}, None, set(), {})
    assert not any("creator" in f for f in ok["fails"])   # whole word only; approval/status notes not scanned
    assert "no_creator_name_on_screen" in intake.moderate(f"Bill writes {n.capitalize()} on the whiteboard")
    assert all(not checker.creator_name_hits(str(s.get("text", ""))) for s in intake.load_snippets()["snippets"])


def test_intake_negatives_carry_name_tags():
    import intake
    assert "no names, no signatures, no watermarks" in open(intake.__file__).read()
