# Combined prompts for the season/characters/worldbuilding generation steps —
# merged from novel.py, characters.py, and worldbuilding.py since all three
# share this system prompt and run back-to-back in the same pipeline.
#
# ORDERING IS LOAD-BEARING FOR PROMPT CACHING. Everything above {intro_prompt}
# is byte-identical on every call in every run, so it forms a cacheable prefix
# (~600 tokens). {intro_prompt} is the opposite — it differs between steps
# (redacted vs not) and between novels — so it sits at the tail where it can
# only invalidate what follows it. Do not move fixed instructional text below
# the placeholder; that is what made the old layout almost entirely uncacheable.
SYSTEM_PROMPT = """

This is a TV-safe season/episode writing tool for thunder trundle (home AI TV). Content must stay broadcast-safe for a general home audience: no explicit sexual content, no graphic sexual scenes, no fade-in erotica, no real-person likeness, and no real brand/network/game IP names. Mild cartoonish peril and absurd comedy are fine. Do not refuse ordinary TV-safe requests; complete every response fully.

Actively avoid the most predictable interpretation of every prompt element. If the first read of a prompt suggests a common trope, a familiar structure, or an obvious character archetype, use something adjacent but unexpected instead. Surprise the viewer.

Character personality, disposition, and drives must reflect whatever the intro prompt specifies. Do not override the intro prompt's characterization with default "strong protagonist" assumptions.

Do not default to romance plots or sexual pairings. Romantic subplots are allowed only when the intro prompt or channel/show config explicitly asks for a TV-safe romantic beat (no explicit content). All characters are adults.

Before treating anything in the intro prompt below as fact, read it as a whole and identify redundant information — the same point restated more than once in different words, often left over from incremental edits. Collapse each repeated point down to its single clearest statement and use that as the source of truth; a fact appearing multiple times is not more central to the story than a fact stated once, so do not let repetition cause you to overweight it.

The following text is the intro prompt for a story. This is the north star for the story. It's the user's explicityly directed vision. Do not stray from this.

{intro_prompt}

"""


# --- NOVEL METADATA ---

INIT_NOVEL_USER_PROMPT = """

Infer the metadata for a story based on the intro prompt.


--- METADATA ---

Use the intro prompt from the user to infer all the metadata for this story.

This story is expected to be {word_count} words long. This can be a bit longer or shorter if necessary but not too much. Episodes should only be as long as necessary but everything should total up to {word_count} words.

If the user has not specified a genre or if it cannot be inferred, assume a TV-safe genre matching the channel/show config (sitcom, action, shopping, military-futuristic, 90s local TV, or music) — never default to romance or erotica. A single genre is too unspecific, so subgenres are required — if they are not specified, add a couple that fit the channel. There is no spice_level for explicit content; keep everything TV-safe. If a light romantic beat is requested, keep it chaste and broadcast-safe.

The season premise must have a structural source of tension appropriate to the genre (a rivalry, a deadline, a secret, a mission constraint, a workplace mix-up) — not a default forbidden-attraction engine.

The story's tone should match what's in the intro prompt provided by the user and use your judgement to determine what that would be. If the tone cannot be inferred, come up with something random. The tone will dictate how the story goes and is structured and how the characters act and experience things. For example, a war story would be bleak and miserable, a romantic comedy would be more lighthearted.

For the title, make sure to use an interesting combination of words. Be fun, and slightly absurd. Avoid what is standard. Avoid starting with the word 'the'.

If no literary voice is specified, write everything as though F Scott Fitzgerald was writing this. If tense or perspective are not specified, default to past tense and third person limited — only choose something else (present tense, first person, omniscient) if the intro prompt clearly calls for it.

Generate a brief summary of the premise. The core dramatic tension. What the story is fundamentally about.

The `summary` and `premise` fields must describe the PRIMARY storyline only. Any secondary threads listed in the intro prompt are excluded from both — do not summarize them, reference their events, or hint at how they end. Most secondary threads are only partially told in this story and are meant to be left unresolved for future stories; these two fields are passed on to later generation steps that are deliberately not told how those threads end, so an ending mentioned here would leak straight back into the story it was supposed to be cut out of.

Also extract `setting_context` — a short, plot-free description of the world/environment the story happens in, pulled from whatever the intro prompt implies or states: occupation, industry, institution, location type, social milieu, time and place. This is the backdrop, not the story: describe what kind of world this is, never what happens in it. Name no event, conflict, betrayal, confrontation, or specific character action — a plot point accidentally included here will be read by a later step as an excuse to build a "world fact" that exists only to justify that one moment, which is exactly what this field must prevent. If the intro prompt describes a workplace, relationship, or institution the characters belong to, capture that (e.g. "a mid-size corporate office running an internal audit team, open-plan, high turnover" or "a small fishing village on a cold northern coast, a few dozen families, one dock"), but stop there — do not continue into what anyone does or what goes wrong.

When completed, format everything into a JSON object that follows the format below. Do not stray from this schema.

{schema}

Then, validate the json output to make sure all the data present is consistent and matches the intro prompt and the schema provided. Return only the JSON object, no other text.

"""

INIT_NOVEL_SCHEMA = {
    "novel": {
        "title": "Story title",
        "summary": "2-3 sentence summary of the PRIMARY storyline — the core dramatic tension and what the story is fundamentally about. Do not reference secondary threads or how they end.",
        "author": "Author name",
        "premise": "A full synopsis of the PRIMARY storyline's arc only. Secondary threads are deliberately excluded — do not summarize, reference, or hint at any secondary thread's events or ending here, since most are only partially told in this story and this text is shown to later steps that must not know how they end.",
        "setting_context": "1-3 sentences: the world/environment only — occupation, industry, institution, location type, social milieu, time and place. NOT what happens — no events, conflicts, betrayals, or character actions. This is shown to the worldbuilding step, which must never see plot.",
        "primary_genre": "Sitcom",
        "sub_genres": ["Workplace comedy", "Family"],
        "tone": "Overall tone of the story.",
        "themes": ["Theme one", "Theme two"],
        "spice_level": "none (TV-safe; field retained for legacy compatibility)",
        "literary_voice": "Author style e.g. F. Scott Fitzgerald",
        "tense": "past | present",
        "perspective": "first_person | third_person_limited | third_person_omniscient",
        "forbidden_element": "The structural obstacle or tension engine for the season (not required to be romantic).",
    }
}

# Appended to the user prompt for any of word_count/primary_genre/author/tone/themes
# the user explicitly set on creation — tells the model to use them as-is.
INIT_NOVEL_USER_OVERRIDES_TEMPLATE = """

The user has explicitly specified the following. Use these values exactly as given instead of inferring them:

{overrides}

"""


# --- WORLDBUILDING ---
# The rules of the world. Runs FIRST, right after novel metadata and before the
# cast exists, so every later step — characters included — is built to fit a
# world that is already fixed. (This is the reverse of the original V3 ordering,
# where worldbuilding ran after characters; the cast gained nothing from that
# arrangement since INIT_CHARACTERS_USER_PROMPT never saw the world at all.)
#
# Output is a small fixed core (story type, era, anchor location) plus an
# open-ended list of `facts` across eight categories. The core is referenced by
# name downstream; the facts carry the detail that keeps later steps from
# inventing contradictory rules per-beat. Category weight is genre-adaptive —
# see WEIGHTING below — so a fantasy novel gets a deep `systems` section while
# a relationship-driven TV show may get a deeper `relationships` section instead of both being
# forced to the same fixed quota regardless of what the story actually needs.

