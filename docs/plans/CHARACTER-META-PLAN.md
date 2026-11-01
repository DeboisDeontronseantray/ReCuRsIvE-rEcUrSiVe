# CHARACTER-META implementation plan (v1)

> **Status: PLAN APPROVED (Trundle, Oct 31, 2026, 10:32 PM CT).** Specification on this branch is approved for implementation on a separate branch/PR. This PR remains the plan + spec landing; implementation is tracked separately.

**Goal:** Add a per-channel **companion character-meta store** (YAML keyed by cast id) that keeps all existing bible cast fields and four optional additions (`traits`, `abilities`, `relationships`, `meta_prompt`), plus an add-only **`trait_observations.jsonl`** log that background processes append to. Promotion to `proposed` on the companion file happens only after **N=3 distinct aired clips** (join observation `clip_id` to LINEAGE rows with **`aired: true`**). **Approval to `approved`/`locked` is owner-only (Trundle).** Conflicts with locked/approved canon are **flagged, never applied.** Generation quirks **never** become traits.

**Spec sources (this repo):**

- `docs/spec/character-meta/CHARACTER-META-SCHEMA-v1.yaml`
- `docs/spec/character-meta/CHARACTER-META-NOTE-v1.md`
- `docs/spec/character-meta/CHARACTER-META-CODING-BRIEF-v1.md`
- `docs/spec/character-meta/CHARACTER-META-SKILL-DRAFT-v1.md`
- Fixtures: `tests/fixtures/character-meta/` (scrubbed bible copy + 20 lineage rows)

**Human canon model (existing, unchanged):** `story-engine/continuity/ch04-military-boutique/SCHEMA.md` on the import snapshot — proposed → approved promotion, observations per clip, `generation_quirks` separate from traits, live bible add-only with owner approval.

---

## 0. Stop line (this PR)

This pull request delivers:

1. Spec files under `docs/spec/character-meta/`
2. This plan under `docs/plans/CHARACTER-META-PLAN.md`
3. Labeled fixtures under `tests/fixtures/character-meta/`

**Plan approved:** Trundle, **Oct 31, 2026, 10:32 PM CT** — implementation proceeds on a follow-up branch/PR (see milestone section 7). Merging this PR is not required before starting implementation, but the implementation PR should target this branch or `main` after merge.

Tasks in sections 5–7 were unblocked by plan approval. An implementation **go** on a code PR is still separate from merging this docs PR.

---

## Plan approval (Trundle, Oct 31, 2026, 10:32 PM CT)

| Decision | Record |
|---|---|
| **Plan status** | **APPROVED** for implementation (Oct 31, 2026, 10:32 PM CT). |
| **LINEAGE `aired` field** | **RESOLVED.** Media Librarian New (or the lineage validator) adds a derived boolean **`aired`** on each clip’s LINEAGE row when the clip reaches **AIRED** status. Character-meta promotion counts only observations whose `clip_id` joins to a row with **`aired: true`**. A **missing** `aired` field is treated as **not aired**. Legacy `air_yes: true` may be read as aired until rows are normalized. The N=3 distinct aired-clip rule depends on this field. |

## Accepted technical points (Trundle, Oct 31, 2026)

Owner decisions recorded on PR #6 (`cursor/character-meta-plan-8490`). Docs-only; no implementation on this basis until separate **go**.

1. **`.gitignore` proposals (section 1):** The suggested additions called out in this plan (companion YAML / observation log paths, lineage `*.jsonl` allowlist reconciliation, optional archive extensions) are **accepted as proposals only**. The **existing `.gitignore` stays unchanged** until a **separate, explicit** `.gitignore` change (its own review), not bundled silently with store implementation.

2. **LINEAGE aired fields (superseded by plan approval):** Canonical field is boolean **`aired`** on LINEAGE rows at AIRED status; missing ⇒ not aired. See **Plan approval** table.

3. **Standing rule (technical vs creative):** Questions that are **purely technical** and **outside personal/creative scope** are resolved with **recommended defaults** documented in the plan or PR (agents need not block on Trundle for those). Personal, creative, canon, approval, and spend/airing decisions still require Trundle’s yes.

---

## 1. Repo survey (2026-11-01)

