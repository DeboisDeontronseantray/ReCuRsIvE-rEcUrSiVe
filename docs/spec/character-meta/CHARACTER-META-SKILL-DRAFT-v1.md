---
name: character-meta-observation-log
description: Use when appending character observations from aired Thunder Trundle clips, checking which traits reached the 3-aired-clip threshold, or building/running the character-meta store with a Cursor Cloud Agent. Not for editing a live bible.
---
# Character meta: observation log and promotion (DRAFT v1, Story Bot New, 2026-10-31)
Status: DRAFT. Not installed as a skill. Nothing runs until Trundle says yes.
Sources: lineage/CHARACTER-META-SCHEMA-v1.yaml, handoffs/current-job/CHARACTER-META-NOTE-v1.md, handoffs/current-job/CHARACTER-META-CODING-BRIEF-v1.md.

## Plan first
Before any run or code change, write a short plan (goal, files read, files written, stop point) in the agent's first message or PR description. No plan, no run.

## Rules (from the schema)
- Live bibles are read-only. Writes go only to the companion files `character-meta/<NN-channel>.yaml` and the add-only `trait_observations.jsonl`.
- The log is append-only. No edits or deletes; corrections are new rows.
- An item becomes `proposed` only after 3 distinct aired clip_ids (aired = LINEAGE row shows aired/air_yes). Unaired drafts don't count.
- proposed -> approved needs Trundle's yes. Locked qualities never change automatically.
- Conflicts with locked/approved fields are flagged, never applied.
- Generation mistakes go to generation_quirks, never to traits or abilities.
- No invented character ids; missing ids are reported.
- No network, no paid calls, no airing or posting. Home-only.

## Steps
1. Append: validate the observation against the schema, then append one row.
2. Promote (dry run by default): count aired clips per (character, field, normalized text); list what would be proposed and any conflicts. Write with `--apply` only when told.
3. Rebuild meta_prompt from approved/locked entries only; bump version.
4. Report: rows added, proposals (dry run or applied), conflicts, missing ids. One status line to coordination/STATUS-story-bot.txt.

## Cursor Cloud Agent use
- Coding work (building or changing the store) goes to a Cursor Cloud Agent, not the CLI, so Trundle can watch it.
- Repo: a new private Cursor Origin repo. Never the unrelated connected GitHub repo, and never Rohan's repo.
- Model: Composer 2.5 for the small, well-specified build and tests; GPT-5.3 Codex (high) as the fallback for hard bugs. Pick per job; don't default.
- Attach the schema, note, brief, a bible COPY and sample LINEAGE rows as files. Results come back as a PR or Origin commit; installing onto the box is a separate yes.

## Parallel agents and follow-ups
- One cloud agent owns the store code at a time. Parallel agents may only do read-only work (review, test ideas) or work in separate files.
- Follow-ups and fixes go to the same agent as a reply (queued), not a new agent, so the history stays in one place.
- Only one writer appends to a channel's log at a time. A second run waits or works dry-run only.
- Each run logs one status line; stop and report on any conflict, missing id, or test failure.

## Open (not decided)
Who runs the background process; who assembles meta_prompt into clip prompts; the confidence cutoff for still analysis; relationships per character or network-wide.