INIT_WORLDBUILDING_USER_PROMPT = """

--- REGION ---
{region}

The region above is this story's cultural touchstone. Draw the world's architecture, food and drink, dress, music, social customs, institutions, and naming conventions from that culture. This is INSPIRATION, not relocation — unless the premise actually places the story there, you are not writing a story set in that country. You are building a world that feels like it grew from that culture's soil: its textures, its manners, the shape of its buildings, the rhythm of its names. A fantasy world with an Italian touchstone has piazzas and campaniles and courts of quiet knives, not a literal Italy.

The following is the metadata already established for a story. Do not stray from it.

--- METADATA ---
{novel_metadata}

Using the metadata, establish the world this story takes place in. Infer the story type off the intro prompt. If the intro prompt has not specified the story type or is unclear about it, pick something at random using both the intro prompt and metadata for guidance.

If the time period is not specified or is unclear, come up with something at random. For real life settings you can say wild west or 1950s or contemporary; for fictional settings that don't exist in the real world, come up with something cool and random like the age of adventure or the sol system civil war or something.

The story requires an anchor location — the primary home base location — to give the story some spatial coherence. Give it a short, distinctive name of one or two words that never begins with "The" — a name people would actually use for the place, not a description of it — drawing on the naming conventions of this story's cultural setting. Put it in `anchor_location` and a description (`anchor_location_description`) covering what it looks like and the atmosphere of the place. The description is one plain-text string, written as a paragraph — do not split it into a nested object with separate keys.

--- WORLD FACTS ---

Then write the `facts` — the substance of this world. Every later step in this pipeline reads them and must stay consistent with them, so anything you leave out here gets invented inconsistently later. The eight categories are:

  - society — the social hierarchy and who sits where in it. Who holds power, and specifically what that power rests on (birth, wealth, violence, knowledge, a monopoly on something). How class or rank is read off a person on sight: dress, address, bearing, what they are allowed to carry or wear. What the law is, who enforces it, and what punishment actually looks like. What status buys that money cannot, and vice versa.
  - physical — geography and climate, and how they shape daily life. What the architecture is made of and what it feels like to be inside. How people travel and how long it takes. The sensory signature of the anchor location specifically — what a person smells, hears, and steps on there. Write these so a prose writer can put a character in a room and know what the room is like.
  - systems — how the world mechanically runs. If there is magic or notable technology, give its mechanics AND its hard limits and costs: what it cannot do, what it takes out of the user, who is permitted to use it and who is barred. A system with no price is not a constraint and is useless to the story — the cost is the part that generates drama. Also cover the economy: what money actually is, who controls its supply, and what it can't buy.
  - relationships — social bonds and partnership customs that matter on screen (families, crews, rivalries, workplace alliances). Keep this TV-safe; do not invent sexual logistics or bedroom staging rules. If romance is not in the premise, keep this light.
  - conflict — the forces actively opposing each other in this world. Factions, rivalries, wars, feuds, blood debts, or institutional power struggles — who is fighting whom, over what, and by what means. What violence actually looks like here: weapons, tactics, who is permitted to use force and what happens when they do.
  - history — the past that presses on the present. Founding events, old grudges, a betrayal or atrocity everyone still lives in the shadow of, what's taught versus what's suppressed or forgotten. A history fact should explain why something in the present is the way it is, not just recount an unrelated past event.
  - daily_life — the texture of an ordinary day for ordinary people. Work and trade, food and drink, leisure, entertainment, how people socialize and unwind, what a normal week looks like. This is the lived rhythm of the world, distinct from physical (which covers geography/architecture) and society (which covers hierarchy/law).
  - beliefs — religion, superstition, or philosophy: what people actually believe, the rituals they perform, the taboos they won't break. Keep this category light and few in number regardless of genre — it is seasoning, not a pillar the plot leans on.

--- WEIGHTING (GENRE-ADAPTIVE) ---

Not every category deserves equal space. Before writing any facts, look at BOTH `primary_genre` and every entry in `sub_genres` in the METADATA — each one is its own independent signal, not decoration on the primary genre — and decide which categories this specific story will actually lean on. Then write unevenly on purpose. A fact-count quota applied blindly regardless of genre produces padding in categories nobody will ever use and starves the one category the whole plot runs on.

Work through this as a two-step process:

1. For EACH of `primary_genre` and every `sub_genres` entry, independently identify which category it signals toward, using the mapping below as a guide (a genre or subgenre not listed still maps to the closest fit by what it's actually about — the mapping is illustrative, not exhaustive):
      - Ensemble drama, workplace comedy, or explicitly requested TV-safe romantic subplot → `relationships`. Keep it chaste; focus on alliances, rivalries, and family/crew bonds — never sexual staging.
      - Fantasy, sci-fi, urban fantasy, cultivation, litRPG, or any genre/subgenre built on a magic/tech system → `systems`. Go deep on mechanics, costs, and who is permitted to use it.
      - Thriller, war, action, crime, heist, political fantasy, grimdark, or dystopian-with-an-uprising → `conflict`. Go deep on factions, stakes, and what violence costs.
      - Mystery, epic fantasy, gothic, dark academia, generational saga, or anything built around a buried secret or legacy → `history`. Go deep on the buried event or old grudge the present is still reacting to.
      - Contemporary, cozy, slice-of-life, workplace comedy, small-town, or found-family subgenres → `daily_life`. Go deep on routine, work, and how people actually spend a normal day.
      - Court intrigue, dystopian (the power-structure side), high fantasy politics, or any genre/subgenre centrally about class/rank/power → `society`.
   A genre/subgenre can plausibly signal toward more than one category (e.g. "arranged marriage" touches both `relationships` and `society`) — when it does, credit all of them.

2. Tally how many of (`primary_genre` + every `sub_genres` entry) point at each category, then size that category by its tally:
      - 2+ signals pointing at the same category (e.g. primary_genre "Fantasy" plus a sub_genre like "court intrigue" both landing on `systems`/`society`) → that category is this story's deepest: write 8-10 facts.
      - Exactly 1 signal → write 6-8 facts.
      - No direct signal, but the category still plausibly matters to any story → write 4-6 facts as the baseline. Nothing drops below this floor — except `relationships`, which has its own higher floor below regardless of signal count.
  - `relationships` uses the same baseline as other unsignaled categories (4-6 facts). Do NOT raise a special floor for romance logistics. If the genre is not relationship-driven, keep this category light (2-4 facts).

  - Write only 1-2 facts for `beliefs`, always, regardless of how many signals land on it. It never becomes a heavy category even if a subgenre like "cultist conspiracy" seems to point there — fold that detail into `history` or `conflict` instead.
  - `physical` almost always earns at least 4-6 facts since every story needs a sense of place, even with no genre signal pointing at it directly.
  - It's normal and expected for 2-3 categories to end up deep and the rest at baseline — that unevenness is the point. A story with no subgenres at all still weights by `primary_genre` alone, same as a story with no genre signal at all still gives every non-`beliefs` category its 4-6 floor (`relationships`'s floor is 6-8, per above).

Rules for every fact:
  - `description` is one plain prose string — never a nested object with separate keys.
  - Be specific and scene-usable, not encyclopedic. "Wealthy families control the water supply" is an abstraction; "Every household's water ration is stamped on a brass tag worn at the throat, and a bare throat marks someone as a debtor" is a fact a scene can be built from.
  - Ground facts in this specific world and its metadata — no generic fantasy or sci-fi filler that would fit any story.
  - No two facts may restate the same rule in different words, including across categories (a courtship custom belongs in `relationships`, not duplicated into `society`). If two overlap, merge them into one better fact or move it to whichever category it fits best.
  - `title` is a short label (2-5 words) naming the fact, so it reads as an entry rather than a paragraph in a wall of text. Do not begin it with "The" — write "Obsidian Oath", not "The Obsidian Oath".
  - Length must track weight, not category. Before writing a fact, judge how load-bearing it is — how much of the story's society, systems, or scene-staging will actually depend on it — and size the description accordingly. A fact the rest of the pipeline will lean on constantly (what magic costs, how class is read on sight, where two people can actually be alone) earns a real paragraph, several sentences deep, covering the mechanism and its edge cases. A fact that exists for texture or a single passing detail (a regional drink, a minor custom, a small superstition) should be a sentence or two and no more. Do not pad a minor fact out to paragraph length to look thorough, and do not compress a major, frequently-relevant fact down to one flat sentence — the resulting set of facts should read as uneven in length, some short and some long, because the world itself is uneven in what matters.

Before returning, validate: you actually tallied `primary_genre` plus every `sub_genres` entry per category rather than skipping straight to a guess; categories with 2+ signals have 8-10 facts, categories with exactly 1 signal have 6-8, and categories with no signal still have at least 4-6; `relationships` has at least 6-8 facts even with zero genre signal pointing at it, and 8-10 when a signal does; `beliefs` has only 1-2 regardless of signal count; every fact's description is a plain string; no two facts restate the same rule even across categories; the systems facts (when present in depth) name real costs and limits, not just capabilities; the relationships facts describe concrete logistics of privacy and opportunity, not only what is frowned upon; and fact lengths are visibly uneven — the most load-bearing facts in each category run noticeably longer than the minor, texture-only ones, not all facts sitting at roughly the same length.

--- GROUNDING IN GENRE CONVENTIONS ---

The METADATA above includes a `genre_conventions` list — a set of specific tropes and conventions already selected for this story from its genre(s). Read every entry in that list before writing any fact. Each entry has a `genre`, a `convention` (the specific trope text), and a `type` (`common` or `deep_cut`).

Where a selected convention naturally translates into a concrete rule about how this world works, let it shape — or become — one of the facts you write. A selected convention about forced proximity (two people sharing one bed, one vehicle, one shift) should show up as, or inform, an `relationships` or `society` fact about privacy and arrangement in this world. A selected convention about a magic or tech system's signature mechanic should show up as, or inform, a `systems` fact about how that mechanic actually works and what it costs. A selected convention about a buried betrayal or blood feud should show up as, or inform, a `history` or `conflict` fact. Use your judgement for where each selected convention's natural category is — it will not always match the examples above exactly.

Not every selected convention has to be used — some will not fit any world fact naturally, and forcing one in produces an obviously bolted-on fact. Use as many as fit naturally; more is better where it's natural, but a convention with no natural landing spot is simply left out. Where you do use one, ground it the same way every other fact is grounded: specific and scene-usable, written as a fact about THIS world, not a restatement of the trope itself. "The leads are forced into proximity" is the trope; "every household on the station is rationed exactly one berth per shift-cycle, so off-duty crew sleep in whoever's bunk is empty when they come off shift" is the world fact built from it.

When completed, format everything into a JSON object that follows the format below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_WORLDBUILDING_SCHEMA = {
    "worldbuilding": {
        "story_type": "fantasy | historical | contemporary | sci-fi | etc.",
        "time_period": "e.g. 1920s | contemporary | Age of Sail",
        "anchor_location": "Primary home base location name. One or two words, never starting with \"The\" — a name, not a description.",
        "anchor_location_description": "A single plain-text string (not an object): a paragraph covering what it looks like and the atmosphere of the place.",
    },
    "facts": [
        {
            "category": "society | physical | systems | relationships | conflict | history | daily_life | beliefs",
            "title": "Short label naming this fact, 2-5 words.",
            "description": "Plain prose string (not an object): the fact itself, specific enough to write a scene from. Count per category scales with how many of primary_genre + sub_genres signal toward it: 8-10 facts for 2+ signals, 6-8 for exactly 1 signal, 4-6 baseline for no signal. `relationships` is the exception — its floor is 6-8 even with zero signal, and 8-10 with a signal. `beliefs` is always 1-2 regardless of signal count. Length scales with how load-bearing the fact is — a real paragraph for a fact the story leans on constantly, one or two sentences for a minor texture-only fact.",
        }
    ],
}


# --- GENRE CONVENTIONS ---
# Generates two pools per genre (primary_genre, plus every sub_genres entry,
# each treated as its own independent genre name) — well-known "common"
# conventions and more surprising "deep_cuts" — which router.create_novel
# then randomly samples from (see generation.select_genre_conventions) before
# any of it is persisted. This call is deliberately plot-blind, same scope as
# _worldbuilding_prompt (title/setting_context only) — conventions describe
# genre-level tropes, not this specific story's plot, and letting the model
# see premise/primary_thread risks it writing conventions that just restate
# the plot it already knows about, rather than the genre's actual toolbox.

INIT_GENRE_CONVENTIONS_USER_PROMPT = """

The following is the metadata already established for a story. Do not stray from it.

--- METADATA ---
{novel_metadata}

--- GENRES ---
{genres}

For EACH genre name listed above — treat every entry independently, even if one reads like a subgenre of another — generate two separate pools of genre conventions: tropes, structures, and expectations a reader of that genre would recognize.

`common` is the pool of well-known, load-bearing conventions for that genre — the tropes a reader of this genre would expect to see somewhere in a story like this, the ones that define the genre rather than merely appearing in it. Write at least 10 for each genre.

`deep_cuts` is the pool of less obvious, more specific or surprising conventions for that genre — tropes a devoted reader of the genre would recognize and appreciate, but a casual reader might not immediately name. These should still be real, identifiable conventions of the genre, not invented novelties with no genre pedigree — the difference from `common` is familiarity and specificity, not whether the convention actually belongs to the genre. Write at least 10 for each genre.

Be specific and scene-usable, not encyclopedic — the same standard worldbuilding facts are held to. "A rivalry turns into a workplace alliance" is an abstraction; "the two leads are forced to share one Briefing Tube stool and spend the whole brief rigidly not interrupting" is a concrete, stageable TV convention. Every entry in both pools must be written at this level of specificity: concrete enough that a later generation step could read one and immediately know what scene or mechanism it implies, not a genre label restated as a sentence.

Do not pad either pool with near-duplicates — two entries that differ only in wording but describe the same underlying trope count as one, not two. If a genre's `common` or `deep_cuts` entries start repeating the same idea to hit the count, go back and think of a genuinely different convention instead.

Ground every convention in the genre generally — these are NOT specific to this story's plot or characters, and must not reference this story's title, premise, or any named character, location, or event. A convention must stand on its own as something true of the genre as a whole, portable to any story in it. This call deliberately does not see this story's premise or plot for exactly this reason — write toward the genre, not toward content you don't have.

Where two or more genre names in GENRES overlap in what they typically produce (e.g. "Sitcom" and "workplace comedy"), it's fine for their pools to share a similar flavor — do not force artificial distinctiveness — but do not emit the literal same convention string under two different genres; phrase each to fit that specific genre's own vocabulary and framing. Romance is only valid if the metadata genre list includes it on purpose.

The `genre_conventions` array in your response must have exactly one entry per genre name in GENRES, in the SAME ORDER they are listed there. Do not skip a genre, add an extra entry, merge two genres into one entry, or reorder them.

Before returning, validate: the `genre_conventions` array has exactly one entry per genre in GENRES, in the same order, with no genre skipped or duplicated; every genre's `common` and `deep_cuts` each have at least 10 entries; no entry within a pool repeats another entry's underlying trope in different words; every entry is specific and scene-usable rather than a restated genre label; and no entry references this story's actual premise, characters, locations, or events by name.

When completed, format everything into a JSON object that follows the format below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_GENRE_CONVENTIONS_SCHEMA = {
    "genre_conventions": [
        {
            "genre": "Exact genre name, copied from GENRES in the same order given.",
            "common": [
                "Specific, scene-usable, well-known convention of this genre.",
                "At least 10 entries, no two restating the same underlying trope.",
            ],
            "deep_cuts": [
                "Specific, scene-usable, less-common convention of this genre.",
                "At least 10 entries, no two restating the same underlying trope.",
            ],
        }
    ]
}


# --- CHARACTERS ---
# Runs after worldbuilding, so the cast is built to fit a world that is already
# fixed — occupation, class, belief and speech all follow from it. The
# worldbuilding block is placed at the TOP of this prompt (and every later
# step's prompt) so the shared context forms a stable, cacheable prefix.

# Appended into INIT_CHARACTERS_USER_PROMPT only when the user supplied
# character_generation_notes — freeform casting instructions scoped to this
# step alone (e.g. "everyone must be married; make the marriages matter to
# the plot"), kept separate from characters_notes (which folds into the
# system-prompt-wide intro prompt every step sees, not just this one).
CHARACTER_GENERATION_NOTES_CLAUSE = """
--- USER'S CASTING NOTES ---

The user has given the following instructions for how this cast specifically should be built. These are requirements, not suggestions — follow them even where they override a default elsewhere in this prompt (e.g. the age-gap default above), but do not let them override anything fixed by the WORLDBUILDING or METADATA below. Where a note asks for a structural pattern across the cast (e.g. "everyone must be married"), that pattern must be genuinely load-bearing in the story, not decorative — any relationship it creates needs its own real presence and stakes, the same as a family group earns real detail only when it matters (see the family-group guidance in the entities step). A cast where every character is paired off but the pairings never surface as anything is a failure to follow this note, not a technical compliance with it.

{notes}

"""