| Area | Finding |
|---|---|
| **`main`** | Bootstrap only: `README.md`, `.gitignore`, proprietary `LICENSE`. |
| **`import/snapshot-20261031`** | Full story-engine + prompt v4 tree; continuity `SCHEMA.md` matches the NOTE’s promotion model. No CHARACTER-META store code yet. |
| **Plan branches (do not merge here)** | `plan/lineage-v1` (root `PLAN.md`), `playout/queue-mutation-plan` (`playout/queue-mutation/PLAN.md`), `cursor/stills-meta-scaffold-plan-a5c4` (root `PLAN.md` + package scaffold). |
| **This work** | Uses README’s `docs/` convention: **`docs/spec/`** + **`docs/plans/`** (other briefs use a single root `PLAN.md` when one folder owns the whole branch). |

### `.gitignore` / `LICENSE` (observations only — not changed on this branch)

Current `main` `.gitignore` already covers: `.env` / secrets, venvs, `node_modules/`, live media (`*.mp4`, images, etc.), `LINEAGE.jsonl`, and `**/data/spend/`. Comment block states small YAML/JSON/JSONL fixtures may stay tracked.

**Proposals for a later implementation PR** (accepted as proposals only per Trundle, Oct 31, 2026 — see **Accepted technical points**; `.gitignore` unchanged until a separate explicit edit):

- If implementation adds repo-local `trait_observations.jsonl` or per-channel `character-meta/*.yaml` with real rows, consider ignoring `**/character-meta/*.yaml` outside `tests/fixtures/` (same pattern as lineage plan’s `data/copies/` + `*.jsonl` exceptions).
- Lineage plan branch proposes stricter `*.jsonl` ignore with allowlists under `tests/fixtures/` — reconcile when both land; CHARACTER-META should not fight lineage’s template path `lineage/CHARACTER-META.jsonl`.
- Optional: `*.tar` / `*.tar.bz2` / `*.sqlite3` if large artifacts appear (lineage plan notes gaps vs bootstrap ignore).

**LICENSE:** Left unchanged per owner rule. Proprietary Thunder Trundle statement on `main`.

---

## 2. Architecture (after go)

### 2.1 Data locations (runtime on the box — not committed)

| Artifact | Role |
|---|---|
| Live continuity bible | **Read-only** (e.g. `.../continuity/ch04-military-boutique/bible-v2.yaml`). Never written by this system. |
| Companion store | `character-meta/<NN>-<channel-slug>.yaml` — one file per channel; top-level map **keyed by cast id**; each entry **copies/retains all existing bible cast fields** plus optional additions (empty until promotion). |
| Observation log | `trait_observations.jsonl` beside existing per-channel observation logs — **append-only**; corrections are new rows. |
| LINEAGE ledger | Join source for **aired** clip ids — boolean **`aired: true`** on row (derived at AIRED status). Missing `aired` ⇒ not aired. Held out of git (`LINEAGE.jsonl` ignored). |

Package name/path (from coding brief): top-level **`charmeta/`** (flat layout, consistent with lineage brief’s “one folder per brief” pattern).

### 2.2 Cast entry shape

**Kept unchanged (from bible / SCHEMA.md):**  
`locked_description`, `still`, `turnaround_paths`, `qualities_locked`, `demeanor`, `fuse`, `catchphrase`, `status`, `approved_by`, `approved_at`, `notes`.

**Optional additions (all start empty):**

- `traits.tangible` / `traits.intangible` — list items with `id`, `text`, `source_clip`, optional `confidence`, `status`
- `abilities` — `id`, `text`, `first_seen_clip`, `times_seen`, `status`
- `relationships` — `with`, `kind`, `text`, `first_seen_clip`, `status`
- `meta_prompt` — `text`, `built_from[]`, `version` (rebuilt only from approved/locked entries)

**States:** `proposed` | `approved` | `locked` | `retired` (retired never deleted).

### 2.3 Rules (from schema)

