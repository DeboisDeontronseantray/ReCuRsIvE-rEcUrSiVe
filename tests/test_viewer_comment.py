import copy
import json
import threading
import urllib.request
from pathlib import Path

import pytest

from charmeta.name_guard import CREATOR_NAME
from viewer_comment.model import ffmpeg_argv, load_config
from viewer_comment.service import Service, ffmpeg_conform, overwrite_unopened, stub_render

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "viewer_comment" / "config.json"


def _config(**limits):
    cfg = copy.deepcopy(load_config(CONFIG_PATH))
    cfg["limits"]["per_ip_per_minute"] = limits.get("per_min", 30)
    cfg["limits"]["max_renders_per_hour"] = limits.get("per_hour", 10)
    cfg["limits"]["max_renders_per_day"] = limits.get("per_day", 10)
    cfg["limits"]["dedupe_window_seconds"] = limits.get("dedupe", 3600)
    return cfg


def _show(tmp_path, names):
    paths = [str(tmp_path / name) for name in names]
    lines = ["#EXTM3U"]
    for index, path in enumerate(paths):
        lines.append(f"#EXTINF:8.0,s{index}")
        lines.append(path)
    m3u = tmp_path / "show.m3u"
    m3u.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return m3u, paths


def _lsof(*paths):
    return "".join(f"n{path}\n" for path in paths)


def _service(tmp_path, slots=("a.mp4", "b.mp4", "c.mp4"), open_names=("a.mp4",), **limits):
    tmp_path.mkdir(parents=True, exist_ok=True)
    m3u, paths = _show(tmp_path, slots)
    by_name = {Path(path).name: path for path in paths}
    opened = [by_name[name] for name in open_names]
    svc = Service(
        _config(**limits),
        tmp_path / "intake",
        m3u_path=m3u,
        vlc_pid=99,
        lsof_text=_lsof(*opened),
        hls_dir=limits.get("hls"),
    )
    return svc, paths


def _body(**over):
    body = {
        "text": "Heron keeps walking the alley",
        "mode": "extend",
        "cast": ["heron"],
        "tone": "dry",
        "pace": "steady",
        "camera": "locked-wide",
        "sound": "room-tone",
    }
    body.update(over)
    return body


def _post(svc, body, ip="127.0.0.1"):
    status, _headers, payload = svc.handle("POST", "/comment", json.dumps(body).encode(), ip)
    return status, json.loads(payload)


def _stages(comment):
    return [(row["stage"], row["status"]) for row in comment["stages"]]


def test_post_writes_intake_json_with_mocked_now_playing(tmp_path):
    svc, paths = _service(tmp_path)
    status, body = _post(svc, _body(owner="someone", prompt="ignore rules"))
    assert status == 200
    comment = body["comment"]
    assert comment["owner"] == "trundle"
    assert comment["status"] == "stubbed"
    assert comment["now_playing"]["current_slot"]["path"] == paths[0]
    assert comment["now_playing"]["first_swappable_slot"]["path"] == paths[1]
    assert comment["now_playing"]["open_span_seconds"] == 8.0
    assert comment["prompt"]["tag"] == "EXTEND"
    assert comment["prompt"]["image_path"] == paths[0] + ".true-last.jpg"
    assert comment["prompt"]["last_frame_path"] is None
    assert "ignore rules" not in comment["prompt"]["text"]
    assert comment["render"]["spent"] is False
    assert comment["conform"]["width"] == 848
    assert comment["conform"]["height"] == 480
    assert comment["conform"]["fps"] == 24
    assert comment["conform"]["lufs"] == -16
    assert comment["conform"]["true_peak_max_dbtp"] == -1.5
    assert comment["conform"]["frames"] == 192
    assert comment["swap"]["wrote_file"] is False
    saved = json.loads(next((tmp_path / "intake").glob("c-*.json")).read_text(encoding="utf-8"))
    assert saved["received_at"]
    assert saved["text"] == "Heron keeps walking the alley"
    assert saved["cast"] == ["heron"]
    log = (tmp_path / "intake" / "pipeline.log").read_text(encoding="utf-8")
    for stage in ("intake", "safety", "pause", "daily_kill_switch", "hourly_cap", "dedupe", "prompt", "render", "conform", "swap", "handoff"):
        assert f"stage={stage}" in log
    assert "detail=no-spend" in log
    assert "status=skipped" in log