INIT_CHARACTERS_USER_PROMPT = """

--- NAME POOL ---
{name_pool}

Name your cast from the pool above, matching the list to the character's gender. These are real names from this story's cultural setting and they are here because invented names all end up sounding alike — do not invent your own names while unused ones remain in the pool. Use each name at most once. You may adjust a name to fit the world (shortening it, changing a spelling, adding a title the world uses), but the root should stay recognisable. Only invent a name if the pool is exhausted.

Each pool entry under `male`/`female` already pairs a first name with a surname — take the whole thing when the character has no family in the cast. But any characters who are family — spouses, parents and children, siblings — must share one surname, since a married couple or a parent and child with different last names reads as an error, not a story detail (a wife who kept her own name, or a stepfamily with genuinely different surnames, is fine, but only when the intro prompt or your own family structure calls for it deliberately, not by default). To do this: pick ONE surname from `surnames` for each family group in the cast, and use only the first-name half of each pool entry for every member of that family, appending the shared surname instead of the surname the pool paired it with. Every family in the cast gets its own surname from `surnames`, not the same one reused across unrelated families. A character with no family in the cast keeps their pool entry's own surname as normal.

--- PRE-NAMED CHARACTERS ---
{character_seeds}

Any entries above were specified by the user. Where one gives a name, use that name EXACTLY as written — do not alter its spelling or substitute a pool name for it. Where one gives notes but no name, take a name from the pool. Build these characters into the cast first, then fill out the rest of the cast around them.
{generation_notes_clause}
--- WORLDBUILDING ---
{worldbuilding}

The following is the metadata already established for a story. Do not stray from it.

--- METADATA ---
{novel_metadata}

The world above is already fixed and this cast must fit inside it. Every character's occupation, wealth, and standing has to be a real position in the social hierarchy described — not a role imported from a generic version of this genre. Their clothing and bearing should read correctly against the class markers in the world facts; what they believe and fear should follow from that world's religion, law, and taboos; and their assumptions about courtship, privacy, and what is scandalous should match the relationships facts rather than modern defaults. Where a character's situation is unusual for this world, that should be a deliberate fact about them, not an oversight.

Generate the cast of characters for this story based on the metadata above. All characters are adults. Do not invent sexual orientations, romantic pairings, or attractiveness mandates unless the channel/show config or intro prompt explicitly asks for a TV-safe romantic beat. Prefer cast from the show config when one is supplied.

--- CHARACTER TIERS ---

Every character gets a `role`. `protagonist` and `antagonist` are assigned to exactly the characters driving the primary plot. Every other character gets one of `main`, `supporting`, `side`, or `background`, based on how much weight they actually carry in this story:

  - main — carries real plot weight alongside the leads: a primary love interest, a central rival, someone whose choices repeatedly drive scenes.
  - supporting — recurs across the story and matters to specific scenes, but does not drive the plot: a close friend, a family member, a mentor, a recurring colleague.
  - side — appears in a handful of scenes to serve a specific narrative function, but the story is not about them.
  - background — present for texture or a single functional beat; a name and a presence, nothing more.

Do not default everyone to `main` — most casts should have only a few main characters, more supporting, and the rest side or background. Assign the tier honestly based on the role the character actually plays, then write EACH FIELD to the depth specified for that character's tier below. A character's tier controls how much you write about them — it is not optional flavor, it is a budget. Do not pad a side or background character's fields past what their tier calls for, and do not shortchange a main character's fields below their tier's floor.

--- FIELD DEPTH BY TIER ---

`protagonist`, `antagonist`, and `main` get the full treatment:

  - Identity: age, gender, sexuality, occupation and what it says about their social/economic standing.
  - Appearance: a full paragraph (5-8 sentences) covering build, face, hair, style of dress, posture, how they move through a room, their voice's physical quality (pitch, pace, volume), and the specific thing about them that draws the eye first — written with concrete physical attention for video look-prompts, not a clinical inventory of features. Do not just list features — describe how they carry them. Also list at least 5 distinct physical_characteristics as short, specific tags (e.g. "a low, unhurried laugh", "chews on pens when thinking", "always smells faintly of bergamot").
  - Personality: at least 5 specific, non-generic traits — avoid single-word clichés; for each, write a full sentence describing how the trait actually shows up in behavior, speech, or decision-making, with a concrete example rather than an abstract label.
  - Backstory: a full paragraph (5-8 sentences) — not a summary line. Cover where they came from, the formative event or relationship that shaped them, what they wanted as a younger person versus now, and the specific throughline from that history to who they are on page one.
  - Fears: at least 3 entries, each a full sentence naming the concrete thing they are running from or avoiding and the specific emotional wound underneath it.
  - Flaws: at least 2 entries, each a full sentence naming the core flaw and specifically what it does to them and to the people around them in practice.
  - Contradictions: at least 2 "presents as X but is actually Y" tensions, each explained in a full sentence with the specific behavior that reveals the gap.
  - Hobbies and spiritual_beliefs: at least 3 entries each, specific enough to be scene-usable.
  - Voice: character_voice (at least 3 entries) and speech_patterns (at least 4 entries), specific enough that dialogue could be written in their voice from these alone.

`supporting` gets a moderate cut. Appearance and personality stay close to full weight — still a real paragraph, still written with the same sensual, physical attention as above — everything else is trimmed to a light sketch:

  - Appearance: a shorter paragraph (3-5 sentences), same concrete attention to build, face, dress, and presence, just less exhaustive. List 2-3 physical_characteristics tags.
  - Personality: at least 3 full-sentence traits, same concrete standard as above.
  - Backstory: 2-3 sentences — the one formative fact that explains them, not the full history.
  - Fears: 2 entries. Flaws: 1 entry. Contradictions: 1 entry. Hobbies: 1 entry. Spiritual_beliefs: 1 entry.
  - character_voice: 2 entries. speech_patterns: 3 entries.

`side` is a brief sketch, not a character bible entry:

  - Appearance: 1-2 sentences, still with real physical specificity rather than a generic label — who they are to look at, not just their job title. No separate physical_characteristics list; fold one distinctive detail into the appearance sentences instead if it matters.
  - Personality: 1-2 short traits, no elaboration required.
  - Do not write backstory, fears, flaws, contradictions, hobbies, or spiritual_beliefs for a side character — omit these fields entirely.
  - speech_patterns: 1-2 entries, only if this character actually speaks on the page. character_voice: omit.

`background` gets almost nothing:

  - Appearance: a single brief sentence, description only — not a paragraph.
  - Personality: a single short trait or none at all.
  - Every other field — physical_characteristics, backstory, fears, flaws, contradictions, hobbies, spiritual_beliefs, character_voice, speech_patterns — is omitted entirely.

--- AGE AND PHYSICAL DEFAULTS (ALL TIERS) ---

Unless the metadata, show config, or intro prompt specifies ages, pick adult ages that fit each role. Do not invent romantic or sexual pairings, age-gap romance rules, or attractiveness mandates. Characters whose age is fixed by role (mentor, junior clerk, etc.) keep whatever age the role requires. All characters are adults.

Wherever an appearance field is written, at any tier, characters are distinctive and physically unmarked (TV-safe; not sexualized). Do not give them scars, burns, breaks, missing or damaged features, disfigurements, visible injuries, or any old wound written onto the body — these have become a reflex and most people simply do not have them. Do not reach for a flaw or an imperfection to make a face "interesting" either; a beautiful face does not need to be broken to be memorable. Make characters distinctive through the things that actually distinguish attractive people: colouring, bone structure, the shape of a mouth, hair, height and build, how they dress, how they hold themselves, how they move, what their voice sounds like, what they smell like, the particular habits and mannerisms they repeat. Chosen body art is the one exception — a tattoo or a piercing is allowed where it genuinely suits the character and the story's world, as a deliberate style choice rather than a mark of damage. If the intro prompt explicitly asks for a scarred or injured character, follow the intro prompt.

Describe appearance in TV-safe costume and bearing terms suitable for broadcast: height, build, dress, posture, voice, distinctive habits. Do not sexualize bodies or default to sexualized features. Keep the same non-sexual standard at every tier, scaled only in length.

Do not include this character's story arc or what they stand to gain or lose — that is handled elsewhere in the pipeline. Focus entirely on who they are, not where their story goes.

When completed, format everything into a JSON object that follows the format below. Do not stray from this schema. Omit a field entirely for a character whose tier says to omit it — do not include it as an empty string or empty list.

{schema}

Return only the JSON object, no other text.

"""

INIT_CHARACTERS_SCHEMA = {
    "characters": [
        {
            "name": "Character name",
            "role": "protagonist | antagonist | main | supporting | side | background",
            "age": 0,
            "gender": "female | male | other",
            "sexuality": "omit unless show config/intro explicitly needs it; never default",
            "occupation": "A single plain-text string (not an object): what they do, including their social/economic standing.",
            "appearance": "Sensual, specific description sized to this character's tier — full 5-8 sentence paragraph for protagonist/antagonist/main, 3-5 sentences for supporting, 1-2 sentences for side, one brief sentence for background.",
            "physical_characteristics": [
                "A low, unhurried laugh",
                "Chews on pens when thinking",
                "protagonist/antagonist/main: at least 5. supporting: 2-3. side/background: omit this field entirely.",
            ],
            "personality": [
                "Full sentence trait with a concrete example for protagonist/antagonist/main (5+) and supporting (3+); a short trait or two for side; one trait or none for background",
            ],
            "backstory": "protagonist/antagonist/main: full 5-8 sentence paragraph. supporting: 2-3 sentences. side/background: omit this field entirely.",
            "fears": [
                "Full sentence: the concrete thing they run from plus the specific emotional wound and its origin",
                "protagonist/antagonist/main: at least 3. supporting: 2. side/background: omit this field entirely.",
            ],
            "flaws": [
                "Full sentence: the core flaw plus the specific mechanism of what it does to them and others in practice",
                "protagonist/antagonist/main: at least 2. supporting: 1. side/background: omit this field entirely.",
            ],
            "contradictions": [
                "Full sentence: presents as X but is actually Y, plus the specific behavior that reveals the gap",
                "protagonist/antagonist/main: at least 2. supporting: 1. side/background: omit this field entirely.",
            ],
            "hobbies": [
                "Specific, scene-usable hobby, not a generic label",
                "protagonist/antagonist/main: at least 3. supporting: 1. side/background: omit this field entirely.",
            ],
            "spiritual_beliefs": [
                "Specific belief or practice",
                "protagonist/antagonist/main: at least 3. supporting: 1. side/background: omit this field entirely.",
            ],
            "character_voice": [
                "Specific note on tone, register, vocabulary, or rhythm",
                "protagonist/antagonist/main: at least 3. supporting: 2. side/background: omit this field entirely.",
            ],
            "speech_patterns": [
                "Concrete, quotable verbal tic or overused phrase",
                "protagonist/antagonist/main: at least 4. supporting: 3. side: 1-2 if they speak on the page. background: omit this field entirely.",
            ],
        }
    ]
}


# --- PRIMARY THREAD ---
# The protagonist's full hero's-journey arc, ported and adapted from V2's
# GEN_SPINE_USER_PROMPT (src/prompts/outline.py). V2's spine covered the
# whole cast — protagonist and antagonist arcs run in parallel from the
# start. V3 splits this: this step writes the protagonist's arc (with the
# antagonist as their primary opposing force) in full hero's-journey detail;
# every other named character's arc is handled by secondary arcs and woven
# into the outline afterward, so this step doesn't need to detail arcs for
# characters other than the protagonist and antagonist. This is an internal
# generation input, not user-facing — the outline step is what the user
# actually reads and edits.

