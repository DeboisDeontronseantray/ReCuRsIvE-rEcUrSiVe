"""Veo dry signals reported to pool-check (trundle 2026-11-02 8:56 PM CT). All mocked; no paid calls."""
import json
from datetime import date
import os
from pathlib import Path
import stat
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
    (tmp_path / "ledger.jsonl").write_text("")
    monkeypatch.setattr(spend, "month_total_for_gate", lambda: (0, "test"))
    tool = tmp_path / "fake-pool-check"
    tool.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$(dirname \"$0\")/calls.txt\"\n")
    tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("TT_POOL_CHECK", str(tool))
    yield
    urlopen.assert_not_called()


def calls(tmp_path):
    path = tmp_path / "calls.txt"
    return path.read_text().splitlines() if path.exists() else []


def request(tmp_path, **kwargs):
    return clips.ClipRequest("A foggy outpost", out_path=str(tmp_path / "clip.mp4"), **kwargs)


def fail_with(status, body):
    return Mock(return_value=(status, body))


@pytest.mark.parametrize("status,body,reason", [
    (404, '{"error":{"code":404,"message":"Publisher Model veo-3.1-fast-generate-001 was not found","status":"NOT_FOUND"}}',
     clips.VEO_DRY_404),
    (403, '{"error":{"code":403,"status":"PERMISSION_DENIED","message":"permission denied"}}', clips.VEO_DRY_403),
    (403, '{"error":{"code":403,"message":"Quota exceeded for aiplatform"}}', clips.VEO_DRY_403),
    (429, '{"error":{"code":429,"status":"RESOURCE_EXHAUSTED","message":"rate"}}', clips.VEO_DRY_429),
    (200, '{"error":{"code":8,"status":"RESOURCE_EXHAUSTED"}}', clips.VEO_DRY_429),
])
def test_http_dry_signals_mark_veo(tmp_path, status, body, reason):
    with pytest.raises(clips.ClipRenderError):
        clips.render(request(tmp_path), approval="yes $0.64", transport=fail_with(status, body), sleep=lambda _: None)
    assert calls(tmp_path) == [f"--mark-dry veo --reason {reason} --bot clip_render"]
    assert KEY not in (tmp_path / "calls.txt").read_text()


def test_cap_hit_marks_veo_and_cli_exits_4(tmp_path):
    (tmp_path / "ledger.jsonl").write_text(json.dumps({"provider": "vertex_veo", "cost_usd": 149.9}) + "\n")
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(clips.asdict(request(tmp_path))))
    assert clips.main(["--spec", str(spec), "--approved", "yes $0.64"]) == 4
    assert calls(tmp_path) == [f"--mark-dry veo --reason {clips.VEO_DRY_CAP} --bot clip_render"]


def test_trial_ended_blocks_before_transport_and_marks_veo(tmp_path, monkeypatch):
    class AfterTrial(clips.datetime):
        @classmethod
        def now(cls, tz=None):
            return clips.datetime(2027, 1, 5, 9, 0, tzinfo=tz)
    monkeypatch.setattr(clips, "datetime", AfterTrial)
    transport = Mock()
    with pytest.raises(clips.VeoTrialCapError, match="trial ended"):
        clips.render(request(tmp_path), approval="yes $0.64", transport=transport)
    transport.assert_not_called()
    assert calls(tmp_path) == [f"--mark-dry veo --reason {clips.VEO_DRY_TRIAL_END} --bot clip_render"]
    assert (tmp_path / "ledger.jsonl").read_text() == ""  # no ledger row


def test_trial_open_dates():
    clips._veo_trial_open(date(2027, 1, 4))  # last trial day is still open
    with pytest.raises(clips.VeoTrialCapError, match="trial ended 2027-01-04"):
        clips._veo_trial_open(date(2027, 1, 5))


@pytest.mark.parametrize("status,body", [(500, "server error"), (400, "bad request"),
                                         (403, '{"error":{"message":"request blocked by policy"}}')])
def test_other_failures_are_not_dry(tmp_path, status, body):
    with pytest.raises(clips.ClipRenderError):
        clips.render(request(tmp_path), approval="yes $0.64", transport=fail_with(status, body))
    assert calls(tmp_path) == []


def test_ledger_fault_is_not_dry(tmp_path):
    (tmp_path / "ledger.jsonl").write_text("{bad\n")
    with pytest.raises(clips.VeoTrialCapError, match="corrupt"):
        clips.render(request(tmp_path), approval="yes $0.64", transport=Mock())
    assert calls(tmp_path) == []


def test_no_tool_set_means_no_report(tmp_path, monkeypatch):
    monkeypatch.delenv("TT_POOL_CHECK")
    with pytest.raises(clips.ClipRenderError):
        clips.render(request(tmp_path), approval="yes $0.64", transport=fail_with(429, "RESOURCE_EXHAUSTED"))
    assert calls(tmp_path) == []
    assert clips.report_veo_dry("x", env={"TT_POOL_CHECK": str(tmp_path / "missing-tool")}) is False


def test_xai_failures_never_mark_veo(tmp_path, monkeypatch):
    monkeypatch.setattr(clips.spend, "check_can_spend", lambda _est: None)
    with pytest.raises(clips.ClipRenderError):
        clips.render(request(tmp_path, provider="xai", duration_s=6, resolution="480p"), approval="yes $1",
                     transport=fail_with(429, "RESOURCE_EXHAUSTED"))
    assert calls(tmp_path) == []
