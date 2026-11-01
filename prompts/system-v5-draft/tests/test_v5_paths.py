"""Step 1: path resolution, pinned configs, and read-only bridges."""
import json
import re

import pytest

import paths
from conftest import REPO, V4, V5


def test_env_beats_local_config_beats_default(tmp_path, monkeypatch):
    local = tmp_path / "tt_paths.json"
    monkeypatch.setattr(paths, "LOCAL_CONFIG", local)
    monkeypatch.delenv("TT_CLIPS", raising=False)
    assert paths.get("TT_CLIPS") is None
    local.write_text(json.dumps({"TT_CLIPS": str(tmp_path / "from_file")}))
    assert paths.get("TT_CLIPS") == tmp_path / "from_file"
    monkeypatch.setenv("TT_CLIPS", str(tmp_path / "from_env"))
    assert paths.get("TT_CLIPS") == tmp_path / "from_env"


def test_repo_defaults_point_into_this_repo(monkeypatch):
    monkeypatch.delenv("TT_PROMPTS_V4", raising=False)
    monkeypatch.setattr(paths, "LOCAL_CONFIG", REPO / "nonexistent.json")
    assert paths.get("TT_PROMPTS_V4") == V4


def test_live_paths_are_never_guessed(monkeypatch):
    monkeypatch.setattr(paths, "LOCAL_CONFIG", REPO / "nonexistent.json")
    for key in ("TT_COMMENT_SPOOL", "TT_CHARACTER_META"):
        monkeypatch.delenv(key, raising=False)
        with pytest.raises(paths.PathNotConfigured):
            paths.get(key, required=True)


def test_unknown_key_rejected():
    with pytest.raises(KeyError):
        paths.get("TT_ANYTHING")


def test_no_workspace_literal_in_v5_code():
    for p in V5.rglob("*.py"):
        if "tests" in p.relative_to(V5).parts:
            continue
        assert "/workspace" not in p.read_text(), p


def test_bridges_expose_only_pure_symbols(v5):
    se = v5("adapters.story_engine_bridge")
    assert set(se.__all__) == {"NEVER_WORDS", "PROTECTED", "HARD", "bend"}
    assert not hasattr(se, "cats")
    v4 = v5("adapters.v4_bridge")
    assert callable(v4.build_prompt_v42.build) and callable(v4.apply_check_v44.check)


def test_vision_model_pinned_in_config_not_code():
    vm = paths.config("vision_model")
    assert vm["provider"] == "xAI" and vm["model"].startswith("grok-") and vm["called"] is False
    assert vm["source"].startswith("https://docs.x.ai/") and vm["looked_up_utc"].startswith("2026-11-01")
    for p in V5.rglob("*.py"):
        if "tests" not in p.relative_to(V5).parts:
            assert vm["model"] not in p.read_text(), p


def test_assembly_config_matches_d4_d5():
    a = paths.config("assembly")
    assert a["comment_window_minutes"] == 15 and a["comment_cap"] == 50 and a["comment_block_list"] == []
    assert a["writein_cap"] == {"0": 0, "1": 1, "2": 1, "3": 2} and a["writein_max"] == 3


def test_spots_have_short_or_unset_thread_holders():
    s = paths.config("spots")
    for spot in s["spot_types"].values():
        assert set(spot) == {"thread_holder"}
        th = spot["thread_holder"]
        assert th is None or (len(th.split()) <= s["thread_holder_max_words"] and not re.search(r"[\[\]@]", th))
