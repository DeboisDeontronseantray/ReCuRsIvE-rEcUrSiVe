# IMPLEMENTATION STEPS v1: prompt assembly (small-PR breakdown)

Version: v1 · Date: Nov 1 2026 · Status: **APPROVED.** Trundle approved the plan (PR #3) and resolved every open decision on Oct 31, 2026, 10:32 PM CT. Steps 1–8 run on `impl/prompt-assembly-v1`.
Plan: `docs/PLAN-prompt-assembly-v1.md` §9. Paths: `docs/PATHS-INVENTORY.md` (PROPOSED inventory; **D10 RESOLVED as inventory only**, accepted Oct 31, 2026 — no migration yet).
**Ownership (D1 RESOLVED):** Trundle owns the rules and final approval. Director New assembles the next prompt from the other systems' outputs; it does not invent or own the inputs. Code and config carry no owner fields.

**All decisions RESOLVED.** Accepted earlier on Oct 31, 2026: D9, D10 (inventory only), D12, dry-run → ignored `out/dryrun/`, and D9b (technical default). Resolved by Trundle on Oct 31, 2026, 10:32 PM CT:

- **D1 Ownership:** Trundle owns the rules and final approval. Director New assembles the next prompt from the other systems' outputs. It does not invent or own the inputs.
- **D2 Base assembler:** wrap the v42 builder. Move to a hybrid only if a clear gap appears, and document that gap.
- **D3 Vision model:** one read-only lookup of xAI's public model docs (no key, no spend). Pin the strongest current Grok model that accepts image input in `config/vision_model.json` (config, not code) with source and date. Do not call the model.
- **D4 Comment intake:** raw collection plus insertion only, with no semantic parsing. Source: the live comment spool via a configured path (fixtures in tests). Window: last 15 minutes, cap 50 comments. Block list empty but configurable. Contributor handles and IDs never reach prompt text (enforced by test); R-NOHANDLES keeps passing.
- **D5 Character memory:** `character-meta/<NN-channel>.yaml` keyed by cast id, plus an add-only `trait_observations.jsonl`. Write-in levels cap memory beats per prompt.
- **D6 Per-spot structure:** a minimal `thread_holder` field per spot type, short and locked before any mutation.
- **D7 Canon promotion:** keep FLASH, SCAR, MARK and LEGEND. Locked threads enter the prompt only as hard constraints, never as soft suggestions.
- **D8:** FT1–FT4 stay OFF until Trundle explicitly turns them on.
- **D11:** the proposed input contracts are accepted (with D5's memory store). `prompts/system-v5-draft/` is the working folder.

## 1. Rules every step follows

- New code goes only under `prompts/system-v5-draft/`. Do not edit `prompts_v4*/`, `config/`, `tools/` or `tests/` under `system-v4-20261030`. Do not edit `story-engine/`. The one exception is step 9, which needs its own approval (Decision 10).
- No network, no render or spend APIs, no renders. `tests/conftest.py` blocks sockets for every test.
- Commenter images stay OFF. Handles never go into prompts or outputs. FT1–FT4 stay off.
- Dry-run outputs go only to `prompts/system-v5-draft/out/dryrun/`, which is git-ignored and never committed (**D12 RESOLVED**, accepted by Trundle Oct 31, 2026).
- **Every PR** must keep these baselines green:
  - legacy suite `pytest tests` in `prompts/system-v4-20261030` at **66 passed, 1 skipped** (`test_static_flip_v3` skips when `static_flip_v2.py` or its REF media is absent; D9b);
  - live v44 gate at 53 PASS / 0 FAIL / 5 held;
  - NP16 parity byte-identical;
  - all active `system-v5-draft` tests green.
- Un-skipping: each step replaces the module-level `pytestmark = pytest.mark.skip(reason="awaiting plan approval")` with per-test skips. It removes the skip **only** from the specs it implements. A step is done when its specs pass unmodified, or when changes to a spec are listed and justified in the PR body.

## 2. Steps

Current test state on this branch: `system-v5-draft` has **13 active (passing) and 45 skipped** tests.

| Step | PR scope | Files touched | Tests | Acceptance check | Depends on decision | Model / effort |
|---|---|---|---|---|---|---|
| **0** (done, PR #1) | Import the A1–A15 checker and add a path fallback | `prompts/experiments/odyssey-design-20261030/tools/apply_check.py` (byte copy), `tools/apply_check_v4.py` (3-line env/relative fallback), `requirements-dev.txt` | legacy suite | **66 passed, 1 skipped.** Live-box behavior unchanged. | **D9 RESOLVED**, accepted by Trundle Oct 31, 2026 | n/a |
| **0b** (done, PR #1) | Skip `test_static_flip_v3` when v2 or REF media is absent. Do **not** import the CC-BY-SA `.ogv` clip. Only the test changes. | `prompts/system-v4-20261030/tests/test_v4.py` | `test_static_flip_v3` | **66 passed, 1 skipped.** On the live box the test still runs. | **D9b RESOLVED** (technical default) | n/a |
| **1** | Scaffold, path config, read-only bridges | `paths.py`, `tt_paths.example.json`, `adapters/__init__.py`, `adapters/v4_bridge.py`, `adapters/story_engine_bridge.py`. `.gitignore` rule for `tt_paths.json`. | new `test_v5_paths.py`: env var beats `tt_paths.json` beats repo default; no `/workspace` literal in any `system-v5-draft/*.py`; bridges import only pure symbols (`NEVER_WORDS`, `PROTECTED`, `bend`, `HARD`, `cats`) | 13 active + new pass. `git diff --stat` shows only `system-v5-draft/` and `.gitignore`. | Plan approval (resolved), D11 (resolved) | GPT-5.3 Codex, medium |
| **2** | Input contracts | `contracts.py` | un-skip the 8 contract specs in `test_v5_acceptance_inputs.py` | Unknown, handle and image keys are hard errors. `FT*` ids are rejected. A mismatch with static_v41 is rejected. | D11 (resolved), D4 (resolved) (`{ts, text}` row), D5 (resolved) (channel YAML + `trait_observations.jsonl`) | Claude Opus 5.5, medium |
| **3** | Base-spec adapter | `adapters/base_spec.py` (load, next clip id, parity helper) | parity tests stay active; new `test_v5_base_spec.py` (NP16 → NP17 id; base spec never mutated) | NP16 parity still byte-identical | D2 (resolved) (Option A, wrap v42) | GPT-5.3 Codex, medium |
| **4** | Comment sanitizer | `sanitize.py` | un-skip the 8 sanitizer specs | Handles (including ones longer than 15 characters; see §4), e-mails, URLs and NEVER_WORDS are dropped. Kid hits are HELD. Camera looks are bent. Brackets are stripped. | D4 (resolved) (configurable block list, empty; spool intake with 15 min / 50 cap window) | Claude Opus 5.5, high |
| **5** | Locked-meta and still adapters, plus Ch4 fixtures | `adapters/locked_meta.py`, `adapters/still_meta.py` (`StubAnalyzer`, `filter_descriptors`, `next_start_frame`), `fixtures/black-ice/BI01/base_spec.json`, `fixtures/black-ice/BI02/*` | un-skip the 3 still specs; new `test_v5_locked_meta.py` | The stub never opens files. Look descriptors for imaged cast are dropped. FT excluded. The Ch4 fixture is **synthetic** (no Ch4 prompt exists in `prompts_v44`) with placeholder ref paths (no photoreal Ch4 sheets exist yet). | D3 (resolved) (model pinned in config, never called; stub analyzer only), D7 (resolved) (locked threads as hard constraints only), D8 (resolved) (FT off) | Claude Opus 5.5, medium |
| **6** | Character memory and write-in | `memory.py` (`WRITEIN_CAP`, `summon`, `memory_beats`, proposed-update writer) | un-skip the 5 memory specs | +≤1 level per summon, cap 3. Beats ≤ cap. FLASH expires via `tier_alive()`. No looks. The fixture is never written back. | D5 (resolved) (channel YAML store; cap mapping `{0:0,1:1,2:1,3:2}` in config) | Claude Opus 5.5, high |
| **7** | Beat placement and budget | `placement.py` (raw insertion in timestamp order; **no** `cats()` categorization, per D4) and `spots.py` (`thread_holder` per spot type, frozen before mutation, per D6) | new `test_v5_placement.py`: overflow carried, never dropped; ≤6 beats / ≤330 words; deterministic; thread holder unchanged by comments | Unit tests pass. No prompt text built here. | D4 (resolved), D6 (resolved), D7 (resolved) | Claude Opus 5.5, high |
| **8** | `assemble_next` CLI, report, NP17 dry run | `assemble_next.py`, `report.py` (`slot_split`, DIFF, GATE, assembly provenance) | un-skip all 12 dry-run specs and all 9 canon specs | Dry run writes only to `out/dryrun/night-porter/`. The slot diff vs the current builder changes only beats and Continue. v44 gate 0 FAIL. No live file changes (sha manifest). All 45 specs pass. | D1 (resolved), D2 (resolved), D11 (resolved) | Claude Opus 5.5, high |
| **9** (optional, not started) | Migrate hardcoded paths in existing code | the 34 code files in `docs/PATHS-INVENTORY.md` §2 | legacy suite, v44 gate, NP16 parity | Byte-identical prompt outputs. No change on the live box when no `TT_*` vars are set. | **D10 inventory is RESOLVED** (accepted Oct 31, 2026). **Migration is not approved yet** and still needs its own go-ahead; it touches `tools/`, `tests/`, `story-engine/`. | GPT-5.3 Codex, medium, with Claude Opus 5.5 review |

Still out of v1 scope after the rulings: calling the pinned vision model (D3 pins it only), the background process that writes `character-meta/` (D5; v1 only reads it and emits a proposed update), a canon promotion counter (D7 keeps the tiers), and turning on any FT (D8, Trundle only).

## 3. Interfaces the acceptance specs assume

The specs in `prompts/system-v5-draft/tests/test_v5_acceptance_*.py` call these names. A step may rename them if the PR updates the specs and says why. D4 and D5 change two rows: comments come from the configured spool (`intake.collect`), and memory comes from the channel YAML (`memory.load_channel_meta`), so `load_inputs` covers only the per-clip files.

| Module | Name | Contract |
|---|---|---|
| `contracts` | `load_inputs(dir) -> {"locked_meta","still_meta","comments","memory"}` | Validates every file. Raises `ContractError`. |
| `contracts` | `validate_comment_row(row)`, `validate_locked_meta(lm)` | Raise `ContractError` on unknown, handle or image keys, `FT*` ids, or a static mismatch |
| `sanitize` | `sanitize(text) -> {"text": str or None, "status": "KEPT", "BENT", "HELD" or "DROPPED", "reasons": [str]}` | Runs in order: handles/e-mails → URLs → NEVER_WORDS → `bend()`/`HARD` → bracket strip |
| `adapters.still_meta` | `StubAnalyzer(descriptors).analyze_still(path) -> list[str]` | Never opens `path` |
| `adapters.still_meta` | `filter_descriptors(descs, imaged_names) -> (kept, dropped)` | Uses `apply_check_v42.VIS` |
| `adapters.still_meta` | `next_start_frame(prev_clip_id) -> "<TT_CLIPS>/<id>_last.png"` | Port of `prev_last_frame()`, keyed on clip id |
| `memory` | `WRITEIN_CAP`, `summon(mem) -> mem`, `memory_beats(mem, *, episode, season, clip_index) -> list[str]` | Pure. Never writes the input file. |
| `assemble_next` | `assemble_next(*, inputs_dir, base_spec, out_dir, clip_id) -> {"spec","args","sidecar","assembly"}` | Calls `build_prompt_v42.build(strict=True)` (Option A) and writes outputs under `out_dir` |
| `assemble_next` | `ReferenceImageRequired`, `CommenterImagesOn`, `COMMENTER_IMAGES_CFG` | Pre-build refusals |
| `report` | `slot_split(prompt) -> {"look","setting","cast","continue","camera","eyelines","beats","ending","rules"}` | Splits a v42 prompt into its fixed slots for the diff |

## 4. Notes found while preparing

- **Handle length gap in the live gate.** `apply_check_v42` `R-NOHANDLES` uses `@[A-Za-z0-9_]{2,15}\b`. A token with more than 15 word characters after `@` does not match, because `\b` cannot fall inside a word. X handles max out at 15 characters, but other sources may not. The sanitizer must use an unbounded pattern (spec `test_sanitizer_drops_long_handles_the_gate_regex_misses`). The live gate is **not** changed. This is for Trundle's information only.
- **`bundle_assembler.bend()` does not strip handles**, so the sanitizer has to run before it (plan G8).
- **No Ch4 prompt exists in `prompts_v44`.** The BLACK ICE fixture in step 5 is synthetic and cannot be parity-checked against a live prompt.
- **NP16 parity is complete.** Prompt, args and sidecar all rebuild byte-for-byte from `fixtures/night-porter/NP16/base_spec.json`. This is checked by the active test `test_v5_parity_np16.py`.
