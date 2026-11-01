# Media Librarian New — LINEAGE `aired` hook

When a clip reaches **AIRED** status in the playout / comment-prompt queue (terminal state `AIRED`; see Ch 4 bible `prompt_queue_rule.read_aliases`), Media Librarian New (or the lineage validator after it validates the row) should record a **derived** aired flag without rewriting existing LINEAGE history.

## Call site (AIRED time)

```python
from pathlib import Path

from lineage.derive_aired import append_aired_derivation_for_clip

# `row` is the LINEAGE JSON object for the clip (must include clip_id).
# Prefer append mode to a dedicated derivations file; never mutate the live ledger in place.
append_aired_derivation_for_clip(
    Path("/path/to/LINEAGE-aired-derivations.jsonl"),
    row,
    apply=True,
)
```

The helper is **idempotent**: if that `clip_id` already has an `aired_flag` derivation (or `aired: true` on a prior patch), it appends nothing.

## Batch backfill (copies only)

```bash
python -m lineage.derive_aired \
  --input tests/fixtures/character-meta/lineage-with-status-aired.jsonl \
  --output /tmp/LINEAGE-derived.jsonl \
  --mode enrich
# add --apply to write; omit for dry-run JSON report
```

- **Default:** dry-run prints `would_mark` clip ids.
- **`--apply`:** writes **only** to `--output` (never `--input`).
- **Live paths refused** unless `--allow-live-paths` (Trundle yes only):
  - `/workspace/thunder-trundle/lineage/LINEAGE.jsonl`
  - any path under `streaming/story-engine/genealogy/`

## Which ledger is canonical?

**Open (Trundle):** which on-box `LINEAGE.jsonl` is canonical for a channel. This code only accepts explicit `--input` / `--output` paths.

## Character-meta promotion

`charmeta.promote` joins observations to LINEAGE via `lineage.aired.build_aired_index`. Pass the **derived** ledger (enriched copy or base + derivations merged with `merge_lineage_with_derivations`) as `--lineage`.