| Rule | Behavior |
|---|---|
| Add-only log | No update/delete API on `trait_observations.jsonl`; new row per correction. |
| Background writes | Append log only; **never** write cast fields directly. |
| Proposal threshold | Same normalized `(character, field, text)` across **N=3 distinct aired `clip_id`s** → eligible for **`proposed`** on companion YAML (default **N=3** in schema). |
| Aired definition | LINEAGE row has **`aired: true`** (set by Media Librarian New / lineage pipeline at AIRED). Missing field ⇒ not aired. Unaired drafts do not count. |
| Approval | `proposed` → `approved` / `locked` requires **Trundle’s yes** only; tools never set approved/locked automatically. |
| Conflicts | Contradiction with locked/approved field or `qualities_locked` → **flag for Trundle**, never auto-applied. |
| Quirks | Generation mistakes → **`generation_quirks`** (bible), **never** traits/abilities. |
| meta_prompt | Rebuild from approved/locked only; bump `version`; record `built_from`. Ignore `proposed` entries. |
| Cast ids | No invented ids (e.g. BLACK ICE HERON/LANTERN/WOLFHOUND); store accepts cast id list input and **reports missing**. |

### 2.4 Promotion CLI default

`promote.py`: **dry-run by default** — print what would become `proposed` and list conflicts. Write companion YAML only with **`--apply`**. Never sets `approved` or `locked`.

---

## 3. Integration with parallel agent work (no duplication)

### 3.1 `plan/lineage-v1` (lineage / CHARACTER-META.jsonl validators)

**Their scope:** Stdlib Python under `lineage/` — validate `replaces`, read-only queries, add-only LINEAGE append, and **`validate_character_meta_row`** for a **closed JSONL companion schema** (`lineage/CHARACTER-META.jsonl` empty template).

**This plan’s scope:** YAML **per-channel character-meta store** + **`trait_observations.jsonl`** + promotion/meta_prompt **after** observations repeat on aired clips.

**Integration (not overlap):**

| Concern | Owner | Notes |
|---|---|---|
| LINEAGE row shape, aired flags, append safety | Lineage brief | CHARACTER-META **consumes** LINEAGE for aired join; does not append lineage rows. |
| JSONL `CHARACTER-META.jsonl` row validator | Lineage brief | Distinct from YAML companion files; align field names (`character_id`, `sha256`, corrections) in section 9 open question. |
| `trait_observations.jsonl` row shape | CHARACTER-META schema | Lineage validators should **not** duplicate this log; optional cross-check that `clip_id` exists in LINEAGE is read-only. |
| Who writes character meta | Both leave open | Lineage plan explicitly does not assign a writer; this plan assigns **background append to log only**, promotion via `promote.py`, approval manual. |

### 3.2 `cursor/stills-meta-scaffold-plan-a5c4` (stills → meta JSON)

**Their scope:** Opt-in `stills_meta` package — vision/dry-run analysis of **one still** → `{description, meta}` JSON; **`to_carry_text()`** adapter; no prompt assembly wiring.

**Integration:**

| Concern | Owner | Notes |
|---|---|---|
| Still → structured observation | Stills-meta (live/dry-run) | Produces rich meta; **does not** write bible or companion YAML. |
| `stills_stub.py` / `extract(image_path, clip_id)` | CHARACTER-META brief | **Interface only**, returns `[]`, `method=still_analysis` until Trundle wires stills-meta output into observation append. |
| Tangible traits | Both | Stills-meta `meta.tangible[]` strings feed **human or downstream mapping** into `traits.tangible` observations — not automatic promotion. |
| Ref-imaged characters (R-REFDESC) | Stills-meta rules | CHARACTER-META still stores **text observations** with `source_clip`; respect no physical look in prompts for ref-imaged cast. |

### 3.3 `playout/queue-mutation-plan`

**Their scope:** Queue mutation planning under `playout/queue-mutation/`.

**Integration:** No shared files. Future: aired clips that count toward N=3 correlate with LINEAGE **`aired: true`** (see plan approval).

---

## 4. Fixture caveat (lineage sample)

`tests/fixtures/character-meta/lineage-sample.jsonl` is a **legacy** twenty-row sample **without** `aired` (missing ⇒ not aired at runtime). Implementation tests use **`lineage-with-aired.jsonl`** (synthetic `aired: true/false` on selected `clip_id`s) for threshold and unaired cases.

---

## 5. Module layout (post-go)

Flat package at repo root (matches coding brief; aligns with lineage brief, not stills-meta `src/` layout):

