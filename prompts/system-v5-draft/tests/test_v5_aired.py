"""Aired flag: only aired clips are canon (playout slot `status: AIRED` + `aired_at`, joined to LINEAGE `clip_id`)."""
import hashlib
import json
import shutil

import pytest
import yaml

import contracts
import paths
from conftest import CHARMETA, LEDGER, NP16, NP17, REPO, fixture_inputs

BASE = NP16 / "base_spec.json"
SLOTS = LEDGER / "slots.jsonl"
LINEAGE = LEDGER / "lineage.jsonl"


@pytest.fixture
def aired(v5):
    return v5("aired")


@pytest.fixture
def an(v5, assembly_harness):
    return v5("assemble_next").assemble_next


def _rows(p):
    return contracts.read_jsonl(p)


def _slot(g, **kw):
    return {"slot_id": f"s{g}", "occupant_global_no": g, "status": "AIRED", "aired_at": "2026-10-31T20:00:00-05:00"} | kw


def _lin(g, cid):
    return {"global_no": g, "clip_id": cid}


def test_fixture_ledger_covers_aired_unaired_and_missing(aired):
    idx = aired.load(SLOTS, LINEAGE)
    assert idx == {}  # slot booleans never establish canonical air
    by_clip = {r["clip_id"]: r["global_no"] for r in _rows(LINEAGE)}
    status = {r["occupant_global_no"]: r.get("status") for r in _rows(SLOTS)}
    assert status[by_clip["NP14"]] == "READY"
    assert status[by_clip["NP13"]] is None


@pytest.mark.parametrize("slot", [
    _slot(1, status="READY"),
    _slot(1, status="APPROVED"),
    _slot(1, status="aired"),
    {k: v for k, v in _slot(1).items() if k != "status"},
    _slot(1, aired_at=None),
    {k: v for k, v in _slot(1).items() if k != "aired_at"},
    _slot(1, aired_at="not a time"),
    _slot(True),
], ids=["ready", "approved", "lowercase", "missing-status", "null-aired_at", "missing-aired_at", "bad-aired_at", "bool-occupant"])
def test_anything_but_status_AIRED_with_aired_at_is_unaired(aired, slot):
    assert aired.build_index([slot], [_lin(1, "NP16")]) == {}


def test_other_aired_conventions_are_not_read(aired):
    lineage = [_lin(1, "NP16") | {"aired": True, "air_yes": True, "status": "AIRED", "air_status": "aired"}]
    assert aired.build_index([_slot(1, status="READY")], lineage) == {}


def test_aired_slot_without_lineage_join_is_unaired(aired):
    assert aired.build_index([_slot(7)], [_lin(1, "NP16")]) == {}


def test_aired_never_reverts_in_an_add_only_slot_log(aired):
    log = [_slot(1), _slot(2, slot_id="s1", status="RESERVED", aired_at=None)]
    assert list(aired.build_index(log, [_lin(1, "NP16"), _lin(2, "NP17")])) == []


def test_lineage_global_no_naming_two_clips_is_refused(aired):
    with pytest.raises(contracts.ContractError):
        aired.build_index([], [_lin(1, "NP16"), _lin(1, "NP15")])


def test_canon_memories_drop_unaired_and_sourceless(aired):
    cm = {"memories": [{"text": "a", "tier": "MARK", "since_index": 9, "clip_id": "NP09"},
                       {"text": "b", "tier": "MARK", "since_index": 14, "clip_id": "NP14"},
                       {"text": "c", "tier": "MARK", "since_index": 15}]}
    canon, dropped = aired.canon_memories(cm, aired.load(SLOTS, LINEAGE))
    assert canon["memories"] == []
    assert dropped == [{"clip_id": "NP09", "since_index": 9, "reason": "not aired"},
                       {"clip_id": "NP14", "since_index": 14, "reason": "not aired"},
                       {"clip_id": None, "since_index": 15, "reason": "no source clip"}]
    assert len(cm["memories"]) == 3


