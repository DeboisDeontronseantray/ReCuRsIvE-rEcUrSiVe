# PROMPT ASSEMBLY NOTE v1
Version: v1 · Date: Oct 31 2026 · Status: DRAFT — NOT LIVE. Nothing here changes live prompts, configs, code or prompts_v44.
Ownership of prompt assembly is OPEN. No bot is assigned to any input below.

## Purpose
Describe how the NEXT clip prompt could be assembled from four inputs — locked meta, previous-clip stills, raw comment text, character memory — using assemblers and layers that already exist. Canon = what plays out over time; only a few threads are locked, everything else is fluid.

## Assemblers that exist (read Oct 31)
- `/workspace/streaming/story-engine/engine/assemble_prompt.py` (473 lines; copies in `harness/phase2/engine_copy/` and backups). `LAYER_NAMES = ["global","channel","format","show_or_ad","shot","commenter"]`; `PROTECTED` layers; `BODY_ORDER`; `assemble()`, `assemble_locked()`, `prev_last_frame()`, `load_mutations()`, `densify()`, `assemble_full_density()` (→ `bundle_assembler.assemble_bundle`). Wired for Ch4 only (`CHANNEL_DIRS = {4: ...}`).
- Live chain: `prompts/system-v4-20261030/tools/build_prompt_v42.py` wrapping `build_prompt_v41.py` `build()`. Fixed slot order: [Look] [Setting] [Cast] → Continue from <IMAGE_0> → Shot → Eyelines → timed beats → ending line → [Rules]. Imaged items = name + image tag only.
- Layers/meta: `tools/layers_v4.py` (`TIER_LIFE` FLASH/SCAR/MARK/LEGEND, `DECAY_CLIPS=3`, `fixed_threads()`, `tier_alive()`, `carry_text()`, `SAFETY_POOL`).
- Gate: `tools/apply_check_v44.py` `check()` = gate v4.2 + 16-ad R-REF exemption (`config/ref_image_exemptions.json`).

## The four inputs
1. **Locked meta** (only continuous threads + world rules). Today: `config/static_v41.json` intangible fields (2 shows: THE NIGHT PORTER, BLACK ICE); `config/fixed_threads.json` FT1–FT4 = PENDING proposal, OFF. Maps to: [Setting]/[Cast] brackets and rules; assemble_prompt `global`/`channel`/`show_or_ad` (PROTECTED). Gate: apply_check_v44 + rules bracket. Owner: OPEN.
2. **Previous-clip stills + AI image analysis → short descriptive meta.** Today: stills in `state_stills_v42/` (8 PNGs, crops by eye, awaiting review); `prev_last_frame()` finds the prior last frame; v41 adds "Continue from <IMAGE_0>" when `start_frame` set. Image analysis: OPEN (no tool). Maps to: Continue slot + `carry_text()` (fluid tiers). Gate: R-REF (reference image hard rule, 16 exempt ads), no look into camera. Owner: OPEN.
3. **Raw comment text** (sanitized, no handles). Today: `commenter` layer + `load_mutations()`, `assemble_full_density()` — experiments, not wired into build_prompt_v42. `config/commenter_images.json` enabled=false. Chat reader/intake: OPEN. Maps to: timed beats / fluid meta only, never PROTECTED layers. Gate: strip handles (`NEVER_WORDS` pattern exists for names only), no commenter images, apply_check_v44. Owner: OPEN.
4. **Character memory** (slow writing-in when summoned). Today: cast = name + image tag (v42); `prompts/locks/` exists for lock files. Memory store and background process: OPEN. Maps to: [Cast] slot (name/tag) + beats for what they remember. Gate: R-REF, R-REFDESC (no written look when image attached). Owner: OPEN.

## Assembly order sketch
locked meta → [Look][Setting][Cast] (+ character memory as name/tag) → Continue from <IMAGE_0> (prev still) → Shot → Eyelines (never lens) → beats (still-analysis meta + fluid carry + sanitized comments) → ending line → [Rules] → apply_check_v44 → HOLD for Trundle yes. Masters stay pure; tags/genealogy in post (CNB).

## OPEN
- Owner of assembly (and of each input)
- Which assembler is the base (assemble_prompt.py vs build_prompt_v42)
- Image-analysis tool for stills
- Comment intake / chat reader
- Character memory store + summon/write-in process
- Per-spot structure, thread-holder per lineup spot, learned expectation per video type
- Canon promotion from what played out (layers_v4 tiers partial)
- FT1–FT4 remain off pending Trundle
