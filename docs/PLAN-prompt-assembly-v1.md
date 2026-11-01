# PLAN: Prompt assembly v1 (next-clip prompt from four inputs)

Version: v1 · Date: Nov 1 2026 · Status: **APPROVED by Trundle (Oct 31, 2026, 10:32 PM CT).** All decisions resolved (§9). Implementation proceeds in `impl/prompt-assembly-v1` following `docs/IMPLEMENTATION-STEPS-v1.md`.
Brief: `briefs/PROMPT-ASSEMBLY-WIRING-BRIEF-v1.md` (prior note: `briefs/PROMPT-ASSEMBLY-NOTE-v1.md`).
**Prompt-assembly ownership: RESOLVED (D1).** Trundle owns the rules and final approval. Director New assembles the next prompt from the other systems' outputs; it does not invent or own the inputs.

---

## 0. Ground truth checked in this repo (Nov 1, read-only)

These facts were checked against the imported snapshot and shape the plan. Nothing was edited.

| # | Fact | Consequence for the plan |
|---|---|---|
| G1 | First run in this repo: `pytest tests` stopped on 1 collection error (**35 passed, 1 error**). *Updated after D9 + D9b accepted Oct 31, 2026:* **66 passed, 1 skipped.** | Acceptance is restated in §7.3. |
| G2 | The original blocker: `tools/apply_check_v4.py:10` execs `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py`. *Updated:* that file is imported (D9) and the path falls back to the repo copy. | The v41/v42/v44 gate chain never depended on it. |
| G3 | `test_v48`/`test_v4` need `cv2` (`opencv-python-headless`) and `numpy`. There is no requirements file for `prompts/system-v4-20261030`. | The new folder ships its own `requirements-dev.txt` (pytest, plus cv2/numpy only to run the legacy suite). |
| G4 | Running `apply_check_v44.check()` read-only over `prompts_v44/*/*.args.json` gives **53 PASS / 0 FAIL**, with 5 held in `BLOCKED/`. This matches `out/gate-v44.json`. | The gate baseline is green and can be re-run read-only as part of acceptance. |
| G5 | `prompts_v44/` stores only the `args` and `meta` outputs, not the input `spec`. Specs were rebuilt by `regen_pending_v4` from experiment folders outside the snapshot. | The NP16 spec must be **reconstructed as a fixture**. |
| G6 | Probe (`/tmp`, not committed): a spec reconstructed from `prompts_v44/odyssey/NP16.{args,meta}.json` and fed to `build_prompt_v42.build(strict=True)` gives a **byte-identical prompt**: same sha256 `f3ddda1b…`, identical `args`, 0 gate FAILs. | The diff baseline in §7.2 is achievable and can be proven with a test. |
| G7 | `build()` treats image paths as strings and never opens them. `state_stills_v42/` and `refs_side/` are absent from the snapshot (images were excluded). There are **no Night Porter stills** (brief §2). | The dry run needs no image files. Still analysis is a stub that returns fixture text. |
| G8 | `story-engine/engine/bundle_assembler.py` and `assemble_prompt.py` both import cleanly. `bundle_assembler.bend()` bends "looks into the camera" and holds kid words, but **passes `@handles` through unchanged**. | The sanitizer must run **before** `bend()`. Both modules can be imported read-only. Nothing needs copying. |
| G9 | `story-engine/queues/COMMENT-PROMPTS.schema.md` rows carry a `handle` field. | Comment intake must drop `handle` (and any author or image field) at load. Fixtures are invented and never copied from `COMMENT-PROMPTS.jsonl`. |
| G10 | `story-engine` suites (`tests/`, `live/tests/`) have 9 collection errors here (missing `/workspace` paths). | Out of scope. They are recorded only as a baseline so nobody mistakes them for a regression. |

---

## 1. Goal

Build the **next** clip prompt from four inputs, without touching any live file:

- (a) **Locked meta**: only the few continuous threads and world rules. Everything else stays fluid.
- (b) **Previous-clip stills, run through image analysis**, giving short descriptive meta (FLASH tier).
- (c) **Raw comment text**, sanitized. It never contains contributor handles, and commenter images stay OFF.
- (d) **Character memory**, written in slowly when a character is summoned.

Canon is what plays out over time. Promotion uses the existing `layers_v4.TIER_LIFE` tiers (FLASH = 1 clip, SCAR = episode, MARK = season, LEGEND = permanent). **No canon is set up front.**

---

## 2. Assembly pipeline

