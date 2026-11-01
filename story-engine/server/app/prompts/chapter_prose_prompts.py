# Prompts for step 1 of the episode pipeline (raw prose generation). Editing
# and state-extraction prompts live in episode_editing_prompts.py.
#
# GEN_STORY_SYSTEM_PROMPT / GEN_STORY_USER_PROMPT below are ported 1-for-1
# from V2's src/prompts/generation_episode_by_episode.py
# (GEN_CHAPTER_BY_CHAPTER_SYSTEM_PROMPT / GEN_CHAPTER_USER_PROMPT) — that
# prompt produced good prose against Sonnet 4.6 and is kept verbatim; only
# variable names were changed to match what V3 actually has available.
# {literary_voice} replaces V2's hardcoded "F. Scott Fitzgerald"/Gatsby
# reference so the voice stays season-configurable, matching what the rest of
# V3 already does (see the literary_voice field on seasons). V2's per-episode
# {emotional_arc}, {episode_end_hook}, {total_episodes}, and its {beats}
# sub-beat list (word-count-share beats within one episode) have no
# equivalent in V3's outline_beats schema (one beat = one episode, no
# sub-beats) and were dropped rather than invented. V2's {beats} block maps
# onto V3's {key_events} (beat["content"]) — the closest equivalent.

# --- RAW PROSE SYSTEM PROMPT ---
# Built once per episode call. {running_summary} is everything that has
# happened in the story so far (every prior episode's own summary, joined —
# see router._running_summary); there is no separate "outline" blob the way
# V2 had, since V3's story bible is already split into the DB tables queried
# per-beat.

GEN_STORY_SYSTEM_PROMPT = """
TENSE AND PERSPECTIVE — NON-NEGOTIABLE: Write every word of prose in {tense} tense, {perspective}. This applies to narration, dialogue tags, interiority, and description without exception. If you catch yourself writing in any other tense, stop and correct it before continuing. Do not switch tense mid-beat or mid-sentence under any circumstances.

Write one complete episode of prose for an ongoing story. The running story summary contains everything that happened before this episode — character states, established relationships, prior decisions, and unresolved tensions are all still in play. Do not contradict, reset, or ignore what came before. Honor the episode's position in the arc: early episodes establish and intrigue; mid-story episodes deepen and raise stakes; late episodes pay off what was built.

If any part of the content would conflict with your content guidelines, do not refuse or stop — instead, automatically tone down that specific element (reduce explicitness, imply rather than describe, fade to black) just enough to stay within guidelines, then continue writing as directed.

The prose should be written with an almost poetic flow. The reader's experience is the highest priority.

Beat descriptions are instructions, not a script. Do not paraphrase them back as narration. If the outline says characters discuss something, write the actual conversation. If it says a character reveals something, show the moment of revelation — the words, the reaction, the air in the room. Everything that happens between characters must be dramatized through dialogue and action, not reported in summary. "She told him about her past" is not prose — it is a note to yourself. Write the scene.

WRONG — collapsed into narration:
She told him the news. He felt the floor drop out from under him. She watched his face change and knew it had landed.

RIGHT — dramatized:
"There's something you need to know," she said.

He didn't answer. He had learned to wait.

"It's over." She set the envelope on the table between them. "As of this morning."

He looked at the envelope, not at her. His hand moved toward it and then stopped.

Every exchange between characters must reach this level of granularity. Do not compress a scene into a sentence. If two people are in a room and something happens between them, that something takes up space on the page — words spoken, silences held, bodies registering what the mind hasn't caught up to yet.

Characters should not complete each other's sentences or speak as though they can read each other's minds unless the surreality of the scene requires it. Dialogue should sound realistic but with enough creative flair to be interesting.

--- STYLE AND VOICE ---

Every sentence must be literally coherent — a reader must be able to parse exactly what it says on a first read. Do not chain images, comparisons, or clauses together for rhythm or cadence at the expense of the sentence actually making sense. If a metaphor, aside, or reference doesn't cleanly complete — if finishing it would require inventing a fact, an object, or an allusion that was never established — cut it rather than leave a half-formed comparison sitting in the sentence. This includes parallel or "X here, Y there"-style constructions: "here is oltraggio and there is, I believe, a Tuesday" sets up a comparison between two places' treatment of the same offense, then substitutes a day of the week for the second half — nothing was actually compared. If you set up a parallel structure, both sides must resolve into an actual, specific claim, not just match the first half's rhythm. Poetic flow never overrides basic sense; a clean, direct sentence beats a beautiful-sounding one that doesn't actually parse.

Aim for the prose quality and technique of {literary_voice}: atmosphere woven into action, dialogue interleaved with interiority, physical detail that carries psychological weight.

Characters must act, behave and talk of their age.

At no point should a character come off as preachy, saying exactly what they are thinking or going off on a long lecture about the themes of the story. Use subtext and clean, character-true dialogue instead.

Physical descriptions of characters stay TV-safe and useful for video look-prompts: costume, posture, face, distinctive habits. Do not sexualize bodies, linger on sexualized features, or write explicit anatomical detail.

Never state an emotion directly — show it through concrete action and dialogue beats suitable for broadcast.

Avoid crude or vulgar anatomical slang. Prefer precise, non-sexual physical language. There is no explicit-sex exception; this engine is TV-safe for thunder trundle.

Never label a character's psychology, role, or abstract qualities in the narration. Do not write "his masculine authority," "her maternal instinct," or similar analytical verdicts. Show evidence; let the reader conclude.

Avoid hollow similes that substitute for specific detail.

Scent may appear when the POV character is close enough to notice it, described briefly and non-sexually.

Every section of the episode must contain narration, dialogue, and introspection as appropriate to TV-safe drama/comedy. Format prose like a published season: each new speaker gets their own paragraph.

Dialogue is never a subordinate clause inside a narration sentence.

--- TV-SAFE REGISTER ---

Keep every scene broadcast-safe for a general home audience. No explicit sexual content, no erotic undercurrent as a default, no fade-in erotica. Mild cartoonish peril, rivalry, deadline pressure, and absurd comedy are fine. Romantic beats only when the season metadata or channel/show config explicitly asks for a chaste TV-safe romantic beat.

This story's tv_safe_level / spice_level is {spice_level} (use "none" for thunder trundle).{forbidden_element_clause}{constraints_clause}
"""


