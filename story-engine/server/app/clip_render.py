"""Priced, approval-gated clip rendering. No automatic provider failover.

Exit codes: 0 ok, 1 FAILED, 2 validation, 3 needs priced yes, 4 Veo trial hard stop (cap or trial ended).
Veo dry signals are reported to pool-check (--mark-dry veo) when TT_POOL_CHECK is set.

Caps and the Veo trial end date come from ONE box-local settings file (no secrets): env TT_CAPS_FILE,
else out-of-scope/shared/spend/caps.json. CAPS_FALLBACK below is only the fail-closed fallback for a
missing or invalid file (today's values, 2026-11-02); cap numbers otherwise stay out of this code.

Veo cost reservation (2026-11-02, trundle 9:11 PM CT go): under a file lock on <ledger>.lock, a
'reserved' row with the estimate is appended before submit; the render then appends a final row with
the same reservation_id: 'success' (estimate), 'possible_charge' (failed or timed out after submit:
the reserved amount is kept) or 'failed' ($0, nothing was submitted). The trial total takes the last
row per reservation_id, so reserved and possible_charge amounts count toward the cap.

Vertex prices read 2026-11-02: the pricing page's '/ 1 count' is treated
as USD per second of generated video. Trial credits are logged separately.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid
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


def plan(req, ledger_path=None):
    quote = price(req)
    result = {"provider": req.provider, "tier": req.tier, "quote": asdict(quote),
            "duration_s": req.duration_s, "resolution": req.resolution, "audio": req.audio,
            "aspect_ratio": req.aspect_ratio, "reference_images": [str(p) for p in req.reference_images],
            "refs": len(req.reference_images), "start_image": str(req.start_image) if req.start_image else None,
            "out_path": str(req.out_path) if req.out_path else None,
            "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
            "key_set": ("GCP_VERTEX_API_KEY" in os.environ if req.provider == "veo" else
                        "XAI_API_KEY" in os.environ or Path(os.environ.get("XAI_KEY_FILE", "out-of-scope/private/keys/xai-render.key")).is_file()),
            "needs": "trundle's priced yes"}
    if req.provider == "veo":
        try:
            result["veo_trial_cap"] = veo_trial_status(quote.est_usd, _ledger_path(ledger_path))
        except VeoTrialCapError as exc:
            caps = load_caps()
            result["veo_trial_cap"] = {"cap_usd": caps["veo_trial_cap_usd"], "warn_usd": caps["veo_trial_warn_usd"],
                                       "status": "ledger_unreadable", "error": str(exc), "basis": VEO_TRIAL_BASIS,
                                       "caps_source": caps["source"]}
    return result


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


CAPS_DEFAULT_PATH = "out-of-scope/shared/spend/caps.json"
# Fail-closed fallback only, used when the caps file is missing or invalid (values as of 2026-11-02:
# xAI $50/month, warn $40, trundle 5:04 PM CT; Veo trial $150, warn $120, trundle 8:44 PM CT; trial ends 2027-01-04).
CAPS_FALLBACK = {"xai_month_cap_usd": 50.0, "xai_month_warn_usd": 40.0,
                 "veo_trial_cap_usd": 150.0, "veo_trial_warn_usd": 120.0, "veo_trial_end": "2027-01-04"}


def load_caps(path=None):
    """Caps from the settings file; any missing/invalid file or field gives the full fallback."""
    path = Path(path or os.environ.get("TT_CAPS_FILE") or CAPS_DEFAULT_PATH)
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        return dict(CAPS_FALLBACK, source="fallback (caps file missing)")
    except (OSError, ValueError):
        return dict(CAPS_FALLBACK, source="fallback (caps file unreadable)")
    caps = {}
    try:
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError
        for name in ("xai_month_cap_usd", "xai_month_warn_usd", "veo_trial_cap_usd", "veo_trial_warn_usd"):
            value = data[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError
            caps[name] = float(value)
        date.fromisoformat(data["veo_trial_end"])
        caps["veo_trial_end"] = data["veo_trial_end"]
        if caps["xai_month_warn_usd"] > caps["xai_month_cap_usd"] or caps["veo_trial_warn_usd"] > caps["veo_trial_cap_usd"]:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return dict(CAPS_FALLBACK, source="fallback (caps file invalid)")
    return dict(caps, source=str(path))


def _xai_cap(estimate, ledger):
    # spend's legacy cap can be higher; this lane always enforces the caps-file xAI monthly cap.
    cap = load_caps()["xai_month_cap_usd"]
    total, _ = spend.month_total_for_gate()
    month = datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m")
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            row = json.loads(line)
            if row.get("provider") == "xai_imagine" and row.get("ts_ct", "").startswith(month):
                total += float(row.get("cost_usd", 0))
    if total + estimate > cap:
        raise spend.SpendLimitError(f"xAI clip hard stop: monthly ${cap:g} cap")


# Veo trial spend cap. trundle, 2026-11-02 8:44 PM CT: "Let's make veo cap $150 for now".
# Separate from the xAI $50 gate: it counts only vertex_veo rows of the clip ledger render() writes,
# over the whole trial (the ledger is one append-only file, not per month; the trial ends 2027-01-04).
# Fallback aliases only; the live numbers come from load_caps().
VEO_TRIAL_CAP_USD = CAPS_FALLBACK["veo_trial_cap_usd"]
VEO_TRIAL_WARN_USD = CAPS_FALLBACK["veo_trial_warn_usd"]
VEO_TRIAL_BASIS = ("sum of cost_usd over all vertex_veo rows in the clip ledger, last row per reservation_id "
                   "(reserved and possible_charge count; whole trial, not per month)")


class VeoTrialCapError(RuntimeError):
    """Hard stop before a Veo render: the trial cap would be crossed, or the ledger can't be read."""


