"""Acceptance specs for the NP17 dry run: placement, slot diff vs the current builder, gate, outputs.

Interfaces follow docs/IMPLEMENTATION-STEPS-v1.md section 3; spec changes required by D4/D5 are listed in the implementation PR.
Outputs go only to system-v5-draft/out/dryrun/, which is git-ignored (Decision 12)."""
import json
import re

import pytest

import apply_check_v44
import build_prompt_v42
import yaml
from conftest import CHARMETA, DRYRUN, NP16, NP17, fixture_inputs


BASE = json.loads((NP16 / "base_spec.json").read_text())
OUT = DRYRUN / "night-porter"
COMMENT_TOKENS = ["luggage trolley", "desk bell", "lobby clock jumps"]
ALLOWED_CHANGED_SLOTS = {"continue", "beats"}


@pytest.fixture
def run(v5, assembly_harness):
    return v5("assemble_next").assemble_next(inputs_dir=NP17, base_spec=NP16 / "base_spec.json", out_dir=OUT, clip_id="NP17", **fixture_inputs(NP17))


@pytest.fixture
def slots(v5):
    return v5("report").slot_split


def test_outputs_written_only_under_out_dryrun(run):
    names = {p.name for p in OUT.iterdir()}
    assert {"NP17.args.json", "NP17.meta.json", "NP17.assembly.json", "NP17.memory.proposed.json", "DIFF-NP17.md", "GATE-NP17.json"} <= names
    assert all(p.resolve().is_relative_to(DRYRUN.resolve()) for p in OUT.rglob("*"))


def test_only_beats_and_continue_differ_from_current_builder(run, slots):
    current = build_prompt_v42.build(BASE, strict=True)["args"]["prompt"]
    a, b = slots(current), slots(run["args"]["prompt"])
    assert set(a) == set(b)
    assert {k for k in a if a[k] != b[k]} <= ALLOWED_CHANGED_SLOTS


def test_args_only_change_start_frame(run):
    current = build_prompt_v42.build(BASE, strict=True)["args"]
    assert run["args"]["reference_image_paths"] == current["reference_image_paths"]
    assert run["args"]["image_path"] == "<TT_CLIPS>/NP16_last.png" != current["image_path"]
    assert run["args"]["duration"] == current["duration"]


def test_gate_v44_passes(run):
    rep = apply_check_v44.check(run["args"]["prompt"], run["args"], run["spec"], run["sidecar"], clip_id="NP17")
    assert [k for k, v in rep.items() if v[0] == "FAIL"] == []
    assert json.loads((OUT / "GATE-NP17.json").read_text())["fails"] == []


def test_beat_and_word_budget(run):
    p = run["args"]["prompt"]
    assert len(re.findall(r"At [\d.]+ s,", p)) <= 6
    assert len(p.split()) <= 330


def test_comment_text_lands_only_in_beats(run, slots):
    s = slots(run["args"]["prompt"])
    for tok in COMMENT_TOKENS:
        hits = [k for k, v in s.items() if tok in v]
        assert hits in ([], ["beats"]), (tok, hits)
    assert any(tok in s["beats"] for tok in COMMENT_TOKENS)


def test_held_and_dropped_comments_never_reach_prompt(run):
    p = run["args"]["prompt"]
    assert "kid runs" not in p and "@" not in p and "PLACEHOLDER" not in p and "example.invalid" not in p
    held = run["assembly"]["comments"]["held"]
    assert [h["status"] for h in held] == ["HELD"] and "handle" not in json.dumps(run["assembly"])


def test_overflow_is_carried_not_dropped(run):
    c = run["assembly"]["comments"]
    assert len(c["placed"]) + len(c["carried"]) + len(c["held"]) + len(c["dropped"]) == 5


def test_memory_and_still_meta_reach_beats_without_looks(run, slots):
    beats = slots(run["args"]["prompt"])["beats"]
    assert "maroon" not in beats and "mustache" not in beats
    assert "cracked glass" in beats
    assert "favour" not in beats and "button" not in beats


def test_cast_entry_stays_name_and_tag(run):
    assert "MARLO QUILL (<IMAGE_2>)" in run["args"]["prompt"]


def test_proposed_memory_update_is_output_only(run):
    yml = CHARMETA / "11-fist-theater.yaml"
    before = yml.read_bytes()
    proposed = json.loads((OUT / "NP17.memory.proposed.json").read_text())
    assert proposed == {"clip_id": "NP17", "proposals": []}
    assert yml.read_bytes() == before


def test_deterministic(v5, tmp_path, assembly_harness):
    an = v5("assemble_next").assemble_next
    a = an(inputs_dir=NP17, base_spec=NP16 / "base_spec.json", out_dir=tmp_path / "a", clip_id="NP17", **fixture_inputs(NP17))
    b = an(inputs_dir=NP17, base_spec=NP16 / "base_spec.json", out_dir=tmp_path / "b", clip_id="NP17", **fixture_inputs(NP17))
    assert a["args"] == b["args"] and a["sidecar"] == b["sidecar"]