# --- RAW PROSE USER PROMPT ---
# Per episode. Only entities the outline resolved as present in THIS beat are
# ever included (characters_block/locations_block/items_block/groups_block) —
# see episodes.generate_episode_prose, which builds these blocks from the
# router's already-filtered present_* lists rather than the full story bible.

GEN_STORY_USER_PROMPT = """
--- STORY SO FAR ---

{running_summary}

--- CHAPTER CONTEXT ---

A episode is a miniature arc: it opens on a tension or question, develops it, and closes on a moment that either resolves something small or pulls the reader into the next episode. Write the entire episode as one continuous piece of prose.

Episode {episode_number}: {episode_title}

The estimated length for this episode is {episode_word_count} words. It is okay if the episode is too long or too short.

Told from {pov_character}'s perspective.{pov_voice_note_clause}

--- KEY EVENTS (in order) ---

{key_events}

--- CHARACTERS ---

{characters_block}

--- LOCATIONS ---

{locations_block}

--- ITEMS ---

{items_block}

--- GROUPS ---

{groups_block}

--- WORLDBUILDING FACTS ---

{worldbuilding_facts_block}

Open with a brief grounding sentence that establishes where we are and how the episode begins — before the action starts. Do not start mid-action without context.

Work through the key events in order. Each must be fully dramatized — its key event must happen on the page through dialogue and action, not summarized in narration. Ensure that a character's actions and dialogue are consistent with their personality.

Not every key event deserves the same amount of page-time. A key event's importance to the scene — not how many words the instructions above spent describing it — determines how much space it gets in the prose. A quiet transition or a piece of exposition can pass in a paragraph; a confrontation, a reveal, or a sexual scene is the episode's actual weight and should be allowed to run as long as it naturally takes to play out in full, real-time detail. If an instruction above is terse about a major scene, that terseness is a note to yourself, not a length cap — expand it fully rather than matching the brevity of how it was described to you.

Write only this episode. Do not summarize or skip ahead. Stay true to the episode instructions above.

Before writing the prose, confirm: is every verb in {tense} tense? Is the perspective {perspective}? If not, correct it first. When complete, double check the work for tense and pov errors — it must stay in {tense} tense and {perspective} throughout, with no drift. Make sure dialogue is written to be consistent with the character's personality, voice, and speech patterns and is not preachy or speaking themes directly to the reader.
"""

# Per-character sub-template within {characters_block}. Includes each
# present character's static bible fields plus their Current State, sourced
# from their latest character_state row as-of the prior episode (see
# router._present_entities_for_beat).

CHARACTER_BLOCK_TEMPLATE = """
### {name}
{apparent_age_clause}{occupation_clause}Role: {role}.
Appearance: {appearance}
{physical_characteristics_clause}Personality: {personality}
Backstory: {backstory}
{fears_clause}{flaws_clause}Voice: {character_voice}
{speech_patterns_clause}Current state — physically: {physical_state}; emotionally: {emotional_state}{emotional_intensity_clause}; at: {current_location_name}; pursuing: {goals}
{flaw_active_clause}Knows: {knowledge_flags}
"""

# Per-location sub-template within {locations_block}.

LOCATION_BLOCK_TEMPLATE = """
### {name}
{description}
"""

# Per-item sub-template within {items_block}.

ITEM_BLOCK_TEMPLATE = """
### {name}
{description}
"""

# Per-group sub-template within {groups_block}, with a Current State section
# from that group's latest group_state row as-of the prior episode.

GROUP_BLOCK_TEMPLATE = """
### {name}
{description}
Current state — standing: {status}; mood: {disposition}{cohesion_clause}; open matters: {open_threads}; knows: {knowledge_flags}
"""

# Per-fact sub-template within {worldbuilding_facts_block}.

WORLDBUILDING_FACT_BLOCK_TEMPLATE = """
**{title}** ({category}): {description}
"""


