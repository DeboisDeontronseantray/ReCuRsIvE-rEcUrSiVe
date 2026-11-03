#!/usr/bin/env python3
"""Lowercase owner references (Trundle/TRUNDLE) in story-engine prose; keep #20 hard-limits and brand lines."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "story-engine"
README = ROOT / "README.md"

SKIP = {
    ENGINE / "live/tests/test_legacy_names.py",
    ENGINE / "rules/hard-limits.yaml",  # address_user_as + b64 ban unchanged; fix comment only
}

BRAND_KEEP = re.compile(
    r"Thunder Trundle Workshop|"
    r'address_user_as:\s*\["Trundle", "Thunder Trundle"\]|'
    r'"Trundle", "Thunder Trundle"'
)


def transform_line(line: str) -> str:
    if BRAND_KEEP.search(line):
        return line
    out = line
    out = re.sub(r"\bTRUNDLE\b", "trundle", out)
    out = re.sub(r"\bTrundle's\b", "trundle's", out)
    out = re.sub(r"\bTrundle\b", "trundle", out)
    return out


def transform_text(path: Path, text: str) -> str:
    if path in SKIP:
        return text
    if path == ENGINE / "rules/hard-limits.yaml":
        lines = text.splitlines(keepends=True)
        if lines and "Trundle's own yes" in lines[0]:
            lines[0] = lines[0].replace("Trundle's own yes", "trundle's own yes")
        return "".join(lines)
    if path == README:
        return text.replace("Thunder Trundle prompt-assembly", "thundertrundle prompt-assembly").replace(
            "Thunder Trundle home AI TV network", "thundertrundle home AI TV network"
        )
    if path.suffix not in {".md", ".yaml", ".yml", ".json", ".py"}:
        return text
    return "".join(transform_line(line) for line in text.splitlines(keepends=True))


def main() -> int:
    changed: list[Path] = []
    targets = [README] + [p for p in ENGINE.rglob("*") if p.is_file()]
    for path in targets:
        if not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = transform_text(path, raw)
        if new != raw:
            path.write_text(new, encoding="utf-8")
            changed.append(path.relative_to(ROOT))
    for rel in sorted(changed):
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