```text
charmeta/
  __init__.py
  schema.py              # load docs/spec/character-meta/CHARACTER-META-SCHEMA-v1.yaml (PyYAML)
  store.py               # load/init companion YAML by channel; cast id list validation
  observations.py        # append_observation() → trait_observations.jsonl only
  promote.py             # dry-run default; --apply writes proposed entries only
  conflicts.py           # flag vs locked/approved / qualities_locked; never apply
  meta_prompt.py         # rebuild from approved/locked; bump version
  stills_stub.py         # extract() → []; method still_analysis (no network)
  cli.py                 # optional thin CLI wrapping promote / append / rebuild

tests/
  fixtures/character-meta/   # existing fixtures + future aired lineage slice
  test_observations_add_only.py
  test_promote_threshold.py
  test_unaired_ignored.py
  test_quirks_not_traits.py
  test_locked_conflict_flagged.py
  test_meta_prompt_ignores_proposed.py
  test_bible_fixture_unchanged.py

pyproject.toml             # name e.g. recursive-charmeta; requires-python >=3.11; PyYAML only runtime dep
```

**Tech stack (coding brief):** Python 3.11+, **stdlib + PyYAML only** at runtime; tests via `unittest` (match lineage plan unless repo standardizes on pytest elsewhere).

**Hard limits (all phases):** No network, no paid APIs, no posting/airing, no secrets in repo, home-only. Live bible byte-identical after full test run touching fixture copy only.

---

## 6. Test matrix (must pass before merge of implementation PR)

| Test | Expectation |
|---|---|
| Add-only | No API to mutate/delete observation rows |
| N=3 threshold | 2 distinct aired clips → no `proposed` write; 3 → `proposed` with `--apply` |
| Unaired | Observations tied to unaired clips do not count |
| Quirks | Paths writing `generation_quirks` do not populate traits |
| Locked conflict | Conflicting observation flagged; companion unchanged |
| meta_prompt | Output excludes `proposed` entries |
| Bible safety | `bible-v2.fixture.yaml` sha unchanged after store/promote dry-run against **copy** paths only |

---

## 7. Milestones (implementation, after go)

| Milestone | Deliverable | Stop point |
|---|---|---|
| M1 Scaffold | `pyproject.toml`, `charmeta/` package skeleton, schema loader, README section | Tests import package |
| M2 Observations | `append_observation()` + validation | Add-only tests green |
| M3 Promote | `promote.py` dry-run + `--apply` (proposed only) | Threshold + unaired tests green |
| M4 Conflicts | `conflicts.py` integrated in promote report | Flag-only tests green |
| M5 meta_prompt | Rebuild + version bump | Ignores proposed |
| M6 Stubs + CLI | `stills_stub.py`, minimal CLI | No network |
| M7 Integration | Aired fixture + join LINEAGE reader (path from env) | Full matrix green |

One commit per milestone (or per task inside milestone), branch stays green. **Do not push implementation to `main` without merged PR and Trundle’s yes.**

---

## 8. Assumptions if Trundle says “go”

1. Companion files are **YAML**, not the JSONL template in `lineage/CHARACTER-META.jsonl` (that file remains lineage’s JSONL schema unless reconciled in section 9).
2. **PyYAML** is an acceptable sole runtime dependency (coding brief).
3. Aired clip membership comes from LINEAGE boolean **`aired: true`** (see **Plan approval**). Missing ⇒ not aired.
4. Implementation tests use **fixture paths only**; default code paths refuse live bible and live `LINEAGE.jsonl` (mirror lineage plan’s `--live` / copy-dir pattern).
5. **`docs/spec/character-meta/CHARACTER-META-SCHEMA-v1.yaml`** is the schema of record unless Trundle bumps version in spec first.

---

## 9. Open questions (need Trundle or cross-agent agreement)

1. ~~**Lineage aired fields:**~~ **RESOLVED** (plan approval, Oct 31, 2026, 10:32 PM CT) — boolean **`aired`** on LINEAGE row at AIRED status; missing ⇒ not aired.
2. **JSONL vs YAML character meta:** Relationship between lineage’s `CHARACTER-META.jsonl` rows and per-channel `character-meta/*.yaml` — merge, mirror, or separate concerns?
3. **Background process owner:** Who runs append-only writers (Story Bot, cron, manual agent)?
4. **meta_prompt in clip prompts:** Story engine vs prompt-assembly v4 ownership for injecting `meta_prompt.text`.
5. **Still analysis confidence cutoff** for auto-append vs human review (schema open item).
6. **Relationships storage:** Per-character lists only vs network-wide relationship graph for crossovers.
7. **Repo layout on full import:** Whether `charmeta/` lives at repo root on merged snapshot or under `story-engine/` (coding brief assumes root package in Origin repo).
8. **N and normalization:** Exact text normalization for “same trait” across clips (case fold, punctuation strip).
9. **`.gitignore` allowlist** for real companion YAML and observation logs outside fixtures (coordinate with lineage plan PR).

