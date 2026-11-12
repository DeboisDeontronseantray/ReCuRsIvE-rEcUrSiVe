"""Local comment panel, intake files, and the guarded render path."""

from __future__ import annotations

import argparse
import html
import importlib
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from viewer_comment.model import (
    blank_probe,
    build_prompt,
    ffmpeg_argv,
    fingerprint,
    load_config,
    parse_comment,
    parse_lsof,
    parse_m3u,
    probe_slots,
    safety_reasons,
)

PACKAGE = Path(__file__).resolve().parent
DEFAULT_CONFIG = PACKAGE / "config.json"
PAGE = PACKAGE / "page" / "index.html"
JSON_HEADERS = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
MEDIA_TYPES = {
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".txt": "text/plain; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}
OWNER = "trundle"


def _dump(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def builtin_safety(ctx: dict) -> dict:
    return {"reasons": safety_reasons(ctx["record"]["text"], ctx["config"])}


def stub_render(ctx: dict) -> dict:
    prompt = ctx["prompt"]
    return {
        "stub": True,
        "spent": False,
        "clip_path": None,
        "image_path": prompt["image_path"],
        "last_frame_path": prompt["last_frame_path"],
    }


def stub_conform(ctx: dict) -> dict:
    spec = ctx["spec"]
    render = ctx.get("render") or {}
    return {
        "stub": True,
        "width": spec["width"],
        "height": spec["height"],
        "fps": spec["fps"],
        "lufs": spec["lufs"],
        "true_peak_max_dbtp": spec["true_peak_max_dbtp"],
        "frames": spec["frames"],
        "clip_path": render.get("clip_path"),
    }


def stub_swap(ctx: dict) -> dict:
    slot = ctx.get("slot") or {}
    return {"stub": True, "wrote_file": False, "target": slot.get("path")}


def ffmpeg_conform(ctx: dict, run=None) -> dict:
    render = ctx.get("render") or {}
    src = render.get("clip_path")
    if not src:
        return {"stub": False, "error": "no clip"}
    dest = str(Path(src).with_suffix(".conform.mp4"))
    argv = ffmpeg_argv(src, dest, ctx["spec"])
    runner = run or subprocess.run
    result = runner(argv, capture_output=True)
    if getattr(result, "returncode", 1) != 0:
        return {"stub": False, "error": "ffmpeg failed", "argv": argv}
    spec = ctx["spec"]
    return {
        "stub": False,
        "clip_path": dest,
        "argv": argv,
        "width": spec["width"],
        "height": spec["height"],
        "fps": spec["fps"],
        "lufs": spec["lufs"],
        "true_peak_max_dbtp": spec["true_peak_max_dbtp"],
        "frames": spec["frames"],
    }


def overwrite_unopened(ctx: dict) -> dict:
    slot = ctx.get("slot") or {}
    target = slot.get("path")
    now = ctx.get("now") or {}
    open_set = {os.path.normpath(path) for path in now.get("open_files") or []}
    if not target:
        return {"wrote_file": False, "error": "no slot"}
    if os.path.normpath(target) in open_set:
        return {"wrote_file": False, "error": "slot is open"}
    conform = ctx.get("conform") or {}
    render = ctx.get("render") or {}
    clip = conform.get("clip_path") or render.get("clip_path")
    if not clip or not os.path.isfile(clip):
        return {"wrote_file": False, "error": "no clip"}
    dest = Path(target)
    intake = Path(ctx["intake_dir"]).resolve()
    resolved = dest.resolve()
    if resolved == intake or intake in resolved.parents:
        return {"wrote_file": False, "error": "target is inside intake"}
    backup = Path(ctx["backup_dir"])
    backup.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        shutil.copy2(dest, backup / dest.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(clip, dest)
    return {"wrote_file": True, "stub": False, "target": str(dest), "backup": str(backup / dest.name)}


ALIASES = {
    "safety": {"builtin": builtin_safety},
    "render": {"stub": stub_render},
    "conform": {"stub": stub_conform, "ffmpeg": ffmpeg_conform},
    "swap": {"stub": stub_swap, "overwrite": overwrite_unopened},
    "runtime": {},
}


def resolve_hook(spec: str, kind: str):
    if spec in ALIASES[kind]:
        return ALIASES[kind][spec]
    if ":" not in spec:
        raise ValueError(f"unknown {kind} hook {spec}")
    module_name, func_name = spec.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, func_name)


def build_hooks(config: dict) -> dict:
    hooks = {}
    for name in ("safety", "render", "conform", "swap"):
        hooks[name] = resolve_hook(config["hooks"][name], name)
    runtime = config["hooks"].get("runtime_intake") or ""
    hooks["runtime_intake"] = resolve_hook(runtime, "runtime") if runtime else None
    return hooks


def render_page(config: dict, stream: str) -> str:
    html = PAGE.read_text(encoding="utf-8")
    return html.replace("__FIELDS__", _render_fields(config)).replace("__STREAM__", json.dumps(stream))


def _render_fields(config: dict) -> str:
    choices = config["choices"]
    max_chars = config["limits"]["max_chars"]
    chunks = [
        (
            '<label class="stack">Comment'
            f'<textarea name="text" maxlength="{max_chars}" required '
            'placeholder="What should happen next"></textarea></label>'
        ),
        _render_select("mode", "Mode", choices),
        _render_cast(choices),
    ]
    for key, label in (("tone", "Tone"), ("pace", "Pace"), ("camera", "Camera"), ("sound", "Sound")):
        chunks.append(_render_select(key, label, choices))
    return "\n".join(chunks)


def _render_select(key: str, label: str, choices: dict) -> str:
    default = choices[key]["default"]
    options = []
    for opt in choices[key]["options"]:
        selected = " selected" if opt["id"] == default else ""
        options.append(
            f'<option value="{html.escape(opt["id"])}"{selected}>{html.escape(opt["label"])}</option>'
        )
    return (
        f'<label class="stack">{html.escape(label)}'
        f'<select name="{key}">{"".join(options)}</select></label>'
    )


def _render_cast(choices: dict) -> str:
    boxes = []
    for opt in choices["cast"]["options"]:
        boxes.append(
            '<label class="hit">'
            f'<input type="checkbox" name="cast" value="{html.escape(opt["id"])}"> '
            f"{html.escape(opt['label'])}</label>"
        )
    return '<fieldset><legend>Cast</legend><div class="cast">' + "".join(boxes) + "</div></fieldset>"


def read_lsof(pid: int) -> str | None:
    try:
        proc = subprocess.run(
            ["lsof", "-p", str(pid), "-Fn"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout or ""


class Service:
    def __init__(
        self,
        config: dict,
        intake_dir: Path,
        *,
        hls_dir: Path | None = None,
        m3u_path: Path | None = None,
        vlc_pid: int = 0,
        lsof_text: str | None = None,
        lsof_file: Path | None = None,
        pause_file: Path | None = None,
    ):
        self.config = config
        self.intake = Path(intake_dir)
        self.intake.mkdir(parents=True, exist_ok=True)
        self.hls_dir = Path(hls_dir) if hls_dir else None
        self.m3u_path = Path(m3u_path) if m3u_path else None
        self.vlc_pid = int(vlc_pid or 0)
        self.lsof_text = lsof_text
        self.lsof_file = Path(lsof_file) if lsof_file else None
        self.pause_path = Path(pause_file) if pause_file else self.intake / "PAUSE"
        self.state_path = self.intake / "state.json"
        self.log_path = self.intake / "pipeline.log"
        self.hooks = build_hooks(config)
        self.now = lambda: datetime.now(timezone.utc)
        self.monotonic = time.monotonic
        self._lock = threading.Lock()
        self._rates: dict[str, list[float]] = {}

    def probe(self) -> dict:
        m3u = str(self.m3u_path) if self.m3u_path else None
        if not self.m3u_path or not self.m3u_path.is_file():
            return blank_probe("m3u is not configured", pid=self.vlc_pid, m3u=m3u)
        text = self._lsof_text()
        if text is None:
            if self.lsof_text is None and not self.lsof_file and not self.vlc_pid:
                return blank_probe("vlc pid is not configured", pid=self.vlc_pid, m3u=m3u)
            return blank_probe("lsof failed", pid=self.vlc_pid, m3u=m3u)
        slots = parse_m3u(self.m3u_path.read_text(encoding="utf-8"))
        return probe_slots(slots, parse_lsof(text), pid=self.vlc_pid, m3u=m3u)

    def _lsof_text(self) -> str | None:
        if self.lsof_text is not None:
            return self.lsof_text
        if self.lsof_file is not None:
            if not self.lsof_file.is_file():
                return None
            return self.lsof_file.read_text(encoding="utf-8")
        if not self.vlc_pid:
            return None
        return read_lsof(self.vlc_pid)

    def handle(self, method: str, path: str, body: bytes, ip: str):
        route = path.split("?", 1)[0]
        if method == "GET" and route in ("/", "/index.html"):
            page = render_page(self.config, "/stream.m3u8").encode("utf-8")
            headers = {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"}
            return 200, headers, page
        if method == "GET" and route == "/now-playing":
            return 200, JSON_HEADERS, _dump({"ok": True, "now_playing": self.probe()})
        if method == "GET" and route == "/health":
            return 200, JSON_HEADERS, _dump({"ok": True})
        if method == "POST" and route == "/comment":
            return self._post(body, ip)
        if method == "GET":
            media = self._media(route)
            if media is not None:
                ctype = MEDIA_TYPES.get(media.suffix.lower(), "application/octet-stream")
                return 200, {"Content-Type": ctype, "Cache-Control": "no-store"}, media.read_bytes()
        return 404, JSON_HEADERS, _dump({"ok": False, "error": "not found"})

    def _post(self, body: bytes, ip: str):
        if self._limited(ip):
            self._log(None, "rate", "rejected", "rate_limit")
            return 429, JSON_HEADERS, _dump({"ok": False, "error": "rate limit"})
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return 400, JSON_HEADERS, _dump({"ok": False, "error": "invalid json"})
        fields, err = parse_comment(payload, self.config)
        if err:
            return 400, JSON_HEADERS, _dump({"ok": False, "error": err})
        record = {
            "id": "c-" + uuid.uuid4().hex[:12],
            "received_at": self.now().isoformat(),
            "owner": OWNER,
            "text": fields["text"],
            "mode": fields["mode"],
            "cast": fields["cast"],
            "tone": fields["tone"],
            "pace": fields["pace"],
            "camera": fields["camera"],
            "sound": fields["sound"],
            "now_playing": self.probe(),
            "status": "queued",
            "hold_reasons": [],
            "prompt": None,
            "render": None,
            "conform": None,
            "swap": None,
            "stages": [],
        }
        self._log(record, "intake", "queued", "accepted")
        self._save(record)
        self._drain()
        return 200, JSON_HEADERS, _dump({"ok": True, "comment": self._load(record["id"])})

    def _limited(self, ip: str) -> bool:
        now = self.monotonic()
        window = self._rates.setdefault(ip, [])
        window[:] = [stamp for stamp in window if now - stamp < 60]
        cap = self.config["limits"]["per_ip_per_minute"]
        if len(window) >= cap:
            return True
        window.append(now)
        return False

    def _drain(self) -> None:
        if not self._lock.acquire(blocking=False):
            return
        try:
            while True:
                nxt = self._next_queued()
                if nxt is None:
                    return
                self._run(nxt)
        finally:
            self._lock.release()

    def _next_queued(self) -> dict | None:
        rows = []
        for path in self.intake.glob("c-*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("status") == "queued":
                rows.append(row)
        rows.sort(key=lambda row: (row.get("received_at") or "", row.get("id") or ""))
        return rows[0] if rows else None

    def _run(self, record: dict) -> None:
        reasons = self._call_safety(record)
        if reasons:
            self._finish(record, "held", reasons, "safety", "held", ",".join(reasons))
            return
        self._log(record, "safety", "pass", "pass")
        self._save(record)
        guard = self._guard(record)
        if guard == "deduped":
            self._finish(record, "deduped", [], "dedupe", "deduped", "deduped")
            return
        if guard:
            self._finish(record, "held", [guard], guard, "held", guard)
            return
        for stage in ("pause", "daily_kill_switch", "hourly_cap", "dedupe"):
            self._log(record, stage, "pass", "pass")
        self._reserve(record)
        prompt = build_prompt(
            record,
            self.config,
            record["now_playing"]["slot_before"],
            record["now_playing"]["first_swappable_slot"],
        )
        record["prompt"] = prompt
        self._log(record, "prompt", prompt["tag"], "built")
        self._save(record)
        self._note_render()
        rendered = self._call_hook("render", record)
        record["render"] = rendered if isinstance(rendered, dict) else {"error": "hook failed"}
        if record["render"].get("error"):
            self._finish(record, "held", ["render"], "render", "held", "render")
            return
        spend = "spent" if record["render"].get("spent") else "no-spend"
        self._log(record, "render", "stub" if record["render"].get("stub") else "pass", spend)
        conformed = self._call_hook("conform", record)
        record["conform"] = conformed if isinstance(conformed, dict) else {"error": "hook failed"}
        if record["conform"].get("error"):
            self._finish(record, "held", ["conform"], "conform", "held", "conform")
            return
        self._log(record, "conform", "stub" if record["conform"].get("stub") else "pass", "spec")
        swapped = self._call_hook("swap", record)
        record["swap"] = swapped if isinstance(swapped, dict) else {"error": "hook failed"}
        if record["swap"].get("wrote_file"):
            record["status"] = "swapped"
            self._log(record, "swap", "swapped", "wrote")
        elif record["swap"].get("stub"):
            record["status"] = "stubbed"
            self._log(record, "swap", "stub", "no-write")
        else:
            record["status"] = "held"
            record["hold_reasons"] = ["swap"]
            self._log(record, "swap", "held", record["swap"].get("error") or "swap")
        self._save(record)
        self._handoff(record)

    def _finish(self, record, status, reasons, stage, stage_status, detail) -> None:
        record["status"] = status
        record["hold_reasons"] = reasons
        self._log(record, stage, stage_status, detail)
        self._save(record)
        self._handoff(record)

    def _guard(self, record: dict) -> str | None:
        if self.pause_path.is_file():
            return "paused"
        now = record["now_playing"]
        if now.get("error"):
            return "now_playing_unavailable"
        if not now.get("first_swappable_slot"):
            return "no_slot_ahead"
        if not now.get("slot_before"):
            return "no_start_frame"
        state = self._state()
        renders = state["renders_at"]
        today = self.now().date()
        day_count = sum(1 for stamp in renders if datetime.fromisoformat(stamp).date() == today)
        if day_count >= self.config["limits"]["max_renders_per_day"]:
            return "daily_kill_switch"
        hour_count = sum(1 for stamp in renders if self._age(stamp) <= 3600)
        if hour_count >= self.config["limits"]["max_renders_per_hour"]:
            return "hourly_cap"
        seen = state["fingerprints"].get(fingerprint(record))
        if seen and seen != record["received_at"] and self._age(seen) <= self.config["limits"]["dedupe_window_seconds"]:
            return "deduped"
        return None

    def _reserve(self, record: dict) -> None:
        state = self._state()
        state["fingerprints"][fingerprint(record)] = record["received_at"]
        self._write_state(state)

    def _note_render(self) -> None:
        state = self._state()
        state["renders_at"].append(self.now().isoformat())
        self._write_state(state)

    def _state(self) -> dict:
        if not self.state_path.is_file():
            return {"renders_at": [], "fingerprints": {}}
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"renders_at": [], "fingerprints": {}}
        raw.setdefault("renders_at", [])
        raw.setdefault("fingerprints", {})
        window = self.config["limits"]["dedupe_window_seconds"]
        raw["fingerprints"] = {
            key: stamp for key, stamp in raw["fingerprints"].items() if self._age(stamp) <= window
        }
        raw["renders_at"] = [stamp for stamp in raw["renders_at"] if self._age(stamp) <= 172800]
        return raw

    def _write_state(self, state: dict) -> None:
        _write_json(self.state_path, state)

    def _age(self, stamp: str) -> float:
        then = datetime.fromisoformat(stamp)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        return (self.now() - then).total_seconds()

    def _ctx(self, record: dict) -> dict:
        return {
            "record": record,
            "config": self.config,
            "prompt": record.get("prompt"),
            "render": record.get("render"),
            "conform": record.get("conform"),
            "spec": self.config["conform"],
            "slot": (record.get("now_playing") or {}).get("first_swappable_slot"),
            "now": record.get("now_playing"),
            "backup_dir": str(self.intake / "backups" / record["id"]),
            "intake_dir": str(self.intake),
        }

    def _call_safety(self, record: dict) -> list[str]:
        try:
            result = self.hooks["safety"](self._ctx(record))
        except Exception:
            print("safety hook failed", flush=True)
            return ["safety_hook"]
        if not isinstance(result, dict):
            return ["safety_hook"]
        reasons = result.get("reasons") or []
        if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
            return ["safety_hook"]
        return reasons

    def _call_hook(self, name: str, record: dict) -> dict:
        try:
            result = self.hooks[name](self._ctx(record))
        except Exception:
            print(f"{name} hook failed", flush=True)
            return {"error": "hook failed"}
        if not isinstance(result, dict):
            return {"error": "hook failed"}
        return result

    def _handoff(self, record: dict) -> None:
        hook = self.hooks["runtime_intake"]
        if hook is None:
            self._log(record, "handoff", "skipped", "no-runtime")
            self._save(record)
            return
        try:
            result = hook({"record": record})
        except Exception:
            print("runtime intake hook failed", flush=True)
            self._log(record, "handoff", "error", "hook-failed")
            self._save(record)
            return
        record["handoff"] = result if isinstance(result, dict) else {"ok": True}
        self._log(record, "handoff", "pass", "handed")
        self._save(record)

    def _log(self, record, stage: str, status: str, detail: str) -> None:
        stamp = self.now().isoformat()
        comment_id = record["id"] if record else "-"
        safe_detail = " ".join(str(detail).split()) or "-"
        line = f"{stamp} comment={comment_id} stage={stage} status={status} detail={safe_detail}"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        print(line, flush=True)
        if record is not None:
            record.setdefault("stages", []).append(
                {"at": stamp, "stage": stage, "status": status, "detail": safe_detail}
            )

    def _save(self, record: dict) -> None:
        _write_json(self.intake / f"{record['id']}.json", record)

    def _load(self, comment_id: str) -> dict:
        return json.loads((self.intake / f"{comment_id}.json").read_text(encoding="utf-8"))

    def _media(self, route: str) -> Path | None:
        if self.hls_dir is None or route in ("/", "/index.html"):
            return None
        rel = route[len("/media"):] if route.startswith("/media/") else route
        rel = rel.lstrip("/")
        if not rel or rel.endswith("/"):
            return None
        root = self.hls_dir.resolve()
        cand = (root / rel).resolve()
        if not cand.is_file() or (cand != root and root not in cand.parents):
            return None
        return cand

    def bind(self, host: str, port: int) -> ThreadingHTTPServer:
        httpd = _Server((host, port), _handler())
        httpd.service = self
        return httpd


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    service: Service


def _handler():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def _dispatch(self, method: str) -> None:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length > 32768:
                self._send(413, JSON_HEADERS, _dump({"ok": False, "error": "too large"}))
                return
            body = self.rfile.read(length) if length else b""
            try:
                status, headers, payload = self.server.service.handle(
                    method, self.path, body, self.client_address[0]
                )
            except Exception as exc:
                print(f"request failed: {type(exc).__name__}", flush=True)
                status, headers, payload = 500, JSON_HEADERS, _dump({"ok": False, "error": "server error"})
            self._send(status, headers, payload)

        def _send(self, status: int, headers: dict, payload: bytes) -> None:
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt: str, *args) -> None:
            print("%s - %s" % (self.address_string(), fmt % args), flush=True)

    return Handler


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Serve the Thunder Trundle comment panel and intake.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50240)
    parser.add_argument("--hls-dir", default="")
    parser.add_argument("--intake-dir", required=True)
    parser.add_argument("--m3u", default="")
    parser.add_argument("--vlc-pid", type=int, default=0)
    parser.add_argument("--lsof-file", default="", help="Read this lsof output instead of running lsof.")
    parser.add_argument("--pause-file", default="")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    service = Service(
        config,
        Path(args.intake_dir),
        hls_dir=Path(args.hls_dir) if args.hls_dir else None,
        m3u_path=Path(args.m3u) if args.m3u else None,
        vlc_pid=args.vlc_pid,
        lsof_file=Path(args.lsof_file) if args.lsof_file else None,
        pause_file=Path(args.pause_file) if args.pause_file else None,
    )
    httpd = service.bind(args.bind, args.port)
    print(f"viewer comment panel http://{args.bind}:{args.port}/", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
