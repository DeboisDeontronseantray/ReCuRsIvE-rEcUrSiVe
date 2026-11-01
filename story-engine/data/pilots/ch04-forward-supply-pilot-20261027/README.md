# ch04-forward-supply-pilot-20261027

First short pilot for **Forward Supply** (thunder trundle Channel 4 Military Boutique). Text only: no video, no spend, nothing sent. Written 2026-10-27 by Story Bot from the APPROVED Continuity Bible.

- `script.md`: title, beat sheet, full dialogue, house ad, ending
- `clip-prompts.json`: 21 clips (5–8 s each) for Commercial News Break, with visual prompt, era/camera tags, dialogue, first/last frame, continuity notes, negative prompt, post text, empty `reference_images`
- `gen.py`: script used to build the JSON (re-run: `python3 gen.py`)

**Title:** Cold Clearance · **Runtime:** 145 s (~2:25) · **Clips:** 21 · **House ad:** Make A Clip Remote (15 s)

## Bible rule checklist
- [x] TV-safe; no weapons, no gore, no actionable tactics
- [x] No slapstick: Tim's chirp and Osmund's wrong pack are played dry
- [x] Cast per Bible: Bill ("Let's ship it forward."), Mira ("Per the sticker, Commander."), Tim chirps only, Osmund ("Is this the priority brief?"), Voice of Forward unseen VO
- [x] Running gags: pedestal salute, invented color (Signal Mauve), signal-drift chirp, wrong pack that fits; side arc envelope seeded
- [x] Gear original, absurd but logical (Quietline Helmet, thermal pack with helmet cavity)
- [x] Respectful of the military; goofy and badass (hatch/launch sequence)
- [x] No real brands/companies/software; SparkNest/Thunderear/Clipforge only; no SpaceX segment
- [x] House ad from approved six, shown ready and working (dev stage disregarded), ad-safety limits kept
- [x] Parody label metadata only; not on screen
- [x] No dial, no phone CTA, no phone keypad; American Hostage absent; no KTVM
- [x] Inspiration notes not in any prompt (grep-checked)
- [x] No voice clones; reference slots empty
- [x] Channel number/name not in body (change-flash only); no "You're watching" clip (pilot < 30 min)
- [x] Clear ending, no rolling credits, motto card, then production card with invented studio "Quiet Hatch Pictures"
- [x] Intended text only via on_screen_text registry in post
- [x] Clip lengths 5–8 s (within Bible 5–15)

## Notes for trundle
- New text items need adding to the on_screen_text registry before air: "MAKE A CLIP REMOTE" super and "QUIET HATCH PICTURES" card. Bible not edited here.
- The Bible bans "keypad" visuals while the remote has keys. Prompts use "no phone-style keypad" and show ordinary remote keys.
- Mira's "Color of the day." belongs to Clearance Brief, so this pilot doesn't use it.
- Show length is 360 s; this is a deliberately short pilot (~2:25).