---

## 11. Director-tested pipeline reconciliation (Nov 1, 2026)

Implementation branches align with the approved Director prompt path (context bundle: PROMPT-LESSONS, LAYERS/LAYERS-BODY-ORDER, lineage SCHEMA) without replacing working assembler behavior:

| Requirement | Implementation |
|---|---|
| Layer order | `charmeta/prompt_injection.py` merges `meta_prompt.text` into the shot **`characters`** block (before **`action`**); system wrappers 1–4 unchanged. |
| Prompt density / cap | `trim_meta_for_injection()` default 512 chars (`CHARMETA_META_PROMPT_MAX_CHARS`). |
| Never-words | `charmeta/name_guard.py` — same runtime-decoded real-first-name pattern as `assemble_prompt.py` / live checker. |
| Aired + N=3 | `lineage/eligibility.py` + `build_trait_promotion_aired_index()`; config `CHARMETA_PROPOSAL_THRESHOLD_N` (default 3). |
| Forward Supply | Excluded from observations ingest and promotion; stays home filler per bible resolutions PR #17. |
| Show masters only | Ads/commercials/embed rows never count toward trait promotion. |

Live `bible-v2.yaml` is still not modified by character-meta tooling.

---

## Locked decisions (Nov 1, 2026)

- **Director pipeline:** Keep approved/tested Director behavior that still works; layer the Nov 1 improvements on top. The new version wins only where this chat explicitly advanced it.
- **Ads and breaks vs trait evidence:** Ads and commercial breaks **may** contain characters (on screen or in copy). They **never** count as trait evidence for promotion. Enforced via show-master eligibility: `lineage/eligibility.py`, `is_show_master_row()`, `build_trait_promotion_aired_index()` (implementation PRs #8 / #15 / #16).
- **One live instance:** Means one **copy** of the same character at a time (duplicate-instance rule), **not** a limit of one person on screen.
- **Promotion threshold:** Environment variable `CHARMETA_PROPOSAL_THRESHOLD_N`, default **3** (schema `rules.N` in `CHARACTER-META-SCHEMA-v1.yaml`).
- **Forward Supply:** Never feeds character-meta observations or BLACK ICE / photoreal 1971 prompt look; approved home filler only (canon PR #17).
- **Unresolved doc conflicts (default pending trundle):**
  1. **Eye contact global vs per-show** — *Sources:* `prompts/LAYERS.md` (2026-10-28 12:45 CT: global) vs `prompts/LAYERS-BODY-ORDER.md` (2026-10-28 12:40 CT: per-show opt-in). **Default used:** treat no eye contact as global per LAYERS.md correction. **Status:** default pending trundle.
  2. **`meta_prompt` injection owner** — *Sources:* plan §9.4 (open: story engine vs prompt-assembly v4) vs PROMPT-ASSEMBLY-NOTE-v1 (OPEN owners). **Default used:** `charmeta/prompt_injection.py` on the charmeta side until assembler merge. **Status:** default pending trundle.
  3. **Character meta storage shape** — *Sources:* plan §9.2 (JSONL vs YAML open) vs `CHARACTER-META-SCHEMA-v1.yaml` (YAML companion + `trait_observations.jsonl`). **Default used:** YAML companion + observation log per schema. **Status:** default pending trundle.

---

## 10. References

- Continuity promotion model: `story-engine/continuity/ch04-military-boutique/SCHEMA.md` (on `import/snapshot-20261031`)
- Parallel plans: `origin/plan/lineage-v1`, `origin/cursor/stills-meta-scaffold-plan-a5c4`, `origin/playout/queue-mutation-plan`
- Agent skill draft: `docs/spec/character-meta/CHARACTER-META-SKILL-DRAFT-v1.md` (plan-first, dry-run default, single writer per channel log)