```
inputs/<show>/<clip_id>/               (or fixtures/ for the dry run)
  base_spec.json  locked_meta.json  still_meta.json  comments.jsonl  character_memory/<NAME>.json
        │
        ▼  load + validate (contracts.py; unknown keys -> hard error; handle/image fields -> hard error)
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ 1. base_spec      = previous clip's v42 spec (NP16) -> next clip id (NP17)    │
  │ 2. locked meta    -> assert matches static_v41 (read-only); FT1–FT4 excluded  │
  │ 3. still meta     -> start_frame = prev last frame  => "Continue from <IMAGE_0>" │
  │                     descriptors (FLASH) -> continuity beat text, no looks     │
  │ 4. comments       -> sanitize (handles/URLs/NEVER_WORDS) -> bend()/HARD       │
  │                     -> place into timed beats ONLY                            │
  │ 5. memory         -> tier_alive() filter -> write-in cap -> memory beats      │
  │                     cast entry stays NAME (<IMAGE_n>) only (R-REFDESC)        │
  └─────────────────────────────────────────────────────────────────────────────┘
        │  produce a v42 spec (same keys build_prompt_v42 already accepts)
        ▼
  build_prompt_v42.build(spec, strict=True)  ── unchanged, imported read-only
        │
        ▼
  apply_check_v44.check(prompt, args, spec, sidecar, clip_id=...)  ── unchanged
        │
        ▼
  system-v5-draft/out/dryrun/<show>/<NEXT>.args.json + .meta.json + .assembly.json (provenance; git-ignored, D12 accepted)
  + DIFF vs current builder + GATE report  -> HOLD for Trundle's yes (nothing renders)
```

### 2.1 Where each input lands in the fixed v42 slot order

The slot order stays fixed: `[Look] [Setting] [Cast] → Continue from <IMAGE_0> → Camera → Eyelines → timed beats → ending line → [Rules]`. It is never shuffled.

| Input | v42 `spec` keys it may set | Prompt slot | May **never** set |
|---|---|---|---|
| Base spec (prev clip) | all existing keys, copied from the NP16 fixture | all slots, unchanged | n/a |
| (a) Locked meta | nothing new. It is validated against `static_v41.json`, which `build_prompt_v41` already reads for `[Look]`/`[Setting]`. Optional `thread` key **only if Trundle opts in (D7)** | `[Look]`, `[Setting]` (via static) | `beats`, comments, FT1–FT4 |
| (b) Still meta | `start_frame`, `parent_clip`, plus continuity text inside one beat | `Continue from <IMAGE_0>`, beats | `[Cast]` looks (R-REFDESC), `refs_raw` |
| (c) Comments | text inside `beats[*].text` only | timed beats | `[Cast]`, `[Setting]`, `extra`, `[Rules]`, `camera`, `eyeline_sentence`, `contributors`, `refs_raw` |
| (d) Character memory | memory beat text (capped), plus sidecar memory state | timed beats | written looks for imaged cast, `[Rules]` |

**Diff contract:** compared with the base spec, only `beats` and `start_frame`/`parent_clip` (the Continue line) may change. Every other slot stays byte-identical. This is what §7.2 diffs.

### 2.2 Beat budget

`apply_check_v41` raises `W-beats` (WARN, not FAIL) above 6 `At N s,` beats and `W-words` above 330 words. The assembler keeps the base clip's beat count (NP16 has 3). It folds still, comment and memory content into a small number of extra beats, so the total stays ≤ 6 beats and ≤ 330 words. The exact placement rule ports `bundle_assembler.bundle()` logic: beats grouped by category, so no two conflicting comments share a beat, and overflow moves to the next clip. Overflow is carried, never dropped.

---

## 3. Reuse of existing code (all read-only imports, no copies edited)

| Existing piece | How the new module uses it | Edited? |
|---|---|---|
| `tools/build_prompt_v42.py` → `build(spec, strict)`, `strip_desc()` | **Output contract.** The new module produces a v42 `spec` and calls `build(strict=True)`. It never re-implements slot order. | No |
| `tools/build_prompt_v41.py` → `build()`, `beat()`, `dialogue()`, `rules_bracket()`, `STATIC` | Reached through v42. The assembler emits beats in the shapes `beat()` already formats (`{t,text}`, `{t,who,line,cue}`). `rules_bracket()` is never bypassed. | No |
| `tools/apply_check_v44.py` → `check(..., clip_id)`, `exempt_ids()` | Final gate on every assembled prompt, passing `clip_id` so the 16-ad R-REF exemption is exact. `exempt_ids()` also gates the pre-build ref check (§5). | No |
| `tools/apply_check_v42.py` → `VIS`, `refdesc()` | Pre-filter: drop any still/memory descriptor that would restate a look for an imaged cast member. | No |
| `tools/layers_v4.py` → `TIER_LIFE`, `tier_alive()`, `carry_text()`, `rng()`, `fixed_threads()` | `tier_alive()` filters memory and still items. `carry_text()` handles decay. `rng(clip_id, META, salt)` makes placement deterministic. `fixed_threads()` is read to assert FT1–FT4 are still `PENDING`, so they are excluded. | No |
| `story-engine/engine/assemble_prompt.py` → `prev_last_frame()`, `load_mutations()`, `NEVER_WORDS`, `PROTECTED`, `commenter_allowed()`, `assemble_full_density()` | **Adapters only.** `prev_last_frame()` logic (previous shot id → its last frame) is ported to the still adapter, keyed on clip ids (`NP16` → `NP16_last`) instead of YAML sidecars. `NEVER_WORDS` is imported read-only, not re-typed. `PROTECTED` is reused as the deny list of fields a comment may target. `load_mutations()` shape is **not** reused, because its structured `fields` let commenters target layers. v1 accepts raw text only. | No |
| `story-engine/engine/bundle_assembler.py` → `bend()`, `HARD`, `cats()`, `bundle()`, `fade_text()` | Imported read-only. `bend()` and `HARD` run after the sanitizer. `cats()` and `bundle()` placement logic is ported for beat placement. `fade_text()` is an option for decaying earlier comments (FLASH → gone). | No |

