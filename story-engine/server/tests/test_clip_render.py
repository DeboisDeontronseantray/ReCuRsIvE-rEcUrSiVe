"""All transports are mocked; no paid calls are permitted in this suite."""
import base64
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from app import clip_render as clips
from app import spend

KEY = "fake-vertex-key-never-print"
VIDEO = b"mock mp4 bytes"


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


def request(tmp_path, **kwargs):
    return clips.ClipRequest("A foggy outpost", out_path=str(tmp_path / "clip.mp4"), **kwargs)


def refs(tmp_path, count):
    result = []
    for n in range(count):
        p = tmp_path / f"ref{n}.png"
        p.write_bytes(b"image")
        result.append(str(p))
    return result


def transport_with(*responses):
    return Mock(side_effect=[(status, json.dumps(body)) for status, body in responses])


def success():
    return transport_with((200, {"name": "projects/1055647348526/operations/op1"}),
                          (200, {"done": False}),
                          (200, {"done": True, "response": {"videos": [{"bytesBase64Encoded": base64.b64encode(VIDEO).decode()}]}}))


def ledger(tmp_path):
    return [json.loads(line) for line in (tmp_path / "ledger.jsonl").read_text().splitlines()]


def test_mocked_veo_success(tmp_path):
    req = request(tmp_path, reference_images=refs(tmp_path, 3), clip_id="clip1", channel="ch4", show_id="show")
    fake = success()
    result = clips.render(req, approval="trundle yes $0.64", transport=fake, sleep=lambda _: None)
    assert Path(result["out_path"]).read_bytes() == VIDEO
    method, url, body = fake.call_args_list[0].args
    assert method == "POST"
    assert url.startswith(clips.VERTEX_ROOT + "veo-3.1-fast-generate-001:predictLongRunning?key=")
    assert body["parameters"] == {"durationSeconds": 8, "sampleCount": 1, "generateAudio": False, "resolution": "720p", "aspectRatio": "16:9"}
    images = body["instances"][0]["referenceImages"]
    assert len(images) == 3 and all(i["referenceType"] == "asset" for i in images)
    assert images[0]["image"]["mimeType"] == "image/png"
    assert fake.call_count == 3
    assert ":fetchPredictOperation" in fake.call_args_list[1].args[1]
    assert fake.call_args_list[1].args[2] == {"operationName": "projects/1055647348526/operations/op1"}
    row, = ledger(tmp_path)
    assert row["est_usd"] == row["cost_usd"] == 8 * 0.08
    assert row["operation"] == "op1" and row["provider"] == "vertex_veo"
    assert row["refs"] == 3 and row["clip_id"] == "clip1"
    assert "prompt" not in row and len(row["prompt_sha256"]) == 64
    assert KEY not in json.dumps(row)


def run_cli(tmp_path, req, *args):
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(clips.asdict(req)))
    return clips.main(["--spec", str(spec), *args])


@pytest.mark.parametrize("responses,expected", [
    ([(403, {"error": {"message": "denied ?key=" + KEY}})], "denied"),
    ([(429, {"error": {"message": "RESOURCE_EXHAUSTED"}})], "RESOURCE_EXHAUSTED"),
    ([(200, {"name": "operations/op8"}), (200, {"done": True, "error": {"code": 8, "message": "quota exhausted"}})], "quota exhausted"),
])
def test_cli_failure_loud_logged_and_redacted(tmp_path, monkeypatch, capsys, responses, expected):
    fake = transport_with(*responses)
    monkeypatch.setattr(clips, "_transport", lambda method, url, body, **kw: fake(method, url, body))
    original = clips.render
    monkeypatch.setattr(clips, "render", lambda req, **kw: original(req, **kw, sleep=lambda _: None))
    assert run_cli(tmp_path, request(tmp_path), "--approved", "trundle yes $0.64") == 1
    output = capsys.readouterr()
    assert expected in output.err and "clip_render FAILED http=" in output.err
    assert KEY not in output.out + output.err + (tmp_path / "ledger.jsonl").read_text()
    row, = ledger(tmp_path)
    assert row["cost_usd"] == 0 and row["status"] == "failed"
    assert not (tmp_path / "clip.mp4").exists()


@pytest.mark.parametrize("options,estimate", [
    ({"tier": "lite", "duration_s": 4}, 0.12),
    ({}, 0.64),
    ({"duration_s": 6, "resolution": "1080p"}, 0.60),
    ({"audio": True}, 0.80),
    ({"provider": "xai", "nrefs": 3}, 0.67),
    ({"provider": "xai", "tier": "lite"}, 0.16),
])
def test_dry_run(tmp_path, monkeypatch, capsys, options, estimate):
    options = dict(options)
    options["reference_images"] = refs(tmp_path, options.pop("nrefs", 0))
    monkeypatch.setattr(clips, "_transport", Mock(side_effect=AssertionError("no transport")))
    assert run_cli(tmp_path, request(tmp_path, **options), "--dry-run") == 0
    output = capsys.readouterr()
    p = json.loads(output.out)
    assert p["quote"]["est_usd"] == estimate
    assert p["needs"] == "trundle's priced yes" and p["key_set"]
    assert KEY not in output.out and "bytesBase64Encoded" not in output.out
    assert not (tmp_path / "ledger.jsonl").exists()


