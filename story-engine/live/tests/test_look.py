# 2026-10-28 11:55 PM CT Director (Trundle pt150u): opt-in --look. Add-only.
import sys, subprocess, json
sys.path.insert(0, "/workspace/streaming/story-engine/engine")
import assemble_prompt as ap
BI01 = "/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments/BI-01.yaml"
LK = ap.load_look("noir-graphic-novel")

def test_look_v2_adds_no_text():
    # 2026-10-29 pt152u: look is the ref recipe; style_block/camera_line null -> no text appended
    assert LK["style_block"] is None and LK["camera_line"] is None
    base = ap.assemble(BI01, dense=True)
    out = ap.apply_look(ap.assemble(BI01, dense=True), "noir-graphic-novel")
    assert out["dense_prompt"] == base["dense_prompt"] and out["dense_prompt_sha256"] == base["dense_prompt_sha256"]
    assert out["look"]["id"] == "noir-graphic-novel"

def test_no_look_or_non_dense_unchanged():
    a = ap.assemble(BI01); assert ap.apply_look(dict(a), "noir-graphic-novel") == a
    d = ap.assemble(BI01, dense=True); assert ap.apply_look(dict(d), None) == d

def test_idempotent_and_cli():
    base = ap.assemble(BI01, dense=True)["dense_prompt"]
    o = ap.apply_look(ap.apply_look(ap.assemble(BI01, dense=True), "noir-graphic-novel"), "noir-graphic-novel")
    assert o["dense_prompt"] == base
    r = subprocess.run([sys.executable, "/workspace/streaming/story-engine/engine/assemble_prompt.py", BI01, "--dense", "--look", "noir-graphic-novel"], capture_output=True, text=True)
    j = json.loads(r.stdout); assert j["dense_prompt"] == base and j["look"]["id"] == "noir-graphic-novel"
