#!/usr/bin/env python3
"""Assemble the next clip's prompt from the other systems' outputs (D1: Director New assembles; it does not invent or own inputs).

Base: the previous clip's v42 spec, built by the unchanged v42 builder (D2). New inputs only add beats:
still continuity (D3, stub analyzer), raw comments from the spool (D4), and capped character memory (D5).
Locked threads and the spot's thread_holder are frozen first and enter only as hard constraints (D6, D7). FT stays off (D8).
Writes only to out_dir (system-v5-draft/out/dryrun/ or a folder outside the repo)."""
import argparse
import copy
import datetime
import hashlib
import json
import pathlib
import sys

import contracts
import intake
import memory
import paths
import placement
import report
import sanitize
from adapters import base_spec as base_spec_mod
from adapters import locked_meta, still_meta
from adapters.v4_bridge import V4_CONFIG, apply_check_v44, build_prompt_v42, layers_v4

COMMENTER_IMAGES_CFG = V4_CONFIG / "commenter_images.json"
DRYRUN_ROOT = paths.V5 / "out" / "dryrun"


class ReferenceImageRequired(RuntimeError):
    pass


class CommenterImagesOn(RuntimeError):
    pass


class OutputLocationRefused(RuntimeError):
    pass


class LockViolated(RuntimeError):
    pass


def _sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _file(path):
    return {"file": pathlib.Path(path).name, "sha256": _sha(path)} if path else None


def _check_out_dir(out_dir):
    o = pathlib.Path(out_dir).resolve()
    if o.is_relative_to(paths.REPO.resolve()) and not o.is_relative_to(DRYRUN_ROOT.resolve()):
        raise OutputLocationRefused(f"{o} is inside the repo but not under {DRYRUN_ROOT}")


def _has_refs(spec):
    return bool(spec.get("refs_raw") or spec.get("ref_for") or any(c.get("ref") for c in spec.get("cast", [])))


def _fails(spec, cid):
    r = build_prompt_v42.build(spec, strict=False)
    rep = apply_check_v44.check(r["args"]["prompt"], r["args"], spec, r["sidecar"], clip_id=cid)
    return {k for k, v in rep.items() if v[0] == "FAIL"}


def _screen(spec, cid, still, comments, memories, duration, cfg):
    """Gate-check each input beat on its own; a beat that adds a FAIL is held with that gate key as the reason."""
    baseline = _fails(spec | {"beats": []}, cid)
    held = {}
    items = ([{"id": "still", "text": still}] if still else []) + comments + memories
    for it in items:
        beat = placement.place(still=None, comments=[it], memories=[], duration=duration, cfg=cfg)["beats"]
        new = _fails(spec | {"beats": beat}, cid) - baseline
        if new:
            held[it["id"]] = sorted(new)
    return held


def _now(now):
    t = datetime.datetime.fromisoformat(now) if isinstance(now, str) else (now or datetime.datetime.now(datetime.timezone.utc))
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def _write(out_dir, name, obj):
    p = pathlib.Path(out_dir) / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1) + "\n")