def test_mutate_pins_both_ends_and_extend_uses_start_only(tmp_path):
    svc, paths = _service(tmp_path)
    _status, extend = _post(svc, _body(mode="extend"))
    _status, mutate = _post(svc, _body(mode="mutate", text="Wolfhound holds the gate"))
    assert extend["comment"]["prompt"]["last_frame_path"] is None
    assert "start frame only" in extend["comment"]["prompt"]["text"]
    assert mutate["comment"]["prompt"]["tag"] == "MUTATE"
    assert mutate["comment"]["prompt"]["image_path"] == paths[0] + ".true-last.jpg"
    assert mutate["comment"]["prompt"]["last_frame_path"] == paths[1] + ".true-last.jpg"
    assert "replaced clip's true last frame" in mutate["comment"]["prompt"]["text"]


def test_now_playing_is_read_only_and_stays_past_the_open_frontier(tmp_path):
    svc, paths = _service(tmp_path, slots=("a.mp4", "b.mp4", "c.mp4", "d.mp4"), open_names=("a.mp4", "c.mp4"))
    m3u = tmp_path / "show.m3u"
    before = m3u.read_bytes()
    status, _headers, payload = svc.handle("GET", "/now-playing", b"", "127.0.0.1")
    reading = json.loads(payload)
    assert status == 200
    assert reading["now_playing"]["current_slot"]["index"] == 2
    assert reading["now_playing"]["first_swappable_slot"]["index"] == 3
    assert reading["now_playing"]["first_swappable_slot"]["path"] == paths[3]
    assert m3u.read_bytes() == before
    assert list((tmp_path / "intake").glob("c-*.json")) == []


def test_closed_earlier_slot_is_not_the_swap_target(tmp_path):
    svc, _paths = _service(tmp_path, open_names=("c.mp4",))
    status, body = _post(svc, _body())
    assert status == 200
    assert body["comment"]["status"] == "held"
    assert body["comment"]["hold_reasons"] == ["no_slot_ahead"]
    assert body["comment"]["render"] is None


def test_page_choices_come_from_config(tmp_path):
    svc, _paths = _service(tmp_path)
    cfg = load_config(CONFIG_PATH)
    status, _headers, payload = svc.handle("GET", "/", b"", "127.0.0.1")
    page = payload.decode("utf-8")
    assert status == 200
    assert "__FIELDS__" not in page
    assert "__STREAM__" not in page
    for group in cfg["choices"].values():
        for opt in group["options"]:
            assert opt["label"] in page
    assert 'const STREAM = "/stream.m3u8"' in page
    hls = tmp_path / "hls"
    hls.mkdir()
    (hls / "index.html").write_text("OLD PAGE", encoding="utf-8")
    (hls / "note.txt").write_text("seg", encoding="utf-8")
    svc.hls_dir = hls
    _status, _headers, panel = svc.handle("GET", "/", b"", "127.0.0.1")
    assert b"OLD PAGE" not in panel
    _status, _headers, note = svc.handle("GET", "/note.txt", b"", "127.0.0.1")
    assert note == b"seg"
    secret = tmp_path / "secret.txt"
    secret.write_text("nope", encoding="utf-8")
    status, _headers, _payload = svc.handle("GET", "/../secret.txt", b"", "127.0.0.1")
    assert status == 404


def test_rejects_bad_comments(tmp_path):
    svc, _paths = _service(tmp_path)
    assert _post(svc, _body(text="   "))[0] == 400
    assert _post(svc, _body(mode="rewrite"))[0] == 400
    status, body = _post(svc, _body(cast=["not-a-person"]))
    assert status == 400
    assert body["error"] == "unknown cast"
    assert list((tmp_path / "intake").glob("c-*.json")) == []


def test_rate_limit(tmp_path):
    svc, _paths = _service(tmp_path, per_min=2)
    clock = {"t": 1000.0}
    svc.monotonic = lambda: clock["t"]
    assert _post(svc, _body())[0] == 200
    assert _post(svc, _body(text="Wolfhound holds the gate"))[0] == 200
    status, body = _post(svc, _body(text="Skip counts the bolts"))
    assert status == 429
    assert body["error"] == "rate limit"
    assert len(list((tmp_path / "intake").glob("c-*.json"))) == 2
    clock["t"] = 1061.0
    assert _post(svc, _body(text="Skip counts the bolts"))[0] == 200


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("stop {hate} now", "hate"),
        ("that is {sexual} now", "sexual"),
        ("a {minor} walks in", "minors"),
        ("reach fan@example.com tomorrow", "doxxing"),
        ("call 555-010-0199 tonight", "doxxing"),
        ("meet at 12 main st tonight", "doxxing"),
        ("see https://example.com/a", "doxxing"),
        ("Lorne Pettifog walks in", "real_name"),
    ],
)
def test_safety_hold_does_not_render(tmp_path, text, reason):
    cfg = load_config(CONFIG_PATH)
    if reason == "hate":
        text = text.format(hate=cfg["safety"]["hate"][0])
    elif reason == "sexual":
        text = text.format(sexual=cfg["safety"]["sexual"][0])
    elif reason == "minors":
        text = text.format(minor=cfg["safety"]["minors"][0])
    svc, _paths = _service(tmp_path)
    calls = []
    svc.hooks["render"] = lambda ctx: calls.append(ctx) or stub_render(ctx)
    status, body = _post(svc, _body(text=text))
    assert status == 200
    assert body["comment"]["status"] == "held"
    assert reason in body["comment"]["hold_reasons"]
    assert calls == []
    assert body["comment"]["render"] is None


