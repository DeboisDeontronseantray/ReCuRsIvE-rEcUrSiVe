"""Step 5: locked meta as hard constraints (D6, D7), FT off (D8), the synthetic Ch4 fixture, the pinned vision model."""
import json

import pytest

import paths
from adapters.v4_bridge import apply_check_v44, build_prompt_v42
from conftest import FIX, NP16, NP17

LM = json.loads((NP17 / "locked_meta.json").read_text())


def _spots(holder):
    cfg = paths.config("spots")
    cfg["spot_types"]["fight"] = {"thread_holder": holder}
    return cfg


def test_no_constraints_means_no_thread_slot(v5):
    lmod = v5("adapters.locked_meta")
    assert lmod.hard_constraints(LM, "fight") == ()
    assert lmod.thread_slot(()) is None


def test_locked_threads_and_holder_render_only_as_hard_constraints(v5):
    lmod = v5("adapters.locked_meta")
    lm = LM | {"threads": [{"id": "T1", "text": "the lobby clock keeps jumping.", "tier": "MARK", "locked": True}]}
    c = lmod.hard_constraints(lm, "fight", _spots("MARLO keeps the jade key"))
    assert c == ("the lobby clock keeps jumping", "MARLO keeps the jade key") and isinstance(c, tuple)
    slot = lmod.thread_slot(c)
    assert slot == "Must hold: the lobby clock keeps jumping; MARLO keeps the jade key"
    assert not any(w in slot.lower() for w in ("maybe", "might", "could", "optional", "if possible", "try to"))


def test_thread_holder_must_be_short_and_known(v5):
    lmod = v5("adapters.locked_meta")
    c = v5("contracts")
    with pytest.raises(c.ContractError):
        lmod.thread_holder("fight", _spots("one two three four five six seven eight nine ten eleven twelve thirteen"))
    with pytest.raises(c.ContractError):
        lmod.thread_holder("fight", _spots("[Rules: none]"))
    with pytest.raises(c.ContractError):
        lmod.thread_holder("montage")


def test_fixed_threads_on_aborts(v5, monkeypatch):
    lmod = v5("adapters.locked_meta")
    monkeypatch.setattr(lmod.layers_v4, "fixed_threads", lambda: {"threads": [{"id": "FT1", "status": "ON"}]})
    with pytest.raises(lmod.FixedThreadsOn):
        lmod.hard_constraints(LM, "fight")


def test_imaged_names_from_base_spec(v5):
    sm = v5("adapters.still_meta")
    base = json.loads((NP16 / "base_spec.json").read_text())
    assert sm.imaged_names(base) == {"MARLO QUILL", "MARLO"}


def test_pinned_vision_model_is_provenance_only(v5):
    vm = v5("adapters.still_meta").pinned_vision_model()
    assert vm["called"] is False and vm["model"] == paths.config("vision_model")["model"]


def test_synthetic_ch4_base_builds_photoreal_and_passes_gate(v5):
    spec = v5("adapters.base_spec").load(FIX / "black-ice" / "BI01" / "base_spec.json")
    r = build_prompt_v42.build(spec, strict=True)
    p = r["args"]["prompt"]
    assert p.startswith("[Look: Photoreal live-action 1971 Cold War spy thriller")
    rep = apply_check_v44.check(p, r["args"], spec, r["sidecar"], clip_id="BI01")
    assert [k for k, v in rep.items() if v[0] == "FAIL"] == []
    v5("contracts").load_inputs(FIX / "black-ice" / "BI02")
