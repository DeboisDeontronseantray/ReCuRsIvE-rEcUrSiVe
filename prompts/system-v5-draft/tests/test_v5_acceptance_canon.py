"""Acceptance specs for the hard canon rules (plan section 5), plus no-live-edit and gate-baseline checks.

SKIPPED until Trundle approves the plan (PR #3). Interfaces are PROPOSED (docs/IMPLEMENTATION-STEPS-v1.md section 3)."""
import copy
import hashlib
import json
import re

import pytest

import apply_check_v44
import layers_v4
from conftest import DRYRUN, FIX, NP16, NP17, REPO, V4

pytestmark = pytest.mark.skip(reason="awaiting plan approval")

BASE = json.loads((NP16 / "base_spec.json").read_text())
OUT = DRYRUN / "night-porter"
PROTECTED_TREES = [V4 / d for d in ("prompts_v4", "prompts_v41", "prompts_v42", "prompts_v43", "prompts_v44", "config", "tools", "tests")]
PROTECTED_FILES = [REPO / "story-engine" / "engine" / f for f in ("assemble_prompt.py", "bundle_assembler.py")]


def _manifest():
    files = [p for t in PROTECTED_TREES for p in sorted(t.rglob("*")) if p.is_file() and "__pycache__" not in p.parts] + PROTECTED_FILES
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


@pytest.fixture
def assemble(v5):
    def go(base=None, **kw):
        bs = base or NP16 / "base_spec.json"
        return v5("assemble_next").assemble_next(inputs_dir=kw.pop("inputs_dir", NP17), base_spec=bs, out_dir=kw.pop("out_dir", OUT), clip_id=kw.pop("clip_id", "NP17"), **kw)
    return go


def _gate(r, clip_id="NP17"):
    return apply_check_v44.check(r["args"]["prompt"], r["args"], r["spec"], r["sidecar"], clip_id=clip_id)


def test_nobody_looks_into_the_camera(assemble):
    r = assemble()
    p = r["args"]["prompt"]
    assert _gate(r)["R-EYES nobody into camera (Oct 29 rule)"][0] == "PASS"
    assert not re.search(r"looks? (in|into|at) (the )?(camera|lens)", p.replace("Nobody looks into the camera.", ""), re.I)


def test_reference_image_required_unless_exempt(assemble, tmp_path, v5):
    spec = copy.deepcopy(BASE) | {"refs_raw": []}
    spec["extra"] = [x.replace("(<IMAGE_2>)", "") for x in spec["extra"]]
    p = tmp_path / "no_refs.json"
    p.write_text(json.dumps(spec))
    with pytest.raises(v5("assemble_next").ReferenceImageRequired):
        assemble(base=p)
    assert len(apply_check_v44.exempt_ids()) == 16 and "NP17" not in apply_check_v44.exempt_ids()


def test_commenter_images_off(assemble, v5, tmp_path, monkeypatch):
    cfg = tmp_path / "commenter_images.json"
    cfg.write_text(json.dumps({"enabled": True}))
    monkeypatch.setattr(v5("assemble_next"), "COMMENTER_IMAGES_CFG", cfg)
    with pytest.raises(v5("assemble_next").CommenterImagesOn):
        assemble()


def test_handles_never_in_prompt_or_outputs(assemble):
    r = assemble()
    assert _gate(r)["R-NOHANDLES no contributor handles in prompt (10:48 PM)"][0] == "PASS"
    assert r["sidecar"].get("contributors", []) == []
    for f in OUT.rglob("*"):
        if f.is_file():
            assert "PLACEHOLDER_" not in f.read_text() and '"handle"' not in f.read_text(), f


def test_fixed_threads_stay_off(assemble):
    r = assemble()
    p = r["args"]["prompt"]
    for t in layers_v4.fixed_threads()["threads"]:
        assert t["status"] == "PENDING"
        assert t["what"] not in p
    assert "[Thread:" not in p


def test_no_kids_no_real_people_or_brands(assemble):
    g = _gate(assemble())
    assert g["R-KIDS no kids"][0] == "PASS"
    assert g["R-BRANDS parody brands, no names on screen (CR L34)"][0] == "PASS"


def test_masters_stay_pure(assemble):
    r = assemble()
    p = r["args"]["prompt"]
    assert _gate(r)["R-OVERLAY no tags/state digits in prompt (overlays post)"][0] == "PASS"
    assert not re.search(r"genealogy|lower third|corner tag|watermark|#\d", p, re.I)


def test_ch4_stays_photoreal_1971(assemble):
    bi = FIX / "black-ice"
    r = assemble(base=bi / "BI01" / "base_spec.json", inputs_dir=bi / "BI02", clip_id="BI02")
    p = r["args"]["prompt"]
    assert p.startswith("[Look: Photoreal live-action 1971 Cold War spy thriller")
    assert _gate(r, "BI02")["R-CH4 photoreal 1971 (Oct 30 7:13 PM)"][0] == "PASS"


def test_no_live_files_change_during_dry_run(assemble):
    before = _manifest()
    assemble()
    assert _manifest() == before
