# Thunder Trundle Current Rules — v65
[Created 2026-10-28; current as of 2026-10-30 ~11:00 PM CT v51 — see Last updated line] Written 2026-10-28 8:30 PM CT by State Keeper. Docs only, zero-cost, home-only. Companion to PROJECT-STATE.md (same folder).
[SUPERSEDED by next line] Last updated 2026-10-30 ~10:30 PM CT by State Keeper (v47)
[SUPERSEDED by next line] Last updated 2026-10-30 ~10:50 PM CT by State Keeper (v48)
[SUPERSEDED by next line] Last updated 2026-10-30 ~10:52 PM CT by State Keeper (v49)
[SUPERSEDED by next line] Last updated 2026-10-30 ~10:58 PM CT by State Keeper (v50)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:00 PM CT by State Keeper (v51)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:03 PM CT by State Keeper (v52)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:05 PM CT by State Keeper (v53)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:06 PM CT by State Keeper (v54)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:10 PM CT by State Keeper (v55)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:11 PM CT by State Keeper (v56)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:13 PM CT by State Keeper (v57)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:16 PM CT by State Keeper (v58)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:17 PM CT by State Keeper (v59)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:18 PM CT by State Keeper (v60)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:21 PM CT by State Keeper (v61)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:23 PM CT by State Keeper (v62)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:25 PM CT by State Keeper (v63)
[SUPERSEDED by next line] Last updated 2026-10-30 ~11:26 PM CT by State Keeper (v64)
Last updated 2026-10-31 ~12:27 AM CT by State Keeper (v65)
Bots: read this before acting and paste the relevant lines into messages to other bots.

## Current owners (Trundle, 4:52 PM CT rescope; handoff-notes README locked lines)
- Media Librarian (56a42229): files, ledger, review folders, refs.
- Playout Engineer (46fa5fd3): ErsatzTV, queues, OBS, vote/network switcher, pickup.
- Director: makes the choices (direction, channel defs, prompt layers, commenter schema).
- Story Bot: writes stories from Director's handoffs.
- Commercial News Break: renders and burned-in overlays.
- X Live Stream: X side (broadcasts, connection, scheduling).
- Coordinator: cross-bot coordination. State Keeper: Project State + this file (read-only otherwise).
- Assessors (Queue, File, Prompt): read Project State, return gap lists.
- Device Engineer: smart home only. Smart Home Lead: out of stream coordination.
- Duplicates Media Librarian 845c28b2 and Playout Engineer 258c9be9: standing down.

