# Offline acceptance coverage

| Contract / failure | Evidence | Scope |
|---|---|---|
| D09 / approval-as-aired | test_D09_*; test_closed_table_rejects_every_unlisted_edge; Task01 | Receipt shape, signature, joins, foreign authority, replay, concurrent callbacks and real process-death rollback |
| D13/D14 / unseen consumption | merged-but-never-aired, pulled-after-assembly, failed reoffer, Task03 | Durable original text, versioned filtering, missed requests remain eligible |
| D08 | local_export/episodes_done tests | Export cannot advance canon |
| B01 | approval/head/preemption tests | Approval does not settle premise; replacement preserves unseen IDs |
| B04 | arbitrary-setter/terminal-release tests | Closed prompt transitions; re-review after release |
| D15/D10/D16/D17 | character/tier tests; Task04 | Aired-only updates, distinct later reuse, expiry, hashed content, still state/history |
| A07 | crash-after-seen; Task10 | Replay durability and idempotency; no live transport |
| D12 | continuity tests; Task05 | Queued/render/air gates block malformed or stale structural input |
| B15 | scheduler-independent eligible/backlog tests | No dependency on unbuilt scheduler |
| Inventory and approval | inventory/price/batch tests; Task06 | Logical exclusion, exact hashes and route, diagnostic blockers, atomic fixture reservations |
| Registry and fixes | compatible-fix tests; Task07 | Durable evidence and reviewed resolution; no portal/pivot still repair |
| Versions | metadata/crossover tests; Task08 | Fluid scaffolding aliases, historical reads, scoped crossover evidence, notes not rules |
| Commenter ledger | observation/handle tests; Task09 | Requested/appeared distinction, aired versus landed, privacy and misses |
| Ch4 full cycle | test_entire_ch4_cycle_and_persisted_snapshot_validate; reports/ch4-cycle | Exactly one canon commit, updated still, expiry, unseen survival, dependency invalidation |
| Source/read-only boundary | reports/source-integrity.json; verify.py | Initial source hashes unchanged; no external I/O attempted during verification |
| Live capture / real moderation / visual and audio QC / production signer / production spend | Not exercised | Explicit integration blockers; fixture evidence cannot establish them |

Tests use existing media bytes and synthetic observations. No timing/regex/schema check establishes real visual continuity or creative quality. Every illegal state-machine class in the supplied failure report has a retained negative test; no production caller deployment is claimed.
