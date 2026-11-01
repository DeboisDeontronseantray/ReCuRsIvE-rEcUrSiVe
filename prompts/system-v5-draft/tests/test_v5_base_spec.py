"""Step 3: the base-spec adapter."""
import json

import pytest

from conftest import NP16, V4

LIVE = V4 / "prompts_v44" / "odyssey"


def test_next_clip_id_keeps_prefix_and_padding(v5):
    bs = v5("adapters.base_spec")
    assert bs.next_clip_id("NP16") == "NP17"
    assert bs.next_clip_id("BI01") == "BI02"
    assert bs.next_clip_id("NP09") == "NP10"
    assert bs.clip_index("NP16") == 16
    with pytest.raises(bs.BaseSpecError):
        bs.next_clip_id("NP-16")


def test_base_spec_is_never_mutated(v5):
    bs = v5("adapters.base_spec")
    before = (NP16 / "base_spec.json").read_bytes()
    spec = bs.load(NP16 / "base_spec.json")
    spec["beats"].clear()
    assert (NP16 / "base_spec.json").read_bytes() == before
    assert bs.load(NP16 / "base_spec.json")["beats"]


def test_parity_through_adapter(v5):
    bs = v5("adapters.base_spec")
    assert bs.verify_parity(bs.load(NP16 / "base_spec.json"), LIVE / "NP16.args.json", LIVE / "NP16.meta.json")


def test_missing_required_key_rejected(v5, tmp_path):
    bs = v5("adapters.base_spec")
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"clip_id": "NP16"}))
    with pytest.raises(bs.BaseSpecError):
        bs.load(p)