def veo_trial_spent(ledger):
    """USD spent or held on the Veo trial so far. A missing, unreadable or corrupt ledger fails closed."""
    return veo_trial_totals(ledger)["total"]


def veo_trial_totals(ledger):
    """Totals by final status; the last row per reservation_id wins (rows without one count alone)."""
    try:
        text = Path(ledger).read_text()
    except FileNotFoundError:
        raise VeoTrialCapError("Veo trial ledger missing; fail closed (create it empty with --init-ledger)") from None
    except (OSError, UnicodeDecodeError):
        raise VeoTrialCapError("Veo trial ledger unreadable; fail closed") from None
    held = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if not isinstance(row, dict):
            raise VeoTrialCapError(f"Veo trial ledger corrupt at line {number}; fail closed")
        if row.get("provider") != "vertex_veo":
            continue
        cost = row.get("cost_usd")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
            raise VeoTrialCapError(f"Veo trial ledger corrupt at line {number} (cost_usd); fail closed")
        rid = row.get("reservation_id")
        held[rid if isinstance(rid, str) and rid else f"line-{number}"] = (cost, row.get("status"))
    totals = {"total": round(sum(c for c, _ in held.values()), 4),
              "reserved": round(sum(c for c, st in held.values() if st == "reserved"), 4),
              "possible_charge": round(sum(c for c, st in held.values() if st == "possible_charge"), 4)}
    return totals


def veo_trial_status(estimate, ledger, caps=None):
    caps = caps or load_caps()
    cap_usd, warn_usd = caps["veo_trial_cap_usd"], caps["veo_trial_warn_usd"]
    totals = veo_trial_totals(ledger)
    spent = totals["total"]
    after = round(spent + estimate, 4)
    return {"cap_usd": cap_usd, "warn_usd": warn_usd, "spent_usd": spent,
            "reserved_usd": totals["reserved"], "possible_charge_usd": totals["possible_charge"],
            "this_est_usd": estimate, "after_usd": after,
            "left_usd": round(max(cap_usd - spent, 0), 4),
            "left_after_usd": round(cap_usd - after, 4),
            "status": "blocked" if after > cap_usd else "warn" if after >= warn_usd else "ok",
            "basis": VEO_TRIAL_BASIS, "caps_source": caps["source"]}


