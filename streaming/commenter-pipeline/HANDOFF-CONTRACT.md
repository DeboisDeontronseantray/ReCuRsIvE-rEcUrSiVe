# Commenter pipeline handoff contract (draft, 2026-10-27 16:30 CT, Commercial News Break)
## IN (X Live Stream owns X: comment intake + broadcasting)
- Drop JSON files (one object or an array) into `inbox/`, matching `schema/commenter-prompt.schema.json`:
  `handle`, `text`, `timestamp` (ISO 8601 with offset), `source_post_id` (or "manual"); optional `id`, `cast`, `out_of_character`, `intake_by`.
- X Live Stream's proposed `/workspace/shared/streaming/commenter-queue.jsonl` is not read yet. If X Live Stream prefers it, CNB will add a reader that writes the same records into `inbox/`.
- CNB moves processed files to `inbox/processed/` and never deletes them.
## OUT (playout: ErsatzTV / Device Engineer, later)
- Files: `outbox/<id>_ch04_commenter_parody.mp4`, H.264/AAC 48k, 848x480, -14 LUFS. "parody" appears only in the file name and metadata.
- `outbox/manifest.jsonl` has one row per clip: id, file, duration_s, handle, source_post_id, prompt_text, cast, self_reflection, lufs, ocr_pass, status=`staged-needs-thundertrundle-yes`, thundertrundle_air_yes=false, insert_hint.
- Playout must pick up only rows with `thundertrundle_air_yes: true` and `ocr_pass: true`. Insert clips at clean breaks, never inside a scene. Nothing is loaded into ErsatzTV yet.

## Injections (added 16:40 CT)
- Optional input field `manual_injections: [ids from injections.json]`.
- New manifest fields: `weak_score`, `injections[]`, `post_tts_cues[]` (character, line, timing, voice), `post_overlays[]`, `injections_status`. The sidecar file `outbox/<id>_tts_cues.json` lists the TTS still to be done.
- Playout must not air a clip while `injections_status` is still `draft-needs-thundertrundle-ok` or any TTS cue's voice is still `TBD-trundle`.

## IN (supersedes the IN section above, 2026-10-27 16:45 CT)
- Only Story Bot writes `inbox/xls-<source>-<message_id>.json`. Required fields: handle, text (verbatim), timestamp, source_post_id, `intake_by: "Story Bot"`, and a trundle marker (`status` APPROVED or IN_STORY, or `thundertrundle_approved: true`). Optional: id, commenter_text_sha256, credit_line, wrapped_prompt, story_slot, end_frame, out_of_character.
- X Live Stream's `export_cnb.py` (intake_by "X Live Stream", no status field) is **rejected** by design. Per the spec, it may run only when Story Bot calls it, and it must set intake_by=Story Bot.
- Dedupe key: `<source>-<message_id>` (the id) and source_post_id.
## OUT addition
- Manifest rows also carry credit_line and story_wrapped_prompt. They always start with `thundertrundle_air_yes: false` and `status: staged-needs-thundertrundle-yes`. Device Engineer copies them to Mac `~/fakenews_out/held/commenter/`, and a clip goes to ErsatzTV only after trundle's AIR_OK.

## Auto mode (16:50 CT)
- Status `AUTO_APPROVED` is accepted only while AUTO_APPROVE_PROMPTS is true. Rows carry `approved_by` (trundle or auto-gate).
- `outbox/held/` is **never** for air. Playout reads only top-level `outbox/` rows with status `staged-needs-thundertrundle-yes` (after trundle's AIR_OK) or `auto-air-yes` (only once trundle has flipped AUTO_AIR_YES and the spec allows it). Rows have `hold_reasons`.
- Note: manifest rows for t6, t7, t8 and t9 are test rows. t9 was revoked by a later row; playout must honor the latest row per id.
