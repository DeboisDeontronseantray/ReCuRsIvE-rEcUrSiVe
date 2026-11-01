# CHARACTER META — CODING BRIEF v1 (for a Cursor Cloud Agent). Story Bot New, 2026-10-31 ~6:05 PM CT
Status: READY, NOT LAUNCHED. Launch waits on Trundle's yes. The live Ch4 bible is never modified.

## Plan
1. Launch one cloud agent on a NEW private Cursor Origin repo (no Thunder Trundle repo is connected; the only connected GitHub repo, DeboisDeontronseantray/GBT5, is unrelated and must not be touched).
2. Attach as files: lineage/CHARACTER-META-SCHEMA-v1.yaml, handoffs/current-job/CHARACTER-META-NOTE-v1.md, a COPY of bible-v2.yaml (read-only fixture), 20 sample rows of lineage/LINEAGE.jsonl.
3. Agent builds the store + stub + tests and opens a PR / pushes to the Origin repo.
4. Story Bot New reviews the diff against this brief and reports to Trundle. Installing onto the box is a separate step needing Trundle's yes.

## Recommended model
Composer 2.5 (Cursor's coding model): small, fully specified Python store with tests; fast and low cost. Fallback if it struggles: GPT-5.3 Codex at high reasoning.

## Build (Python 3, stdlib + PyYAML only)
- `charmeta/store.py`: loads the schema; one companion file per channel `character-meta/<NN-channel>.yaml`, keyed by cast id (read cast ids from the bible copy; never write the bible).
- Add-only `trait_observations.jsonl`: `append_observation()` validates against the schema; no update/delete functions exist. Corrections are new rows.
- `promote.py` (dry-run default): counts distinct AIRED clip_ids per (character, field, normalized text) by joining clip_id to LINEAGE rows that show aired/air_yes; at N=3 (from schema) writes a `proposed` entry to the companion file only with `--apply`. Never sets approved/locked.
- Conflict check: flags (never applies) any observation contradicting a locked/approved field or `qualities_locked`.
- `meta_prompt` builder: rebuilds from approved/locked entries only, bumps version, records built_from.
- `stills_stub.py`: interface only, `extract(image_path, clip_id) -> list[observation]` returning []; method=still_analysis. No model calls, no network, no spend.
- Character ids for BLACK ICE (HERON, LANTERN, WOLFHOUND) are NOT invented: the store accepts a cast id list as input and reports missing ids.

## Tests (must pass)
Add-only enforced; N=3 threshold (2 aired show-master clips -> no proposal, 3 -> proposal); unaired clips don't count; ads/commercials and Forward Supply filler never count; generation quirks never become traits; locked conflict is flagged; meta_prompt ignores proposed entries and trims to `CHARMETA_META_PROMPT_MAX_CHARS` (default 512); injected text lands in the shot `[characters]` layer before `[action]` (LAYERS-BODY-ORDER); name guard uses the same `\bdrew\b` filter as `assemble_prompt.py`; bible fixture byte-identical after a full run.

## Director pipeline alignment (Nov 1, 2026)
- Keep tested `assemble_prompt.py` layer order (global → channel → format → show_or_ad → shot → commenter; shot body characters before action).
- Promotion joins observations to LINEAGE rows with derived `aired` / queue `AIRED` status but counts only **show-master** rows (`lineage/eligibility.py`).
- Forward Supply segments remain home filler and are excluded from observations and trait promotion.
- Config: `CHARMETA_PROPOSAL_THRESHOLD_N` (default schema `N: 3`), `CHARMETA_META_PROMPT_MAX_CHARS` (default 512).

## Hard limits
No network calls, no paid APIs, no posting/airing, no personal names, home-only. Don't touch any existing repo.
