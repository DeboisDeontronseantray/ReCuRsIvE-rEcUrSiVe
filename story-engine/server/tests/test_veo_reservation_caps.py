"""Veo cost reservation + caps settings file (2026-11-02, trundle 9:11 PM CT go). All transports mocked."""
import base64
import json
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

from app import clip_render as clips
from app import spend

KEY = "fake-vertex-key-never-print"


@pytest.fixture(autouse=True)
def no_network(monkeypatch, tmp_path):
    urlopen = Mock(side_effect=AssertionError("real network forbidden"))
    monkeypatch.setattr(clips.urllib.request, "urlopen", urlopen)
    monkeypatch.setenv("GCP_VERTEX_API_KEY", KEY)
    monkeypatch.setenv("XAI_API_KEY", KEY)
    monkeypatch.setenv("XAI_KEY_FILE", str(tmp_path / "missing-key"))
    monkeypatch.setenv("TT_CLIP_LEDGER", str(tmp_path / "ledger.jsonl"))
    monkeypatch.setenv("TT_CAPS_FILE", str(tmp_path / "caps.json"))
    (tmp_path / "ledger.jsonl").write_text("")
    monkeypatch.setattr(spend, "month_total_for_gate", lambda: (0, "test"))
    yield
    urlopen.assert_not_called()


def write_caps(tmp_path, **over):
    data = {"version": 1, "xai_month_cap_usd": 50, "xai_month_warn_usd": 40,
            "veo_trial_cap_usd": 150, "veo_trial_warn_usd": 120, "veo_trial_end": "2027-01-04", "sources": {}}
    data.update(over)
    (tmp_path / "caps.json").write_text(json.dumps(data))


def rows(tmp_path):
    return [json.loads(l) for l in (tmp_path / "ledger.jsonl").read_text().splitlines() if l.strip()]


def add(tmp_path, cost, status, rid=None):
    row = {"provider": "vertex_veo", "cost_usd": cost, "status": status}
    if rid:
        row["reservation_id"] = rid
    with open(tmp_path / "ledger.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")


def request(tmp_path, name="clip.mp4", **kw):
    return clips.ClipRequest("A foggy outpost", out_path=str(tmp_path / name), **kw)


def ok_responses():
    return [(200, json.dumps({"name": "operations/op1"})),
            (200, json.dumps({"done": True, "response": {"videos": [{"bytesBase64Encoded": base64.b64encode(b"mp4").decode()}]}}))]


def test_reserved_row_is_written_before_submit(tmp_path):
    seen = []

    def transport(method, url, body):
        if ":predictLongRunning" in url:
            seen.extend(rows(tmp_path))
        return ok_responses()[0 if ":predictLongRunning" in url else 1]

    clips.render(request(tmp_path), approval="trundle yes $0.64", transport=transport, sleep=lambda _: None)
    assert [r["status"] for r in seen] == ["reserved"] and seen[0]["cost_usd"] == 0.64
    assert [r["status"] for r in rows(tmp_path)] == ["reserved", "success"]
    assert clips.veo_trial_spent(tmp_path / "ledger.jsonl") == 0.64  # not double counted
    assert (tmp_path / "ledger.jsonl.lock").exists()


def test_reserved_and_possible_charge_count_toward_cap(tmp_path):
    add(tmp_path, 100.0, "possible_charge", "a")
    add(tmp_path, 49.5, "reserved", "b")  # an unfinished render still holds its amount
    status = clips.veo_trial_status(0.64, tmp_path / "ledger.jsonl")
    assert status["spent_usd"] == 149.5 and status["status"] == "blocked"
    assert status["reserved_usd"] == 49.5 and status["possible_charge_usd"] == 100.0
    fake = Mock()
    with pytest.raises(clips.VeoTrialCapError, match="would cross"):
        clips.render(request(tmp_path), approval="trundle yes $0.64", transport=fake)
    fake.assert_not_called()


def test_last_row_per_reservation_wins(tmp_path):
    add(tmp_path, 0.64, "reserved", "r1")
    add(tmp_path, 0, "failed", "r1")
    add(tmp_path, 0.64, "reserved", "r2")
    add(tmp_path, 0.64, "success", "r2")
    add(tmp_path, 1.0, "success")  # legacy row, no reservation_id
    assert clips.veo_trial_spent(tmp_path / "ledger.jsonl") == 1.64


