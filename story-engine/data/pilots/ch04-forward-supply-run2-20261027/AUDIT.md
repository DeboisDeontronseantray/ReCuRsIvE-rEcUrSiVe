# Run 2 self-audit vs bible-v2.yaml (2026-10-27 15:52 CT, Story Bot, local checks only)
- Locked looks: every cast shot embeds cast.<name>.locked_description verbatim from bible-v2 + still/turnaround refs (max 11/clip, ≤14). PASS
- Ref files exist on disk: 33/33 PASS. 1.5 used only with refs; lite only on 2 empty inserts (S2E, S4D). PASS
- Draft-1 quirks fixed: Bill sleeved + glasses lock in every Bill prompt + negatives; "only these, nobody else" + no extra people / no other uniformed women; Tim cargo clipped lock + negative; all text in post (ost_ lists), "no on-screen text" negative. PASS
- TV-safe: device unbranded, never lit/used, no vapor (negatives), word never in prompts/dialogue; eruption no swearing, audio in post; Motion Guard nobody touched, no lights. PASS
- No real brands / banned list: grep for brand names, American Hostage, flags, phone, dial in prompts and dialogue: 0 hits. PASS
- Continuity: fog never lifts, envelope stays unopened, motto + Mira catchphrase, Tim chirps only, Bill calm default with one rare eruption, Mira invents colors. PASS
- House ads: only at clean breaks after S2E and S4D. PASS
## Fixes made during audit
1. S4D: Sky Diffuser glow in bunk room had no source (panel was in the bay) → panel now carried in and leaning on a bunk (S4A + S4D).
2. Device kept out of frame in S1B (it is missing) and described generically everywhere.
## Notes / open
- Locked Mira text still says "co-host" (catalog-era wording inside a locked look); left untouched, harmless in prompts. trundle may re-word.
- New text items for on_screen_text registry before air: POCKET TAUPE, INSPECTION OCHRE, DAY ONE GREEN, REQUISITION DENIED slip.
- Runtime 270 s picture (~4:30) + ad breaks + cards ≈ 5–6 min; kept shorter to stay under the fal $40 warn line.

## Update 2026-10-27 15:48 CT (screen insert)
- Added S2F (1.5, Osmund+Bill, 6 refs) and S2G (lite, empty insert). Prompts describe only a blank softly glowing display; POST_INSERT: trundles-videos field set. Grep for game names in clip-prompts.json/.md and build_run2.py: 0 hits. PASS
- Shots 35, runtime 284 s, est. $23.46.
