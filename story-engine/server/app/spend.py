"""xAI spend ledger + monthly hard stop.

Key: box env var XAI_API_KEY (see /workspace/shared/INVENTORY/accounts-subs-apis.md).
Never print the key. Never write the key into shared files or the repo.

Shared month tracker (payments): /workspace/shared/spend/xai-month.md
Local ledger (per-call usage): data/spend/ledger.jsonl under the story-engine root.
Warn at $40, hard stop at $50 of the monthly xAI total (trundle, Nov 2, 2026: "Monthly limit will now be $50").
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")
ENGINE_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = ENGINE_ROOT / "data" / "spend" / "ledger.jsonl"
SHARED_MONTH = Path("/workspace/shared/spend/xai-month.md")
WARN_USD = 40.0
HARD_STOP_USD = 50.0

# Prices USD per 1M tokens (docs.x.ai, fetched 2026-10-27). Fallback if model unknown.
PRICE_TABLE = {
    "grok-build-0.1": (1.00, 2.00),
    "grok-4.20-0309-non-reasoning": (1.25, 2.50),
    "grok-4.20-0309-reasoning": (1.25, 2.50),
    "grok-4.3": (1.25, 2.50),
    "grok-4.5": (2.00, 6.00),
    "grok-4.6": (2.00, 6.00),
    "grok-4.7": (2.00, 6.00),
}


def _now_ct() -> datetime:
    return datetime.now(CT)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = PRICE_TABLE.get(model, (2.00, 6.00))
    return (prompt_tokens / 1_000_000.0) * pin + (completion_tokens / 1_000_000.0) * pout


def local_month_spend(now: datetime | None = None) -> float:
    if not LEDGER_PATH.exists():
        return 0.0
    month = (now if now is not None else _now_ct()).strftime("%Y-%m")
    total = 0.0
    for line in LEDGER_PATH.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = row.get("ts_ct") or ""
        if ts.startswith(month):
            total += float(row.get("cost_usd") or 0.0)
    return total


class SharedMonth(NamedTuple):
    spent: float
    cap: float


def _month_label(now: datetime) -> str:
    months = (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    )
    return f"{months[now.month - 1]} {now.year}"


def shared_month_payments(
    now: datetime | None = None, path: Path | None = None,
) -> SharedMonth | None:
    """Parse the latest payment total and cap in the selected month's section."""
    now = now if now is not None else _now_ct()
    path = path if path is not None else SHARED_MONTH
    try:
        text = path.read_text()
    except (OSError, UnicodeError):
        return None
    header = re.compile(r"\s*##\s+" + re.escape(_month_label(now)) + r"\s*", re.IGNORECASE)
    pattern = re.compile(r"\$(\d[\d,]*(?:\.\d+)?)\s+(?:spent\s+)?of\s+\$(\d[\d,]*(?:\.\d+)?)")
    in_month = False
    result = None
    for line in text.splitlines():
        if re.match(r"\s*##\s+", line):
            if in_month:
                break
            in_month = header.fullmatch(line) is not None
        elif in_month:
            for match in pattern.finditer(line):
                result = SharedMonth(*(float(value.replace(",", "")) for value in match.groups()))
    return result


def month_total_for_gate(now: datetime | None = None) -> tuple[float, str]:
    """Return (usd, source_note) used for warn/hard-stop gate.

    Uses max(shared prepaid payments if known, local usage ledger) so we never
    under-count against the monthly limit (HARD_STOP_USD).
    """
    total, note, _ = _month_gate_values(now)
    return total, note


def _month_gate_values(now: datetime | None = None) -> tuple[float, str, float]:
    now = now if now is not None else _now_ct()
    shared = shared_month_payments(now)
    if shared is None:
        raise SpendLimitError(
            f"xAI hard stop: no parseable {_month_label(now)} line in {SHARED_MONTH} (fail closed)"
        )
    local = local_month_spend(now)
    total = max(shared.spent, local)
    note = f"shared_payments=${shared.spent:.2f}; local_ledger=${local:.4f}; gate_uses=${total:.4f}"
    return total, note, min(HARD_STOP_USD, shared.cap)


class SpendLimitError(RuntimeError):
    pass


def check_can_spend(est_usd: float = 0.05, now: datetime | None = None) -> None:
    total, note, hard_stop = _month_gate_values(now)
    if total >= hard_stop:
        raise SpendLimitError(
            f"xAI hard stop: month total ${total:.2f} >= ${hard_stop:.2f} ({note})"
        )
    if total + est_usd > hard_stop:
        raise SpendLimitError(
            f"xAI hard stop: ${total:.2f} + est ${est_usd:.2f} would exceed ${hard_stop:.2f} ({note})"
        )
    if total >= WARN_USD:
        print(
            f"[spend-warn] month total ${total:.2f} >= warn ${WARN_USD:.0f} "
            f"(hard stop ${hard_stop:.2f}); {note}",
            flush=True,
        )


def log_call(
    *,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    step: str,
    show_id: str | None = None,
) -> dict:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts_ct": _now_ct().isoformat(timespec="seconds"),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost_usd, 6),
        "step": step,
        "show_id": show_id,
        "bot": "story-bot",
        "key_ref": "env:XAI_API_KEY",
    }
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row