def assemble_next(*, inputs_dir, base_spec, out_dir, clip_id=None, spool_path=None, character_meta_dir=None, now=None,
                  episode=1, season=1, advance=True, consumed_path=None):
    cfg = paths.config("assembly")
    _check_out_dir(out_dir)
    if json.loads(pathlib.Path(COMMENTER_IMAGES_CFG).read_text()).get("enabled"):
        raise CommenterImagesOn("commenter images are NOT YET (Trundle 10:48 PM CT Oct 30); only Trundle turns them on")
    base = base_spec_mod.load(base_spec)
    prev = base["clip_id"]
    cid = clip_id or (base_spec_mod.next_clip_id(prev) if advance else prev)
    if cid != (base_spec_mod.next_clip_id(prev) if advance else prev):
        raise ValueError(f"clip id {cid} does not follow {prev}")
    if not _has_refs(base) and cid not in apply_check_v44.exempt_ids():
        raise ReferenceImageRequired(f"{cid}: a reference image is required (hard rule); only the 16 listed ads are exempt")
    if advance and not base.get("start_frame"):
        raise ValueError(f"{prev} has no start frame; adding one would renumber its <IMAGE_n> tags (not supported in v1)")

    inputs = contracts.load_inputs(inputs_dir)
    lm, sm = inputs["locked_meta"], inputs["still_meta"]
    if (lm["show"], lm["channel"]) != (base.get("show"), base["channel"]):
        raise contracts.ContractError("locked_meta show/channel do not match the base spec")
    locked = locked_meta.hard_constraints(lm, base.get("clip_type"))
    thread = locked_meta.thread_slot(locked)
    now = _now(now)
    idx = base_spec_mod.clip_index(cid)

    spec = copy.deepcopy(base)
    spec["clip_id"] = cid
    if thread and advance:
        if base.get("thread") not in (None, thread):
            raise LockViolated(f"base spec thread {base['thread']!r} conflicts with the locked constraints")
        spec["thread"] = thread
    frozen_thread = report.slot_split(build_prompt_v42.build(spec, strict=False)["args"]["prompt"])["thread"]

    comments = {"placed": [], "carried": [], "held": [], "dropped": []}
    still_rec = {"used": False, "vision_model": still_meta.pinned_vision_model()}
    mem_rec = {"summoned": [], "beats": []}
    spool_rec, cmeta_rec, proposed, sources = None, None, {}, []
    if advance:
        spool = spool_path or paths.get("TT_COMMENT_SPOOL", required=True)
        consumed_path = pathlib.Path(consumed_path or paths.get("TT_COMMENT_CONSUMED") or pathlib.Path(out_dir) / "comments.consumed.jsonl")
        rows, stats = intake.collect(spool, now=now, cfg=cfg, consumed=intake.load_consumed(consumed_path, clip_id=cid))
        spool_rec = _file(spool) | stats
        kept = []
        for i, row in enumerate(rows, 1):
            s = sanitize.sanitize(row["text"], cfg=cfg)
            rec = {"id": f"c{i}", "key": intake.comment_key(row), "ts": row["ts"], "status": s["status"], "reasons": s["reasons"]}
            if s["status"] in ("KEPT", "BENT"):
                kept.append(rec | {"text": s["text"]})
            else:
                comments["held" if s["status"] == "HELD" else "dropped"].append(rec)

        still_text = None
        if sm["prev_clip_id"] == prev:
            descs = still_meta.StubAnalyzer(sm["descriptors"]).analyze_still(sm["still_path"])
            k, d = still_meta.filter_descriptors(descs, still_meta.imaged_names(base))
            still_text = "; ".join(k) or None
            still_rec |= {"used": bool(still_text), "prev_clip_id": sm["prev_clip_id"], "kept": k, "dropped_looks": d}
        else:
            still_rec |= {"stale": sm["prev_clip_id"]}

        cmeta_dir = character_meta_dir or paths.get("TT_CHARACTER_META", required=True)
        cfile = memory.channel_file(cmeta_dir, base["channel"])
        mems = []
        if cfile.is_file():
            cm = memory.load_channel_meta(cmeta_dir, base["channel"])
            cmeta_rec = _file(cfile)
            summoned = memory.present_cast(cm, base)
            for cast_id in summoned:
                for j, text in enumerate(memory.memory_beats(cm["cast"][cast_id], episode=episode, season=season, clip_index=idx)):
                    mems.append({"id": f"{cast_id}#{j}", "text": text})
            mem_rec = {"summoned": summoned, "beats": [m["id"] for m in mems]}
            proposed = memory.proposed_update(cm, summoned)

        spec["start_frame"] = still_meta.next_start_frame(prev, paths.get("TT_CLIPS"))
        spec["parent_clip"] = f"{prev}_last"
        spec["consequences"] = [c | {"created_here": False} for c in base.get("consequences", [])
                                if layers_v4.tier_alive(c, episode, season, idx)]

        held = _screen(spec, cid, still_text, kept, mems, spec["duration"], cfg)
        for rec in [r for r in kept if r["id"] in held]:
            kept.remove(rec)
            comments["held"].append({k: v for k, v in rec.items() if k != "text"} | {"status": "HELD", "reasons": rec["reasons"] + [f"gate:{g}" for g in held[rec["id"]]]})
        if "still" in held:
            still_text, still_rec["used"], still_rec["held"] = None, False, held["still"]
        mem_rec["held"] = {m["id"]: held[m["id"]] for m in mems if m["id"] in held}
        mems = [m for m in mems if m["id"] not in held]

        max_comments = len(kept)
        while True:
            pl = placement.place(still=still_text, comments=kept, memories=mems, duration=spec["duration"], cfg=cfg, max_comments=max_comments)
            spec["beats"] = pl["beats"]
            built = build_prompt_v42.build(spec, strict=True)
            if len(built["args"]["prompt"].split()) <= cfg["max_words"] or max_comments == 0:
                break
            max_comments -= 1
        by_id = {r["id"]: r for r in kept}
        comments["placed"] = [by_id[i] for i in pl["placed"]]
        comments["carried"] = [by_id[i] for i in pl["carried"]]
        sources = pl["sources"]
    else:
        built = build_prompt_v42.build(spec, strict=True)

    if report.slot_split(built["args"]["prompt"])["thread"] != frozen_thread:
        raise LockViolated("the locked thread slot changed during assembly")
    if built["sidecar"].get("contributors"):
        raise LockViolated("contributors must stay out of assembled clips in v1")

    rep = apply_check_v44.check(built["args"]["prompt"], built["args"], spec, built["sidecar"], clip_id=cid)
    gate = report.gate_summary(cid, rep)
    current = build_prompt_v42.build(base, strict=True)
    d = report.diff(current, built, sources, locked_thread=thread if advance else None)
    assembly = {
        "clip_id": cid, "base_clip": prev, "mode": "next" if advance else "parity",
        "now": now.isoformat(), "episode": episode, "season": season,
        "builder": built["sidecar"]["builder"],
        "inputs": {"base_spec": _file(base_spec), "locked_meta": _file(pathlib.Path(inputs_dir) / "locked_meta.json"),
                   "still_meta": _file(pathlib.Path(inputs_dir) / "still_meta.json"), "spool": spool_rec, "character_meta": cmeta_rec},
        "hard_constraints": list(locked), "still": still_rec, "comments": comments, "memory": mem_rec,
        "beats": sources, "gate": {"fails": gate["fails"], "warns": gate["warns"]},
        "diff": {k: d[k] for k in ("changed_slots", "disallowed_slots", "identical_prompt")},
    }
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _write(out, f"{cid}.args.json", built["args"])
    _write(out, f"{cid}.meta.json", built["sidecar"])
    _write(out, f"{cid}.assembly.json", assembly)
    _write(out, f"{cid}.memory.proposed.json", proposed)
    _write(out, f"GATE-{cid}.json", gate)
    _write(out, f"DIFF-{cid}.md", report.diff_markdown(prev, cid, d, gate))
    if advance:
        intake.mark_consumed(consumed_path, [c["key"] for c in comments["placed"]], clip_id=cid)
    return {"spec": spec, "args": built["args"], "sidecar": built["sidecar"], "assembly": assembly, "diff": d, "gate": gate}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inputs", required=True, help="inputs/<show>/<clip_id>/ with locked_meta.json and still_meta.json")
    ap.add_argument("--base-spec", required=True, help="previous clip's v42 spec (JSON)")
    ap.add_argument("--out", required=True, help="output folder (under system-v5-draft/out/dryrun/ or outside the repo)")
    ap.add_argument("--spool", help="comment spool .jsonl (default: TT_COMMENT_SPOOL)")
    ap.add_argument("--character-meta", help="character-meta folder (default: TT_CHARACTER_META)")
    ap.add_argument("--now", help="assembly time, ISO-8601 (default: current UTC time)")
    ap.add_argument("--episode", type=int, default=1)
    ap.add_argument("--season", type=int, default=1)
    a = ap.parse_args(argv)
    r = assemble_next(inputs_dir=a.inputs, base_spec=a.base_spec, out_dir=a.out, spool_path=a.spool,
                      character_meta_dir=a.character_meta, now=a.now, episode=a.episode, season=a.season)
    print(json.dumps({"clip_id": r["args"]["filename"], "gate_fails": r["gate"]["fails"], **r["assembly"]["diff"]}, indent=1))
    return 1 if r["gate"]["fails"] or r["assembly"]["diff"]["disallowed_slots"] else 0


if __name__ == "__main__":
    sys.exit(main())