@pytest.mark.parametrize("approval", [None, "", "trundle yes", "$", "$invalid"])
def test_approval_precedes_key_read_and_transport(tmp_path, monkeypatch, capsys, approval):
    fake = Mock(side_effect=AssertionError("no transport"))
    req = request(tmp_path)
    original_get = clips.os.environ.get
    def no_key(name, *args, **kwargs):
        if name in ("GCP_VERTEX_API_KEY", "XAI_API_KEY", "XAI_KEY_FILE"):
            raise AssertionError("must not read credential")
        return original_get(name, *args, **kwargs)
    monkeypatch.setattr(clips.os.environ, "get", no_key)
    with pytest.raises(clips.ApprovalRequired):
        clips.render(req, approval=approval, transport=fake)
    fake.assert_not_called()
    args = ["--approved", approval] if approval is not None else []
    assert run_cli(tmp_path, req, *args) == 3
    assert "needs trundle's priced yes" in capsys.readouterr().err


@pytest.mark.parametrize("case", ["4refs", "lite", "both", "exists", "masters", "duration", "fal", "kie", "unknown", "missing", "suffix", "resolution", "unknown_key"])
def test_validation_cli(tmp_path, capsys, case):
    req = request(tmp_path)
    if case == "4refs": req.reference_images = refs(tmp_path, 4)
    if case == "lite": req.reference_images = refs(tmp_path, 1); req.tier = "lite"
    if case == "both": req.reference_images = refs(tmp_path, 1); req.start_image = req.reference_images[0]
    if case == "exists": Path(req.out_path).write_bytes(b"keep")
    if case == "masters": req.out_path = str(tmp_path / "masters" / "clip.mp4")
    if case == "duration": req.duration_s = 5
    if case in ("fal", "kie", "unknown"): req.provider = case
    if case == "missing": req.reference_images = [str(tmp_path / "missing.png")]
    if case == "suffix": req.start_image = str(tmp_path / "image.gif"); Path(req.start_image).write_bytes(b"image")
    if case == "resolution": req.resolution = "4k"; req.tier = "lite"
    if case == "unknown_key":
        with pytest.raises(clips.ClipRequestError): clips.ClipRequest.from_dict({"prompt": "x", "unknown": True})
        return
    assert run_cli(tmp_path, req, "--dry-run") == 2
    output = capsys.readouterr()
    if case in ("fal", "kie"): assert "blocked by CURRENT-RULES L60 (paid resellers held)" in output.err
    assert not (tmp_path / "ledger.jsonl").exists()


@pytest.mark.parametrize("response,expected", [
    ({"done": True, "response": {"raiMediaFilteredCount": 1, "raiMediaFilteredReasons": ["safety"]}}, "safety"),
    ({"done": True, "response": {}}, "empty"),
    ({"done": True, "response": {"videos": [{"bytesBase64Encoded": "!invalid"}]}}, "base64"),
])
def test_output_failures(tmp_path, response, expected):
    fake = transport_with((200, {"name": "operations/op"}), (200, response))
    with pytest.raises(clips.ClipRenderError) as error:
        clips.render(request(tmp_path), approval="trundle $0.64 yes", transport=fake, sleep=lambda _: None)
    assert expected in str(error.value).lower()
    assert ledger(tmp_path)[0]["cost_usd"] == 0


def test_timeout(tmp_path):
    fake = Mock(side_effect=lambda method, url, body: (200, json.dumps({"name": "operations/op"} if ":predictLongRunning" in url else {"done": False})))
    with pytest.raises(clips.ClipRenderError, match="timeout"):
        clips.render(request(tmp_path), approval="trundle $0.64 yes", transport=fake, sleep=lambda _: None, poll_seconds=1, timeout_seconds=1)
    assert ledger(tmp_path)[0]["cost_usd"] == 0


def test_exception_redacts_key_and_limits_body(tmp_path):
    fake = transport_with((403, {"error": KEY + " ?key=another-secret&foo=bar " + "x" * 2000}))
    with pytest.raises(clips.ClipRenderError) as error:
        clips.render(request(tmp_path), approval="trundle $0.64 yes " + KEY, transport=fake)
    assert KEY not in str(error.value) and "another-secret" not in str(error.value)
    assert len(error.value.body) <= 1000
    assert KEY not in (tmp_path / "ledger.jsonl").read_text()


