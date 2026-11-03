#!/usr/bin/env python3
"""Fail if the owner's real first name appears as a standalone word in tracked text.

The denylisted token is never stored in this repository. CI may set ``OWNER_REAL_NAME_B64``
(base64 of the lowercase token) for an explicit scan; otherwise a SHA-256 of that token is used."""
from __future__ import annotations

import base64
import hashlib
import os
import re
from pathlib import Path

SCAN_ROOTS = (
    "charmeta",
    "lineage",
    "tests",
    "prompts",
    "docs",
    "scripts",
    "story-engine/engine",
    "story-engine/live",
    "story-engine/rules",
    "story-engine/templates",
    "story-engine/configs",
)
REPO = Path(__file__).resolve().parents[1]
# sha256(lowercase denylisted owner first name) — token itself is not stored here
TOKEN_SHA256 = "c850c75d30a9360f81eff0a01abcf9125ba034ef9a2dd9f95bbc073a60032299"

SKIP_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "out",
}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".jsonl",
    ".txt",
    ".sh",
    ".toml",
    ".cfg",
    ".ini",
    ".rst",
}
WORD = re.compile(r"(?<![A-Za-z])([A-Za-z]+)(?![A-Za-z])")


def secret_token() -> str | None:
    raw = os.environ.get("OWNER_REAL_NAME_B64", "").strip()
    if not raw:
        return None
    return base64.b64decode(raw).decode().lower()


def iter_files() -> list[Path]:
    out: list[Path] = []
    for root_name in SCAN_ROOTS:
        root = REPO / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.is_relative_to(REPO / "scripts") and path.name == "ci_name_scan.py":
                continue
            out.append(path)
    return out


def main() -> int:
    explicit = secret_token()
    hits: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in WORD.finditer(text):
            tok = match.group(1).lower()
            if explicit is not None and tok == explicit:
                hits.append(str(path.relative_to(REPO)))
                break
            if hashlib.sha256(tok.encode()).hexdigest() == TOKEN_SHA256:
                hits.append(str(path.relative_to(REPO)))
                break
    if hits:
        print("Denylisted owner real-name token found as a whole word in:", file=os.sys.stderr)
        for h in sorted(set(hits)):
            print(f"  - {h}", file=os.sys.stderr)
        return 1
    print("Name denylist scan: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
