# Dress Inspection: Ch 4, Clearance Brief rebuild (Story Bot, 2026-10-27 CT)
Brief: /workspace/director/brief-dress-inspection-20261027.md (Director; trundle said "Let's go" at 7:36 PM CT).
Status: PROMPTS ONLY. Nothing rendered, nothing spent. Paid render needs trundle's yes on the price below.

## Files
- prompts.json: 11 generation prompts, Bill's beats only. Refs are the locked cast stills, resolved through checker.resolve_clean. Every prompt ends with "no readable text, no signage lettering".
- overlay_specs.json: 10 post overlays (DRESS INSPECTION bug, 7 insult captions, PASSED: 1 / 7). Made by checker.split_overlay_text, never sent to the generator.
- bookkeeping-pending.jsonl: 11 draft node rows plus 7 reused-ad reference rows. LINEAGE.jsonl was NOT written (CNB is the only writer).
- anchors/: first and last frames of the 7 clean ad masters (4_Military-Boutique/raw/mb_*.mp4).
- checker-result.json: pass 11, warn 0, fail 0.
- build.py: rebuilds everything, makes no API calls.

## Shots (all grok-imagine-video-1.5, 480p, the model the run2 remakes used)
DI-01 wide entry 6 s | DI-02-1..7 takedowns 6 s each (one per product) | DI-03 Mira cutaway 6 s | DI-04 Osmund cutaway 6 s | DI-05 survivor handoff and empty deck 8 s.
New footage: 68 s. Reused ads: 7 x ~6 s = 42.2 s. Full 7-product cut is about 110 s. A 3-product cut is about 62 s.
Survivor in DI-05 is the Modular Field Pack, a placeholder. Director can change it. Insult lines are spoken in the dialogue field; the captions are overlays only.
Audio: dry and quiet (boots, breath, voice), no music, no hum or sub-bass.

## Ads (used as-is): tagfade air copies, BA layout
Cloak #36 (lineage 4.11), Drone #34 (4.8), Helmet #30 (4.9), Pack #31 (4.7), Gauntlet #33 (4.6), Cruiser #32 (4.5), Binoculars #35 (4.10).
All 7 have audio_leveled=true, are listed in BEST-CLIPS, and appear in neither PULLED file. None come from the Lightning Lamp, Sky Diffuser or Drawbridge Puffs series.
Flag: these 7 carry the small "MB | thunder trundle" line that trundle allowed on these 7 at 6:27 PM. That conflicts with the brief's "no Military Boutique text" limit. Director and trundle need to choose: keep (OK per 6:27) or hold.
Flag: queue items ch4-q08..q14 already air the same 7 products (B_cover versions, #45-57). Running both repeats each ad twice per loop. Under the duplicate rule, both stay on file and rotate.

## Bookkeeping
Lineage 4.2 (marketing show, seeded by Clearance Brief), gen 1, original, no parent. global_no is left for CNB to assign (LINEAGE max is 70). Supersedes nothing: Color of the Day was only a pitch.
Slot: ch4-S5 (group boundary after comment clips, before the ad break). Alternative: ch4-S8. Each takedown's anchor_out is the clean first frame of its ad (hard cut). The shot after each ad gets anchor_in, the ad's clean last frame. The shots' own last frames get saved after render.

## Price (estimate, xAI)
Rate: run2 remakes, 15 shots / 130 s for $11.15 = $0.0858/s. Logged run2 grok-imagine-video-1.5 rows in spend.jsonl: $23.10 / 266 s = $0.0868/s.
68 s comes to $5.83 to $5.91, so call it about $5.90. That is about $0.53 per 6 s shot and $0.69 for the 8 s shot.
October xAI spend so far: $48.45 (spend.jsonl, xai_* providers). Remaining before this: $101.55 of the $150 cap. After it: about $95.65. The $120 warning line is not close.
