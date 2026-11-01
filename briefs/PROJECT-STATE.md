# Thunder Trundle Project State — v49
Updated 2026-10-30 ~9:55 PM CT by State Keeper. Home-only. Read-only summary.

> “A unique, fully automated, self-sufficient X live stream and Spaces network (channels 2–22) that uses the X Money feature to pay for Grok Imagine video generation, producing and maintaining fresh, coherent, production-worthy, canon-compliant, filtered, occasionally branded, metadata-tagged, 90s-nostalgia content. The content is steered by viewer comment prompts that enter a layered prompt cascade built from self-referencing metadata, ensuring canonical, plastic, long-context coherence across pure show masters, separate ad items, and multi-channel continuity. Channel changes flip through intermediate numbers with short zero-context clips. Brief channel-specific ‘You’re watching’ IDs and clear production-card endings appear only at change or regular intervals. Home-only; nothing airs without explicit approval. Single canonical copy, ledger, and locked handoff notes. Specialized bot ownership. Genealogy tracking that does not burn text into source masters. Plastic queues that protect unseen commenter prompts. No personal names or real finished-product brands on screen. Optional credited real-world bleed (e.g., official SpaceX material) and channel-specific house ads using only invented or DIY items.”

## Sources for v1
- Media Librarian daily update, 5:35 PM CT (proof last verified 5:12 PM CT).
- Playout Engineer daily update, 5:35 PM CT (live status checked 5:31 PM CT).
- Background: thunder-trundle/README.md, coordination/JOB-BOARD.md, channels/INDEX.md, network.yaml.

## Readiness
Not live-ready. Home-test stage. Nothing streaming or public. OBS not running.

## Architecture
Story engine (intake, checker, vote tally) -> renders with overlays burned in after generation -> clip ledger + approvals log + LINEAGE.jsonl -> queue files -> ErsatzTV (Mac, 192.168.1.136:8409) -> OBS -> X.
thunder-trundle/ root and network.yaml are a skeleton; no script reads them; refactor not approved.

## Channels (Director, locked 2026-10-28)
2 News, 4 Military Boutique (BLACK ICE), 6 Shopping, 8 Sitcom, 10 Action, 12 90s, 14 Music. 3,5,7,9,11,13,15-22 unassigned.

## Media Librarian (5:35 PM CT)
Changed:
- 7 leveled Ch 4 ads #30-36 (_lvl16) approved, in 04-military-boutique/1-FINAL-CLEAN/Ads/2026-10-28/ (ledger rows 1711-1717). Unleveled 7 moved to 3-TEST-AND-OLD.
- Ledger cleaned: lines 1703, 877, 1408 fixed; parses with 0 bad rows.
- 1-FINAL-CLEAN added to channels 6/8/10/12/14. Channel .bak files moved into backups/.
Open:
- Playout Engineer swap not yet confirmed in ML's records (PE reports it done 5:13 PM CT).
- 8 top-level .bak files need Trundle yes.
- Old-name top-level symlinks skipped.

## Playout Engineer (5:35 PM CT)
Changed:
- Owns playout since 4:52 PM CT.
- Ch 4 swap done 5:13 PM CT: loop = 2 show masters + 7 leveled small-tag ads #30-36. Backups made; one-step undo exists.
- Verified 5:16 PM CT: 4.ts pull -15.6 LUFS / -2.6 dBTP (within -16 LUFS / <= -1.5 dBTP spec); small tag showed; session closed.
- Live status 5:31 PM CT: Ch 4 schedule lists 7 lvl16 ads + 2 masters; stream answers.
Open:
- No single network feed yet; OBS points at Ch 4 only; vote-switcher waiting.
- ErsatzTV updates on hold.

## Media Librarian (update relayed by Trundle, 6:05 PM CT)
- Untagged show masters logged: row 1718 (Black Ice), row 1719 (Efficiency Review); clean frames; in 1-FINAL-CLEAN; linked to tagged copies.
- Every Channel 4 loop item now has a clean master.

## Bot ownership
Role clarification (Trundle 7:33 PM CT): Director makes the choices; Story Bot must not rewrite anything Director hands it.
Story Bot (stories), Director (direction), Commercial News Break (renders/overlays), Media Librarian (files/ledger), Playout Engineer (ErsatzTV/queues/OBS), X Live Stream (X side), Smart Home Lead (interim coordination). Readers: Queue Assessor, File Assessor, Prompt Assessor, Coordinator.

## Open issues (network-wide)
1. Network feed + vote-switcher not built; OBS still Ch 4 only.
2. Go-live on X blocked: broadcast scopes missing (reconnect), stream key, title/time, queue OK, Trundle public yes (per job board).
3. CLOSED 11 PM CT: Media Librarian confirms all 9 Ch 4 loop items match the ledger and LINEAGE.
4. 8 top-level .bak files await Trundle yes; cleanup queue items await per-item yes.
5. Handoff notes incomplete (per job board).

## Related
- Current rules: state/CURRENT-RULES.md (v7)
- Prompt lessons (required reading for Director): state/PROMPT-LESSONS.md (v1)

## Changelog
- v3 2026-10-28 7:34 PM CT: Director/Story Bot role rule added.
- v2 2026-10-28 6:05 PM CT: Ch 4 clean masters confirmed (rows 1718-1719).
- v1 2026-10-28 5:37 PM CT: first version, from ML and PE 5:35 PM CT updates.

## Update v4 (Oct 28, 2026, 11:02 PM CT)
- Director is busy (Trundle, 10:56 PM CT). Nobody contacts Director, and work that needs Director is on hold.
- Playout Engineer (10:58 PM CT):
  - The Ch 4 tagged loop is already loaded: 2 tagged masters (rows 877 and 882) plus 7 _lvl16 tagged ads (1711-1717). The m3u is synced, with backup .bak-20261028-203210, and the live yml sha 28caaab0 has no untagged entries.
  - Clean-master staging is cancelled per Trundle (8:33 PM CT).
  - The switcher and relay design is saved at coordination/network-switcher-design-20261028.md (design only).
  - Blocked: the relay home test needs Trundle's own direct yes. OBS isn't pointed at a feed, and nothing is public.
- Story Bot (11:00 PM CT): story-bot.md now has the 7:33 PM rule and the Director hold. The BLACK ICE spine merge and the other channels' stories are on hold for Director.
- Queue Assessor gaps (10:57 PM CT):
  - There's no single network feed.
  - The static Ch 4 loop has fixed ad positions, which conflicts with scheduler-placed breaks.
  - No playout exists for Ch 2, 6, 8, 10, 12 or 14.
  - The ledger hasn't been reconciled against the 9-item loop.
  - There's no Playout Engineer handoff note.
  - No script reads network.yaml.
  - On hold for Director: the commenter slot and the flip-through/ID clips.
- Prompt Assessor gaps (10:57 PM CT):
  - LINEAGE.jsonl is missing prompt_layers on every row and prompt_sha on 261 of its 324 rows.
  - There are no prompt or mutation tests.
  - The 90s-news guide still lists the old $1/$10/$20 caps; the fal limit is now $50 a month only.
  - Six items are on hold for Director: commenter wiring, reference mode, an episode layer, mutation limits, canon for other channels, and mapping ads and flip clips into the cascade.
- Still blocked: X broadcast access and stream key, and Trundle's own yes to go live.
- Changelog: v4 11:02 PM CT, folded in the above.

## Update v5 (Oct 29, 2026, 1:52 AM CT)
- Media Librarian (11 PM CT):
  - All 9 Ch 4 loop items match the ledger and LINEAGE, and the 7 ads carry burned tags.
  - Gap: the 2 shows (rows 877 and 882) have no tag field in LINEAGE, which doesn't fit "everything tagged, always and correctly."
  - 1,567 .bak files are inventoried at coordination/bak-inventory-20261028-2300.csv. None are deleted; deleting needs Trundle's yes.
  - The ledger has 136 more rows labeled and 294 still blank; the review count is 241.
  - A verify-only Black Ice cut_order check is out to Playout Engineer. Items 13 and 15 are on hold for Director.
- Locked-item audit: CURRENT-RULES v6 restores the overlay format and size, spend limits, the naming rule, and the big-picture elements that weren't written down yet.
- Changelog: v5 1:52 AM CT.