### 3.1 Base assembler: **RESOLVED (D2): Option A, wrap v42**

| Option | Summary | For | Against |
|---|---|---|---|
| **A. v42 as output contract** *(brief's recommended default)* | New module produces a v42 `spec` and calls `build_prompt_v42.build()`. Adapters are ported from `assemble_prompt.py`. | Live path: produced the 53 ready prompts. Gate and 35 runnable tests are green. Fixed slot order. NP16 rebuild is byte-identical (G6). | Comment and memory concepts must be squeezed into `beats`. The two assembler lineages stay separate. |
| B. `assemble_prompt.py` as base | Extend `assemble()`/`assemble_locked()`/`densify()` with still and memory layers. | Already has layered commenter path, `PROTECTED`, locks library, dense mode. | Ch4-only `CHANNEL_DIRS` wiring. Needs `_channel.md`/`_wrapper.md` files under `TT_PROMPTS` that are **not** in the snapshot. Different slot order (`BODY_ORDER`). Its header names a specific owner, which conflicts with ownership being OPEN. Output does not go through `apply_check_v44` today. |
| C. Hybrid | Option A now, plus a later adapter that exports v42 specs into `assemble_prompt` dense mode. | Keeps the door open. | More surface. Defer. |

The plan is written so that **only the build/gate call site differs** between A and B. Adapters, contracts, sanitizer, memory and tests are base-agnostic. Until D2 is decided, any sketch in this document that names `build()` assumes Option A, per the brief.

---

## 4. Input contracts (all **PROPOSED**, pending Trundle)

Location: `prompts/system-v5-draft/inputs/<show>/<clip_id>/`. Dry-run fixtures go in `prompts/system-v5-draft/fixtures/`. Every file is validated on load. Unknown keys are a **hard error**, not a warning. That is what keeps handles and image fields out by construction.

### 4.1 `base_spec.json` (PROPOSED; added by this plan, not in the brief)
The previous clip's v42 `spec`, which is exactly what `build_prompt_v42.build()` accepts. For the dry run it is the reconstructed NP16 spec (G6). A test proves `build(base_spec)` reproduces `prompts_v44/odyssey/NP16.args.json` byte-for-byte before any assembly runs.

### 4.2 `locked_meta.json` (PROPOSED)
```json
{"show": "THE NIGHT PORTER", "channel": "Ch11 Fist Theater",
 "world_rules": ["the hotel adds a floor each time the clock ticks wrong"],
 "threads": [{"id": "NP-T1", "text": "...", "tier": "LEGEND", "locked": true}],
 "source": "static_v41.json"}
```
- Read-only derivation from `config/static_v41.json` → `shows[show].intangible`. The loader checks that `world_rules`/`channel` match static. On a mismatch it fails, and never writes back.
- `tier` ∈ {`LEGEND`, `MARK`} only. `locked: true` is required.
- **FT1–FT4 are excluded while `config/fixed_threads.json` says `PENDING`.** Any `id` matching `^FT\d` is rejected.

### 4.3 `still_meta.json` (PROPOSED)
```json
{"prev_clip_id": "NP16", "still_path": "<TT_CLIPS>/NP16_last.png", "analyzer": "stub",
 "descriptors": ["MARLO stands on the top step", "the thug sits three stairs down"], "tier": "FLASH"}
```
- Interface: `analyze_still(path) -> list[str]`, each descriptor ≤ 12 words. v1 ships only `StubAnalyzer`, which returns fixture text and never opens the image or calls the network. The real vision model is **OPEN (D3)**.
- Descriptors describe **state and position, not looks.** Any descriptor that matches `apply_check_v42.VIS` and names an imaged cast member is dropped and logged (R-REFDESC).
- `still_path` uses a config root token, never an absolute `/workspace` path (§6).

### 4.4 `comments.jsonl` (PROPOSED)
One `{"ts": "<ISO-8601>", "text": "<raw>"}` per line. **No other keys are allowed.** `handle`, `user`, `author`, `avatar`, `image`, `img`, `url` and `media` are rejected at load.
Sanitizer, applied in this order:
1. Drop `@handles` (same regex family as `R-NOHANDLES`: `(?<![\w.])@[A-Za-z0-9_]{2,15}\b`) and e-mail-like tokens.
2. Drop URLs (`https?://…`, `www.…`, bare `domain.tld/…`).
3. Drop any comment matching `assemble_prompt.NEVER_WORDS`, imported, never re-typed.
4. `bundle_assembler.bend()`: HARD hits (kids, etc.) → **HELD** (kept in the report, never in the prompt, never deleted). Bendable hits ("looks into the camera", gore) → bent text.
5. Collapse whitespace, cap length, strip brackets `[]` so comment text can never open a `[Cast]`/`[Rules]` bracket.

No handle field is ever stored, in inputs, outputs or reports. The `contributors[]` sidecar field stays empty in v1, because contributor data handling is part of D4.

### 4.5 `character_memory/<NAME>.json` (PROPOSED)
```json
{"name": "MARLO QUILL", "image_tag": "MARLO_QUILL_threequarter_face",
 "memories": [{"text": "kept the jade key in his waistcoat lining", "tier": "SCAR", "since_index": 14, "episode": 1, "season": 1}],
 "summon_count": 2, "writein_level": 1}
```
- **Slow write-in:** each summon raises `writein_level` by **at most 1** (cap 3). The level caps how many memory beats are emitted (proposed: level 0 → 0, 1 → 1, 2 → 1 plus a carried clause, 3 → 2; mapping is D5b).
- Memory items are filtered by `layers_v4.tier_alive(item, episode, season, clip_index)` and decayed by `carry_text()`.
- **Never written looks:** memory text is checked against `VIS` for imaged characters (R-REFDESC). Cast entry stays `NAME (<IMAGE_n>)`.
- The dry run **does not write** memory back. It emits a *proposed* updated memory file under `out/` so the write-in step can be reviewed. The store is resolved by D5: `character-meta/<NN-channel>.yaml` keyed by cast id, plus an add-only `trait_observations.jsonl`.

### 4.6 Fixtures for the dry run
All are invented. Nothing is copied from `COMMENT-PROMPTS.jsonl`, `LINEAGE.jsonl` or spend data. `NP17` is a placeholder id for "the clip after NP16"; the real next id comes from the queue.
- `fixtures/night-porter/NP16/base_spec.json`: reconstructed NP16 spec (G6).
- `fixtures/night-porter/NP17/locked_meta.json`: derived from static_v41 THE NIGHT PORTER.
- `fixtures/night-porter/NP17/still_meta.json`: stub descriptor for `NP16_last` (no image file).
- `fixtures/night-porter/NP17/comments.jsonl`: 5 raw comments. At least one each with a `@handle`, a URL, a "looks into the camera" phrase, a kid word (expected HELD), and one clean comment.
- `fixtures/night-porter/NP17/character_memory/MARLO_QUILL.json`: one memory file.
- `fixtures/black-ice/…`: a minimal Ch4 locked-meta + base spec used **only by tests**, to prove the Ch4 photoreal 1971 look is untouched.

---

## 5. Hard canon rules: where each is enforced

Every rule is enforced at least twice: by the assembler **before** build, and by the unchanged gate **after** build.

| Rule | Before build (new module) | After build (existing gate, unchanged) |
|---|---|---|
| Nobody looks into the camera | Eyeline sentence copied from base spec, never from comments. `bend()` rewrites camera-look phrases. A post-sanitize regex rejects any surviving "into the camera/lens". | `R-EYES` (rules bracket "Nobody looks into the camera."), `W-eyeline` |
| Reference image required, except the 16 exempt ads | Refuse to assemble if `refs_raw` is empty and `clip_id ∉ apply_check_v44.exempt_ids()`. The exemption list is read, never extended. | `R-REF` via `apply_check_v44.check(clip_id=…)`, `R-NOREFSTART` |
| Commenter images OFF | The contract has no image fields (hard error). The assembler reads `config/commenter_images.json` and aborts if `enabled` is anything but `false`. It never writes that file. | `R-NOCOMMENTERIMG` |
| Contributor handles never in prompts | Sanitizer drops handles. No handle field is stored. `spec.contributors` stays empty. | `R-NOHANDLES` |
| FT1–FT4 stay off | `locked_meta` rejects `FT*` ids. `fixed_threads()` status must be `PENDING`, else abort and ask. | (no gate check exists; new test asserts no FT text in output) |
| No kids; no real people or brands outside parody | `bundle_assembler.HARD` holds kid words. `NEVER_WORDS` drop. A PROPOSED `deny_names.json` (empty by default, Trundle-maintained) holds suspected real-person/brand comments for review. | `R-KIDS`, `R-BRANDS` ("Parody brands only; no real brands or personal names on screen.") |
| Masters stay pure | Output is prompt text plus sidecar only. No overlays, tags, genealogy or embedded clips in the prompt. Provenance goes in `*.assembly.json`, not the prompt. | `R-OVERLAY` |
| Ch4 is photoreal 1971 | The assembler never sets `look`/`look_override`. `[Look]` always comes from `static_v41`. A BLACK ICE test fixture proves it. | `R-CH4 photoreal 1971` (also fails ink-art refs), `R-CH4NAME` |

The assembler never calls xAI, fal, X or any render/spend API, never renders, and never spends. Tests enforce this with a socket guard (§7.1).

---

## 6. Module and file layout (NEW folder only)

Everything new lives under **`prompts/system-v5-draft/`**. Nothing under `prompts/system-v4-20261030/` (`prompts_v4*`, `config/`, `tools/`, `tests/`, `out/`) or `story-engine/` is edited.

```
prompts/system-v5-draft/
  README.md                 what this is, how to run the dry run, status: DRAFT
  requirements-dev.txt      pytest (+ opencv-python-headless, numpy only for the legacy v4 suite)
  tt_paths.example.json     path config template (no secrets, no absolute /workspace paths)
  assemble_next.py          CLI + assemble_next(inputs_dir, out_dir, *, base="v42") -> result
  paths.py                  config resolver (§6.1); the only place roots are defined
  contracts.py              load + validate the 5 input files; unknown keys -> error
  sanitize.py               comment sanitizer (handles, URLs, NEVER_WORDS, bracket strip) -> bend()
  placement.py              beat placement (ported from bundle_assembler.bundle/cats), beat/word budget
  memory.py                 tier_alive filter, carry_text decay, write-in cap, proposed memory update
  adapters/
    v4_bridge.py            sys.path bridge to system-v4 tools/ (read-only import of v42, v44, layers_v4)
    story_engine_bridge.py  read-only import of assemble_prompt (NEVER_WORDS, PROTECTED) + bundle_assembler
    base_spec.py            load base spec; next clip id; parity check vs prompts_v44
    locked_meta.py          derive/validate from static_v41 + fixed_threads (FT excluded)
    still_meta.py           prev_last_frame port (clip-id keyed) + StubAnalyzer (analyze_still)
  report.py                 DIFF.md / diff.json vs current builder, GATE.json, assembly provenance
  fixtures/                 §4.6 (invented data only)
  inputs/                   empty placeholder (.keep); comments come from the configured spool (D4), memory from `character-meta/` (D5)
  out/dryrun/               dry-run outputs only (written by assemble_next; git-ignored, never committed; D12 accepted)
  tests/
    conftest.py             socket guard (no network), tmp out dirs
    test_contracts.py  test_sanitize.py  test_placement.py  test_memory.py
    test_parity_np16.py  test_dry_run_np17.py  test_canon_rules.py  test_no_live_edits.py
```

The new tests live in `prompts/system-v5-draft/tests/` and run with `pytest tests` from that folder. They never join the legacy 67, so the legacy count stays meaningful.

### 6.1 Replacing hardcoded `/workspace` paths with config

**New code:** no absolute paths at all. `paths.py` resolves roots in this order: environment variable, then `tt_paths.json` (git-ignored local file, from `tt_paths.example.json`), then a repo-relative default. This follows the precedent `assemble_prompt.py` already sets with `TT_PROMPTS`/`TT_LOCKS`.

| Config key / env var | Replaces prefix (MANIFEST counts) | Repo-relative default |
|---|---|---|
| `TT_REPO_ROOT` | n/a | auto-detected (git root) |
| `TT_PROMPTS_V4` | `/workspace/thunder-trundle/prompts/system-v4-20261030` | `prompts/system-v4-20261030` |
| `TT_PROMPTS` (existing) | `/workspace/thunder-trundle/prompts` (712 hits / 241 files) | `prompts` |
| `TT_STORY_ENGINE` | `/workspace/streaming/story-engine` (1436 / 50) | `story-engine` |
| `TT_QUEUES` | `/workspace/streaming/queues` (304 / 6) | `story-engine/queues` |
| `TT_CHANNELS` | `/workspace/thunder-trundle/channels` (75 / 58) | unset → refs treated as opaque strings |
| `TT_EXPERIMENTS` | `/workspace/thunder-trundle/prompts/experiments` | unset → features needing it are skipped with a clear message |
| `TT_CLIPS` | odyssey `…/ODYSSEY/clips` (start frames) | unset → token kept as `<TT_CLIPS>/NP16_last.png` in dry-run args |
| `TT_CHANNEL_READY` | `/workspace/fakenews/channel-ready` (1884 / 43) | unset (out of scope for assembly) |

**Existing 34 code files** (MANIFEST list, including `tools/apply_check_v4.py`, `tools/meta_check.py`, `tests/test_v41.py`, `story-engine/engine/assemble_prompt.py`): **not edited in this build**, because the hard rule forbids changing `tools/`, `tests/` and live files. Instead:
1. `report.py` ships a read-only `path-audit` that lists every `/workspace` hit, grouped by the table above, so a later migration is mechanical.
2. A **separate follow-up PR** (Decision D10, needs Trundle's yes because it touches `tools/` and `tests/`) would replace each literal with `os.environ.get("TT_…", <repo-relative default>)`. It keeps byte-identical prompt outputs and is proven by re-running the v44 gate (53/53) and the parity test.
3. Paths stored **inside data** (`args.image_path`, `reference_image_paths` in `prompts_v44/*.json`) are left as-is. They are opaque strings to `build()` and the gate. The new module only rewrites the *new* clip's start-frame path, through `TT_CLIPS`.

---

## 7. Tests and acceptance

### 7.1 New tests (in `prompts/system-v5-draft/tests/`)
- **Sanitizer** drops `@handles`, e-mails and URLs, and drops `NEVER_WORDS` matches. HARD hits are HELD, not emitted. "Looks into the camera" is bent. Bracket characters are stripped. No `handle` key survives anywhere in the outputs or report (scan of all written JSON).
- **Comment isolation:** comment text never lands in `[Cast]`, `[Setting]`, `[Look]` or `[Rules]`. Slot-parse the prompt and assert comment tokens appear only between the eyeline sentence and the ending line.
- **Write-in cap:** one summon raises `writein_level` by ≤ 1. The number of memory beats emitted is ≤ the cap for the level. Level never exceeds 3.
- **Tier decay** via `layers_v4.tier_alive()`: a FLASH still descriptor is alive for exactly 1 clip, SCAR for the episode, MARK for the season, LEGEND always. `carry_text()` decay is respected.
- **Contracts:** unknown keys, image fields and `FT*` threads are rejected. A `locked_meta` mismatch with static_v41 is rejected.
- **Canon rules:** for every rule in §5, a negative test (inject the violation, gate FAILs or assembler refuses) and a positive test (dry-run output PASSes). Includes a BLACK ICE fixture asserting the Ch4 photoreal 1971 `[Look]` is unchanged and `R-CH4` PASSes.
- **No live edits:** a sha256 manifest of `prompts/system-v4-20261030/{prompts_v4*,config,tools,tests}` and of `story-engine/engine/{assemble_prompt,bundle_assembler}.py` is taken before and after a dry run and must be identical. `config/commenter_images.json` still says `enabled: false`.
- **No network:** `conftest.py` replaces `socket.socket.connect` with a raising stub for the whole session.
- **Determinism:** two dry runs give byte-identical outputs (placement uses `layers_v4.rng(clip_id, META, salt)`).

### 7.2 Dry run and diff (the acceptance artifact)
1. **Parity:** `build_prompt_v42.build(fixtures/.../NP16/base_spec.json)` must reproduce `prompts_v44/odyssey/NP16.args.json` byte-for-byte (sha `f3ddda1b…`). This proves the fixture *is* "the same spec" as the current builder (G6).
2. **Assemble:** `python assemble_next.py --inputs fixtures/night-porter/NP17 --base-spec fixtures/night-porter/NP16/base_spec.json --out out/dryrun/night-porter/` writes `NP17.args.json`, `NP17.meta.json`, `NP17.assembly.json` and `NP17.memory.proposed.json`, **only under `system-v5-draft/out/dryrun/`** (git-ignored; D12 accepted).
3. **Diff** (`out/dryrun/night-porter/DIFF-NP17.md` + `.json`): slot-by-slot comparison of NP17 against the current-builder output for the same base spec (NP16). **Allowed differences: timed beats and the Continue line (`image_path`/`parent_clip`).** Any other slot that differs (`[Look]`, `[Setting]`, cast/extra brackets, camera, eyelines, ending line, `[Rules]`, `reference_image_paths`) fails the run.
4. **Gate:** `apply_check_v44.check(prompt, args, spec, sidecar, clip_id="NP17")` → 0 FAIL, written to `out/dryrun/night-porter/GATE-NP17.json`. The v44 gate is also re-run read-only over all of `prompts_v44` and must still be 53 PASS / 0 FAIL / 5 held.

### 7.3 Existing tests (legacy suite)
- *Updated after Trundle accepted D9 and D9b (Oct 31, 2026):* `pytest tests` in `prompts/system-v4-20261030` is **66 passed, 1 skipped**. The skip is `test_static_flip_v3` when `static_flip_v2.py` or its REF media is absent (the CC-BY-SA static clip is not imported). On the live box the test still runs. Acceptance for every build PR: those 66 stay green, the skip stays the same skip, and the v44 gate stays 53/53.

---

## 8. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Legacy suite was 35/67, then 66/67, before D9b. | §7.3 is now **66 passed, 1 skipped**. D9 and D9b are accepted. |
| R2 | The reconstructed NP16 spec drifts from the real (lost) spec. | Parity test pins byte-identical output and sha. If v42 ever changes, parity breaks loudly. |
| R3 | Comment text smuggles names, brands or bracket syntax into the prompt. | Strict contract, sanitizer, bracket stripping, slot-isolation test, `R-NOHANDLES`/`R-BRANDS` gate. Real-person detection is imperfect, so suspected names are **held for review** (deny list is D4). |
| R4 | Still/memory descriptors restate looks (R-REFDESC FAIL) or re-describe imaged cast. | `VIS` pre-filter plus gate. Descriptors are limited to state/position. |
| R5 | Extra beats push past `W-beats` (6) / `W-words` (330), or the model adds cuts. | Beat budget (§2.2). Overflow carries to the next clip. Camera stays the base spec's single move. |
| R6 | Importing story-engine modules drags in `/workspace` paths or side effects. | Only pure symbols are used (`NEVER_WORDS`, `PROTECTED`, `bend`, `HARD`, `cats`). The bridge imports lazily and never calls `resolve_embed`. Covered by the no-network and no-live-edit tests. |
| R7 | No Night Porter stills exist, so the still path is untested against real frames. | Stub analyzer only. The dry run uses fixture descriptors. Real stills plus vision model are D3. |
| R8 | Someone flips `commenter_images.enabled` or FT1–FT4 status as a side effect. | The assembler only reads those files and aborts on unexpected values. The no-live-edit sha manifest catches writes. |
| R9 | The ownership question leaks into code (owner names in headers or config). | No owner fields in code or config. Ownership is recorded in docs only (D1). |
| R10 | The v42 base (Option A) proves too narrow for per-spot or dense formats later. | Base-agnostic adapters (§3.1). Only the build/gate call site changes if D2 picks B or C. |
| R11 | 44 small JSON/MD files in `story-engine/data/{smoke,exports,continuity}` are git-ignored by the imported `story-engine/.gitignore`, and `live/checker.py` references `data/continuity`. | Not needed for assembly. D12 accepted: they stay out. Dry-run outputs go to ignored `out/dryrun/`. |

---

## 9. DECISIONS — all RESOLVED

Trundle **approved the plan** and resolved every open decision on **Oct 31, 2026, 10:32 PM CT**. Earlier on Oct 31 he accepted D9, D10 (inventory only), D12 and the dry-run location. D9b is a technical default (he authorized recommended defaults for purely technical questions). Nothing is open.

| # | Status | Ruling |
|---|---|---|
| **D1** Ownership | **RESOLVED** Oct 31, 2026, 10:32 PM CT | Trundle owns the rules and final approval. **Director New** assembles the next prompt from the other systems' outputs. It does not invent or own the inputs. |
| **D2** Base assembler | **RESOLVED** Oct 31, 2026, 10:32 PM CT | Wrap the v42 builder (Option A). Move to a hybrid only if a clear gap appears, and document that gap. |
| **D3** Vision model | **RESOLVED** Oct 31, 2026, 10:32 PM CT | One read-only lookup of xAI's public docs (no key, no spend). Pick the strongest current Grok model that accepts image input. Pin the id in config (`prompts/system-v5-draft/config/vision_model.json`), not in code, with source and date. **Never call it** in v1; the still analyzer stays a stub. |
| **D4** Comment intake | **RESOLVED** Oct 31, 2026, 10:32 PM CT | Raw collection plus insertion only, no semantic parsing. Source: the live comment spool, read through a path from config (fixtures in tests). Window: last 15 minutes, capped at 50 comments. Block list: empty but configurable. Contributor handles and IDs never reach prompt text, enforced by a test, and R-NOHANDLES keeps passing. |
| **D5** Character memory | **RESOLVED** Oct 31, 2026, 10:32 PM CT | One companion YAML per channel at `character-meta/<NN-channel>.yaml`, keyed by cast id, plus an add-only `trait_observations.jsonl`. Write-in levels cap how many memory beats enter a single prompt. This replaces the `character_memory/<NAME>.json` shape in §4.5. |
| **D6** Per-spot structure | **RESOLVED** Oct 31, 2026, 10:32 PM CT | A minimal `thread_holder` field for each spot type. It is short and locked before any mutation. |
| **D7** Canon promotion | **RESOLVED** Oct 31, 2026, 10:32 PM CT | Keep the FLASH, SCAR, MARK and LEGEND tiers. Locked threads enter the prompt only as hard constraints, never as soft suggestions. |
| **D8** FT1–FT4 | **RESOLVED** Oct 31, 2026, 10:32 PM CT | Stay OFF until Trundle explicitly turns them on. |
| **D9** Missing A1–A15 checker | **RESOLVED**, accepted Oct 31, 2026 | Imported on PR #1 (byte copy). `tools/apply_check_v4.py` falls back to the repo copy when `/workspace` is absent. Live-box behavior unchanged. |
| **D9b** `static_flip_v2.py` / REF media | **RESOLVED** (technical default) | The CC-BY-SA `.ogv` clip is not imported. `test_static_flip_v3` skips when v2 or its REF media is absent; it still runs on the live box. Legacy suite: **66 passed, 1 skipped**. |
| **D10** Hardcoded `/workspace` paths | **RESOLVED (inventory only)**, accepted Oct 31, 2026 | `docs/PATHS-INVENTORY.md` is the PROPOSED inventory. **No migration yet**; a migration PR needs its own go-ahead. |
| **D11** Input contracts and folder | **RESOLVED** Oct 31, 2026, 10:32 PM CT | The proposed input contracts are accepted (with D5's YAML memory store). `prompts/system-v5-draft/` is the working folder. |
| **D12** Git-ignored snapshot data | **RESOLVED**, accepted Oct 31, 2026 | The 44 files in `story-engine/data/{smoke,exports,continuity}` stay out. |
| **Dry-run location** | **RESOLVED**, accepted Oct 31, 2026 | Dry-run outputs go to the ignored `out/dryrun/` folder and are not committed. |

---

## 10. Effort and recommended model for the build phase

Sizes are by technical scope (files, approximate lines, and integration risk), not calendar time.

| Work item | Files | Approx. size | Complexity / risk |
|---|---|---|---|
| Paths config + bridges | `paths.py`, `adapters/v4_bridge.py`, `adapters/story_engine_bridge.py`, `tt_paths.example.json` | ~120 LOC | Low. Main risk is import side effects (R6). |
| Contracts + fixtures | `contracts.py`, `fixtures/**` (≈8 JSON/JSONL files) | ~150 LOC + data | Low |
| NP16 base spec + parity | `adapters/base_spec.py`, `test_parity_np16.py` | ~80 LOC | Low. Already proven by probe (G6). |
| Sanitizer | `sanitize.py`, `test_sanitize.py` | ~120 LOC | Medium. Regex edge cases (handles vs e-mail vs `@` in text). |
| Locked meta + still adapters | `adapters/locked_meta.py`, `adapters/still_meta.py` | ~150 LOC | Low–medium (R-REFDESC filter). |
| Memory + write-in | `memory.py`, `test_memory.py` | ~150 LOC | Medium. Tier semantics, cap mapping pending D5b. |
| Beat placement + budget | `placement.py`, `test_placement.py` | ~180 LOC | Medium–high. Must keep slot diff to beats only, and stay deterministic. |
| `assemble_next.py` + report/diff/gate | `assemble_next.py`, `report.py` | ~220 LOC | Medium |
| Canon/no-live-edit/no-network tests | `test_canon_rules.py`, `test_no_live_edits.py`, `conftest.py` | ~200 LOC | Medium (many negative cases). |
| **Total** | ~20 files | **~1.4k LOC incl. tests** | Single build PR. No edits outside `prompts/system-v5-draft/`. |

**Recommended model:** **Claude Opus 5.5 (`claude-opus-5-5`), effort high**, for the implementation. This is multi-file Python integration against strict rule constraints and byte-level parity, matching brief §8. Alternative per the brief: a cheaper implementation pass with **GPT-5.3 Codex** once the plan is approved. Keep Opus for review of the sanitizer, placement and canon tests.

---

## 11. Stop point

This PR contains **only this plan**. Trundle approved it on Oct 31, 2026, 10:32 PM CT. Implementation happens in a separate PR (`impl/prompt-assembly-v1`), step by step per `docs/IMPLEMENTATION-STEPS-v1.md`. No renders, no network calls beyond the single D3 docs lookup, no spend, and no live files touched.
