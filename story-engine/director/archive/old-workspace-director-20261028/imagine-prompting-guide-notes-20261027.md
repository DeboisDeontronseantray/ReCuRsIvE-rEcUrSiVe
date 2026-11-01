# Grok Imagine prompting guide: notes for Channel 4
Director, 2026-10-27, ~8:40 PM CT. Home-only reference. No other bots were contacted, and no existing files were edited.

## Source status (read first)
- Trundle's post: https://x.com/imagine/status/2115214583983935517 is an X Article titled "Inside Episode 1: The Oath". t.co resolves to x.com/i/article/2114831189475483648.
- **The full article body could NOT be retrieved.** X requires a login. The X API returned only the title, and the fxtwitter and xitter mirrors were blocked or returned 404.
- Instead, these notes come from related material by the same team, read this turn:
  - [A] @imagine "Odyssey Challenge Cinematic Guide" (earlier article, mirror): https://xitter.cf/imagine/article/2092675531057885288
  - [B] Odyssey Pilot tips thread (Wonder Studios / Dev Walker): https://helpolos.com/channel/@grok/3gNg7NdoPIk
  - [C] Community Grok Imagine 1.5 prompt guide: https://github.com/seaimagineai/awesome-grok-imagine-prompts/blob/main/docs/guides/en-US.md
- To get the real text, open the article logged in (box browser) or ask Trundle to paste it.

## 1. Key techniques
1. **Aim before you create [A].** First decide "what should the scene do for the viewer?" Then choose the shots for that experience.
2. **Use specific film language, not "cinematic" [A].** Shot size (wide/medium/CU/ECU/OTS/POV), angle (eye level, low, high, dutch), move (static, dolly in, push-in, pan, handheld), and lens (24/35/50/85mm, shallow DOF).
3. **Prompt like a director, in 4 parts [A].** (a) the shot, e.g. "Wide shot from the cliffside, camera static"; (b) what they do and feel, e.g. "side-by-side... feeling distant. Not looking into the camera"; (c) **performed speech with bracketed delivery cues**, e.g. `"It's been 20 years..." [long pause - she looks in the distance] [emphasis]... [she speeds up, angry]`; (d) what to remember, e.g. "Preserve natural skin, natural pores, fine lines. Nature sounds and ocean sounds. No music."
4. **Imperfection reads as human [B].** "Scenes that look perfectly clean give off 'AI vibes'." Ask for off-level framing, a subject pushed to the side, or a wobbly camera.
5. **Precise motion beats more words [B].** "When a shot keeps drifting, more words rarely fix it." Cut vague verbs like "crossing" and write "enters left, exits right."
6. **Lock the image as a "Reference" [B].** This unlocks the Omni video model, which makes characters respond better to prompts. Lock the base style, and use segmentation edits for wardrobe, hair and props.
7. **Speed Mode for volume, Quality Mode for clean work [B].** The team generated a wall of Speed Mode takes and cherry-picked.
8. **Prompt order [C]:** mode/output → opening frame → one action + 2-3 secondary motions → one camera move → audio → 3-6 continuity locks → a short avoid list. "Assign every reference image a single, explicit role." "Change one variable per iteration; do not rewrite a successful prompt from scratch." "End on a stable composition that can be used as the start of the next shot."

## 2. Applying it to "The Efficiency Review"
Prompts: /workspace/streaming/story-engine/data/shows/the-efficiency-review-20261027/prompts.json (14 shots, checker pass). What already matches: one move per shot, no music, a "never acknowledge the lens" line, text only in post, and first/last-frame chaining.

### Worth fixing before the render (cheap prompt edits, Story Bot's lane; ask, don't edit)
- **Dialogue has no delivery cues.** This is the biggest gap, because the show runs on subtext. For example, ER-06: `"Praise her bold flexibility." [small pause, warm smile that doesn't reach the eyes] [light emphasis] "Around timekeeping."` ER-07: `"Praise his calm." [beat] [dry] "Which some mistake for absence."` ER-02: `[flat] "Reassigned. Sure."` then Mira `[sweet, too quick] "How exciting for someone."` ER-13: Osmund `[voice cracks] "Effective immediately?"`.
- **Add a lens and angle to each shot.** Today there's shot size and move only. Suggestions: 35mm for wides and two-shots, 50mm for mediums, 85mm shallow DOF for the Mira sticker (ER-05) and the Osmund reading push-in (ER-11), and a slightly low angle on Tim in ER-10/ER-12 to give the hidden player power.
- **Replace vague blocking with exact motion.** ER-01: "Osmund enters frame left, walks to center, stops facing right." ER-12: "Bill turns his head left first, then Mira; Tim stays frame right." ER-14: "Tim enters frame right, drifts left through the warm doorway, exits."
- **Trim the reference stacks.** ER-02/03 use 9 refs and ER-09/10/12/14 use 8. The guide says to give each ref one explicit role. 1 front still per character (2 max) cuts both drift and CNB's ref cost; at ~$0.0857/s, refs were part of the $12.35. Add a line naming roles, e.g. "ref 1 = Bill identity/wardrobe, ref 2 = Mira identity."
- **Add a stable last-frame instruction** to every chained shot: "end on a stable held composition."
- **Add a texture line:** "natural skin, pores, fine lines; slight off-level framing" on the character shots. Keep it subtle so it doesn't fight the late-90s broadcast polish. Leave the ad pods clean.
- Leave everything else alone. The checker passes and the cap is $14.50. These are wording changes that don't add cost.
- If CNB has already started rendering, don't interrupt (Trundle: "Don't bug any working bots rn"). Apply these to retries only, changing one variable per retry.

### For future episodes
- Open every brief with a "what this scene does for the viewer" line per act.
- Shot template: `SHOT (size, angle, lens, move) | ACTION (exact entry/exit) | FEELING (subtext, eyelines) | SPEECH (quoted + [cues]) | REMEMBER (texture, sound, no music) | LOCKS (3-6) | AVOID (short)`.
- Keep the character bible as a fixed paste block (already done) plus one locked reference image per character.
- If our pipeline ever gets Speed/Quality modes or segmentation (consumer grok.com features; the API may differ), use Speed takes to cherry-pick and segmentation to fix wardrobe (e.g. sleeveless Bill) instead of re-rendering.
- The negative lists are long (27 items). The guide favors a short list of likely failures, so keep about 8-10 that actually happen (sleeveless/duplicate Bill, text, extra people, lens contact).
