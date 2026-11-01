"""Story Bot CLI — seasons/episodes/ads/CNB export (local)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python -m app.cli` from server/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def cmd_smoke(args: argparse.Namespace) -> int:
    from app.spend import LEDGER_PATH, local_month_spend, month_total_for_gate
    from app.tv.pipeline import run_smoke

    before = local_month_spend()
    result = run_smoke(
        channel_id=args.channel,
        show_id=args.show,
        slot_id=args.slot,
        model_alias=args.model,
        out_dir=Path(args.out) if args.out else None,
    )
    after = local_month_spend()
    gate_total, gate_note = month_total_for_gate()
    spend = {
        "test_cost_usd": round(after - before, 6),
        "local_month_ledger_usd": after,
        "gate": gate_note,
        "gate_total_usd": gate_total,
        "ledger_path": str(LEDGER_PATH),
    }
    spend_path = Path(result["out_dir"]) / "spend_summary.json"
    spend_path.write_text(json.dumps(spend, indent=2) + "\n")
    print(json.dumps({"result": result, "spend": spend}, indent=2))
    print(
        "\nNOTE: CNB export is local only. Nothing was sent to CNB or aired.",
        flush=True,
    )
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    from app.config_layers import merge_configs

    merged = merge_configs(args.channel, args.show, args.slot)
    print(json.dumps(merged["flat"], indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="story-engine", description="thunder trundle Story Bot engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("smoke", help="Run Ch 4 Military Boutique smoke test")
    s.add_argument("--channel", default="4")
    s.add_argument("--show", default="forward-supply")
    s.add_argument("--slot", default="smoke-outline")
    s.add_argument("--model", default="grok-cheap")
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_smoke)

    m = sub.add_parser("merge-config", help="Print merged channel<show<slot config")
    m.add_argument("--channel", required=True)
    m.add_argument("--show", required=True)
    m.add_argument("--slot", required=True)
    m.set_defaults(func=cmd_merge)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
