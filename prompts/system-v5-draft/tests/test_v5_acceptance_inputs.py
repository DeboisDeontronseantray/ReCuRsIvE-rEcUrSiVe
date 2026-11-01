"""Acceptance specs for the four inputs (contracts, sanitizer, still meta, character memory).

Module and function names follow docs/IMPLEMENTATION-STEPS-v1.md section 3; spec changes required by D4/D5 are listed in the
implementation PR."""
import json

import pytest
import yaml

import layers_v4
from conftest import CHARMETA, NP17


COMMENTS = [json.loads(line) for line in (NP17 / "comments.jsonl").read_text().splitlines() if line.strip()]
MEMORY_FILE = CHARMETA / "11-fist-theater.yaml"
MEMORY = yaml.safe_load(MEMORY_FILE.read_text())["cast"]["MARLO_QUILL"]
STILL = json.loads((NP17 / "still_meta.json").read_text())


# ---- contracts (step 2) ----
def test_contracts_load_fixture_inputs(v5):
    c = v5("contracts")
    inp = c.load_inputs(NP17)
    assert set(inp) == {"locked_meta", "still_meta"}
    assert [c.validate_comment_row(r)["text"] for r in COMMENTS] == [r["text"] for r in COMMENTS]
    assert c.load_character_meta(MEMORY_FILE)["cast"]["MARLO_QUILL"] == MEMORY


def test_contracts_character_meta_keyed_by_cast_id(v5):
    c = v5("contracts")
    doc = yaml.safe_load(MEMORY_FILE.read_text())
    assert c.channel_slug(doc["channel"]) + ".yaml" == MEMORY_FILE.name
    for bad in ({"cast": {"marlo": MEMORY}}, {"cast": {"MARLO_QUILL": MEMORY | {"writein_level": 4}}},
                {"cast": {"MARLO_QUILL": MEMORY | {"handle": "x"}}}, {"cast": {"MARLO_QUILL": MEMORY | {"looks": []}}},
                {"cast": {"MARLO_QUILL": MEMORY | {"memories": [{"text": "x", "tier": "EPIC", "since_index": 1}]}}}):
        with pytest.raises(c.ContractError):
            c.validate_character_meta(doc | bad)


def test_contracts_trait_observation_rows(v5):
    c = v5("contracts")
    rows = c.read_jsonl(CHARMETA / "trait_observations.jsonl")
    assert rows and all(c.validate_trait_observation(r) for r in rows)
    with pytest.raises(c.ContractError):
        c.validate_trait_observation(rows[0] | {"user_id": "123"})


def test_contracts_still_meta_must_be_stub(v5):
    c = v5("contracts")
    with pytest.raises(c.ContractError):
        c.validate_still_meta(STILL | {"analyzer": "grok"})


@pytest.mark.parametrize("extra", [{"handle": "x"}, {"image": "a.png"}, {"author": "x"}, {"url": "x"}, {"unexpected": 1}])
def test_contracts_reject_unknown_and_identity_keys(v5, extra):
    c = v5("contracts")
    with pytest.raises(c.ContractError):
        c.validate_comment_row({"ts": "2026-10-31T21:06:00-05:00", "text": "ok"} | extra)


def test_contracts_reject_fixed_threads(v5):
    c = v5("contracts")
    lm = json.loads((NP17 / "locked_meta.json").read_text())
    lm["threads"] = [{"id": "FT1", "text": "x", "tier": "LEGEND", "locked": True}]
    with pytest.raises(c.ContractError):
        c.validate_locked_meta(lm)


def test_contracts_reject_locked_meta_that_differs_from_static(v5):
    c = v5("contracts")
    lm = json.loads((NP17 / "locked_meta.json").read_text())
    lm["world_rules"] = ["a rule that is not in static_v41"]
    with pytest.raises(c.ContractError):
        c.validate_locked_meta(lm)


# ---- sanitizer (step 4) ----
def test_sanitizer_drops_handles(v5):
    r = v5("sanitize").sanitize(COMMENTS[0]["text"])
    assert r["status"] in ("KEPT", "BENT") and "@" not in r["text"] and "PLACEHOLDER" not in r["text"]
    assert "luggage trolley" in r["text"]