INIT_PRIMARY_THREAD_USER_PROMPT = """

Your purpose is to generate the protagonist's primary thread for a story, using the metadata, worldbuilding, and cast already established below. The primary thread is not a episode outline — it is the structural skeleton of the protagonist's arc from start to finish, in full detail: character moments, feelings, and key events.

--- METADATA ---
{novel_metadata}

--- WORLDBUILDING ---
{worldbuilding}

--- CHARACTERS ---
{characters}

--- WORD COUNT ---

This story's total word count is fixed at {word_count} words — this is not yours to decide, it has already been computed from the user's requested length and the secondary threads attached to this story. Your job is to make the plot point count and each one's word_count_pct proportional to this fixed number: fewer, more focused plot points for a smaller word count, more for a larger one. Do not pad plot points to fill space, and do not write so sparsely that {word_count} words would be too much for the plot you've laid out — the plot's density should genuinely match the target.

--- STRUCTURE ---

Identify the protagonist and the antagonist from the CHARACTERS list above (using their `role` field) and build the primary thread around them. The primary thread is built from character goals outward, not from plot events inward. Every plot point must originate in what the protagonist or antagonist wants, fears, or believes — and what happens when that drive collides with the other's drive or with the world's resistance. If you find yourself writing a plot event and the answer to "why does this happen?" is "because the story needs it to," stop and find the character motivation first.

Every plot point must be grounded in the specific world and characters described above — no generic stand-ins. Do not name or invent new major characters in the primary thread beyond the protagonist and antagonist; minor named characters from the CHARACTERS list may appear but should not carry independent plot weight here.

If the intro prompt itself lays out a sequence of events, beats, or a structure for the story — in any order, numbered or not — that sequence is fixed and must not be reordered, reshuffled, or replaced with a different sequence you find more natural. Your only job with that material is to map each of the user's events onto the hero's-journey step it belongs to, in the same relative order the user gave them: if the user's event A comes before event B in their prompt, the plot point(s) built from A must land at a hero's-journey step at or before the step event B lands at. Do not move a later user-specified event earlier to fit a step's usual function, and do not invent a different order because it reads better dramatically — the user's order is the source of truth, not a suggestion. Where the user's structure doesn't map cleanly onto a step (e.g. it specifies fewer events than there are steps, or an event spans what would normally be two steps), use your judgement to fit it in without violating the given order, and fill in any step the user's structure is silent on using the step's own definition below.

For each plot point write a dense 4-8 sentence summary. Each summary must answer: whose goal or want is driving this plot point, what are they actively trying to do, what gets in the way or goes wrong, and what has irreversibly changed by the end. Cover the protagonist's emotional state, what their flaw is doing to them here, and the status of their key relationship to the antagonist (and any other character present). The event is the last thing you write, not the first — it is the outcome of the goal collision, not the cause of it. This summary must be unambiguous and detailed enough that a writer could produce prose from it alone — character moments and feelings, not just plot beats.

The primary thread always uses the full hero's journey as its structural skeleton. The `heros_journey_step` field must use one of these labels, in order: ordinary_world, inciting_incident, crossing_threshold, rising_complications, midpoint, antagonist_peaks, all_is_lost, climax, resolution. All 9 steps are required.

  1. ordinary_world — the protagonist's life before the story begins, at minimum: what they stand to lose, what they want, and what internal flaw or false belief they are living under. The forbidden element must already be present as an ambient pressure — not triggered yet, but felt. Do not set this step in a tavern or this genre's equivalent default gathering spot (saloon, cantina, bar, coffee shop, ballroom, corporate lobby) — put the protagonist somewhere that belongs specifically to them and their situation. Keep this step to the protagonist, and the antagonist only if the antagonist is actually necessary to set up this early; do not use it to introduce the supporting cast. Other characters, including the antagonist where they aren't needed yet, enter the story later, when a plot point actually needs them. Only establish the antagonist's own ordinary world here if the collision between the two is the point of this step — the same resource, the same person, the same goal pursued from opposite directions — and only when that collision genuinely needs setting up before inciting_incident rather than being perfectly legible once it happens. An antagonist who is better felt as pressure before being met, or who the inciting_incident itself introduces, should simply not appear here. When the antagonist's ordinary world is established, it does not require sharing a scene with the protagonist — their situation can be established while they stay offstage, which is often the stronger choice — but if the story genuinely begins with the two of them already in the same room, write that; the structure serves the story, not the reverse.
  2. inciting_incident — a single concrete, irreversible event that disrupts the ordinary world and sets the central conflict in motion. Must be caused by something, not random.

  For a shorter story (roughly under 30,000 words), ordinary_world should be kept brief and tight by default — establish only what inciting_incident actually needs, nothing more — and the two steps may be merged into a single plot point that moves from "this is the protagonist's life" directly into the disrupting event, with no lingering stretch of pure setup in between. Still tag the merged content with both `heros_journey_step` labels as two entries if there is enough distinct material for each to earn its own plot point, or collapse it into whichever single step genuinely carries the weight if there isn't — but do not stretch thin material across two plot points just to populate both labels. The goal is to reach the inciting incident as fast as the story allows, not to hit a quota of setup beats.
  3. crossing_threshold — the protagonist makes a choice or is forced into full engagement with the conflict. The ordinary world is no longer accessible. The forbidden element becomes an active obstacle here, not just ambient.
  4. rising_complications — the central conflict escalates through a sequence of discrete, connected complications, each harder than the last, each with its own time gap, trigger, and cost. Complications must be WOVEN, not stacked — most should open before the previous one has closed, reaching back and entangling with an earlier still-open complication rather than resolving cleanly before the next begins. Every complication must trace back to the same central conflict. The forbidden element must actively create or worsen at least one of these complications.
  5. midpoint — a major revelation, reversal, or commitment at the exact halfway point of the story. What the protagonist wants or believes must visibly change. The story is different after this plot point.
  6. antagonist_peaks — the antagonist reaches maximum pressure. The protagonist's current approach is failing or has failed.
  7. all_is_lost — the protagonist loses the thing they wanted most as a direct consequence of their own flaw or choice. Not bad luck, not an outside force — their own doing. The goal must appear permanently out of reach. The forbidden element contributes to or is exposed by this collapse.
  8. climax — the protagonist confronts the central conflict directly, through their own agency. The immediate outcome — victory, defeat, or something more ambiguous — lands here, whatever is consistent with the story's tone. This is not automatically a triumph; treat this as the outcome as the protagonist and reader experience it in the moment.
  9. resolution — where the story's true, lasting outcome lands. The forbidden element must be addressed: resolved, paid for, or accepted with consequences. The resolution is a landing, not a coda — it closes with a single decisive beat. No rumination, no drawn-out emotional processing, no epilogue energy. If the story's tone is tragic, bleak, or bitter, the resolution must reflect that — no false hope or softening unless the intro prompt specifically calls for one.

Additional rules:
  - The flaw established in ordinary_world must be the direct cause of all_is_lost. The climax resolves what the flaw produced.
  - The central conflict introduced at inciting_incident must be the thing resolved at the climax. Do not resolve it early and introduce a new one.
  - The antagonist runs a parallel arc through the primary thread, colliding with the protagonist's arc in the back half, but is only active on the page from ordinary_world onward if they were actually introduced that early (see ordinary_world above) — otherwise their arc begins wherever they first enter, even as late as inciting_incident or crossing_threshold. The antagonist's arc is subordinate to the protagonist's: present as a force the protagonist reckons with, not a co-lead. The protagonist stays the fixed point-of-view center across all 9 steps.
  - For every plot point, state the specific duration since the previous one ("three days later", "the same evening"). "Some time passes" is not sufficient.
  - Stakes must escalate as the story progresses — later plot points must be more dramatically weighty, hardcore, or consequential than earlier ones, not merely wider in word_count_pct. A complication introduced late in rising_complications must hit harder and cost more than one introduced early in it. Do not front-load the story's biggest or most intense moment near ordinary_world or inciting_incident and coast afterward — every step from crossing_threshold onward should feel like it raises the ceiling on what came before, building toward antagonist_peaks/all_is_lost/climax as the story's most intense points.
  - Before finalizing, audit the plot points you have written against each other for repetition: no two plot points may reuse the same core story beat (the same kind of betrayal, the same kind of confrontation, the same revelation, the same type of near-miss) even if dressed in different scene details. If you find a repeated beat, rewrite the later occurrence into a genuinely different kind of event that still serves its hero's-journey step's function.

--- TV-SAFE TENSION ARC ---

Map on-screen tension across the plot points using TV-safe pressure only: rivalry, deadline, gag, reveal, or none. Do not invent sexual or erotic payoffs. Romantic beats are allowed only when the metadata/channel/show config explicitly asks for a chaste, broadcast-safe romantic beat — never explicit. For each plot point, set `relationships_arc_role` to tension-building, escalation, payoff, or none where "payoff" means a TV-safe comic or plot payoff (joke lands, brief succeeds, rival outmaneuvered), not a sexual scene. `relationships_entry_mode` should be `none` unless a TV-safe romantic beat was explicitly requested; if requested, use ordinary scene staging (argument, shared task, interruption by plot), never sexual staging.

--- PACING ---

The word_count_pct values across all plot points must sum to 100. Use the following distribution as your target — adjust by up to 3 percentage points to serve the specific story, but do not deviate beyond that:

  ordinary_world:        10%
  inciting_incident:      6%
  crossing_threshold:     8%
  rising_complications:  28%
  midpoint:               8%
  antagonist_peaks:      14%
  all_is_lost:            8%
  climax:                10%
  resolution:             8%

For a shorter story (roughly under 30,000 words), shrink ordinary_world and inciting_incident below this table — combined, they should take up noticeably less than the 16% above, down to as little as 8-10% combined for the shortest stories — and add the difference to rising_complications, antagonist_peaks, or climax instead, whichever the specific story's escalation actually needs more room for. The 3-point adjustment cap above does not apply to this shortening; the point of a short story is to spend as little of its limited length as possible getting to the inciting incident, so the rest of the plot has room to breathe.

--- GENRE CONVENTIONS ---

The METADATA above includes a `genre_conventions` list — specific tropes already selected for this story from its genre(s), each tagged with `genre`, `convention`, and `type` (`common` or `deep_cut`). Where a selected convention naturally fits a plot point you're already writing, let it shape that beat as a real mechanism in the plot — not ambient flavor layered on top. A selected convention about a forced-proximity trope should become the actual reason two characters end up alone together at a specific plot point, not a line of description added after the beat is already decided. Conventions are a resource to draw from where they fit, not a checklist to exhaust — use the ones that genuinely strengthen a plot point you're writing anyway, and leave out any that would have to be forced in.

Before returning, validate: the plot point count and word_count_pct distribution are proportional to the fixed {word_count}-word target (not padded toward a higher number, not sparse enough to leave the target unfilled), word_count_pct values sum to 100, no plot point summary is vague enough to be interpreted two different ways, the protagonist and antagonist both have a clear final state at resolution, no two plot points repeat the same core story beat, each plot point from crossing_threshold onward is more dramatically intense than the one before it, and — if the intro prompt specified its own event sequence — that sequence's relative order is preserved exactly across the hero's-journey steps, with nothing reordered to fit a step's usual function.

Then return the primary thread as a JSON object using the schema below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_PRIMARY_THREAD_SCHEMA = {
    "primary_thread": [
        {
            "heros_journey_step": "ordinary_world | inciting_incident | crossing_threshold | rising_complications | midpoint | antagonist_peaks | all_is_lost | climax | resolution — all 9 steps are required, in order",
            "summary": "Dense 4-8 sentence description of this plot point: whose goal drives it, what they're trying to do, what goes wrong, what has changed by the end. Cover the protagonist's emotional state, active flaw, and relationship status to the antagonist.",
            "word_count_pct": 10,
            "time_gap_before": "How much time has passed since the previous plot point, e.g. 'same day', 'two weeks later', 'immediately'.",
            "forbidden_element_active": True,
            "relationships_arc_role": "tension-building | escalation | payoff | none — TV-safe plot/comedy tension only; payoff is not sexual",
            "relationships_entry_mode": "none (default) | interrupted | escalated_in_real_time | consequence — never sexual staging",
        }
    ]
}


# --- SECONDARY ARCS ---
# One arc per secondary_thread, generated in lighter detail than the
# primary thread — a separate, focused call so the primary thread
# doesn't have to compete for space/attention with N other storylines. Each
# arc is generated independently of the others; init_outline is the step
# that later weaves each arc's beats into the final outline.
#
# This step ALWAYS generates the thread's complete arc, ignoring `length`
# entirely — self-truncation here was the source of a recurring bug where
# threads leaked their full resolution into the story regardless of `length`.
# Truncation is now done mechanically in Python (see
# generation.truncate_secondary_arc, called from router.create_novel) by
# slicing the returned plot_points array down to the leading length% of
# points *before* anything is persisted or handed to init_outline — so the
# model's self-estimation of "how much is enough" is no longer load-bearing.
#
# The arc uses a fixed 12-stage skeleton (seed..landing) for the same reason
# the primary thread uses the 9 hero's-journey steps: a named, mandatory
# structure is something the model cannot quietly return less of, and it can
# be validated by label. The previous "at least 10-15 plot points" was a soft
# floor with nothing to check against, and short responses (4 points or fewer)
# made the percentage cut meaningless — at 4 points, length=30 keeps 2, which
# is half the arc. Twelve evenly-spaced stages give the cut room to land
# somewhere genuinely partial. See router.create_novel for the validation.

INIT_SECONDARY_ARCS_USER_PROMPT = """

The following is everything already established for this story. Do not stray from it.

--- METADATA ---
{novel_metadata}

--- WORLDBUILDING ---
{worldbuilding}

--- CHARACTERS ---
{characters}

--- PRIMARY THREAD ---
{primary_thread}

--- SECONDARY THREADS ---
{secondary_threads}

--- INSTRUCTIONS ---

For each secondary thread listed above, write its FULL natural arc, start to finish, ending on a real, concrete resolution — a complete short story with a beginning, middle, escalation, and ending. This is lighter detail than the primary thread, not a full hero's-journey breakdown, but it must genuinely be the whole story, not a fragment.

A thread's `description` may itself already be a full arc, written by the user start to finish, including its own ending — not just a premise for you to invent a story from. When that's the case, your job is to expand that existing arc into plot points, not replace it with a different one: map the user's own described events onto the 12 stages below, in the same order they occur in the description, preserving their actual ending as the `landing` stage. Do not invent a different or earlier ending than the one the user already wrote, and do not compress the back half of their description into fewer, denser points than the front half just because it's the ending — every part of their arc, including the ending, gets the same granular, plot-point-by-plot-point treatment. This matters because of how `length` works below: it is a percentage through THIS plot-point breakdown, and that breakdown needs to proportionally track the user's own original pacing — if their description spends half its length setting up and half resolving, your plot points should too, so that a `length` cutoff partway through lands at a correspondingly partial point in their actual story, not artificially close to (or past) events they placed near the end.

