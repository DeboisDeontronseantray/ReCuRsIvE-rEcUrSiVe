# system-v5-draft (DRAFT, not live)

Next-clip prompt assembler from `docs/PLAN-prompt-assembly-v1.md`, built step by step per `docs/IMPLEMENTATION-STEPS-v1.md`.
Trundle approved the plan and resolved every decision on Oct 31, 2026, 10:32 PM CT. Trundle owns the rules and final approval;
Director New assembles the next prompt from the other systems' outputs and does not invent or own the inputs (D1).

## How a next clip is assembled

`assemble_next.py` wraps the unchanged v42 builder (D2). The previous clip's spec is the base; every slot is copied as is, and
only these change:

- **Continue:** the start frame becomes the previous clip's last still (`<TT_CLIPS>/<prev>_last.png`).
- **Beats:** the previous clip's beats have played, so the new clip's beats come only from the inputs, in this order:
  1. one still-continuity beat from the previous clip's still meta (stub analyzer; the pinned vision model is never called, D3);
  2. raw comments from the spool (D4): last 15 minutes, max 50, sanitized, inserted verbatim with no semantic parsing;
  3. character memory beats from `character-meta/<NN-channel>.yaml`, capped by write-in level (D5).
- Locked threads and the spot type's `thread_holder` are frozen before any change and enter only as `[Thread: Must hold: ...]`
  (D6, D7). FT1–FT4 stay off (D8).

**Aired clips only.** A clip is aired when a playout slot row has `status: "AIRED"` and `aired_at` and its
`occupant_global_no` joins a LINEAGE row's `clip_id` (playout queue-mutation plan section 3.1; pickup.py writes the
status). The previous clip must have aired, or assembly stops with `PreviousClipNotAired`. Memory beats come only from
memories whose `clip_id` aired. Any other status, a missing status, or a missing `clip_id` counts as unaired, and the
assembly report lists what was ignored under `memory.unaired`. The slot sheet and LINEAGE are read-only here.

Budget: 6 beats and 330 words. Comments that don't fit are carried, never dropped. A comment that would fail the gate is held.

## Layout

| Path | What |
|---|---|
| `paths.py`, `tt_paths.example.json` | `TT_*` path keys: env var, then git-ignored `tt_paths.json`, then repo default. The live spool, character-meta and clips folders, slot sheet and LINEAGE have no default and must be configured. |
| `aired.py` | Aired index from the slot sheet + LINEAGE; previous-clip and memory gates |
| `config/assembly.json` | D4 window/cap/block list, beat and word budget, D5 write-in caps |
| `config/vision_model.json` | D3 pinned model id, source and lookup date. Never called. |
| `config/spots.json` | D6 `thread_holder` per spot type (all `null` for now) |
| `contracts.py` | Strict input contracts (D11) |
| `intake.py`, `sanitize.py` | D4 spool intake and comment sanitizer |
| `adapters/` | Read-only bridges to v4 and story-engine; base spec, locked meta, still meta |
| `memory.py` | D5 character meta, write-in, add-only `trait_observations.jsonl` |
| `placement.py` | Beat order, timing and budget |
| `report.py` | Slot split, diff and gate report |
| `assemble_next.py` | The assembler (library + CLI) |
| `dryrun.py` | Fixture dry run: NP16 parity, then NP16 -> NP17 |
| `fixtures/` | Invented fixture data (placeholders only) |

## Run

```
pip install -r requirements.txt
pytest tests
python3 dryrun.py            # writes out/dryrun/night-porter/ (git-ignored)
python3 assemble_next.py --inputs <dir> --base-spec <spec.json> --out out/dryrun/<show> [--spool ...] [--character-meta ...] [--slots ...] [--lineage ...] [--now ...]
```

Tests block all network access. Outputs go only to `out/dryrun/` (or a folder outside the repo). Nothing here edits
`prompts_v44/`, `config/`, `tools/` or `tests/` under `system-v4-20261030`, or story-engine.