def test_xai_fallback_success(tmp_path, monkeypatch):
    gate = Mock()
    monkeypatch.setattr(spend, "check_can_spend", gate)
    fake = Mock(side_effect=[(200, '{"request_id":"x1"}'), (200, '{"status":"pending"}'),
                            (200, '{"status":"done","video":{"url":"https://video.example/clip.mp4"}}'), (200, VIDEO)])
    req = request(tmp_path, provider="xai", reference_images=refs(tmp_path, 3))
    clips.render(req, approval="trundle yes $0.67", transport=fake, sleep=lambda _: None)
    gate.assert_called_once_with(0.67)
    assert fake.call_args_list[0].args[1] == clips.XAI_ROOT + "/generations"
    assert fake.call_args_list[1].args[:2] == ("GET", clips.XAI_ROOT + "/x1")
    assert fake.call_args_list[0].args[2]["reference_images"][0]["url"].startswith("data:image/png;base64,")
    assert Path(req.out_path).read_bytes() == VIDEO
    assert ledger(tmp_path)[0]["provider"] == "xai_imagine"


def test_xai_spend_gate_stops_before_call(tmp_path, monkeypatch):
    monkeypatch.setattr(spend, "check_can_spend", Mock(side_effect=spend.SpendLimitError("monthly cap")))
    fake = Mock()
    with pytest.raises(spend.SpendLimitError):
        clips.render(request(tmp_path, provider="xai"), approval="trundle yes $0.64", transport=fake)
    fake.assert_not_called()
    assert ledger(tmp_path)[0]["cost_usd"] == 0


def test_xai_lane_enforces_50_including_clip_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(spend, "check_can_spend", Mock())
    monkeypatch.setattr(spend, "month_total_for_gate", lambda: (49, "test"))
    previous = {"provider": "xai_imagine", "ts_ct": clips.datetime.now(clips.ZoneInfo("America/Chicago")).isoformat(), "cost_usd": 0.5}
    (tmp_path / "ledger.jsonl").write_text(json.dumps(previous) + "\n")
    fake = Mock()
    with pytest.raises(spend.SpendLimitError, match="50"):
        clips.render(request(tmp_path, provider="xai"), approval="trundle yes $0.64", transport=fake)
    fake.assert_not_called()


def test_missing_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GCP_VERTEX_API_KEY")
    assert run_cli(tmp_path, request(tmp_path), "--approved", "trundle yes $0.64") == 2
    assert "missing GCP_VERTEX_API_KEY" in capsys.readouterr().err
    assert ledger(tmp_path)[0]["cost_usd"] == 0


@pytest.mark.parametrize("field,value", [("provider", []), ("tier", {}), ("resolution", []), ("out_path", 7), ("audio", "false"), ("reference_images", "ref.png")])
def test_invalid_json_field_types(tmp_path, field, value):
    req = request(tmp_path)
    setattr(req, field, value)
    assert run_cli(tmp_path, req, "--dry-run") == 2


def test_first_frame_and_negative_prompt(tmp_path):
    start = tmp_path / "first.jpg"
    start.write_bytes(b"jpeg")
    req = request(tmp_path, start_image=str(start), negative_prompt="no text", tier="lite", duration_s=4)
    fake = success()
    clips.render(req, approval="trundle yes $0.12", transport=fake, sleep=lambda _: None)
    body = fake.call_args_list[0].args[2]
    assert body["instances"][0]["image"] == {"bytesBase64Encoded": base64.b64encode(b"jpeg").decode(), "mimeType": "image/jpeg"}
    assert body["parameters"]["negativePrompt"] == "no text"
    assert ledger(tmp_path)[0]["start_image"] is True


def test_poll_http_error_and_transport_exception(tmp_path):
    for failure in ((503, '{"message":"unavailable"}'), OSError("connection ?key=" + KEY)):
        fake = Mock(side_effect=[(200, '{"name":"operations/op"}'), failure])
        with pytest.raises(clips.ClipRenderError) as error:
            clips.render(request(tmp_path), approval="trundle yes $0.64", transport=fake, sleep=lambda _: None)
        assert KEY not in str(error.value)
    assert len(ledger(tmp_path)) == 2
    assert all(row["cost_usd"] == 0 for row in ledger(tmp_path))


def test_dry_run_does_not_read_key_values(tmp_path, monkeypatch, capsys):
    original_get = clips.os.environ.get
    def guarded_get(name, *args, **kwargs):
        if name in ("GCP_VERTEX_API_KEY", "XAI_API_KEY"):
            raise AssertionError("dry-run read credential")
        return original_get(name, *args, **kwargs)
    monkeypatch.setattr(clips.os.environ, "get", guarded_get)
    assert run_cli(tmp_path, request(tmp_path), "--dry-run") == 0
    assert KEY not in capsys.readouterr().out


def test_cli_overrides(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(clips, "_transport", Mock(side_effect=AssertionError("no transport")))
    assert run_cli(tmp_path, request(tmp_path), "--provider", "xai", "--tier", "lite", "--out", str(tmp_path / "other.mp4"), "--dry-run") == 0
    p = json.loads(capsys.readouterr().out)
    assert p["quote"]["model"] == "grok-imagine-video-1.5-lite" and p["quote"]["est_usd"] == 0.16
    assert p["out_path"].endswith("other.mp4")
