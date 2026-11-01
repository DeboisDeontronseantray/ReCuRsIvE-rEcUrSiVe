# Engine scripts (planned; none written yet except checker.py, which still lives in live/)
- new_channel.py   copy templates/channel -> channels/<NN>-<slug>, add to REGISTRY.yaml, enforce whole 2-22
- new_show.py      copy templates/show, register lineage in genealogy/LINEAGES.yaml
- resolve_slot.py  slot lineage -> newest approved, non-replaced clip
- merge_prompts.py combine compatible comment prompts, write merges.jsonl
- age_priority.py  raise priority with wait, enforce max_wait from rules/queue-policy.yaml
- burn_overlay.py  the ONLY writer to cut/: ffmpeg burn from overlay_specs + rules/overlay-style.yaml
- build_stream.py  stream/<channel>/ links only to clips in approvals/AIR-APPROVALS.jsonl
- checker.py       currently /workspace/streaming/story-engine/live/checker.py (95/95 tests)
- resolve_embed.py  WRITTEN: ref (#58 / 4.1:2) -> clean master; prints origin:embed LINEAGE row for CNB to append

2026-10-28 12:45 CT: no-eye-contact always-on (global, Trundle 10:41 CT); channel lookup via CHANNEL_DIRS for 02/04/06/08/10/12/14, unknown/missing channel raises UnknownChannelError (no Ch 4 fallback). Story Bot per Director spec.
