import re, subprocess, sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker, legacy_names as ln

L = ln.LEGACY_OWNER
REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("old, new", [
    (f"{L}s-videos", "trundles-videos"),
    (f"{L}-project-status.json", "trundle-project-status.json"),
    (f"{L}-rules-20261027-1404", "trundle-rules-20261027-1404"),
    (f"{L}_notes_20261027", "trundle_notes_20261027"),
    (f"approved_by_{L}", "approved_by_trundle"),
    (f"no_{L}_name_20261027_1744", "no_trundle_name_20261027_1744"),
    (f"HELD_FOR_{L.upper()}", "HELD_FOR_trundle"),
    (f"PENDING {L.upper()} APPROVAL - not sent to CNB", "PENDING trundle APPROVAL - not sent to CNB"),
    (f"DRAFT-pending-{L.capitalize()}", "DRAFT-pending-trundle"),
], ids=["videos-dir", "status-file", "rule-id", "notes-key", "approved-by", "rule-key", "held", "pending", "draft"])
def test_legacy_spellings_map_to_trundle_form(old, new):
    assert ln.canonical(old) == new and ln.same(old, new) and ln.canonical(new) == new


def test_canonical_leaves_other_words_alone():
    for w in ("withdrew", f"An{L}", "thunder trundle", "thunder-trundle", "Trundle"):
        assert ln.canonical(w) == w


def test_get_reads_legacy_keys_and_prefers_trundle_form():
    old = {f"{L}_notes_20261027": "old note", f"{L}_adds": ["lamp"]}
    assert ln.get(old, "trundle_notes_20261027") == "old note" and ln.get(old, "trundle_adds") == ["lamp"]
    both = {f"{L}_notes_20261027": "old", "trundle_notes_20261027": "new"}
    assert ln.get(both, "trundle_notes_20261027") == "new"
    assert ln.get({}, "trundle_notes_20261027", "none") == "none"


def test_resolve_path_finds_the_legacy_folder_and_file(tmp_path):
    (tmp_path / "media_server" / f"{L}s-videos").mkdir(parents=True)
    clip = tmp_path / "media_server" / f"{L}s-videos" / "clip.mp4"
    clip.write_text("x")
    (tmp_path / f"{L}-project-status.json").write_text("{}")
    assert ln.resolve_path(tmp_path / "media_server" / "trundles-videos" / "clip.mp4") == clip
    assert ln.resolve_path(tmp_path / "trundle-project-status.json") == tmp_path / f"{L}-project-status.json"


def test_resolve_path_prefers_the_trundle_form_and_returns_missing_paths_as_given(tmp_path):
    (tmp_path / f"{L}s-videos").mkdir()
    (tmp_path / "trundles-videos").mkdir()
    assert ln.resolve_path(tmp_path / "trundles-videos") == tmp_path / "trundles-videos"
    assert ln.resolve_path(tmp_path / "nope" / "trundles-videos") == tmp_path / "nope" / "trundles-videos"


@pytest.mark.parametrize("by", ["trundle", L.capitalize()], ids=["trundle", "legacy"])
def test_withdraw_accepts_trundle_and_the_legacy_caller(by):
    rows = checker.set_state([], "cp-a", "WITHDRAWN", by=by)
    assert rows[-1]["state"] == "WITHDRAWN" and rows[-1]["by"] == by


@pytest.mark.parametrize("by", ["bot", None, "Trundle", L.upper()], ids=["bot", "missing", "capitalized", "legacy-upper"])
def test_withdraw_still_refuses_everyone_else(by):
    with pytest.raises(AssertionError):
        checker.set_state([], "cp-a", "WITHDRAWN", by=by)


def test_hard_limits_ban_the_real_name_not_the_network():
    hl = yaml.safe_load((REPO / "story-engine/rules/hard-limits.yaml").read_text())
    assert ln.never_on_screen(hl) == [L] and "trundle" not in ln.never_on_screen(hl)
    assert ln.never_on_screen({"never_on_screen_or_spoken": [L.capitalize()]}) == [L.capitalize()]
    assert hl["address_user_as"] == ["trundle", "thundertrundle"]


def test_no_config_or_brief_bans_the_trundle_name():
    for p in (REPO / "story-engine").rglob("*"):
        if p.suffix in (".yaml", ".md", ".json") and p.is_file():
            t = p.read_text(encoding="utf-8")
            assert not re.search(r"""(no|never(?: write)?|reading)\s+["']trundle["']|\[\s*["']trundle["']\s*\]""", t, re.I), p


def test_block_list_still_uses_the_same_decoded_name():
    assert checker.CREATOR_NAME == L and checker.CREATOR.search(f"hi {L.capitalize()}")


def test_no_literal_name_in_tracked_story_engine_files():
    files = subprocess.run(["git", "-C", str(REPO), "grep", "-l", "-I", "-i", L, "--", "story-engine"],
                           capture_output=True, text=True).stdout.split()
    hits = [f for f in files if re.search(rf"(?<![A-Za-z]){L}", (REPO / f).read_text(encoding="utf-8"), re.I)]
    assert hits == []
