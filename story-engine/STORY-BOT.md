# Story Bot engine (private copy)

Private adaptation of toastedsugar/AI_Slop_Novels for the Thunder trundle network (Ch 4 Military Boutique).
**No git remote. Do not push, open issues/PRs, or change Rohan's repo.**

## Key
- Box env var `XAI_API_KEY` (also accepted: `GROK_API_KEY`)
- Documented in `/workspace/shared/INVENTORY/accounts-subs-apis.md`
- Never print the key; never write it into shared files or this repo

## Layered configs
`configs/channels/*.yaml` < `configs/shows/*.yaml` < `configs/slots/*.yaml`
Merge helper: `python -m app.cli merge-config --channel 4 --show forward-supply --slot smoke-outline`

## Smoke test (Channel 4 Military Boutique)
```bash
cd /workspace/streaming/story-engine/server
source ../.venv/bin/activate
python -m app.cli smoke --channel 4 --show forward-supply --slot smoke-outline --model grok-cheap
```
Output under `data/smoke/`. CNB export is **local only** — do not hand to CNB until trundle reviews.

## Spend
- Local ledger: `data/spend/ledger.jsonl`
- Shared month tracker checked: `/workspace/shared/spend/xai-month.md`
- xAI cap: see state/CURRENT-RULES.md (v48 is inconsistent on the cap)

## UI
React client label soft-renames only; UI build skipped by default.
