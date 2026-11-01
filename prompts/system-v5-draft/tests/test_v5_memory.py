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


def test_trait_observations_skip_ad_and_break_items(v5, tmp_path):
    lineage = [{"global_no": g, "clip_id": c} for g, c in ((1116, "NP16"), (1117, "NP17"), (1118, "NP17-AD"), (1119, "NP17-ID"))]
    lineage.append({"global_no": 1120, "clip_id": "NP17-HOUSE", "spot_type": "ad"})
    slots = [{"occupant_global_no": 1116, "kind": "segment"}, {"occupant_global_no": 1117, "kind": "segment"},
             {"occupant_global_no": 1118, "kind": "ad"}, {"occupant_global_no": 1119, "kind": "break"},
             {"occupant_global_no": 9999, "kind": "break"}]
    skip = v5("aired").not_trait_evidence(slots, lineage)
    assert skip == {"NP17-AD", "NP17-ID", "NP17-HOUSE"}

    mem = v5("memory")
    p = tmp_path / "trait_observations.jsonl"
    shutil.copy(CHARMETA / "trait_observations.jsonl", p)
    before = p.read_bytes()
    for cid in sorted(skip):
        assert mem.append_trait_observation(p, ROW | {"clip_id": cid}, skip_clips=skip) is False
    assert p.read_bytes() == before
    assert mem.append_trait_observation(p, ROW, skip_clips=skip) is True
    p.write_text(p.read_text() + json.dumps(ROW | {"clip_id": "NP17-AD"}) + "\n")
    assert [r["clip_id"] for r in mem.read_trait_observations(p, skip_clips=skip)] == ["NP16", "NP17"]
    assert len(mem.read_trait_observations(p)) == 3


def test_one_live_instance_means_one_copy_not_one_person(v5):
    mem = v5("memory")
    cast = {cid: {"name": cid.replace("_", " ")} for cid in ("MARLO_QUILL", "HERON", "WOLFHOUND")}
    spec = {"extra": ["MARLO QUILL faces MARLO QUILL's reflection; HERON and WOLFHOUND wait by the door."], "beats": []}
    assert mem.present_cast({"cast": cast}, spec) == ["MARLO_QUILL", "HERON", "WOLFHOUND"]


def test_proposed_update_raises_level_by_one(v5):
    mem = v5("memory")
    doc = mem.load_channel_meta(CHARMETA, "Ch11 Fist Theater")
    up = mem.proposed_update(doc, ["MARLO_QUILL"])
    assert up == {"file": "11-fist-theater.yaml", "channel": "Ch11 Fist Theater",
                  "cast": {"MARLO_QUILL": {"summon_count": 3, "writein_level": 2}}}
