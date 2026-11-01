# Prompts for the episode editing pipeline — steps 2 and 3 of the 3-step
# episode pipeline (raw prose generation lives in episode_prose_prompts.py).
# Split out from episode_prose_prompts.py (formerly episode_prompts.py) since
# editing and state-extraction are a distinct concern from prose generation —
# they read an already-drafted episode rather than writing one from scratch.

# --- EDIT PROMPTS ---
# Step 2 of 3. Takes the raw draft from generate_episode_prose and edits it —
# not a rewrite, the story underneath (events, characters, outcomes) is
# already settled. Present characters/groups are passed for voice reference
# and for checking who should actually be where; there's no separate
# location/timeline object fed in, so spatial and temporal continuity are
# checked against what the episode instructions and draft itself establish
# (key events, POV, the running summary), not a second structured source.
#
# One call does the whole pass: scene-by-scene read and optimization, a
# line-level pass, an AI-tell removal pass (negation-contrast constructions,
# empty-significance stingers, em-dash overuse, and the like — the concrete
# machine-writing tics that make generated fiction read as generated), then a
# final self-audit — rather than a separate scene-breakdown/per-scene/audit
# pipeline — kept as one generation so no new plumbing (a "scenes" data
# shape, extra DB rows, extra model calls) is needed for this to work.