def test_concurrent_renders_cannot_both_take_the_last_room(tmp_path):
    write_caps(tmp_path, veo_trial_cap_usd=1.0, veo_trial_warn_usd=0.9)
    release = threading.Event()
    in_flight = threading.Event()

    def slow(method, url, body):
        if ":predictLongRunning" in url:
            in_flight.set()
            release.wait(5)
        return ok_responses()[0 if ":predictLongRunning" in url else 1]

    errors = []
    first = threading.Thread(target=lambda: clips.render(request(tmp_path, "a.mp4"), approval="trundle yes $0.64",
                                                         transport=slow, sleep=lambda _: None))
    first.start()
    assert in_flight.wait(5)
    try:
        clips.render(request(tmp_path, "b.mp4"), approval="trundle yes $0.64", transport=Mock())
    except clips.VeoTrialCapError as exc:
        errors.append(str(exc))
    release.set()
    first.join(5)
    assert errors and "cap $1.00" in errors[0]
    assert [r["status"] for r in rows(tmp_path)] == ["reserved", "success"]


def test_failed_submit_keeps_possible_charge_and_blocks_next(tmp_path):
    write_caps(tmp_path, veo_trial_cap_usd=1.0, veo_trial_warn_usd=0.9)
    with pytest.raises(clips.ClipRenderError):
        clips.render(request(tmp_path), approval="trundle yes $0.64",
                     transport=Mock(side_effect=[(200, '{"name":"operations/op"}'), (503, "{}")]), sleep=lambda _: None)
    assert rows(tmp_path)[-1]["status"] == "possible_charge"
    with pytest.raises(clips.VeoTrialCapError):
        clips.render(request(tmp_path, "c.mp4"), approval="trundle yes $0.64", transport=Mock())


def test_caps_file_drives_veo_cap_trial_end_and_xai_cap(tmp_path, monkeypatch):
    write_caps(tmp_path, veo_trial_cap_usd=0.5, veo_trial_warn_usd=0.4, veo_trial_end="2026-01-01")
    caps = clips.load_caps()
    assert caps["veo_trial_cap_usd"] == 0.5 and caps["source"] == str(tmp_path / "caps.json")
    with pytest.raises(clips.VeoTrialCapError, match="Veo trial ended 2026-01-01"):
        clips.render(request(tmp_path), approval="trundle yes $0.64", transport=Mock())
    write_caps(tmp_path, veo_trial_cap_usd=0.5, veo_trial_warn_usd=0.4)
    with pytest.raises(clips.VeoTrialCapError, match=r"cap \$0.50"):
        clips.render(request(tmp_path), approval="trundle yes $0.64", transport=Mock())
    write_caps(tmp_path, xai_month_cap_usd=0.5, xai_month_warn_usd=0.4)
    monkeypatch.setattr(spend, "check_can_spend", Mock())
    with pytest.raises(spend.SpendLimitError, match=r"monthly \$0.5 cap"):
        clips.render(request(tmp_path, provider="xai"), approval="trundle yes $0.64", transport=Mock())


@pytest.mark.parametrize("content,source", [(None, "missing"), ("{bad", "unreadable"),
                                            (json.dumps({"version": 1}), "invalid"),
                                            (json.dumps({"version": 1, "xai_month_cap_usd": 50, "xai_month_warn_usd": 40,
                                                         "veo_trial_cap_usd": -1, "veo_trial_warn_usd": 0,
                                                         "veo_trial_end": "2027-01-04"}), "invalid")])
def test_missing_or_invalid_caps_file_falls_back_to_todays_values(tmp_path, content, source):
    if content is not None:
        (tmp_path / "caps.json").write_text(content)
    caps = clips.load_caps()
    assert caps["source"] == f"fallback (caps file {source})"
    assert (caps["xai_month_cap_usd"], caps["xai_month_warn_usd"], caps["veo_trial_cap_usd"],
            caps["veo_trial_warn_usd"], caps["veo_trial_end"]) == (50, 40, 150, 120, "2027-01-04")


def test_plan_reports_caps_source_and_reservations(tmp_path):
    write_caps(tmp_path)
    add(tmp_path, 2.0, "reserved", "x")
    cap = clips.plan(request(tmp_path))["veo_trial_cap"]
    assert cap["reserved_usd"] == 2.0 and cap["caps_source"] == str(tmp_path / "caps.json")


def test_reserved_row_never_holds_the_key(tmp_path):
    clips.render(request(tmp_path), approval="trundle yes $0.64 " + KEY,
                 transport=Mock(side_effect=ok_responses()), sleep=lambda _: None)
    assert KEY not in (tmp_path / "ledger.jsonl").read_text()


def test_missing_ledger_dir_fails_closed_without_rows(tmp_path, monkeypatch):
    monkeypatch.setenv("TT_CLIP_LEDGER", str(tmp_path / "nope" / "ledger.jsonl"))
    with pytest.raises(clips.VeoTrialCapError, match="missing"):
        clips.render(request(tmp_path), approval="trundle yes $0.64", transport=Mock())
    assert not (tmp_path / "nope").exists()
