# CHARACTER-META test fixtures

Synthetic, scrubbed example data for plan review and future unit tests. Not live bibles or ledgers.

| File | Purpose |
|---|---|
| `bible-v2.fixture.yaml` | Read-only copy of Ch 4 Military Boutique continuity bible v2 (cast ids and locked fields). The live bible on the box is never modified. |
| `lineage-sample.jsonl` | Twenty sample LINEAGE rows (legacy; no `aired` — missing counts as not aired). |
| `lineage-with-aired.jsonl` | Synthetic `aired: true/false` for unit tests. |
| `lineage-with-status-aired.jsonl` | Rows with `status` / playout AIRED (no `aired` until deriver runs). |

Paths inside rows point at historical box locations; they are labels only in git.
