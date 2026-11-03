"""Veo trial $150 cap (trundle 2026-11-02 8:44 PM CT). All transports are mocked; no paid calls."""
import base64
import json
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
    monkeypatch.setattr(spend, "month_total_for_gate", lambda: (0, "test"))
    yield
    urlopen.assert_not_called()


def ledger_path(tmp_path):
    return tmp_path / "ledger.jsonl"


def write_ledger(tmp_path, *costs, provider="vertex_veo", extra=""):
    rows = [json.dumps({"provider": provider, "cost_usd": c, "status": "success"}) for c in costs]
    ledger_path(tmp_path).write_text("".join(r + "\n" for r in rows) + extra)


def request(tmp_path, **kwargs):
    return clips.ClipRequest("A foggy outpost", out_path=str(tmp_path / "clip.mp4"), **kwargs)


def success():
    return Mock(side_effect=[(200, json.dumps({"name": "operations/op1"})),
                             (200, json.dumps({"done": True, "response": {"videos": [
                                 {"bytesBase64Encoded": base64.b64encode(b"mp4").decode()}]}}))])


def rows(tmp_path):
    return [json.loads(line) for line in ledger_path(tmp_path).read_text().splitlines() if line.strip()]


def run_cli(tmp_path, req, *args):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(clips.asdict(req)))
    return clips.main(["--spec", str(spec), *args])


def test_constants_separate_from_xai_gate():
    assert clips.VEO_TRIAL_CAP_USD == 150 and clips.VEO_TRIAL_WARN_USD == 120


def test_under_cap_renders(tmp_path, capsys):
    write_ledger(tmp_path, 10.0, 0, 5.5)
    result = clips.render(request(tmp_path), approval="trundle yes $0.64", transport=success(), sleep=lambda _: None)
    assert Path(result["out_path"]).read_bytes() == b"mp4"
    assert "WARNING" not in capsys.readouterr().err
    assert rows(tmp_path)[-1]["cost_usd"] == 0.64


def test_render_that_would_cross_150_is_blocked(tmp_path, capsys):
    write_ledger(tmp_path, 149.5)  # + 0.64 = 150.14
    fake = success()
    req = request(tmp_path)
    with pytest.raises(clips.VeoTrialCapError, match=r"cap \$150.00: spent \$149.50 \+ this render \$0.64 = \$150.14"):
        clips.render(req, approval="trundle yes $0.64", transport=fake, sleep=lambda _: None)
    fake.assert_not_called()
    assert len(rows(tmp_path)) == 1  # no row for the refused render
    assert run_cli(tmp_path, req, "--approved", "trundle yes $0.64") == 4
    err = capsys.readouterr().err
    assert "clip_render HARD STOP: Veo trial cap $150.00" in err and "($0.50 left)" in err
    assert not (tmp_path / "clip.mp4").exists()


def test_exactly_150_is_allowed(tmp_path):
    write_ledger(tmp_path, 149.36)
    clips.render(request(tmp_path), approval="yes $0.64", transport=success(), sleep=lambda _: None)


def test_warn_at_120(tmp_path, capsys):
    write_ledger(tmp_path, 119.5)
    clips.render(request(tmp_path), approval="yes $0.64", transport=success(), sleep=lambda _: None)
    err = capsys.readouterr().err
    assert "clip_render WARNING: Veo trial spend $120.14 after this render" in err
    assert "$29.86 of the $150 cap left" in err


def test_xai_rows_do_not_count_and_failed_rows_cost_zero(tmp_path, capsys):
    write_ledger(tmp_path, 140.0, provider="xai_imagine")
    with ledger_path(tmp_path).open("a") as f:
        f.write(json.dumps({"provider": "vertex_veo", "cost_usd": 0, "status": "failed"}) + "\n")
    assert clips.veo_trial_spent(ledger_path(tmp_path)) == 0
    clips.render(request(tmp_path), approval="yes $0.64", transport=success(), sleep=lambda _: None)
    assert "WARNING" not in capsys.readouterr().err


