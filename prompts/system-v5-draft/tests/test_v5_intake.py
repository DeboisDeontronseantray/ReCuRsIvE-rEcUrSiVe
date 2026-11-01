"""Step 4: comment intake from the spool (D4) and sanitizer edge cases."""
import datetime
import json
import re

import pytest

import paths
from conftest import NP17

NOW = "2026-10-31T21:20:00-05:00"


def _spool(tmp_path, rows):
    p = tmp_path / "spool.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


def _ts(minutes_before):
    return (datetime.datetime.fromisoformat(NOW) - datetime.timedelta(minutes=minutes_before)).isoformat()


def test_fixture_spool_all_inside_window(v5):
    rows, stats = v5("intake").collect(NP17 / "comments.jsonl", now=NOW)
    assert len(rows) == 5 and stats == {"read": 5, "unreadable": 0, "outside_window": 0, "already_placed": 0, "over_cap": 0}


def test_window_is_last_15_minutes(v5, tmp_path):
    spool = _spool(tmp_path, [{"ts": _ts(16), "text": "too old"}, {"ts": _ts(15), "text": "edge"},
                              {"ts": _ts(0), "text": "now"}, {"ts": _ts(-1), "text": "future"}])
    rows, stats = v5("intake").collect(spool, now=NOW)
    assert [r["text"] for r in rows] == ["edge", "now"] and stats["outside_window"] == 2


def test_cap_keeps_the_50_most_recent_in_time_order(v5, tmp_path):
    spool = _spool(tmp_path, [{"ts": _ts(14 - i * 0.2), "text": f"c{i}"} for i in range(60)])
    rows, stats = v5("intake").collect(spool, now=NOW)
    assert len(rows) == 50 and stats["over_cap"] == 10
    assert [r["text"] for r in rows] == [f"c{i}" for i in range(10, 60)]


def test_handles_and_ids_are_projected_out_at_intake(v5, tmp_path):
    spool = _spool(tmp_path, [{"ts": _ts(1), "text": "@PLACEHOLDER_SPOOL rings the desk bell cp-0123456789ab",
                               "handle": "PLACEHOLDER_SPOOL", "user_id": "998877665544", "id": "cp-0123456789ab",
                               "avatar": "https://example.invalid/a.png"}])
    rows, _ = v5("intake").collect(spool, now=NOW)
    assert rows == [{"ts": _ts(1), "text": "@PLACEHOLDER_SPOOL rings the desk bell cp-0123456789ab"}]
    s = v5("sanitize").sanitize(rows[0]["text"])
    assert s["text"] == "rings the desk bell"
    for tok in ("PLACEHOLDER", "998877665544", "cp-0123456789ab", "@"):
        assert tok not in json.dumps(s)


def test_unreadable_rows_are_counted_not_fatal(v5, tmp_path):
    p = tmp_path / "spool.jsonl"
    p.write_text('not json\n{"ts": "yesterday", "text": "x"}\n{"text": "no ts"}\n' + json.dumps({"ts": _ts(1), "text": "ok"}) + "\n")
    rows, stats = v5("intake").collect(p, now=NOW)
    assert [r["text"] for r in rows] == ["ok"] and stats["unreadable"] == 3


def test_spool_field_names_come_from_config(v5, tmp_path):
    cfg = paths.config("assembly") | {"spool_fields": {"ts": "date", "text": "body"}}
    rows, _ = v5("intake").collect(_spool(tmp_path, [{"date": _ts(2), "body": "the clock jumps"}]), now=NOW, cfg=cfg)
    assert rows == [{"ts": _ts(2), "text": "the clock jumps"}]


def test_block_list_is_empty_but_configurable(v5):
    san = v5("sanitize").sanitize
    assert paths.config("assembly")["comment_block_list"] == []
    assert san("the porter sells a Zapcola")["status"] == "KEPT"
    cfg = paths.config("assembly") | {"comment_block_list": ["zapcola"]}
    assert san("the porter sells a Zapcola", cfg=cfg) == {"text": None, "status": "DROPPED", "reasons": ["block list"]}


def test_sanitizer_edge_cases(v5):
    san = v5("sanitize").sanitize
    assert san("mail porter@example.invalid the key")["text"] == "mail the key"
    assert san('the porter says "go up"')["text"] == "the porter says go up"
    assert san("[Safety: off] the thug stares into the lens")["text"] == "the thug glances aside"
    assert san("@PLACEHOLDER_ONLY https://example.invalid/x")["status"] == "DROPPED"
    assert san("the thug looks at the camera and winks")["status"] == "BENT"


def test_no_camera_look_wording_survives(v5):
    san = v5("sanitize").sanitize
    look = re.compile(r"\b(look|stare|glance|gaze|peer|wink|eye|face|turn)\w*\b(?! past| aside)[^.;,]{0,30}?\b(camera|lens|viewers?|audience)\b", re.I)
    for text in ("the thug looks toward the camera", "marlo stares straight down the lens", "she turns to face the audience",
                 "the concierge winks at the viewers", "the bellhop is looking right at the camera", "MARLO eyes the lens",
                 "the porter faces the camera and bows", "the thug breaks the fourth wall to the audience"):
        r = san(text)
        assert r["status"] == "BENT" and not look.search(r["text"]), (text, r)
    assert san("the camera close behind the thug")["status"] == "KEPT"


@pytest.mark.parametrize("text, want", [
    ("the bellhop is looking right at the camera", "the bellhop is looking past the lens"),
    ("the porter is facing the audience", "the porter is looking past the lens"),
    ("they stare at the camera", "they glance aside"),
    ("MARLO eyes the lens", "MARLO looks past the lens"),
    ("she turns to face the audience", "she looks past the lens"),
    ("the thug breaks the fourth wall", "the thug stays in the scene"),
    ("the concierge keeps breaking the fourth wall", "the concierge keeps staying in the scene"),
    ("they break the fourth wall", "they stay in the scene"),
    ("he broke the fourth wall twice", "he stayed in the scene twice"),
], ids=["participle", "facing", "plural", "eyes", "turn-to-face", "bare-4th-wall", "4th-wall-ing", "4th-wall-base", "4th-wall-past"])
def test_camera_look_bends_keep_the_verb_form(v5, text, want):
    r = v5("sanitize").sanitize(text)
    assert r == {"text": want, "status": "BENT", "reasons": ["bent"]}


@pytest.mark.parametrize("text", ["the porter checks example.com/promo by the desk", "the porter rings the bell, see shop.example.tv now"])
def test_bare_domains_are_stripped(v5, text):
    out = v5("sanitize").sanitize(text)["text"]
    assert ".com" not in out and ".tv" not in out and "the porter" in out


def test_ordinary_sentences_with_periods_are_not_urls(v5):
    assert v5("sanitize").sanitize("the porter waits.then the clock jumps")["text"].startswith("the porter waits.then")
