"""Vote-tally stub matching VOTING-DESIGN-20261026.md + the Device Engineer channel-change switcher handoff
(free chat '!vote N', ballot = ready-series channels + Stay, 10-min window, <3 valid votes = Stay, one vote per handle).
Writes tally.json / tally.txt / winner.txt into an output dir (default data/live/tally, NOT the shared live dir). No money, no X."""
import json, re, sys
from collections import Counter
from pathlib import Path
VOTE = re.compile(r"^\s*!vote\s+(\w+)\s*$", re.I)

def tally(chat, ballot, seconds_left, out_dir, min_votes=3):
    seen, counts, unmatched = set(), Counter(), []
    for m in chat:
        v = VOTE.match(m["text"])
        if not v: continue
        opt = v.group(1)
        if opt not in ballot: unmatched.append(m); continue
        if m["handle"] in seen: continue
        seen.add(m["handle"]); counts[opt] += 1
    rows = [{"option": o, "label": ballot[o], "votes": counts[o]} for o in ballot]
    total = sum(counts.values()); top = max(rows, key=lambda r: r["votes"])
    tie = sum(r["votes"] == top["votes"] for r in rows) > 1
    winner = "stay" if total < min_votes or tie else top["option"]
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    (out / "tally.json").write_text(json.dumps({"rows": rows, "seconds_left": seconds_left, "total": total, "unmatched": len(unmatched)}, indent=1))
    (out / "tally.txt").write_text("\n".join(f"{r['option']} {r['label']}: {r['votes']}" for r in rows) + f"\n{seconds_left}s left\n")
    if seconds_left <= 0: (out / "winner.txt").write_text(winner + "\n")
    return winner, rows
