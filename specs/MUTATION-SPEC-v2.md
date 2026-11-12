# Thunder trundle comment-mutation spec v2 (Director, Oct 29 2026 ~11:20 AM CT)
Status: DRAFT for trundle. Free work; nothing rendered. Add-only; older rules stay, and where this conflicts, see MUTATION-GAP-CHECK-v2.md.
Source words (verbatim): prompts/references/TRUNDLE-VERBATIM-mutation-20261029.md (t215u 10:58 AM CT, t217u 11:10 AM CT).
Builds on: queue-policy.yaml `comment_prompt_slots` (Oct 28 12:55 PM CT), COMMENTER-SCHEMA.md, LAYERS.md, lineage/SCHEMA.md, CONTINUITY.md (v5/v6 chaining), TRUNDLE-VERBATIM-t121.md (JW skeleton), channels/<nn>/ARSENAL-v1.md.

Core idea in one line: **commenters own what happens in the scene; we own the edges.** Every clip starts and ends on a seamless cut in the queue. That handoff is the only locked thing.

---
## 1. Handoff contract (the only lock)
- **Start:** every clip, original or mutated, is rendered with `image` = the incoming clip's REAL last frame (ffmpeg `-sseof -0.1`; step back to -0.3/-0.5 s if blurred; crop any burned HUD out first; CONTINUITY.md v5/v6).
- **End = clean handoff frame.** A frame is clean when:
  1. Same characters (sheets, wardrobe) and the same setting continuity as the scene (or the new setting reached through a physical action: a door, a train, a jump).
  2. Steady: last ~0.5 s has no motion blur, no mid-move pose, no text/labels, nobody facing the lens.
  3. Camera mount noted: `eye-level handheld | high fixed cam <where> | crane-to-mount`. A cam clip may follow only a clip that ends AT the mount angle (v6 lesson).
  4. Pose and state MAY change (someone is down, a door is broken, a coat is torn, snow started). Every change is written into the branch canon (section 5) as a state line.
- **How the next queued clip adapts:** it is NOT spliced. Its `image` is the new real last frame; its prompt pulls state from the branch canon ("WOLFHOUND is on the floor and stays down; back door hangs open") so it starts where the mutation left things. Re-rendering runs forward only until the **reconvergence point**: the first clip whose end frame can again match the original queued clip's end frame (same place, same mount, compatible state). After that the original clips play unchanged. If no reconvergence is possible within the ripple limit (default 3 clips), the branch continues as its own universe and the rest of that episode airs from the branch.
- Handoff check per clip (free, local): first frame of N+1 vs last frame of N (SSIM/eye check), plus a 2-frame trim at the join (`-ss 0.08`).

## 2. Comment → prompt
- A comment changes the **scene itself** (action, props, location detail, weather, dialogue intent, gear, powers). It is not a caption.
- It merges into trundle's **full-density John Wick direction**, never one diluted sentence. Build order of the final prompt:
  1. trundle's skeleton, verbatim (TRUNDLE-VERBATIM-t121.md #2), minus "Extend this video:" (we never extend). On cam clips the v6 fixed-mount sentence replaces "Camera pov changes…".
  2. **Action block (full density):** the whole move from the start frame to the end, every beat, with the comment's change woven in at the same density as trundle's own direction ("From the start frame, Woman in @Image2 … ending like @ImageN").
  3. Branch canon state lines (section 5/7), capped.
  4. Channel arsenal: "Only weapon: X" from channels/<nn>/ARSENAL-v1.md; powers only where the channel allows them (Ch 9/11 supers; BLACK ICE/DOSSIER grounded prototype gear).
  5. One camera sentence in industry jargon; bracketed non-direction notes; dialogue only as brief bracketed intent.
- **Safety filter (before the prompt builder):** no kids; no real people's names, likeness or voices; parody brands only; no gore (blades never wound, no blood written into text); nobody looks into the camera; trundle's real name and KTVM never appear.
- **Bend, don't drop.** A rule-breaking comment is translated to its nearest allowed version and logged with both texts ("stab him" → "blade pins his sleeve to the table, pommel strike"; a real brand → its parody; a real celebrity → an original look-alike-free character). Only hard-limit hits that can't be bent (kids, real person as subject) are rejected-and-logged (existing `hard_limit_violation` rule). Comment text is never deleted (`retention: never_delete`).

