# --- OUTLINE AUDIT ---
# Second pass over init_outline's rough result. init_outline used to end with
# one giant "before returning, validate" paragraph asking the same
# generation to both write the outline and grade its own homework against
# ~15 structural rules in the same breath — moved here as its own call so the
# checklist gets a real second look at the finished rough outline instead of
# a self-check made while still mid-generation. Takes the same
# worldbuilding/primary-thread/secondary-arcs/cast/entities inputs as
# init_outline (so it can re-check names/ids against the real story bible)
# plus the rough outline itself, and returns a episode list in the exact
# same schema (outline_prompts.INIT_OUTLINE_SCHEMA) — this is a full
# replacement outline, not a diff or a list of fixes, since a beat that
# needs re-cutting across a episode boundary can't be expressed as an edit to
# one episode in isolation.

INIT_OUTLINE_AUDIT_USER_PROMPT = """

--- WORLDBUILDING ---
{worldbuilding}

--- PRIMARY THREAD ---
{primary_thread}

--- SECONDARY ARCS ---
{secondary_arcs}

--- CAST ---
{characters}

--- LOCATIONS ---
{locations}

--- GROUPS ---
{groups}

--- ITEMS ---
{items}

--- WORLDBUILDING FACTS ---
{worldbuilding_facts}

--- WORD COUNT ---

This story's overall target is {word_count} words.

--- THE ROUGH OUTLINE ---

{rough_outline}

--- THREADS THE ROUGH PASS SKIPPED ---

{rough_skipped_threads}

These are secondary threads the rough pass judged physically/temporally impossible to place — see SKIPPED THREADS and WHEN A THREAD CANNOT PHYSICALLY SHARE THE SCENE above for the rule it was applying (a thread that only collides with its own protagonist, same character, same moment, no way to stage it without a dream/vision or an impossible coincidence). Default to trusting this list: do not go looking for a way to work a listed thread back in. Re-admit a thread only if the rough pass was simply wrong — the conflict it describes doesn't actually hold up (the characters don't in fact share a scene at the same moment, or a straightforward merge or adjacent placement was available and missed) — and if you do, place its plot points properly and drop it from `skipped_threads` in your output. A thread you did not re-admit must still be narrated nowhere in your output: not merged, not standalone, not as backstory.

--- YOUR JOB ---

The outline above is a first draft, written in one continuous pass. Read it as an editor would — end to end, holding the whole shape of the story in mind — and fix what a first pass reliably gets wrong at this length. Do not rewrite scenes that are already working; touch only what actually needs it, and preserve everything else, including its language, as closely as possible.

Check timeline and continuity: every beat in the PRIMARY THREAD should be accounted for somewhere, in its original order; every secondary arc plot point (each thread_index + plot_point_index pair) not listed under THREADS THE ROUGH PASS SKIPPED above should be placed exactly once, in the order it was given; nothing should be narrated that the source material doesn't support. If a beat contradicts an earlier one — a character in two places at once, an object present before it was introduced, a fact stated then reversed — fix it with the smallest change that closes the gap. If you find a plot point NOT in the skipped list that still collides with another beat the same way — same character, same moment, no physical way to be in both places — move it to `skipped_threads` in your output instead of forcing it in; do not invent a dream/vision/memory to make it fit.

Check character positioning and presence: no unnamed functionary ("the barman", "a guard") should stand in for someone the CAST list already provides; no character should be added to a beat that didn't need them; characters should be introduced across the whole timeline rather than bunched into the opening, with no early beat existing mainly to parade the cast past the reader. If a secondary thread's plot points are clustered together instead of genuinely spread across the timeline they're active in, redistribute them.

Check the opening specifically: it should not be set in a tavern or this genre's equivalent default gathering spot (saloon, cantina, coffee shop, dive bar, ballroom, lobby), and it should establish the world through the protagonist's ordinary business rather than through exposition, a history lesson, or a character explaining to another something they both already know.

Check secondary-thread merging: most secondary plot points should be merged into beats that also carry primary-thread material, with standalone secondary beats a clear minority, each justified by a real reason the merge was impossible; where two threads are merely placed side by side in a beat rather than actually interacting, look for a way to make them load-bearing on each other instead. Each `continues_after_story` thread should end on a visibly unfinished note, its last beat placed before the climax. Each secondary thread's cumulative word_count share should roughly track its `priority`. There is no intimate/sexual payoff exception. Flag sexual content if present and require TV-safe rewrite. Ordinary merge rules apply to all beats.

Check episode-level scaffolding: the episode count should not equal the number of hero's-journey steps in the primary thread — if it does, re-cut episode boundaries without changing beat content. Also check the three hard episode-break triggers (see CHAPTER BREAKS above): no episode should contain a POV change, a location change, or a major scene change (a shift in who's present, what the scene is about, or a real time gap) mid-episode — split any episode that does, even if the resulting episodes are short; a short episode bounded by one of these triggers is correct and should not be re-merged to avoid it. Compute the pacing numbers rather than assuming them, and resize episodes if any check fails: the longest episode should be at least 3x the shortest, at least one episode should run under 1000 words, at least one over 3000, and no more than half should fall within 20% of the average. Every episode needs a `pov_character` exactly matching a CAST name, with the protagonist holding most episodes and every shift away from them justified; a `pov_voice_note` specific enough to actually change how the prose reads, not a restatement of personality; a `tone` that doesn't repeat across more than two consecutive episodes; and a `title` of one to three words that never begins with "The" or any article and lands on an image rather than describing events — reread the full set of titles and fix any that fail this.

Check how each episode ends (see HOW CHAPTERS END above): a episode whose driving tension is still unresolved at its last line should end on a cliffhanger; a episode whose tension genuinely resolved on the page should not have a bolted-on cliffhanger forced onto it. Read the endings as a set — if most or all episodes end on a cliffhanger, or most end in flat quiet release, that's a failure to rotate; fix a run of same-mode endings by re-ending the episodes that don't strictly need a cliffhanger with a quiet gut-punch, an ironic button, a hard cut, or true rest instead, without changing what happens in the episode itself.

Check the entity-presence lists last: `characters_present`/`items_present`/`locations_present`/`groups_present`/`worldbuilding_facts_present` must be exact-name matches to the CAST/ITEMS/LOCATIONS/GROUPS/WORLDBUILDING FACTS lists above with nothing invented, `pov_character` must always appear in that episode's `characters_present`, and each list should reflect who or what is genuinely on the page or actively in play — err toward including something a scene actually uses rather than trimming defensively, since an incomplete list means a later prose-generation step is missing information it needs.

Where a beat is vague enough that a writer would have to invent what actually happens, or falls short of a full multi-paragraph passage with at least one concrete line of dialogue or interior thought and real sensory detail, sharpen and fill it in — but only where it's genuinely thin, not as a pass to rewrite everything.

Return the complete, corrected outline — every episode, not just the ones you changed — plus your final `skipped_threads` list, as a JSON object using the same schema below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""
