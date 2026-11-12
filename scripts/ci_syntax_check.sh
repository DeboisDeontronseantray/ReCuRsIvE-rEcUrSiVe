#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== Python compileall (syntax) =="
python3 -m compileall -q charmeta lineage tests prompts scripts astra_lifecycle de-parity streaming story-engine/engine story-engine/live 2>/dev/null \
  || python3 -m compileall -q charmeta lineage tests prompts scripts astra_lifecycle de-parity streaming story-engine/engine

echo "== YAML parse (PyYAML) =="
python3 - <<'PY'
import sys
from pathlib import Path

import yaml

root = Path(".")
paths = list(root.glob("**/*.yaml")) + list(root.glob("**/*.yml"))
bad = 0
for p in paths:
    if any(x in p.parts for x in (".git", "__pycache__", "node_modules", ".venv")):
        continue
    try:
        yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as exc:
        bad += 1
        print(f"YAML error in {p}: {exc}", file=sys.stderr)
raise SystemExit(1 if bad else 0)
PY

echo "Syntax checks passed."
