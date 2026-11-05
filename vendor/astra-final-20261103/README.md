# Final offline foundation

> Build on, don't redo, the earlier offline prototypes

Matches order: yes. This package adopts the earlier package prototype and hardens it in Tasks 1–11 order. The final synthesis wins over the original job order. All writes, temporary databases and reports stay here. External prototypes, sources and shared logs remain read-only. No network, live air, renders, spend, bot messages or git operations.

Earlier foundation: coordination/astra-lifecycle-20261103. Additional recovery, storage and character-still design evidence: /workspace/codex-tt-astra-buildout-20261103. Source hashes are recorded before changes. This is a separate offline authority, never a production migration.

Run from this directory (installed local Python and jsonschema only; no installs):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -m astra_lifecycle.demo --out reports/ch4-another-run
```

The suite uses fresh temporary directories under runtime/ and removes only its own fixtures. The cycle refuses to overwrite an existing database. For an I/O-guarded cycle, import `offline_guard` from verify, install it with `sys.addaudithook`, then call `astra_lifecycle.demo.run` with a new directory under this package. All runtime database paths are confined to this package even without the harness. No production migration is automatic.

See ASTRA-BUILD-OUT-20261103.md for task acceptance, file inventory and blockers; reports/ch4-cycle/CH4-OFFLINE-CYCLE.md for the complete saved cycle; INTEGRATION.md for trust and rollout boundaries; reports/test-results.txt for all 91 named tests. The original 67-test suite was retained, with two alias tests corrected to match the synthesis, and 24 additional tests were added.