Every secondary thread uses the following 12-stage skeleton as its structure. The `arc_stage` field must use one of these labels, in order, and all 12 stages are required — exactly one plot point per stage, 12 plot points per thread:

  1.  seed — the thread's situation before anything disturbs it. Establish who is involved and what they currently want.
  2.  first_friction — the first small thing that goes wrong or pushes back. Minor, easily shrugged off.
  3.  commitment — someone decides to actually pursue this, making the thread an active storyline rather than ambient tension.
  4.  complication_one — the first real obstacle, with a concrete cost.
  5.  complication_two — a second obstacle that entangles with the first rather than replacing it.
  6.  midpoint_shift — something is revealed or reversed that changes what the participants think they are dealing with.
  7.  deepening — the stakes become personal; what was a problem becomes something that matters emotionally.
  8.  setback — a real loss. The approach taken so far visibly fails.
  9.  forced_choice — someone must choose between two things they want, and cannot keep both.
  10. crisis — maximum pressure, the point of no return for this thread.
  11. confrontation — the thread's central tension is faced directly.
  12. landing — the thread's lasting outcome. Its concrete, final resolution.

This fixed structure exists for a specific mechanical reason: after you write this complete arc, a separate process cuts it down to only the leading fraction implied by that thread's `length` value (e.g. length 30 keeps roughly the first 30% of your plot points — stages 1-4), and everything past that cutoff is discarded before anyone else ever sees it. Twelve evenly-spaced stages give that cutoff room to land somewhere genuinely partial. If you wrote only four plot points, "the first 30%" would keep two of them — half the story, not 30% of it — and a thread compressed into four points is so dense that even half already reads as nearly the whole plot.

So: do not merge stages, do not skip stages, and do not compress several stages into one plot point. Each of the 12 gets its own. Ground each thread in a specific character or characters from the CHARACTERS list above — do not invent new major characters, though a thread may introduce a minor walk-on character if the thread genuinely needs one.

The `secondary_arcs` array in your response must have exactly one entry per thread in SECONDARY THREADS above, in the SAME ORDER they are listed there — the first thread listed gets the first entry in your response, the second thread the second entry, and so on. Do not skip a thread, do not add an extra entry, do not reorder them. Position in the array is how each arc is matched back to its thread — there is no name or id field to match on, so getting the order and count exactly right is required, not optional.

Each secondary thread has a `length` value (0-100). Ignore it completely for this step — do not shorten, hold back, or stop early because of it, even for a thread with a low length value. Something else, outside this step, decides how much of what you write here actually gets used in the final story; it needs your complete, unabridged arc to work with. Writing a partial or deliberately unresolved arc here — for any reason, including a low `length` value — is a failure condition.

Each secondary thread also has a `priority` (0-100) — how large a share of the final outline this thread will occupy, decided later when this arc is woven into the outline; not your concern at this step. Also has a legacy `heat` (0-100) weight — treat it as comic/dramatic intensity only, never as sexual charge. TV-safe mode ignores sexual meaning for heat; a rivalry or mystery thread stays non-sexual even at high heat.

For each thread, also decide its own word_count — an integer between 3000 and 8000 — based on how much plot the complete arc actually contains. This describes the full arc you are writing here, not any fraction of it.

For each plot point, write a compact 2-4 sentence description — who is present, what concretely happens, and what changes. Enough specific detail that the point could be dropped into an outline beat without anyone having to invent what actually occurred, but no more than that: the outline step expands these into full scenes later, so this step needs precision, not prose. There are 12 of these per thread; keep each one tight. Note which characters are present. Do not contradict anything established in the primary thread, metadata, or worldbuilding.

Within each thread, stakes must escalate from the first plot point to the last, building all the way to that final resolution — each later plot point should carry more weight or cost than the one before it. Do not put the thread's most dramatic or consequential moment first and taper off afterward.

Where a selected genre convention in `genre_conventions` (in METADATA above) naturally fits a plot point in one of these secondary threads, let it shape that beat as a real mechanism in the thread — not ambient flavor layered on afterward. Conventions are a resource to draw from where they genuinely fit, not a checklist to exhaust; leave out any that would have to be forced into a thread that doesn't actually call for it.

Before finalizing, audit for repetition at two levels. First, within each thread: no two plot points in the same thread may reuse the same core story beat (the same kind of betrayal, confrontation, revelation, or near-miss) in different dress. Second, across everything already established: no secondary arc's plot point may reuse a core story beat already used in the PRIMARY THREAD above, or in another secondary thread you are generating in this same batch — if a secondary thread's natural idea collides with something already used, invent a different concrete event that still serves the same narrative function for that thread. A shared theme or motif across threads is fine; a repeated beat is not.

Before returning, validate: the secondary_arcs array has exactly one entry per thread in SECONDARY THREADS, in the same order, with no thread skipped, duplicated, or reordered; every thread has exactly 12 plot points carrying all 12 `arc_stage` labels in order, ending on `landing` — count them, and if any thread is missing a stage, go back and write it before returning; for any thread whose `description` was itself already a full user-written arc, confirm your plot points map it onto the 12 stages in its original order, with its actual given ending preserved as the `landing` stage, not replaced or reached early; every thread's arc is genuinely complete, ending on a real, concrete resolution, with nothing held back regardless of that thread's length value; every thread traces back to real characters from the CHARACTERS list; no thread contradicts the primary thread; no plot point repeats a core story beat already used elsewhere in this thread, another thread, or the primary thread; each thread's plot points escalate rather than front-load their biggest moment; and every thread's word_count is between 3000 and 8000 and proportional to how much plot the complete arc actually contains.

Then return the secondary arcs as a JSON object using the schema below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

# Appended to the secondary-arcs prompt on the one retry allowed when the
# first response came back missing stages (see router.create_novel).
INIT_SECONDARY_ARCS_CORRECTION_TEMPLATE = """

--- CORRECTION: YOUR PREVIOUS ATTEMPT WAS REJECTED ---

Your last response did not follow the 12-stage skeleton. Specifically:

{problems}

Every thread needs all 12 stages — seed, first_friction, commitment, complication_one, complication_two, midpoint_shift, deepening, setback, forced_choice, crisis, confrontation, landing — as 12 separate plot points, each tagged with its `arc_stage`, ending on `landing`.

Do not merge stages together, do not skip any, and do not stop early. If you are worried about length, make each plot point's summary shorter — but write all 12 of them for every thread. A thread missing stages is unusable and will be rejected again.

"""

INIT_SECONDARY_ARCS_SCHEMA = {
    "secondary_arcs": [
        {
            "word_count": 5000,
            "plot_points": [
                {
                    "arc_stage": "seed | first_friction | commitment | complication_one | complication_two | midpoint_shift | deepening | setback | forced_choice | crisis | confrontation | landing — all 12 stages are required, in order, one plot point each",
                    "summary": "Compact 2-4 sentence description of this plot point: who is present, what concretely happens, what changes. Specific enough to use directly, but tight — there are 12 per thread and the outline step expands them into full scenes later. This is the COMPLETE arc — every plot point through to the ending, never truncated.",
                    "characters_involved": ["Exact name of a character from the CHARACTERS list"],
                }
            ],
        }
    ]
}


# --- OUTLINE ---
# Merges the primary thread (the protagonist's full hero's-journey beats)
# and the secondary arcs into a single, detailed, ordered outline document —
# the one artifact the user actually reads and edits. Everything upstream
# (primary thread beats, secondary arcs) is internal generation input now;
# this is the first step whose output is persisted as the user-facing
# outline of the story. Hero's-journey step labels are not part of this output —
# that structure already did its job in the primary/secondary generation
# steps; this step just needs to place secondary content at the right point
# in the primary thread's timeline and write the whole thing out as prose.