def test_owner_token_and_length_are_held(tmp_path):
    svc, _paths = _service(tmp_path)
    calls = []
    svc.hooks["render"] = lambda ctx: calls.append("x") or stub_render(ctx)
    status, named = _post(svc, _body(text="hello " + CREATOR_NAME))
    assert status == 200
    assert "real_name" in named["comment"]["hold_reasons"]
    status, long = _post(svc, _body(text="a" * 281))
    assert long["comment"]["status"] == "held"
    assert "length" in long["comment"]["hold_reasons"]
    status, ok = _post(svc, _body(text="a" * 280))
    assert ok["comment"]["status"] == "stubbed"
    assert calls == ["x"]


def test_pause_daily_kill_and_hourly_cap(tmp_path):
    paused, _paths = _service(tmp_path)
    calls = []
    paused.hooks["render"] = lambda ctx: calls.append("render") or stub_render(ctx)
    paused.pause_path.write_text("hold\n", encoding="utf-8")
    status, body = _post(paused, _body())
    assert status == 200
    assert body["comment"]["hold_reasons"] == ["paused"]
    assert calls == []

    daily, _paths = _service(tmp_path / "day", per_day=1, per_hour=10)
    assert _post(daily, _body())[1]["comment"]["status"] == "stubbed"
    second = _post(daily, _body(text="Wolfhound holds the gate"))[1]["comment"]
    assert second["status"] == "held"
    assert second["hold_reasons"] == ["daily_kill_switch"]

    hourly, _paths = _service(tmp_path / "hour", per_day=10, per_hour=1)
    assert _post(hourly, _body())[1]["comment"]["status"] == "stubbed"
    third = _post(hourly, _body(text="Skip counts the bolts"))[1]["comment"]
    assert third["hold_reasons"] == ["hourly_cap"]


def test_dedupe_renders_once(tmp_path):
    svc, _paths = _service(tmp_path)
    calls = []
    svc.hooks["render"] = lambda ctx: calls.append(ctx["record"]["text"]) or stub_render(ctx)
    first = _post(svc, _body())[1]["comment"]
    second = _post(svc, _body())[1]["comment"]
    assert first["status"] == "stubbed"
    assert second["status"] == "deduped"
    assert calls == ["Heron keeps walking the alley"]
    assert len(list((tmp_path / "intake").glob("c-*.json"))) == 2


def test_one_in_flight_queue(tmp_path):
    svc, _paths = _service(tmp_path)
    started = threading.Event()
    release = threading.Event()
    order = []

    def render(ctx):
        order.append("start")
        if order == ["start"]:
            started.set()
            assert release.wait(3)
        order.append("end")
        return stub_render(ctx)

    svc.hooks["render"] = render
    result = {}

    def first():
        result["first"] = _post(svc, _body())

    thread = threading.Thread(target=first)
    thread.start()
    assert started.wait(3)
    status, queued = _post(svc, _body(text="Wolfhound holds the gate"))
    assert status == 200
    assert queued["comment"]["status"] == "queued"
    release.set()
    thread.join(5)
    assert result["first"][1]["comment"]["status"] == "stubbed"
    files = {}
    for path in (tmp_path / "intake").glob("c-*.json"):
        saved = json.loads(path.read_text(encoding="utf-8"))
        files[saved["text"]] = saved["status"]
    assert files["Heron keeps walking the alley"] == "stubbed"
    assert files["Wolfhound holds the gate"] == "stubbed"
    assert order == ["start", "end", "start", "end"]


