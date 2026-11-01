# PROPOSED addendum: flexible preemption + prompt queue + duplicates (trundle 18:01 / 18:05 CT)
Proposed for /workspace/shared/streaming/CLIP-PROMOTION-PROCESS-20261027.md (shared doc NOT edited; parent forwards to Smart Home Lead). Home-only.

## Preemption (18:01)
a. Each queue slot points to a lineage: `slot_head = {lineage '4.N', root #, head #}`. It plays the newest version that is READY and APPROVED (`checker.slot_head`).
b. A new version carries the same lineage, gen+1, parent #, `supersedes` #old and `slot_id`. On approval the head pointer moves (`checker.approve`).
c. The old version gets status=superseded, `superseded_by` and `superseded_at`. Nothing is deleted. Rollback moves the head back (`checker.rollback`, `head_history`).
d. Comment prompts get permanent `cp-` ids in add-only `/workspace/streaming/queues/COMMENT-PROMPTS.jsonl`. Each clip row carries `prompt_ids`: its parent's list plus its own. Superseding never removes or edits a prompt row.
e. Every version in a slot matches the same slot anchors (in = prev clip's clean last frame, out = next clip's clean first frame).

## Prompt queue (18:05)
- Never deleted. State is waiting | combined | aired | held, and changes only through new add-only rows.
- Prompts that fit together (same show, premise or character) merge into one clip. The clip's `prompt_ids` lists every included prompt, and all are marked used (combined).
- Wait time raises priority. `max_wait_loops` defaults to 3 (configurable). At max wait, a prompt takes the next clean break ahead of new prompts.
- A prompt that fails a filter is held with its reason, plus a safe rewrite where possible.

## Duplicates (18:05)
- Premise fingerprint = show + premise keywords (embedding later).
- A near-duplicate becomes a sibling in the existing lineage: (a) same idea: rotate in the slot; (b) new take: next episode or callback; (c) drifted far enough: spin off into a new lineage with a link back.
- Exact copies (same sha256/phash) air once. Extra copies are kept, marked `duplicate_of` and `airable=false`. Never dropped.

## Schema / code
- QUEUE-PLAN-20261027.json v2: per item `slot_id`, `slot_head`, `head_history`; per break slot `slot_id`, `anchors`; top-level `schema`, `max_wait_loops`. v1 is kept as QUEUE-PLAN-20261027.v1-pre-preempt.json.
- checker.py, append-only (backups .bak-20261027-1803-preempt, -1807-promptqueue): slot_head, new_version, approve, rollback, preemption_fails, add_comment_prompt, prompt_state, set_state, next_for_break, combine, hold_prompt, fingerprint, classify_duplicate, register_clip.
- Tests: tests/test_preemption.py (superseding keeps all prompt rows, rollback, unapproved version not played, dropped-prompt and anchor-drift flagged) and tests/test_prompt_queue.py (max-wait reaches head, combined clip lists all ids, never deleted and held with reason, duplicate never dropped, near-duplicate classes). The full suite has 77 tests; all pass.

## 18:10 CT update — unified prompt states (per shared CLIP-PROMOTION-PROCESS 18:09)
- Open: WAITING, PARKED (park_reason). Terminal: AIRED, MERGED (merged_into), WITHDRAWN (trundle only). Nothing deleted.
- Renames: combined→MERGED, held→PARKED; old lowercase names remain read aliases (checker.STATE_ALIASES).
- skipped_breaks capped at 3 (checker.SKIPPED_BREAKS_CAP, configurable); a prompt at the cap is guaranteed the next break.
- Clips carry comment_prompt_ids[]; DE pickup refuses preempt/retire leaving a linked prompt non-terminal (checker.unterminated_prompts).

## 18:29 CT — overlay text rule (trundle)
- Requested on-screen text in a comment prompt (prices, labels, captions, signs, quoted 'says'/'reads'/'with the words' text) is extracted by `checker.split_overlay_text(prompt) -> (gen_prompt, overlay_specs)` and never sent to generation.
- Every gen_prompt gets the constraint "no readable text, no signage lettering". `checker.gen_prompt_requests_text()` flags any gen_prompt still asking for readable text.
- Overlay spec = {text, kind, position, start_s, end_s, style, prompt_id, blocked[], airable}. Burned in post-process on a separate copy, like the genealogy tag. The clean text-free master stays the mutation parent and anchor-frame source.
- Overlay text runs through the same filters: no owner first name, no kids, no real brands, no money/donation/tip lines, no Military Boutique text (blocked → airable=false).
- COMMENT-PROMPTS.jsonl row format adds `gen_prompt` and `overlay_specs[]`. Edits are add-only rows with the same id and new `overlay_specs`; latest wins (`checker.overlay_specs_for`), no re-render.