@pytest.mark.parametrize("case", ["missing", "bad_json", "not_object", "bad_cost", "negative", "directory"])
def test_missing_or_corrupt_ledger_fails_closed(tmp_path, capsys, case):
    path = ledger_path(tmp_path)
    if case == "missing":
        path.unlink(missing_ok=True)
    elif case == "bad_json":
        write_ledger(tmp_path, 1.0, extra="{not json\n")
    elif case == "not_object":
        write_ledger(tmp_path, extra="[1, 2]\n")
    elif case == "bad_cost":
        write_ledger(tmp_path, "1.0")
    elif case == "negative":
        write_ledger(tmp_path, -5)
    elif case == "directory":
        path.mkdir()
    fake = success()
    req = request(tmp_path)
    with pytest.raises(clips.VeoTrialCapError, match="fail closed"):
        clips.render(req, approval="yes $0.64", transport=fake, sleep=lambda _: None)
    fake.assert_not_called()
    assert run_cli(tmp_path, req, "--approved", "yes $0.64") == 4
    assert "clip_render HARD STOP: Veo trial ledger" in capsys.readouterr().err
    if case == "missing":
        assert not path.exists()  # never created by a refused render


def test_dry_run_shows_cap_and_left(tmp_path, capsys):
    write_ledger(tmp_path, 20.0)
    assert run_cli(tmp_path, request(tmp_path), "--dry-run") == 0
    cap = json.loads(capsys.readouterr().out)["veo_trial_cap"]
    assert cap["cap_usd"] == 150 and cap["warn_usd"] == 120
    assert cap["spent_usd"] == 20.0 and cap["this_est_usd"] == 0.64
    assert cap["left_usd"] == 130.0 and cap["left_after_usd"] == 129.36 and cap["status"] == "ok"


def test_dry_run_with_unreadable_ledger_reports_it(tmp_path, capsys):
    ledger_path(tmp_path).unlink(missing_ok=True)
    assert run_cli(tmp_path, request(tmp_path), "--dry-run") == 0
    cap = json.loads(capsys.readouterr().out)["veo_trial_cap"]
    assert cap["status"] == "ledger_unreadable" and "missing" in cap["error"]


def test_dry_run_xai_has_no_veo_cap(tmp_path, capsys):
    assert run_cli(tmp_path, request(tmp_path, provider="xai", tier="lite"), "--dry-run") == 0
    assert "veo_trial_cap" not in json.loads(capsys.readouterr().out)


def test_priced_yes_gate_still_first(tmp_path):
    ledger_path(tmp_path).unlink(missing_ok=True)  # even with no ledger, the approval error comes first
    with pytest.raises(clips.ApprovalRequired):
        clips.render(request(tmp_path), approval="yes", transport=success())


def test_xai_lane_not_gated_by_veo_cap(tmp_path, monkeypatch):
    write_ledger(tmp_path, 149.9)  # Veo nearly capped; xAI lane uses only its own $50 gate
    monkeypatch.setattr(clips.spend, "check_can_spend", lambda _est: None)
    fake = Mock(side_effect=[(200, json.dumps({"request_id": "r1"})),
                             (200, json.dumps({"status": "done", "video": {"url": "https://x.test/v.mp4"}})),
                             (200, b"mp4")])
    clips.render(request(tmp_path, provider="xai", tier="lite"), approval="yes $0.16", transport=fake, sleep=lambda _: None)
    assert rows(tmp_path)[-1]["provider"] == "xai_imagine"


def test_init_ledger(tmp_path, capsys):
    ledger_path(tmp_path).unlink(missing_ok=True)
    assert clips.main(["--init-ledger"]) == 0
    assert ledger_path(tmp_path).read_text() == ""
    write_ledger(tmp_path, 3.0)
    assert clips.main(["--init-ledger"]) == 0
    assert clips.veo_trial_spent(ledger_path(tmp_path)) == 3.0  # never truncates
