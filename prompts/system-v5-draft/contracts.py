"""Input contracts for next-clip assembly (D11, with D4 comment rows and D5 character meta).

Every validator is strict: unknown keys, identity keys (handles, authors, accounts) and image keys are hard errors."""
import datetime
import json
import pathlib
import re

import yaml

from adapters.v4_bridge import V4_CONFIG, layers_v4

IDENTITY_KEYS = {"handle", "user", "username", "user_id", "author", "account", "avatar", "contributor", "contributors",
                 "image", "img", "images", "media", "url"}
TIERS = set(layers_v4.TIER_LIFE)
CAST_ID = re.compile(r"^[A-Z0-9_]+$")
FIXED_THREAD_ID = re.compile(r"^FT\d", re.I)
DESCRIPTOR_MAX_WORDS = 12


class ContractError(ValueError):
    pass


def _static():
    return json.loads((V4_CONFIG / "static_v41.json").read_text())


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def _exact(obj, required, what, optional=()):
    if not isinstance(obj, dict):
        raise ContractError(f"{what}: expected an object, got {type(obj).__name__}")
    bad = IDENTITY_KEYS & set(_keys(obj))
    if bad:
        raise ContractError(f"{what}: identity/image keys are never allowed: {sorted(bad)}")
    missing = set(required) - set(obj)
    extra = set(obj) - set(required) - set(optional)
    if missing or extra:
        raise ContractError(f"{what}: missing {sorted(missing)}, unknown {sorted(extra)}")


def _iso(ts, what):
    try:
        return datetime.datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        raise ContractError(f"{what}: ts must be ISO-8601, got {ts!r}") from None


def _str(v, what):
    if not isinstance(v, str) or not v.strip():
        raise ContractError(f"{what}: expected non-empty text")


def channel_slug(channel):
    m = re.match(r"^Ch\s?(\d+)\s+([^/]+)", channel or "")
    if not m:
        raise ContractError(f"cannot derive a channel slug from {channel!r}")
    return f"{int(m.group(1)):02d}-" + re.sub(r"[^a-z0-9]+", "-", m.group(2).strip().lower()).strip("-")


def validate_comment_row(row):
    _exact(row, {"ts", "text"}, "comment row")
    _iso(row["ts"], "comment row")
    _str(row["text"], "comment row text")
    return row


def validate_locked_meta(lm):
    _exact(lm, {"show", "channel", "world_rules", "threads", "source"}, "locked_meta")
    if lm["source"] != "static_v41.json":
        raise ContractError("locked_meta.source must be static_v41.json")
    show = _static()["shows"].get(lm["show"])
    if show is None:
        raise ContractError(f"locked_meta.show {lm['show']!r} is not in static_v41.json")
    if lm["channel"] != show["channel"] or lm["world_rules"] != show["intangible"]["world_rules"]:
        raise ContractError("locked_meta differs from static_v41.json; locked meta is read-only")
    for t in lm["threads"]:
        _exact(t, {"id", "text", "tier", "locked"}, "locked_meta thread")
        if FIXED_THREAD_ID.match(str(t["id"])):
            raise ContractError(f"fixed thread {t['id']} stays OFF until Trundle turns it on (D8)")
        if t["tier"] not in ("LEGEND", "MARK") or t["locked"] is not True:
            raise ContractError("locked threads must be LEGEND or MARK and locked: true (D7)")
        _str(t["text"], "locked_meta thread text")
    return lm


def validate_still_meta(sm):
    _exact(sm, {"prev_clip_id", "still_path", "analyzer", "descriptors", "tier"}, "still_meta")
    if sm["analyzer"] != "stub":
        raise ContractError("still_meta.analyzer must be 'stub'; the pinned vision model is never called in v1 (D3)")
    if sm["tier"] != "FLASH":
        raise ContractError("still_meta.tier must be FLASH")
    if not isinstance(sm["descriptors"], list):
        raise ContractError("still_meta.descriptors must be a list")
    for d in sm["descriptors"]:
        _str(d, "still descriptor")
        if len(d.split()) > DESCRIPTOR_MAX_WORDS:
            raise ContractError(f"still descriptor longer than {DESCRIPTOR_MAX_WORDS} words: {d!r}")
    return sm


def validate_memory_item(item):
    _exact(item, {"text", "tier", "since_index"}, "memory item", optional={"episode", "season"})
    _str(item["text"], "memory item text")
    if item["tier"] not in TIERS:
        raise ContractError(f"memory tier must be one of {sorted(TIERS)}")
    return item


def validate_cast_meta(cast_id, cm):
    if not CAST_ID.match(str(cast_id)):
        raise ContractError(f"cast id {cast_id!r} must be UPPER_SNAKE")
    _exact(cm, {"name", "image_tag", "summon_count", "writein_level", "memories"}, f"character meta {cast_id}")
    _str(cm["name"], f"{cast_id}.name")
    if cm["name"].replace(" ", "_") != cast_id:
        raise ContractError(f"{cast_id}: name {cm['name']!r} does not match its cast id")
    if not (isinstance(cm["writein_level"], int) and 0 <= cm["writein_level"] <= 3):
        raise ContractError(f"{cast_id}.writein_level must be 0-3")
    if not (isinstance(cm["summon_count"], int) and cm["summon_count"] >= 0):
        raise ContractError(f"{cast_id}.summon_count must be >= 0")
    for item in cm["memories"]:
        validate_memory_item(item)
    return cm


def validate_character_meta(doc):
    _exact(doc, {"channel", "cast"}, "character meta")
    channel_slug(doc["channel"])
    if not isinstance(doc["cast"], dict):
        raise ContractError("character meta cast must be a mapping keyed by cast id")
    for cast_id, cm in doc["cast"].items():
        validate_cast_meta(cast_id, cm)
    return doc


def validate_trait_observation(row):
    _exact(row, {"ts", "cast_id", "clip_id", "trait", "tier", "source"}, "trait observation")
    _iso(row["ts"], "trait observation")
    if not CAST_ID.match(str(row["cast_id"])):
        raise ContractError("trait observation cast_id must be UPPER_SNAKE")
    _str(row["trait"], "trait observation trait")
    if row["tier"] not in TIERS:
        raise ContractError(f"trait observation tier must be one of {sorted(TIERS)}")
    return row


def read_jsonl(path):
    rows = []
    for n, line in enumerate(pathlib.Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ContractError(f"{path}:{n}: {e}") from None
    return rows


def load_character_meta(path):
    return validate_character_meta(yaml.safe_load(pathlib.Path(path).read_text()))


def load_inputs(clip_dir):
    clip_dir = pathlib.Path(clip_dir)
    return {
        "locked_meta": validate_locked_meta(json.loads((clip_dir / "locked_meta.json").read_text())),
        "still_meta": validate_still_meta(json.loads((clip_dir / "still_meta.json").read_text())),
    }