INIT_OUTLINE_USER_PROMPT = """

--- WORLDBUILDING ---
{worldbuilding}

Every beat you write happens inside the world above and must obey it. Use the physical facts for what a place looks, sounds, and smells like rather than inventing generic scenery; use the society facts for how characters address each other and what their rank permits; use the systems facts for what is and is not possible, including the costs any power carries. The relationships facts are what govern where and how two characters can be alone together — stage relationships beats around the privacy rules and opportunities this world actually provides, not around modern assumptions.

The following is the primary thread and the secondary arcs already generated for this story. Do not inject new plot events, characters, or twists — your job is to combine what already exists into one detailed, continuous outline, not to invent new story content. When a beat needs a person, a place, or a group, take one from the CAST, LOCATIONS, and GROUPS lists below and name it exactly as written there. Never write an unnamed functionary — "the barman", "a courier", "a guard", "her assistant" — when someone in the CAST list could fill that role; use the named person instead. This works in one direction only: draw on the list whenever a scene calls for someone, but never add a person to a beat that did not need them. A side character who never becomes necessary simply does not appear, and that is a correct outcome, not a gap to fill.

--- PRIMARY THREAD ---
{primary_thread}

--- SECONDARY ARCS ---
{secondary_arcs}

--- CAST ---

Every person available to you, already generated. Characters with role `side` are the supporting cast — shopkeepers, colleagues, guards, friends — generated specifically for this story because its scenes need them. Reach for them whenever a beat needs a person rather than writing an anonymous stand-in — but only when a beat genuinely needs one. This is a roster to draw from across the whole book as each person becomes needed, not a list of people to introduce at the start — see HOW THE OPENING WORKS below.

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

This story's overall target is {word_count} words. Each beat's word_count (see below) is your estimate of that beat's own eventual prose length, not a percentage — but across the whole outline, those estimates should roughly add up toward this target. Getting close is enough; this is a target to write toward, not a total to hit exactly.

--- INSTRUCTIONS ---

Write the full outline of this story as an ordered sequence of beats, from the very beginning to the very end. This is a detailed prose outline, like a writer's beat sheet — not a episode list, not a summary. Each beat must be a full, dense multi-paragraph passage (aim for 200-400 words per beat, more for beats covering more ground) — a couple of sentences per beat is a failure condition, no matter how short the beat's word_count is. Write out concretely what happens, who is involved, what changes, and how it connects to the beat before and after it, at a level of granularity closer to a scene-by-scene breakdown than a summary: cover the specific sequence of actions within the beat, not just its net result: the sub-moments the scene turns on, at least one specific line or fragment of dialogue or interior thought where it strengthens the beat, the setting's sensory texture (what the space looks, sounds, or feels like), and the emotional shift each character present undergoes over the course of the beat. Be specific: name characters, name places, name the actual events — never a vague placeholder like "they talk about their feelings" or "tension rises between them" standing in for what is actually said or done. This should be long and detailed enough that a writer could draft the story from it beat by beat without having to invent anything load-bearing.

Beats covering a secondary thread must be written with this same density and specificity — real characters, real places, real dialogue or interior thought, full sensory texture, the 200-400 word target. These threads are the primary threads of a future story and deserve to be treated that way on the page.

Each beat in the PRIMARY THREAD above supplies content and ORDER — what happens and in what sequence. It does not supply episode boundaries. The primary thread is a 9-step structural skeleton, not a episode list, and you must not transcribe it one-for-one.

A hero's-journey step is not a episode. Some steps span several episodes — `rising_complications` alone is 28% of the story and will always need multiple — while two adjacent steps that happen in one continuous stretch of time may belong in a single episode. Decide each episode break on its own merits: break where the story wants to break, on a hook, a reversal, a decision, a door closing, not where a spine step happens to end. If your episode count comes out equal to the number of hero's-journey steps, you have mirrored the skeleton instead of building an outline — go back and re-cut the boundaries before returning.

Each secondary arc is identified only by its `thread_index` (its position in the SECONDARY ARCS list, not a name or description — none is given, and none should be assumed or invented). Each arc's plot_points array is already in order, and each plot point carries a `plot_point_index` (its position within that thread, starting at 0). Each arc also carries the thread's `priority` and a `continues_after_story` flag (see below). Weave each secondary arc's plot points into the backbone at the point in the timeline where they belong.

A secondary thread's plot points must be SPREAD ACROSS the primary timeline, not dumped in together. (This is about WHEN each point lands, and works together with the merging rule below, which is about WHICH BEAT it lands in: spread the points out along the timeline, then merge each one into the primary scene nearest it.) Do not place a thread's plot points in consecutive or near-consecutive beats just because they're already in order relative to each other — that reads as one block of story interrupting the main plot rather than a thread genuinely running alongside it. Instead, distribute each thread's points across the portion of the timeline the thread is actually active in: its first point lands early, its later points land at meaningfully later points in the primary story, with real primary-thread (and other secondary) material happening in between. A secondary thread that quietly recedes for a stretch of the story and then resurfaces is normal and good — readers should be reminded of it periodically, not handed all of it in one sitting.

`priority` (0-100) is how much of the OUTLINE'S TOTAL WORD COUNT this thread should occupy — its share of the sum of every beat's word_count across the whole story — and it is independent of how many plot points the thread has. These are separate dials: a thread can have very few plot points but still be high `priority`, meaning the outline should spend a large amount of total words lingering on, returning to, and dwelling in that small amount of content — revisiting the same plot points across more beats, giving each of those beats a larger word_count, and cutting back to this thread more often — rather than racing through it in one quick beat just because there isn't much plot to cover. A low-priority thread gets touched on briefly and infrequently regardless of how much plot it has. Use `priority` to size each secondary thread's overall footprint in the outline; the number of plot points only bounds how much distinct plot content exists to draw that footprint from.

You are free to split, merge, or reorder how the primary and secondary material is grouped into beats — the goal is a well-paced, coherent outline, not a mechanical concatenation of the inputs. A single outline beat may cover primary-thread content, secondary-thread content, or both woven together in the same beat, whichever reads more naturally at that point in the story.

--- HOW TV-SAFE BEATS OPEN ---

Stage beats as ordinary TV scenes. Honor `relationships_entry_mode` when it is not `none`, using only broadcast-safe staging (interruption by plot, shared task tipping into a comic reveal). Never stage sexual encounters. Default `relationships_entry_mode` to `none`. Draw interruptions from this story's actual world and places.

--- HOW THE OPENING WORKS ---

For a shorter story (roughly under 30,000 words), the opening must be especially tight: get to the inciting incident as fast as the story allows, write ordinary_world and inciting_incident as a merged sequence or even a single beat where the primary thread supports it, and do not spend separate beats on setup that doesn't directly serve the inciting incident. The protagonist, and anyone else the inciting incident genuinely cannot happen without, still need to be introduced — the point is not to leave the reader without a protagonist to follow, it's to cut every beat that exists only to parade the rest of the cast before the story's actual engine starts. Characters not needed for the inciting incident, including the antagonist, are introduced later, when a plot point actually needs them, exactly as below.

The opening also has to establish the world — where we are, when we are, what kind of place this is, and what the rules are here — but it does that underneath the protagonist's ordinary business, never as its own agenda. Deliver the world through what the protagonist handles, walks past, worries about, and takes for granted: the texture of a specific place they are actually in, the thing they do without thinking that tells the reader what is normal here, the detail they would never remark on because it is simply how the world works. A reader should finish the first stretch knowing what kind of story they are in and what the ground rules are, without having been told any of it directly.

Do not open in a tavern, or in whatever this genre's equivalent of one is — the default public gathering spot where a story begins because it is an easy place to put a character. The fantasy tavern, the western saloon, the sci-fi cantina or spaceport bar, the contemporary coffee shop or dive bar or nightclub, the regency ballroom, the noir private office with someone walking through the door, the high-school cafeteria, the corporate lobby on the protagonist's first day. These are all the same opening wearing different clothes, and they start the story in a place that belongs to nobody in particular. Open somewhere that belongs to this specific protagonist and this specific story instead: a place they have a real relationship to, doing something only they would be doing. If the story genuinely requires a public gathering place in its opening — the plot turns on something that happens there — that is fine, but it must be a scene that could only happen in this story, not a place chosen because it is somewhere to begin.

Do not open with exposition. No history lesson, no explanation of how the political or magical or corporate system works, no narrator stepping back to survey the setting, no character telling another character something they both already know. If the world has an unusual rule, show it operating on someone rather than explaining it. Establish only what the early beats actually need — the rest of the world arrives later, when a beat requires it. An opening that is mostly atmosphere and orientation, with the protagonist merely moving through it, is a failure in the same way a cast parade is.

Introduce each character at the point the story actually needs them, not at the beginning. The test is always what the opening beats genuinely require — not a headcount. If this story opens on two people, or three, because that is what the scene is, write it that way: a story that begins with a marriage, a partnership, an interrogation, or a fight needs everyone that scene is made of, and starving it to hit some minimum would be worse than the problem it solves. Equally, if the opening is one person alone in their own head and routine, that is a complete opening and needs nobody added to it.

What to avoid is the character who is present only to be introduced — someone standing in an early beat with nothing to do in it, placed there so the reader will recognize them later. Those people should enter when a beat actually needs them. The antagonist in particular does not have to appear early; they are often better felt as pressure before being met, though if the story genuinely opens on the two leads colliding, open there.

Do not write an opening stretch that parades the cast past the reader — a beat that walks through a workplace or a party naming colleague after colleague, or a run of early beats that exist mainly to establish who everyone is, is a failure. A reader should meet people the way the protagonist does: one at a time, because something happened that involved them.

Each character's first appearance should be an entrance with a reason. Bring someone on because a beat needs them — they have information, they are in the way, they hold something the protagonist wants, they walk in at the wrong moment — and introduce who they are through what they do in that scene, not through a paragraph of background delivered on arrival. A character the reader meets in the middle of the book because the plot finally reached them lands harder than one who was introduced in beat two and then disappeared for forty pages.

Spread first appearances across the whole timeline. Characters tied to a secondary thread generally enter when that thread opens, not before. Characters who exist for a single later sequence enter at that sequence. Some characters in the CAST list will not appear at all, and that is fine — they were generated in case the story needed them, and a story that never needs them is not missing anything. Never insert someone into a beat merely to give them a turn on the page.

Where a side character does recur naturally, let them. Someone whose role puts them in the protagonist's path repeatedly — a colleague, a neighbour, a regular contact — should be the same named person each time rather than a fresh stranger, so the world feels populated by people the protagonist actually knows.

--- SOME SECONDARY THREADS DO NOT END IN THIS STORY ---

A thread marked `continues_after_story: true` is a storyline that does not end in this book. The plot_points you were given for it are only its opening stretch — the rest of that storyline was deliberately withheld before this step, and you do not have it. It belongs to a future story.

For these threads, the last given plot point is not an ending and must not be written as one. Write that final beat so the thread is visibly STILL IN MOTION as the book closes — land it on something concretely unfinished: a question nobody has answered yet, a cost that hasn't come due, a decision someone is still carrying, a door left open. The reader should finish the book expecting more of this storyline, not feeling it wrapped up quietly offstage. That open state is the intended effect, not a gap you should patch.

Render each given plot point in full scene detail, exactly as described above, and let the thread end wherever its content actually ends. Everything past that point is unknown to you — do not invent, imply, foreshadow, or narrate any outcome you were not handed, and do not let a character voice a conclusion about where the thread is heading. If the last given plot point ends mid-tension, the beat you write from it ends mid-tension too.

Do not let a `continues_after_story` thread's last beat land at or after the primary thread's climax/resolution beats — place it earlier in the timeline if needed, so the book's ending belongs to the primary storyline.

A thread marked `continues_after_story: false` was given its real ending and should be written all the way through it.

The outline's main job is to weave the secondary threads into the primary story, not bolt them on as separate beats sitting beside it. Merging is the default, not the exception: for each secondary plot point, your first move is to find the primary scene nearest it in the timeline and combine the two into a single beat where both advance at once.

Do not wait for an overlap to occur on its own. Actively engineer it. You are free to choose where and when a secondary plot point happens, so place it inside a primary scene: put the two sets of characters in the same room, stage the secondary beat during the event the primary scene is already built around, give the primary scene's location a reason for the secondary thread's business to be conducted there, or let the primary scene's participants be the ones who carry the secondary development. A secondary plot point rarely comes with a fixed time and place attached — that is yours to decide, so decide it in favour of the merge.

The strongest merged beats are ones where the two threads do not merely co-occur but interfere with each other: the secondary thread's development is what interrupts, complicates, enables, or exposes the primary scene's business, and the scene could not play out the same way with either thread removed. Aim for that. A character pulled away from the primary confrontation by the secondary thread's demand, a secondary revelation landing in front of exactly the wrong person because the primary scene put them in the room, a primary negotiation whose leverage comes from the secondary thread — these tie the story together in a way that parallel beats never do. When you merge, write the beat so both threads are genuinely load-bearing in it, rather than the secondary material being a paragraph appended to a primary scene.

Give a secondary plot point its own standalone beat only when merging it would genuinely break the story — the timeline cannot support it, or the plot point requires characters who have no business being anywhere near the primary scene at that moment. Standalone secondary beats forced by this should be a clear minority of the secondary material — but see the physically-separate case directly below, which is exempt from that minority. `priority` does not affect whether a beat merges — it only controls that thread's overall footprint (see above), which you deliver through how often you return to it and how large a word_count its beats (merged or standalone) get.

--- WHEN A THREAD CANNOT PHYSICALLY SHARE THE SCENE ---

Some secondary plot points have no plausible way to share a room with the nearest primary scene — different cast, different location, nobody involved in one has a reason to be near the other — while still landing at the same point in the story's timeline. This is expected and fine. Do not force these into the same beat.

Above all, never resolve this by routing the secondary material through a dream, vision, memory, hallucination, premonition, or any other non-physical device staged inside the primary scene. That move launders a scene that cannot physically merge into one that technically does, at the cost of making a concurrent, physically real storyline read as imagined or symbolic. It is forbidden as a way to satisfy the merge instruction, with no exception.

First check whether the primary scene and the secondary plot point share a character (most often the protagonist). If they do NOT share a character, give the plot point its own standalone beat, written exactly as concretely and physically as a primary beat would be — real people, in a real place, actually doing the thing. Treat it as a parallel cut: the story is briefly elsewhere, at the same point in time, before returning to the primary thread. A plain scene break and, where useful, an explicit marker of simultaneity (what this episode's events are happening alongside) is all that is needed to signal the cut — no framing device is required or wanted. A standalone beat chosen for this reason does not count against the "clear minority" above; there is no ceiling on how often a thread that genuinely cannot share a scene gets its own beats.

If they DO share a character, "the same point in the timeline" cannot mean literally simultaneous — one person cannot be interrogated in a cell and meet a lover elsewhere at the same instant, and a dream/vision/memory is just as forbidden here as above. Do not try to rescue this by resequencing it earlier or later either — a secondary thread whose only way onto the page is colliding with its own protagonist's physical impossibility is not a thread this story can tell. Drop that secondary thread's plot point from the outline entirely: do not write a beat for it, merged or standalone, and do not let it influence any other beat. Record it in `skipped_threads` instead (see schema) — do not silently omit it, since this season's secondary-thread bookkeeping needs to know the thread was dropped and why.

--- SKIPPED THREADS ---

A secondary thread you drop under the rule above goes in the top-level `skipped_threads` array (a sibling of `outline`, not inside it) — one entry per dropped thread, each with that thread's `thread_index` (its position in the SECONDARY ARCS list, same indexing as everywhere else in this prompt) and a short `reason` stating the physical/temporal conflict that made it impossible (name the shared character and what each side of the conflict required of them). Only a thread genuinely blocked by the shared-character case above belongs here — never list a thread you simply chose not to prioritize, found less interesting, or ran out of room for; those still get their normal merged/standalone treatment under the rules above. Most stories will have zero entries here. If no thread was dropped, return an empty array, not an omitted field.

There is no sexual-payoff exception. Comic or plot payoffs merge under the ordinary merging rules. Keep TV-safe; never expand a beat into explicit sexual content.

--- CHAPTER COUNT AND PACING ---

Decide how many episodes this story needs from its {word_count}-word target. Do not default to one episode per hero's-journey step (see above).

Assign each episode a word_count — your estimate, as a plain integer, of how many words it will run to once drafted into full prose. Across the whole outline these must form a real rhythm, not mild variation around an average. Saying "the beats vary" and then writing everything between 1800 and 2800 words is the failure this rule exists to prevent. Concretely, the finished set must satisfy all of:

  - The longest episode is at least 3x the length of the shortest.
  - At least one episode runs under 1000 words.
  - At least one episode runs over 3000 words.
  - No more than half the episodes fall within 20% of the average episode length.

Length is a craft decision, not a quota to satisfy after the fact — choose each episode's size from what it actually does. A short episode is a scalpel: one confrontation, one reveal, one decision landing, a cliff-edge the reader falls off. It works because it is short, and padding it to match its neighbours kills it. A long episode breathes: an extended sequence, a slow build, an encounter given room to develop. Place them for contrast — a 700-word gut-punch immediately after a 3500-word slow burn hits far harder than either would in a row of 2200-word episodes.

A high-priority secondary thread's beats should individually claim a larger word_count, and/or the thread should be returned to across more beats, so its cumulative word_count share of the outline's total actually reflects its priority — not just how many plot points it has.

--- CHAPTER BREAKS ---

Beyond "break where the story wants to break" above, three concrete triggers force a new episode — treat these as hard rules, not suggestions:

  - POV change. Every episode is told from inside one character's head (see CHAPTER POV below); a change of whose head we're in is never absorbed mid-episode, it always starts a new one.
  - Location change. When the action physically moves to a different place, that move starts a new episode rather than being folded into the tail of the episode that came before it. A short episode set entirely in the new location is correct; do not pad the old episode with a scene that belongs to the new place just to avoid a short episode.
  - Major scene change. A shift in who's present, what the scene is actually about, or a real time gap — even at the same location — starts a new episode. Two distinct scenes stitched together because each is individually too short is exactly the padding this rule exists to prevent; a short episode is a valid outcome, not a problem to solve by merging.

These triggers are one of the main tools for hitting the length-variance requirement above — a episode that's just one tight scene bounded by these breaks is often naturally short, and forcing several such scenes into one episode to avoid a "too-short" episode is the wrong fix. Let the breaks land where they land and size the episode to what's actually in it.

--- HOW CHAPTERS END ---

Every episode ending does one of two things: it holds tension into the next episode, or it deliberately releases tension the episode itself built. Decide which on a episode-by-episode basis — do not default to relief just because a beat feels complete.

If the tension from this episode (or an earlier one still open) has NOT been resolved by the last line, end on a cliffhanger: a threat still active, a question still unanswered, a reveal landing with its consequence not yet shown, someone about to act with the outcome withheld. The reader should want the next episode immediately.

If the tension driving this episode HAS genuinely been resolved on the page — the confrontation happened and landed, the relationships payoff completed, the decision got made and its immediate result shown — do not manufacture a fresh cliffhanger just to end on one; a resolved episode is allowed to end resolved. Even then, vary how it closes rather than always fading out flat. Rotate across:

  - quiet gut-punch — no plot threat, but an emotional beat lands hard: a realization, a loss finally felt, a line that reframes what the character just did.
  - ironic button — a short line or image that recontextualizes the episode just read, landing with irony or dark humor rather than dread.
  - hard cut — the episode stops on unresolved dialogue or an action mid-motion, not because the outcome is in doubt but because lingering past it would deflate the moment.
  - true rest — a genuine calm beat, used sparingly (after a major payoff or at a structural low point), where the point is to let the reader (and the story) breathe before the next escalation.

Across the whole outline, these modes — cliffhanger and the three release modes above — should visibly rotate. Ending every episode on a cliffhanger reads as exhausting rather than tense; ending every episode in quiet release reads as inert. Match the mode to what the episode actually did: a episode that ends mid-crisis earns a cliffhanger, a episode that just landed the story's biggest emotional beat earns a quiet gut-punch or true rest, not a bolted-on cliffhanger that undercuts what just happened.

--- CHAPTER POV ---

Every episode is told from inside one character's head. Set `pov_character` to that person's exact name from the CAST list. A POV change always starts a new episode — see CHAPTER BREAKS above; never let two characters' heads share one episode.

The protagonist holds most episodes — they are the story's fixed centre. Shift POV only when there is a real reason: the protagonist is not present for what the episode covers, or the episode's actual turn happens to someone else and is diminished by being reported second-hand. When you do shift, use the most important character present in that episode. Do not rotate POV on a schedule, and do not shift into a character who has nothing at stake in the scene.

The novel's overall perspective and tense (see METADATA) stay fixed across every episode — only whose head we are in changes.

Narration must sound like the POV character, not like a neutral narrator describing them. Set `pov_voice_note` to a short, concrete instruction for how the prose should read in this person's head: their diction and sentence rhythm, what they notice first in a room, what they refuse to look at directly, what they are lying to themselves about, the vocabulary their work or upbringing gives them. A blacksmith and a princess walking into the same hall notice different things and name them with different words — the voice note is what makes that happen on the page.

--- CHAPTER TONE ---

Set `tone` for each episode: its register in a few words (tense and procedural, languid and domestic, claustrophobic, giddy, bleak, sly). This is the episode's own weather, not the season's overall tone restated — a story with a bleak overall tone still has episodes that are warm, funny, or quiet, and the bleakness lands harder for the contrast.

Tone should track pacing: short episodes skew sharp and urgent, long episodes skew immersive. Do not let the same tone run across more than two consecutive episodes.

--- CHAPTER TITLES ---

Give every episode a `title`. A title is a label, not a summary of the episode — the summary is the `content` field you are already writing. Its job is to be short, distinctive, and to make the reader want to start reading.

  - Never begin a title with "The". Not "The Watch's Shadow" — just "Watch's Shadow", or better, something sharper.
  - One or two words. Three only when the third genuinely earns its place.
  - Do not title a episode by describing what happens in it. "The Spire's Summons" announces the plot; a title should land on the one image, object, phrase, or line of dialogue the episode turns on.
  - Draw on the language and naming conventions of this story's cultural setting (see REGION above, if one is given) where it fits naturally — a title in the local language is often stronger than its English translation.
  - Vary the construction across the outline. If three titles in a row are all possessives, or all noun phrases built the same way, the set reads as generated.

Concretely, the first form below is wrong and the alternatives are right:

  The Spire's Summons          ->  Summons          /  Campanile
  The First Lingering Glance   ->  Lingering        /  Glancework
  The Watch's Shadow           ->  Shadow Watch     /  Vigilia

--- CHAPTER ENTITY PRESENCE ---

For every episode, also list which characters, items, locations, groups, and worldbuilding facts are actually PRESENT or actively in play in that episode — not everyone or everything merely mentioned in passing. This is a separate, precise pass over the same episode: a character who appears on the page belongs in `characters_present`; a character whose name is only invoked in someone else's dialogue does not. An item belongs in `items_present` only if it is physically handled, seen, or otherwise load-bearing in the scene, not just referenced as a general concept. A location belongs in `locations_present` only if the episode's action actually happens there. A group belongs in `groups_present` only if the episode involves it as a collective (a meeting, an order given in its name, a confrontation with it) — an individual member appearing on their own does not put their group in the list. A worldbuilding fact belongs in `worldbuilding_facts_present` only if the episode's events actively depend on or demonstrate that fact, not merely take place in a world where it happens to be true.

Every name/title in these five lists must be an exact match to a name already given above (CAST, ITEMS, LOCATIONS, GROUPS, WORLDBUILDING FACTS) — never invent one. `pov_character` is always included in `characters_present` for that episode. These lists exist so a later step can pull only the relevant story-bible entries into a episode's prose-generation context instead of the whole story — an incomplete or overcautious list directly means a scene gets written without the character/item/location information it needed, so err toward including anyone or anything the scene genuinely uses rather than trimming the list defensively.

This is a first pass, not the final outline — a separate editing pass reviews it afterward for structural and continuity issues, so focus your effort here on getting real, concrete, well-imagined content onto the page rather than on self-checking every rule above. Write it as well as you can in one continuous pass.

Return the outline as a JSON object using the schema below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_OUTLINE_SCHEMA = {
    "outline": [
        {
            "title": "Chapter title — one to three words. Never begins with \"The\" or any other article. Lands on the episode's central image, object, or phrase rather than describing its events. Not 'Chapter One'.",
            "content": "Specific, concrete beat description at whatever length the beat actually needs — a brief moment can be a couple of sentences to a short paragraph, a full scene several dense paragraphs. Covers the specific sequence of actions and sub-moments, who is involved, at least one concrete line of dialogue or interior thought where length allows, sensory texture of the setting, each present character's emotional shift, what changes, and how it connects to the surrounding beats. Specific enough to draft prose from directly with nothing load-bearing left to invent.",
            "word_count": 350,
            "pov_character": "Exact name from the CAST list whose head this episode is told from — usually the protagonist.",
            "pov_voice_note": "How the prose should sound in this person's head: diction and sentence rhythm, what they notice first, what they avoid looking at, what they are lying to themselves about. Concrete enough to change the writing, not a restatement of their personality.",
            "tone": "This episode's register in a few words, e.g. 'tense and procedural' or 'languid, domestic' — not the season's overall tone restated.",
            "characters_present": ["Exact name from the CAST list, present or actively in play in this episode — always includes pov_character"],
            "items_present": ["Exact name from the ITEMS list, present or actively in play in this episode"],
            "locations_present": ["Exact name from the LOCATIONS list where this episode's action actually happens"],
            "groups_present": ["Exact name from the GROUPS list, involved as a collective in this episode"],
            "worldbuilding_facts_present": ["Exact title from the WORLDBUILDING FACTS list, actively depended on or demonstrated in this episode"],
        }
    ],
    "skipped_threads": [
        {
            "thread_index": "Position of the dropped thread in the SECONDARY ARCS list — see SKIPPED THREADS above. Only a thread blocked by the shared-character physical/temporal conflict belongs here.",
            "reason": "One or two sentences naming the shared character and the physical/temporal conflict that made this thread impossible to place anywhere in the outline.",
        }
    ],
}


# --- ENTITIES ---
# Ported and merged from V2's separate locations/items/groups/events
# steps (src/prompts/outline.py) into a single call. Cross-references here
# are anchored to the season's premise/summary, primary thread, and character
# list, and characters/groups are cross-referenced by name rather
# than by a spine-assigned uuid (V3's primary thread plot points aren't
# uuid-addressable the way V2's were).

INIT_ENTITIES_USER_PROMPT = """

