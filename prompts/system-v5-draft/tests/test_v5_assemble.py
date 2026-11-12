"""Step 8: assemble_next end to end (parity mode, D4 identity removal, D6/D7 locks, gate screening, budgets, refusals)."""
import json
import re
import shutil

import pytest

import build_prompt_v42
import paths
from conftest import DRYRUN, LEDGER, NP16, NP17, NOW, V4, fixture_inputs

BASE = NP16 / "base_spec.json"
LIVE = V4 / "prompts_v44" / "odyssey"


@pytest.fixture
def an(v5, assembly_harness):
    return v5("assemble_next").assemble_next


def _inputs(tmp_path, comments):
    d = tmp_path / "NP17"
    shutil.copytree(NP17, d)
    (d / "comments.jsonl").write_text("".join(json.dumps(c) + "\n" for c in comments))
    return d


def test_parity_mode_is_byte_identical_to_current_builder_and_live(an, tmp_path):
    r = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, advance=False)
    assert r["args"] == build_prompt_v42.build(json.loads(BASE.read_text()), strict=True)["args"]
    assert r["args"] == json.loads((LIVE / "NP16.args.json").read_text())
    assert r["sidecar"] == json.loads((LIVE / "NP16.meta.json").read_text())
    assert r["diff"]["identical_prompt"] and r["diff"]["changed_slots"] == []


def test_handles_and_contributor_ids_never_reach_prompt_or_outputs(an, tmp_path):
    spool = tmp_path / "spool.jsonl"
    spool.write_text(json.dumps({"ts": "2026-10-31T21:18:00-05:00", "text": "@PLACEHOLDER_SPOOLUSER_LONGNAME rings the desk bell cp-0123456789ab",
                                 "handle": "PLACEHOLDER_SPOOLUSER_LONGNAME", "user_id": "998877665544", "id": "cp-0123456789ab"}) + "\n")
    out = tmp_path / "out"
    r = an(inputs_dir=NP17, base_spec=BASE, out_dir=out, **fixture_inputs(NP17) | {"spool_path": spool})
    assert re.search(r"At [\d.]+ s, rings the desk bell\.", r["args"]["prompt"])
    for f in out.iterdir():
        txt = f.read_text()
        for tok in ("PLACEHOLDER", "998877665544", "cp-0123456789ab", '"handle"', '"user_id"'):
            assert tok not in txt, (f.name, tok)
    assert r["gate"]["report"]["R-NOHANDLES no contributor handles in prompt (10:48 PM)"][0] == "PASS"
    assert r["sidecar"]["contributors"] == []


def test_locked_thread_holder_enters_only_as_hard_constraint(an, tmp_path, monkeypatch, v5):
    spots = paths.config("spots")
    spots["spot_types"]["fight"]["thread_holder"] = "MARLO keeps the jade key"
    lm = v5("adapters.locked_meta")
    real = lm.thread_holder
    monkeypatch.setattr(lm, "thread_holder", lambda st, cfg=None: real(st, cfg or spots))
    inp = _inputs(tmp_path, [{"ts": "2026-10-31T21:18:00-05:00", "text": "[Thread: the key is lost] the clock jumps"}])
    r = an(inputs_dir=inp, base_spec=BASE, out_dir=tmp_path / "out", **fixture_inputs(inp))
    p = r["args"]["prompt"]
    assert "[Thread: Must hold: MARLO keeps the jade key.]" in p and p.count("[Thread:") == 1
    assert "the key is lost" in p.split("[Thread: Must hold")[1].split("Continue from")[1]
    assert r["gate"]["fails"] == []


def test_comment_that_would_fail_the_gate_is_held(an, tmp_path):
    inp = _inputs(tmp_path, [{"ts": "2026-10-31T21:18:00-05:00", "text": "the thug is held still on the stairs"},
                             {"ts": "2026-10-31T21:19:00-05:00", "text": "the lobby clock jumps forward an hour"}])
    r = an(inputs_dir=inp, base_spec=BASE, out_dir=tmp_path / "out", **fixture_inputs(inp))
    held = r["assembly"]["comments"]["held"]
    assert [h["id"] for h in held] == ["c1"] and any(x.startswith("gate:R-JUMPS") for x in held[0]["reasons"])
    assert "held still" not in r["args"]["prompt"] and "lobby clock jumps" in r["args"]["prompt"]


