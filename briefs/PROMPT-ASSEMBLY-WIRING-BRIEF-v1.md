# PROMPT ASSEMBLY WIRING BRIEF v1
Version: v1 · Date: Oct 31 2026 · Status: DRAFT — NOT LAUNCHED. Cloud Agent brief; PLAN FIRST, no code until Trundle approves the plan.
Prompt-assembly ownership: OPEN. Build a neutral module; assign no bot.
Prior note: `handoffs/current-job/PROMPT-ASSEMBLY-NOTE-v1.md`.

## 1. Goal
Assemble the NEXT clip prompt from four inputs:
- (a) Locked meta: only the few continuous threads and world rules. Everything else is fluid.
- (b) Previous-clip stills → AI image analysis → short descriptive meta.
- (c) Raw comment text: sanitized. Contributor handles are never in prompts. Commenter images stay OFF.
- (d) Character memory, with slow writing-in when a character is summoned.
Canon = what plays out over time. Promotion uses the existing tiers in `layers_v4.py` (FLASH 1 clip → SCAR episode → MARK season → LEGEND permanent). Do not set canon up front.

## 2. Existing pieces (read Oct 31)
- `/workspace/streaming/story-engine/engine/assemble_prompt.py`: `LAYER_NAMES=["global","channel","format","show_or_ad","shot","commenter"]`. Functions: `assemble()`, `assemble_locked()`, `prev_last_frame()` (last frame), `load_mutations()` (comment mutation), `densify()`, `commenter_allowed()`, `assemble_full_density()` (comment bundling → `bundle_assembler.assemble_bundle`). Wired for Ch4 only (`CHANNEL_DIRS`).
- `prompts/system-v4-20261030/tools/build_prompt_v42.py`: `build(spec,strict)`, `strip_desc()`, `write()`. It wraps `build_prompt_v41.py` (`build()`, `rules_bracket()`, `beat()`, `dialogue()`).
- `tools/layers_v4.py`: `TIER_LIFE`, `fixed_threads()`, `tier_alive()`, `carry_text()`, `rng()`.
- `tools/apply_check_v44.py`: `check()`, `exempt_ids()` (16-ad R-REF exemption via `config/ref_image_exemptions.json`).
- `tools/regen_v44.py` produced `prompts_v44/` (for example `prompts_v44/odyssey/NP01.args.json`, `NP01.meta.json`).
- Tests: `tests/test_v4.py … test_v48.py` (67 tests per handoff).
- Config: `config/static_v41.json` (THE NIGHT PORTER, BLACK ICE), `config/fixed_threads.json` (FT1–FT4, OFF), `config/commenter_images.json` (enabled=false).
- Stills: `state_stills_v42/`, 8 PNGs (BEAR_P07-1, DALE_P12-1, DEV_P08-1, MAE_P03-2, OSCAR_P08-1, RITA_P07-1, SABLE_P09-1, VIK_P09-1). Crops were set by eye and await review. **None are Night Porter.**

**Base assembler: OPEN.** Recommended default: use build_prompt_v42 as the output contract. It keeps the fixed slot order [Look][Setting][Cast] → Continue from <IMAGE_0> → Camera → Eyelines → timed beats → ending line → [Rules], and the apply_check_v44 gate. The new module produces a v42 `spec` and calls `build()`. Port only `prev_last_frame` / `load_mutations` / bundling logic from assemble_prompt.py as adapters. Why: v42 is the live path that made the 53 ready prompts and already passes the gate and tests, while assemble_prompt.py is Ch4-only and its header names Director as owner.

## 3. Input contracts (all PROPOSED)
Location: `prompts/system-v5-draft/inputs/<show>/<clip_id>/`. Fixtures go in `prompts/system-v5-draft/fixtures/`.
- `locked_meta.json`: `{show, channel, world_rules:[str], threads:[{id, text, tier:"LEGEND"|"MARK", locked:true}], source:"static_v41.json"}`. Read-only from static_v41. FT1–FT4 excluded while OFF.
- `still_meta.json`: `{prev_clip_id, still_path, analyzer:"stub", descriptors:[str ≤12 words], tier:"FLASH"}`. Interface `analyze_still(path)->list[str]`. Stub returns fixture text. Real vision model: OPEN.
- `comments.jsonl`: `{ts, text}` per line. Sanitizer drops @handles, URLs and names matching the existing `NEVER_WORDS` pattern. No handle field is ever stored. No image fields.
- `character_memory/<NAME>.json`: `{name, image_tag, memories:[{text, tier, since_index}], summon_count, writein_level 0–3}`. Slow write-in: each summon raises `writein_level` by at most 1, and the level caps how many memory beats get emitted. Never written looks (R-REFDESC).
Fixtures: one Night Porter clip (NP16 → next), a stub still descriptor, 5 raw comments including handles and a URL, and one character memory file.

## 4. Hard constraints
- Do not modify `prompts_v44/`, `prompts_v4*`, `config/`, `tools/`, `tests/` or any live file. New code goes only in `prompts/system-v5-draft/`.
- All 67 existing tests must still pass. Output must pass `apply_check_v44.check()`: nobody looks into the camera, reference-image rule (16 exempt ads), R-NOHANDLES, masters pure, FT1–FT4 off.
- No network calls, renders, spending or messages. The image analysis is a stub interface.

## 5. Deliverables + acceptance
1. A plan document (first step; stop for Trundle's approval).
2. `system-v5-draft/assemble_next.py` plus adapters and the sanitizer.
3. New tests: sanitizer drops handles, comment text never lands in [Cast]/[Rules], write-in is capped, and tier decay works via `tier_alive()`.
4. A dry run that produces the next prompt for one Night Porter clip from fixtures. The output is written only under system-v5-draft/out/.
5. A diff against the current builder output for the same spec (`prompts_v44/odyssey/NP*.args.json`). The only differences may be in beats and Continue.
6. Gate pass report, and existing tests 67/67.

## 6. OPEN
Assembly owner and per-input owners · base assembler · vision model · comment intake/chat reader · character memory store/background process · per-spot structure / thread-holder / learned expectation per video type · canon promotion counter (partial) · FT1–FT4 off · no Night Porter stills exist · repo (below).

## 7. Repo prerequisite (checked read-only Oct 31)
- `/workspace/streaming/story-engine`: git repo on branch `main`, last commit `ed705fb "Version 3 as good as done"`, **no remote configured**, 68 uncommitted changes.
- `/workspace/thunder-trundle` (including `prompts/system-v4-20261030`): **not in any git repo**.
- Cloud Agents need a GitHub or Cursor Origin repo. Before launch, the code must be put into a repo and pushed. OPEN, needs Trundle's yes. Nothing was pushed.

## 8. Recommended model
Claude Opus 5.5 (`claude-opus-5-5`), effort high, for plan and implementation: multi-file Python integration with strict rule constraints. Alternative: GPT-5.3 Codex (`gpt-5.3-codex`) for a cheaper implementation pass after the plan is approved.
