"""Unified charmeta CLI (dry-run defaults; live-path refusal)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from charmeta.config import allow_live_paths, resolve_path
from charmeta.meta_prompt import rebuild_meta_prompt_for_character
from charmeta.observations import append_observation
from charmeta.paths import refuse_charmeta_path
from charmeta.promote import promote
from charmeta.stills_stub import ingest_stills_meta_to_log
from charmeta.store import build_companion_from_bible, load_companion, save_companion
from lineage.derive_aired import derive_aired_enriched_copy


def _allow_flag(args: argparse.Namespace) -> bool:
    return allow_live_paths() or bool(getattr(args, "allow_live_paths", False))


def _guard(path: Path | None, args: argparse.Namespace) -> Path | None:
    if path is None:
        return None
    return refuse_charmeta_path(path, allow_live_paths=_allow_flag(args))


def cmd_init_companion(args: argparse.Namespace) -> int:
    bible = _guard(args.bible, args)
    out = _guard(args.companion, args)
    if bible is None or out is None:
        print("init-companion requires --bible and --companion (or env paths)", file=sys.stderr)
        return 2
    cast_ids = [part.strip() for part in args.cast_ids.split(",") if part.strip()]
    doc = build_companion_from_bible(bible, cast_ids)
    if args.apply:
        save_companion(out, doc)
    print(yaml.safe_dump({"cast_ids": cast_ids, "dry_run": not args.apply}, sort_keys=False))
    return 0


def cmd_append_obs(args: argparse.Namespace) -> int:
    obs_path = _guard(args.observations, args)
    if obs_path is None:
        return 2
    row: dict[str, Any] = {
        "clip_id": args.clip_id,
        "character": args.character,
        "field": args.field,
        "extracted_text": args.text,
        "method": args.method,
    }
    if args.apply:
        append_observation(obs_path, row)
    print(json.dumps({"dry_run": not args.apply, "row": row}, ensure_ascii=False, indent=2))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    companion = _guard(args.companion, args)
    observations = _guard(args.observations, args)
    lineage = _guard(args.lineage, args)
    if companion is None or observations is None or lineage is None:
        return 2
    report = promote(
        companion_path=companion,
        observations_path=observations,
        lineage_path=lineage,
        apply=args.apply,
    )
    print(yaml.safe_dump(report.__dict__, sort_keys=False))
    return 2 if report.conflicts else 0


def cmd_rebuild_meta_prompt(args: argparse.Namespace) -> int:
    companion_path = _guard(args.companion, args)
    if companion_path is None:
        return 2
    companion = load_companion(companion_path)
    report = rebuild_meta_prompt_for_character(
        companion,
        args.character,
        apply=args.apply,
    )
    if args.apply:
        save_companion(companion_path, companion)
    print(yaml.safe_dump(report.__dict__, sort_keys=False))
    return 0


def cmd_stills_ingest(args: argparse.Namespace) -> int:
    obs_path = _guard(args.observations, args)
    meta_path = _guard(args.stills_meta, args)
    if obs_path is None or meta_path is None:
        return 2
    rows = ingest_stills_meta_to_log(
        observations_path=obs_path,
        stills_meta_path=meta_path,
        clip_id=args.clip_id,
        character=args.character,
        image_path=args.image,
        apply=args.apply,
    )
    print(json.dumps({"dry_run": not args.apply, "rows": rows}, ensure_ascii=False, indent=2))
    return 0


def cmd_derive_aired(args: argparse.Namespace) -> int:
    input_path = _guard(args.input, args)
    output_path = _guard(args.output, args)
    if input_path is None or output_path is None:
        return 2
    report = derive_aired_enriched_copy(
        input_path=input_path,
        output_path=output_path,
        apply=args.apply,
    )
    print(json.dumps(report.__dict__, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Character-meta tooling (dry-run default)")
    parser.add_argument(
        "--allow-live-paths",
        action="store_true",
        help="Allow known live bible/ledger paths (Trundle yes only)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init-companion", help="Build companion YAML from bible copy")
    init_p.add_argument("--bible", type=Path, default=resolve_path(None, "CHARMETA_BIBLE_PATH"))
    init_p.add_argument("--companion", type=Path, default=resolve_path(None, "CHARMETA_COMPANION_PATH"))
    init_p.add_argument("--cast-ids", required=True, help="Comma-separated cast ids")
    init_p.add_argument("--apply", action="store_true")
    init_p.set_defaults(func=cmd_init_companion)

    append_p = sub.add_parser("append-obs", help="Append one trait observation")
    append_p.add_argument("--observations", type=Path, default=resolve_path(None, "CHARMETA_OBSERVATIONS_PATH"))
    append_p.add_argument("--clip-id", required=True)
    append_p.add_argument("--character", required=True)
    append_p.add_argument("--field", required=True)
    append_p.add_argument("--text", required=True)
    append_p.add_argument("--method", default="human_note")
    append_p.add_argument("--apply", action="store_true")
    append_p.set_defaults(func=cmd_append_obs)

    promote_p = sub.add_parser("promote", help="Promote observations to proposed (N=3 aired)")
    promote_p.add_argument("--companion", type=Path, default=resolve_path(None, "CHARMETA_COMPANION_PATH"))
    promote_p.add_argument("--observations", type=Path, default=resolve_path(None, "CHARMETA_OBSERVATIONS_PATH"))
    promote_p.add_argument("--lineage", type=Path, default=resolve_path(None, "CHARMETA_LINEAGE_PATH"))
    promote_p.add_argument("--apply", action="store_true")
    promote_p.set_defaults(func=cmd_promote)

    meta_p = sub.add_parser("rebuild-meta-prompt", help="Rebuild meta_prompt for one character")
    meta_p.add_argument("--companion", type=Path, default=resolve_path(None, "CHARMETA_COMPANION_PATH"))
    meta_p.add_argument("--character", required=True)
    meta_p.add_argument("--apply", action="store_true")
    meta_p.set_defaults(func=cmd_rebuild_meta_prompt)

    stills_p = sub.add_parser("stills-ingest", help="Append stills meta JSON to observation log")
    stills_p.add_argument("--observations", type=Path, default=resolve_path(None, "CHARMETA_OBSERVATIONS_PATH"))
    stills_p.add_argument("--stills-meta", type=Path, required=True)
    stills_p.add_argument("--clip-id", required=True)
    stills_p.add_argument("--character", required=True)
    stills_p.add_argument("--image", type=Path, default=None)
    stills_p.add_argument("--apply", action="store_true")
    stills_p.set_defaults(func=cmd_stills_ingest)

    derive_p = sub.add_parser("derive-aired", help="Pass-through to lineage aired deriver")
    derive_p.add_argument("--input", type=Path, required=True)
    derive_p.add_argument("--output", type=Path, required=True)
    derive_p.add_argument("--apply", action="store_true")
    derive_p.set_defaults(func=cmd_derive_aired)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