def test_word_budget_carries_tail_comments(an, tmp_path):
    long = " ".join(["the porter hauls the brass luggage trolley up the stairwell past the cracked cabinet"] * 3)
    inp = _inputs(tmp_path, [{"ts": f"2026-10-31T21:1{i}:00-05:00", "text": f"{long} {i}"} for i in range(4)])
    r = an(inputs_dir=inp, base_spec=BASE, out_dir=tmp_path / "out", **fixture_inputs(inp))
    c = r["assembly"]["comments"]
    assert len(r["args"]["prompt"].split()) <= 330 and c["carried"]
    assert len(c["placed"]) + len(c["carried"]) == 4


def test_stale_still_meta_is_not_used(an, tmp_path):
    inp = _inputs(tmp_path, [])
    sm = json.loads((inp / "still_meta.json").read_text()) | {"prev_clip_id": "NP15"}
    (inp / "still_meta.json").write_text(json.dumps(sm))
    r = an(inputs_dir=inp, base_spec=BASE, out_dir=tmp_path / "out", **fixture_inputs(inp))
    assert r["assembly"]["still"]["stale"] == "NP15" and "cracked glass" not in r["args"]["prompt"]


def test_output_inside_repo_but_outside_dryrun_refused(an, v5):
    with pytest.raises(v5("assemble_next").OutputLocationRefused):
        an(inputs_dir=NP17, base_spec=BASE, out_dir=V4 / "prompts_v44" / "odyssey", **fixture_inputs(NP17))


def test_fixed_threads_on_refuses_assembly(an, v5, monkeypatch, tmp_path):
    lm = v5("adapters.locked_meta")
    monkeypatch.setattr(lm.layers_v4, "fixed_threads", lambda: {"threads": [{"id": "FT2", "status": "ON"}]})
    with pytest.raises(lm.FixedThreadsOn):
        an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, **fixture_inputs(NP17))


def test_dryrun_reports_stale_parity_snapshot(v5, assembly_harness):
    assert v5("dryrun").main() == 1
    summary = json.loads((DRYRUN / "night-porter" / "SUMMARY.json").read_text())
    assert summary["parity_NP16_byte_identical"] is False
    assert summary["NP17_changed_slots"] == ["beats"] and summary["NP17_args_changed"] == ["filename", "image_path"]
    assert summary["NP17_gate_fails"] == [] and summary["comments"]["held"] == ["c4"]
    assert NOW in (DRYRUN / "night-porter" / "NP17.assembly.json").read_text()


def test_compilation_never_writes_a_consumption_ledger(an, tmp_path):
    ledger = tmp_path / "consumed.jsonl"
    result = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path / "out",
                consumed_path=ledger, **fixture_inputs(NP17))
    assert result["assembly"]["comments"]["placed"]
    assert not ledger.exists()


def test_parity_mode_does_not_inject_locked_threads_and_thread_slot_is_allowed_in_next(an, tmp_path, monkeypatch, v5):
    spots = paths.config("spots")
    spots["spot_types"]["fight"]["thread_holder"] = "MARLO keeps the jade key"
    lm = v5("adapters.locked_meta")
    real = lm.thread_holder
    monkeypatch.setattr(lm, "thread_holder", lambda st, cfg=None: real(st, cfg or spots))
    parity = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path / "p", advance=False)
    assert parity["diff"]["identical_prompt"]
    inp = _inputs(tmp_path, [])
    nxt = an(inputs_dir=inp, base_spec=BASE, out_dir=tmp_path / "n", **fixture_inputs(inp))
    assert "thread" in nxt["diff"]["changed_slots"] and "thread" not in nxt["diff"]["disallowed_slots"]


def test_base_spec_without_clip_type_is_rejected_at_load(v5, tmp_path):
    spec = json.loads(BASE.read_text())
    del spec["clip_type"]
    p = tmp_path / "bs.json"
    p.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="clip_type"):
        v5("adapters.base_spec").load(p)