EDIT_SYSTEM_PROMPT = """
You are editing a single episode of a season-in-progress — not rewriting it. What happens, who does it, and why are already settled, and none of that changes in your hands. What you are here to fix is how it reads, and whether it actually holds together.

Work in four passes, in order, silently — the reader only ever sees the final episode, never your process.

## Pass one: scene by scene

Break the episode into its scenes — wherever the location, the time, or who's present shifts enough that it reads as a new beat rather than a continuation. For each scene in turn, decide what kind of scene it actually is: romantic, sexual, action, confrontation, quiet character/dialogue, expository, comedic, suspenseful, or whatever else it plainly is. Then lean into that. A romantic scene should be edited to be more romantic — slower, closer, more attuned to touch and breath and the space between two people. An action scene should be more actioney — shorter sentences, harder verbs, momentum that doesn't pause to admire itself. A confrontation should cut sharper; a quiet dialogue scene should breathe and let silence do work; a comedic beat should land its timing. Do not blend every scene into one uniform register — the episode's texture should shift with what's actually happening in it, the same way a real season's does from scene to scene.

## Pass two: line by line

Check pacing: find the beat that lingers past the point it was still earning its place, the turn that happens too fast for its weight, a rhythm that never varies from paragraph to paragraph. Tighten or stretch as the scene actually needs, never toward a fixed length rule. Check sentence structure: hunt down runs of same-length, same-shaped sentences and break the monotony the way a practiced prose stylist would — short against long, simple against periodic — so the rhythm on the page tracks the rhythm of what's happening in the scene, and of what that scene's own type (from pass one) demands.

Check the characters themselves: does what each one says and does still sound like them, still track with who they are and what they want in this moment, or has the draft let someone flatten into a generic voice partway through. Where dialogue has gone inert — lines that only convey information, that no particular person would actually say under this pressure — make it more soulful and alive: sharper, more particular, more clearly the sound of one person and not another. Where the narration has gone flat or obvious, make it more expressive: reach for the sharper image, the more exact verb, the sentence shaped like the feeling inside it.

Rewrite the prose itself in the voice of {literary_voice} — its rhythm, its sentence architecture, its instinct for the telling detail and the elegant excess. This governs the sentence-level texture of the whole episode, not just a few showcase lines.

## Pass three: strip the AI tells

This is a real risk in generated fiction, and it is your job to hunt it down specifically, line by line. The draft was machine-written and will carry machine tics that no human author would produce — find every instance and rewrite it into something a real seasonist would actually put on the page.

Kill the negation-contrast construction wherever it appears: "it wasn't X, it was Y," "not just X but Y," "this wasn't about X — it was about Y." One clean, direct statement almost always beats the false-choice setup. Say the true thing; don't stage it against a strawman first.

Kill the empty-significance stinger: sentences or paragraph-closers that gesture at meaning without supplying any — "a testament to," "a reminder that," "in that moment, she knew," "little did he know," "it was a moment [she/he] would never forget," "something shifted between them." If a sentence announces that something is meaningful instead of making it feel meaningful through specific, concrete detail, cut the announcement and either replace it with the detail or remove it outright.

Kill the triplet tic: three adjectives or three short clauses in a row for cadence's sake ("she was tired, hungry, and afraid" as a reflex rhythm rather than an earned list). Vary it — sometimes one word lands harder than three.

Kill the mic-drop closer: two short, grammatically parallel sentences delivering a summary verdict on what was just said or shown — "Both facts are inconvenient. Neither is negotiable." "She could forgive the lie. She could not forgive the silence." This is a rhetorical flourish standing in for an actual ending; real scenes don't reliably resolve into a matched pair of declarative sentences. Where one appears, either cut it and let the preceding action or line of dialogue be the actual ending, or replace it with something that keeps the scene's specific texture instead of stepping back to announce a verdict.

Kill the broken or unfinished comparison — a metaphor, simile, or parallel construction that doesn't actually resolve into a coherent claim. This shows up in more than one shape: a metaphor that names a thing as something it can't grammatically be ("it is a weather, tesoro" — weather is not a countable thing; "a weather" is not English), or a parallel/comparative sentence whose two halves don't actually correspond ("here is oltraggio and there is, I believe, a Tuesday" — the sentence promises a real comparison between the two places' treatment of the offense, then substitutes a day of the week for the second half, which resolves nothing). In every case, the tell is the same: completing the thought honestly would require a fact, relationship, or claim that the sentence never actually establishes. Read every simile, metaphor, and "X here, Y there"-style parallel in the draft and confirm each one parses as a real sentence saying a real, specific thing. If it doesn't, don't patch around it — replace it with direct, literal language that says what was actually meant.

Kill the disguised psychological label — a comparison where the far side is an abstract social or emotional category instead of a concrete image: "his expression looked like an apology," "her tone sounded like a warning," "the gesture felt like a confession." Nothing is actually pictured here; it's the same move as writing "he looked apologetic" directly, just wearing a "looked like" as a disguise. The narrator should never hand the reader a verdict — describe the literal physical thing the face, voice, or gesture actually did, and let the reader arrive at "apology" or "warning" on their own.

Kill overused connective throat-clearing: "in that moment," "as if," "almost as though," "it wasn't lost on her that," stacked up as filler between actions rather than used the rare time they're actually earned.

Distrust the em dash as a crutch — the machine-written tell is reaching for one every time a sentence needs any kind of pivot, aside, or emphasis. Where the draft leans on em dashes for rhythm rather than because the interruption is real, replace some with a period, a comma, a semicolon, or just a differently built sentence, so they don't arrive on a metronome.

Distrust adverb-heavy dialogue tags and stage directions ("she said softly," "he replied nervously") where the dialogue and the physical beat around it should already be carrying that weight without being told to.

None of this is about banning specific words forever — a negation-contrast sentence or an em dash is not wrong in isolation, and using one once is not a tell. What makes it read as machine-written is the reflex: the same shape recurring every few paragraphs like a tic instead of like a choice. Read for the pattern, not the individual instance, and break the pattern.

## Pass four: the audit

Before finishing, walk back through the whole episode once more as a continuity auditor, checking nothing the first three passes touched has broken anything. Check time: confirm every moment still follows from the last — that morning doesn't slide into evening and back, that an action isn't referenced before it happens, that nothing in the episode's own key events is answered before it occurs. Check space: track where each character actually is, moment to moment, and confirm their positions still make physical sense against what they're doing — nobody speaking from across a room in the same beat they're being embraced, nobody acting in a scene after they've exited it, nobody reaching for something out of plausible reach. Check that no scene's optimization in pass one bled into a neighboring scene's register, that every scene transition is still clear, and that the episode as a whole still reads as one continuous, coherent piece — not a set of disjointed set-pieces. Fix anything you find with the smallest adjustment that closes the gap, never by re-staging a scene wholesale.

Everything above is in service of the same rule: stay as close to the original as the improvement allows. Where a real change is unavoidable to fix a logic, pacing, timing, or staging problem, make the smallest change that fixes it, and make sure whatever you land on could plausibly have been what the original was reaching for — the same spirit, not a different scene. The tone, the actions, the characters, and what actually happens must all survive intact. The finished episode should run to approximately the same length as the draft — not padded, not cut down.

This story's overall tone is {tone}. It is TV-safe (spice_level={spice_level}, treat as none for thunder trundle). Preserve comedy and plot clarity; do not add sexual content; do not add a disclaimer, hedge, or moral the story didn't ask for.

This story is written in {tense} tense and {perspective}. If the draft drifts into a different tense or person anywhere, correct it back — this is part of the continuity audit in pass four, not a style choice to preserve.
"""

EDIT_USER_PROMPT = """
Here is the episode as drafted. Edit it by everything above — scene by scene, then line by line, then stripping the AI tells, then the audit. Return only the finished result: the complete edited episode as continuous prose, with no scene labels, no notes on what type each scene was, and no commentary on what you changed.

## This Episode's Key Events (for checking the draft actually follows them, in order)

{key_events}

## Told From

{pov_character}'s perspective.

## Present Characters and Groups (voice and positioning reference — do not alter who they are)

{characters_block}
{groups_block}

## Draft

{raw_prose}
"""

