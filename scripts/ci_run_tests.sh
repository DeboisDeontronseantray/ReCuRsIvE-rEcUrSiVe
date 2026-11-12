#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install -q -r requirements-dev.txt
python3 -m pip install -q -r prompts/system-v5-draft/requirements.txt

echo "== root tests =="
python3 -m pytest -q -p no:cacheprovider tests

echo "== comment slot policy =="
python3 story-engine/tests/test_queue_policy.py

echo "== v5 draft tests =="
(
  cd prompts/system-v5-draft
  python3 -m pytest -q -p no:cacheprovider
)

echo "== v5 dryrun =="
(
  cd prompts/system-v5-draft
  set +e
  PYTHONPATH="$ROOT" python3 dryrun.py
  rc=$?
  set -e
  python3 - <<'PY'
import json
from pathlib import Path
summary = json.loads(Path("out/dryrun/night-porter/SUMMARY.json").read_text())
assert summary["parity_NP16_byte_identical"] is False, summary
print("dryrun reported stale NP16 live snapshot (expected; v44 pack stays locked to v43)")
PY
  if [ "$rc" -ne 1 ]; then
    echo "expected dryrun exit 1 for the stale snapshot, got $rc"
    exit 1
  fi
)

echo "== legacy v4 tests =="
(
  cd prompts/system-v4-20261030
  python3 -m pytest -q -p no:cacheprovider tests
)

echo "All CI test suites passed."