def _veo_trial_gate(estimate, ledger, caps=None):
    cap = veo_trial_status(estimate, ledger, caps)
    if cap["status"] == "blocked":
        raise VeoTrialCapError(f"Veo trial cap ${cap['cap_usd']:.2f}: spent ${cap['spent_usd']:.2f} + this render "
                               f"${estimate:.2f} = ${cap['after_usd']:.2f} would cross it (${cap['left_usd']:.2f} left)")
    if cap["status"] == "warn":
        print(f"clip_render WARNING: Veo trial spend ${cap['after_usd']:.2f} after this render is at or over the "
              f"${cap['warn_usd']:.0f} warn line; ${cap['left_after_usd']:.2f} of the ${cap['cap_usd']:.0f} cap left", file=sys.stderr)
    return cap


@contextlib.contextmanager
def _ledger_lock(ledger):
    """Exclusive flock on <ledger>.lock, so the cap check and the reservation are one step."""
    import fcntl
    try:
        fd = os.open(str(ledger) + ".lock", os.O_RDWR | os.O_CREAT, 0o600)
    except FileNotFoundError:
        raise VeoTrialCapError("Veo trial ledger missing; fail closed (create it empty with --init-ledger)") from None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _append_row(ledger, row):
    with open(ledger, "a") as stream:
        stream.write(json.dumps(row) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _veo_reserve(estimate, ledger, row, caps=None):
    """Cap check plus a 'reserved' row, under the ledger lock. Returns the reservation_id."""
    with _ledger_lock(ledger):
        _veo_trial_gate(estimate, ledger, caps)
        rid = uuid.uuid4().hex
        _append_row(ledger, dict(row, reservation_id=rid, reserved_usd=estimate, cost_usd=estimate, status="reserved"))
        return rid


# Veo dry signals (trundle 2026-11-02 8:56 PM CT "Ok what do we do"; MODEL-MAP "Detect dry").
VEO_TRIAL_END = date.fromisoformat(CAPS_FALLBACK["veo_trial_end"])  # fallback; live date from load_caps()
VEO_DRY_404 = "veo-404-model-not-found"
VEO_DRY_403 = "veo-403-permission-or-quota"
VEO_DRY_429 = "veo-429-resource-exhausted"
VEO_DRY_TRIAL_END = "veo-trial-ended"
VEO_DRY_CAP = "veo-cap-150-hit"


def veo_dry_signal(exc):
    """Return the pool-check dry reason for a Veo failure, or None (not a dry signal)."""
    if isinstance(exc, VeoTrialCapError):
        text = str(exc)
        if text.startswith("Veo trial ended"):
            return VEO_DRY_TRIAL_END
        if text.startswith("Veo trial cap"):
            return VEO_DRY_CAP
        return None  # a missing or corrupt ledger is a local fault, not a dry pool
    if not isinstance(exc, ClipRenderError):
        return None
    body = str(getattr(exc, "body", ""))
    status = getattr(exc, "status", None)
    if status == 429 or re.search(r"RESOURCE_EXHAUSTED", body):
        return VEO_DRY_429
    if status == 404:
        return VEO_DRY_404
    if status == 403 and re.search(r"PERMISSION_DENIED|permission|quota|billing|credit", body, re.I):
        return VEO_DRY_403
    return None


def report_veo_dry(reason, env=None):
    """Fail-soft: tell pool-check (path in TT_POOL_CHECK) that Veo is dry. Never sends bodies or keys."""
    env = os.environ if env is None else env
    tool = env.get("TT_POOL_CHECK", "")
    if not tool:
        return False
    try:
        result = subprocess.run([tool, "--mark-dry", "veo", "--reason", reason, "--bot", "clip_render"],
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        return result.returncode == 0
    except Exception:  # never let the report change the render's own error
        return False


def _veo_trial_open(today=None, caps=None):
    today = today or datetime.now(ZoneInfo("America/Chicago")).date()
    end = date.fromisoformat((caps or load_caps())["veo_trial_end"])
    if today > end:
        raise VeoTrialCapError(f"Veo trial ended {end.isoformat()}; no Veo renders")


def render(req, **kwargs):
    try:
        return _render(req, **kwargs)
    except (VeoTrialCapError, ClipRenderError) as exc:
        reason = veo_dry_signal(exc) if getattr(req, "provider", None) == "veo" else None
        if reason:
            report_veo_dry(reason)
        raise


def _render(req, *, approval, transport=None, sleep=time.sleep, poll_seconds=10, timeout_seconds=900, ledger_path=None):
    # This gate precedes validation, credential lookup, spend checks and transport.
    if not isinstance(approval, str) or not re.search(r"\$\s*\d+(?:\.\d+)?", approval):
        raise ApprovalRequired("needs trundle's priced yes")
    _validate(req, rendering=True)
    quote = price(req)
    ledger = _ledger_path(ledger_path)

    def ledger_row(**final):
        row = {"ts_ct": datetime.now(ZoneInfo("America/Chicago")).isoformat(timespec="seconds"),
               "provider": "vertex_veo" if req.provider == "veo" else "xai_imagine", "model": quote.model,
               "seconds": req.duration_s, "resolution": req.resolution, "audio": req.audio,
               "refs": len(req.reference_images), "start_image": bool(req.start_image), "est_usd": quote.est_usd,
               "cost_usd": 0, "cost_source": quote.basis, "status": "failed", "http_status": None,
               "operation": None, "clip_id": req.clip_id, "channel": req.channel, "show_id": req.show_id,
               "step": "clip-render", "bot": "story-bot",
               "key_ref": "env:GCP_VERTEX_API_KEY" if req.provider == "veo" else "file/env:XAI",
               "approved_by": " ".join(approval.split())[:200],
               "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest()}
        row.update(final)
        # Sanitize all caller/remote supplied metadata as well as the approval. The reserved row is
        # written before the key is loaded, so redact the Veo env key too.
        secret = key or (os.environ.get("GCP_VERTEX_API_KEY", "") if req.provider == "veo" else "")
        return {name: _redact(value, secret) if isinstance(value, str) else value for name, value in row.items()}

    key = ""
    reservation = None
    if req.provider == "veo":
        # Before the try: a refused render writes no ledger row and never creates a missing ledger.
        caps = load_caps()
        _veo_trial_open(caps=caps)
        reservation = _veo_reserve(quote.est_usd, ledger, ledger_row(), caps)
    operation = None
    http_status = None
    success = False
    submitted = False
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
            keyfile = Path(os.environ.get("XAI_KEY_FILE", "out-of-scope/private/keys/xai-render.key"))
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
            submitted = True  # from here a failure may still have been charged
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
            submitted = True
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
        final = {"http_status": http_status,
                 "operation": operation.rsplit("/", 1)[-1] if isinstance(operation, str) else None}
        if reservation:
            # Veo: finalize the reservation. A failure after submit keeps the reserved amount.
            status = "success" if success else "possible_charge" if submitted else "failed"
            final.update(reservation_id=reservation, reserved_usd=quote.est_usd, status=status,
                         cost_usd=0 if status == "failed" else quote.est_usd)
            with _ledger_lock(ledger):
                _append_row(ledger, ledger_row(**final))
        else:
            final.update(cost_usd=quote.est_usd if success else 0, status="success" if success else "failed")
            ledger.parent.mkdir(parents=True, exist_ok=True)
            with ledger.open("a") as stream:
                stream.write(json.dumps(ledger_row(**final)) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec")
    parser.add_argument("--provider")
    parser.add_argument("--tier")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved")
    parser.add_argument("--out")
    parser.add_argument("--init-ledger", action="store_true", help="create the clip ledger empty if absent (Veo trial cap reads it)")
    args = parser.parse_args(argv)
    if args.init_ledger:
        ledger = _ledger_path(None)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a"):
            pass
        print(f"clip ledger ready: {ledger}")
        return 0
    if not args.spec:
        parser.error("--spec is required")
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
    except VeoTrialCapError as exc:
        print(f"clip_render HARD STOP: {exc}", file=sys.stderr)
        return 4
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