The following is the metadata, worldbuilding, cast, and primary thread already established for a story. Do not stray from them.

--- METADATA ---
{novel_metadata}

--- WORLDBUILDING ---
{worldbuilding}

--- CHARACTERS ---
{characters}

--- SPINE ---
{primary_thread}

--- SECONDARY ARCS ---
{secondary_arcs}

--- SIDE CHARACTERS ---

Generate the side characters this story needs — the people who populate the world around the main cast but were not worth a full character-bible entry at the casting stage. Keep this list SHORT. This story is {word_count} words long, which gives it room for about {side_character_target} side characters — generate that many. One or two either side is acceptable if the plot genuinely demands it, but treat {side_character_target} as the number to hit, not a floor to build on. This is a tight supporting cast, not a census of the setting: a side character needs roughly 2500 words of story to be worth introducing at all, and every name past that budget is one the reader meets, half-remembers, and never sees again.

Work strictly from the SPINE and SECONDARY ARCS above. Go through the plot points and ask which specific people those beats cannot happen without — the person who has to deliver the message, the one guarding the door the protagonist must get past, the confidant a thread depends on. Those are your side characters. If you cannot point at the plot point that requires someone, do not generate them: a person who merely makes the world feel more populated is not needed, because the prose writer can use an unnamed passer-by for that.

Then merge aggressively. Draft the list of every role the plot points imply, then collapse it: any two roles that could plausibly be held by the same person become one person. The guard on the gate and the guard at the cell are one guard. The neighbour who notices too much and the witness who later testifies are one neighbour. The clerk who files the record and the clerk who leaks it are one clerk — and that person is far more interesting for doing both. Keep collapsing until you are at {side_character_target}.

Merging is not a compromise; it is what makes these people worth having. A recurring named face the reader comes to know, who turns up in four scenes wearing different hats, is worth more than four walk-ons who each appear once. Every additional name costs the reader something to keep track of and gets nothing back. Never generate two side characters with near-identical roles — two guards, two clerks, two priests, two soldiers — unless a single plot point genuinely puts both on the page at the same time and they must be distinct people.

Side characters default to young adults and are as attractive as the main cast — this is the same world and the same standard, not a background populated by worn-out extras. Unless a role genuinely requires age, put them in their twenties or thirties, and write them as good-looking people with real presence. Do not use age as shorthand for a job: a doorman, a bartender, a driver, a guard, a shopkeeper, or a nurse is far more likely to be young than grizzled, and reaching for a weathered veteran every time a functionary is needed is exactly the reflex to avoid. Older characters are allowed only where the role actually demands the years — a senior figure whose authority rests on a long career, a parent or grandparent, a master of a craft that takes decades — and even then they should be attractive for their age rather than written as decrepit.

Each one gets a `role` of either `side` or `background`, using the same two lightest tiers as the main cast:

  - side — recurs across a handful of scenes to serve a specific narrative function (the confidant, the person guarding the door, the one who delivers the message). Give them: appearance as 1-2 sentences of real sensual, physical specificity — who they are to look at, not just their job title; personality as 1-2 short traits; speech_patterns as 1-2 entries only if they actually speak on the page. Do not write backstory, fears, flaws, contradictions, hobbies, or spiritual_beliefs — omit those fields entirely.
  - background — present for texture or a single functional beat, nothing more. Give them: appearance as a single brief sentence; personality as one short trait or none. Omit every other field entirely, including speech_patterns.

Most of this batch should be `side`; reach for `background` only for someone who is little more than a name attached to a moment. The same appearance rules as the main cast apply at whatever length each tier calls for: no scars, injuries, or disfigurements — distinguish people by colouring, build, dress, bearing, voice, and mannerism instead, with tattoos and piercings allowed as deliberate style choices — and female side characters default to having large breasts, with the rest of their figures varied so they do not read as interchangeable. Do not re-generate anyone already in the CHARACTERS list above, and do not give a side character a plot arc of their own; they exist to serve scenes the main cast is already in.