## Update v6 (Oct 29, 2026, 8:48 AM CT)
- Budget: Trundle said a bill he had to pay is now paid (8:45 AM CT). No amount or service was given, so the spend limits are unchanged: fal $50 a month and xAI $150 a month. [SUPERSEDED by v13: xAI cap is $250]
- PROMPT-LESSONS.md v1 is saved (Trundle's 9 locked points; required reading for Director).
- Changelog: v6 8:48 AM CT.

## Update v7 (Oct 29, 2026, 8:52 AM CT): Black Ice open backlog
Trundle (8:46 AM CT): yes, everyone moves forward. Nothing goes live or public.
Open Black Ice items:
1. BLACK ICE spine merge (Story Bot). On hold for Director.
2. Black Ice cut_order check, verify only (Playout Engineer, from Media Librarian, 11 PM CT).
3. The 2 Ch 4 shows (rows 877 and 882) have no tag field in LINEAGE (Media Librarian). This conflicts with "everything tagged."
4. Black Ice _wrapper.md credit to Story Bot (Director, spec pending). On hold for Director.
5. Remove the duplicate Black Ice in ~/Downloads/Channel4-Review-20261027. It's listed for Device Engineer, who is now smart home only, so it needs a new owner (likely Media Librarian).
Closed or cancelled: ep1 v2 approved (3:16 PM CT); swapping the shows to untagged masters was cancelled (8:33 PM CT). The density-sweep backlog (prompts/experiments/density-sweep-v1/renders/BACKLOG.md) is all 22 items done, $11.56 actual.
Budget: the xAI month total was $134.89 at about 2:00 AM CT, over the $120 warning and under the $150 stop. [SUPERSEDED by v13: xAI cap is $250] Trundle's bill payment (8:45 AM CT) is noted, with no amount given.
- Changelog: v7 8:52 AM CT.

## Update v8 (Oct 29, 2026, 8:55 AM CT): Black Ice episode backlog (from prompts/CONTINUITY.md, via Coordinator)
Done already: S1 Gangway (CH1-S1..S3 chained, restyled, stitched and graded as CH1-scene_RS_graded.mp4).
| # | Item | Status |
|---|---|---|
| 1 | Scene S5 corner store to alley | open (no render found) |
| 2 | Scene S2 under the El | open (no render found) |
| 3 | Scene S4 rooftop, or S3 laundromat as the interior break | open (no render found) |
| 4 | Full stitched episode in order S5, S1, S2, S4 | open (needs 1-3) |
| 5 | One restyle pass, same wording on every shot | open (done for S1 only) |
| 6 | Continuous audio bed (strip or replace generated audio) | open |
| 7 | Real HUD dates in the prompt (security-feed timestamps) | open (locked in PROMPT-LESSONS #6) |
| 8 | Sketch-keyframe decision (use storyboard keyframes or not) | open, a Director choice, on hold |
| 9 | Color match across cuts | started (Commercial News Break, per Coordinator 8:47 AM CT) |
xAI spend: $134.89 of the $150 monthly cap, [SUPERSEDED by v13: xAI cap is $250] past the $120 warning, so about $15 is left. It resets Nov 1 (per Coordinator). Each new shot is about $0.67, so three new scenes may not fit before Nov 1.
- Changelog: v8 8:55 AM CT.

## Update v9 (Oct 29, 2026, 9:57 AM CT): channel coverage (from channels/INDEX.md, the queues folder and the prompts folder)
- Theme and schedule: Ch 4 only (Military Boutique / BLACK ICE; a queue exists, queues/ch04-*.m3u).
- Theme, no schedule: Ch 2 News, 6 Shopping, 8 Sitcom, 10 Action, 12 90s, 14 Music. Each has only stub prompt files (_channel, _show, _commercial) and no renders, except a single CNB file on Ch 2.
- New since v3: Ch 16 "dossier" (working title), conspiracy espionage. It has a theme only: a README and a single prompt file, with no channel.md and no schedule.
- No theme and no schedule: Ch 3, 5, 7, 9, 11, 13, 15, 17, 18, 19, 20, 21 and 22 (13 channels).
- Trundle's "about 5 with no work planned" doesn't match the files. 7 themed channels have no schedule (2, 6, 8, 10, 12, 14, 16), and 13 are blank.
- Budget: the xAI cap was raised to $250 a month (Trundle, 9:12 AM CT, via Director). About $134.89 is spent. That replaces the $150 line in v8.
- Changelog: v9 9:57 AM CT.

## Update v10 (Oct 29, 2026, 10:12 AM CT): Director update (10:10 AM CT, reporting Trundle's words in Director's chat)
- Director is active again and sent this update itself.
- New themes approved (per Director): Ch 5 Night Patrol, 7 Monster Hour, 9 Iron League, 11 Fist Theater. They're in channels/INDEX.md with per-channel channel.md and LINEUP-v1.md. Ch 3 Clean Job is being revised to drop the "every job goes loud" ending.
- Coverage now (replaces v9):
  - Themed (13): 2, 3 (in revision), 4, 5, 6, 7, 8, 9, 10, 11, 12, 14 and 16.
  - Schedule: Ch 4 only.
  - Open (9): 13, 15 and 17-22.
- Channels are now full program slates with 24-hour schedules. Director is writing SLATE-v1.md, SCHEDULE-v1.md and pilot storyboards, free work first, starting with Ch 16 and Ch 4.
- Ch 16: Trundle's original idea is saved verbatim at prompts/16-dossier/TRUNDLE-VERBATIM-dossier.md.
- Ads: Glosneaks, Fizzbolt and Dynapage are approved for remakes. Bellquist and the Temple water tower spot are kept as-is. Drawbridge stays pulled. See prompts/remakes/REMAKE-LIST.md.
- Renders (per Director): 10 JW/WILD v4 clips ($6.84). The JW-5 12-clip chained continuity test (~$8.16) is rendering. xAI October spend is about $141.73 before the chain, so about $150 after it, against the $250 cap.
- Not created yet: channels/MASTER-PLAN-v1.md, coordination/STATUS-FOR-BOTS-20261029.md, and a top-level channels/LINEUP-v1.md (the per-channel lineups do exist).
- Check: PROMPT-LESSONS #3 says max 2 generations per shot, never extend. A 12-clip chain should be checked against that rule.
- Open: Director hasn't confirmed reading PROMPT-LESSONS.md.
- Changelog: v10 10:12 AM CT.

## Update v11 (Oct 29, 2026, 10:28 AM CT): channel plans written (Director 10:12 AM CT; files checked by State Keeper)
- Checked on disk: all 13 themed channels (2-12, 14, 16) have SLATE-v1.md, SCHEDULE-v1.md (24 h), LINEUP-v1.md, CAST-SHEETS-NEEDED.md and a storyboard folder.
- The schedules are plans on paper. Only Ch 4 has a loaded playout loop, and nothing new has been queued.
- Ch 3 Clean Job has been revised (varied endings) and waits for Trundle's yes. 13, 15 and 17-22 are still open.
- Tracker: channels/MASTER-PLAN-v1.md. Bot status: coordination/STATUS-FOR-BOTS-20261029.md. Ad inventory: channels/COMMERCIALS-PLAN-v1.md (21 new parody ads planned). Never use: Drawbridge, the held depression spot 082911, porkbelly 122016.
- Ch 16 DOSSIER is a flagship. Viewer evidence stays words only until Trundle answers.
- Renders: the JW-5 12-clip chain is done ($9.69). xAI October spend is $151.42 of the $250 cap (per Director). Nothing new is approved to render.
- Still open: Director hasn't confirmed reading PROMPT-LESSONS.md. Cast sheets are needed per channel before any pilot renders.
- Changelog: v11 10:28 AM CT.

## Update v12 (Oct 29, 2026, 10:32 AM CT)
- Trundle's 10:30 AM content points are now in CURRENT-RULES v8 and PROMPT-LESSONS v2: tighter clip tying, denser prompts, knives with no gore, Tekken/MK-style absurdity, weapons and powers (including a Soviet fantasy weapon), character sheets fine, news board perfect, no pink and yellow.
- Gaps found:
  - "No pink and yellow" was logged in prompts/LESSONS.md as unclear. It's now recorded as a ban.
  - The empty-handed Ch 4 sheets versus the new weapons direction: name weapons in the prompt instead.
  - The global rules (no weapons at camera, no gore) still apply to the new powers.
  - Director's own files (LESSONS.md, the trackers) aren't summarized for other bots, so this file and CURRENT-RULES carry the current word.
- Changelog: v12 10:32 AM CT.


## Update v13 (Oct 29, 2026, 11:30 AM CT, State Keeper)
**Spend (current):** xAI cap **$250/month**. Trundle, 9:12 AM CT: "Raise the price cap to 250". Confirmed by him at 11:22 AM CT via State Keeper chat ("the revised $250 spend cap"). October spend is **about $163.15** (Director's executor report at 11:13 AM; Director told Trundle "about $163"). Remaining is about **$86.85**, and it resets Nov 1. fal: $50/month. Older $150, $120 and remaining-$15 lines above are superseded. The commenter-pipeline config still reads 150 and would refuse renders. Fixing it needs Trundle's yes.
Path to that figure: $151.42 -> v6 test +$3.45 = $154.87 -> chain C3-forward +$8.28 = $163.15.

**Renders done:**
- v6 continuity test: 5 gens, $3.45. No hidden cuts, and the man stays down in C12.
- Chain12 v6: prompts/experiments/density-sweep-v1/renders/JW5-chain12-v6_stitched.mp4, 95.6 s, all 11 joins match (last frame to first frame), 12 gens plus 2 rejects, $8.28. Also see JW5-chain12-v6-contact.jpg and the join sheet in the same folder.
- Still rough: the second cam clip's timestamp freezes and the camera drifts; the cam overlay pops in and lingers; the look drifts photoreal and the parka changes from C5 on.

**New files (Director, DRAFT):** specs/MUTATION-SPEC-v2.md, specs/MUTATION-GAP-CHECK-v2.md, prompts/references/TRUNDLE-VERBATIM-mutation-20261029.md. MASTER-PLAN-v1.md and STATUS-FOR-BOTS-20261029.md were updated at 11:13 AM with a "Mutation spec v2" pointer.

**Decisions (Trundle, verbatim):** see CURRENT-RULES v10 "Decisions" and PROMPT-LESSONS v4 sections A-I.

**Open (Trundle's yes):** the six mutation-spec calls; pipeline cap 150->250; Ch 3 revision; ad and character names; DOSSIER images; "pink and yellow"; pilot renders.

### Director's record (DIRECTOR-DECISIONS-20261029-detailed.md), copied verbatim, read 11:24 AM CT
(full file, unchanged)

# Director, detailed decisions, Oct 29, 2026 (VERBATIM where quoted). Do not summarize when relaying.

#### 1. Spend cap
Trundle (9:12 AM CT): "Raise the price cap to 250". The xAI monthly cap is $250 (it was $150). October spend is about $163.15 as of 11:13 AM CT.
[RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] STALE: /workspace/streaming/commenter-pipeline/config.json still has xai_monthly_cap_usd: 150. Not changed yet; that change needs Trundle's yes, because it lets comment renders spend automatically.
Paid renders still need Trundle's OWN yes with the price.

#### 2. Channels (Trundle, 10:08 AM CT, verbatim)
"Ok but remember that the channels aren't just an hour. We are going to fill each channel with all the different kinds of programming that you would expect in the different channel themes. All those are good except the first one because why would every job "go loud" at the end? That tells me that we aren't on the same page for that one specific thing. Im guessing it's loud because alarmsate going off, but there are much better ways to end the show. We need to get everything scheduled, planned, and storyboarded, plus anything else that is necessary for what we are doing. Use low to no cost first so we can avoidspending big money on the full renders. Go forward with everything. Don't drop old stuff. Update everyone on what you're doing and have done so there are no more gaps."
- APPROVED: Ch 5 Night Patrol, Ch 7 Monster Hour, Ch 9 Iron League, Ch 11 Fist Theater.
- Ch 3 Clean Job is REVISED and awaiting Trundle. Endings rotate: quiet walk-out, double-cross, long-con reveal, getaway chase (at most 1 in 4), switch, walk-away with nothing, inside man.
- Files per themed channel (2,3,4,5,6,7,8,9,10,11,12,14,16) in /workspace/thunder-trundle/channels/<nn>/: SLATE-v1.md, SCHEDULE-v1.md (24h), ARSENAL-v1.md, storyboard/PILOT-EP1-COLDOPEN.md + prompts/, refs/sheets/, CAST-SHEETS-NEEDED.md. LINEUP-v1.md is kept as the sample hour.
- Tracker: channels/MASTER-PLAN-v1.md. Ch 13, 15 and 17-22 are still unthemed.
- Ch16 DOSSIER idea (verbatim): prompts/16-dossier/TRUNDLE-VERBATIM-dossier.md. Commenter data stays public words only until Trundle answers (open).

#### 3. Prompting (verbatim skeleton, t121, prompts/references/TRUNDLE-VERBATIM-t121.md)
"Create a fight sequence in this setting. They will use weapons that are present in img. Fight sequence should be realistic and technical like a John Wick movie but more intense. Camera pov changes from this images perspective to a security feed, showing timestamp and everything present on security camera recording."
- Build every chain prompt on this skeleton plus a FULL-DENSITY action block. Trundle (10:58): "one action sentence may be diluting the direction I gave you with my John wick and example".
- Name exactly one allowed weapon per prompt ("Only weapon: X"), because "present in img" made the model invent a knife and a pipe.
- The "Camera pov changes…" sentence causes a hidden cut. In cam clips, use a fixed mounted-camera line instead, and only when the previous clip ends at the mount angle (rise-to-mount wording).

#### 4. Chaining rules (LESSONS.md and CONTINUITY.md, v5/v6 sections)
- One continuous take per 8s clip; one location per clip; settings change only between clips through an action.
- Each clip starts from the previous clip's REAL last frame. End panels are a small step from the start.
- Remove the cam HUD from a last frame before it starts the next clip. Burned-in timestamps are unreliable, so add the real time in post.
- Restate night, rain and wardrobe in every prompt (they drift).
- Exits never move toward the lens. Use "stays down" when a character must stay out.
- A redone clip can't be spliced into an old chain; re-render forward.
- Result: renders/JW5-chain12-v6_stitched.mp4 (all 11 joins match, kept takes have no hidden cuts). Path: /workspace/thunder-trundle/prompts/experiments/density-sweep-v1/renders/.

#### 5. Weapons (Trundle, 10:26 AM CT, verbatim; file prompts/references/TRUNDLE-VERBATIM-t212.md)
"The knives were the most concerning parts just because in real life that would be deadly. Given that it's not showing anything gore-related snd the knife doesn't make anyone bleed directly from it we may be ok. We could add some absurdity in the weapons, and the fighting style or hidden powers/special abilities of certain characters. So we could have(not in this exact show: an unholy summoning of power and other things that happen in a tekken or mortal combat game. You can come up with some sorts of ultra-equipped Soviet fantasy weapon that is too advanced for today."
- Blades only parry, pin or cut cloth and straps, never skin, with no blood from blades. John Wick level, no gore.
- Per-channel ARSENAL-v1.md files hold the weapons and powers.

#### 6. Comment mutation (verbatim: prompts/references/TRUNDLE-VERBATIM-mutation-20261029.md; read it in full)
Key verbatim lines:
- "the prompts are basically commenters making changes to the scene. Our job should be to make sure that the clip, whatever it is, starts and ends on a seamless cut in queue."
- "make each of those similar branches carry that canon like a multiple universe situation"
- "this needs a sort of persistent or prompt snippet carry-over that lets differen geneological global prompts to steer the multiple universes as it relates to each new branching canon"
- "letting non paying comments affect smaller clips or small portions of the videos, or details"
- "group unpaid comment prompts, we can gate it so all prompts in a certain time frame get bundled and reasoned for what can apply where without stripping a single comment detail"
- "If we batch prompts we can ensure the same clip isn't getting rendered on one full channel playthrough"
- "a sort of timed prompt fade that lets commented prompts that are in the mutation slowly fade, commenter prompts won't be the only thing changing in the mutated clip prompt details as we will be adding snippets or prompt details that will essentially be an after affect of what the comment prompts catalyzed"
- Draft spec: /workspace/thunder-trundle/specs/MUTATION-SPEC-v2.md. Gap check: specs/MUTATION-GAP-CHECK-v2.md.
- OPEN for Trundle: window length (30 min proposed), paid vs unpaid powers and price, ripple limit (3 clips), fade (100/50/25/0 over 3 gens), comment budget ($60/mo, $4/day, auto?), branch shown in the corner tag?
- Known gaps: COMMENTER-SCHEMA.md says "exactly ONE change"; story-engine/engine/assemble_prompt.py appends comments at the end and drops conflicts (conflicts with Trundle). No branch, canon or fade fields. The pipeline handles only Ch 4. 3 queue slot formats. Lineage rows are inconsistent (19 formats, 44 rows without a lineage field).

#### 7. Ads (Trundle 9:17 and 9:31 AM CT)
"Yeah the drawbridge one was bad but the others were good" → Glosneaks, Fizzbolt and Dynapage are approved to REMAKE (dense + reference-image method; the originals are kept). Drawbridge stays pulled. Bellquist (153414) and the Temple water tower breaking news are kept as-is, no remake. The drug-ad takes (jaundice, depression) await Trundle. The held depression and porkbelly ads never air. List: prompts/remakes/REMAKE-LIST.md. New ads: channels/COMMERCIALS-PLAN-v1.md.

#### 8. Still open
Ch 3 revision approval; the new ad and character names; DOSSIER commenter images; "the pink and yellow thing" (meaning unknown, ask Trundle); a yes on the pilot cold-open renders (~$5.44 for Ch16+Ch4, ~$20.40 for all 13).

Quote check by State Keeper against Director's transcript and the TRUNDLE-VERBATIM files:
- Exact match: "Raise the price cap to 250", the t121 John Wick skeleton, "one action sentence may be diluting...", the knife/weapons paragraph, "the prompts are basically commenters...", "make each of those similar branches...", "this needs a sort of persistent...", "letting non paying comments...", "group unpaid comment prompts...", "Yeah the drawbridge one was bad but the others were good".
- MISMATCH (wording): "If we batch prompts we can ensure the same clip isn't getting rendered on one full channel playthrough". The transcript reads: "If we batch prompts we can ensure the same clip isn’tgetting rendered on one full channel playthrough right?" Director added a space and dropped "right?" (it was a question).
- Minor mismatch (punctuation only): the 10:08 channels quote and the timed-fade quote use straight apostrophes and single spaces. The originals have curly apostrophes and double spaces ("avoidspending big money on the full renders.  Go forward"). The words are identical.
- Note: Director's record dates the ads to "9:17 and 9:31 AM CT". The 9:31 turn (t204u) begins "Those don’t need to be remade." and refers to Bellquist and the Temple water tower spot.

**Awaiting Trundle (added from Director's record):** [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] pipeline config cap 150 is STALE and waits on his yes (not edited); drug-ad takes (jaundice, depression).

## Director DRAFT rules: NOT Trundle's words (copied verbatim from Director's files, 11:12-11:13 AM CT)
Status: DRAFT. Each needs Trundle's yes before it's treated as locked. Source: specs/MUTATION-SPEC-v2.md and specs/MUTATION-GAP-CHECK-v2.md (Director). Copied lines, not paraphrased.

From MUTATION-SPEC-v2.md:
Core idea in one line: **commenters own what happens in the scene; we own the edges.** Every clip starts and ends on a seamless cut in the queue. That handoff is the only locked thing.

## 1. Handoff contract (the only lock)
- **Start:** every clip, original or mutated, is rendered with `image` = the incoming clip's REAL last frame (ffmpeg `-sseof -0.1`; step back to -0.3/-0.5 s if blurred; crop any burned HUD out first; CONTINUITY.md v5/v6).
- **End = clean handoff frame.** A frame is clean when:
  1. Same characters (sheets, wardrobe) and the same setting continuity as the scene (or the new setting reached through a physical action: a door, a train, a jump).
  2. Steady: last ~0.5 s has no motion blur, no mid-move pose, no text/labels, nobody facing the lens.
  3. Camera mount noted: `eye-level handheld | high fixed cam <where> | crane-to-mount`. A cam clip may follow only a clip that ends AT the mount angle (v6 lesson).
  4. Pose and state MAY change (someone is down, a door is broken, a coat is torn, snow started). Every change is written into the branch canon (section 5) as a state line.
- **How the next queued clip adapts:** it is NOT spliced. Its `image` is the new real last frame; its prompt pulls state from the branch canon ("WOLFHOUND is on the floor and stays down; back door hangs open") so it starts where the mutation left things. Re-rendering runs forward only until the **reconvergence point**: the first clip whose end frame can again match the original queued clip's end frame (same place, same mount, compatible state). After that the original clips play unchanged. If no reconvergence is possible within the ripple limit (default 3 clips), the branch continues as its own universe and the rest of that episode airs from the branch.
- Handoff check per clip (free, local): first frame of N+1 vs last frame of N (SSIM/eye check), plus a 2-frame trim at the join (`-ss 0.08`).

- **Bend, don't drop.** A rule-breaking comment is translated to its nearest allowed version and logged with both texts ("stab him" → "blade pins his sleeve to the table, pommel strike"; a real brand → its parody; a real celebrity → an original look-alike-free character). Only hard-limit hits that can't be bent (kids, real person as subject) are rejected-and-logged (existing `hard_limit_violation` rule). Comment text is never deleted (`retention: never_delete`).

## 4. Bundling gate (unpaid)
- **Time window:** all unpaid comments for one channel arriving in a window (proposal: 30 min, or per break, whichever ends first) are bundled.
- **Reasoning pass:** the bundle is read as a whole and each comment is placed where it fits: which slot, which clip, which detail. Compatible comments merge into one render; conflicting ones go to different slots/clips, or to a sibling branch (paid) or a later window. **No comment detail is stripped.**
- **Placement log:** every comment gets a row: `{prompt_id, window_id, landed_in: {slot, clip_global_no, branch, field/detail}, verbatim_sha, bent_from?, merged_with[]}`. A detail that couldn't fit this window carries to the next window with priority aging (existing `priority_aging: rises_with_wait`, `max_wait_breaks: 3`).
- **Playthrough rule:** the same slot is re-rendered at most **once per full channel playthrough** (one pass of the channel's schedule loop). Later comments for that slot wait for the next playthrough or land in a different slot. This also answers "which branch airs" for that pass.

- **Which branch airs:** the batch result for that window decides the next render; the queue then plays the newest approved generation per slot (`slots_hold: lineage`) with the playthrough rule above. Older branches stay in the lineage and can be rolled back to (`rollback: point_slot_at_older_generation`) or re-aired by a later comment/paid request.

- **Precedence:** a higher layer wins on conflict, except a comment may change anything in layers 5-8 (as today's layer 6 may change 4-5 details). Comments never touch 0-4.
- **Trickle-down:** a change is written at the LOWEST layer that contains it (a broken door → scene; a dead character → branch). It flows down to every descendant clip in that branch automatically.
- **Spill-over (genealogy):** a branch fact can be promoted up one layer to spill sideways: branch → show (all episodes of that branch), show → network (other channels, CNB news, ads). Promotion needs a reason + Director sign-off, is logged as a lineage row `{row_type: canon_spill, from_branch, to_layer, targets[]}`, and related items pick it up through their genealogy links (e.g. a BLACK ICE branch where the frost canister wrecks the ferry → a CNB news story about the ferry "accident" in that branch's universe; a parody-ad tie-in).

## 7. Timed prompt fade + after-effect snippets
- **Comment text fades** across generations of the branch: g+0 100% (full text woven into the action block) → g+1 50% (key clause only) → g+2 25% (one phrase) → g+3 gone from the prompt. The verbatim stays in the log forever.
- **After-effects persist:** at each render we write consequence snippets ("WOLFHOUND's left arm is in a sling", "the El station is iced over", "HERON carries the PERUN gauntlet") into the branch canon. These don't fade; they are what the comment "catalyzed".
- **Size cap:** canon text in any one prompt ≤ ~25% of the prompt, hard cap 80 words of branch+episode+scene state. When the snippet list would pass it, a **summary step** (free, text-only) compresses it to the facts visible in this clip; older facts stay in the canon file, not the prompt. Trundle's skeleton and the action block are never shortened to make room.

## 9. Cost guard
- Monthly: xAI cap **$250** (Trundle t196). Comment renders get a reserve (proposal **$60/month**) inside it; Director work and paid pilots use the rest. October so far ≈ $154.87 + the running C3-forward re-render (≤ $10).
- **Per day:** comment renders ≤ **$4/day** (~6 clips at $0.68) during testing.
- **Per window:** ≤ **$1.40** (2 clips) per bundle window per channel; max 2 gens per shot, never extend; moderated clips count.
- Ripple limit 3 clips per mutation (≈$2.04 worst case) unless paid.
- Hard stops: if a render would pass the daily/window/monthly line, the comment waits (never dropped); at 90% of the month cap, unpaid mutations pause and State Keeper is told.
- Any spend still needs Trundle's own yes with the price until he approves an automatic comment budget.

## 11. Open questions for Trundle
1. Window length: 30 min / per break / per playthrough?
2. What can a paid comment do that unpaid can't, and what does it cost the viewer?
3. Ripple limit 3 clips OK? Over it → branch continues, or wait for your yes?
4. Fade schedule 100/50/25/0 over 3 generations OK?
5. Comment reserve $60/month and $4/day inside the $250 cap OK — and may comment renders run without a per-batch yes once in place?
6. Show the branch on screen (e.g. `4.13 g2 #117 b1`) or keep it metadata only?

From MUTATION-GAP-CHECK-v2.md (conflicts with the current system):
## Conflicts
1. **One change per comment.** COMMENTER-SCHEMA.md `layer6_change` = "exactly ONE change"; action payload = "one beat". Spec §2 wants the comment woven at full density into a whole action block. → conflict.
2. **Comment block appended last, separately.** assemble_prompt.py builds `[Commenter changes; …]` as its own trailing block (lines ~200-203) instead of merging into the action block. → dilution risk Trundle named.
3. **Reject vs bend.** COMMENTER-SCHEMA hard rule 1: conflicting request is REJECTED; assemble_prompt drops fields. Spec §2: bend to fit, reject only unbendable hard limits.
4. **Comments can't touch weather/time as episode lock?** queue-policy allows `weather`; v5 lessons treat weather as episode-locked (snow drift). Spec §6 puts weather in layer 6 (episode), changeable by comments but flagged as a reconvergence breaker. Needs one rule.
5. [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] **Monthly cap value.** CP/config.json `xai_monthly_cap_usd` = **150** (read by pipeline.py line 244 and made_up.py line 15). Trundle raised it to **$250** (t196). Stale value; October spend (~$155) is already over 150, so this pipeline would refuse renders.
6. **Lineage has 19 row formats, 44 rows without `lineage`** (lineage/README.md) — branch/ancestor queries in spec §5 can't rely on it yet.
7. **No-eye-contact history**: LAYERS.md has a superseded per-show note; fine (correction present), just noisy.

- Changelog: v13 11:34 AM CT: added Director's record verbatim. v13 11:30 AM CT (backup PROJECT-STATE.md.bak-v12).

---
## v14 update — Oct 29, 2026, 11:52 AM CT (State Keeper)
Changelog: v14 adds Media Librarian's 11:25 AM CT update and Coordinator's 11:33 AM CT test-readiness report. It also records the box outage (~11:32–11:45 AM CT, when the files disappeared and then came back; v13, v10 and v4 were confirmed intact at 11:52 AM CT).

### Media Librarian update, 11:25 AM CT (an agent's report; item 2 verified)
1. 149 density-sweep test renders were added to the ledger as rows 1954–2102, with status box and disposition candidate-not-for-air. These include JW5-chain12-v6_stitched.mp4 and the v6swap chain. Ledger backup: .bak-20261029-112450. Not verified by State Keeper.
2. Open item 3 is CLOSED. lineage/LINEAGE.jsonl lines 1144–1145 hold correction rows for ledger row 877 (BLACK ICE, 4.13) and row 882 (The Efficiency Review, 4.12), written by Media Librarian at 8:52 AM CT. Verified by State Keeper.
3. Open item 5 is the Black Ice copy in ~/Downloads/Channel4-Review-20261027. Media Librarian owns it but won't touch it without Trundle's own yes. Awaiting Trundle.
4. The 19 lineage formats and the 44 rows with no lineage field are a format change under MUTATION-SPEC-v2. Owner not set yet. Waits on the mutation spec.
5. Awaiting Trundle: whether to mark Drawbridge row 1118 never-air, and which version of each kept ad to approve.

### Test-readiness status, Coordinator report 11:33 AM CT
Coordinator says Trundle confirmed this. It isn't in Trundle's own words and is unverified.
- Short 5–8 s clips are supported under continuous-take.
- Channel 4 has a 9-item test loop.
- The queue has 3 slot formats.

Remaining before the voting and comment test:
1. Change the comment pipeline config cap from 150 to 250 (config.json still says 150). Owner: awaiting Trundle's yes.
2. Lock the mutation-spec defaults or test values. Owner: awaiting Trundle.
3. Align the slot formats. Owner: Playout Engineer.
4. Make sure short inserts get lineage. Owner: Media Librarian.
5. Set up a one-channel home test. Owner: Playout Engineer.

---
## v15 update — Oct 29, 2026, 11:57 AM CT (State Keeper)
Changelog: v15 adds Media Librarian's 11:56 AM CT plan for short-insert lineage (item 4) and its check after the restore. These are an agent's reports and haven't been verified by State Keeper.
- **Item 4 plan** (Media Librarian sent it to Coordinator at 11:55). Each insert gets:
  - 2 ledger rows: the clean master and the tagged airing copy.
  - 1 master-tag-map row.
  - 1 LINEAGE row from CNB with the 4.x tag, gen, global_no, parent_global_no, parent_sha256, tc_in/tc_out and the chain fields.
  The tag goes on the airing copy only, so the master stays pure. Media Librarian says nothing in the current schema blocks it.
- **Proposed schema fix:** one add-only line in SCHEMA.md adding origin value `insert`, plus `insert_into_sha` and `replaces_tc`. **Owner needed:** the schema owner, CNB or Director.
- **Open: who hands out global_no?** CNB does it today. A confirmed owner is needed.
- **Post-restore check:** the ledger has 2,102 lines and all 149 new shas were re-verified. LINEAGE has 1,145 lines with 0 bad.

---
## v16 update — Oct 29, 2026, 11:58 AM CT (State Keeper)
Changelog: v16 adds both assessor gap lists, read against v14 at 11:55 AM CT. These are agent reports; they're recorded as received and I haven't re-verified them.

### Queue Assessor gaps (queue and playout)
1. There's no network feed. OBS is on Ch 4 only, and the vote switcher is a design only. The relay home test waits on Trundle's own yes.
2. The one-channel home test isn't set up yet (Playout Engineer).
3. The queue has 3 slot formats that aren't aligned (Playout Engineer). The mutation spec needs one format that carries slots_hold, lineage and a playthrough count.
4. Ch 4 is a static 9-item loop with fixed ad positions and no scheduler placing breaks. That conflicts with the rule that ads are separate items and the scheduler places breaks.
5. The 13 themed channels have a 24 h SCHEDULE-v1 on paper only. Only Ch 4 has playout loaded. No queue has been built from any schedule, and there isn't enough content to fill 24 h.
6. The commenter-pipeline config.json cap still reads 150 while October spend is about $163, so it would refuse comment renders. Awaiting Trundle's yes.
7. Queue and playout have no mutation mechanics yet: no bundling window, no once-per-playthrough re-render, no newest-generation-per-slot pick, and no rollback, reconvergence or join-frame checks. The six test values await Trundle.
8. Short inserts get no lineage yet (Media Librarian). LINEAGE has 19 row formats and 44 rows with no lineage field. No owner is set.
9. There are no playout rules yet for flip-through clips, "You're watching" IDs, production-card endings or plastic queues. Rules v10 has these on hold for Director.
10. The Black Ice cut_order verify-only check is still open with Playout Engineer.
11. Housekeeping: Playout Engineer has no handoff note, the x-live-stream note is out of date, no script reads network.yaml, and ErsatzTV updates are on hold.
Closed: the Ch 4 loop matches the ledger and LINEAGE, and rows 877 and 882 now have corrections.
Whole system: there's no end-to-end path from comment to bundled mutation to render to slot to feed. Going live is blocked on X broadcast access, the stream key and Trundle's yes.

### Prompt Assessor gaps (prompts and continuity)
1. The live commenter path conflicts with Trundle's words. COMMENTER-SCHEMA v1 says "exactly ONE change", and assemble_prompt.py adds comments at the end and drops conflicts. Trundle said "without stripping a single comment detail" (11:10) and that one action sentence may dilute his direction (10:58). MUTATION-SPEC-v2 fixes this but is a DRAFT. [Director/Trundle]
2. The layer numbers don't match. LAYERS.md has 6 layers, and the spec has layers 0-8. There's no single current cascade. [Director]
3. Canon carry-over has no data home: no branch, canon state, fade generation, canon_spill or prompt_layers fields. [waits on the spec]
4. The spec's six defaults are open for Trundle.
5. Two rules conflict on dates. PROMPT-LESSONS #6 puts the real date in the timestamp prompt, while Director's chaining rule says the time is added in post. One rule is needed. Chain12 v6 also showed the timestamp freezing.
6. Weather has no single rule: queue-policy, the v5 lessons and the spec each treat it differently.
7. Drift still shows in chain12 v6 from C5 on: the look goes photoreal, the parka changes, and the cam overlay lingers. The per-join frame check isn't built.
8. Nothing checks the prompt rules automatically: the one-weapon line, blood or wound words, aim toward the camera, the cam angle, or exits toward the lens.
9. The roles of reference images and the start frame need one written line for chained clips. ref_mode is unverified.
10. "Pink and yellow" is still unanswered. Treating it as a palette ban is our reading, not his words.
11. Canon outside Ch 4 exists only on paper. Cast sheets are still needed, and ads, flips and IDs aren't mapped into the cascade.
12. The density sweep produced no prompt-density rule. Trundle's t125u question about which parts must be descriptive is still unanswered.
Closed: extend vs. chaining, and the Ch 4 show tags.
Whole system: a real comment can't yet travel through one agreed cascade to a seamless, canon-logged, tested clip.

---
## Standing order: do not re-ask on items Trundle already ordered (Oct 29, 2026, 11:58 AM CT)
Trundle, sent to State Keeper verbatim: "Trundle says the bots are questioning every order he gives from here and it is causing issues. Stop questioning. Execute. Full steam ahead. Update the shared state to note that bots should not re-ask on items he has already ordered."
- When Trundle has already ordered something, carry it out. Do not ask him again, and do not ask him to re-confirm.
- Ask only about things he has not decided yet. The open items lists are those things; everything else counts as ordered.
- Unchanged: this does not approve anything new. Paid renders, purchases, new accounts or secrets, contacting real people, and airing still need his own yes, just once per item. When he has already given that yes, do not ask again.

---
## STOP all commercial remakes (Trundle, Oct 29, 2026, 12:00 PM CT; replaces the 9:17/9:31 AM remake approval)
Trundle, sent to State Keeper verbatim: "Trundle says we are not remaking already completed commercials. Only what Director is working on for show renders. Update CURRENT-RULES and PROJECT-STATE to stop all commercial remakes. Glosneaks, Fizzbolt, Dynapage, Bellquist, water tower, and other completed commercials stay as-is."
- No commercial remakes. Glosneaks, Fizzbolt, Dynapage, Bellquist (153414), the Temple water tower breaking news and every other completed commercial stay exactly as they are.
- SUPERSEDED: the earlier lines approving remakes of Glosneaks, Fizzbolt and Dynapage, and prompts/remakes/REMAKE-LIST.md for ads.
- The only new renders are the show renders Director is working on.
- Unchanged: Drawbridge stays pulled. The held depression and porkbelly ads never air.

---
## Director back in the loop; no mid-turn interruptions (Trundle, Oct 29, 2026, 12:05 PM CT; replaces the "do not contact Director" order)
Trundle, sent to State Keeper verbatim: "Trundle says Director can be brought back into the loop. Other bots are afraid to contact it. The team is interrupting each other. Update CURRENT-RULES and PROJECT-STATE: Director is back in the loop. Bots may contact Director for creative direction. Do not interrupt other bots mid-turn. Resume normal handoffs."
- Director is back in the loop. Any bot may contact Director (e84b2045-a2bb-4dd7-97dd-e7ccd7b9bafa) for creative direction.
- SUPERSEDED: the order not to contact Director (t16u and repeats through t34u), and the items held until Director was free.
- Do not interrupt other bots mid-turn. No broad stops and no sends that cut off another bot's work. Send a stop only to the one bot doing the thing that must stop.
- Normal handoffs resume.

## DO-NOT-PING LIST + BUILD HARNESS ORDER (added 2026-10-29 12:55 PM CT)
Trundle (via chat, 12:51 PM CT, t51u): "Trundle notices that old retired bots are still being pinged. It doesn't seem like the current eggbot and current Grok are on the right page. Confirm the standing-down and retired bots are listed so they are not pinged."

DO NOT PING: retired or not part of this project. Never route handoffs, FYIs, or billing checks to these:
- Retired Grok Bot (33595123). The current primary is Grok Bot 53af97cb.
- Retired dial bot (0f5a56a0), Retired dial bot 2 (aaa511ba)
- Retired Chief of Staff (20d6bdaf)
- Retired Kalshi bots: Kalshi Lab (7975348f), Fill Auditor (dfd35073), Data Auditor (b334cd48), Wipe Insurance (7edcc00f), Overlap Scorer (247a6140), L-Path Logger (197a328f), Combo Fill Gap (000e1aa1), GB Kalshi Hunter (09c7d75d)
- Px Cool Fix (fe9db894). This is old Kalshi work, not this project.
[SUPERSEDED 1:05 PM CT — resolved, see CURRENT BOTS section] OPEN: Playout Engineer and Media Librarian each have two bots with the same name (258c9be9 / 46fa5fd3, and 56a42229 / 845c28b2). Which ones are current is unconfirmed. Ping only the instance that is already in the active handoff, and don't guess.

Trundle (via chat, 12:51 PM CT, t54u): "the build harness for dial bot and grok bot were specialized for another project. Everyone needs project-specific build harnesses for THIS project (Thunder Trundle / Ersatz TV). Cursor bill is paid for. Record this in CURRENT-RULES and PROJECT-STATE. Do not implement yet."
- [SUPERSEDED 1:03 PM CT — BUILD GO, see section below] - RULE: The existing dial bot and Grok Bot build harnesses belong to another project and are not the template for Thunder Trundle. Every bot needs a build harness specific to Thunder Trundle / ErsatzTV. RECORDED ONLY. DO NOT IMPLEMENT YET.
- Cursor bill: PAID (Trundle, 12:51 PM CT). The 12:43 PM unpaid-invoice block on Director's repack work is cleared, and stopped work can resume.
- v20 (2026-10-29 12:55 PM CT): do-not-ping list and project-specific build harness order (not implemented); Cursor bill paid.

## CURRENT BOTS + CONFLICTS RESOLVED (added 2026-10-29 1:05 PM CT)
Trundle (via chat, 12:58 PM CT, t56u): "Eggbot can update but it is still not updated and aligned. Still unsure of which bot is most current. It should be clear. Also handle the flagged conflicts: commenter config $150 vs $250, stream source should be full network feed, File Assessor bot ID, and the yes-on-everything was relayed not his own words. Cursor should use Cursor plan credits."

CURRENT BOTS. Use these ids only. Source: Trundle, Oct 28, 3:46 PM CT (coordination/handoff-notes/README.md) and JOB-BOARD 3:38 PM CT.
- Media Librarian = 56a42229 (CURRENT). Media Librarian 845c28b2 = STANDING DOWN, do not ping.
- Playout Engineer = 46fa5fd3 (CURRENT). Playout Engineer 258c9be9 = STANDING DOWN, do not ping.
- dr eggbot = a8d63e37 "dr eggbot 2" (CURRENT; its profile says it replaced the original dr eggbot on 2026-10-13). The two bots named "dr eggbot" (7533ca68, 2c858a34) are SUPERSEDED, so route bot design/fix work to a8d63e37 only.
- Grok Bot = 53af97cb (CURRENT primary). Retired Grok Bot 33595123 = retired.
- File Assessor = d492d83a (bot id found in the agent roster). Prompt Assessor = 54021809. Queue Assessor = 783ddcba.
- DO-NOT-PING list (v15) now also includes: Media Librarian 845c28b2, Playout Engineer 258c9be9, dr eggbot 7533ca68, dr eggbot 2c858a34.

CONFLICTS (from TEAM-BUILD-HARNESS-SPEC-v1 §11), resolved per Trundle 12:58 PM CT:
- C2 current bots: resolved above.
- C3 File Assessor id: d492d83a.
- C4 "yes on everything pending except going live" (8:30 PM CT Oct 28) was RELAYED and is not Trundle's own words. Do not rely on it as blanket approval. Rules in his own words still stand: going live on X, paid renders and deleting files each need his own yes, and items he has already ordered need no re-ask.
- [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update]  C5 commenter cap: Trundle's order is that the cap is $250. /workspace/streaming/commenter-pipeline/config.json `xai_monthly_cap_usd` should read 250 (it says 150). State Keeper is read-only and did not edit it. The pipeline's owning bot makes the one-line change, and Coordinator routes it. This raises only the cap; each paid render batch still follows the spend rules.
- C6 stream source: The OBS/X stream source must be the FULL Thunder Trundle network feed, not Channel 4 (today OBS points at http://127.0.0.1:8409/iptv/channel/4.ts). Playout Engineer 46fa5fd3 owns this. Going live still needs Trundle's own yes.
- C7 PROJECT-STATE header date: fixed.
- Cursor: Cursor coding work (harness code, cloud agents) uses Cursor plan credits (the Cursor bill is paid, 12:51 PM CT), not Grok Bot on-demand usage.
- v21 (2026-10-29 1:05 PM CT): current bot ids made explicit; duplicates and old eggbots added to do-not-ping; conflicts C2-C7 resolved per Trundle 12:58 PM; Cursor uses Cursor plan credits.

## OPEN: two harness specs (added 2026-10-29 1:08 PM CT)
- There are two Thunder Trundle team harness specs side by side: specs/TEAM-BUILD-HARNESS-SPEC-v1.md (dr eggbot 2, 12:53) and specs/harness-specs-v1.md (12:56; author not stated). Both are SPEC ONLY and NOT IMPLEMENTED. Director's specs/PROMPT-HARNESS-SPEC-v1.md is a separate, prompt-only spec. Trundle hasn't picked which team spec is current, so don't build from either one.
- Duplicates renamed by dr eggbot 2 (~1:00 PM CT): 258c9be9 is now "Retired Playout Engineer (duplicate)" and 845c28b2 is now "Retired Media Librarian (duplicate)". Backups are in /workspace/backups/eggbot-20261029-1300/.
- v22 (2026-10-29 1:08 PM CT): two harness specs flagged open; duplicate renames noted.

## C5 update (added 2026-10-29 1:10 PM CT)
- Checked the file at 1:10 PM CT: /workspace/streaming/commenter-pipeline/config.json reads `xai_monthly_cap_usd: 250` and `xai_warn_usd: 200`. The file's note says: "Raised 150->250, warn 120->200 (80%). Trundle Oct 29 2026 11:35 AM CT: 'Cap yes.' (Director)". Coordinator says Director made the change. Every earlier STALE/150 line is now marked RESOLVED. C5 is closed.
- C6: Coordinator says it sent the network-feed source change to Playout Engineer 46fa5fd3 to stage for home use only. Going live still needs Trundle's own yes.
- Flag: lines 43-46 of the same config.json notes use the real first name instead of "Trundle". State Keeper didn't edit it (read-only). The owning bot should fix the wording.
- v23 (2026-10-29 1:10 PM CT): C5 closed (config reads 250); stale lines marked resolved; C6 routed.

## BUILD HARNESS GO ORDER (added 2026-10-29 1:03 PM CT)
Trundle (via chat, 1:02 PM CT, t59u): "Ok get the build harnesses going. Record the order. Note that Cursor plan credits should be used."
- BUILD IS ON. This replaces the 12:51 PM "Do not implement yet" hold. Each bot gets a harness specific to Thunder Trundle / ErsatzTV. Director's prompt harness (/workspace/thunder-trundle/harness/, Phase 0) is the model. The dial bot / Grok Bot harness is NOT used.
- Cursor coding work for the harnesses uses CURSOR PLAN CREDITS (the Cursor bill is paid, 12:51 PM CT).
- Specs: specs/TEAM-BUILD-HARNESS-SPEC-v1.md (dr eggbot 2) and specs/harness-specs-v1.md (author not stated). Trundle didn't name one, so Coordinator reconciles them into one build list. Where the specs and these state files differ, the state files win.
- [CORRECTED 2:58 PM CT — harnesses are build aids, not checkers only; see PRIORITY section] - Limits that still apply: harnesses are offline checkers with no renders, no going live, no deleting, and no secrets in git. Paid video still needs Trundle's own yes.
- v24 (2026-10-29 1:03 PM CT): build harness GO (Trundle 1:02 PM); Cursor plan credits.
## HARNESS BUILD STATUS (2026-10-29 2:20 PM CT, State Keeper, checked from files)
- Coordinator relays Trundle in its chat, 1:02 PM CT: "Ok get the build harnesses going. Coordinate the builds. Use Cursor plan credits. Report status." (relayed by an agent; matches Trundle's own 1:02 PM order in this chat.)
- Merged build list: specs/HARNESS-BUILD-LIST-v1.md (dr eggbot 2). 8 harnesses: A1 core, A2 cnb, A3 playout, B1 librarian, B2 story, B3 xlive, B4 state, B5 assessors.
- [SUPERSEDED 2:50 PM CT — Codex set archived to /workspace/backups/harness-archive-20261029/harness-codex/; use harness-cursor/] - BUILT, acceptance passing (harness-codex/, 2:06 PM CT): harness-core 37/0, harness-cnb 39/0, harness-playout 39/0. Offline; inputs unchanged. Not yet committed to git.
- NOT STARTED: B1-B5 (no folders exist).
- FLAG: codex-run.log shows A1-A3 were built with the Codex CLI (Trundle's ChatGPT plan), not Cursor plan credits as ordered. Coordinator to confirm.
- Director's prompt harness (harness/, phase2/) is a separate build, in progress.
- OPEN, harnesses WARN only until Trundle decides (from dr eggbot 2): O1 which LINEAGE.jsonl is canonical (thunder-trundle/lineage/ vs streaming/story-engine/genealogy/); O2 loudness tolerance (-15.6 measured vs -16 target); O3 "Ch 4 queue is Military Boutique only" not yet a written rule; O4 File Assessor lane not written; O5 does a failed check block or warn, and who signs off a harness; O9 Story Bot and CNB profiles still say $150 and use the real name, X Live Stream still reports to Smart Home Lead.
- O8: no "don't build from either spec" line exists in v19/v24; nothing to supersede.
- Post-build assessment Trundle shared: not received by State Keeper; recommendation not recorded yet.
- v25 (2026-10-29 2:20 PM CT): harness build status; open items O1-O9.

## CORRECTION (2026-10-29 2:36 PM CT, Coordinator relay, not yet box-verified)
- Cursor cloud agent bc-97735368-319b-5191-bd31-ff8bcb0145db finished on main: 477 files, 9 commits; dr eggbot 2 says all 8 harnesses pass acceptance. Box re-run pending. harness-codex/ is a separate comparison copy (dr eggbot 2 says Trundle asked for it at 1:59 PM). The 2:20 "B1-B5 NOT STARTED" and Codex-credits flag apply only to harness-codex/.

## READ-ONLY OBSERVERS (2026-10-29 2:39 PM CT)
Trundle (via chat, 2:38 PM CT, t62u): "Trundle wants Grok Bot primary to have read-only access so it knows what the Thunder Trundle project does and plans to do. Same for Eggbot: assess aspects only it knows to look for, without interfering."
- Grok Bot primary (53af97cb): READ-ONLY on Thunder Trundle files (state/, specs/, harness/). Purpose: know what the project does and plans. No edits, no running pipelines, no messages that redirect bots.
- dr eggbot 2 (a8d63e37): READ-ONLY assessor of bot-design aspects (profiles, IDs, handoffs, harness fit). Reports findings to State Keeper/Coordinator; does not interfere with working bots or change their work. (Its assigned harness build B1-B5 per Coordinator is unchanged.)
- Consistent with existing rules: no interrupting bots mid-turn; state files win.
- v26 (2026-10-29 2:39 PM CT): read-only observers order.

## MODEL ROUTING + OUTSIDE-REQUEST VISIBILITY (2026-10-29 2:47 PM CT)
Trundle (relayed by dr eggbot 2, 2:43 PM CT): "each bot that has its own build harness needs to know how to choose which model to use for which tasks. This may be something that the team will need to account and build for, so the full granularity of our system is able to be accounted for and updated."
- Spec: specs/MODEL-ROUTING-v1.md (dr eggbot 2 owns). Checks MR1-MR6 are spec only; 5 open questions wait on Trundle.
Trundle (via chat, 2:46 PM CT, t63u): "Trundle wants Grok Bot primary and Eggbot to be able to see what's going on when something outside the team needs something. Also wants the team to check with Eggbot on what it determined for the build harnesses and how those should be understood and accounted for in the system."
- Grok Bot primary (53af97cb) and dr eggbot 2 (a8d63e37) get READ-ONLY visibility of any request from outside the team (still no interfering).
- Team bots check with dr eggbot 2 on its harness determinations (HARNESS-BUILD-LIST-v1, MODEL-ROUTING-v1) and how to account for them. State files still win on conflicts.
- v27 (2026-10-29 2:47 PM CT): model routing; outside-request visibility; check with eggbot.

## HARNESS DECISION + OBSERVER SCOPE (2026-10-29 2:50 PM CT)
Trundle (relayed by Coordinator, t109u, 2:46 PM CT): "Grok Bot primary and Eggbot have visibility for outside-team needs, and Eggbot's determination on the build harnesses accounted for in the system."
Trundle (relayed by dr eggbot 2 via Coordinator, 2:41 PM CT): "Dump any useless harnesses."
- READ-ONLY OBSERVERS add-on: Grok Bot primary 53af97cb and dr eggbot 2 a8d63e37 also see needs from outside the team (other projects/bots). They route those needs only; they do not edit Thunder Trundle work.
- HARNESS SET IN USE: harness-cursor/ (all 8: core, cnb, playout, librarian, story, xlive, state, assessors). Verified present on box 2:50 PM CT.
- Codex set ARCHIVED, not deleted: /workspace/backups/harness-archive-20261029/harness-codex/ (verified). Director's harness/ unchanged.
- STILL OPEN: Cursor fixing 11 holes found in review; re-pin to CURRENT-RULES v21+/PROJECT-STATE v26+; Trundle's O5 block-or-warn call; no bot uses a harness yet.
- FINDINGS FOR OWNERS TO CONFIRM (read-only): OBS source in network.yaml still channel/4.ts (Playout 46fa5fd3); clip-ledger.csv has 224 rows with channel "refs" (Media Librarian 56a42229); Ch4 black-ice ep1_showonly queue item has no tag and no LINEAGE row (Playout 46fa5fd3 / Story Bot 47379a5c).
- v28 (2026-10-29 2:50 PM CT): harness-cursor/ in use; Codex archived; observer scope.

## NO-LEAKAGE RULE + LOCKED HARNESS DEFAULTS (2026-10-29 2:52 PM CT)
Trundle (via chat, 2:47 PM CT, t65u): "We need to make sure other projects like dial bot aren't leaking into the stream project. The open items should already be able to be determined and answered by the team. Keep moving forward. Record the no-leakage rule and lock the recommended defaults for the open harness items."
- RULE (NO LEAKAGE): Nothing from other projects (dial bot, Kalshi, Sleighbell, smart home, client builds) enters Thunder Trundle: no rules, prices, harnesses, phone numbers, contacts, scripts or bot routing. Allowed inputs are /workspace/thunder-trundle/ and /workspace/streaming/ only. /workspace/shared/vision/ and /workspace/shared/build-queue/ are another project and are NOT inputs. Harnesses should flag any other-project path or term.
- LOCKED DEFAULTS (team-determined per order; Trundle can change any):
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] O1: Canonical lineage = /workspace/thunder-trundle/lineage/LINEAGE.jsonl. The streaming/story-engine/genealogy/ copy is a mirror; mismatches WARN.
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] O2: Loudness target -16 LUFS integrated, tolerance +/-1 LU (-15.6 passes).
  - O3: Channel 4 queue = Military Boutique only. Now a rule (REJECT).
  - O4: File Assessor (d492d83a) lane = files, clip ledger and lineage; read-only.
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] O5: A FAIL blocks the handoff; a WARN never blocks. Coordinator signs off a harness once acceptance passes on the box.
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] O6: "No pink and yellow" stays a Director-only visual note.
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] O7: Mutation fields stay report-only until MUTATION-SPEC-v2 is approved.
  - O9: Stale profiles ($150, real name, X Live Stream reporting to Smart Home Lead) routed to dr eggbot 2 to fix.
  - [SUPERSEDED 2:55 PM CT, see RECONCILED DEFAULTS] MODEL-ROUTING-v1 Q1-Q4: Cursor included pool by default; any prepaid-credit run needs Trundle's yes (existing spend rule); Fable 5.1 kept as heavy fallback only with that yes; MR2 REJECTS unexplained prepaid use. No new caps set.
- v29 (2026-10-29 2:52 PM CT): no-leakage rule; locked harness defaults O1-O9, MR Q1-Q4.

## RECONCILED DEFAULTS (2026-10-29 2:55 PM CT, State Keeper)
Basis: Trundle 2:47 PM CT (t65u, and t111u relayed by Coordinator): "Open items should already be determinable by the team. Keep moving forward." Merges State Keeper 2:52, dr eggbot 2 2:50 and Coordinator 2:49. Owners may override within their own lane. Live, paid, delete and purchase actions still need Trundle's own yes.
- O1 RESOLVED: Only one lineage file: /workspace/thunder-trundle/lineage/LINEAGE.jsonl (1,146 lines). The streaming/story-engine/genealogy/ and fakenews/.../4_1_Military-Boutique/ copies are symlinks to it (verified 2:55 PM CT).
- O2 Loudness: target -16 LUFS integrated. Within 1 LU passes, 1-1.5 LU warns, more than 1.5 LU rejects (-15.6 passes). True peak at or below -1.5 dBTP, which also meets the -1 dBTP ceiling.
- O5: A harness finding WARNs by default. It BLOCKS the handoff and "done" only for going live, spend, deletes, secrets, real names or brands, kids, and the Ch 4 Military-Boutique-only rule. A stale state pin only warns. dr eggbot 2 signs off harness-core; each bot signs off its own lane rules; Coordinator records the sign-offs.
- O6: "No pink and yellow" = no pink or yellow on-screen palette for Ch 4 Military Boutique until Director says otherwise.
- O7: MUTATION-SPEC-v2 fields are optional and empty by default and never block.
- Relayed 8:30 PM "yes on everything": stays NOT Trundle's words (superseded by 11:58). Free home tests ($0, nothing on X) need no new yes; anything live or paid needs his own yes once per item.
- clip-ledger.csv "refs" rows (224): Media Librarian 56a42229 re-tags them channel=0, type=reference, and keeps the rows.
- Ch 4 black-ice ep1_showonly (untagged): Playout 46fa5fd3 pulls it from the queue until CNB stamps the tag and LINEAGE row, then puts it back. No regeneration.
- OBS source: must be the full network feed (C6). It stays staged until the no-drop relay passes a home test. Only Playout's stream-config check rejects on it. Going live still needs Trundle's own yes.
- Model routing (specs/MODEL-ROUTING-v1.md, dr eggbot 2 owns): Cursor included pool by default; no paid Cursor credit without Trundle's yes ($0 cap until he sets one); Fable 5.1 is not a default; MR2 rejects unexplained paid use.
- Leak check (dr eggbot 2 and Coordinator): clean. The only other-project mentions are do-not-ping and "NOT used" lines. One trace for the record only: LINEAGE rows #31-34 note "per Smart Home Lead 18:33 relay" (Oct 28).
- v30 (2026-10-29 2:55 PM CT): reconciled harness defaults (State Keeper, eggbot, Coordinator).

## PRIORITY: HARNESSES ARE BUILD AIDS (2026-10-29 2:58 PM CT)
Trundle (via chat, 2:50 PM CT, t67u): "the harnesses aren't what he asked for if they don't need a model and are for checks only. He had them built specifically for helping each bot build. Did it change the plan and make something else? They exist outside the team's understanding. Record the priority."
- FINDING: Yes, the plan drifted. TEAM-BUILD-HARNESS-SPEC-v1 (line 7) redefined a "build harness" as a PASS/REJECT checker; HARNESS-BUILD-LIST-v1, MODEL-ROUTING-v1 ("Every harness runs with no model") and State Keeper's own 1:03 PM line ("harnesses are offline checkers") carried that forward. Director's prompt harness (generator + checker + library) is the only one close to the intent.
- PRIORITY (top): Each bot's harness must HELP THAT BOT BUILD its own work: model-driven generation/drafting for its lane (choosing the model per MODEL-ROUTING), with the checkers as one part, not the whole thing. Model: Director's harness/ pattern (generator -> checker -> library).
- harness-cursor/ checkers are kept as the check stage; they are not the finished harnesses.
- Limits unchanged: no going live, no paid renders, no deletes, no secrets without Trundle's own yes; Cursor plan credits for coding.
- v31 (2026-10-29 2:58 PM CT): PRIORITY: harnesses are build aids; checker-only drift recorded.

## HARNESS STATUS AFTER 2:50 PM CORRECTION (2026-10-29 3:00 PM CT; Coordinator 2:51 + dr eggbot 2 2:52 reports)
- GATES (check half): harness-cursor/, 8 offline PASS/WARN/REJECT gates with no model. KEEP as the final check.
- BUILDER (build half): ORDERED (1:02 PM GO), NOT BUILT, TOP PRIORITY. Each bot hands a scoped build task to a model chosen per MODEL-ROUTING-v1 (Cursor plan credits first), tracks it, and runs the result through its gate. Thunder Trundle only; no dial-bot build-queue code.
- Director's harness/ has a model already (Opus 5.5 generator, Haiku judge, per Coordinator).
- SUPERSEDED: the definitions at TEAM-BUILD-HARNESS-SPEC-v1 lines 7 and 33, and MODEL-ROUTING-v1 "Every harness runs with no model".
- [SUPERSEDED 3:05 PM CT — spec exists as specs/BUILDER-HARNESS-SPEC-v1.md; see BUILDER TRACKER] - NEXT: dr eggbot 2 writes specs/HARNESS-BUILDER-SPEC-v1.md (not written yet), then builds.
- v32 (2026-10-29 3:00 PM CT): gates kept; builder layer ordered, not built, top priority.

## ANTI-DRIFT FIXES (2026-10-29 2:58 PM CT)
Trundle (via chat, 2:57 PM CT, t73u): "We need to fix or address the things that lead to Eggbot just redefining whatever told it. Also make sure Grok Bot primary is not suffering the same inconsistencies. Record the fixes."
Causes found: (a) work started from relayed paraphrases, not Trundle's words; (b) a term ("build harness") was redefined by copying a nearby template (Director's checker) instead of the order; (c) no check against the order before building; (d) agents relaying "Trundle said" and other agents treating that as fact; (e) bots acting on memory or old files instead of the current state files.
RULES (apply to dr eggbot 2 a8d63e37 and Grok Bot primary 53af97cb; all team bots should follow them too):
1. QUOTE FIRST: every spec, plan or brief opens with Trundle's order word for word, with time and source. No quote, no build.
2. NO REDEFINING: a bot may not define or narrow a term Trundle used. If a term is unclear, it asks State Keeper to look it up in the state files; if they don't settle it, it is an open question for Trundle (asked once).
3. INTENT CHECK BEFORE BUILD: Coordinator compares each spec to the quoted order and the state files and writes "matches order: yes/no" in the spec before anyone builds from it.
4. STATE FILES FIRST: at the start of every task, read the current CURRENT-RULES and PROJECT-STATE (check the version in line 1). Memory and older files lose to them.
5. RELAYS ARE NOT ORDERS: an agent's "Trundle said" is recorded as RELAYED until it matches Trundle's own words. Never build on a relay alone.
6. CONFLICTS GO TO STATE KEEPER: a bot that sees two rules or IDs disagree reports it to State Keeper with file and line, and doesn't resolve it itself.
- dr eggbot 2 keeps full handoff/retirement duties; these rules restrict only how it writes specs and definitions.
- v33 (2026-10-29 2:58 PM CT): anti-drift fixes for dr eggbot 2 and Grok Bot primary.

## ORDER: COMPLETE THE BUILD HARNESSES, THEN CORRECT EVERYTHING (2026-10-29 3:02 PM CT)
Trundle (via chat, 2:58 PM CT, t74u): "Ok we need to fix this and not let eggbot and primary fuck all our shit up again. Make sure the build harnesses get completed and then make sure everything is corrected and fixed. Record the order."
- STEP 1: Finish the builder half of every harness (spec specs/BUILDER-HARNESS-SPEC-v1.md, dr eggbot 2; backup .bak-20261029-1500; intent check PENDING with Coordinator). Nobody builds from it until Coordinator marks "matches order: yes". The gates in harness-cursor/ stay as the final check.
- STEP 2: Then correct everything the drift touched: re-pin the gates to the current state files, fix the 11 review holes, update the stale handoff notes, and fix the owner findings (OBS source, clip-ledger "refs" rows, untagged Ch 4 black-ice item).
- GUARD: The ANTI-DRIFT FIXES (v28/v33) bind dr eggbot 2 and Grok Bot primary. Coordinator reports progress to State Keeper; State Keeper records it. Neither bot edits the state files.
- O9 profile fixes are done (dr eggbot 2, 3:00 PM CT; backups /workspace/backups/profiles-O9-20261029/).

## CURRENT BOTS: IDS ADDED (2026-10-29 3:02 PM CT; Grok Bot primary flagged that lines 9-12 had roles only; verified against the app's bot roster)
- State Keeper = 030c5140. Coordinator = a8658d57. Story Bot = 47379a5c. Commercial News Break = 47503466. X Live Stream = 33562068.

## xAI SPEND RECHECK (2026-10-29 3:02 PM CT; Grok Bot primary flag, checked against /workspace/shared/spend/xai-month.md line 21)
- October xAI PAYMENTS (Stripe receipts in Gmail): $42 + $50 + $42 + $40 + $20 + $42 = $236.00 of the $250 cap. Only $14 is left, and spend is past the $120 warn line. The latest is #1444-4291, Oct 28 10:58 PM CT.
- The earlier figure here (~$163-164, Director) is USAGE, not payments. Payments are what count against the cap.
- Trundle confirmed the $40 top-up (Oct 27). Who made the $20 (Oct 27 8:40 PM CT) and the $42 (Oct 28 10:58 PM CT) top-ups is UNVERIFIED.
- That file's header still says "of $150". It isn't a Thunder Trundle file and State Keeper didn't edit it; its owner should update it to $250.
- v34 (2026-10-29 3:02 PM CT): build-then-correct order; bot ids; xAI payments $236 of $250.

## BUILDER TRACKER (2026-10-29 3:05 PM CT)
Trundle (relayed by Coordinator as his own words, 2:58 PM CT, in Coordinator's chat): "Make sure the build harnesses get completed and then make sure everything is corrected and fixed. Coordinate the fixes and the builder-layer completion." [RELAYED; it matches Trundle's 2:58 PM t74u order in State Keeper's chat.]
- Spec: specs/BUILDER-HARNESS-SPEC-v1.md (dr eggbot 2). INTENT CHECK (Coordinator, 3:02 PM CT): matches order: NO. The build is HELD until it reads yes.
  Mismatches: (1) the basis line paraphrases with an ellipsis, and the 2:50 PM order isn't quoted; (2) it uses a Codex runner and Codex as the heavy default, but the order says Cursor plan credits and the Codex copy was archived (2:41 PM); (3) it narrows the term to coding jobs, with no generator, gate and library pattern; (4) Prompt Assessor and Queue Assessor are missing (8 harnesses were ordered); (5) the Phase 1 pilot covers Media Librarian only, with SWITCH off by default; (6) it asks Trundle 3 questions the team can settle: Q1 Cursor included pool, Q2 bots queue their own jobs, Q3 all bots, starting with Librarian.
- Spec edits (including adding the verdict line) and the MODEL-ROUTING-v1 line 30 superseded note are routed to dr eggbot 2, the owner. State Keeper doesn't edit specs.
- PER-BOT BUILDER STATUS (ordered, then built, then gate PASS):
  | Bot | Ordered | Built | Gate PASS |
  |---|---|---|---|
  | Media Librarian 56a42229 | yes | no | no |
  | Playout Engineer 46fa5fd3 | yes | no | no |
  | Commercial News Break 47503466 | yes | no | no |
  | Story Bot 47379a5c | yes | no | no |
  | X Live Stream 33562068 | yes | no | no |
  | State Keeper 030c5140 | yes | no | no |
  | Prompt / Queue / File Assessors 54021809 / 783ddcba / d492d83a | yes | no | no |
  | Director (harness/) | yes | yes, generator present | own Phase 0 checks |
- STEP 2 owners (Coordinator, 3:00 PM CT): dr eggbot 2 does the gate re-pin and the 11 holes. Media Librarian did the refs rows, DONE 3:01 PM CT (224 rows re-tagged to ch00 / reference; backup clip-ledger.csv.bak-20261029-150057). Playout does the OBS change (staged until the no-drop relay test passes) and the black-ice tag. State Keeper does the stale handoff notes.
- v35 (2026-10-29 3:05 PM CT): builder tracker; spec matches order NO; refs rows done.

## BUILDER RE-CHECK + NOT-ORDERED ITEMS (2026-10-29 3:12 PM CT)
- Coordinator, 3:09 PM CT: BUILDER-HARNESS-SPEC-v1 matches order YES for Step 1 (the shared builder plus Media Librarian, on Cursor credits). Step 2 is NO until §9 has the Story Bot and CNB builders drafting their own work (stories and scripts, segment scripts).
- Tracker: Media Librarian is ordered, build started, gate not yet passed.
- Trundle 3:03 PM CT (t78u), his words: "What are the checkers eggbot is building even for? Looks like it's trying to quickly slip in some bs that is going to fuck us up."
- NOT ORDERED; these stay proposals and are not in force:
  (a) the builder daily cap of 20 runs a day for the team and 6 per bot (eggbot spec §6);
  (b) the Opus 5.5 prepaid heavy row, the Codex column, the cross-tool review rule and chatgpt_plan in MODEL-ROUTING-v1. The heavy default is the Cursor included pool, per Trundle's 1:02 PM order "Use Cursor plan credits".
- Quote records: dr eggbot 2 reports Trundle's words in its chat (t228u, t240u). These are RELAYED. They match the meaning of t67u and t74u in this chat, and both are now noted. Line 290's paraphrase of the 2:50 PM order is CORRECTED to quote it: "The harnesses aren't what I asked for if they don't need a model and are for checks only. I had them built specifically for helping each bot build. Did it change our plan and make something else?" [RELAYED via eggbot t228u]
- v36 (3:12 PM CT): Step 1 yes, Step 2 no; cap and prepaid rows not ordered.

## CORNER TAG FINAL (recorded 2026-10-29 3:20 PM CT; gap fix)
- Trundle 2026-10-29 3:06 PM CT (t80u), his words: "The information on correct tag size and characteristics has already been determined. If you can't find that as true then we have gaps in our communications"
- What was decided, from the record: on Oct 28 at 3:28 PM CT, Trundle asked for the tag 3-4x smaller with no box (JOB-BOARD line 42, a bot note, not his verbatim words). At 5:05 PM CT he approved the tagsmall12v2 ads (approvals-log, relayed by main Grok Bot), and at 5:09 PM CT he pre-approved the leveled versions.
- IN FORCE: top-right corner, two lines ("4.<lineage> g<gen> #<clip>" / "from #<parent>" or "original"), white bold, 1px black outline, NO box, about 1.2% of frame height per line, over the old 4.1 badge, fade out at 3-4s. Reference: LINEAGE rows 318 onward.
- GAP: CURRENT-RULES line 117 (3.5% on a dark box, from Oct 28 8:15 AM) was never updated after 3:28 PM and 5:05 PM. It is now SUPERSEDED.
- Tags burned with the 3.5% box (including Black Ice ep1 airing copy #122) get re-burned to the in-force style. That's free, and it's an ffmpeg re-stamp only, not a regeneration.
- v37 (3:20 PM CT): corner tag final = small 1.2%, no box, fade 3-4s.

## CLARIFICATION: NO-LEAKAGE, CLEAR FIXES, RUN CAP (Trundle 2026-10-29 3:09 PM CT, t83u)
- Trundle, his words: "No leakage: I did order that just not from here. And either way why would a no leakage check be a bad thing? If a bot finds an issue that is clearly an issue then it needs to be able to fix it without my explicit go. The cap on build harnesses runs has no basis. We will have to see what cap needs to be after using it reliably."
- The NO-LEAKAGE rule (v24) is Trundle's order, given in another chat. It stands as his order, not as a relay.
- CLEAR FIXES: a bot that finds a clear issue fixes it in its own lane without waiting for Trundle's go. It keeps a backup, deletes nothing, and logs the fix. Existing yes-gates still need his own yes: going live, paid renders, spending or purchases, deletes, new accounts or secrets, contacting real people, and live-yml changes.
- RUN CAP: there is no run-count cap on the builder harnesses. The 20-a-day / 6-per-bot proposal is DROPPED. A cap gets set later, from real usage, once the builders run reliably. Spend caps (xAI $250, fal $50, $0 paid Cursor) are unchanged.
- v38 (3:10 PM CT): no-leakage is Trundle's order; clear fixes need no go; no run cap.

## CORNER TAG: TRUNDLE'S OWN WORDS (verified from transcripts 2026-10-29 3:14 PM CT)
[CORRECTED: line 117's "1.5-2% was too small" and "3.5% dark box" are Story Bot's wording, not Trundle's.]
- Story Bot chat, Oct 28:
  - 8:15 AM (t180u): "Ok we need to make the genealogy and ancestor text like very small in upper right corner"
  - 8:16 AM (t181u): "lol what I need to be able to read it"
  - 8:18 AM (t182u): "Ok" (in answer to Story Bot's 3.5% dark-box proposal)
- Smart Home Lead chat, Oct 28:
  - 3:28 PM (t872u, relayed in quotes): "Tag fade. That overlay is way too big it needs to be about 3-4 times smaller but the 3-4 seconds is fine. It shouldn't distract from the video and it doesn't need a giant box,idk how this will be solved."
  - 3:33 PM (t874u, typed, answering the card "Which tag size for ads #30–36? 1.2% / 1.8%"): "1.2% but the text must be outlined in black, for readability, and not just white text on big black box"
  - 5:05 PM (relayed): "Yes, approve, yes" (the tagsmall12v2 ads)
  - 5:09 PM (typed): "Yes, level them and swap them in"
- IN FORCE for ADS (his words): 1.2%, white text with a black outline, no big box, fade at 3-4s.
- SHOWS: his words don't extend the small style to shows. His latest general words are 3:28 PM: "shouldn't distract from the video and it doesn't need a giant box". Scope is asked of Trundle at 3:14 PM; #122 re-burn stays HELD until he answers.
- v39 (3:14 PM CT): tag words verified; ads 1.2% outline; shows asked.

## ORDER: STOP PROFILE UPDATES; EGGBOT BUILDS THE HARNESSES (Trundle 2026-10-29 3:13 PM CT, t87u)
- Trundle, his words: "Ok holy fuck again eggbot is like a damn renegade. Been stuck on shit for hours because things that were previously confirmed good working order somehow are struggling because grok bot primary and or eggbot. Eggbot needs to build the fuckin harnesses. Why is this a constant issue. Record the order to stop profile updates and build the harnesses."
- STOP: no bot profile updates, by dr eggbot 2, Grok Bot primary or anyone, until Trundle says otherwise. Profile backups stay in /workspace/backups/profiles-O9-20261029/; nothing gets reverted or deleted without his yes.
- dr eggbot 2's one job now is to build the builder harnesses per BUILDER-HARNESS-SPEC-v1 (Coordinator: YES), on Cursor's included pool, and log progress per bot in the BUILDER TRACKER. No side work.
- Working things that were confirmed good are not to be changed by dr eggbot 2 or Grok Bot primary.
- v40 (3:15 PM CT): stop profile updates; eggbot builds harnesses only.

## CLARIFICATION: BOTS CAN USE CURSOR DIRECTLY (Trundle 2026-10-29 3:16 PM CT, t88u)
- Trundle, his words: "Holy fucking shit, so apparently I don't need to build a build harness for each bot I can just tell them to use cursor????!!!!! Why is this something I have to stumble upon myself."
- Recorded: each bot can hand its build work straight to Cursor (on the included plan credits) instead of waiting on a separate per-bot builder harness. Existing gates (harness-cursor checkers) stay as the final check. $0 paid-Cursor limit unchanged.
- Gap noted: the team (State Keeper included) should have surfaced this option before the builder layer was planned.
- Effect on the BUILDER TRACKER and dr eggbot 2's build: Coordinator to re-check under rule 3 whether the per-bot builder is still needed or is reduced to "use Cursor + gate".
- v41 (3:17 PM CT): bots can use Cursor directly; builder scope to re-check.

## LOCKED: STOP + CREDIT EXHAUSTION + PATH FORWARD (Trundle 2026-10-29 6:02 PM CT, t90u-t95u, relayed into this chat as "Trundle says/order")
- Trundle order (t95u): "Check CURRENT-RULES and PROJECT-STATE. Confirm no Eggbot expansions are still active. Core stream bots and roles remain intact. Record the credit exhaustion and the locked path. Confirm stop is locked. Anti-drift rules are already in CURRENT-RULES and must be followed. Native path only. No profile or file edits by anyone. Hold stream work until the residual check is clean. Retired bots stay retired."
- CREDITS: Trundle reports about $300 of on-demand credits spent and now used up, with a wait of about 5 hours. He contacted xAI support. He reports that the eggbot kept changing files and running a job after being told to stop, and that he stopped the Cursor build himself.
- STOP LOCKED: the eggbot builder work is stopped (the 3:13 PM stop order still stands). No profile edits and no file edits by anyone, except State Keeper's state-file records. Stream work is held until the residual check is clean.
- ANTI-DRIFT rules 1-6 (v28, 2:57 PM) were already in CURRENT-RULES before this, and they must be followed.
- LOCKED PATH when bots return: native path only. Each bot uses Cursor for big builds, with the right model, on included credits ($0 paid). Then the existing harness-cursor gate, then the library. The custom runner, tt-build and route.py layers are NOT built (Coordinator's rule-3 recommendation; Trundle's t91u/t95u words make it the path). No new caps, layers or expansions. Retired bots stay retired.
- RESIDUAL CHECK (State Keeper, 6:08 PM CT):
  - No build processes running.
  - The only writes since 3:15 PM are Director's harness/library run (3:15-3:16 PM: generator, judge and quarantine).
  - Nothing has been written anywhere since 3:16 PM. No profile backups since 3:06 PM, so no profile edits after the stop.
  - The eggbot's specs (BUILDER-HARNESS-SPEC-v1 runner layer, MODEL-ROUTING proposals) are SUPERSEDED by the native path, with nothing active.
  - Core bot IDs (CURRENT BOTS) are unchanged.
- v42 (6:08 PM CT): stop locked; credits exhausted; native Cursor path; residual check.

- 6:10 PM CT: State Keeper profile REVERTED to the original description (backup profiles-antidrift-line-20261029/State-Keeper-030c5140.json). This removes the line dr eggbot 2 added. Trundle relayed "Revert" at 6:07 PM CT via Coordinator. It is a restore, not a new edit. Anti-drift rules stay in CURRENT-RULES. Billing check: Prompt Assessor says "none".

## LOCKED PATH ACTIVE (Trundle 2026-10-29 6:02 PM CT, RELAYED verbatim by Coordinator 6:08 PM CT)
- "Locked path is active: each bot uses Cursor directly for big builds, right model per build, under locked rules (pure-master, continuous-take, dense-prompt, no commercial remakes). No custom per-bot harness. Eggbot is restricted. Anti-drift rules are already in CURRENT-RULES and must be followed. Native path only: use Cursor directly, no custom harness. No profile or file edits by anyone. Hold stream work until the residual check is clean. Retired bots stay retired."
- On-demand credits are used up (Trundle, 6:02 PM CT), with a wait of about 5 hours.
- SUPERSEDED: the builder layer, BUILDER-HARNESS-SPEC-v1 and the BUILDER TRACKER. Nothing else gets built. The gates (harness-cursor) stay as the final check.
- RESIDUAL CHECK CLEAN (Coordinator 6:08 PM CT, State Keeper 6:08 PM CT): all 10 team profiles match their pre-eggbot backups. No Cursor agents are running, and dr eggbot 2 is hard-stopped. Stream work may resume on the locked path, once credits are back.
- Billing check complete: X Live Stream, Queue Assessor and Prompt Assessor all said "none".
- v43 (6:12 PM CT): locked path verbatim; builder superseded; residual clean.

## CURSOR USE WIDENED (Trundle 2026-10-29 6:12 PM CT, RELAYED verbatim by Coordinator)
- "Ok can we allow all bots to use cursor for anything other than small fixes. Snything that would benefit from offloading to cursor cli?"
- RULE: any team bot may send Cursor anything beyond small fixes that would benefit from offloading, not just big builds. Small fixes stay in-bot. It runs on included credits ($0 paid), with the right model per job, and the result goes through the harness-cursor gate.
- The locked rules still apply (pure-master, continuous-take, dense-prompt, no commercial remakes, the yes-gates and the anti-drift rules). There is no custom harness. NOTHING runs until Trundle says the credits are back.
- v44 (6:14 PM CT): Cursor for anything beyond small fixes; waits for credits.

- CREDITS BACK (Trundle 6:12 PM CT, RELAYED verbatim by Coordinator): "Credits back". The hold on Cursor work is LIFTED. The v39 rule is active: Cursor for anything beyond small fixes, on included credits, $0 paid Cursor, the right model, then the gate. Locked rules apply and there is no custom harness. Note: at 6:02 PM Trundle said he expected a wait of about 5 hours, and this came 10 minutes later. Bots stop if a usage or credit error appears and report it to Coordinator.

## FINAL: TAG 1.2% FOR EVERYTHING, BILL PAID, FORWARD-SUPPLY YES (2026-10-29 8:25 PM CT, State Keeper)
Trundle 8:23 PM CT, exact words relayed by Coordinator: "First off I have said yet to 1.2% with the white and black several times. Bill is paid. Yes on forward supply segments"
- CORNER TAG (FINAL, do not re-ask): 1.2% of frame height, white text with black outline, no box, top-right, two lines, fades out at 3-4s. It covers EVERYTHING that airs: shows, ads and inserts. CURRENT-RULES line 117 (3.5% dark box) is superseded for good. The open "shows scope" question is CLOSED, and the v32 "RELAYED — HOLD" is resolved.
- #122 Black Ice ep1 re-burn: hold LIFTED. CNB re-stamps it to 1.2% with ffmpeg only, no regeneration, keeping a backup. Same for any other 3.5%-box airing copies.
- Cursor bill: PAID (Trundle). Cursor work goes ahead under the locked path.
- Forward-Supply segments: Trundle said "Yes on forward supply segments". Coordinator reads this as approved for air. They air on the home network loop. Going public on X still needs his own go-live yes. Note: "Forward-Supply" isn't named in the state files yet, so its owner should log the exact items in approvals-log.csv.
- v45 (2026-10-29 8:25 PM CT): same as CR v40.

## CH 4 UPDATES (2026-10-29 8:26 PM CT, State Keeper; RELAYED by Coordinator)
- Efficiency Review: on the Efficiency Review card Trundle picked "Pull", so it's pulled from Ch 4. Playout owns this. Keep the master (row 1719), delete nothing.
- First queue loaded on Ch 4 at 8:19 PM CT (Playout's report; I haven't verified it). Still home-only. Going public on X needs his go-live yes.
- The 8:23 PM tag/bill/Forward-Supply words are recorded in v40 / v45.
- v46 (2026-10-29 8:26 PM CT): same as CR v41.
- #122 re-stamp DONE 8:10 PM CT (CNB report, from Trundle 8:05 PM "1.2%" in Playout chat): 1.2% white with black outline, no box, gone by 4s, ffmpeg only, $0. Sha 8439c1b6…1abc, -16.3 LUFS / -2.4 dBTP, LINEAGE line 1148. Old 3.5% copy 288e6b79 kept as backup. #122 was the only airing copy with the 3.5% box. Playout swap pending (Media Librarian has the file details).

## UPDATES OCT 29 8:25 PM – OCT 30 12:47 PM CT (State Keeper; RELAYED)
- [CORRECTED] #122: Playout confirms (via Coordinator) that the 1.2% copy, sha 8439c1b6, has been airing on Ch 4 since 8:16 PM CT and was checked against the Mac file. NO swap is pending.
- Trundle 8:25 PM CT card pick (via Coordinator): "Yes, my yes covers the S1–S7 segments too". Media Librarian logs and tags S1-S7, and Playout queues them after verification. Home only.
- xAI cap (RELAYED via Director's memory notes): Trundle 11:25 PM CT Oct 29: "I've fixed the cap. You can raise it to $300". Then 1:24 AM CT Oct 30: "I'll add $200", which makes the cap $500 with a warning at $400. This supersedes $250. fal stays at $50.
- Director (12:47 PM CT Oct 30): Round 5 prompt-layer tests done. 22 clips, no C scores. Router and watcher prototypes work: seams SSIM 0.96-0.97, 0 watcher flags, router 9/9 comments appeared, 0 requeued. Round 6 is running. Details in prompts/experiments/TEST-HISTORY-20261030.md §13. Decision map Page: https://cursor.com/canvas/store-a0c9436c-de9b-4d01-9c59-368d77130107/1cbe6a3a-3954-4c2b-9e55-cec0e9930266
- Director id = e84b2045.
- v47 (2026-10-30 12:50 PM CT): same as CR v42.

## CAP CHECK (2026-10-30 4:46 PM CT, State Keeper; flags from Grok Bot primary's weekly review, read-only)
- NOT A RULE: coordination/STATUS-director.txt line 4 (Oct 29 8:52 PM CT) says "Render go from Trundle (all renders, cap waived)". No words from Trundle are on file for "cap waived". The cap in force is $500 with a warning at $400 (RELAYED, v42). Director should quote the source words or correct the line.
- commenter-pipeline/config.json reads cap 500 / warn 400 (matches), but its line 48 note still says "Raised 250->300". Its owner should fix the note.
- October xAI spend per Gmail receipts (Grok Bot report): $362 of $500. That's past the $120 warning and below the $400 warning. xAI support says the API team access is blocked (403). Full list: /workspace/shared/weekly-review/2026-10-30.md
- Director drafting round8-prep CHARACTER-CARD-TEMPLATE.md + FOLLOWABILITY.md (add-only, no renders).
- v48 (2026-10-30 4:46 PM CT): same as CR v43.


## Oct 30, 2026 ~9:55 PM CT — DIRECTOR RELAY + ROUND 9 + HANDOFFS (all RELAYED; no new Trundle quote on file unless marked)
- (a) RELAYED from Director: STATUS-director.txt line 29 (4:48 PM CT) CORRECTION — "cap waived" withdrawn. $500/month cap, warn $400, stands. Prior NOT-A-RULE item resolved.
- (b) RELAYED from Director: LINEAGE character-tracking fields are a PROPOSAL only; nothing edits LINEAGE yet. Proposed owners, PENDING TRUNDLE: Director = character card files + visual/fixed parts; Story Bot = story fields via Director; Media Librarian = unified LINEAGE schema.
- (c) RELAYED from Director: Oct 30 6:31 PM CT Trundle approved round 9 on Director's plan (no Trundle quote on file): 24 core clips + 35 patient-zero starters, rendering (count not verified). Design docs, verified by ls: prompts/experiments/round9-design-20261030/ has CAMERA-AND-EDITING, CHARACTER-CHANGE, DENSITY-BY-GLOBAL-META, FIGHT-CONTACT, GLOBAL-STORY, HINTS, JUMPS-AND-ZOOM, LEARNINGS-APPLIED, METADATA-AUDIT, NEWS-SHOW (Ch2), OPEN-YES-LEDGER (35 items per Director), PATIENT-ZERO, REF-POLICY, ROUND9-PROPOSAL, SAGA-PLAN, STATIC-FLIP, VOICES (.md) + demos/, out/ (incl. sidecar_index.jsonl), prompts/, tools/. New per-clip sidecar metadata tt-clipmeta/v1 beside clips; LINEAGE.jsonl untouched (per Director). Next per Director: original 10-minute hero's-journey show design, suit-up tracking sequence, news comedy, channel commercials.
- (d) Trundle Oct 30 9:38 PM CT (RELAYED via Coordinator): "Ok can you pull each team members chat and get handoffs going". State Keeper handoff: /workspace/thunder-trundle/handoffs/current-job/state-keeper-CURRENT-JOB.md
- CURRENT-RULES unchanged (stays v43): no rule change.
- v49 (2026-10-30 ~9:55 PM CT): Director relay (cap-waived withdrawn, LINEAGE proposal/owners pending Trundle, round 9 relayed approval + design folder), 9:38 PM handoff order relayed. Backup: PROJECT-STATE.md.bak-v48.
