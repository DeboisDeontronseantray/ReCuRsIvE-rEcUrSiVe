#!/usr/bin/env python3
"""Assemble a render prompt from layers 1-6 (thunder-trundle/prompts/LAYERS.md). Owner: Director (spec). Code drafted by Story Bot, Oct 28 2026.
Home-only: builds text and JSON only. No rendering, no API calls, nothing aired.

Usage: assemble_prompt.py <segments/BI-12.yaml> [--mutations FILE.json | --mutations-json '[...]'] [--kind show|commercial]
Mutation item: {"prompt_id": "cp-...", "fields": {"action": "...", ...}, "screen_inserts": [{ref, surface, in, out, loop, treatment}]}
(top-level keys other than prompt_id/fields/screen_inserts are treated as fields too)."""
import argparse, base64, hashlib, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROMPTS = os.environ.get("TT_PROMPTS", "/workspace/thunder-trundle/prompts")
POLICY = os.path.join(ROOT, "rules", "queue-policy.yaml")
CHANNEL_DIRS = {4: "04-military-boutique", "4": "04-military-boutique"}
# 2026-10-28 12:45 CT Director spec: channel lookup; folders written by Director (prompts/<NN-slug>/_channel.md)
for _n, _d in {2: "02-news", 4: "04-military-boutique", 6: "06-shopping", 8: "08-sitcom", 10: "10-action", 12: "12-90s", 14: "14-music"}.items():
    CHANNEL_DIRS[_n] = _d; CHANNEL_DIRS[str(_n)] = _d; CHANNEL_DIRS[_d] = _d


class UnknownChannelError(LookupError):
    pass


def channel_dir(channel):
    """Unknown or missing channel raises; never falls back to Ch 4."""
    d = CHANNEL_DIRS.get(channel if not isinstance(channel, str) or not channel.isdigit() else int(channel))
    if d is None: d = CHANNEL_DIRS.get(channel)
    if d is None: raise UnknownChannelError(f"unknown channel {channel!r}; no fallback to Ch 4")
    p = os.path.join(PROMPTS, d, "_channel.md")
    if not os.path.isfile(p): raise UnknownChannelError(f"channel {channel!r} has no {p}; no fallback to Ch 4")
    return d
LAYER_NAMES = ["global", "channel", "format", "show_or_ad", "shot", "commenter"]
# names a commenter might use to reach layers 1-3 (always dropped + reported)
PROTECTED = {"global", "channel", "format", "system_wrappers", "constraints", "hard_limits", "rules",
             "style", "safety", "home_only", "tv_safe", "show_or_ad", "wrapper", "prompt", "camera_style"}
# The owner's real first name is base64 so the literal never sits in the source; it is decoded only to block it.
CREATOR_NAME = base64.b64decode("ZHJldw==").decode()
NEVER_WORDS = re.compile(rf"\b{re.escape(CREATOR_NAME)}\b", re.I)

sys.path.insert(0, HERE)
import resolve_embed  # noqa: E402


