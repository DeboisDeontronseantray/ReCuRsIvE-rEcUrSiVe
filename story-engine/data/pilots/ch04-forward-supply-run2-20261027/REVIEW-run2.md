# Run 2 "Pocket Taupe" review (Story Bot, 2026-10-27 16:09 CT), NOT AIRED

Renders: run2/renders-480p-20261027_1547/ (CNB's run_all2.py was still running at 16:09 CT)
Rendered: 13/35. S1A 10.0s, S1B 8.0, S1C 8.0, S1D 8.0, S1E 8.0, S2A 10.0, S2B 8.0, S2C 8.0, S2D 8.0, S2E 6.0 (lite), S2F 8.0, S2G 6.0 (lite), S4D 6.0 (lite)
Missing so far: S3A-S3E, S4A-S4C, S5A-S5E, S6A-S6E, S7A-S7D (22 shots)
Assembled episode: none found.
Cost from log.jsonl (list-price estimate, 480p, not a billed figure): $7.66 for 13 clips.
Copies: S2E/S2G/S4D are also in shared/MEDIA-LIBRARY/videos and media-library/ch04-military-boutique/story-bot-pilot-run2 (the second has a doubled ".5-lite.5-lite" name).

## Frame check (one mid-clip frame per shot, judged at low resolution)
- Outpost set matches across shots: graphite and olive steel, cyan edge light, fog through the porthole, supply shelving.
- Osmund (olive coveralls, field pack) and Bill (black uniform, tinted glasses, big build) look the same from shot to shot. Mira (grey top, scarf, tablet) matches in S1C, S2A, S2C, S2D. Tim (the dome-headed unit) shows in S1A and S1D.
- Vape: no device and no vapor seen in any frame checked.
- Text: no legible text or logos seen. Screens and the HUD read as blank.
- S2F/S2G: the screen is blank and ready for the post insert. OK.
- Watch: S1A, Mira isn't clearly identifiable in the mid frame (there's a small green-lit figure at the left). Check the full clip.
- Watch: S2D, the "half the shelf emptied onto the floor in rows" beat isn't visible in the mid frame.
- Watch: S2E, the panel reads more like a window or screen with fog than a frosted Sky Diffuser.
- Watch: S4D, warm ceiling wash in the bunk room, but the diffuser panel leaning on a bunk isn't clearly visible and the light is more gold than "sickly ochre".
Limits: one frame per clip, no audio check.

## 2026-10-27 16:58 CT — Camera-rule remake flags (add-only, Story Bot)
trundle 4:51 PM CT: no one looks into or addresses the camera; fly-on-the-wall. Judged from 1 fps contact sheets in `frames/<ID>_sheet.jpg` (480p, faces small, so treat as a first pass). Remakes still need trundle's yes. No renders made.
| Shot | Confidence | Reason |
|---|---|---|
| S1D | High | Bill frontal, centered, eyes on lens through the clip |
| S1E | High | Bill seated frontal at desk staring out at lens, Tim behind |
| S2C | High | Mira centered, frontal, looking straight at camera |
| S3C | High | Osmund close-up in helmet, eyes to lens while adjusting liner |
| S5B | High | Bill frontal mid-shot facing lens (rage build reads as at viewer) |
| S5C | High | Bill frontal close, eruption aimed at camera (already on remake list) |
| S5D | High | Bill frontal at desk, eyes on lens |
| S6E | High | Osmund close frontal, looking at lens while Mira works behind |
| S1B | Medium | Osmund frontal over table; mostly eyes down, some frames up to lens |
| S2A | Medium | Osmund frontal among shelves, glances toward lens |
| S4C | Medium | Bill frontal at hatch, gaze near lens while Osmund kneels |
| S5A | Medium | Bill seated frontal, Mira/Osmund flanking; Bill eyes near lens |
| S2B | Low | Osmund behind helmet, face mostly hidden |
| S7A | Low | Group wide; Bill faces room, may pass lens |
Not flagged (eyelines on each other/task/off-frame): the rest, incl. S6D, S7C, S7D.
Template: `build_run2.py` now appends the OBSERVATIONAL RULE to every visual_prompt (backup .bak-20261027-1654); clip-prompts.json not regenerated.
