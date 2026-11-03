"""Priced, approval-gated clip rendering. No automatic provider failover.

Vertex prices read 2026-11-02: the pricing page's '/ 1 count' is treated
as USD per second of generated video. Trial credits are logged separately.
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass, fields
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

try:
    from app import spend
    _SpendLimitError = spend.SpendLimitError
except ImportError:  # vendored box copy without the story-engine app package: Veo only
    spend = None

    class _SpendLimitError(RuntimeError):
        pass

DEFAULT_CLIP_PROVIDER = "veo"
FALLBACK_CLIP_PROVIDER = "xai"
VEO_MODELS = {"lite": "veo-3.1-lite-generate-001", "fast": "veo-3.1-fast-generate-001"}
DEFAULT_VEO_TIER = "fast"  # Reference images are the identity lock.
VEO_MAX_REFS = 3
VEO_DURATIONS = (4, 6, 8)
VEO_PRICES = {
    "lite": {"720p": (0.03, 0.05), "1080p": (0.05, 0.08)},
    "fast": {"720p": (0.08, 0.10), "1080p": (0.10, 0.12), "4k": (0.25, 0.30)},
}
BLOCKED_PROVIDERS = {"fal", "fal.ai", "kie", "kie.ai", "replicate", "openrouter", "wavespeed", "runware", "apimart", "unifically", "apiyi", "yir", "yir.ai"}
ENGINE_ROOT = Path(__file__).resolve().parents[2]
VERTEX_ROOT = "https://us-central1-aiplatform.googleapis.com/v1/projects/1055647348526/locations/us-central1/publishers/google/models/"
XAI_ROOT = "https://api.x.ai/v1/videos"


class ClipRequestError(ValueError):
    pass


class ApprovalRequired(ValueError):
    pass


def _redact(value, key=""):
    text = str(value)
    if key:
        text = text.replace(key, "[redacted]")
        text = text.replace(urllib.parse.quote(key, safe=""), "[redacted]")
    return re.sub(r"(?i)(key=)[^\s&\"'<>]+", r"\1[redacted]", text)


class ClipRenderError(RuntimeError):
    def __init__(self, status, body, *, key=""):
        self.status = status
        self.body = _redact(body, key)[:1000]
        super().__init__(self.body)


@dataclass
class ClipRequest:
    prompt: str
    duration_s: int = 8
    resolution: str = "720p"
    audio: bool = False
    aspect_ratio: str = "16:9"
    reference_images: tuple = ()
    start_image: str | None = None
    negative_prompt: str | None = None
    out_path: str | None = None
    provider: str = DEFAULT_CLIP_PROVIDER
    tier: str = DEFAULT_VEO_TIER
    clip_id: str | None = None
    channel: str | None = None
    show_id: str | None = None

    @classmethod
    def from_dict(cls, spec):
        if not isinstance(spec, dict):
            raise ClipRequestError("spec must be an object")
        if set(spec) - {f.name for f in fields(cls)}:
            raise ClipRequestError("unknown spec keys")
        try:
            req = cls(**spec)
        except TypeError:
            raise ClipRequestError("spec requires prompt") from None
        _validate(req)
        return req


def _validate(req, *, rendering=False):
    if not isinstance(req.provider, str):
        raise ClipRequestError("provider must be exactly veo or xai")
    if req.provider in BLOCKED_PROVIDERS:
        raise ClipRequestError("blocked by CURRENT-RULES L60 (paid resellers held)")
    if req.provider not in ("veo", "xai"):
        raise ClipRequestError("provider must be exactly veo or xai")
    if not isinstance(req.prompt, str) or not req.prompt.strip():
        raise ClipRequestError("prompt must be non-empty")
    if not isinstance(req.tier, str) or req.tier not in VEO_MODELS:
        raise ClipRequestError("tier must be lite or fast")
    if not isinstance(req.resolution, str):
        raise ClipRequestError("resolution must be a string")
    if not isinstance(req.aspect_ratio, str) or not req.aspect_ratio.strip():
        raise ClipRequestError("aspect_ratio must be a non-empty string")
    if req.negative_prompt is not None and not isinstance(req.negative_prompt, str):
        raise ClipRequestError("negative_prompt must be a string")
    if req.out_path is not None and not isinstance(req.out_path, (str, Path)):
        raise ClipRequestError("out_path must be a path")
    if req.start_image is not None and not isinstance(req.start_image, (str, Path)):
        raise ClipRequestError("start_image must be an image path")
    for value in (req.clip_id, req.channel, req.show_id):
        if value is not None and not isinstance(value, (str, int)):
            raise ClipRequestError("clip_id, channel and show_id must be strings or integers")
    if not isinstance(req.audio, bool):
        raise ClipRequestError("audio must be boolean")
    if not isinstance(req.reference_images, (tuple, list)):
        raise ClipRequestError("reference_images must be a list of image paths")
    if req.provider == "veo":
        if type(req.duration_s) is not int or req.duration_s not in VEO_DURATIONS:
            raise ClipRequestError("Veo duration must be 4, 6 or 8 seconds")
        if req.resolution not in VEO_PRICES[req.tier]:
            raise ClipRequestError("unsupported resolution for Veo tier")
        if len(req.reference_images) > VEO_MAX_REFS:
            raise ClipRequestError("Veo max 3 reference images; never drop identity references")
        if req.reference_images and req.tier == "lite":
            raise ClipRequestError("lite has no documented reference-image support; use tier fast")
        if req.reference_images and req.start_image:
            raise ClipRequestError("Veo reference images with start_image is an unverified combination; refuse")
    else:
        if type(req.duration_s) is not int or not 1 <= req.duration_s <= 15:
            raise ClipRequestError("xAI duration must be 1 to 15 seconds")
        if req.resolution not in ("480p", "720p"):
            raise ClipRequestError("unsupported xAI resolution")
        if req.audio or req.negative_prompt:
            raise ClipRequestError("xAI audio and negative_prompt controls are unverified")
    for path in list(req.reference_images) + ([req.start_image] if req.start_image else []):
        if not isinstance(path, (str, Path)) or Path(path).suffix.lower() not in (".png", ".jpg", ".jpeg") or not Path(path).is_file():
            raise ClipRequestError("image must be an existing .png/.jpg/.jpeg file")
    if rendering and not req.out_path:
        raise ClipRequestError("out_path is required for render")
    if req.out_path:
        out = Path(req.out_path)
        if "masters" in out.resolve().parts or "masters" in out.parts:
            raise ClipRequestError("masters stay pure; choose a different out_path")
        if out.exists() or out.is_symlink():
            raise ClipRequestError("out_path exists; never overwrite")


@dataclass(frozen=True)
class Quote:
    provider: str
    model: str
    seconds: int
    usd_per_second: float
    est_usd: float
    basis: str


def price(req):
    _validate(req)
    if req.provider == "veo":
        rate = VEO_PRICES[req.tier][req.resolution][int(req.audio)]
        return Quote("veo", VEO_MODELS[req.tier], req.duration_s, rate, round(req.duration_s * rate, 4), "estimate: Vertex list price 2026-11-02, trial credit")
    rate = 0.02 if req.tier == "lite" else 0.08
    extra = 0 if req.tier == "lite" else 0.01 * len(req.reference_images)
    return Quote("xai", "grok-imagine-video-1.5" + ("-lite" if req.tier == "lite" else ""), req.duration_s, rate, round(req.duration_s * rate + extra, 4), "estimate: xAI rate")


def plan(req):
    quote = price(req)
    return {"provider": req.provider, "tier": req.tier, "quote": asdict(quote),
            "duration_s": req.duration_s, "resolution": req.resolution, "audio": req.audio,
            "aspect_ratio": req.aspect_ratio, "reference_images": [str(p) for p in req.reference_images],
            "refs": len(req.reference_images), "start_image": str(req.start_image) if req.start_image else None,
            "out_path": str(req.out_path) if req.out_path else None,
            "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
            "key_set": ("GCP_VERTEX_API_KEY" in os.environ if req.provider == "veo" else
                        "XAI_API_KEY" in os.environ or Path(os.environ.get("XAI_KEY_FILE", "/workspace/private/keys/xai-render.key")).is_file()),
            "needs": "trundle's priced yes"}


def _transport(method, url, body, *, headers=None, binary=False):
    request = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
            return response.status, data if binary else data.decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def _image(path):
    return {"bytesBase64Encoded": base64.b64encode(Path(path).read_bytes()).decode(),
            "mimeType": "image/png" if Path(path).suffix.lower() == ".png" else "image/jpeg"}


def _ledger_path(override):
    return Path(override or os.environ.get("TT_CLIP_LEDGER") or ENGINE_ROOT / "data/spend/clip-ledger.jsonl")


def _xai_cap(estimate, ledger):
    # spend's legacy cap can be higher; this lane always enforces $50/month.
    total, _ = spend.month_total_for_gate()
    month = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m")
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            row = json.loads(line)
            if row.get("provider") == "xai_imagine" and row.get("ts_ct", "").startswith(month):
                total += float(row.get("cost_usd", 0))
    if total + estimate > 50:
        raise spend.SpendLimitError("xAI clip hard stop: monthly $50 cap")


def render(req, *, approval, transport=None, sleep=time.sleep, poll_seconds=10, timeout_seconds=900, ledger_path=None):
    # This gate precedes validation, credential lookup, spend checks and transport.
    if not isinstance(approval, str) or not re.search(r"\$\s*\d+(?:\.\d+)?", approval):
        raise ApprovalRequired("needs trundle's priced yes")
    _validate(req, rendering=True)
    quote = price(req)
    ledger = _ledger_path(ledger_path)
    key = ""
    operation = None
    http_status = None
    success = False
    started = time.monotonic()
    deadline = started + timeout_seconds
    elapsed = 0.0
    try:
        if req.provider == "veo":
            key = os.environ.get("GCP_VERTEX_API_KEY", "")
        else:
            if spend is None:
                raise ClipRequestError("xAI route needs the story-engine app.spend gate; not available here")
            spend.check_can_spend(quote.est_usd)
            _xai_cap(quote.est_usd, ledger)
            keyfile = Path(os.environ.get("XAI_KEY_FILE", "/workspace/private/keys/xai-render.key"))
            key = (keyfile.read_text().strip() if keyfile.is_file() else "") or os.environ.get("XAI_API_KEY", "")
        if not key:
            raise ClipRequestError("missing GCP_VERTEX_API_KEY" if req.provider == "veo" else "missing xAI key (XAI_KEY_FILE or XAI_API_KEY)")
        headers = {"Authorization": "Bearer " + key} if req.provider == "xai" else {}

        def invoke(method, url, body, *, binary=False):
            nonlocal http_status
            if transport is not None:
                http_status, raw = transport(method, url, body)
            else:
                http_status, raw = _transport(method, url, body, headers=headers if url.startswith(XAI_ROOT + "/") else {}, binary=binary)
            if not 200 <= http_status < 300:
                raise ClipRenderError(http_status, raw, key=key)
            if binary:
                return raw if isinstance(raw, bytes) else raw.encode("latin1")
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ClipRenderError(http_status, "invalid response object", key=key)
            if data.get("error") or re.search(r"RESOURCE_EXHAUSTED|quota", str(data.get("code", "")) + str(data.get("message", "")), re.I):
                raise ClipRenderError(http_status, raw, key=key)
            return data

        if req.provider == "veo":
            root = VERTEX_ROOT + quote.model
            query = "?key=" + urllib.parse.quote(key, safe="")
            instance = {"prompt": req.prompt}
            if req.reference_images:
                instance["referenceImages"] = [{"image": _image(p), "referenceType": "asset"} for p in req.reference_images]
            if req.start_image:
                instance["image"] = _image(req.start_image)
            params = {"durationSeconds": req.duration_s, "sampleCount": 1, "generateAudio": req.audio,
                      "resolution": req.resolution, "aspectRatio": req.aspect_ratio}
            if req.negative_prompt:
                params["negativePrompt"] = req.negative_prompt
            data = invoke("POST", root + ":predictLongRunning" + query, {"instances": [instance], "parameters": params})
            operation = data.get("name")
        else:
            def ximage(p):
                img = _image(p)
                return {"url": "data:" + img["mimeType"] + ";base64," + img["bytesBase64Encoded"]}
            body = {"model": quote.model, "prompt": req.prompt, "duration": req.duration_s, "resolution": req.resolution}
            if req.reference_images:
                body["reference_images"] = [ximage(p) for p in req.reference_images]
            if req.start_image:
                body["image"] = ximage(req.start_image)
            else:
                body["aspect_ratio"] = req.aspect_ratio
            data = invoke("POST", XAI_ROOT + "/generations", body)
            operation = data.get("request_id")
        if not isinstance(operation, str) or not operation:
            raise ClipRenderError(http_status, "submit response missing operation/request_id")
        while True:
            remaining = min(deadline - time.monotonic(), timeout_seconds - elapsed)
            if remaining <= 0:
                raise ClipRenderError(http_status, "poll timeout")
            delay = min(max(poll_seconds, 0), remaining)
            sleep(delay)
            elapsed += delay
            if req.provider == "veo":
                data = invoke("POST", root + ":fetchPredictOperation" + query, {"operationName": operation})
                if data.get("done"):
                    response = data.get("response") or {}
                    if response.get("raiMediaFilteredCount", 0) or not response.get("videos"):
                        raise ClipRenderError(http_status, "filtered or empty output: " + json.dumps(response.get("raiMediaFilteredReasons", [])), key=key)
                    video = base64.b64decode(response["videos"][0]["bytesBase64Encoded"], validate=True)
                    break
            else:
                data = invoke("GET", XAI_ROOT + "/" + urllib.parse.quote(operation, safe=""), None)
                if data.get("status") in ("failed", "expired") or data.get("code"):
                    raise ClipRenderError(http_status, json.dumps(data), key=key)
                if data.get("status") == "done":
                    url = (data.get("video") or {}).get("url")
                    if not url or urllib.parse.urlsplit(url).scheme != "https":
                        raise ClipRenderError(http_status, "empty output or invalid video URL")
                    video = invoke("GET", url, None, binary=True)
                    break
        if not video:
            raise ClipRenderError(http_status, "empty video output")
        out = Path(req.out_path)
        _validate(req, rendering=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".clip-", dir=out.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(video)
                stream.flush()
                os.fsync(stream.fileno())
            if out.exists() or out.is_symlink():
                raise ClipRequestError("out_path exists; never overwrite")
            os.replace(tmp, out)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        success = True
        return {"out_path": str(out), "est_usd": quote.est_usd, "provider": req.provider}
    except (ClipRequestError, _SpendLimitError):
        raise
    except Exception as exc:
        raise ClipRenderError(getattr(exc, "status", http_status), str(exc), key=key) from None
    finally:
        row = {"ts_ct": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
               "provider": "vertex_veo" if req.provider == "veo" else "xai_imagine", "model": quote.model,
               "seconds": req.duration_s, "resolution": req.resolution, "audio": req.audio,
               "refs": len(req.reference_images), "start_image": bool(req.start_image), "est_usd": quote.est_usd,
               "cost_usd": quote.est_usd if success else 0, "cost_source": quote.basis,
               "status": "success" if success else "failed", "http_status": http_status,
               "operation": operation.rsplit("/", 1)[-1] if isinstance(operation, str) else None,
               "clip_id": req.clip_id, "channel": req.channel, "show_id": req.show_id,
               "step": "clip-render", "bot": "story-bot",
               "key_ref": "env:GCP_VERTEX_API_KEY" if req.provider == "veo" else "file/env:XAI",
               "approved_by": " ".join(_redact(approval, key).split())[:200],
               "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest()}
        # Sanitize all caller/remote supplied metadata as well as the approval.
        row = {name: _redact(value, key) if isinstance(value, str) else value for name, value in row.items()}
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a") as stream:
            stream.write(json.dumps(row) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--provider")
    parser.add_argument("--tier")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    provider = args.provider or DEFAULT_CLIP_PROVIDER
    try:
        spec = json.loads(Path(args.spec).read_text())
        if not isinstance(spec, dict):
            raise ClipRequestError("spec must be an object")
        for field, value in (("provider", args.provider), ("tier", args.tier), ("out_path", args.out)):
            if value is not None:
                spec[field] = value
        req = ClipRequest.from_dict(spec)
        provider = req.provider
        preview = plan(req)
        if args.dry_run:
            print(json.dumps(preview, indent=2))
            return 0
        if not args.approved or not re.search(r"\$\s*\d+(?:\.\d+)?", args.approved):
            print(json.dumps(preview, indent=2))
            raise ApprovalRequired("needs trundle's priced yes")
        print(json.dumps(render(req, approval=args.approved)))
        return 0
    except ApprovalRequired:
        print("needs trundle's priced yes", file=sys.stderr)
        return 3
    except (ClipRequestError, OSError, ValueError) as exc:
        # Validation messages never include spec values or file contents.
        message = str(exc) if isinstance(exc, ClipRequestError) else "invalid spec or file I/O failure"
        print("clip_render validation: " + message, file=sys.stderr)
        return 2
    except (ClipRenderError, _SpendLimitError) as exc:
        print(f"clip_render FAILED http={getattr(exc, 'status', None)} provider={provider if provider in ('veo', 'xai') else 'invalid'} error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