def sha(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()


def read(p):
    with open(p, encoding="utf-8") as f: return f.read().strip()


def commenter_allowed():
    with open(POLICY) as f: pol = yaml.safe_load(f) or {}
    return list((pol.get("prompt_layers") or {}).get("commenter_may_set") or [])


def resolve(ref):
    """-> (row dict, None) or (None, error). Uses resolve_embed's own lookup (clean masters only)."""
    try:
        for r in reversed(resolve_embed.find(ref)):
            p = resolve_embed.clean_path(r)
            if p:
                return {"global_no": r.get("global_no"), "tag": r.get("tag"), "clean_master": p}, None
        return None, f"{ref} has no clean untagged master on disk"
    except SystemExit as e:
        return None, str(e.code)
    except (ValueError, TypeError) as e:
        return None, f"bad ref {ref!r}: {e}"


def ref_str(ref):
    if isinstance(ref, dict): return f"{ref.get('lineage')}:{ref.get('gen')}"
    return str(ref)


SCREEN_SURFACE = {  # per-channel embed surface; Director Oct 28 12:10 PM CT
    4: "a powered-off CRT: dark grey glass with a faint reflection, nothing displayed",
}
DEFAULT_SURFACE = "a plain flat evenly lit green screen, nothing displayed"


def screen_line(si, channel=None):
    look = SCREEN_SURFACE.get(channel, DEFAULT_SURFACE)
    return (f"The {si.get('surface', 'screen')} is {look}, unobstructed "
            f"(an older clip is composited in later).")


# ---- Lock library + ordered shot body (Director 12:26 PM CT, CNB 12:27 PM CT; Story Bot add-only) ----
LOCKS_DIR = os.environ.get("TT_LOCKS", os.path.join(PROMPTS, "locks"))
LOCK_TYPES = ("CHR", "LOC", "LOOK", "PRP", "WAR")
MAX_REFS_PER_CHR, MAX_REFS_TOTAL, MAX_CLIP_S = 2, 14, 15
BODY_ORDER = ["camera", "look", "location", "characters", "action", "in_scene_text", "physics", "audio", "sfx", "rules", "constraints"]


def load_locks():
    out = {}
    for dp, _, fs in os.walk(LOCKS_DIR):
        for f in fs:
            if f.endswith(".yaml"):
                with open(os.path.join(dp, f)) as fh: d = yaml.safe_load(fh) or {}
                if d.get("id"): out[d["id"]] = d
    return out


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def policy_locks():
    with open(POLICY) as f: pol = yaml.safe_load(f) or {}
    return pol.get("prompt_layers_locks") or {}


def prev_last_frame(sidecar_path, sc):
    sid = sc.get("shot_id", "")
    m = re.match(r"(.*?)(\d+)$", sid)
    if not m: return None
    prev = os.path.join(os.path.dirname(sidecar_path), f"{m.group(1)}{int(m.group(2)) - 1:0{len(m.group(2))}d}.yaml")
    if not os.path.exists(prev): return None
    with open(prev) as f: ps = yaml.safe_load(f) or {}
    kf = ps.get("keyframes") or {}
    return kf.get("last_frame_clean_extract") or kf.get("last_frame")


def load_mutations(a):
    if a.mutations: 
        with open(a.mutations) as f: m = json.load(f)
    elif a.mutations_json: m = json.loads(a.mutations_json)
    else: return []
    return m if isinstance(m, list) else [m]


def assemble(sidecar_path, mutations=None, kind=None, dense=False):
    with open(sidecar_path) as f: sc = yaml.safe_load(f) or {}
    mutations = mutations or []
    show = sc.get("show") or "black-ice"
    chan_dir = channel_dir(sc.get("channel", 4))  # 2026-10-28: raises on unknown, no Ch 4 fallback
    kind = kind or (sc.get("system_wrappers") or {}).get("segment_kind") or "show"
    paths = {"global": os.path.join(PROMPTS, "_global.md"),
             "channel": os.path.join(PROMPTS, chan_dir, "_channel.md"),
             "format": os.path.join(PROMPTS, chan_dir, "_commercial.md" if kind == "commercial" else "_show.md"),
             "show_or_ad": os.path.join(PROMPTS, chan_dir, show, "_wrapper.md")}
    layers = {}
    for k, p in paths.items():
        txt = read(p)
        layers[k] = re.sub(r"<!--.*?-->\s*", "", txt, flags=re.S).strip()  # strip authoring comment

    if sc.get("locks"):
        return assemble_locked(sidecar_path, sc, mutations, kind, layers, paths, dense=dense)
    errors, embeds, notes = [], [], []
    # layer 5: shot
    shot = [f"[Shot {sc.get('shot_id', '?')}] " + (sc.get("prompt") or "").strip()]
    if sc.get("in_scene_text"):
        shot.append("[In-scene text] Render exactly these words and nothing else: "
                    + "; ".join(f'"{t}"' for t in sc["in_scene_text"]))
    for si in sc.get("screen_inserts") or []:
        row, err = resolve(ref_str(si.get("ref")))
        if err:
            errors.append(f"system embed {si.get('ref')}: {err}")
            continue
        embeds.append({"source": "system", "prompt_id": None, **si, "ref": ref_str(si.get("ref")), **row, "status": "resolved"})
        shot.append("[Screen] " + screen_line(si, sc.get("channel", 4)))
    layers["shot"] = "\n".join(shot)

    # layer 6: commenter
    allowed = set(commenter_allowed())
    applied, dropped, cblock, pids = [], [], [], []
    for m in mutations:
        pid = m.get("prompt_id") or "unknown"
        pids.append(pid)
        fields = dict(m.get("fields") or {})
        fields.update({k: v for k, v in m.items() if k not in ("prompt_id", "fields", "screen_inserts")})
        for k, v in fields.items():
            if k in PROTECTED or k not in allowed:
                dropped.append({"prompt_id": pid, "field": k, "reason": "protected layer 1-3/format" if k in PROTECTED else "not in commenter_may_set"})
                continue
            if NEVER_WORDS.search(json.dumps(v)):
                dropped.append({"prompt_id": pid, "field": k, "reason": "hard limit: name never on screen/spoken"}); continue
            if k == "in_scene_text":
                v = v if isinstance(v, list) else [v]
                cblock.append("In-scene text (overrides the shot's no-text line for these words only), render exactly: "
                              + "; ".join(f'"{t}"' for t in v))
            elif k != "screen_inserts":
                cblock.append(f"{k.replace('_', ' ').capitalize()}: {v if isinstance(v, str) else json.dumps(v)}")
            applied.append({"prompt_id": pid, "field": k})
        sis = (m.get("screen_inserts") or []) + (fields.get("screen_inserts") or [] if "screen_inserts" in allowed else [])
        if sis and "screen_inserts" not in allowed:
            dropped.append({"prompt_id": pid, "field": "screen_inserts", "reason": "not in commenter_may_set"}); sis = []
        for si in sis:
            r = ref_str(si.get("ref"))
            row, err = resolve(r)
            if err:
                embeds.append({"source": "commenter", "prompt_id": pid, **si, "ref": r, "status": "held", "reason": err})
                notes.append(f"commenter embed {r} from {pid} held (not deleted): {err}")
                continue
            embeds.append({"source": "commenter", "prompt_id": pid, **si, "ref": r, **row, "status": "resolved"})
            cblock.append("[Screen] " + screen_line(si, sc.get("channel", 4)))
            if not any(a["prompt_id"] == pid and a["field"] == "screen_inserts" for a in applied):
                applied.append({"prompt_id": pid, "field": "screen_inserts"})
    if cblock:
        layers["commenter"] = ("[Commenter changes; may change show/shot details only, never the Global, Channel or Format rules above] "
                               + "\n".join(cblock))

    final = "\n\n".join(layers[k] for k in LAYER_NAMES if layers.get(k))
    out = {"shot_id": sc.get("shot_id"), "sidecar": os.path.abspath(sidecar_path), "segment_kind": kind,
           "ok": not errors, "errors": errors, "final_prompt": final,
           "generation_note": "Screens with embeds are generated per channel surface (Ch 4: powered-off dark CRT, else plain green); CNB composites the CLEAN master in post (ffmpeg corner-pin/track). Corner tag/lower-thirds are post overlays.",
           "embeds": embeds, "commenter_applied": applied, "commenter_dropped": dropped, "notes": notes,
           "commenter_prompt_ids": pids,
           "prompt_layers": {k: sha(layers[k]) for k in LAYER_NAMES if layers.get(k)},
           "layer_files": paths, "home_only": True}
    return out


def assemble_locked(sidecar_path, sc, mutations, kind, layers, paths, dense=False):
    """Ordered body: camera first ... constraints last; wrappers sit between sfx and constraints as [Rules]."""
    locks, pol = load_locks(), policy_locks()
    allowed = set(commenter_allowed()) | set(pol.get("commenter_may_set_also") or [])
    errors, embeds, notes, warnings = [], [], [], []
    bl = dict(sc.get("blocks") or {})
    sel = {k: list(v or []) for k, v in (sc.get("locks") or {}).items()}
    applied, dropped, pids, cparts = [], [], [], []
    over = {}
    for m in mutations:
        pid = m.get("prompt_id") or "unknown"; pids.append(pid)
        fields = dict(m.get("fields") or {})
        fields.update({k: v for k, v in m.items() if k not in ("prompt_id", "fields", "screen_inserts")})
        if m.get("screen_inserts"): fields["screen_inserts"] = m["screen_inserts"]
        for k, v in fields.items():
            if k in ("new_lock", "lock", "locks", "create_lock"):
                vs = v if isinstance(v, list) else [v]
                for nl in vs:
                    t = str((nl or {}).get("id", "")).split("-")[0] if isinstance(nl, dict) else str(nl).split("-")[0]
                    dropped.append({"prompt_id": pid, "field": k, "reason": f"commenters may not create locks ({t or 'unknown'} lock)"})
                continue
            if k in PROTECTED or k not in allowed:
                dropped.append({"prompt_id": pid, "field": k, "reason": "protected layer 1-3/format" if k in PROTECTED else "not in commenter_may_set"}); continue
            if NEVER_WORDS.search(json.dumps(v)):
                dropped.append({"prompt_id": pid, "field": k, "reason": "hard limit: name never on screen/spoken"}); continue
            if k == "lock_swap":
                fr, to = (v or {}).get("from"), (v or {}).get("to")
                tf, tt = str(fr).split("-")[0], str(to).split("-")[0]
                bucket = {"CHR": "chr", "LOC": "loc", "LOOK": "look", "PRP": "prp", "WAR": "war"}.get(tf)
                if to not in locks or fr not in locks or tf != tt or not bucket or fr not in sel.get(bucket, []):
                    dropped.append({"prompt_id": pid, "field": "lock_swap", "reason": f"swap {fr}->{to} needs two existing locks of the same type, from-lock in this shot"}); continue
                tl = locks[to]
                if tl.get("deprecated") or tl.get("selectable") is False or tl.get("off_model"):
                    dropped.append({"prompt_id": pid, "field": "lock_swap", "reason": f"refused: {to} is deprecated/off-model/not selectable (Director 2026-10-28)"}); continue
                sel[bucket] = [to if x == fr else x for x in sel[bucket]]
                applied.append({"prompt_id": pid, "field": "lock_swap", "detail": f"{fr}->{to}"}); continue
            if k == "screen_inserts":
                for si in (v or []):
                    r = ref_str(si.get("ref")); row, err = resolve(r)
                    if err:
                        embeds.append({"source": "commenter", "prompt_id": pid, **si, "ref": r, "status": "held", "reason": err})
                        notes.append(f"commenter embed {r} from {pid} held (not deleted): {err}"); continue
                    embeds.append({"source": "commenter", "prompt_id": pid, **si, "ref": r, **row, "status": "resolved"})
                applied.append({"prompt_id": pid, "field": k}); continue
            over.setdefault(k, []).append(v if isinstance(v, str) else json.dumps(v))
            applied.append({"prompt_id": pid, "field": k})

    def L(i):
        if i not in locks: errors.append(f"unknown lock {i}"); return ""
        return locks[i]["sentence"].strip()

    body = {}
    body["camera"] = "[Camera] " + (bl.get("camera") or "").strip() + ". One continuous shot, no cuts."
    look = " ".join(L(i) for i in sel.get("look", []))
    if over.get("look"): look += " Viewer change: " + " ".join(over["look"])
    body["look"] = "[Look] " + look
    loc = " ".join(L(i) for i in sel.get("loc", [])) + (" " + bl["environment"] if bl.get("environment") else "")
    if over.get("location"): loc += " Viewer change: " + " ".join(over["location"])
    if over.get("weather"): loc += " Weather: " + " ".join(over["weather"])
    body["location"] = "[Location] " + loc.strip()
    chars = []
    for c in sel.get("chr", []):
        name = c.split("-")[1]
        w = [L(x) for x in sel.get("war", []) if x.split("-")[1] == name]
        chars.append(" ".join([L(c)] + w))
    props = [L(x) for x in sel.get("prp", [])]
    if over.get("props"): props += ["Viewer change: " + " ".join(over["props"])]
    body["characters"] = "[Characters] " + (" ".join(chars) if chars else "No characters' faces in frame.") + (" Props: " + " ".join(props) if props else "")
    try:
        from charmeta_hook import apply_character_meta_to_body

        body = apply_character_meta_to_body(body, channel=sc.get("channel", 4), sidecar=sc)
    except Exception as exc:  # noqa: BLE001 — assembly must not fail if charmeta optional
        notes.append(f"charmeta injection skipped: {exc}")
    act = (bl.get("action") or "").strip()
    if over.get("action"): act += " Viewer change: " + " ".join(over["action"])
    body["action"] = "[Action] " + act
    ist = list(sc.get("in_scene_text") or []) + [t for v in over.get("in_scene_text", []) for t in ([v] if not v.startswith("[") else json.loads(v))]
    screens = [si for si in (sc.get("screen_inserts") or [])]
    for si in screens:
        r = ref_str(si.get("ref")); row, err = resolve(r)
        if err: errors.append(f"system embed {si.get('ref')}: {err}"); continue
        embeds.insert(0, {"source": "system", "prompt_id": None, **si, "ref": r, **row, "status": "resolved"})
    txt = []
    if ist: txt.append("Render exactly these words and nothing else: " + "; ".join(f'"{t}"' for t in ist) + ".")
    for e in embeds:
        if e["status"] == "resolved": txt.append(f"The {e.get('surface', 'screen')} shows no image (screen surface specified at the end).")
    body["in_scene_text"] = "[In-scene text] " + (" ".join(txt) if txt else "None: no text, signage, subtitles, logos or readable dials.")
    body["physics"] = "[Physics] " + (bl.get("physics") or "")
    aud = bl.get("audio") or ""
    if over.get("dialogue"): aud += " Viewer dialogue change: " + " ".join(over["dialogue"])
    body["audio"] = "[Audio] " + aud
    body["sfx"] = "[SFX] " + (bl.get("sfx") or "")
    body["rules"] = "\n".join(layers[k] for k in ("global", "channel", "format", "show_or_ad"))
    glow = "" if "monitor" in (bl.get("extra_constraints") or "") else " No glowing monitors."
    if "green" not in (bl.get("extra_constraints") or "").lower(): glow += " Nothing glows green."  # Director 2026-10-28: no green glow everywhere
    # 2026-10-28 Trundle 12:33 CT: no-eye-contact is per-show opt-in (show.yaml/sidecar no_eye_contact: true, or show wrapper mentions eye contact), never global
    eye_opt = bool(sc.get("no_eye_contact")) or "eye contact" in (layers.get("show_or_ad") or "").lower()
    eye = "No eye contact with camera: eyeline off-lens, characters never look into the lens (looking at each other is fine). " if eye_opt else ""
    # 2026-10-28 12:45 CT Director spec (Trundle 10:41 CT): no-eye-contact is GLOBAL, always on; eye_opt kept but redundant
    eye = "No eye contact with camera: eyeline off-lens, characters never look into the lens (looking at each other is fine). "
    body["constraints"] = ("[Constraints] Fictional adults only. Strictly photorealistic live action. " + eye + (bl.get("extra_constraints") or "No other people in frame.") + glow
                           + " No logos, insignia or brands. No cuts.")
    scr = [screen_line(e, sc.get("channel", 4)) for e in embeds if e["status"] == "resolved"]
    if scr: body["constraints"] += " [Screen] " + " ".join(scr)
    final = "\n".join(body[k] for k in BODY_ORDER)
    for i in [x for v in sel.values() for x in v]:
        if re.search(re.escape(i), final): errors.append(f"lock id {i} leaked into prompt")

    # refs: CHR (max 2 each) first, then LOC/WAR/PRP/LOOK, cap 14
    refs = []
    for c in sel.get("chr", []):
        for p in (locks.get(c, {}).get("refs") or [])[:MAX_REFS_PER_CHR]: refs.append({"lock": c, "path": p})
    for b in ("loc", "war", "prp", "look"):
        for i in sel.get(b, []):
            for p in (locks.get(i, {}).get("refs") or []): refs.append({"lock": i, "path": p})
    if len(refs) > MAX_REFS_TOTAL: warnings.append(f"refs capped {len(refs)}->{MAX_REFS_TOTAL}"); refs = refs[:MAX_REFS_TOTAL]
    for r in refs: r["sha256"] = file_sha(r["path"]) if os.path.exists(r["path"]) else None
    lock_ids = sorted(x for v in sel.values() for x in v)
    ck_src = json.dumps({"locks": lock_ids, "refs": [r["sha256"] for r in refs]}, sort_keys=True)

    kf = sc.get("keyframes") or {}
    chain = bool(sc.get("chain"))
    start = prev_last_frame(sidecar_path, sc) if chain else (sc.get("start_frame_v2") or kf.get("first_frame"))
    if chain and not start: warnings.append("chain=true but previous shot has no clean last frame"); start = kf.get("first_frame")
    dur = sc.get("duration_planned_s") or ((sc.get("tc_out") or 0) - (sc.get("tc_in") or 0))
    if sc.get("over_15s") or (dur and dur > MAX_CLIP_S + 0.5): warnings.append(f"clip {dur}s exceeds {MAX_CLIP_S}s max")

    layers = dict(layers)
    layers["shot"] = "\n".join(body[k] for k in BODY_ORDER if k not in ("rules",))
    if over or any(a["field"] in ("lock_swap", "screen_inserts") for a in applied):
        layers["commenter"] = json.dumps({"applied": applied, "over": over, "locks": sel}, sort_keys=True)
    out = {"shot_id": sc.get("shot_id"), "sidecar": os.path.abspath(sidecar_path), "segment_kind": kind, "mode": "locked",
            "ok": not errors, "errors": errors, "warnings": warnings, "final_prompt": final, "block_order": BODY_ORDER,
            "generation_note": "Screens with embeds: Ch 4 powered-off dark CRT (else plain green); CNB composites the CLEAN master in post. Corner tag/lower-thirds are post overlays.",
            "image": start, "start_frame": start, "last_frame": kf.get("last_frame") or sc.get("end_frame"), "end_frame": kf.get("last_frame") or sc.get("end_frame"),
            "chain": chain, "chain_basis": sc.get("chain_basis"),
            "refs": refs, "ref_mode_unverified": True, "seed": None,
            "lock_ids": lock_ids, "consistency_key": {"lock_ids": lock_ids, "ref_sha256": [r["sha256"] for r in refs], "sha256": sha(ck_src)},
            "embeds": embeds, "commenter_applied": applied, "commenter_dropped": dropped, "notes": notes, "commenter_prompt_ids": pids,
            "prompt_layers": {k: sha(layers[k]) for k in LAYER_NAMES if layers.get(k)}, "layer_files": paths, "home_only": True}
    if dense: out.update(densify(body, layers, refs, locks, sc))
    return out



# ---- 2026-10-28 ~10:30 PM CT, Director (Trundle t121): dense mode, see prompts/PROMPT-STYLE.md. Add-only; default output unchanged.
TAKE_POLICY = {"from_scratch": True, "max_gens_per_shot": 2, "extend": False, "on_fail": "revise prompt, then gen 1 again",
               "continuity": "stitch shots in the edit, never extend", "lineage_field": "gen"}
DENSE_SKIP_LABELS = {"cast", "locations", "screens", "text"}  # covered by locks / handled in post
DENSE_DROP = re.compile(r"(first image|last image|starting frame|ending frame|keyframe|continuity sheet|STORY SPINE)", re.I)
LABEL = re.compile(r"\[[^\]]*\]\s*")


def _sentences(t):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", t.strip()) if x.strip()]


def _clean(t):
    t = LABEL.sub("", t).replace("Props: ", "Also in the scene, ")
    t = re.sub(r"[*_`#>]+", "", t)
    t = re.sub(r"^\s*[-\u2022]\s*", "", t, flags=re.M)
    return re.sub(r"\s+", " ", t).strip()


def _rules_text(layer_txt):
    keep = []
    for line in layer_txt.splitlines():
        if line.startswith("## "): break  # sections below a heading are authoring notes (spine, embeds)
        m = re.match(r"\s*\[([^\]:]+)", line)
        if m and m.group(1).strip().lower().split()[0] in DENSE_SKIP_LABELS: continue
        if line.lstrip().startswith(">"): continue
        keep.append(line)
    return _clean(" ".join(keep))


def _lock_label(lock_id):
    parts = lock_id.split("-")[1:-1]
    name = " ".join(parts)
    return name if lock_id.startswith("CHR-") else "the " + name.lower() + {"LOC": " location", "PRP": " prop", "WAR": " wardrobe", "LOOK": " look"}.get(lock_id.split("-")[0], "")


class MissingReferenceImageError(ValueError):
    """2026-10-28 Director (Trundle t132): every dense prompt needs >=1 reference image."""


def densify(body, layers, refs, locks, sc):
    """One plain-English paragraph: refs, who/where, action, camera, audio, dialogue/text, style, limits."""
    if not refs:  # 2026-10-28 Trundle t132: reference image REQUIRED, not optional
        raise MissingReferenceImageError("dense prompt has 0 @Image refs: at least 1 reference image (character sheet first) is required for every render")
    images, groups = [], {}
    for i, r in enumerate(refs, 1):
        tag = f"@Image{i}"
        images.append({"tag": tag, "lock": r["lock"], "path": r["path"], "sha256": r["sha256"], "role": "identity_setting", "use": "reference_only"})
        groups.setdefault(r["lock"], []).append(tag)
    ref_bits = [(" and ".join(v)) + (" show " if len(v) > 1 else " shows ") + _lock_label(k) for k, v in groups.items()]
    ref_line = ("Use the attached images only as reference for identity, wardrobe, setting and props, never as the opening or output frame: "
                + "; ".join(ref_bits) + ".") if ref_bits else ""
    order = ["characters", "location", "action", "physics", "camera", "audio", "sfx", "in_scene_text", "look"]
    parts = [ref_line] + [_clean(body.get(k, "")) for k in order]
    parts += [_rules_text(layers.get(k, "")) for k in ("global", "channel", "format", "show_or_ad")]
    parts.append(_clean(body.get("constraints", "")))
    drop_more = re.compile(r"(post overlay|Ads never|\bBI-\d|open thread" + ("" if "Screen" in body.get("constraints", "") else r"|carry a clip") + ")", re.I)
    seen, out = set(), []
    for s_ in _sentences(" ".join(p for p in parts if p)):
        key = re.sub(r"\W+", " ", s_.lower()).strip()
        if not key or key in seen or DENSE_DROP.search(s_) or drop_more.search(s_): continue
        seen.add(key); out.append(s_ if s_[-1] in ".!?" else s_ + ".")
    para = " ".join(out)
    para = para.replace("None: no text", "No text")
    for i in groups:  # bind first body mention of each character to its first image, @Image style
        if i.startswith("CHR-"):
            nm = i.split("-")[1]; head, sep, rest = para.partition(ref_line) if ref_line else ("", "", para)
            para = head + sep + re.sub(rf"\b{nm}\b", f"{nm} from {groups[i][0]}", rest, count=1)
    errs = [f"label syntax left in dense prompt: {m}" for m in re.findall(r"\[[A-Za-z][^\]]*\]|^\w+:\s", para, flags=re.M)]
    return {"dense_prompt": para, "dense_prompt_sha256": sha(para), "image_bindings": images,
            "attach_order": [x["path"] for x in images], "start_frame_dense": None,
            "take_policy": TAKE_POLICY, "lineage_required": ["gen", "dense_prompt_sha256", "image_bindings", "prompt_layers"],
            "dense_errors": errs}


# ---- 2026-10-28 11:55 PM CT, Director (Trundle pt150u): opt-in reusable looks, prompts/looks/<id>/look.json. Add-only; default output unchanged.
LOOKS_DIR = "/workspace/thunder-trundle/prompts/looks"


def load_look(look_id):
    with open(os.path.join(LOOKS_DIR, look_id, "look.json")) as f: return json.load(f)


def apply_look(out, look_id):
    """Append the look's style_block + camera_line to dense_prompt (dense only). Null/empty -> no text added (2026-10-29 pt152u)."""
    if not look_id or "dense_prompt" not in out: return out
    lk = load_look(look_id)
    add = " ".join(x for x in (lk.get("style_block"), lk.get("camera_line")) if x)
    if add and add not in out["dense_prompt"]:
        out["dense_prompt"] = out["dense_prompt"].rstrip() + " " + add
        out["dense_prompt_sha256"] = sha(out["dense_prompt"])
    out["look"] = {"id": lk["id"], "trim_head_s": lk.get("trim_head_s"), "max_gens": lk.get("max_gens"), "no_extend": lk.get("no_extend")}
    return out


def main():
    a = argparse.ArgumentParser(); a.add_argument("sidecar")
    a.add_argument("--mutations"); a.add_argument("--mutations-json"); a.add_argument("--kind", choices=["show", "commercial"])
    a.add_argument("--dense", action="store_true", help="PROMPT-STYLE.md: one plain-English paragraph + @ImageN refs")
    a.add_argument("--look", help="opt-in look id from prompts/looks/ (dense only), e.g. noir-graphic-novel")
    o = a.parse_args()
    out = assemble(o.sidecar, load_mutations(o), o.kind, dense=o.dense)
    out = apply_look(out, o.look)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    sys.exit(0 if out["ok"] else 2)


if __name__ == "__main__": main()


# --- 2026-10-29 Director (add-only; Trundle approved spec v2 11:35 AM CT) ---
# Full-density bundled comments: use bundle_assembler.assemble_bundle() instead of the
# one-change layer6 path above (kept unchanged as the legacy path / backup).
def assemble_full_density(clips, comments, canon_by_clip=None, channel=4):
    import sys as _s, os as _o
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
    from bundle_assembler import assemble_bundle
    return assemble_bundle(clips, comments, canon_by_clip, channel)
