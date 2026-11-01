# CHARACTER META NOTE v1 (proposal only). Story Bot New, 2026-10-31 ~4:40 PM CT
Status: PROPOSED. The live bible (streaming/story-engine/continuity/ch04-military-boutique/bible-v2.yaml) is NOT modified. Nothing here promotes without Trundle's yes.
Basis: the existing SCHEMA.md model (locked qualities, proposed->approved promotion, per-clip observations, aired_history, callbacks, generation_quirks kept separate). Canon is emergent: these fields start empty and fill from what airs. No forced roles.

## What already exists per cast entry (keep as-is)
locked_description, still, turnaround_paths, qualities_locked, demeanor, fuse, catchphrase, status, approved_by/approved_at, notes.

## Minimal additions per cast entry (all optional, all start empty)
```yaml
traits:
  tangible:        # visible and extractable from stills by image analysis
    - {id, text, source_clip, confidence, status}   # e.g. "brass tag, blank", "left side braid"
  intangible:      # personality, habits, values, voice manner; from what plays out on screen
    - {id, text, source_clip, status}
abilities:         # only what a character has actually done on screen
  - {id, text, first_seen_clip, times_seen, status}
relationships:     # pairwise, can be one-way
  - {with, kind, text, first_seen_clip, status}
meta_prompt:       # distilled short prompt text, built only from approved fields
  text: ""
  built_from: []   # ids of the trait/ability/relationship entries used
  version: 0
```
status uses the existing states: proposed | approved | locked (plus retired, never deleted).

## Background process support (one shared log, add-only)
```yaml
trait_observations:   # sits next to the existing observations log
  - {obs_id, clip_id, character, field, extracted_text, method: still_analysis|aired_event|human_note,
     seen_count, proposed_status, decision, decided_by, decided_at}
```
## Slow writing-in rule (proposal)
1. The background process only appends to trait_observations; it never writes cast fields.
2. An item becomes "proposed" on the cast entry only after it repeats across N separate aired clips (suggest N = 3, Trundle sets it).
3. proposed -> approved needs Trundle's yes (matches SCHEMA.md rule 3). Locked qualities never change automatically.
4. A contradiction with a locked or approved field is flagged, never auto-applied.
5. Generation mistakes go to generation_quirks, never to traits (matches SCHEMA.md rule 4).
6. meta_prompt is rebuilt only from approved/locked entries; each rebuild bumps version.

## Open (not decided here)
- Who runs the background process, and who assembles meta_prompt into clip prompts (story vs prompt-assembly ownership is open).
- The N threshold and the confidence cutoff for still analysis.
- Whether relationships live per character or in one network-wide list for crossovers.