def test_memory_clip_id_must_be_a_clip_id():
    with pytest.raises(contracts.ContractError):
        contracts.validate_memory_item({"text": "x", "tier": "MARK", "since_index": 1, "clip_id": "ch11-q06"})


def test_aired_previous_clip_is_recorded(an, tmp_path):
    r = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, **fixture_inputs(NP17))
    a = r["assembly"]["aired"]
    assert a["prev"]["clip_id"] == "NP16" and a["prev"]["global_no"] == 1116
    assert a["prev"]["aired_at"]
    assert a["slots"]["file"] == "slots.jsonl" and a["lineage"]["file"] == "lineage.jsonl"
    assert {(u["clip_id"], u["reason"]) for u in r["assembly"]["memory"]["unaired"]} == {("NP14", "not aired"), ("NP13", "not aired")}
    assert json.loads((tmp_path / "NP17.assembly.json").read_text())["aired"] == a


@pytest.mark.parametrize("slots", ["slots.NP16-unaired.jsonl", "slots.NP16-missing.jsonl"])
def test_legacy_slot_snapshot_cannot_revoke_verified_air(an, aired, tmp_path, slots):
    out = tmp_path / "out"
    result = an(inputs_dir=NP17, base_spec=BASE, out_dir=out,
                **fixture_inputs(NP17) | {"slots_path": LEDGER / slots})
    assert result["assembly"]["aired"]["prev"]["clip_id"] == "NP16"


def test_ledger_paths_are_never_guessed(an, tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "LOCAL_CONFIG", REPO / "nonexistent.json")
    for key in ("TT_SLOTS", "TT_LINEAGE"):
        monkeypatch.delenv(key, raising=False)
    kw = {k: v for k, v in fixture_inputs(NP17).items() if k not in ("slots_path", "lineage_path")}
    with pytest.raises(paths.PathNotConfigured, match="TT_SLOTS"):
        an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, **kw)


def test_parity_mode_needs_no_ledger(an, tmp_path, monkeypatch):
    for key in ("TT_SLOTS", "TT_LINEAGE"):
        monkeypatch.delenv(key, raising=False)
    r = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, advance=False)
    assert r["assembly"]["aired"] is None and r["diff"]["identical_prompt"]


def test_only_aired_memories_reach_the_prompt(an, tmp_path):
    doc = yaml.safe_load((CHARMETA / "11-fist-theater.yaml").read_text())
    doc["cast"]["MARLO_QUILL"]["memories"] = [
        {"text": "owes THE CONCIERGE a favour", "tier": "MARK", "since_index": 9, "season": 1, "clip_id": "NP09"},
        {"text": "hid the night ledger under the rug", "tier": "MARK", "since_index": 14, "season": 1, "clip_id": "NP14"},
        {"text": "promised the bellhop a day off", "tier": "MARK", "since_index": 15, "season": 1, "clip_id": "NP13"},
        {"text": "found a jade key in the lift", "tier": "MARK", "since_index": 16, "season": 1},
    ]
    cdir = tmp_path / "cm"
    shutil.copytree(CHARMETA, cdir)
    (cdir / "11-fist-theater.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    r = an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path / "out", **fixture_inputs(NP17) | {"character_meta_dir": cdir})
    p = r["args"]["prompt"]
    assert "MARLO QUILL remembers: owes THE CONCIERGE a favour" not in p  # unregistered consequence
    for text in ("night ledger", "bellhop a day off", "jade key"):
        assert text not in p
    assert [(u["clip_id"], u["reason"]) for u in r["assembly"]["memory"]["unaired"]] == [
        ("NP14", "not aired"), ("NP13", "not aired"), (None, "no source clip")]


def test_ledger_files_are_read_only(an, tmp_path):
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in LEDGER.iterdir()}
    an(inputs_dir=NP17, base_spec=BASE, out_dir=tmp_path, **fixture_inputs(NP17))
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in LEDGER.iterdir()} == before
