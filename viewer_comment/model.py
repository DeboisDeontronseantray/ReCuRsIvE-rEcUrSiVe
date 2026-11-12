"""Pure comment, probe, and prompt rules. No sockets and no files."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from charmeta.name_guard import find_blocked_name_tokens

VIDEO_SUFFIXES = {".mp4", ".mkv", ".mov", ".m4v", ".webm"}
CHOICE_GROUPS = ("mode", "cast", "tone", "pace", "camera", "sound")
SINGLE_GROUPS = ("mode", "tone", "pace", "camera", "sound")
NAME_PAIR = re.compile(r"\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b")
DOXXING = (
    re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b"),
    re.compile(r"\b(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]*)\d{3}[\s.-]\d{4}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(
        r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,3}\s+"
        r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|way)\b",
        re.I,
    ),
    re.compile(r"https?://", re.I),
    re.compile(r"\bwww\.", re.I),
)


def load_config(path: Path | str) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config must be an object")
    choices = raw.get("choices")
    if not isinstance(choices, dict):
        raise ValueError("config choices missing")
    for group in CHOICE_GROUPS:
        block = choices.get(group)
        options = block.get("options") if isinstance(block, dict) else None
        if not isinstance(options, list) or not options:
            raise ValueError(f"config choices.{group} missing")
        ids = [opt.get("id") for opt in options]
        if any(not isinstance(item, str) or not item for item in ids):
            raise ValueError(f"config choices.{group} ids")
        if len(ids) != len(set(ids)):
            raise ValueError(f"config choices.{group} duplicate id")
        if group in SINGLE_GROUPS and block.get("default") not in ids:
            raise ValueError(f"config choices.{group} default")
    mode_ids = {opt["id"] for opt in choices["mode"]["options"]}
    if not {"extend", "mutate"} <= mode_ids:
        raise ValueError("config mode must include extend and mutate")
    limits = raw.get("limits")
    for key in (
        "min_chars",
        "max_chars",
        "per_ip_per_minute",
        "max_renders_per_hour",
        "max_renders_per_day",
        "dedupe_window_seconds",
    ):
        if not isinstance(limits, dict) or not isinstance(limits.get(key), int):
            raise ValueError(f"config limits.{key}")
    if limits["min_chars"] < 1 or limits["max_chars"] < limits["min_chars"]:
        raise ValueError("config comment length")
    conform = raw.get("conform")
    for key in ("width", "height", "fps", "frames"):
        if not isinstance(conform, dict) or not isinstance(conform.get(key), int):
            raise ValueError(f"config conform.{key}")
    for key in ("lufs", "true_peak_max_dbtp"):
        if not isinstance(conform.get(key), (int, float)):
            raise ValueError(f"config conform.{key}")
    safety = raw.get("safety")
    if not isinstance(safety, dict):
        raise ValueError("config safety missing")
    for key in ("hate", "sexual", "minors", "blocked_name_pairs", "allowed_name_pairs"):
        if not isinstance(safety.get(key), list):
            raise ValueError(f"config safety.{key}")
    hooks = raw.get("hooks")
    if not isinstance(hooks, dict):
        raise ValueError("config hooks missing")
    for key in ("safety", "render", "conform", "swap", "runtime_intake"):
        if not isinstance(hooks.get(key), str):
            raise ValueError(f"config hooks.{key}")
    return raw


def parse_m3u(text: str) -> list[dict]:
    slots = []
    duration = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            try:
                duration = float(line.split(":", 1)[1].split(",", 1)[0])
            except ValueError:
                duration = None
            continue
        if line.startswith("#"):
            continue
        slots.append({"index": len(slots), "path": line, "duration": duration})
        duration = None
    return slots


def parse_lsof(text: str) -> list[str]:
    found = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("n/") or (line.startswith("n") and len(line) > 2 and line[1] == "/"):
            found.append(line[1:])
            continue
        for token in line.split():
            if token.startswith("/") and Path(token).suffix.lower() in VIDEO_SUFFIXES:
                found.append(token)
    return list(dict.fromkeys(os.path.normpath(path) for path in found))


def probe_slots(slots: list[dict], open_paths: list[str], *, pid, m3u) -> dict:
    open_norm = [os.path.normpath(path) for path in open_paths]
    open_set = set(open_norm)
    matched = [slot["index"] for slot in slots if os.path.normpath(slot["path"]) in open_set]
    frontier = max(matched) if matched else None
    if frontier is None:
        current = None
        swappable = slots[0] if slots else None
        before = None
    else:
        current = slots[frontier]
        if frontier + 1 < len(slots):
            swappable = slots[frontier + 1]
            before = slots[frontier]
        else:
            swappable = None
            before = None
    earliest = slots[min(matched)] if matched else None
    span = None
    if matched:
        span = sum((slots[index].get("duration") or 0) for index in range(min(matched), max(matched) + 1))
    return {
        "vlc_pid": pid or None,
        "m3u": m3u,
        "open_files": open_norm,
        "open_slots": matched,
        "current_slot": current,
        "earliest_open_slot": earliest,
        "first_swappable_slot": swappable,
        "slot_before": before,
        "open_span_seconds": span,
        "slot_count": len(slots),
        "error": None,
    }


def blank_probe(error: str, *, pid, m3u) -> dict:
    return {
        "vlc_pid": pid or None,
        "m3u": m3u,
        "open_files": [],
        "open_slots": [],
        "current_slot": None,
        "earliest_open_slot": None,
        "first_swappable_slot": None,
        "slot_before": None,
        "open_span_seconds": None,
        "slot_count": 0,
        "error": error,
    }


def parse_comment(body, config: dict) -> tuple[dict | None, str | None]:
    if not isinstance(body, dict):
        return None, "comment must be an object"
    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        return None, "comment is empty"
    choices = config["choices"]
    fields = {"text": text.strip()}
    mode = body.get("mode", choices["mode"]["default"])
    if not isinstance(mode, str) or mode not in _ids(choices, "mode"):
        return None, "unknown mode"
    fields["mode"] = mode
    cast = body.get("cast", [])
    if not isinstance(cast, list) or not all(isinstance(item, str) for item in cast):
        return None, "unknown cast"
    known = [opt["id"] for opt in choices["cast"]["options"]]
    if any(item not in known for item in cast):
        return None, "unknown cast"
    picked = set(cast)
    fields["cast"] = [item for item in known if item in picked]
    for group in ("tone", "pace", "camera", "sound"):
        value = body.get(group, choices[group]["default"])
        if not isinstance(value, str) or value not in _ids(choices, group):
            return None, f"unknown {group}"
        fields[group] = value
    return fields, None


def _ids(choices: dict, group: str) -> set[str]:
    return {opt["id"] for opt in choices[group]["options"]}


def _terms_hit(text: str, terms: list) -> bool:
    folded = text.casefold()
    for term in terms:
        if not isinstance(term, str):
            continue
        token = term.casefold().strip()
        if not token:
            continue
        if " " in token:
            if token in folded:
                return True
            continue
        if re.search(rf"\b{re.escape(token)}\b", folded):
            return True
    return False


def _allow_names(config: dict) -> tuple[set[str], set[str]]:
    words: set[str] = set()
    pairs: set[str] = set()
    for opt in config["choices"]["cast"]["options"]:
        label = str(opt["label"]).casefold()
        pairs.add(label)
        words.update(label.split())
        words.update(str(opt["id"]).replace("-", " ").split())
    for pair in config["safety"].get("allowed_name_pairs") or []:
        if isinstance(pair, str) and pair.strip():
            folded = pair.casefold().strip()
            pairs.add(folded)
            words.update(folded.split())
    return words, pairs


def real_name_hit(text: str, config: dict) -> bool:
    if find_blocked_name_tokens(text):
        return True
    folded = text.casefold()
    for pair in config["safety"].get("blocked_name_pairs") or []:
        if isinstance(pair, str) and pair.casefold().strip() and pair.casefold().strip() in folded:
            return True
    words, pairs = _allow_names(config)
    for match in NAME_PAIR.finditer(text):
        pair = match.group(0).casefold()
        if pair in pairs:
            continue
        left, right = pair.split()
        if left in words or right in words:
            continue
        return True
    return False


def safety_reasons(text: str, config: dict) -> list[str]:
    reasons = []
    limits = config["limits"]
    if len(text) > limits["max_chars"] or len(text) < limits["min_chars"]:
        reasons.append("length")
    safety = config["safety"]
    for key in ("hate", "sexual", "minors"):
        if _terms_hit(text, safety.get(key) or []):
            reasons.append(key)
    if any(pattern.search(text) for pattern in DOXXING):
        reasons.append("doxxing")
    if real_name_hit(text, config):
        reasons.append("real_name")
    return reasons


def true_last_frame(path: str) -> str:
    return f"{path}.true-last.jpg"


def choice_labels(fields: dict, config: dict) -> dict:
    choices = config["choices"]

    def label(group: str, ident: str) -> str:
        for opt in choices[group]["options"]:
            if opt["id"] == ident:
                return opt["label"]
        return ident

    return {
        "cast": [label("cast", ident) for ident in fields["cast"]],
        "tone": label("tone", fields["tone"]),
        "pace": label("pace", fields["pace"]),
        "camera": label("camera", fields["camera"]),
        "sound": label("sound", fields["sound"]),
    }


def build_prompt(fields: dict, config: dict, before: dict, target: dict) -> dict:
    labels = choice_labels(fields, config)
    tag = "MUTATE" if fields["mode"] == "mutate" else "EXTEND"
    cast = ", ".join(labels["cast"]) if labels["cast"] else "the cast already in the slot"
    spoken = " ".join(fields["text"].split()).replace('"', "'")
    image = true_last_frame(before["path"])
    end = true_last_frame(target["path"]) if tag == "MUTATE" else None
    lines = [
        f"{tag}.",
        f"Cast: {cast}.",
        (
            f"Tone: {labels['tone']}. Pace: {labels['pace']}. "
            f"Camera: {labels['camera']}. Sound: {labels['sound']}."
        ),
        f'Viewer comment: "{spoken}".',
        "One continuous take. Nobody looks into the lens. No on-screen text.",
        "The start frame is the true last frame of the clip before this slot.",
    ]
    if tag == "MUTATE":
        lines.append(
            "The end frame is the replaced clip's true last frame. "
            "Later clips stay as they are. Forward re-render is a priced last resort."
        )
    else:
        lines.append("This clip uses a start frame only.")
    return {
        "tag": tag,
        "image_path": image,
        "last_frame_path": end,
        "source_before": before["path"],
        "source_slot": target["path"],
        "text": "\n".join(lines),
    }


def fingerprint(fields: dict) -> str:
    payload = {
        "text": " ".join(fields["text"].casefold().split()),
        "mode": fields["mode"],
        "cast": list(fields["cast"]),
        "tone": fields["tone"],
        "pace": fields["pace"],
        "camera": fields["camera"],
        "sound": fields["sound"],
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def ffmpeg_argv(src: str, dest: str, spec: dict) -> list[str]:
    video = f"scale={spec['width']}:{spec['height']},fps={spec['fps']}"
    audio = f"loudnorm=I={spec['lufs']}:TP={spec['true_peak_max_dbtp']}:LRA=11"
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-vf",
        video,
        "-frames:v",
        str(spec["frames"]),
        "-af",
        audio,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        str(dest),
    ]