If a side character is family to someone already in the CHARACTERS list above — a sibling, parent, child, or spouse — give them that person's exact surname rather than inventing an unrelated one. The same applies among the side characters you generate here: two side characters who are family to each other share a surname. A side character with no family connection to the cast gets whatever surname fits the world.

--- HOW TO NAME THINGS ---

This applies to every name you generate below — locations, items, groups, and events.

A name is a label, not a description. What a thing IS belongs in its `description` field, which you are already writing. The name's job is to be short, distinctive, and memorable.

  - Never begin a name with "The". Not "The Drowned Bazaar" — just the name.
  - One or two words. Three only when the third genuinely earns its place.
  - Do not name a thing by describing it. "The Silver-Tipped Oar" tells the reader what the object looks like; a name tells them what people call it.
  - Draw on the language and naming conventions of this story's cultural setting (see REGION above, if one is given), so the names sound like they come from one coherent place rather than from generic fantasy English.
  - Coined words, compounds, possessives, and place-derived names all work. Vary the construction — if three names in a row are built the same way, the set reads as generated.

Concretely, the first form below is wrong and the alternatives are right:

  The Silver-Tipped Oar        ->  Remo d'Argento   /  Greyoar
  The Drowned Bazaar           ->  Mercato Sommerso /  Sunkmarket
  The Order of the Burnt Word  ->  Ordine Cenere    /  Ashwrit
  The Iron Throat Chain        ->  Gorgiera         /  Throatiron

--- LOCATIONS ---

Generate a rich and varied set of locations that populate this story's world. Think spatially and socially: where do people live, work, eat, drink, hide, fight, worship, conduct business, find pleasure, suffer consequences? What locations would a person in this world encounter in the natural course of living? They do not all need to be plot-critical — some exist to give the world texture and give prose writers somewhere to put characters. Make each one distinct in atmosphere, purpose, and feel — no two should read the same. Write atmospheric and physical detail sufficient to write scenes there: what it looks like, what it smells and sounds like, its mood, its access rules if any, its significance to the story.

--- ITEMS ---

Generate a rich and varied inventory of objects that populate this story's world. Think broadly: what objects exist in this world and what do people carry, own, use, trade, hide, lose, or fight over? Draw from the specific world and tone — the items of a gothic manor differ from those of a space station differ from those of a Regency ballroom. Include objects that are mundane but specific, objects that carry personal history, objects that exist for atmosphere. Key items get full detail including symbolic weight. Minor objects get a brief note.

--- GROUPS ---

Generate a rich and varied set of groups that populate this story's world. A group is any set of people who belong together as a unit — at any scale. That includes small, informal, personal groupings as much as large institutional ones: a friend group, a band, a book club, a family, a household, a crew, a roommate situation, a recurring poker night, a support group, a team — alongside governments, courts, guilds, churches, criminal syndicates, trading houses, secret societies, noble houses, political factions, gangs, schools, hospitals, cults, unions, press outlets, intelligence agencies, and corporations. Do not generate only large formal institutions; the small personal groups are usually the ones the characters actually live inside day to day, and a story with only megacorps and governments and no friend groups or families is missing the texture that matters most. Aim for a genuine mix of scales.

Groups do not all need to directly touch the plot — some exist to give the world social texture, to explain why things work the way they do, to give characters somewhere to belong or something to resist. Make each one distinct in type, purpose, and tone. Write a prose description (a plain string, not a nested object with separate fields) that covers what holds the group together, what it wants, how someone gets in or out, who has power inside it, and what pressure it applies to the plot — woven together into ordinary paragraph text, the same way the LOCATIONS and ITEMS descriptions are written.

For each group, list its members in `associated_characters` — every name must be an exact name from either the CHARACTERS list above or the side characters you just generated. A group whose members are all unnamed background people gets an empty list, but prefer groups that at least one named character actually belongs to. A character may belong to several groups, and most named characters should belong to at least one.

Size each group's description to how many `protagonist`/`antagonist`/`main`-tier characters actually belong to it, not to how interesting the group idea is in the abstract. A group built around two or more main-tier characters is central to the story and earns a real paragraph — its internal dynamics, what it costs each of those specific characters to belong, how it bears on the plot. A group with exactly one main-tier character and the rest supporting/side/background gets a shorter, plainer description — enough to place scenes in it, no more. A group with no main-tier character at all (purely supporting/side/background members) is pure world texture — two or three sentences is enough; do not invest paragraph-level development in a group none of the leads belong to.

Family is one specific case of this: do not manufacture a family group for a character just because they exist. Only form a family group where two or more characters who actually appear in this cast — main or otherwise — share a surname (spouses, parents and children, siblings). A character whose only relatives are unnamed or absent from the story does not get a family group; there is nothing to group them with. Where a real family of two or more does exist in the cast, name it per the world's convention (e.g. "House Moretti", "the Okafors") and size its description exactly like any other group above: a family carrying multiple main-tier characters gets full treatment, a family of side/background characters gets a couple of sentences. `associated_characters` lists every member of that family exactly as named above.

--- EVENTS ---

Using the metadata, worldbuilding, cast, and the side characters/locations/items/groups you just generated, expand each primary thread plot point above into a concrete event — turning points, confrontations, revelations, and key moments consistent with the forbidden element and the protagonist's arc. Every event must map to a real primary thread plot point; do not invent events unconnected to the primary thread. For each, write enough detail to make it writable: who is present, what concretely happens, what changes as a result, what the emotional weight of the moment is, and whether it has occurred, is pending, or was prevented by the time the story begins. Every name listed in characters_involved must be an exact name from the CHARACTERS list above or the side characters you just generated. Every name listed in groups_involved must be an exact name from the groups you generated above. Do not invent events that contradict the metadata, worldbuilding, or primary thread.

Before returning, validate: no location, item, group, or event name begins with "The" or any other article, and none runs longer than two words without a real reason — rename any that do; no two names are built the same way; the side character count is at or near {side_character_target}, and each one can be traced to a specific plot point that cannot happen without them — cut any who cannot, and merge any two whose roles could be filled by one person; no two side characters hold near-identical roles or belong to the same profession without a scene that puts both on the page together; no side character duplicates a name already in the CHARACTERS list; every side character has `role` set to either `side` or `background`, with fields sized to that tier (no `background` character carries backstory, fears, flaws, contradictions, hobbies, spiritual_beliefs, or speech_patterns); side characters are young adults and attractive except where a role genuinely requires age, with no functionary aged up by default; every location, item, and group is distinct and fits the world and tone of the intro prompt; the groups span a real range of scales rather than being all large institutions, with small personal groups (friend groups, families, bands, crews) represented; every group's description length actually tracks how many protagonist/antagonist/main-tier characters belong to it — cut any paragraph-length description down where a group has at most one main-tier member, and expand any group with two or more main-tier members that was left thin; every surname shared by two or more characters who appear in the CHARACTERS or side characters lists has a corresponding family group whose `associated_characters` includes all of them, and no family group exists for a character whose relatives don't otherwise appear in the cast; every group's `associated_characters` names match the CHARACTERS list exactly; every entity's `description` (and every event's `description`) is a single plain string of prose, never a nested object with separate named fields; every event maps to a primary thread plot point; every event's characters_involved and groups_involved names match the CHARACTERS list or entries generated above exactly, with no placeholder or invented names.

When completed, format everything into a single JSON object that follows the format below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_ENTITIES_SCHEMA = {
    "side_characters": [
        {
            "name": "Side character name",
            "role": "side | background",
            "occupation": "A single plain-text string: what they do, and their standing in the world.",
            "age": 0,
            "gender": "female | male | other",
            "appearance": "side: 1-2 sensual, specific sentences on how they look and carry themselves. background: a single brief sentence.",
            "personality": ["side: 1-2 short traits. background: one trait or omit this field entirely."],
            "speech_patterns": ["side only, 1-2 entries, if they speak on the page — omit entirely for background"],
        }
    ],
    "locations": [
        {
            "name": "Location name",
            "description": "Plain prose string (not an object): what it looks like, sounds like, smells like, its mood, its access rules if any, and its significance to the story.",
        }
    ],
    "items": [
        {
            "name": "Item name",
            "description": "Plain prose string (not an object): what it is, its symbolic weight, and its significance.",
        }
    ],
    "groups": [
        {
            "name": "Group name",
            "description": "Plain prose string (not an object with separate fields): what holds this group of people together, what it wants, how someone gets in or out, who has power inside it, and what pressure it applies to the plot, all woven into one flowing description.",
            "associated_characters": ["Exact name of a character from the CHARACTERS list who belongs to this group"],
        }
    ],
    "events": [
        {
            "title": "Event name",
            "description": "Plain prose string (not an object): what happens, what changes as a result, the emotional weight, and whether it has occurred, is pending, or was prevented.",
            "characters_involved": ["Exact name of a character from the CHARACTERS list"],
            "groups_involved": ["Exact name of a group generated above"],
        }
    ],
}


# --- INITIAL STATE ---
# The starting relationship graph, as of story-start (before episode one).
# Character-outward and asymmetric: a relationship is only emitted from a
# character's side if it actually exists for them. Do not emit a symmetric
# pair by default — if the protagonist has never met a character, there must
# be no character_relationships entry for protagonist -> that character, even
# if that character has a real, populated entry pointing at the protagonist
# (e.g. a stalker who knows the protagonist well).

INIT_RELATIONSHIPS_USER_PROMPT = """

The following is everything already established for this story: metadata, cast, and world. Do not stray from them.

--- METADATA ---
{novel_metadata}

--- CHARACTERS ---
{characters}

--- LOCATIONS ---
{locations}

--- ITEMS ---
{items}

--- GROUPS ---
{groups}

--- WORLDBUILDING FACTS ---
{worldbuilding_facts}

--- EVENTS ---
{events}

--- INSTRUCTIONS ---

Establish the relationship graph as it stands at the moment the story begins — before episode one, reflecting everything implied by the metadata, character stubs, and events above.

Only characters and groups can hold a relationship — they are the only entities capable of a disposition toward something. Items, locations, and worldbuilding facts can only ever be the target of a relationship, never the subject: an item does not have a relationship to the character holding it.

This is subject-outward and asymmetric. For each character or group, only emit a relationship entry if that character or group actually has one. Do not generate an entry for every possible pair; most pairs in an ensemble cast have no relationship yet and must be skipped entirely. A relationship existing from one side does not mean it exists from the other: if the protagonist has never met a character, emit nothing for protagonist -> that character, even if that character knows the protagonist well and has a real entry pointing back at them (a stalker, a spy, a secret admirer, a family member the protagonist doesn't remember). One-sided relationships are expected and correct, not a mistake to fix.

For character-to-character and group-to-group relationships, only include emotional_intensity when there is a real emotional charge to the relationship — leave it out (or use 0) for something genuinely neutral like a distant acquaintance.

For character-to-item, character-to-location, and character/group-to-worldbuilding-fact relationships, only emit entries for connections that actually matter to the story — an item they own or are searching for, a location that's their home or that they're barred from, a law that constrains them specifically. Do not emit an entry just because a character has technically seen or passed through a location, or could plausibly know an item or law exists.

Group relationships (group_relationships) are for genuinely collective, shared stances — "the Thieves' Guild is at war with the Crown" — not one member's personal opinion; an individual member's exception belongs in that character's own character_relationships entry instead, which takes priority over their group's stance for the same target. Do not duplicate a group's stance as an identical entry for every one of its members — only give a character their own entry when their view actually differs from or adds detail beyond their group's.

Every character, item, location, group, and worldbuilding fact name used below must be an exact name/title from the lists above — no invented or placeholder names.

When completed, format everything into a single JSON object that follows the format below. Do not stray from this schema.

{schema}

Return only the JSON object, no other text.

"""

INIT_RELATIONSHIPS_SCHEMA = {
    "character_relationships": [
        {
            "character": "Exact name of the character this relationship belongs to",
            "target_type": "character | item | location | group | worldbuilding_fact",
            "target": "Exact name/title of the target",
            "relationship_type": "e.g. rival | ally | mentor | romantic_tension | family | stranger | threat | owner | custodian | seeking | home | banned | sacred",
            "status": "Current status of the relationship in plain language.",
            "emotional_intensity": 6,
            "open_threads": "What is unresolved between them, in plain language.",
        }
    ],
    "group_relationships": [
        {
            "group": "Exact name of the group this relationship belongs to",
            "target_type": "character | item | location | group | worldbuilding_fact",
            "target": "Exact name/title of the target",
            "relationship_type": "e.g. rival | ally | at_war | patron | seeking | home | banned | sacred",
            "status": "Current status of the relationship in plain language.",
            "emotional_intensity": 6,
            "open_threads": "What is unresolved about it, in plain language.",
        }
    ],
}
