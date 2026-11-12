# Mutation gap check v2 (Director, Oct 29 2026 ~11:25 AM CT)
Compares the current system against specs/MUTATION-SPEC-v2.md. Read-only check; NO code changed. Proposed changes are a list only.
SE = /workspace/streaming/story-engine (thunder-trundle/engine symlinks here). CP = /workspace/streaming/commenter-pipeline.

## Already exists (keep)
- Slot targeting, protect unaired comment videos, collisions shift/merge, never drop, max_wait 3 breaks, show masters pure, ads separate — SE/rules/queue-policy.yaml `comment_prompt_slots`.
- Never delete comments, hold on failed filter, rollback to older gen — queue-policy.yaml `comment_prompts`, COMMENTER-SCHEMA.md `retention: never_delete`.
- Layer order + commenter may not override layers 1-3 — prompts/LAYERS.md; enforced in SE/engine/assemble_prompt.py (PROTECTED fields dropped and reported).
- Chain start from previous last frame — assemble_prompt.py `prev_last_frame()` (uses `last_frame_clean_extract`), CP/pipeline.py `extract_last_frame()`; lineage/SCHEMA.md `start_frame`, `end_frame`, `chain`, `chain_basis`.
- Lineage, parents, inherited comment ids — lineage/LINEAGE.jsonl, CP/comment_prompts.py `inherited()`, `prompt_layers`, `commenter_prompt_ids`.
- Dense output mode / JW skeleton verbatim — prompts/PROMPT-STYLE.md, prompts/references/TRUNDLE-VERBATIM-t121.md, assemble_prompt.py `densify()`.
- v6 chaining rules (dense single move, fixed-mount cam line, stays down, Only weapon, re-render forward) — prompts/CONTINUITY.md, prompts/LESSONS.md.
- Arsenals — channels/<nn>/ARSENAL-v1.md (13 channels). Hard limits — SE/rules/hard-limits.yaml.
- Spend guards — CP/pipeline.py `xai_month_spend()`, `safety_stop()` (session cap, MAX_CLIPS_PER_HOUR, KILL_SWITCH).

## Conflicts
1. **One change per comment.** COMMENTER-SCHEMA.md `layer6_change` = "exactly ONE change"; action payload = "one beat". Spec §2 wants the comment woven at full density into a whole action block. → conflict.
2. **Comment block appended last, separately.** assemble_prompt.py builds `[Commenter changes; …]` as its own trailing block (lines ~200-203) instead of merging into the action block. → dilution risk trundle named.
3. **Reject vs bend.** COMMENTER-SCHEMA hard rule 1: conflicting request is REJECTED; assemble_prompt drops fields. Spec §2: bend to fit, reject only unbendable hard limits.
4. **Comments can't touch weather/time as episode lock?** queue-policy allows `weather`; v5 lessons treat weather as episode-locked (snow drift). Spec §6 puts weather in layer 6 (episode), changeable by comments but flagged as a reconvergence breaker. Needs one rule.
5. **Monthly cap value.** CP/config.json `xai_monthly_cap_usd` = **150** (read by pipeline.py line 244 and made_up.py line 15). trundle raised it to **$250** (t196). Stale value; October spend (~$155) is already over 150, so this pipeline would refuse renders.
6. **Lineage has 19 row formats, 44 rows without `lineage`** (lineage/README.md) — branch/ancestor queries in spec §5 can't rely on it yet.
7. **No-eye-contact history**: LAYERS.md has a superseded per-show note; fine (correction present), just noisy.

## Missing
1. Handoff contract check: no "clean handoff frame" validator (steady, no text, mount noted) and no reconvergence/ripple-limit logic.
2. Branch/universe fields: `branch_id`, `parent_branch`, `forked_at`, `ancestors[]`, `canon_snippet` — not in lineage/SCHEMA.md.
3. Canon layers network / show / branch / episode / scene as stored canon — only file-layers global/channel/format/show_or_ad/shot/commenter exist. No branch canon file.
4. Bundling window gate + placement log (`window_id`, `landed_in`) — none; current flow is per-prompt.
5. Playthrough rule (one re-render per slot per playthrough) — none.
6. Tiers paid/unpaid — no `tier` field anywhere.
7. Timed fade + after-effect snippets + canon size cap/summary step — none.
8. Cross-owner notices (MUTATION-NOTICES.jsonl) and `canon_spill` lineage rows — none.
9. Per-window / per-day comment render caps and a comment reserve — only session cap ($5) and clips/hour.
10. Unified queue format — queues/README.md: three slot formats exist, not unified.
11. Pipeline is Ch 4 only; commenter/README.md: per-channel commenter folders not wired.

## Proposed changes (list only — nothing applied; each needs Director sign-off, add-only + backups)
1. COMMENTER-SCHEMA add-only v2: `layer6_change` may hold multiple changes; add `tier`, `window_id`, `landed_in`, `bent_from`, `branch_id`.
2. assemble_prompt.py: new dense mode that rewrites the shot's action block with the comment merged (keep the old trailing block for v1 records).
3. assemble_prompt.py: replace drop-on-conflict with "bend + log" for non-hard-limit fields; keep hard-limit reject.
4. lineage/SCHEMA.md add-only: branch fields, `canon_spill` row type, `handoff {mount, clean:bool, state_lines[]}`.
5. New `lineage/branches/<branch_id>.yaml` canon file with layered facts + fade counters + summary.
6. New bundler step (window gate, placement log, playthrough counter) in front of the prompt builder.
7. queue-policy.yaml add-only block `mutation_v2`: window_min, ripple_limit 3, once_per_playthrough, daily/window caps, comment reserve.
8. CP/config.json: set `xai_monthly_cap_usd: 250` (backup first).
9. Handoff validator script (ffmpeg last-frame blur/SSIM + text check) — free, local.
10. coordination/MUTATION-NOTICES.jsonl + one-line format for CNB, Media Librarian, Playout Engineer, Story Bot, State Keeper.
11. Normalize LINEAGE row formats before branch queries (Media Librarian task).
