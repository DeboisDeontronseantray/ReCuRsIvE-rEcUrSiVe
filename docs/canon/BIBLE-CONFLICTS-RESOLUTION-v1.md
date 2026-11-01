# Bible conflicts resolution v1 (additive canon notes)

Status: **recorded defaults** (trundle, Nov 1, 2026). Additive documentation only — does **not** rewrite live `story-engine/continuity/ch04-military-boutique/bible-v2.yaml` or historical ledgers.

Purpose: resolve overlapping channel/show/character labels found across INDEX drafts, slates, and working bibles so agents stop re-litigating the same conflicts.

---

## Ch 4 — channel identity

| Topic | Resolution |
|---|---|
| **Channel identity** | **Military Boutique / BLACK ICE** — locked network index choice **Oct 28, 2026**; **photoreal 1971** look pick **Oct 30, 2026**. |
| **Primary show brand on Ch 4** | **BLACK ICE** (Military Boutique is the channel shell / boutique framing). |
| **Forward Supply** | **Legacy pre-reboot Ch 4 show.** Its segments remain **approved home filler** (trundle: *“Yes on forward supply segments”*, **Oct 29, 2026**). Forward Supply is **not** the channel identity and must not replace BLACK ICE / Military Boutique indexing. **Character-meta:** Forward Supply clips must not append trait observations or feed BLACK ICE `meta_prompt` / photoreal 1971 look (home filler only). |
| **Other Ch 4 shows** | Clearance Brief, Depot After Hours, house ads, etc. stay as catalog/filler per existing bible; this doc does not retire them. |

---

## Ch 2 — anchors and crossovers

| Topic | Resolution |
|---|---|
| **Ch 2 anchors** | **Dora Vance & Hal Brisk** (desk), **field reporter Tess Okafor**, **Gale Morrow**, **heli pilot Skip**. |
| **Dale & Marla** | **Ch 12** (*Dale & Marla Live*) — **not** Ch 2 hosts. Oct 26 **KTVM** draft slates that placed them on Ch 2 are **superseded**. |
| **Marla home channel** | **Ch 12**. |
| **Crossovers** | Any Ch 2 appearance by Dale/Marla/Tess/etc. is a **deliberate crossover only**, subject to the **one live instance at a time** duplicates rule. |
| **Surname** | **“Venn-Oakes”** — **unused / pending** trundle decision; do not assign in prompts or bible text until approved. |

---

## Ch 11 — Fist Theater

| Topic | Resolution |
|---|---|
| **Channel** | **Fist Theater** (approved). |
| **Main show** | **The Night Porter** (approved). |

---

## Repo-local additive edits (this PR)

Clarifying comments / fields only (no content rewrites):

- `story-engine/channels/04-military-boutique/channel.yaml`
- `story-engine/channels/04-military-boutique/SHOWS.md`
- `story-engine/configs/channels/04-military-boutique.yaml`
- `story-engine/configs/channels/12-90s.yaml`

**Not edited:** `story-engine/continuity/ch04-military-boutique/bible-v2.yaml` (live bible on the box).

---

## Follow-ups outside this repo (manual / other agents)

These fixes live in paths not vendored on `main` today; track separately:

| Item | Where | Issue |
|---|---|---|
| Ch 11 “unassigned” | channels **INDEX** / **PROJECT-STATE** | Should read **Fist Theater** + **The Night Porter** (approved). |
| Ch 2 slates | KTVM / Oct 26 draft slates | Dale & Marla shown as Ch 2 — superseded; anchors per above. |
| Shared lineup | `shared/streaming` lineup + **character bible** | Align Dale/Marla to Ch 12; Ch 2 anchor list; Ch 4 identity = Military Boutique / BLACK ICE. |

---

## Locked decisions (Nov 1, 2026)

- **Director pipeline:** Keep approved/tested Director behavior that still works; layer the Nov 1 improvements on top. The new version wins only where character-meta / lineage work explicitly advanced it.
- **Ads and breaks vs trait evidence:** Ads and commercial breaks **may** contain characters (on screen or in copy). They **never** count as trait evidence for promotion. Enforced via show-master eligibility: `lineage/eligibility.py`, `is_show_master_row()`, `build_trait_promotion_aired_index()` (implementation PRs #8 / #15 / #16).
- **One live instance:** Means one **copy** of the same character at a time (duplicate-instance rule), **not** a limit of one person on screen.
- **Promotion threshold:** Environment variable `CHARMETA_PROPOSAL_THRESHOLD_N`, default **3** (schema `rules.N` in `docs/spec/character-meta/CHARACTER-META-SCHEMA-v1.yaml`).
- **Forward Supply:** Never feeds character-meta observations or BLACK ICE / photoreal 1971 prompt look; approved home filler only (see Ch 4 table above).
- **Unresolved doc conflicts (default pending trundle):**
  1. **Eye contact global vs per-show** — *Sources:* `prompts/LAYERS.md` (2026-10-28 12:45 CT: global) vs `prompts/LAYERS-BODY-ORDER.md` (2026-10-28 12:40 CT: per-show opt-in). **Default used:** treat no eye contact as global per LAYERS.md correction. **Status:** default pending trundle.
  2. **`meta_prompt` injection owner** — *Sources:* CHARACTER-META plan §9.4 (open: story engine vs prompt-assembly v4) vs PROMPT-ASSEMBLY-NOTE-v1 (OPEN owners). **Default used:** `charmeta/prompt_injection.py` on the charmeta side until assembler merge. **Status:** default pending trundle.
  3. **Character meta storage shape** — *Sources:* plan §9.2 (JSONL vs YAML open) vs `CHARACTER-META-SCHEMA-v1.yaml` (YAML companion + `trait_observations.jsonl`). **Default used:** YAML companion + observation log per schema. **Status:** default pending trundle.

---

## Standing rule (technical defaults)

Purely technical clarifications outside personal/creative scope use these defaults until trundle overrides in chat. Canon promotion and airing still require trundle’s yes.