## 3. Tiers (TBD — tune in testing)
| tier | reach | examples |
|---|---|---|
| unpaid | small: one detail, a portion of one clip, or one short clip | a prop swap, weather, a gear item, a line of intent, a move inside an existing beat, a screen insert |
| paid | bigger: a whole beat or scene direction, a new branch, a character's fate, a setting change at a seam | "she loses this fight", "they take the train instead" |
Exact limits, pricing and whether paid comments may open a branch immediately are **TBD by testing** (trundle: "We will learn a lot when we test").

## 4. Bundling gate (unpaid)
- **Time window:** all unpaid comments for one channel arriving in a window (proposal: 30 min, or per break, whichever ends first) are bundled.
- **Reasoning pass:** the bundle is read as a whole and each comment is placed where it fits: which slot, which clip, which detail. Compatible comments merge into one render; conflicting ones go to different slots/clips, or to a sibling branch (paid) or a later window. **No comment detail is stripped.**
- **Placement log:** every comment gets a row: `{prompt_id, window_id, landed_in: {slot, clip_global_no, branch, field/detail}, verbatim_sha, bent_from?, merged_with[]}`. A detail that couldn't fit this window carries to the next window with priority aging (existing `priority_aging: rises_with_wait`, `max_wait_breaks: 3`).
- **Playthrough rule:** the same slot is re-rendered at most **once per full channel playthrough** (one pass of the channel's schedule loop). Later comments for that slot wait for the next playthrough or land in a different slot. This also answers "which branch airs" for that pass.

## 5. Branches as multiverses
- Each mutation creates a branch (universe) with ancestor info: `branch_id`, `parent_branch`, `forked_at {global_no, slot, window_id}`, `ancestors[]`, `canon_snippet` (section 7).
- Branches never reset or overwrite each other; "dead" in one universe is fine and alive in another.
- **Which branch airs:** the batch result for that window decides the next render; the queue then plays the newest approved generation per slot (`slots_hold: lineage`) with the playthrough rule above. Older branches stay in the lineage and can be rolled back to (`rollback: point_slot_at_older_generation`) or re-aired by a later comment/paid request.
- Tag: existing `4.<lineage> g<gen> #<no>` / `from #<parent>`; add branch as metadata, not a new on-screen line (proposal; on-screen change is trundle's call).

## 6. Canon layers (trundle: "more layers?" — yes)
Eight canon layers, highest precedence first. Safety/hard limits sit above all and never move.
| # | layer | holds | owned by |
|---|---|---|---|
| 0 | hard limits | kids, real people/brands, gore, eye contact, home-only | rules/hard-limits.yaml |
| 1 | global | look rules, JW skeleton, style refs, handoff contract | Director |
| 2 | network | cross-channel universe facts (shared parody brands, shared villains, the ad world) | Director + Story Bot |
| 3 | channel | tone, arsenal, powers allowed | channels/<nn> |
| 4 | show | cast, wardrobe locks, recurring places | show bible |
| 5 | branch / universe | mutation consequences: who's hurt, what gear, who's dead, what's broken | lineage branch canon |
| 6 | episode | this episode's time of day, weather, HUD clock, scene order | episode sheet |
| 7 | scene | setting ref, props in play, carry-forward damage | CONTINUITY per-scene kit |
| 8 | clip | the action block, the start/end frames, camera mount | shot sidecar |
| — | comment | the scene change itself (lands inside 5-8) | commenter |
- **Precedence:** a higher layer wins on conflict, except a comment may change anything in layers 5-8 (as today's layer 6 may change 4-5 details). Comments never touch 0-4.
- **Trickle-down:** a change is written at the LOWEST layer that contains it (a broken door → scene; a dead character → branch). It flows down to every descendant clip in that branch automatically.
- **Spill-over (genealogy):** a branch fact can be promoted up one layer to spill sideways: branch → show (all episodes of that branch), show → network (other channels, CNB news, ads). Promotion needs a reason + Director sign-off, is logged as a lineage row `{row_type: canon_spill, from_branch, to_layer, targets[]}`, and related items pick it up through their genealogy links (e.g. a BLACK ICE branch where the frost canister wrecks the ferry → a CNB news story about the ferry "accident" in that branch's universe; a parody-ad tie-in).

## 7. Timed prompt fade + after-effect snippets
- **Comment text fades** across generations of the branch: g+0 100% (full text woven into the action block) → g+1 50% (key clause only) → g+2 25% (one phrase) → g+3 gone from the prompt. The verbatim stays in the log forever.
- **After-effects persist:** at each render we write consequence snippets ("WOLFHOUND's left arm is in a sling", "the El station is iced over", "HERON carries the PERUN gauntlet") into the branch canon. These don't fade; they are what the comment "catalyzed".
- **Size cap:** canon text in any one prompt ≤ ~25% of the prompt, hard cap 80 words of branch+episode+scene state. When the snippet list would pass it, a **summary step** (free, text-only) compresses it to the facts visible in this clip; older facts stay in the canon file, not the prompt. trundle's skeleton and the action block are never shortened to make room.

## 8. Cross-owner notices (plain English)
"Owners" = the other bots that run pieces of the network. Nothing changes for trundle. When a branch spills outside its own clip chain, they get a short note so they use the right universe's version:
| who | when told | why |
|---|---|---|
| Commercial News Break (CNB) | a branch fact spills to news or ads | so news breaks and ads match that universe |
| Media Librarian | any new branch, render, or spill row | files and ledger point at the right version |
| Playout Engineer | a slot is replaced, shifted or a branch picked to air | so the queue plays the right clip at the right time |
| Story Bot | canon changes at show/branch layer or higher | so bibles and continuity files stay true |
| State Keeper | daily roll-up + any cap hit | single source of truth / status |
Format: one line per event appended to coordination/ (e.g. MUTATION-NOTICES.jsonl), read by the bots; no chat spam.

## 9. Cost guard
- Monthly: xAI cap **$250** (trundle t196). Comment renders get a reserve (proposal **$60/month**) inside it; Director work and paid pilots use the rest. October so far ≈ $154.87 + the running C3-forward re-render (≤ $10).
> **SUPERSEDED cap note (Director, Oct 30 ~11:05 PM CT, add-only):** the $250 monthly cap in this cost guard is superseded by the $500 monthly cap (State Keeper, CURRENT-RULES v52). Reserve/day/window figures are unchanged and still need trundle's yes for any spend.
- **Per day:** comment renders ≤ **$4/day** (~6 clips at $0.68) during testing.
- **Per window:** ≤ **$1.40** (2 clips) per bundle window per channel; max 2 gens per shot, never extend; moderated clips count.
- Ripple limit 3 clips per mutation (≈$2.04 worst case) unless paid.
- Hard stops: if a render would pass the daily/window/monthly line, the comment waits (never dropped); at 90% of the month cap, unpaid mutations pause and State Keeper is told.
- Any spend still needs trundle's own yes with the price until he approves an automatic comment budget.

## 10. Worked example: JW-5 chain, comment on C6
Chain (CHAIN-JW5-v5.md): C1 store | C2 store→alley | C3-C5 alley | **C6 alley→El** | C7-C9 El | C10 El→platform | C11-C12 platform.
1. Unpaid comment in window W: "she should grab the alley fire extinguisher and blast him before running for the El."
2. Filter: passes (no gore). Arsenal: Ch 10/JW chain allows found props → "Only weapon: fire extinguisher (spray + one body hit)". Tier: unpaid = changes a portion of one clip → OK.
3. Bundle: one other window comment ("make it start raining") conflicts with the episode's locked weather? No: weather is episode layer, comments may change 5-8 → merged into C6 as a detail; both logged to C6.
4. Build C6′: skeleton + full action block: "From the start frame, Woman in @Image2 rips the extinguisher off the alley wall, blasts a white cloud into the face of the man in @Image3, swings it into his ribs, and he staggers back into the dumpster and stays down; she runs across frame toward the stairs of the El, ending like @Image4. Rain begins to fall." + canon lines + "Only weapon: fire extinguisher" + camera sentence.
5. C6′ end: she is on the El stairs, WOLFHOUND down in the alley, rain, white powder on his coat. Clean? Steady, same people, eye-level mount → yes. Canon written: `WOLFHOUND: powder on coat, winded, catches up late`, `weather: rain from C6`.
6. C7′ re-renders from C6′'s real last frame, pulling canon (rain, powder, he arrives later). C7 originally ended with both on the El walkway; C7′ can end there too → **reconvergence at end of C7′**? Rain conflicts with original C8-C9 (which have no rain) → no, state differs. C8′ re-renders; with rain written in, C9 original can't match either → ripple limit (3: C6′,C7′,C8′) reached → the branch continues as universe `4.x-b1`, and C9-C12 of the branch render in later windows/playthroughs (or trundle approves the extra ~$2.72).
7. Lesson in the example: weather comments break reconvergence; tier them as paid or place them at a scene seam (C10 El→platform).
8. Cost: 3 clips ≈ $2.04 (+ up to 3 retakes). Notices: Playout (slots C6-C8 replaced), Media Librarian (3 new rows + branch), State Keeper (daily roll-up).

## 11. Open questions for trundle
1. Window length: 30 min / per break / per playthrough?
2. What can a paid comment do that unpaid can't, and what does it cost the viewer?
3. Ripple limit 3 clips OK? Over it → branch continues, or wait for your yes?
4. Fade schedule 100/50/25/0 over 3 generations OK?
5. Comment reserve $60/month and $4/day inside the $250 cap OK — and may comment renders run without a per-batch yes once in place?
6. Show the branch on screen (e.g. `4.13 g2 #117 b1`) or keep it metadata only?

---
## APPROVED by trundle Oct 29 11:35 AM CT
trundle's own words: "Cap yes. Yes mutation 2 good. Yes test seeds. Yes". Spec v2's proposed defaults are locked for the short-clip test (values copied exactly as proposed above; add-only, nothing above edited):
- Bundling window (§4): 30 min, or per break, whichever ends first.
- Tiers (§3): unpaid = small: one detail, a portion of one clip, or one short clip; paid = bigger: a whole beat or scene direction, a new branch, a character's fate, a setting change at a seam. Exact limits/pricing still "TBD by testing".
- Playthrough rule (§4): same slot re-rendered at most once per full channel playthrough.
- Carry-over: priority_aging rises_with_wait, max_wait_breaks 3.
- Ripple limit (§1/§9): 3 clips.
- Fade (§7): g+0 100% → g+1 50% → g+2 25% → g+3 gone; after-effect snippets persist.
- Canon cap (§7): ≤ ~25% of the prompt, hard cap 80 words of branch+episode+scene state.
- Canon layers (§6): 0 hard limits + 8 layers (global, network, channel, show, branch, episode, scene, clip); comments may change 5-8 only.
- Cost guard (§9): monthly cap $250; comment reserve $60/month; ≤ $4/day; ≤ $1.40 per window per channel; 90% month cap pauses unpaid mutations. Spend still needs trundle's own yes with the price until he approves an automatic comment budget.
> **SUPERSEDED cap note (Director, Oct 30 ~11:05 PM CT, add-only):** the $250 monthly cap in this cost guard is superseded by the $500 monthly cap (State Keeper, CURRENT-RULES v52). Reserve/day/window figures are unchanged and still need trundle's yes for any spend.
- Branch tag (§5): metadata only, not on screen (proposal default).
Commenter pipeline config cap raised to $250 (warn $200) the same day.

---
## Note: fade default (Director, Oct 30 2026 ~11:05 PM CT, add-only; nothing above edited)
- Resolves Prompt Assessor held item 7 ("'fade' spec default", prompt-assessor-SYNC.md:16). The "fade" in the six spec defaults is THIS §7 comment-text fade, NOT the corner-tag fade (1.2% tag "fades out at 3-4s", CURRENT-RULES v50:446 / RULES-OF-RECORD T24). Different things; both stand.
- Default kept: g+0 100% → g+1 50% → g+2 25% → g+3 gone; after-effect snippets persist (§7, line 68; locked line 118).
- Source: trundle's own words Oct 29 11:35 AM CT "Cap yes. Yes mutation 2 good. Yes test seeds. Yes" (line 112), plus t217 "timed prompt fade that lets commented prompts that are in the mutation slowly fade" (CURRENT-RULES v50:64; no numbers in his words).
- Docs disagree: CURRENT-RULES v50:100 still lists "Fade schedule 100/50/25/0 over 3 generations OK?" as open and does not record the 11:35 AM approval. Shared file, State Keeper's to update; not touched here.
- No builder or config uses this value (mutation fields optional/empty, CURRENT-RULES v50:285), so no stored prompt changes.
