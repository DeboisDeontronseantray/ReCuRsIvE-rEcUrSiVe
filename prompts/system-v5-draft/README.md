# system-v5-draft (DRAFT, not live)

This is the future home of the next-clip prompt assembler described in `docs/PLAN-prompt-assembly-v1.md`. **It contains no assembler code yet.** Implementation waits for Trundle's approval of the plan (PR #3). The build order is `docs/IMPLEMENTATION-STEPS-v1.md`.

Prompt-assembly ownership is OPEN.

## What is here

- `fixtures/night-porter/NP16/base_spec.json`: the NP16 v42 spec, reconstructed from `prompts_v44/odyssey/NP16.{args,meta}.json`. The live builder rebuilds the prompt, args and sidecar byte-for-byte from it. Its image paths are copied verbatim from the live args and are treated as opaque strings.
- `fixtures/night-porter/NP17/` (all PROPOSED contracts, invented data):
  - `locked_meta.json`: derived read-only from `config/static_v41.json`. `threads` is empty on purpose, because which threads are locked is a canon decision for Trundle. FT1–FT4 stay excluded.
  - `still_meta.json`: a stub still description for `NP16_last`. No image file exists. One descriptor restates a look on purpose, so the R-REFDESC filter has something to drop.
  - `comments.jsonl`: 5 raw comments, `{ts, text}` only. The handles (`@PLACEHOLDER_*`) and URLs (`*.invalid`) are placeholders, not real accounts or sites. One comment is a kid hit that must be HELD.
  - `character_memory/MARLO_QUILL.json`: one memory file. It includes a FLASH item that has expired by NP17 and one look item that must never be emitted.
- `tests/`:
  - `test_v5_fixtures.py` and `test_v5_parity_np16.py` are **active**. They check the fixture data, NP16 parity, and the live v44 gate baseline (53 pass, 5 held).
  - `test_v5_acceptance_*.py` are **skipped** (`awaiting plan approval`). They are specs for the build steps.

## Run

```
pip install -r ../../requirements-dev.txt
pytest tests
```

The tests block all network access, write nothing outside `out/dryrun/` (git-ignored), and never edit `prompts_v44/`, `config/`, `tools/` or `tests/` under `system-v4-20261030`.