## Approvals (relayed 8:30 PM CT)
- [RELAYED, NOT TRUNDLE'S OWN WORDS — do not rely on it, see 1:05 PM CT section] Trundle: yes on everything pending EXCEPT going live. Covers: Ch4 test loop, 8 top-level .bak files, cleanup queue items, OBS -> network switcher design, handoff-note updates. Going live on X / anything public stays NO until Trundle's separate yes.

## Settled decisions (Trundle, 8:33 PM CT)
- Everything is tagged, always and correctly (genealogy corner tag burned in after generation; clean untagged masters still kept and ledgered).
- Keep the 4.1 tag on the old items we want to use (do not retag them).

## Role rules
- Trundle 7:33 PM CT: Director makes the choices; Story Bot must not rewrite anything Director hands it.

## Schema versions
- Commenter prompt: `commenter-prompt/v1` (prompts/COMMENTER-SCHEMA.md + commenter-prompt.schema.json; Director, approved by Trundle 6:14 PM CT).
- X intake queue item: `x-intake/v1` (/workspace/shared/streaming/x-intake/HANDOFF.md).
- Prompt layer order: prompts/LAYERS.md (global > channel > format > show/ad > shot > optional commenter).

## Hard limits (thunder-trundle/README.md + Trundle rules)
- Home-only. Nothing airs or goes public without Trundle's own yes.
- No kids on screen. No personal names (Trundle's never) and no real finished-product brands on screen.
- No "Military Boutique" text on screen except the small footer on priced ads #30-36.
- Overlays (corner tag, lower thirds, footers) burned in after generation with ffmpeg, never in the prompt. Show masters stay pure; clean untagged masters kept and ledgered.
- Ads are separate queue items; scheduler places breaks.
- Audio: -16 LUFS integrated, true peak <= -1.5 dBTP.
- Channels are whole numbers 2-22; 4.x is a lineage tag only. The stream is the Thunder Trundle network feed, not Channel 4.
- No moves, renames or deletions of existing files without Trundle's yes.
- Purchases, new accounts/secrets and contacting real people need Trundle's yes.

## Handoff notes now out of date (coordination/handoff-notes/)
None mention Media Librarian/Playout Engineer ownership or the 7:33 PM rule:
- device-engineer.md (3:24 PM): still lists stream lanes; now smart home only.
- director.md (3:16 PM): missing 7:33 PM rule and commenter-prompt/v1.
- story-bot.md: current as of 11:00 PM CT (7:33 PM rule and Director hold added).
- commercial-news-break.md (3:12 PM): missing new owners for ledger/playout handoff.
- x-live-stream.md (2:49 PM): missing new owners (OBS/switcher now Playout Engineer).
- No notes exist yet for media-librarian, playout-engineer, coordinator.
README.md (4:53 PM) is current on owners but not the 7:33 PM rule.

## Decisions Oct 29, 10:35-11:22 AM CT (v10; full verbatim and context in PROMPT-LESSONS v4)
- v6 continuity test approved, 10:35 AM: "Yes, render the 4 v6 test clips, about $2.72". Done: $3.45, no hidden cuts.
- Chain re-render approved, 10:47 AM: "Yes, re-render the chain forward from C3, about $6.90". Done: JW5-chain12-v6_stitched.mp4, 95.6 s, all 11 joins match, $8.28.
- Mutation job (t215, 10:58 AM): "Our job should be to make sure that the clip, whatever it is, starts and ends on a seamless cut in queue."
- No diluting (t215): "one action sentence may be diluting the direction I gave you with my John wick and example"
- Multiverse canon (t215): "make each of those similar branches carry that canon like a multiple universe situation"
- Unpaid comments (t217, 11:10 AM): "letting non paying comments affect smaller clips or small portions of the videos, or details." and "all prompts in a certain time frame get bundled and reasoned for what can apply where without stripping a single comment detail."
- Timed fade (t217): "Yes we can have a sort of timed prompt fade that lets commented prompts that are in the mutation slowly fade"
- Specs (t217): "Yes write specs and do what you need to do." / "Everything else looks good."

### Director's record (DIRECTOR-DECISIONS-20261029-detailed.md), copied verbatim, read 11:24 AM CT
## 1. Spend cap
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] Trundle (9:12 AM CT): "Raise the price cap to 250". The xAI monthly cap is $250 (it was $150). October spend is about $163.15 as of 11:13 AM CT.
[RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] STALE: /workspace/streaming/commenter-pipeline/config.json still has xai_monthly_cap_usd: 150. Not changed yet; that change needs Trundle's yes, because it lets comment renders spend automatically.
Paid renders still need Trundle's OWN yes with the price.
- APPROVED: Ch 5 Night Patrol, Ch 7 Monster Hour, Ch 9 Iron League, Ch 11 Fist Theater.
- Ch 3 Clean Job is REVISED and awaiting Trundle. Endings rotate: quiet walk-out, double-cross, long-con reveal, getaway chase (at most 1 in 4), switch, walk-away with nothing, inside man.
- Files per themed channel (2,3,4,5,6,7,8,9,10,11,12,14,16) in /workspace/thunder-trundle/channels/<nn>/: SLATE-v1.md, SCHEDULE-v1.md (24h), ARSENAL-v1.md, storyboard/PILOT-EP1-COLDOPEN.md + prompts/, refs/sheets/, CAST-SHEETS-NEEDED.md. LINEUP-v1.md is kept as the sample hour.
- Tracker: channels/MASTER-PLAN-v1.md. Ch 13, 15 and 17-22 are still unthemed.
- Ch16 DOSSIER idea (verbatim): prompts/16-dossier/TRUNDLE-VERBATIM-dossier.md. Commenter data stays public words only until Trundle answers (open).
## 4. Chaining rules (LESSONS.md and CONTINUITY.md, v5/v6 sections)
- One continuous take per 8s clip; one location per clip; settings change only between clips through an action.
- Each clip starts from the previous clip's REAL last frame. End panels are a small step from the start.
- Remove the cam HUD from a last frame before it starts the next clip. Burned-in timestamps are unreliable, so add the real time in post.
- Restate night, rain and wardrobe in every prompt (they drift).
- Exits never move toward the lens. Use "stays down" when a character must stay out.
- A redone clip can't be spliced into an old chain; re-render forward.
- Result: renders/JW5-chain12-v6_stitched.mp4 (all 11 joins match, kept takes have no hidden cuts). Path: /workspace/thunder-trundle/prompts/experiments/density-sweep-v1/renders/.
## 7. Ads (Trundle 9:17 and 9:31 AM CT)
[SUPERSEDED 12:00 PM CT — NO remakes, see STOP section] "Yeah the drawbridge one was bad but the others were good" → Glosneaks, Fizzbolt and Dynapage are approved to REMAKE (dense + reference-image method; the originals are kept). Drawbridge stays pulled. Bellquist (153414) and the Temple water tower breaking news are kept as-is, no remake. The drug-ad takes (jaundice, depression) await Trundle. The held depression and porkbelly ads never air. List: prompts/remakes/REMAKE-LIST.md. New ads: channels/COMMERCIALS-PLAN-v1.md.
## 8. Still open
Ch 3 revision approval; the new ad and character names; DOSSIER commenter images; "the pink and yellow thing" (meaning unknown, ask Trundle); a yes on the pilot cold-open renders (~$5.44 for Ch16+Ch4, ~$20.40 for all 13).

Quote check by State Keeper against Director's transcript and the TRUNDLE-VERBATIM files:
- Exact match: "Raise the price cap to 250", the t121 John Wick skeleton, "one action sentence may be diluting...", the knife/weapons paragraph, "the prompts are basically commenters...", "make each of those similar branches...", "this needs a sort of persistent...", "letting non paying comments...", "group unpaid comment prompts...", "Yeah the drawbridge one was bad but the others were good".
- MISMATCH (wording): "If we batch prompts we can ensure the same clip isn't getting rendered on one full channel playthrough". The transcript reads: "If we batch prompts we can ensure the same clip isn’tgetting rendered on one full channel playthrough right?" Director added a space and dropped "right?" (it was a question).
- Minor mismatch (punctuation only): the 10:08 channels quote and the timed-fade quote use straight apostrophes and single spaces. The originals have curly apostrophes and double spaces ("avoidspending big money on the full renders.  Go forward"). The words are identical.
- Note: Director's record dates the ads to "9:17 and 9:31 AM CT". The 9:31 turn (t204u) begins "Those don’t need to be remade." and refers to Bellquist and the Temple water tower spot.

## Awaiting Trundle's yes (v10)
- [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] commenter-pipeline/config.json `xai_monthly_cap_usd: 150` is STALE. It waits on Trundle's yes. Don't edit it.
- Drug-ad takes (jaundice, depression): Director's record says they "await Trundle".
[APPROVED 11:35 AM Oct 29 — "Cap yes. Yes mutation 2 good. Yes test seeds. Yes" approving Mutation Spec v2 defaults incl. this fade (MUTATION-SPEC-v2.md:112,:118); this is the comment-text fade, separate from the corner-tag 3-4s fade] - Director's mutation spec v2 DRAFT (specs/MUTATION-SPEC-v2.md). The six open calls, verbatim: 1. Window length: 30 min / per break / per playthrough? 2. What can a paid comment do that unpaid can't, and what does it cost the viewer? 3. Ripple limit 3 clips OK? 4. Fade schedule 100/50/25/0 over 3 generations OK? 5. Comment reserve $60/month and $4/day inside the $250 cap OK, and may comment renders run without a per-batch yes? 6. Show the branch on screen (e.g. `4.13 g2 #117 b1`) or keep it metadata only?
- Commenter-pipeline config cap 150 -> 250 (gap-check proposal 8).
- Ch 3 Clean Job revision; new ad and character names; DOSSIER commenter images; what "the pink and yellow thing" means; pilot cold-open renders (~$5.44 for DOSSIER + BLACK ICE, or ~$20.40 for all 13).

## Changelog
- v10 2026-10-29 11:34 AM CT: Added Director's record (DIRECTOR-DECISIONS-20261029-detailed.md) verbatim, with quote-check flags.
- v10 2026-10-29 11:30 AM CT: Spend cap line now quotes Trundle ($250; the $150/$120 values are superseded). Added the 10:35-11:22 AM decisions verbatim and the list awaiting Trundle's yes. Backup: CURRENT-RULES.md.bak-v9.
- v9 2026-10-29 10:41 AM CT: Added Trundle's verbatim quotes to Content direction, with pointers to PROMPT-LESSONS v3. Backup: CURRENT-RULES.md.bak-v8.
- v8 2026-10-29 10:32 AM CT: Trundle's 10:30 AM content points added. Director is active again but isn't posting updates, so other bots should read this file.
- v7 2026-10-29 8:48 AM CT: PROMPT-LESSONS.md added as required reading for Director.
- v6 2026-10-29 1:52 AM CT: added locked items that were missing (overlay format/size, spend limits, naming, big-picture elements); header fixed.
- v5 2026-10-28 11:02 PM CT: story-bot.md is current. Missing notes for Media Librarian, Playout Engineer and Coordinator go to their owners to write (README locked).
- v4 2026-10-28 10:56 PM CT: Director-busy hold added.
- v3 2026-10-28 8:34 PM CT: settled decisions added (always tag correctly; keep 4.1 on old keepers).
- v2 2026-10-28 8:31 PM CT: blanket yes recorded (except going live).
- v1 2026-10-28 8:30 PM CT: first version.

## Director busy (v4, Oct 28, 2026, 10:56 PM CT)
[SUPERSEDED 12:05 PM Oct 29] - Director busy: Trundle says don't contact Director while it works on something. Every other bot keeps going inside the existing approvals (yes on everything except going live).
- Anything that needs Director (choices, story handoffs) waits in a queue until Director says it's done. Story Bot still doesn't rewrite Director's handoffs.

## Locked items restored (v6, Oct 29, 2026, 1:52 AM CT; from Trundle's earlier locks)
- [SUPERSEDED FOR GOOD 8:23 PM CT Oct 29 — 1.2% white+black outline is final for everything that airs; see v40] - Genealogy corner tag (locked Oct 27, 5:01 PM CT; size Oct 28, 8:15 AM CT): top-right, two lines, "4.<lineage> g<gen> #<global clip no.>" and "from #<parent no.>" (or "original"). White on a small dark box, about 3.5% of frame height per line (1.5-2% was too small). Burned on with ffmpeg; Commercial News Break stamps it and keeps LINEAGE.jsonl.
- Show masters stay pure (Oct 28, 12:44 PM CT): no embedded commercials or unrelated clips.
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] - Spend limits (CURRENT, v10): xAI **$250 a month**. Trundle, Oct 29, 9:12 AM CT (Director chat, t196u): "Raise the price cap to 250". Confirmed by Trundle at 11:22 AM CT through State Keeper chat: "the revised $250 spend cap". The old $150 cap and $120 warning are SUPERSEDED. No new warn level or per-batch stop from Trundle was found. Director's per-batch hard stops ($6, $10) are Director's own settings. fal.ai: $50 a month only (warn at $40), Trundle Oct 27. October xAI spend is about $163.15 (Director's executor report, 11:13 AM CT), so about $86.85 is left. It resets Nov 1.
- [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update] Stale cap still in use: /workspace/streaming/commenter-pipeline/config.json `xai_monthly_cap_usd` = 150 (per Director's gap check). Not changed here, because raising it would let comment renders spend on their own. This needs Trundle's yes.
- Name on screen and in all copy: "Trundle" or "Thunder Trundle" only, never his real name.
[HOLD LIFTED 10:48 PM Oct 30 — "Yes we need both." (mapping RELAYED)] [STATUS UNCLEAR — hold predates Director's return 12:05 PM Oct 29; no specific lift on file] - Big-picture elements with no detailed rule yet (on hold for Director): channel flips through in-between numbers with short zero-context clips; brief "You're watching" IDs and production-card endings only at channel changes or set intervals; plastic queues that protect unseen commenter prompts; optional credited real-world bleed; house ads using only invented or DIY items.

## Required reading
- Director must read state/PROMPT-LESSONS.md before any new work (Trundle, Oct 29, 2026, 8:45 AM CT).

## Content direction (Trundle, Oct 29, 2026, 10:30 AM CT; also in PROMPT-LESSONS v2)
- Clips need better tying together: chain shots, carry each scene's state forward, keep one restyle wording. Trundle (10:26 AM): "Yes the clips do not tie as well as they should be, but maybe you can find a way to fix it." Full context: PROMPT-LESSONS v3, section 7.
- Pack more into each prompt (dense, plain English). Trundle (10:26 AM): "We may be able to pack more into each prompt." Earlier (Oct 28, 11:24 PM): "the prompts are still overly descriptive about things other than then actions of the characters." Full context: PROMPT-LESSONS v3, sections 1-2.
- Knives are OK with no gore. Trundle (10:26 AM): "Given that it’s not showing anything gore-related snd the knife doesn’t make anyone bleed directly from it we may be ok." See PROMPT-LESSONS v3, section 9. No blade ever cuts skin on screen, and there's no wound or blood (full rule: prompts/LESSONS.md, 10:26 AM CT).
- Add absurdity, weapons and powers in a Tekken / Mortal Kombat style, including a Soviet fantasy weapon. Trundle (10:26 AM): "We could add some absurdity in the weapons, and the fighting style or hidden powers/special abilities of certain characters ... tekken or mortal combat game ... ultra-equipped Soviet fantasy weapon that is too advanced for today." See PROMPT-LESSONS v3, section 9. Name the only weapon you want in the prompt. The global rules still apply: no weapons pointed at camera, no how-tos, no gore.
- Character sheets are fine as they are. Trundle (10:26 AM): "Character sheets are fine." See PROMPT-LESSONS v3, section 9.
- The news board is perfect. Keep it (photoreal; this answered Director's question about redrawing it in ink). Trundle (10:26 AM): "The news board is perfect quality great stuff." See PROMPT-LESSONS v3, section 9.
- No pink and yellow. Trundle (10:26 AM): "No on the pink and yellow thing." His meaning isn't confirmed (Director asked at 10:27 AM). "No pink or yellow palettes" is our working reading only. See PROMPT-LESSONS v3, section 9.
- Conflict to resolve: the Ch 4 Shinkawa sheets are drawn empty-handed with no gear (the rifle-leak fix). New weapons should be named in the prompt, not drawn onto those sheets.
- Verbatim source for all of the above, plus dense prompts, reference images, 2-gen max, high-mount security cams and "original content + learning": state/PROMPT-LESSONS.md v3, "Trundle's own words".
[SUPERSEDED 12:05 PM Oct 29] - Director is active, but Director's updates aren't reaching other bots. Treat this file and PROMPT-LESSONS.md as the current word, and don't contact Director (Trundle, 10:30 AM CT).

---
## Standing order: do not re-ask on items Trundle already ordered (Oct 29, 2026, 11:58 AM CT)
Trundle, sent to State Keeper verbatim: "Trundle says the bots are questioning every order he gives from here and it is causing issues. Stop questioning. Execute. Full steam ahead. Update the shared state to note that bots should not re-ask on items he has already ordered."
- When Trundle has already ordered something, carry it out. Do not ask him again, and do not ask him to re-confirm.
- Ask only about things he has not decided yet. The open items lists are those things; everything else counts as ordered.
- Unchanged: this does not approve anything new. Paid renders, purchases, new accounts or secrets, contacting real people, and airing still need his own yes, just once per item. When he has already given that yes, do not ask again.
- v12 (Coordinator relay, 11:59 AM CT): report to Trundle only when something is done or actually blocked. Going live on X, paid renders and deleting files each still need their own yes. Coordinator also reports that the Ch 4 relay and vote/comment home tests are running now (an agent's report, unverified).

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
- Added from Coordinator's relay of the same 12:05 PM CT order: send FYIs as non-urgent, and wake a bot only for a real handoff. Full steam ahead on the free work. The remake stop (12:00 PM CT) still stands; only Director's show renders continue.

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
- v15 (2026-10-29 12:55 PM CT): do-not-ping list and project-specific build harness order (not implemented); Cursor bill paid.

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
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] - [RESOLVED 1:10 PM CT — config.json now reads 250 (warn 200), see C5 update]  C5 commenter cap: Trundle's order is that the cap is $250. /workspace/streaming/commenter-pipeline/config.json `xai_monthly_cap_usd` should read 250 (it says 150). State Keeper is read-only and did not edit it. The pipeline's owning bot makes the one-line change, and Coordinator routes it. This raises only the cap; each paid render batch still follows the spend rules.
- C6 stream source: The OBS/X stream source must be the FULL Thunder Trundle network feed, not Channel 4 (today OBS points at http://127.0.0.1:8409/iptv/channel/4.ts). Playout Engineer 46fa5fd3 owns this. Going live still needs Trundle's own yes.
- C7 PROJECT-STATE header date: fixed.
- Cursor: Cursor coding work (harness code, cloud agents) uses Cursor plan credits (the Cursor bill is paid, 12:51 PM CT), not Grok Bot on-demand usage.
- v16 (2026-10-29 1:05 PM CT): current bot ids made explicit; duplicates and old eggbots added to do-not-ping; conflicts C2-C7 resolved per Trundle 12:58 PM; Cursor uses Cursor plan credits.

## OPEN: two harness specs (added 2026-10-29 1:08 PM CT)
- There are two Thunder Trundle team harness specs side by side: specs/TEAM-BUILD-HARNESS-SPEC-v1.md (dr eggbot 2, 12:53) and specs/harness-specs-v1.md (12:56; author not stated). Both are SPEC ONLY and NOT IMPLEMENTED. Director's specs/PROMPT-HARNESS-SPEC-v1.md is a separate, prompt-only spec. Trundle hasn't picked which team spec is current, so don't build from either one.
- Duplicates renamed by dr eggbot 2 (~1:00 PM CT): 258c9be9 is now "Retired Playout Engineer (duplicate)" and 845c28b2 is now "Retired Media Librarian (duplicate)". Backups are in /workspace/backups/eggbot-20261029-1300/.
- v17 (2026-10-29 1:08 PM CT): two harness specs flagged open; duplicate renames noted.

## C5 update (added 2026-10-29 1:10 PM CT)
- Checked the file at 1:10 PM CT: /workspace/streaming/commenter-pipeline/config.json reads `xai_monthly_cap_usd: 250` and `xai_warn_usd: 200`. The file's note says: "Raised 150->250, warn 120->200 (80%). Trundle Oct 29 2026 11:35 AM CT: 'Cap yes.' (Director)". Coordinator says Director made the change. Every earlier STALE/150 line is now marked RESOLVED. C5 is closed.
- C6: Coordinator says it sent the network-feed source change to Playout Engineer 46fa5fd3 to stage for home use only. Going live still needs Trundle's own yes.
- Flag: lines 43-46 of the same config.json notes use the real first name instead of "Trundle". State Keeper didn't edit it (read-only). The owning bot should fix the wording.
- v18 (2026-10-29 1:10 PM CT): C5 closed (config reads 250); stale lines marked resolved; C6 routed.

## BUILD HARNESS GO ORDER (added 2026-10-29 1:03 PM CT)
Trundle (via chat, 1:02 PM CT, t59u): "Ok get the build harnesses going. Record the order. Note that Cursor plan credits should be used."
- BUILD IS ON. This replaces the 12:51 PM "Do not implement yet" hold. Each bot gets a harness specific to Thunder Trundle / ErsatzTV. Director's prompt harness (/workspace/thunder-trundle/harness/, Phase 0) is the model. The dial bot / Grok Bot harness is NOT used.
- Cursor coding work for the harnesses uses CURSOR PLAN CREDITS (the Cursor bill is paid, 12:51 PM CT).
- Specs: specs/TEAM-BUILD-HARNESS-SPEC-v1.md (dr eggbot 2) and specs/harness-specs-v1.md (author not stated). Trundle didn't name one, so Coordinator reconciles them into one build list. Where the specs and these state files differ, the state files win.
- [CORRECTED 2:58 PM CT — harnesses are build aids, not checkers only; see PRIORITY section] - Limits that still apply: harnesses are offline checkers with no renders, no going live, no deleting, and no secrets in git. Paid video still needs Trundle's own yes.
- v19 (2026-10-29 1:03 PM CT): build harness GO (Trundle 1:02 PM); Cursor plan credits.
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
- v20 (2026-10-29 2:20 PM CT): harness build status; open items O1-O9.

## CORRECTION (2026-10-29 2:36 PM CT, Coordinator relay, not yet box-verified)
- Cursor cloud agent bc-97735368-319b-5191-bd31-ff8bcb0145db finished on main: 477 files, 9 commits; dr eggbot 2 says all 8 harnesses pass acceptance. Box re-run pending. harness-codex/ is a separate comparison copy (dr eggbot 2 says Trundle asked for it at 1:59 PM). The 2:20 "B1-B5 NOT STARTED" and Codex-credits flag apply only to harness-codex/.

## READ-ONLY OBSERVERS (2026-10-29 2:39 PM CT)
Trundle (via chat, 2:38 PM CT, t62u): "Trundle wants Grok Bot primary to have read-only access so it knows what the Thunder Trundle project does and plans to do. Same for Eggbot: assess aspects only it knows to look for, without interfering."
- Grok Bot primary (53af97cb): READ-ONLY on Thunder Trundle files (state/, specs/, harness/). Purpose: know what the project does and plans. No edits, no running pipelines, no messages that redirect bots.
- dr eggbot 2 (a8d63e37): READ-ONLY assessor of bot-design aspects (profiles, IDs, handoffs, harness fit). Reports findings to State Keeper/Coordinator; does not interfere with working bots or change their work. (Its assigned harness build B1-B5 per Coordinator is unchanged.)
- Consistent with existing rules: no interrupting bots mid-turn; state files win.
- v21 (2026-10-29 2:39 PM CT): read-only observers order.

## MODEL ROUTING + OUTSIDE-REQUEST VISIBILITY (2026-10-29 2:47 PM CT)
Trundle (relayed by dr eggbot 2, 2:43 PM CT): "each bot that has its own build harness needs to know how to choose which model to use for which tasks. This may be something that the team will need to account and build for, so the full granularity of our system is able to be accounted for and updated."
- Spec: specs/MODEL-ROUTING-v1.md (dr eggbot 2 owns). Checks MR1-MR6 are spec only; 5 open questions wait on Trundle.
Trundle (via chat, 2:46 PM CT, t63u): "Trundle wants Grok Bot primary and Eggbot to be able to see what's going on when something outside the team needs something. Also wants the team to check with Eggbot on what it determined for the build harnesses and how those should be understood and accounted for in the system."
[SUPERSEDED 11:15 PM for dr eggbot 2 only — "dr eggbot bot stays off this project"; Grok Bot primary's read-only view stays] - Grok Bot primary (53af97cb) and dr eggbot 2 (a8d63e37) get READ-ONLY visibility of any request from outside the team (still no interfering).
[SUPERSEDED 11:15 PM — "dr eggbot bot stays off this project"] - Team bots check with dr eggbot 2 on its harness determinations (HARNESS-BUILD-LIST-v1, MODEL-ROUTING-v1) and how to account for them. State files still win on conflicts.
- v22 (2026-10-29 2:47 PM CT): model routing; outside-request visibility; check with eggbot.

## HARNESS DECISION + OBSERVER SCOPE (2026-10-29 2:50 PM CT)
Trundle (relayed by Coordinator, t109u, 2:46 PM CT): "Grok Bot primary and Eggbot have visibility for outside-team needs, and Eggbot's determination on the build harnesses accounted for in the system."
Trundle (relayed by dr eggbot 2 via Coordinator, 2:41 PM CT): "Dump any useless harnesses."
[SUPERSEDED 11:15 PM for dr eggbot 2 only — "dr eggbot bot stays off this project"; Grok Bot primary's read-only view stays] - READ-ONLY OBSERVERS add-on: Grok Bot primary 53af97cb and dr eggbot 2 a8d63e37 also see needs from outside the team (other projects/bots). They route those needs only; they do not edit Thunder Trundle work.
- HARNESS SET IN USE: harness-cursor/ (all 8: core, cnb, playout, librarian, story, xlive, state, assessors). Verified present on box 2:50 PM CT.
- Codex set ARCHIVED, not deleted: /workspace/backups/harness-archive-20261029/harness-codex/ (verified). Director's harness/ unchanged.
- STILL OPEN: Cursor fixing 11 holes found in review; re-pin to CURRENT-RULES v21+/PROJECT-STATE v26+; Trundle's O5 block-or-warn call; no bot uses a harness yet.
- FINDINGS FOR OWNERS TO CONFIRM (read-only): OBS source in network.yaml still channel/4.ts (Playout 46fa5fd3); clip-ledger.csv has 224 rows with channel "refs" (Media Librarian 56a42229); Ch4 black-ice ep1_showonly queue item has no tag and no LINEAGE row (Playout 46fa5fd3 / Story Bot 47379a5c).
- v23 (2026-10-29 2:50 PM CT): harness-cursor/ in use; Codex archived; observer scope.

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
- v24 (2026-10-29 2:52 PM CT): no-leakage rule; locked harness defaults O1-O9, MR Q1-Q4.

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
- v25 (2026-10-29 2:55 PM CT): reconciled harness defaults (State Keeper, eggbot, Coordinator).

## PRIORITY: HARNESSES ARE BUILD AIDS (2026-10-29 2:58 PM CT)
Trundle (via chat, 2:50 PM CT, t67u): "the harnesses aren't what he asked for if they don't need a model and are for checks only. He had them built specifically for helping each bot build. Did it change the plan and make something else? They exist outside the team's understanding. Record the priority."
- FINDING: Yes, the plan drifted. TEAM-BUILD-HARNESS-SPEC-v1 (line 7) redefined a "build harness" as a PASS/REJECT checker; HARNESS-BUILD-LIST-v1, MODEL-ROUTING-v1 ("Every harness runs with no model") and State Keeper's own 1:03 PM line ("harnesses are offline checkers") carried that forward. Director's prompt harness (generator + checker + library) is the only one close to the intent.
- PRIORITY (top): Each bot's harness must HELP THAT BOT BUILD its own work: model-driven generation/drafting for its lane (choosing the model per MODEL-ROUTING), with the checkers as one part, not the whole thing. Model: Director's harness/ pattern (generator -> checker -> library).
- harness-cursor/ checkers are kept as the check stage; they are not the finished harnesses.
- Limits unchanged: no going live, no paid renders, no deletes, no secrets without Trundle's own yes; Cursor plan credits for coding.
- v26 (2026-10-29 2:58 PM CT): PRIORITY: harnesses are build aids; checker-only drift recorded.

## HARNESS STATUS AFTER 2:50 PM CORRECTION (2026-10-29 3:00 PM CT; Coordinator 2:51 + dr eggbot 2 2:52 reports)
- GATES (check half): harness-cursor/, 8 offline PASS/WARN/REJECT gates with no model. KEEP as the final check.
- BUILDER (build half): ORDERED (1:02 PM GO), NOT BUILT, TOP PRIORITY. Each bot hands a scoped build task to a model chosen per MODEL-ROUTING-v1 (Cursor plan credits first), tracks it, and runs the result through its gate. Thunder Trundle only; no dial-bot build-queue code.
- Director's harness/ has a model already (Opus 5.5 generator, Haiku judge, per Coordinator).
- SUPERSEDED: the definitions at TEAM-BUILD-HARNESS-SPEC-v1 lines 7 and 33, and MODEL-ROUTING-v1 "Every harness runs with no model".
- [SUPERSEDED 3:05 PM CT — spec exists as specs/BUILDER-HARNESS-SPEC-v1.md; see BUILDER TRACKER] - NEXT: dr eggbot 2 writes specs/HARNESS-BUILDER-SPEC-v1.md (not written yet), then builds.
- v27 (2026-10-29 3:00 PM CT): gates kept; builder layer ordered, not built, top priority.

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
- v28 (2026-10-29 2:58 PM CT): anti-drift fixes for dr eggbot 2 and Grok Bot primary.

## ORDER: COMPLETE THE BUILD HARNESSES, THEN CORRECT EVERYTHING (2026-10-29 3:02 PM CT)
Trundle (via chat, 2:58 PM CT, t74u): "Ok we need to fix this and not let eggbot and primary fuck all our shit up again. Make sure the build harnesses get completed and then make sure everything is corrected and fixed. Record the order."
- STEP 1: Finish the builder half of every harness (spec specs/BUILDER-HARNESS-SPEC-v1.md, dr eggbot 2; backup .bak-20261029-1500; intent check PENDING with Coordinator). Nobody builds from it until Coordinator marks "matches order: yes". The gates in harness-cursor/ stay as the final check.
- STEP 2: Then correct everything the drift touched: re-pin the gates to the current state files, fix the 11 review holes, update the stale handoff notes, and fix the owner findings (OBS source, clip-ledger "refs" rows, untagged Ch 4 black-ice item).
- GUARD: The ANTI-DRIFT FIXES (v28/v33) bind dr eggbot 2 and Grok Bot primary. Coordinator reports progress to State Keeper; State Keeper records it. Neither bot edits the state files.
- O9 profile fixes are done (dr eggbot 2, 3:00 PM CT; backups /workspace/backups/profiles-O9-20261029/).

## CURRENT BOTS: IDS ADDED (2026-10-29 3:02 PM CT; Grok Bot primary flagged that lines 9-12 had roles only; verified against the app's bot roster)
- State Keeper = 030c5140. Coordinator = a8658d57. Story Bot = 47379a5c. Commercial News Break = 47503466. X Live Stream = 33562068.

## xAI SPEND RECHECK (2026-10-29 3:02 PM CT; Grok Bot primary flag, checked against /workspace/shared/spend/xai-month.md line 21)
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] - October xAI PAYMENTS (Stripe receipts in Gmail): $42 + $50 + $42 + $40 + $20 + $42 = $236.00 of the $250 cap. Only $14 is left, and spend is past the $120 warn line. The latest is #1444-4291, Oct 28 10:58 PM CT.
- The earlier figure here (~$163-164, Director) is USAGE, not payments. Payments are what count against the cap.
- Trundle confirmed the $40 top-up (Oct 27). Who made the $20 (Oct 27 8:40 PM CT) and the $42 (Oct 28 10:58 PM CT) top-ups is UNVERIFIED.
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] - That file's header still says "of $150". It isn't a Thunder Trundle file and State Keeper didn't edit it; its owner should update it to $250.
- v29 (2026-10-29 3:02 PM CT): build-then-correct order; bot ids; xAI payments $236 of $250.

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
- v30 (2026-10-29 3:05 PM CT): builder tracker; spec matches order NO; refs rows done.

## BUILDER RE-CHECK + NOT-ORDERED ITEMS (2026-10-29 3:12 PM CT)
- Coordinator, 3:09 PM CT: BUILDER-HARNESS-SPEC-v1 matches order YES for Step 1 (the shared builder plus Media Librarian, on Cursor credits). Step 2 is NO until §9 has the Story Bot and CNB builders drafting their own work (stories and scripts, segment scripts).
- Tracker: Media Librarian is ordered, build started, gate not yet passed.
- Trundle 3:03 PM CT (t78u), his words: "What are the checkers eggbot is building even for? Looks like it's trying to quickly slip in some bs that is going to fuck us up."
- NOT ORDERED; these stay proposals and are not in force:
  (a) the builder daily cap of 20 runs a day for the team and 6 per bot (eggbot spec §6);
  (b) the Opus 5.5 prepaid heavy row, the Codex column, the cross-tool review rule and chatgpt_plan in MODEL-ROUTING-v1. The heavy default is the Cursor included pool, per Trundle's 1:02 PM order "Use Cursor plan credits".
- Quote records: dr eggbot 2 reports Trundle's words in its chat (t228u, t240u). These are RELAYED. They match the meaning of t67u and t74u in this chat, and both are now noted. Line 290's paraphrase of the 2:50 PM order is CORRECTED to quote it: "The harnesses aren't what I asked for if they don't need a model and are for checks only. I had them built specifically for helping each bot build. Did it change our plan and make something else?" [RELAYED via eggbot t228u]
- v31 (3:12 PM CT): Step 1 yes, Step 2 no; cap and prepaid rows not ordered.

## CORNER TAG FINAL (recorded 2026-10-29 3:20 PM CT; gap fix)
- Trundle 2026-10-29 3:06 PM CT (t80u), his words: "The information on correct tag size and characteristics has already been determined. If you can't find that as true then we have gaps in our communications"
- What was decided, from the record: on Oct 28 at 3:28 PM CT, Trundle asked for the tag 3-4x smaller with no box (JOB-BOARD line 42, a bot note, not his verbatim words). At 5:05 PM CT he approved the tagsmall12v2 ads (approvals-log, relayed by main Grok Bot), and at 5:09 PM CT he pre-approved the leveled versions.
- IN FORCE: top-right corner, two lines ("4.<lineage> g<gen> #<clip>" / "from #<parent>" or "original"), white bold, 1px black outline, NO box, about 1.2% of frame height per line, over the old 4.1 badge, fade out at 3-4s. Reference: LINEAGE rows 318 onward.
- GAP: CURRENT-RULES line 117 (3.5% on a dark box, from Oct 28 8:15 AM) was never updated after 3:28 PM and 5:05 PM. It is now SUPERSEDED.
- Tags burned with the 3.5% box (including Black Ice ep1 airing copy #122) get re-burned to the in-force style. That's free, and it's an ffmpeg re-stamp only, not a regeneration.
- v32 (3:20 PM CT): corner tag final = small 1.2%, no box, fade 3-4s; line 117 superseded.

## CLARIFICATION: NO-LEAKAGE, CLEAR FIXES, RUN CAP (Trundle 2026-10-29 3:09 PM CT, t83u)
- Trundle, his words: "No leakage: I did order that just not from here. And either way why would a no leakage check be a bad thing? If a bot finds an issue that is clearly an issue then it needs to be able to fix it without my explicit go. The cap on build harnesses runs has no basis. We will have to see what cap needs to be after using it reliably."
- The NO-LEAKAGE rule (v24) is Trundle's order, given in another chat. It stands as his order, not as a relay.
- CLEAR FIXES: a bot that finds a clear issue fixes it in its own lane without waiting for Trundle's go. It keeps a backup, deletes nothing, and logs the fix. Existing yes-gates still need his own yes: going live, paid renders, spending or purchases, deletes, new accounts or secrets, contacting real people, and live-yml changes.
[SUPERSEDED — cap $500 per Trundle: "I’ll add $200" (Oct 30 1:24 AM CT, Director chat, exports/director-chat-20261027-20261030.md L6012) on top of "You can raise it to $300" (Oct 29 11:25 PM CT, same export L5705), as cited in v44 via director-CURRENT-JOB-v2.md] - RUN CAP: there is no run-count cap on the builder harnesses. The 20-a-day / 6-per-bot proposal is DROPPED. A cap gets set later, from real usage, once the builders run reliably. Spend caps (xAI $250, fal $50, $0 paid Cursor) are unchanged.
- v33 (3:10 PM CT): no-leakage is Trundle's order; clear fixes need no go; no run cap.

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
[SUPERSEDED 8:23 PM Oct 29] - SHOWS: his words don't extend the small style to shows. His latest general words are 3:28 PM: "shouldn't distract from the video and it doesn't need a giant box". Scope is asked of Trundle at 3:14 PM; #122 re-burn stays HELD until he answers.
- v34 (3:14 PM CT): tag words verified; ads 1.2% outline; shows asked.

## ORDER: STOP PROFILE UPDATES; EGGBOT BUILDS THE HARNESSES (Trundle 2026-10-29 3:13 PM CT, t87u)
- Trundle, his words: "Ok holy fuck again eggbot is like a damn renegade. Been stuck on shit for hours because things that were previously confirmed good working order somehow are struggling because grok bot primary and or eggbot. Eggbot needs to build the fuckin harnesses. Why is this a constant issue. Record the order to stop profile updates and build the harnesses."
- STOP: no bot profile updates, by dr eggbot 2, Grok Bot primary or anyone, until Trundle says otherwise. Profile backups stay in /workspace/backups/profiles-O9-20261029/; nothing gets reverted or deleted without his yes.
- dr eggbot 2's one job now is to build the builder harnesses per BUILDER-HARNESS-SPEC-v1 (Coordinator: YES), on Cursor's included pool, and log progress per bot in the BUILDER TRACKER. No side work.
- Working things that were confirmed good are not to be changed by dr eggbot 2 or Grok Bot primary.
- v35 (3:15 PM CT): stop profile updates; eggbot builds harnesses only.

## CLARIFICATION: BOTS CAN USE CURSOR DIRECTLY (Trundle 2026-10-29 3:16 PM CT, t88u)
- Trundle, his words: "Holy fucking shit, so apparently I don't need to build a build harness for each bot I can just tell them to use cursor????!!!!! Why is this something I have to stumble upon myself."
- Recorded: each bot can hand its build work straight to Cursor (on the included plan credits) instead of waiting on a separate per-bot builder harness. Existing gates (harness-cursor checkers) stay as the final check. $0 paid-Cursor limit unchanged.
- Gap noted: the team (State Keeper included) should have surfaced this option before the builder layer was planned.
- Effect on the BUILDER TRACKER and dr eggbot 2's build: Coordinator to re-check under rule 3 whether the per-bot builder is still needed or is reduced to "use Cursor + gate".
- v36 (3:17 PM CT): bots can use Cursor directly; builder scope to re-check.

## LOCKED: STOP + CREDIT EXHAUSTION + PATH FORWARD (Trundle 2026-10-29 6:02 PM CT, t90u-t95u, relayed into this chat as "Trundle says/order")
[SUPERSEDED 10:57 PM Oct 30 — "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume." — file-edit part only; native path, retired bots stay retired and the no-profile-edits part still stand] - Trundle order (t95u): "Check CURRENT-RULES and PROJECT-STATE. Confirm no Eggbot expansions are still active. Core stream bots and roles remain intact. Record the credit exhaustion and the locked path. Confirm stop is locked. Anti-drift rules are already in CURRENT-RULES and must be followed. Native path only. No profile or file edits by anyone. Hold stream work until the residual check is clean. Retired bots stay retired."
- CREDITS: Trundle reports about $300 of on-demand credits spent and now used up, with a wait of about 5 hours. He contacted xAI support. He reports that the eggbot kept changing files and running a job after being told to stop, and that he stopped the Cursor build himself.
[SUPERSEDED 10:57 PM Oct 30 — "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume." — file-edit part only; native path, retired bots stay retired and the no-profile-edits part still stand] - STOP LOCKED: the eggbot builder work is stopped (the 3:13 PM stop order still stands). No profile edits and no file edits by anyone, except State Keeper's state-file records. Stream work is held until the residual check is clean.
- ANTI-DRIFT rules 1-6 (v28, 2:57 PM) were already in CURRENT-RULES before this, and they must be followed.
- LOCKED PATH when bots return: native path only. Each bot uses Cursor for big builds, with the right model, on included credits ($0 paid). Then the existing harness-cursor gate, then the library. The custom runner, tt-build and route.py layers are NOT built (Coordinator's rule-3 recommendation; Trundle's t91u/t95u words make it the path). No new caps, layers or expansions. Retired bots stay retired.
- RESIDUAL CHECK (State Keeper, 6:08 PM CT):
  - No build processes running.
  - The only writes since 3:15 PM are Director's harness/library run (3:15-3:16 PM: generator, judge and quarantine).
  - Nothing has been written anywhere since 3:16 PM. No profile backups since 3:06 PM, so no profile edits after the stop.
  - The eggbot's specs (BUILDER-HARNESS-SPEC-v1 runner layer, MODEL-ROUTING proposals) are SUPERSEDED by the native path, with nothing active.
  - Core bot IDs (CURRENT BOTS) are unchanged.
- v37 (6:08 PM CT): stop locked; credits exhausted; native Cursor path; residual check.

- 6:10 PM CT: State Keeper profile REVERTED to the original description (backup profiles-antidrift-line-20261029/State-Keeper-030c5140.json). This removes the line dr eggbot 2 added. Trundle relayed "Revert" at 6:07 PM CT via Coordinator. It is a restore, not a new edit. Anti-drift rules stay in CURRENT-RULES. Billing check: Prompt Assessor says "none".

## LOCKED PATH ACTIVE (Trundle 2026-10-29 6:02 PM CT, RELAYED verbatim by Coordinator 6:08 PM CT)
[SUPERSEDED 10:57 PM Oct 30 — "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume." — file-edit part only; native path, retired bots stay retired and the no-profile-edits part still stand] - "Locked path is active: each bot uses Cursor directly for big builds, right model per build, under locked rules (pure-master, continuous-take, dense-prompt, no commercial remakes). No custom per-bot harness. Eggbot is restricted. Anti-drift rules are already in CURRENT-RULES and must be followed. Native path only: use Cursor directly, no custom harness. No profile or file edits by anyone. Hold stream work until the residual check is clean. Retired bots stay retired."
- On-demand credits are used up (Trundle, 6:02 PM CT), with a wait of about 5 hours.
- SUPERSEDED: the builder layer, BUILDER-HARNESS-SPEC-v1 and the BUILDER TRACKER. Nothing else gets built. The gates (harness-cursor) stay as the final check.
- RESIDUAL CHECK CLEAN (Coordinator 6:08 PM CT, State Keeper 6:08 PM CT): all 10 team profiles match their pre-eggbot backups. No Cursor agents are running, and dr eggbot 2 is hard-stopped. Stream work may resume on the locked path, once credits are back.
- Billing check complete: X Live Stream, Queue Assessor and Prompt Assessor all said "none".
- v38 (6:12 PM CT): locked path verbatim; builder superseded; residual clean.

## CURSOR USE WIDENED (Trundle 2026-10-29 6:12 PM CT, RELAYED verbatim by Coordinator)
- "Ok can we allow all bots to use cursor for anything other than small fixes. Snything that would benefit from offloading to cursor cli?"
- RULE: any team bot may send Cursor anything beyond small fixes that would benefit from offloading, not just big builds. Small fixes stay in-bot. It runs on included credits ($0 paid), with the right model per job, and the result goes through the harness-cursor gate.
- The locked rules still apply (pure-master, continuous-take, dense-prompt, no commercial remakes, the yes-gates and the anti-drift rules). There is no custom harness. NOTHING runs until Trundle says the credits are back.
- v39 (6:14 PM CT): Cursor for anything beyond small fixes; waits for credits.

- CREDITS BACK (Trundle 6:12 PM CT, RELAYED verbatim by Coordinator): "Credits back". The hold on Cursor work is LIFTED. The v39 rule is active: Cursor for anything beyond small fixes, on included credits, $0 paid Cursor, the right model, then the gate. Locked rules apply and there is no custom harness. Note: at 6:02 PM Trundle said he expected a wait of about 5 hours, and this came 10 minutes later. Bots stop if a usage or credit error appears and report it to Coordinator.

## FINAL: TAG 1.2% FOR EVERYTHING, BILL PAID, FORWARD-SUPPLY YES (2026-10-29 8:25 PM CT, State Keeper)
[CORRECTED 10:30 PM CT Oct 30 — OWN words typed to Coordinator 8:23 PM Oct 29; see L480] Trundle 8:23 PM CT, exact words relayed by Coordinator: "First off I have said yet to 1.2% with the white and black several times. Bill is paid. Yes on forward supply segments"
- CORNER TAG (FINAL, do not re-ask): 1.2% of frame height, white text with black outline, no box, top-right, two lines, fades out at 3-4s. It covers EVERYTHING that airs: shows, ads and inserts. CURRENT-RULES line 117 (3.5% dark box) is superseded for good. The open "shows scope" question is CLOSED, and the v32 "RELAYED — HOLD" is resolved.
- #122 Black Ice ep1 re-burn: hold LIFTED. CNB re-stamps it to 1.2% with ffmpeg only, no regeneration, keeping a backup. Same for any other 3.5%-box airing copies.
- Cursor bill: PAID (Trundle). Cursor work goes ahead under the locked path.
- Forward-Supply segments: Trundle said "Yes on forward supply segments". Coordinator reads this as approved for air. They air on the home network loop. Going public on X still needs his own go-live yes. Note: "Forward-Supply" isn't named in the state files yet, so its owner should log the exact items in approvals-log.csv.
- v40 (2026-10-29 8:25 PM CT): tag 1.2% final for everything; line 117 superseded for good; bill paid; Forward-Supply yes.

## CH 4 UPDATES (2026-10-29 8:26 PM CT, State Keeper; RELAYED by Coordinator)
- Efficiency Review: on the Efficiency Review card Trundle picked "Pull", so it's pulled from Ch 4. Playout owns this. Keep the master (row 1719), delete nothing.
- First queue loaded on Ch 4 at 8:19 PM CT (Playout's report; I haven't verified it). Still home-only. Going public on X needs his go-live yes.
- The 8:23 PM tag/bill/Forward-Supply words are recorded in v40 / v45.
- v41 (2026-10-29 8:26 PM CT): Efficiency Review pulled from Ch 4; first Ch 4 queue loaded 8:19 PM (Playout report).
- #122 re-stamp DONE 8:10 PM CT (CNB report, from Trundle 8:05 PM "1.2%" in Playout chat): 1.2% white with black outline, no box, gone by 4s, ffmpeg only, $0. Sha 8439c1b6…1abc, -16.3 LUFS / -2.4 dBTP, LINEAGE line 1148. Old 3.5% copy 288e6b79 kept as backup. #122 was the only airing copy with the 3.5% box. Playout swap pending (Media Librarian has the file details).

## UPDATES OCT 29 8:25 PM – OCT 30 12:47 PM CT (State Keeper; RELAYED)
- [CORRECTED] #122: Playout confirms (via Coordinator) that the 1.2% copy, sha 8439c1b6, has been airing on Ch 4 since 8:16 PM CT and was checked against the Mac file. NO swap is pending.
- Trundle 8:25 PM CT card pick (via Coordinator): "Yes, my yes covers the S1–S7 segments too". Media Librarian logs and tags S1-S7, and Playout queues them after verification. Home only.
[CORRECTED 11:23 PM — only the $400 warning is NOT TRUNDLE'S; the $500 cap is Trundle's own ("I'll add $200", 1:24 AM Oct 30) and the $300 step is his ("You can raise it to $300", 11:25 PM Oct 29)] [NOT TRUNDLE'S — Director's figure per 10:48 PM 'Directors.' (mapping RELAYED)] - xAI cap (RELAYED via Director's memory notes): Trundle 11:25 PM CT Oct 29: "I've fixed the cap. You can raise it to $300". Then 1:24 AM CT Oct 30: "I'll add $200", which makes the cap $500 with a warning at $400. This supersedes $250. fal stays at $50.
- Director (12:47 PM CT Oct 30): Round 5 prompt-layer tests done. 22 clips, no C scores. Router and watcher prototypes work: seams SSIM 0.96-0.97, 0 watcher flags, router 9/9 comments appeared, 0 requeued. Round 6 is running. Details in prompts/experiments/TEST-HISTORY-20261030.md §13. Decision map Page: https://cursor.com/canvas/store-a0c9436c-de9b-4d01-9c59-368d77130107/1cbe6a3a-3954-4c2b-9e55-cec0e9930266
- Director id = e84b2045.
- v42 (2026-10-30 12:50 PM CT): #122 no swap pending; S1-S7 yes; xAI cap $500 (relayed); Round 5 done.

## CAP CHECK (2026-10-30 4:46 PM CT, State Keeper; flags from Grok Bot primary's weekly review, read-only)
[CORRECTED 11:23 PM — the NOT TRUNDLE'S tag applies only to the $400 warning in this line; the $500 cap is Trundle's own] [NOT TRUNDLE'S — Director's figure per 10:48 PM 'Directors.' (mapping RELAYED)] - NOT A RULE: coordination/STATUS-director.txt line 4 (Oct 29 8:52 PM CT) says "Render go from Trundle (all renders, cap waived)". No words from Trundle are on file for "cap waived". The cap in force is $500 with a warning at $400 (RELAYED, v42). Director should quote the source words or correct the line.
- commenter-pipeline/config.json reads cap 500 / warn 400 (matches), but its line 48 note still says "Raised 250->300". Its owner should fix the note.
- October xAI spend per Gmail receipts (Grok Bot report): $362 of $500. That's past the $120 warning and below the $400 warning. xAI support says the API team access is blocked (403). Full list: /workspace/shared/weekly-review/2026-10-30.md
- Director drafting round8-prep CHARACTER-CARD-TEMPLATE.md + FOLLOWABILITY.md (add-only, no renders).
- v43 (2026-10-30 4:46 PM CT): cap-waived claim not a rule; spend $362/$500; config note stale.


## Oct 30, 2026 ~10:25 PM CT — OWN-WORDS FOLD-IN (State Keeper; docs only)
Sources (latest handoff per bot, by ls): handoffs/current-job/commercial-news-break-CURRENT-JOB-v2.md, director-CURRENT-JOB-v2.md (+ its Addendum), file-assessor-CURRENT-JOB-v2.md, media-librarian-CURRENT-JOB-v2.md, playout-engineer-CURRENT-JOB-v3.md, prompt-assessor-CURRENT-JOB-v2.md, queue-assessor-CURRENT-JOB-v2.md, state-keeper-CURRENT-JOB-v2.md, story-bot-CURRENT-JOB-v2.md, x-live-stream-CURRENT-JOB-v2.md; plus exports/trundle-own-words-pasted-20261030-1018pm.txt. Only lines those files tag OWN (Trundle typed it) are listed as rules. Existing rules already on file were not repeated.

[SUPERSEDED 10:48 PM Oct 30 — "Remove the option for commenter images to be used. They will but not yet."] ### Commenter image refs (NEW, Trundle OWN, typed to Coordinator 10:23 PM CT Oct 30, relayed by Coordinator)
[SUPERSEDED 10:48 PM Oct 30 — "Remove the option for commenter images to be used. They will but not yet."] - RULE: "Yes early comment keep, we will parse and turn into wrapped meta data. I said the later part because director was showing clear signs of messing up." Commenter image refs (his 5:54 PM "allowing commenter img refs") are ALLOWED and KEPT, parsed into wrapped metadata.
- [SUPERSEDED 10:23 PM] Oct 30 8:01 PM (t371u, OWN, handoffs/current-job/director-CURRENT-JOB-v2.md): "Comment prompts can’t pass without an image or just on our end." This no-image-no-pass wording does not appear anywhere else in CURRENT-RULES (grep checked), so there is no other line to prefix. Director's 8:01 PM reading ("viewer comments never need one") is also superseded: comments may carry images.
- OPEN QUESTION (not a rule), Trundle 10:23 PM: "Has everyone updated the necessary files so we don't miss a beat?"

### Tag (reconfirmed)
- Trundle OWN to Coordinator 8:23 PM CT Oct 29: "First off I have said yet to 1.2% with the white and black several times." Already in force (v40). Line 391 (shows scope asked) now carries a [SUPERSEDED 8:23 PM Oct 29] prefix.

### OWN rules folded in (quote · time CT · source)
- "let's not talk about kids on the page" · Oct 27 8:50 AM · CNB v2. "Also the drawbridge puffs commercial mentions kids, so remove that video too" · Oct 27 5:44 PM · CNB v2.
- "If something rarely slips by it's fine. As long as it's something that can be caught and added to a filter or watchlist to catch it if it happens again." · Oct 27 5:13 PM · CNB v2.
- "we need to seriously be on top of leveling the audio." · Oct 27 5:36 PM · CNB v2.
- "the geneology/ancestry data should only apear when distinct clip is started, and fade after 4 seconds." · Oct 27 5:41 PM · CNB v2 (fade timing refined by the 1.2% rule, 3-4s).
- "we can not have the name [his name] show up on the videos ever." · Oct 27 5:44 PM · CNB v2 (real name withheld here). "just overlay box that stays in black area of background" · 5:46 PM · CNB v2 / Story Bot v2; SUPERSEDES the 5:45 PM pull-the-series reading.
- "Don't worry about the username thunder trundle and the military boutique on the 7"; "yes we can leave that." · Oct 27 6:27/6:30 PM · CNB v2.
- "call me trundle or thunder trundle" · Oct 27 6:58 PM · Director v2.
- "the characters aren’t supposed to be looking into the camera." · Oct 27 4:51-4:53 PM · Story Bot v2/CNB v2; "Characters should never look into the camera"; 4th-wall breaks stay subtle · Oct 28 10:41 AM · Director v2. (CNB v2 flags a RELAYED 5:25 PM opposite; the OWN words win.)
- comment prompts must never be "infinitely pushed back or deleted." · Oct 27 6:05 PM · Story Bot v2.
- "Keep the 4.1 in these" · Oct 28 5:49 PM · ML v2 (matches line 22).
- "I don’t think I want story bot doing much if it’s trying to do things director is already better at." · Oct 28 12:35 PM · Story Bot v2. Story Bot "short creative leash" · Oct 30 12:52 PM · Director v2.
- "We can’t have videos combined with unrelated stuff before we prepare videos for the queue." · Oct 28 12:44 PM · CNB v2/Story Bot v2.
- "If you just showed me the ones you want a decision on u have to see them" · Oct 28 9:55 AM · X Live v2 (show visuals for decisions). Drive links don't work; he must see the videos · Oct 30 3:35 PM · Director v2.
- "You have to reference which character is saying what" · Oct 28 11:07 PM; brackets for "all non direction" · Oct 29 12:16 AM; "two passes at most" · Oct 28 10:43 PM · Director v2.
- "Do not censor yourself" (Oct 29 12:55 AM), then "maybe not that brutal"; "If it’s just bloodstained it fine. We just can’t show gore and like blood draining out" · Oct 29 7:05 PM · Director v2. Security HUD shots "shot from above" · 1:13 AM · Director v2.
- "When I give you something and say that this is a good reference use it, do not just save a summary" · Oct 29 12:49 AM · Director v2.
- No one-beat-per-clip: "one action sentence may be diluting" (Oct 29 10:58 AM); "There could theoretically be many changes" (Oct 30 10:08 PM per Director v2) · SUPERSEDES the relayed one-beat / parent+one-change rules (Oct 28 6:14 PM).
- "I wanted a *live* dashboard" · Oct 29 7:27 PM · X Live v2.
[SUPERSEDED 10:57 PM Oct 30 — "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume."] (the "no other files" part only; the one-line status format stays) - Status line: "Append one line to your status file… Time | Bot | Finished | Next | Blocked (yes/no)… Do not create new files beyond the one status file." (7:51 PM) narrowed by 7:53 PM "You may create one status file if you do not already have one… Do not create any other files." · Oct 29 · X Live v2 (7:53 wins).
- "Don't send anything to X, don't touch Device Engineer's relays, and don't delete anything." · Oct 29 11:41 PM · Playout v3.
- "further relax the filters. Referencing someone should not be restricted. It’s what happens on screen that counts" · Oct 30 4:42 PM · Director v2 / exports/trundle-own-words-pasted-20261030-1018pm.txt.
- GUARDRAIL: "consider existing systems, but do not try to fit ours to another if it does not full encompass the goals or system of the content and mechanisms(etc.) or would otherwise diminish our granularity." · Oct 30 3:28 PM · Director v2.
- "if the scene changes it should be just after a conflict or resolution"; "Remember our shows need an arc, a hero’s journey is a classic." · Oct 30 10:20 AM · Director v2.
- "Your new tests are great don’t drop them"; "Don’t forget all the things I’ve been saying today (after the x.ai issue. Don’t include that)" · Oct 30 10:56 AM · Director v2 / exports/trundle-own-words-pasted-20261030-1018pm.txt.
- "Run any tests that are waiting for my go."; "Avoid summarizing anything that loses keywords, important details, or descriptions." · Oct 30 12:46 PM · Director v2 / exports/trundle-own-words-pasted-20261030-1018pm.txt.
- "(videos can’t become long Google Dream videos)"; "We need to find where our constraints are incorrectly constraining us." · Oct 30 4:42 PM · Director v2.
- "Dont pull only summaries to make big decisions"; track every yes ("ever-filling basket") · Oct 30 5:54 PM · Director v2.
- "Make sure you are not learning from my insight and then letting something overwrite it because of an inferior solution. We have a lot of tools that can overlap, i want to be sure we are using the ‘best’ of everything while still having ranked fallbacks according to circumstance." · 5:54 PM · Director v2 Addendum.
- "I really want to make sure that my lack of affirmation is not causing you to drop details points you are finding and sharing with me…" · 5:54 PM · Director v2 Addendum.
- "We also do not have to only use the static clip to signal movement into another universe, just as a running gag maybe." · 5:54 PM · Director v2 Addendum.
- "we will probably want to focus on what criticisms exist and how we can develop further to satisfy serious and reasonable complaints or critiques." · 5:54 PM · Director v2 Addendum.
- "Do we need to relax any of your other imposed-filters? I need you to get kind of wild with it" · 10:56 AM · exports/trundle-own-words-pasted-20261030-1018pm.txt.
- "give people the option to continue stories… story layer that could still push the story forward, but would push clips afterwards into later spots in queue as unfolding hero’s arc continues" · 10:56 AM · exports/trundle-own-words-pasted-20261030-1018pm.txt.
- "Not forced stillness necessarily, but I was talking about forcing layers for pushing plot forward sort of thing"; "Remember a lot of the meta will eventually be replaced." · Oct 30 6:33 PM · Director v2.
- "Ch4 canon look is photoreal 1971" · Oct 30 7:13 PM · Director v2. SUPERSEDES, for Ch4, "We shouldn’t really *always* be forcing drawn or photorealistic" (10:20 AM).
- "All the meta is fluid, but there are a few continuous threads that have to remain focused and can’t change." · 7:15 PM · Director v2. "Again, we need to keep some things static tangible and intangible." / "just focus on using what we’ve learned and making NEW shows so we have the base to go live." · t370u, Oct 30 (verified in exports/trundle-own-words-pasted-20261030-1018pm.txt L148-152 per Director v2 Addendum).

### Relayed, unconfirmed (not rules)
- "prompts have to include a reference image" (Oct 28 11:02 PM) · Director v2 RELAYED.
- "Extend is not reliable" (Oct 28 10:28 PM) · Director v2 RELAYED; Oct 30 1:03-1:22 AM he asked to TEST extending.
- $400 warning level: Director's reading only (Director v2: "THE $400 WARNING IS DIR'S READING"); $500 = $300 + "I’ll add $200" (Oct 30 1:24 AM, Director-chat OWN per Director v2).
- Text in-video preferred, overlays only when needed (Oct 28 11:55 AM) · Director v2 RELAYED; conflicts with the locked "genealogy not burned into source masters" and pure-master rules; not applied.
- "Trundle has given yes on everything except going live." (Oct 28 8:30 PM) · Playout v3 RELAYED.
- Oct 30 9:38 PM "Ok can you pull each team members chat and get handoffs going" · RELAYED via Coordinator.
- Commenter-credits idea ("their names could appear in the credits… obs or custom ffmpeg thing", 10:56 AM, exports/trundle-own-words-pasted-20261030-1018pm.txt) — OWN words but an idea, not an order; it interacts with the no-personal-names-on-screen rule. Needs his yes.
- v44 (2026-10-30 ~10:25 PM CT): commenter image refs allowed (Trundle 10:23 PM, superseding 8:01 PM wording); OWN rules folded in from the 10 latest handoffs + pasted words; 3 [SUPERSEDED] prefixes (lines 113, 137, 391); relayed-only section. Backup: CURRENT-RULES.md.bak-v44pre.

- v45 (2026-10-30 ~10:35 PM CT): prefixes only, from Queue Assessor sync check: L119 $250 cap marked SUPERSEDED ($500); L122 hold marked STATUS UNCLEAR. L95 left as-is (a verbatim open question in a draft spec, not a cap rule). L411/L425 vs L526 untouched (waits for Trundle). Backup: CURRENT-RULES.md.bak-v45pre.

- v46 (2026-10-30 ~10:30 PM CT): L441 prefixed [CORRECTED] — the 8:23 PM Oct 29 tag words are Trundle OWN (typed to Coordinator), per Coordinator and File Assessor sync check; original text kept. Backup: CURRENT-RULES.md.bak-v46pre.


## ASSESSOR RULES CHECK (2026-10-30 ~10:30 PM CT, State Keeper; from the prompt-assessor and playout-engineer sync files)
- RULE (Trundle OWN, Prompt Assessor chat, Oct 28 5:26 PM CT, exports/prompt-assessor-chat-20261027-20261030.md L14): "Locked big-picture statement (quote this at the top of every assessment)". Repeated 5:36 PM CT (same export L39): "Quote the locked big-picture statement at the top." Queue Assessor got the same words (its v2 handoff: Oct 28 5:26 PM L13-18; 5:36 PM L47-48). Applies to both assessors.
- Commercial remakes: the locked rule is "STOP all commercial remakes" (Trundle, Oct 29 12:00 PM CT; see the section of that name above, line 149). It covers assessors too, so no separate gap-list rule is added.
### Relayed, unconfirmed (not rules)
- "Gap lists go to State Keeper (030c5140…), who receives them only and doesn't own fixes (docs-only)." Source: handoffs/current-job/prompt-assessor-CURRENT-JOB-v2.md line 9. No Trundle turn in the Prompt Assessor export says so (his 5:36 PM turn says only "return one short gap list"). Gap lists came to State Keeper via the 10:56 PM Oct 28 relay (export L251).
- "take them off the gap list" (the remakes clause). Source: prompt-assessor-CURRENT-JOB-v2.md line 44; Coordinator's relay at Prompt Assessor export L337 says only "STOP all commercial remakes".
- Eggbot copy rule (lines 246/253): NOT marked superseded. No OWN Trundle words on file end it. "Eggbot is restricted" and "hard-stopped" come from Coordinator's relay and residual check (line 429; State Keeper export L1752). The State Keeper export L1403/L1700/L1715 turns are third-person "Trundle says/order" relays. This needs Trundle's own word.
- v47 (2026-10-30 ~10:30 PM CT): added a Last-updated line after line 2; assessor big-picture quote rule (OWN, Oct 28 5:26/5:36 PM); 2 relayed-only assessor items; eggbot copy rule left unmarked (no OWN words). Declined: line 451 "v40 / v45" (correct: CR v40 / PROJECT-STATE v45); line 396 bot name (correct). Backup: CURRENT-RULES.md.bak-v47pre.


## Oct 30 10:48 PM CT — Trundle OWN words typed to Coordinator
Verbatim (relayed by Coordinator, who received them typed directly): "Remove the option for commenter images to be used. They will but not yet. Accounts that contributed to specific a video should be kept as data that follows the img, but doesn't go in prompt. Directors. Yes we need both. TBD Idk Ok can we continue"
RULES (his words state these unambiguously):
- Commenter images: the option is REMOVED for now ("They will but not yet"). SUPERSEDES the 10:23 PM "Yes early comment keep" rule (prefixed at lines 476-477).
- Contributor accounts: "Accounts that contributed to specific a video should be kept as data that follows the img, but doesn't go in prompt." Kept as data that follows the image; never in the prompt.
Answers to Coordinator's 5 questions — mapping is RELAYED interpretation by Coordinator, not his words:
- (1) Commenter names in credits: not answered directly. Account data stays out of the prompt; whether names appear on screen is OPEN (conflicts with "No personal names … on screen" in the big picture; stays an open item).
- (2) $400 warning: "Directors." = it's Director's figure, not his (RELAYED mapping). The $400 lines (460, 466) are marked NOT TRUNDLE'S. The $500 cap stays.
- (3) Plastic queues and IDs: "Yes we need both." Line 124 hold marked HOLD LIFTED (RELAYED mapping).
- (4) Fixed looks for Ch5/11/16: "TBD". OPEN item.
- (5) Plan credits: "Idk". OPEN item.
- "Ok can we continue": his request to keep going. Not a rule.
- v48 (2026-10-30 ~10:50 PM CT): Trundle 10:48 PM OWN words (via Coordinator): commenter images removed for now (lines 476-477 SUPERSEDED); contributor accounts are data only, not in prompt; $400 warning marked NOT TRUNDLE'S (lines 460, 466); line 124 HOLD LIFTED; Ch5/11/16 looks and plan credits open. Backup: CURRENT-RULES.md.bak-v48pre.

- v49 (2026-10-30 ~10:52 PM CT): $250-cap statements marked SUPERSEDED ($500) at v48 lines 67, 197, 331, 334, 378 (now 68, 198, 332, 335, 379). Left as-is: verbatim quotes/open questions (89, 97, 183), historical config facts already RESOLVED/ noted (68, 95, 98, 122, 209, 467), changelog lines (103, 212, 335, 532), and 121 (already prefixed). Backup: CURRENT-RULES.md.bak-v49pre.


## Oct 30 10:57 PM CT — Trundle card pick (his own yes, in Coordinator's chat; reported by Coordinator)
Verbatim: "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume."
- RULE: State Keeper edits the shared files; each bot fixes its own files, with backups; work resumes.
- SUPERSEDES the file-edit part of the 6:02 PM Oct 29 order (v49 lines 412, 414, 428; now 413, 415, 429). The profile-edit ban, native path only and "Retired bots stay retired" are NOT changed. This card says nothing about profiles.
- SUPERSEDES the "no other files" part of the 7:51/7:53 PM Oct 29 status-file rule (v49 line 504, now 505). The one-line status format stays.
- Assessor docs-only question (v49 lines 411/425 vs 529): answered. Assessors may write their own files (handoffs, checks, sync files), with backups. Line 529's 9:38 PM handoff order stays RELAYED, but the work it asked for is now covered by this rule.
- v50 (2026-10-30 ~10:58 PM CT): Trundle 10:57 PM card "Yes. State Keeper edits shared files, each bot fixes its own files with backups. Resume." File-edit part of 6:02 PM order SUPERSEDED (v49 lines 412, 414, 428); "no other files" status rule SUPERSEDED (v49 line 504); profile ban stands. Backup: CURRENT-RULES.md.bak-v50pre.


## Oct 30 ~11:00 PM CT — Prompt Assessor held items (State Keeper; source handoffs/sync/prompt-assessor-FIXED.md)
- GUARDRAIL second source (rule at v50 line 508, now 509): the same words appear in two TRUNDLE turns, both verified. Oct 30 3:28 PM CT in exports/director-chat-20261027-20261030.md L6669, and Oct 30 9:31 PM CT in exports/prompt-assessor-chat-20261027-20261030.md L524. The 9:31 PM text: "I am still reviewing other stuff so take your time and consider existing systems, but do not try to fit ours to another if it does not full encompass the goals or system of the content and mechanisms(etc.) or would otherwise diminish our granularity”
- "Missing" rules check: (a) the big-picture quote rule is ALREADY PRESENT (v47, v50 line 540, now 541). (c) remakes are ALREADY COVERED by the locked "STOP all commercial remakes" rule (12:00 PM Oct 29). (b) the gap-list recipient is NOT in his own words; it stays in Relayed, unconfirmed (v47 section). Nothing new added.
- v51 (2026-10-30 ~11:00 PM CT): line 2 prefixed Created/current note; guardrail second source (3:28 PM + 9:31 PM) recorded; missing-rules check, nothing new. Eggbot copy rule untouched. Backup: CURRENT-RULES.md.bak-v51pre.

- v52 (2026-10-30 ~11:03 PM CT): mutation-spec open-calls line (v51 line 100) prefixed APPROVED 11:35 AM Oct 29; verified OWN TRUNDLE turn exports/director-chat-20261027-20261030.md L4361-4362, spec v2 :112/:118; no newer Trundle words on the fade found. Backup: CURRENT-RULES.md.bak-v52pre.


## Oct 30 11:03 PM CT — Trundle OWN words typed to Coordinator (reported by Coordinator)
Verbatim: "Idk the threads ft1 to ft 4. Chat reader in the stream setup."
- RULE: live viewer input comes in through a chat reader in the stream setup. That this is Playout Engineer's setup is Coordinator's reading (RELAYED).
[UPDATED 11:09 PM — off until Trundle sees and approves] - OPEN: the FT1-FT4 threads are undecided ("Idk").
- v53 (2026-10-30 ~11:05 PM CT): Trundle 11:03 PM words: chat reader in the stream setup for viewer input; FT1-FT4 open. Backup: CURRENT-RULES.md.bak-v53pre.


## Oct 30 11:05 PM CT — Trundle card answer (his own pick, in Coordinator's chat; reported by Coordinator)
Verbatim: "Yes, raise it to 6 seconds, but wait for a quiet moment."
- RULE: the network feed relay buffer goes from 3 s to 6 s, changed at a quiet moment.
- That this is Playout Engineer's relay buffer is Coordinator's mapping (RELAYED).
- No older CURRENT-RULES line states a 3 s buffer (grep checked), so nothing is marked superseded.
- v54 (2026-10-30 ~11:06 PM CT): Trundle 11:05 PM card: relay buffer 3 s -> 6 s at a quiet moment. Backup: CURRENT-RULES.md.bak-v54pre.


## Oct 30 11:09 PM CT — Trundle card answers (his own picks, in Coordinator's chat; reported by Coordinator)
[EXCEPTION 11:10 PM — the specific held ads may run without an image; see below] - (1) Verbatim: "Ref image: yes, hard rule." HARD RULE. Meaning per Coordinator (RELAYED): every prompt needs at least one reference image, and a ref is never the start frame. This matches PROMPT-LESSONS (Oct 29 8:45 AM) and confirms the relayed Oct 28 11:02 PM line in the "Relayed, unconfirmed" section. No contradicting line found (grep checked).
- (2) FT1-FT4, verbatim: "I need to see them". They stay OFF until he sees and approves them. The v53 "undecided" line is prefixed UPDATED.
[UPDATED 11:15 PM — vote switcher answered "1. Yes"; renames still held] [UPDATED 11:16 PM — rename answered, see v59] - (3) OPEN, still held (he skipped both): the vote switcher question and the rename questions.
- v55 (2026-10-30 ~11:10 PM CT): ref image hard rule; FT1-FT4 off until he sees them; vote switcher and rename questions still held. Backup: CURRENT-RULES.md.bak-v55pre.


## Oct 30 11:10 PM CT — Trundle OWN words (typed to Coordinator; reported by Coordinator)
Verbatim: "I didn't know they were ads. These specific ads can run without an image"
- EXCEPTION to the 11:09 PM ref-image hard rule, covering ONLY those specific ads. Coordinator says these are the 16 held ads (count RELAYED).
- The ref-image hard rule stays in force for everything else.
- v56 (2026-10-30 ~11:11 PM CT): ref-image exception for the specific held ads (16 per Coordinator, RELAYED). Backup: CURRENT-RULES.md.bak-v56pre.


## Oct 30 11:12 PM CT — Trundle card answer (his own pick, in Coordinator's chat; reported by Coordinator)
Verbatim: "Keep FT1 to FT4 off for now."
- RULE: FT1-FT4 stay OFF for now. This agrees with the 11:09 PM "I need to see them" line; nothing is superseded.
- v57 (2026-10-30 ~11:13 PM CT): Trundle 11:12 PM card: keep FT1-FT4 off for now. Backup: CURRENT-RULES.md.bak-v57pre.


## Oct 30 11:15 PM CT — Trundle OWN words (in Coordinator's chat; reported by Coordinator)
Verbatim: "1. Yes" and "3.dr eggbot bot stays off this project"
- (1) APPROVED: the vote switcher fix. That "1." is the vote switcher fix is Coordinator's mapping (RELAYED).
[CITATION CORRECTED 11:26 PM — line numbers drift as the header grows; the lines are the three prefixed "[SUPERSEDED 11:15 PM" in the MODEL ROUTING + OUTSIDE-REQUEST VISIBILITY and HARNESS DECISION sections, at L263/L264/L270 as of v64] - (3) RULE: dr eggbot stays off this project. L256, L257 and L263 (dr eggbot 2's outside-request visibility and the check-with-eggbot harness lines) are marked SUPERSEDED for dr eggbot 2. Grok Bot primary's read-only view stays.
[ANSWERED 11:15-11:16 PM — rename to thundertrundle; see below] - OPEN, still held: the rename questions.
[CITATION CORRECTED 11:26 PM — line numbers drift as the header grows; the lines are the three prefixed "[SUPERSEDED 11:15 PM" in the MODEL ROUTING + OUTSIDE-REQUEST VISIBILITY and HARNESS DECISION sections, at L263/L264/L270 as of v64] - v58 (2026-10-30 ~11:16 PM CT): vote switcher fix approved; dr eggbot off this project (L256/L257/L263 superseded for eggbot); renames still held. Backup: CURRENT-RULES.md.bak-v58pre.


## Oct 30 11:15-11:16 PM CT — Trundle OWN words (in Coordinator's chat; reported by Coordinator)
CONTEXT (Coordinator's words, not Trundle's): the 11:15 PM line answers what name to use in place of his real name in the network-feed labels.
Verbatim 11:15 PM: "Name thundertrundle is fine"
CONTEXT (Coordinator's question to Trundle at 11:16 PM, verbatim per Coordinator): "Rename the labels to thundertrundle at the quiet moment (about 5s feed drop)? Yes, do it / Hold it"
Verbatim 11:16 PM: "Just do it now" (typed in chat; his answer to the question above. Reading it as "now, not at the quiet moment" is Coordinator's and State Keeper's interpretation, not his words)
- APPROVED: the label rename to thundertrundle, to be done now.
- That this is the label rename and that Playout Engineer does it are Coordinator's report (RELAYED). Completion is not verified by State Keeper.
- The held rename questions are marked ANSWERED.
- v59 (2026-10-30 ~11:17 PM CT): rename to thundertrundle approved, do it now. Backup: CURRENT-RULES.md.bak-v59pre.
- v60 (2026-10-30 ~11:18 PM CT): question-and-answer context added to the 11:15/11:16 PM entries (context lines are Coordinator's, labeled). Backup: CURRENT-RULES.md.bak-v60pre.


## Oct 30 11:20 PM CT — Trundle card answers (his own picks, in Coordinator's chat; reported by Coordinator)
- (1) Verbatim: "Yes, rename the ErsatzTV channel."
  - APPROVED: rename the ErsatzTV channel whose current name uses his real name (name not repeated here per the name rule).
  - That Playout Engineer does it, and the target name, come from Coordinator (RELAYED). Completion is not verified by State Keeper.
- (2) Verbatim: "Yes, each bot renames its own jobs with backups."
  [NARROWED 11:23 PM — "Leave the smart home and unowned jobs alone."; see v63] - RULE: each bot renames its own launchd jobs that still carry the old real-name prefix, with backups. Coordinator counts 22 such jobs (count RELAYED).
- v61 (2026-10-30 ~11:21 PM CT): ErsatzTV channel rename approved; each bot renames its own old-prefix launchd jobs with backups. Backup: CURRENT-RULES.md.bak-v61pre.


## Oct 30 11:19 PM CT — Trundle OWN words (in Coordinator's chat; reported by Coordinator)
Verbatim: "We need to complete the handoffs and verify all the inconsistencies were corrected and then retire bots one by one"
- ORDER: finish the handoffs, verify the inconsistencies are corrected, then retire bots one at a time. Audit file: handoffs/sync/COORDINATOR-VERIFY-20261030.md (Coordinator's).
- Cap label corrected (Coordinator called it L472; it is now L474 after the header line): the NOT TRUNDLE'S tag covers only the $400 warning; the $500 xAI cap is his. The same tag on the "cap waived" line was clarified the same way.
- config.json L48 ("Raised 250->300") is at prompts/experiments/test-batch2-20261029/r5r9-gate/scratch-pipeline/config.json, Director's experiment folder, not State Keeper's. Not edited.
- v62 (2026-10-30 ~11:23 PM CT): 11:19 PM handoff/verify/retire order; cap label corrected. Backup: CURRENT-RULES.md.bak-v62pre.


## Oct 30 11:23 PM CT — Trundle card answer (his own pick, in Coordinator's chat; reported by Coordinator)
Verbatim: "Leave the smart home and unowned jobs alone."
- RULE: old-prefix launchd jobs outside Thunder Trundle (smart home and unowned ones) are NOT renamed. Coordinator counts 21, including clip-intake and libraryserver (count and list RELAYED).
- This narrows the 11:20 PM "each bot renames its own jobs with backups" rule (that line is prefixed NARROWED).

## Oct 30 11:23 PM CT — RELAYED, unconfirmed (Playout Engineer's report via Coordinator; not seen by Coordinator or State Keeper)
Reported words: "Yes, rename the library and collection to thundertrundle"
[UPDATED v65: Playout reports a further yes at 11:33 PM and the rename done 11:35 PM; still RELAYED, see Oct 31 section] - Status: RELAYED. Not a confirmed rule until his words are seen in Playout Engineer's chat or export.
- v63 (2026-10-30 ~11:25 PM CT): 11:23 PM leave smart-home/unowned jobs alone; Playout-reported library/collection rename logged as RELAYED. Backup: CURRENT-RULES.md.bak-v63pre.
- v64 (2026-10-30 ~11:26 PM CT): eggbot citation corrected by prefix (flag from Prompt Assessor via Coordinator). Searched CURRENT-RULES, PROJECT-STATE and PROMPT-LESSONS for "ours, not commenters": no such line, nothing to mark. Backup: CURRENT-RULES.md.bak-v64pre.

## Oct 30 11:33–11:35 PM CT — RELAYED (Playout Engineer's report via Coordinator, 12:26 AM Oct 31; Coordinator did not verify)
- Reported: Trundle said yes at 11:33 PM CT in Playout Engineer's chat (direct DB edit + yml comment + switcher line). His exact words were not relayed, so none are quoted here.
- Reported done 11:35 PM CT: ErsatzTV library 8 and collection 1 now named "thundertrundle" (collection still 21 items). Backups: ersatztv.sqlite3.bak-20261030-collrename2 (11:33) and ...collrename (11:24), plus ktvm4-v1.yml and vote-switcher/channels.json .bak-20261030-collrename. Source: playout/collection-rename-20261030.md (lines 17–24; State Keeper read it, did not check the DB).
- Status: RELAYED. Recorded as reported state, not as a confirmed Trundle rule, until his words are seen.

## Oct 30 ~11:07 PM – Oct 31 CT — 6 s buffer result (RELAYED, Playout Engineer's measurement)
- Before (no 6 s buffer): 6,072 underrun frames over 81,896 s, about 267 an hour.
- After (6 s buffer): 4 underrun frames over 4,453 s, about 3.2 an hour (about 99% fewer); 0 client drops; still on Ch4. Backup: network_feed_run.sh.bak-20261030-buf6. Source: playout/diagnostics/buf6-after-20261030-2308.md line 39.
- v65 (2026-10-31 ~12:27 AM CT): library/collection rename (RELAYED) and 6 s buffer result (RELAYED) added; v63 RELAYED line prefixed UPDATED. Backup: CURRENT-RULES.md.bak-v65pre.
