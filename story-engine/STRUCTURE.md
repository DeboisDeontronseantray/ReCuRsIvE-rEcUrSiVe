# story-engine structure (skeleton added Oct 28, 2026, 11:08 AM CT; add-only)

```
story-engine/
├── templates/                copy, never edit in place
│   ├── channel/              channel.yaml, bible.yaml, CHANGELOG.md, shows/, ads/, best-list/{BEST.jsonl, stills/}
│   ├── show/                 show.yaml
│   └── episode/              prompts.json, overlays/overlay_specs.json, anchors/, masters/, cut/, qc/, BRIEF.md, STATUS.md
├── channels/
│   ├── REGISTRY.yaml         whole-number channels 2-22, with old paths
│   └── 04-military-boutique/ channel.yaml, SHOWS.md, shows/, ads/, best-list/{BEST.jsonl, stills/}
├── rules/                    hard-limits, overlay-style, tag-format, queue-policy (.yaml)
├── genealogy/                LINEAGES.yaml, LINEAGE-POINTER.md, LINEAGE.jsonl (link to Commercial News Break's file)
├── director/                 README.md, pitches/PITCHES.jsonl, briefs/{BRIEFS.jsonl, ch04/},
│                             direction-notes/{notes.jsonl, ch04-channel-voice.md}, series-plans/ch04/,
│                             handoffs/{to-story-bot, from-story-bot}/, clashes.jsonl, archive/
├── queues/                   merges.jsonl, priority.jsonl, shifts.jsonl, held/, promotions/,
│                             slots/04-military-boutique.json, README.md
│                             + links: COMMENT-PROMPTS.jsonl(+schema), PROMOTION-PROCESS.md,
│                               PREEMPTION-ADDENDUM.md, QUEUE-PLAN-20261027.json
├── approvals/                AIR-APPROVALS.jsonl (trundle's own yes only), README.md
├── engine/                   README.md (planned scripts; checker.py still in live/)
├── stream/                   README.md, 04-military-boutique/ (empty until something is approved)
└── existing, untouched:      configs/, continuity/, data/ (shows, pilots, refs, exports, spend), live/, server/, client/, docs/
```
