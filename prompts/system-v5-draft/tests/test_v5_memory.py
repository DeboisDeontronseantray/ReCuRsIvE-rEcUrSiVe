"""Step 6: character-meta loading, presence, add-only trait observations, proposed updates (D5)."""
import json
import shutil

import pytest

from conftest import CHARMETA, NP16

BASE = json.loads((NP16 / "base_spec.json").read_text())
ROW = {"ts": "2026-10-31T21:21:00-05:00", "cast_id": "MARLO_QUILL", "clip_id": "NP17", "trait": "hums on the stairs",
       "tier": "FLASH", "source": "story"}


def test_load_channel_meta_by_channel_name(v5):
    doc = v5("memory").load_channel_meta(CHARMETA, "Ch11 Fist Theater")
    assert list(doc["cast"]) == ["MARLO_QUILL"]
    with pytest.raises(FileNotFoundError):
        v5("memory").load_channel_meta(CHARMETA, "Ch8 Sitcom")


def test_present_cast_is_name_match_only(v5):
    mem = v5("memory")
    doc = mem.load_channel_meta(CHARMETA, "Ch11 Fist Theater")
    assert mem.present_cast(doc, BASE) == ["MARLO_QUILL"]
    assert mem.present_cast(doc, BASE | {"extra": [], "beats": []}) == []


def test_memory_beat_form_is_neutral_insertion(v5):
    mem = v5("memory")
    m = mem.load_channel_meta(CHARMETA, "Ch11 Fist Theater")["cast"]["MARLO_QUILL"]
    assert mem.memory_beats(m, episode=1, season=1, clip_index=17) == ["MARLO QUILL remembers: lost a button in the stairwell fight"]
    assert mem.memory_beats(m | {"writein_level": 0}, episode=1, season=1, clip_index=17) == []


def test_trait_observations_are_add_only(v5, tmp_path):
    mem = v5("memory")
    p = tmp_path / "trait_observations.jsonl"
    shutil.copy(CHARMETA / "trait_observations.jsonl", p)
    before = p.read_bytes()
    mem.append_trait_observation(p, ROW)
    assert p.read_bytes().startswith(before)
    assert mem.read_trait_observations(p)[-1] == ROW
    with pytest.raises(v5("contracts").ContractError):
        mem.append_trait_observation(p, ROW | {"handle": "x"})
    assert len(mem.read_trait_observations(p)) == 2


def test_proposed_update_raises_level_by_one(v5):
    mem = v5("memory")
    doc = mem.load_channel_meta(CHARMETA, "Ch11 Fist Theater")
    up = mem.proposed_update(doc, ["MARLO_QUILL"])
    assert up == {"file": "11-fist-theater.yaml", "channel": "Ch11 Fist Theater",
                  "cast": {"MARLO_QUILL": {"summon_count": 3, "writein_level": 2}}}
