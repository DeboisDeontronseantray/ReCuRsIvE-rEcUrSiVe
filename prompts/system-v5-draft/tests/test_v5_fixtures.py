"""Fixture checks (active now). They validate the fixture data only; no assembler logic is involved."""
import datetime
import json
import re
import socket

import pytest

import layers_v4
from conftest import FIX, NP17, V4, NetworkBlocked

FORBIDDEN_KEYS = {"handle", "user", "username", "author", "avatar", "image", "img", "images", "media", "url", "contributor", "contributors"}
HANDLE = re.compile(r"(?<![\w.])@[A-Za-z0-9_]+")
URL = re.compile(r"https?://\S+|www\.\S+")


def _all_fixture_files():
    return sorted(p for p in FIX.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl"))


def _load(p):
    if p.suffix == ".jsonl":
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    return json.loads(p.read_text())


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


def test_fixtures_parse():
    files = _all_fixture_files()
    assert len(files) == 5
    for p in files:
        _load(p)


def test_no_handle_or_image_keys_anywhere():
    for p in _all_fixture_files():
        assert not FORBIDDEN_KEYS & set(_keys(_load(p))), p


def test_comment_rows_are_ts_and_text_only():
    rows = _load(NP17 / "comments.jsonl")
    assert len(rows) == 5
    for r in rows:
        assert set(r) == {"ts", "text"}
        datetime.datetime.fromisoformat(r["ts"])


def test_handles_and_urls_are_placeholders_only():
    for p in _all_fixture_files():
        txt = p.read_text()
        handles = HANDLE.findall(txt)
        urls = URL.findall(txt)
        if p.name == "comments.jsonl":
            assert handles and all(h.startswith("@PLACEHOLDER_") for h in handles), handles
            assert urls and all(".invalid/" in u for u in urls), urls
        else:
            assert not handles and not urls, (p, handles, urls)


def test_still_meta_is_stub_flash_and_short():
    s = _load(NP17 / "still_meta.json")
    assert s["analyzer"] == "stub" and s["tier"] == "FLASH" and s["prev_clip_id"] == "NP16"
    assert "/workspace" not in s["still_path"]
    assert all(len(d.split()) <= 12 for d in s["descriptors"])


def test_character_memory_shape():
    m = _load(NP17 / "character_memory" / "MARLO_QUILL.json")
    assert m["name"].replace(" ", "_") + ".json" == "MARLO_QUILL.json"
    assert 0 <= m["writein_level"] <= 3 and m["summon_count"] >= 0
    assert {x["tier"] for x in m["memories"]} <= set(layers_v4.TIER_LIFE)


def test_locked_meta_matches_static_and_has_no_fixed_threads():
    lm = _load(NP17 / "locked_meta.json")
    static = json.loads((V4 / "config" / "static_v41.json").read_text())["shows"][lm["show"]]
    assert lm["channel"] == static["channel"]
    assert lm["world_rules"] == static["intangible"]["world_rules"]
    assert not any(re.match(r"^FT\d", t["id"]) for t in lm["threads"])
    assert all(t["tier"] in ("LEGEND", "MARK") and t["locked"] is True for t in lm["threads"])


def test_live_switches_still_off():
    cimg = json.loads((V4 / "config" / "commenter_images.json").read_text())
    assert cimg["enabled"] is False
    ft = json.loads((V4 / "config" / "fixed_threads.json").read_text())
    assert {t["id"] for t in ft["threads"]} == {"FT1", "FT2", "FT3", "FT4"}
    assert all(t["status"] == "PENDING" for t in ft["threads"])


def test_network_guard_active():
    with pytest.raises(NetworkBlocked):
        socket.create_connection(("example.invalid", 443), timeout=1)
