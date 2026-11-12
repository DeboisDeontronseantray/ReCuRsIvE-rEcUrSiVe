# Commenter prompt schema (layer 6), `commenter-prompt/v1`
Owner: Director, Oct 28 2026, approved by trundle 6:14 PM CT. Home-only. Nothing airs. Machine-readable: `commenter-prompt.schema.json` (JSON Schema 2020-12, its 5 examples validate).

## Sources
- [x-intake] `/workspace/shared/streaming/x-intake/HANDOFF.md` "Queue item contract (schema x-intake/v1)" + export contract; read by `story-engine/live/intake.py`.
- [embed] `thunder-trundle/commenter/README.md` (embed), `streaming/commenter-pipeline/comment_prompts.py` (store row), `lineage/SCHEMA.md` (embed rows, commenter_prompt_ids).
- [slot] `streaming/story-engine/rules/queue-policy.yaml` `comment_prompt_slots`, `prompt_layers_locks`.
- [new] Director, this file.

## Fields (31 top-level)
| field | source | notes |
|---|---|---|
| record_schema | new | const `commenter-prompt/v1` |
| schema | x-intake | const `x-intake/v1` |
| status | x-intake | HELD_FOR_trundle / APPROVED / AUTO_APPROVED / REJECTED / IN_STORY / RENDERED / AIR_OK (existing literals; only trundle approves) |
| target, show, channel, rules{channel, channel_name, network, bible, continuity, banned[], brands, ai_disclosure, airing}, credit_line | x-intake | exact names |
| commenter{handle, source, message_id, ts} | x-intake | |
| commenter_text, commenter_text_verbatim, commenter_text_sha256 | x-intake | verbatim, never edited, sha must match |
| wrapped_at, approved_by, approved_at | x-intake | approved_* from export contract |
| prompt_id, global_no, link, merged_into, park_reason, writer, written | embed (comment_prompts.py) | |
| queue_status | embed (comment_prompts.py `status`) | renamed only to avoid clash with x-intake `status` |
| embed | embed (commenter/README) | `{clip_no}` or `{lineage[, gen]}`; README's `global_no` = `clip_no` |
| target_parent{parent_no, lineage, gen, result_gen, shot_id?} | new | result_gen = gen+1 |
| layer6_change{change_type, payload} | new | exactly ONE change |
| lock_refs_touched[] | new | lock ids read or swapped; locks never edited |
| moderation{status, reasons[], conflict_layer, checked_at, log_path} | new | rejected needs reason + conflict_layer + log_path |
| slot{target_slot, render_eta_min (15), margin_min (10), skipped_breaks 0-3, protected_unaired, merged_prompt_ids[]} | slot | `skipped_breaks` also in comment_prompts.py |
| retention | new | const `never_delete` |
| air | new | const `needs_trundle_yes` |

## layer6_change payloads (one per record)
- action: `{action, performer_lock?}` one beat
- dialogue: `{speaker_lock, line, delivery_cue "[...]"}`
- props: `{op swap|add|remove, from_lock?, to_lock?, description?}` swap = existing PRP lock to existing PRP lock
- weather: `{weather, time_of_day?}`
- screen_insert: `{surface, exact_text ≤60, position: lower_third}`
- embed: `{ref: {clip_no} XOR {lineage, gen?}, surface}`; resolved by engine/resolve_embed.py, clean masters only; unknown ref = hold, not delete

## Hard rules
1. Layer 6 can never override global, channel or format layers, or any lock (no new CHR/LOOK, no deprecated/selectable:false locks). A conflicting request is REJECTED and logged with its reason, never deleted. Comment prompts are never deleted (`retention: never_delete`).
2. Hard limits: no kids; no real people or brands outside parody; nobody looks into the camera; text in the lower third only, never centered.
3. Nothing airs without trundle's yes.

## Examples (full JSON in the .json `examples`)
Valid: (1) dialogue, HERON `"Only the ice is asking." [flat, not looking up]` on #101 (4.13 g1 → g2). (2) weather, heavy wet snow at the ferry landing. (3) embed `{clip_no: 58}` on the dark radio-room CRT.
Rejected: (4) "Heron winks into the camera" → global conflict, logged. (5) olive jacket + centered title → lock (WAR-HERON-OLIVEJACKET-v1 not selectable) + centered text + two changes, logged.

## image_ref (optional, added Oct 28 2026, trundle-approved 7:03 PM)
- Optional field on any layer6_change: `{source{kind: x_attachment|url|trundle_refs, uri}, sha256, use, filter, overrides_locks:false}`.
- use is one of prop, wardrobe_detail, screen_insert, palette_hint or weather_hint. Never a face, a character identity, a location replacement or a starting frame.
- filter: real_face, brand_or_logo and minor must all be false to reach status "pass". Anything else is held, never deleted. A broken link is also held.
- Never overrides a lock or layers 1-3. A lock always wins. Max 1 image per change. trundle's own refs become locks only through Director, not through image_ref.
- Doc/schema only: intake download, filter and assembler support are not built yet.

2026-10-28 ~10:30 PM CT (Director, trundle t121): image_ref.use adds `identity_setting`, valid only with source.kind `trundle_refs`. Commenter filter is unchanged. See PROMPT-STYLE.md. Add-only.


## 2026-10-28 note (trundle t132)
Commenter image_ref stays OPTIONAL in commenter-prompt.schema.json. Commenter changes ride on the shot's own reference images, which are required (>=1, character sheets first) at assembly.

## 2026-10-29 v2 add-only (Director; trundle approved MUTATION-SPEC-v2 defaults 11:35 AM CT, "Yes mutation 2 good")
Supersedes "exactly ONE change" / "one beat" for bundled comments (gap-check conflict 1). The one-change path stays as the legacy path.
- `layer6_change` may hold a LIST of changes; each comment is woven verbatim at full density into the action block of trundle's JW skeleton (TRUNDLE-VERBATIM-t121.md #2, minus "Extend this video:").
- New fields: `tier` (unpaid|paid), `window_id` (ch<nn>-<date>-<HHMM>-w30), `landed_in{clip_id, beat}`, `moved_for_conflict`, `merged_with[]`, `bent_from`, `branch_id`, `verbatim_sha`.
- Conflicts are placed in another beat or clip, else carried to the next window (priority_aging rises_with_wait, max_wait_breaks 3). Nothing is dropped; unbendable hard-limit hits are HELD (never deleted).
- Canon carry-over layers 5-8 (branch, episode, scene, clip) + fade 100/50/25/0 over g+0..g+3; after-effect snippets persist; canon ≤ 80 words.
- Code: streaming/story-engine/engine/bundle_assembler.py, entry `assemble_prompt.assemble_full_density()`; dry run engine/tests/dryrun_bundle_ch4.py.