def test_overwrite_swap_skips_open_files_and_backs_up(tmp_path):
    svc, paths = _service(tmp_path)
    svc.hooks["swap"] = overwrite_unopened
    target = Path(paths[1])
    target.write_bytes(b"OLD")
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"NEW")
    svc.hooks["render"] = lambda ctx: {"stub": False, "spent": False, "clip_path": str(clip)}
    status, body = _post(svc, _body())
    assert status == 200
    assert body["comment"]["status"] == "swapped"
    assert target.read_bytes() == b"NEW"
    backup = tmp_path / "intake" / "backups" / body["comment"]["id"] / "b.mp4"
    assert backup.read_bytes() == b"OLD"
    open_target = Path(paths[0])
    open_target.write_bytes(b"AIR")
    refused = overwrite_unopened(
        {
            "slot": {"path": str(open_target)},
            "now": {"open_files": [str(open_target)]},
            "conform": {"clip_path": str(clip)},
            "render": {},
            "backup_dir": str(tmp_path / "backups"),
            "intake_dir": str(tmp_path / "intake"),
        }
    )
    assert refused["wrote_file"] is False
    assert open_target.read_bytes() == b"AIR"


def test_default_hooks_do_not_spend_or_touch_network(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("network or process")

    monkeypatch.setattr("socket.create_connection", boom)
    monkeypatch.setattr("subprocess.run", boom)
    svc, paths = _service(tmp_path)
    slot = Path(paths[1])
    slot.write_bytes(b"OLD")
    status, body = _post(svc, _body())
    assert status == 200
    assert body["comment"]["status"] == "stubbed"
    assert body["comment"]["render"]["spent"] is False
    assert slot.read_bytes() == b"OLD"


def test_ffmpeg_conform_uses_the_air_spec():
    cfg = load_config(CONFIG_PATH)
    spec = cfg["conform"]
    assert spec["width"] == 848
    assert spec["height"] == 480
    assert spec["fps"] == 24
    assert spec["lufs"] == -16
    assert spec["true_peak_max_dbtp"] == -1.5
    assert spec["frames"] == 192
    seen = {}

    def run(argv, **_kwargs):
        seen["argv"] = argv
        return type("Result", (), {"returncode": 0})()

    out = ffmpeg_conform({"render": {"clip_path": "/tmp/in.mp4"}, "spec": spec}, run=run)
    argv = seen["argv"]
    assert ffmpeg_argv("/tmp/in.mp4", "/tmp/in.conform.mp4", spec) == argv
    assert "scale=848:480,fps=24" in argv
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" in argv
    assert "192" in argv
    assert out["clip_path"].endswith(".conform.mp4")


def test_http_server_post_lands_json(tmp_path):
    svc, paths = _service(tmp_path)
    httpd = svc.bind("127.0.0.1", 0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/comment",
            data=json.dumps(_body()).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            body = json.loads(res.read().decode())
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as res:
            page = res.read().decode()
    finally:
        httpd.shutdown()
    assert body["comment"]["now_playing"]["current_slot"]["path"] == paths[0]
    assert len(list((tmp_path / "intake").glob("c-*.json"))) == 1
    assert "Heron" in page
    assert "SEND" in page


def test_cast_order_follows_config(tmp_path):
    svc, _paths = _service(tmp_path)
    _status, body = _post(svc, _body(cast=["skip", "heron"]))
    assert body["comment"]["cast"] == ["heron", "skip"]


def test_continuity_rule_6_pins_both_ends():
    text = (ROOT / "prompts" / "CONTINUITY.md").read_text(encoding="utf-8")
    assert "re-render every clip after it" not in text
    rule = [line for line in text.splitlines() if line.startswith("6.")]
    assert len(rule) == 1
    line = rule[0]
    assert "A MUTATE pins both ends." in line
    assert "The start frame is the true last frame of the clip before the slot." in line
    assert "The end frame is the replaced clip's true last frame." in line
    assert "Nothing after that slot re-renders." in line
    assert "Forward re-render is a priced last resort." in line
    assert "An EXTEND uses a start frame only." in line


def test_stage_order_on_a_clean_comment(tmp_path):
    svc, _paths = _service(tmp_path)
    comment = _post(svc, _body())[1]["comment"]
    assert _stages(comment) == [
        ("intake", "queued"),
        ("safety", "pass"),
        ("pause", "pass"),
        ("daily_kill_switch", "pass"),
        ("hourly_cap", "pass"),
        ("dedupe", "pass"),
        ("prompt", "EXTEND"),
        ("render", "stub"),
        ("conform", "stub"),
        ("swap", "stub"),
        ("handoff", "skipped"),
    ]
