"""NP16 parity (active now): the reconstructed base spec is "the same spec" the current builder used.

Run against the unchanged live builder and gate; nothing is written."""
import hashlib
import json

import apply_check_v44
import build_prompt_v42
from conftest import NP16, V4

LIVE = V4 / "prompts_v44" / "odyssey"


def _build():
    return build_prompt_v42.build(json.loads((NP16 / "base_spec.json").read_text()), strict=True)


def test_prompt_and_args_byte_identical():
    live = json.loads((LIVE / "NP16.args.json").read_text())
    r = _build()
    assert r["args"] == live
    assert hashlib.sha256(r["args"]["prompt"].encode()).hexdigest() == json.loads((LIVE / "NP16.meta.json").read_text())["prompt_sha256"]


def test_sidecar_identical():
    assert _build()["sidecar"] == json.loads((LIVE / "NP16.meta.json").read_text())


def test_live_gate_baseline_53_pass_5_held():
    fails = []
    for f in sorted((V4 / "prompts_v44").glob("*/*.args.json")):
        a = json.loads(f.read_text())
        rep = apply_check_v44.check(a["prompt"], a, clip_id=f.name[: -len(".args.json")])
        fails += [f.name] if any(v[0] == "FAIL" for v in rep.values()) else []
    assert len(list((V4 / "prompts_v44").glob("*/*.args.json"))) == 53 and fails == []
    assert len(list((V4 / "prompts_v44" / "BLOCKED").glob("*.json"))) == 5


def test_v44_gate_passes():
    r = _build()
    spec = json.loads((NP16 / "base_spec.json").read_text())
    rep = apply_check_v44.check(r["args"]["prompt"], r["args"], spec, r["sidecar"], clip_id="NP16")
    assert [k for k, v in rep.items() if v[0] == "FAIL"] == []