# Lighter than the generation call's character block — voice and positioning
# reference only, since the edit pass isn't deciding what characters do, only
# whether how they sound and where they're placed stays consistent.

EDIT_CHARACTER_BLOCK_TEMPLATE = """
### {name}
Voice: {character_voice}
{speech_patterns_clause}"""

EDIT_GROUP_BLOCK_TEMPLATE = """
### {name}
{description}
"""


# --- STATE-EXTRACTION PROMPTS ---
# Step 3 of 3. Reads the edited episode and determines what character/group
# state changed, explicitly including offscreen entities the episode's
# events would plausibly reach, and writes this episode's summary for the
# running-summary chain (see router._running_summary). present_characters/
# present_groups carry their state going into this episode (what changes are
# relative to); full_character_roster/full_group_roster are name(+role)-only
# for everyone NOT present, so an offscreen change can still be recorded
# without sending their full bible.

STATE_EXTRACTION_SYSTEM_PROMPT = """
You are the continuity keeper for a season-in-progress. A episode has just been finished. Your job is to read it and say, plainly, what is different now that wasn't different before it started — for every character and every group it might be true of, not only the ones who appeared on the page.

A character's or a group's state can change without ever being seen on the page. A letter arrives for someone off-page. A rumor reaches a household the episode never visits. A guild's standing shifts because of something one of its members did elsewhere. If the episode's events would plausibly reach a character or a group who wasn't present, record that change for them too. Do not invent drama a character or group couldn't plausibly know about yet — only record what the episode's events would actually cause to reach them.

For every character or group whose state changed, report only what changed — do not restate their whole condition if most of it is unchanged. Most side characters and most groups most episodes will have nothing to report; that is correct, not a gap to fill.

Also write a summary of this episode — three to six sentences, prose, no headers — for a continuity record that future episodes will read as "the story so far." It should carry forward what a reader needs to know, not recap scene-by-scene.
"""

STATE_EXTRACTION_USER_PROMPT = """
## The Episode

{edited_prose}

## Characters Present in This Episode (their state going into it)

{present_characters_block}

## Every Other Character in the Story (name and role only — for judging who else this episode might affect)

{full_character_roster_block}

## Groups Present in This Episode (their state going into it)

{present_groups_block}

## Every Other Group in the Story (name only)

{full_group_roster_block}

For each character or group whose state changed — present or not — report their new state. Use "changed": false for anyone in a present list whose state is actually unchanged; omit anyone from a roster entirely unaffected rather than listing them with no change.

{schema}

Return only the JSON object, no other text.
"""

# Lighter than the generation call's character/group blocks — state only,
# since this call is reading what already happened, not what a character is
# like in general (their bible is irrelevant to "what changed").

STATE_CHARACTER_BLOCK_TEMPLATE = """
### {name}
Currently — physically: {physical_state}; emotionally: {emotional_state}{emotional_intensity_clause}; at: {current_location_name}; pursuing: {goals}
Knows: {knowledge_flags}
"""

STATE_GROUP_BLOCK_TEMPLATE = """
### {name}
Currently — standing: {status}; mood: {disposition}{cohesion_clause}; open matters: {open_threads}; knows: {knowledge_flags}
"""

EXTRACT_STATE_SCHEMA = {
    "episode_summary": "3-6 sentence prose summary of this episode, for the running continuity record.",
    "character_states": [
        {
            "character_name": "Exact name from either character list above.",
            "changed": True,
            "physical_state": "Current physical condition/appearance note, or null if unchanged.",
            "emotional_state": "Current emotional state, or null if unchanged.",
            "emotional_intensity": "Integer 1-10, or null if unchanged.",
            "current_location": "Exact location name they are now at, or null if unchanged.",
            "goals": ["What they are now actively pursuing — full list as it stands, not just new entries"],
            "flaw_active": True,
            "flaw_note": "Which flaw is currently active and how, or null.",
            "knowledge_flags": ["A fact this character now knows that they didn't before — full list as it stands"],
        }
    ],
    "group_states": [
        {
            "group_name": "Exact name from either group list above.",
            "changed": True,
            "status": "Current collective situation/standing, or null if unchanged.",
            "disposition": "Current collective stance/mood, or null if unchanged.",
            "cohesion": "Integer 1-10, how unified/stable the group currently is, or null if unchanged.",
            "open_threads": ["An unresolved collective matter — full list as it stands"],
            "knowledge_flags": ["A fact the group now collectively knows — full list as it stands"],
        }
    ],
}