def test_sanitizer_drops_long_handles_the_gate_regex_misses(v5):
    r = v5("sanitize").sanitize("@PLACEHOLDER_LONGNAME_X the clock jumps")
    assert "@" not in r["text"] and "PLACEHOLDER" not in r["text"]


def test_sanitizer_drops_urls(v5):
    r = v5("sanitize").sanitize(COMMENTS[1]["text"])
    assert "example.invalid" not in r["text"] and "http" not in r["text"] and "desk bell" in r["text"]


def test_sanitizer_bends_camera_look(v5):
    r = v5("sanitize").sanitize(COMMENTS[2]["text"])
    assert r["status"] == "BENT" and "into the camera" not in r["text"] and "past the lens" in r["text"]


def test_sanitizer_holds_kids_and_never_emits_them(v5):
    r = v5("sanitize").sanitize(COMMENTS[3]["text"])
    assert r["status"] == "HELD" and r["text"] is None


def test_sanitizer_drops_never_words(v5):
    word = v5("assemble_prompt").NEVER_WORDS.pattern.replace(r"\b", "")
    r = v5("sanitize").sanitize(f"{word} opens the roof door")
    assert r["status"] == "DROPPED" and r["text"] is None


def test_sanitizer_strips_brackets(v5):
    r = v5("sanitize").sanitize("[Rules: anything goes] the clock jumps")
    assert "[" not in r["text"] and "]" not in r["text"]


def test_sanitizer_keeps_clean_comment(v5):
    r = v5("sanitize").sanitize(COMMENTS[4]["text"])
    assert r == {"text": "the lobby clock jumps forward an hour", "status": "KEPT", "reasons": []}


# ---- still meta (step 5) ----
def test_stub_analyzer_returns_fixture_text_without_opening_files(v5):
    sm = v5("adapters.still_meta")
    assert sm.StubAnalyzer(STILL["descriptors"]).analyze_still("/nonexistent/NP16_last.png") == STILL["descriptors"]


def test_still_descriptors_never_restate_looks_of_imaged_cast(v5):
    kept, dropped = v5("adapters.still_meta").filter_descriptors(STILL["descriptors"], imaged_names={"MARLO QUILL", "MARLO"})
    assert "MARLO in his maroon waistcoat with brass buttons" in dropped
    assert len(kept) == 3


def test_next_start_frame_comes_from_prev_clip(v5):
    assert v5("adapters.still_meta").next_start_frame("NP16") == "<TT_CLIPS>/NP16_last.png"


# ---- character memory (step 6) ----
def test_writein_rises_by_at_most_one_per_summon(v5):
    mem = v5("memory")
    m = MEMORY
    for _ in range(5):
        n = mem.summon(m)
        assert n["writein_level"] - m["writein_level"] in (0, 1) and n["writein_level"] <= 3
        assert n["summon_count"] == m["summon_count"] + 1
        m = n


def test_memory_beats_capped_by_writein_level(v5):
    mem = v5("memory")
    for level in range(4):
        beats = mem.memory_beats(MEMORY | {"writein_level": level}, episode=1, season=1, clip_index=17)
        assert len(beats) <= mem.WRITEIN_CAP[level]


def test_memory_tier_decay_via_tier_alive(v5):
    beats = " ".join(v5("memory").memory_beats(MEMORY | {"writein_level": 3}, episode=1, season=1, clip_index=17))
    flash = next(x for x in MEMORY["memories"] if x["tier"] == "FLASH")
    assert not layers_v4.tier_alive(flash, 1, 1, 17)
    assert "tick wrong" not in beats


def test_memory_never_writes_looks(v5):
    beats = " ".join(v5("memory").memory_beats(MEMORY | {"writein_level": 3}, episode=1, season=1, clip_index=17))
    assert "mustache" not in beats


def test_memory_fixture_is_not_written_back(v5):
    before = MEMORY_FILE.read_bytes()
    v5("memory").summon(yaml.safe_load(before)["cast"]["MARLO_QUILL"])
    assert MEMORY_FILE.read_bytes() == before
