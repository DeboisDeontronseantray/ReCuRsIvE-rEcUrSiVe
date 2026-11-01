#!/usr/bin/env python3
"""Fixture dry run: NP16 parity through the assembler, then NP16 -> NP17 with all four inputs.

Writes only to system-v5-draft/out/dryrun/night-porter/ (git-ignored). Exits non-zero if parity breaks, the v44 gate
fails, or any slot other than beats/continue differs from the current v42 build of NP16."""
import json
import sys

import paths
from adapters.v4_bridge import build_prompt_v42
from assemble_next import DRYRUN_ROOT, assemble_next

FIX = paths.V5 / "fixtures"
NP16 = FIX / "night-porter" / "NP16" / "base_spec.json"
NP17 = FIX / "night-porter" / "NP17"
LIVE = paths.get("TT_PROMPTS_V4") / "prompts_v44" / "odyssey"
NOW = "2026-10-31T21:20:00-05:00"


def main():
    out = DRYRUN_ROOT / "night-porter"
    parity = assemble_next(inputs_dir=NP17, base_spec=NP16, out_dir=out / "parity", advance=False)
    current = build_prompt_v42.build(json.loads(NP16.read_text()), strict=True)
    live_args = json.loads((LIVE / "NP16.args.json").read_text())
    live_meta = json.loads((LIVE / "NP16.meta.json").read_text())
    parity_ok = parity["args"] == current["args"] == live_args and parity["sidecar"] == current["sidecar"] == live_meta
    nxt = assemble_next(inputs_dir=NP17, base_spec=NP16, out_dir=out, spool_path=NP17 / "comments.jsonl",
                        character_meta_dir=FIX / "character-meta", now=NOW)
    summary = {
        "parity_NP16_byte_identical": parity_ok,
        "NP17_changed_slots": nxt["diff"]["changed_slots"],
        "NP17_disallowed_slots": nxt["diff"]["disallowed_slots"],
        "NP17_args_changed": sorted(nxt["diff"]["args"]),
        "NP17_gate_fails": nxt["gate"]["fails"],
        "NP17_gate_warns": nxt["gate"]["warns"],
        "NP17_words": len(nxt["args"]["prompt"].split()),
        "NP17_beats": [f"[{b['requester']}: {b['source']}] {b['beat']}" for b in nxt["diff"]["new_beats"]],
        "comments": {k: [c["id"] for c in v] for k, v in nxt["assembly"]["comments"].items()},
        "out": str(out.relative_to(paths.V5)),
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    ok = parity_ok and not summary["NP17_gate_fails"] and not summary["NP17_disallowed_slots"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
