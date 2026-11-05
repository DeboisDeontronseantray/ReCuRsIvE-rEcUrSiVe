"""Export receipt-backed canonical air projections (add-only; idempotent)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lineage.aired import clip_id_aired, load_lineage_jsonl
from lineage.paths import refuse_live_path


DERIVE_EVENT = "aired_flag"


@dataclass
class DeriveReport:
    dry_run: bool
    input_path: str
    output_path: str
    would_mark: list[dict[str, Any]] = field(default_factory=list)
    appended: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


def enrich_row_with_derived_aired(row: dict[str, Any], *, lifecycle=None) -> dict[str, Any]:
    """Export a projection, stripping any untrusted legacy air latch."""
    enriched = dict(row)
    enriched.pop("aired_derived_from", None)
    enriched["aired"] = clip_id_aired(row, lifecycle=lifecycle)
    if enriched["aired"]:
        enriched["aired_derived_from"] = "verified-lifecycle-receipt"
    return enriched


def derivation_patch_row(row: dict[str, Any], *, lifecycle=None) -> dict[str, Any] | None:
    clip_id = row.get("clip_id")
    if not isinstance(clip_id, str) or not clip_id.strip():
        return None
    if not clip_id_aired(row, lifecycle=lifecycle):
        return None
    return {
        "clip_id": clip_id,
        "derive": DERIVE_EVENT,
        "aired": True,
        "aired_derived_from": "verified-lifecycle-receipt",
        "derived_at": datetime.now(timezone.utc).isoformat(),
    }


def _existing_derived_clip_ids(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    clip_ids: set[str] = set()
    for row in load_lineage_jsonl(output_path):
        if row.get("derive") != DERIVE_EVENT:
            if row.get("aired") is True and isinstance(row.get("clip_id"), str):
                clip_ids.add(row["clip_id"])
            continue
        clip_id = row.get("clip_id")
        if isinstance(clip_id, str) and row.get("aired") is True:
            clip_ids.add(clip_id)
    return clip_ids


def derive_aired_enriched_copy(
    *,
    input_path: Path,
    output_path: Path,
    apply: bool,
    lifecycle=None,
) -> DeriveReport:
    """Write one enriched row per input row (derived ``aired`` field only on output)."""
    rows = load_lineage_jsonl(input_path)
    report = DeriveReport(
        dry_run=not apply,
        input_path=str(input_path),
        output_path=str(output_path),
    )
    enriched_lines: list[str] = []
    for row in rows:
        clip_id = row.get("clip_id")
        enriched = enrich_row_with_derived_aired(row, lifecycle=lifecycle)
        if enriched.get("aired") is True:
            report.would_mark.append(
                {
                    "clip_id": clip_id,
                    "aired_derived_from": enriched.get("aired_derived_from"),
                }
            )
        else:
            report.unchanged.append(str(clip_id))
        enriched_lines.append(json.dumps(enriched, ensure_ascii=False))
    if apply:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(enriched_lines) + "\n", encoding="utf-8")
        report.appended = [item["clip_id"] for item in report.would_mark if item.get("clip_id")]
    return report


def derive_aired_append_patches(
    *,
    input_path: Path,
    output_path: Path,
    apply: bool,
    lifecycle=None,
) -> DeriveReport:
    """Append idempotent ``derive: aired_flag`` rows; never modifies the input ledger."""
    rows = load_lineage_jsonl(input_path)
    report = DeriveReport(
        dry_run=not apply,
        input_path=str(input_path),
        output_path=str(output_path),
    )
    already = _existing_derived_clip_ids(output_path)
    patches: list[str] = []
    for row in rows:
        clip_id = row.get("clip_id")
        if isinstance(clip_id, str) and clip_id in already:
            report.skipped_existing.append(clip_id)
            continue
        patch = derivation_patch_row(row, lifecycle=lifecycle)
        if patch is None:
            if isinstance(clip_id, str):
                report.unchanged.append(clip_id)
            continue
        cid = patch["clip_id"]
        if cid in already:
            report.skipped_existing.append(cid)
            continue
        report.would_mark.append(patch)
        patches.append(json.dumps(patch, ensure_ascii=False))
        already.add(cid)
    if apply and patches:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as handle:
            for line in patches:
                handle.write(line + "\n")
        report.appended = [patch["clip_id"] for patch in report.would_mark]
    return report


def append_aired_derivation_for_clip(
    output_path: Path,
    row: dict[str, Any],
    *,
    apply: bool = True,
    lifecycle=None,
    receipt=None,
) -> DeriveReport:
    """Hook for Media Librarian New at AIRED time — append one idempotent patch row."""
    report = DeriveReport(
        dry_run=not apply,
        input_path="",
        output_path=str(output_path),
    )
    if receipt is not None:
        from astra_lifecycle.repo import gateway
        # Every requested air transition still passes the existing receipt verifier.
        if not apply:
            raise ValueError("receipt transitions require apply=True")
        gateway(lifecycle).call("D09", "aired", clip_id=row["clip_id"], receipt=receipt)
    patch = derivation_patch_row(row, lifecycle=lifecycle)
    if apply and patch is None:
        from astra_lifecycle.contracts import GuardError
        raise GuardError("air cannot be set without a verified canonical receipt")
    if patch is None:
        clip_id = row.get("clip_id")
        if isinstance(clip_id, str):
            report.unchanged.append(clip_id)
        return report
    already = _existing_derived_clip_ids(output_path)
    cid = patch["clip_id"]
    if cid in already:
        report.skipped_existing.append(cid)
        return report
    report.would_mark.append(patch)
    if apply:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(patch, ensure_ascii=False) + "\n")
        report.appended.append(cid)
    return report


def merge_lineage_with_derivations(
    base_path: Path | str,
    derivations_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Load base ledger rows plus optional add-only derivation patches."""
    rows = load_lineage_jsonl(base_path)
    if derivations_path is None:
        return rows
    rows.extend(load_lineage_jsonl(derivations_path))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive LINEAGE aired flags (dry-run default; never writes input ledger)"
    )
    parser.add_argument("--input", required=True, type=Path, help="Source LINEAGE.jsonl (read-only)")
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Explicit output path for derived rows (required with --apply)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write derived output (default is dry-run report only)",
    )
    parser.add_argument(
        "--mode",
        choices=("enrich", "append"),
        default="enrich",
        help="enrich=full derived copy; append=add-only aired_flag patch rows",
    )
    parser.add_argument(
        "--allow-live-paths",
        action="store_true",
        help="Allow known live LINEAGE paths (trundle yes only)",
    )
    args = parser.parse_args(argv)

    allow = args.allow_live_paths
    input_path = refuse_live_path(args.input, allow_live_paths=allow)
    output_path = refuse_live_path(args.output, allow_live_paths=allow)

    if args.mode == "append":
        report = derive_aired_append_patches(
            input_path=input_path,
            output_path=output_path,
            apply=args.apply,
        )
    else:
        report = derive_aired_enriched_copy(
            input_path=input_path,
            output_path=output_path,
            apply=args.apply,
        )

    print(json.dumps(report.__dict__, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
