# CHARACTER-META test fixtures

Synthetic, scrubbed example data for plan review and future unit tests. Not live bibles or ledgers.

| File | Purpose |
|---|---|
| `bible-v2.fixture.yaml` | Read-only copy of Ch 4 Military Boutique continuity bible v2 (cast ids and locked fields). The live bible on the box is never modified. |
| `lineage-sample.jsonl` | Twenty sample LINEAGE rows (Ch 4 ads/overlays). **No `aired` / `air_yes` fields** — promotion tests will need synthetic aired flags or a fixture extension after the lineage agent lands those fields. |

Paths inside rows point at historical box locations; they are labels only in git.
