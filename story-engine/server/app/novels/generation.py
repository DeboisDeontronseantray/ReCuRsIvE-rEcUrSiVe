import json
import math
import random
import re

from app.model_routing import DEFAULTS, call_model
from app.novels.names import DEFAULT_REGION, build_name_pool
from app.prompts import outline_editing_prompts, outline_prompts

# User-supplied target word count is capped here rather than trusting the
# client — this is the ceiling for the *base* count the primary thread is
# built from; calculate_word_count's bonuses can still push the actual
# primary thread target above this.
MAX_INITIAL_WORD_COUNT = 20000

# Default weights for calculate_word_count. flat_bonus_pct is the fraction of
# initial_word_count always added on top, regardless of secondary threads.
# per_thread_base_pct is the fraction of initial_word_count a single
# secondary thread can contribute at most (length=100, priority=100,
# heat=100). heat_weight controls how much heat alone can inflate a thread's
# contribution beyond what length/priority already produced.
DEFAULT_WORD_COUNT_WEIGHTS = {
    "flat_bonus_pct": 0.25,
    "per_thread_base_pct": 0.10,
    "heat_weight": 0.3,
}

# Per-step max_tokens overrides, passed to call_model instead of the model's
# own default cap (see model_routing.yaml). Steps that return one bounded
# object (init_novel, init_worldbuilding) are fine on the model's default and
# aren't listed here. Steps listed below return many long, per-item passages
# (multiple characters each with several paragraph-level fields; 9 dense
# primary-thread beats; 2-4 beats per secondary thread; 20-30+ dense outline
# beats; a relationship graph spanning every character/group against every
# other character, item, location, group, and worldbuilding fact; side
# characters plus locations, items, groups, and events all in one call) whose
# total output regularly exceeds a model's default budget once combined with
# JSON structural overhead — each has been truncated in practice
# (finish_reason='length') at the default 16000 before getting its own larger
# budget here.
CHARACTERS_MAX_TOKENS = 40000
PRIMARY_THREAD_MAX_TOKENS = 24000
SECONDARY_ARCS_MAX_TOKENS = 24000
OUTLINE_MAX_TOKENS = 32000
OUTLINE_AUDIT_MAX_TOKENS = 32000
RELATIONSHIPS_MAX_TOKENS = 24000
ENTITIES_MAX_TOKENS = 32000

# Computes the primary thread's target word count from the user's requested
# base word count plus a bonus for every secondary thread attached to the
# story. This is additive, not a shared budget — secondary threads add to the
# primary thread's target on top of the user's number, since each thread
# generates its own separate content downstream (see init_secondary_arcs).
#
# Formula: base + (base * flat_bonus_pct) + sum(per-thread bonus), where each
# thread's bonus is base * per_thread_base_pct * (length/100) * (priority/100)
# * (1 + heat_weight * heat/100) — length and priority are the primary
# drivers (multiplicative, so a thread needs to be both long and
# high-priority to matter much), heat is a smaller modifier on top of that,
# reflecting that legacy heat weight remains in the formula but TV-safe mode does not add romantic scenes; it isn't
# what makes a thread long on its own.
def calculate_word_count(
    initial_word_count: int,
    secondary_threads: list[dict] | None = None,
    weights: dict | None = None,
) -> int:
    weights = {**DEFAULT_WORD_COUNT_WEIGHTS, **(weights or {})}
    base = max(1, min(initial_word_count, MAX_INITIAL_WORD_COUNT))

    total = base + base * weights["flat_bonus_pct"]
    for thread in secondary_threads or []:
        length = thread.get("length", 0) / 100
        priority = thread.get("priority", 0) / 100
        heat = thread.get("heat", 0) / 100
        thread_bonus = base * weights["per_thread_base_pct"] * length * priority * (
            1 + weights["heat_weight"] * heat
        )
        total += thread_bonus

    return round(total)


# Keeps only the leading length_pct% of a secondary arc's plot points,
# discarding the rest. init_secondary_arcs always generates a thread's
# complete arc (see outline_prompts.INIT_SECONDARY_ARCS_USER_PROMPT) —
# this function is what actually enforces `length`, mechanically, so the
# model's own judgment about "how much is enough" is never load-bearing.
# The cut lands on a plot-point boundary rather than a word/character count,
# so it can never land mid-sentence. Rounds up (ceiling), minimum 1 kept
# point for any length_pct > 0 — e.g. 11 points at length=30 (11*0.3=3.3)
# keeps 4, not 3; 5 points at length=50 (5*0.5=2.5) keeps 3, not 2 (avoiding
# Python's round() banker's-rounding surprise on exact .5 values).
def truncate_secondary_arc(plot_points: list[dict], length_pct: int) -> list[dict]:
    if not plot_points:
        return []
    keep_count = max(1, math.ceil(len(plot_points) * length_pct / 100))
    return plot_points[:keep_count]


# Randomly samples 2-4 conventions (mixed pool: common + deep_cuts combined,
# no guaranteed deep cut, no fixed split) from each genre entry returned by
# init_genre_conventions, flattening the per-genre {common, deep_cuts} pools
# into one flat list the rest of the pipeline (genre_conventions column,
# novel_metadata passthrough) can consume directly. Each selected item keeps
# its genre and which pool (common/deep_cut) it came from, so the type
# information survives the random mixing.
def select_genre_conventions(genre_conventions: list[dict]) -> list[dict]:
    selected = []
    for entry in genre_conventions:
        genre = entry.get("genre")
        pool = (
            [(c, "common") for c in entry.get("common", [])]
            + [(c, "deep_cut") for c in entry.get("deep_cuts", [])]
        )
        if not pool:
            continue
        k = random.randint(2, 4)
        for convention, kind in random.sample(pool, min(k, len(pool))):
            selected.append({"genre": genre, "convention": convention, "type": kind})
    return selected


# Calls a model and parses its JSON, retrying once if the response comes back
# malformed. Models occasionally emit a truncated or subtly broken object — an
# unescaped quote, a trailing comma — and with no retry a single bad response
# kills an entire novel generation partway through. The retry is unconditional
# rather than correction-guided: the prompt was already correct, the response
# just landed badly, so asking again is the whole fix.
#
# Steps with their own richer retry (init_secondary_arcs' correction pass,
# init_outline's truncation pass) layer on top of this.
def _call_and_parse(
    model: str,
    system_prompt: str,
    user_prompt: str,
    reasoning: bool = False,
    max_tokens: int | None = None,
) -> dict:
    for attempt in (1, 2):
        text = call_model(
            model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=max_tokens
        )
        try:
            return _extract_json(text, model)
        except RuntimeError:
            if attempt == 2:
                raise
            print(f"[{model}] malformed JSON, retrying once", flush=True)
    raise RuntimeError(f"unreachable: {model}")  # pragma: no cover


# Pulls the first {...} JSON object out of a model response.
def _extract_json(text: str, label: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"No JSON found in {label} response: {text[:200]}")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Malformed JSON in {label} response: {e}") from e


# Builds the combined intro prompt from the title plus the five user-facing
# sections (ported from V2's single-prompt --- Premise/Tone/Characters/Story
# Structure --- sections), plus any secondary threads. Empty sections
# are omitted rather than included blank.
#
# include_characters_notes is True only for init_novel and init_characters —
# once init_characters has generated the real cast, every later step should
# see that generated cast instead of the user's raw Characters notes, so
# those steps rebuild the prompt with include_characters_notes=False rather
# than sending the model both a rough draft and a finished character sheet.
def _build_intro_prompt(
    title: str,
    premise: str,
    tone_notes: str | None,
    characters_notes: str | None,
    worldbuilding_notes: str | None,
    primary_thread: str | None,
    secondary_threads: list[dict] | None,
    include_characters_notes: bool = True,
    include_secondary_threads: bool = True,
) -> str:
    sections = [f"Title: {title}", f"--- Premise ---\n{premise}"]
    if tone_notes:
        sections.append(f"--- Tone ---\n{tone_notes}")
    if include_characters_notes and characters_notes:
        sections.append(f"--- Characters ---\n{characters_notes}")
    if worldbuilding_notes:
        sections.append(f"--- Worldbuilding ---\n{worldbuilding_notes}")
    if primary_thread:
        sections.append(f"--- Story Structure ---\n{primary_thread}")
    # `length` is deliberately not rendered — it is enforced mechanically in
    # Python (truncate_secondary_arc) and init_secondary_arcs is explicitly
    # told to ignore it, so showing the model "N% of this storyline resolved"
    # only invites it to reason about how much story is left.
    if include_secondary_threads and secondary_threads:
        thread_lines = "\n\n".join(
            f"Thread {i}: {t['description']}\n"
            f"(priority: {t['priority']}/100, heat: {t['heat']}/100)"
            for i, t in enumerate(secondary_threads, start=1)
        )
        sections.append(f"--- Secondary Threads ---\n{thread_lines}")
    return "\n\n".join(sections)


# Rebuilds the intro prompt from a novel row (as stored in the DB) with the
# Characters notes section dropped — used once init_characters has generated
# the real cast, so downstream steps see the finished character sheet
# instead of the user's raw notes.
#
# include_secondary_threads defaults to False because init_secondary_arcs is
# the LAST step allowed to see the raw thread descriptions. A description is
# frequently a complete storyline including its ending; every step after the
# arcs step must see only the already-truncated plot points, or it will write
# toward an ending it was never supposed to know about. That leak — the raw
# description sitting in the system prompt under "this is the north star for
# the story, do not stray from this" — is why low-`length` threads kept
# arriving fully resolved. Only the init_secondary_arcs call passes True.
def _post_characters_prompt(
    novel: dict,
    secondary_threads: list[dict] | None,
    include_secondary_threads: bool = False,
) -> str:
    return _build_intro_prompt(
        novel.get("title", ""),
        novel.get("premise", ""),
        novel.get("tone_notes"),
        novel.get("characters_notes"),
        novel.get("worldbuilding_notes"),
        novel.get("primary_thread"),
        secondary_threads,
        include_characters_notes=False,
        include_secondary_threads=include_secondary_threads,
    )


# Builds the intro prompt seen by init_worldbuilding — title, setting_context,
# tone, characters_notes, and the user's own worldbuilding_notes. Deliberately
# NOT built via _build_intro_prompt, which always renders a "--- Premise ---"
# section unconditionally: worldbuilding must never see the premise, primary
# thread, or plot endings, since those describe concrete plot events, and
# a worldbuilding pass that sees them tends to invent "facts" that just
# rationalize what the story already describes rather than independently
# deriving rules the story is then built to obey.
#
# setting_context (generated by init_novel — see INIT_NOVEL_SCHEMA) is the
# deliberate exception: it is a plot-free description of the world/environment
# only (occupation, institution, location type — e.g. "a corporate office
# running an internal audit team"), extracted specifically so worldbuilding
# can reflect the kind of place the story is set in without ever seeing what
# happens there. characters_notes and worldbuilding_notes are included for the
# same reason — they are concepts/setting descriptions, not plot events.
def _worldbuilding_prompt(novel: dict) -> str:
    sections = [f"Title: {novel.get('title', '')}"]
    if novel.get("setting_context"):
        sections.append(f"--- Setting ---\n{novel['setting_context']}")
    if novel.get("tone_notes"):
        sections.append(f"--- Tone ---\n{novel['tone_notes']}")
    if novel.get("characters_notes"):
        sections.append(f"--- Characters ---\n{novel['characters_notes']}")
    if novel.get("worldbuilding_notes"):
        sections.append(f"--- Worldbuilding ---\n{novel['worldbuilding_notes']}")
    return "\n\n".join(sections)


# Calls the LLM to generate the novel metadata from the title and the five
# intro-prompt sections. Any of primary_genre/author/themes passed in are
# treated as fixed user choices rather than left for the model to infer.
# word_count is the primary thread's target, computed server-side by
# calculate_word_count (see router.create_novel) from the user's requested
# word count plus the secondary threads' bonuses.
def init_novel(
    title: str,
    premise: str,
    word_count: int,
    tone_notes: str | None = None,
    characters_notes: str | None = None,
    worldbuilding_notes: str | None = None,
    primary_thread: str | None = None,
    secondary_threads: list[dict] | None = None,
    primary_genre: str | None = None,
    author: str | None = None,
    themes: list[str] | None = None,
    tense: str | None = None,
    perspective: str | None = None,
    model: str = DEFAULTS["metadata"],
    reasoning: bool = False,
) -> dict:
    intro_prompt = _build_intro_prompt(
        title,
        premise,
        tone_notes,
        characters_notes,
        worldbuilding_notes,
        primary_thread,
        secondary_threads,
    )
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=intro_prompt)
    user_prompt = outline_prompts.INIT_NOVEL_USER_PROMPT.format(
        word_count=word_count,
        schema=json.dumps(outline_prompts.INIT_NOVEL_SCHEMA, indent=2),
    )

    overrides = {
        "primary_genre": primary_genre,
        "author": author,
        "themes": themes or None,
        "tense": tense,
        "perspective": perspective,
    }
    overrides = {k: v for k, v in overrides.items() if v}
    if overrides:
        user_prompt += outline_prompts.INIT_NOVEL_USER_OVERRIDES_TEMPLATE.format(
            overrides=json.dumps(overrides, indent=2)
        )

    data = _call_and_parse(model, system_prompt, user_prompt, reasoning=reasoning)

    novel = data.get("novel", {})
    novel["prompt"] = intro_prompt
    return novel


# Calls the LLM to generate two convention pools (common, deep_cuts) for each
# genre name derived from init_novel's output — primary_genre plus every
# sub_genres entry, each treated as an independent genre. Deliberately
# plot-blind (see outline_prompts.INIT_GENRE_CONVENTIONS_USER_PROMPT) — uses
# the same restricted _worldbuilding_prompt scope as init_worldbuilding, not
# the full intro prompt, so conventions describe the genre generally rather
# than leaking this story's actual plot into "genre conventions." Runs
# immediately after init_novel and before the novels row is inserted (see
# router.create_novel) because its output (genre_conventions, after
# select_genre_conventions above) is persisted as part of that same row.
def init_genre_conventions(
    generated: dict,
    model: str = DEFAULTS["genre_conventions"],
    reasoning: bool = False,
) -> list[dict]:
    genres = [g for g in [generated.get("primary_genre"), *(generated.get("sub_genres") or [])] if g]
    if not genres:
        return []
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=_worldbuilding_prompt(generated))
    user_prompt = outline_prompts.INIT_GENRE_CONVENTIONS_USER_PROMPT.format(
        novel_metadata=json.dumps(generated, indent=2),
        genres=json.dumps(genres, indent=2),
        schema=json.dumps(outline_prompts.INIT_GENRE_CONVENTIONS_SCHEMA, indent=2),
    )
    data = _call_and_parse(model, system_prompt, user_prompt, reasoning=reasoning)
    return data.get("genre_conventions", [])


# Serializes the worldbuilding block for a prompt. Every step that sends
# worldbuilding MUST go through this: prompt caching keys on an exact prefix
# match, so a difference in key order or indentation between two steps costs
# the cache hit. sort_keys pins the ordering regardless of how the dict was
# built (model output vs rebuilt from the database).
def _worldbuilding_json(worldbuilding: dict) -> str:
    return json.dumps(worldbuilding, indent=2, sort_keys=True)


# Calls the LLM to generate the character list from the novel's metadata and
# the already-generated world. Runs after init_worldbuilding so the cast is
# built to fit a world that is already fixed — occupation, class, belief and
# assumptions about privacy all follow from it.
def init_characters(
    novel: dict,
    worldbuilding: dict,
    name_pool: dict | None = None,
    model: str = DEFAULTS["characters"],
    reasoning: bool = False,
) -> dict:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    seeds = novel.get("character_seeds") or []
    generation_notes = novel.get("character_generation_notes")
    user_prompt = outline_prompts.INIT_CHARACTERS_USER_PROMPT.format(
        name_pool=json.dumps(name_pool or build_name_pool(novel.get("region")), indent=2),
        character_seeds=(
            json.dumps(seeds, indent=2) if seeds else "None — name the whole cast from the pool."
        ),
        generation_notes_clause=(
            outline_prompts.CHARACTER_GENERATION_NOTES_CLAUSE.format(notes=generation_notes)
            if generation_notes
            else ""
        ),
        worldbuilding=_worldbuilding_json(worldbuilding),
        novel_metadata=json.dumps(novel, indent=2),
        schema=json.dumps(outline_prompts.INIT_CHARACTERS_SCHEMA, indent=2),
    )

    data = _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=CHARACTERS_MAX_TOKENS
    )
    return data.get("characters", [])


# Calls the LLM to generate the world — story type, time period, anchor
# location, plus a detailed list of facts across society/physical/systems/
# relationships worldbuilding. Runs FIRST, before the cast exists, so every later step (characters
# included) is built to fit a world that is already fixed.
#
# Returns the full {story_type, ..., facts: [...]} dict, not just the core.
def init_worldbuilding(
    novel: dict,
    model: str = DEFAULTS["worldbuilding"],
    reasoning: bool = False,
) -> dict:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=_worldbuilding_prompt(novel))
    user_prompt = outline_prompts.INIT_WORLDBUILDING_USER_PROMPT.format(
        region=novel.get("region") or DEFAULT_REGION,
        novel_metadata=json.dumps(novel, indent=2),
        schema=json.dumps(outline_prompts.INIT_WORLDBUILDING_SCHEMA, indent=2),
    )

    data = _call_and_parse(model, system_prompt, user_prompt, reasoning=reasoning)
    return {**data.get("worldbuilding", {}), "facts": data.get("facts", [])}


# Calls the LLM to generate the protagonist's full hero's-journey primary
# thread — deep detail, character moments and feelings included, not just
# plot events. Identifies the protagonist/antagonist from the generated cast
# rather than needing separate stubs (see
# outline_prompts.INIT_PRIMARY_THREAD_USER_PROMPT). The target word count is
# fixed by the caller (novel["word_count"], computed server-side by
# calculate_word_count) rather than self-decided by the model — the plot
# point count and pacing must be proportional to that fixed target. This is
# an internal generation input now — the outline (see init_outline below) is
# what the user actually reads and edits.
def init_primary_thread(
    novel: dict,
    worldbuilding: dict,
    characters: list[dict],
    model: str = DEFAULTS["primary_thread"],
    reasoning: bool = False,
) -> list[dict]:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    user_prompt = outline_prompts.INIT_PRIMARY_THREAD_USER_PROMPT.format(
        novel_metadata=json.dumps(novel, indent=2),
        worldbuilding=_worldbuilding_json(worldbuilding),
        characters=json.dumps(characters, indent=2),
        word_count=novel.get("word_count"),
        schema=json.dumps(outline_prompts.INIT_PRIMARY_THREAD_SCHEMA, indent=2),
    )

    data = _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=PRIMARY_THREAD_MAX_TOKENS
    )
    return data.get("primary_thread", [])


# Calls the LLM to generate a short, lighter-detail arc for each secondary
# thread, independently of the others. A separate call from init_primary_thread
# so the primary thread doesn't compete for space with N secondary
# storylines in the same response. Each thread's `length` caps how much of
# its own natural arc is actually resolved in this story — see
# outline_prompts.INIT_SECONDARY_ARCS_USER_PROMPT for the cutoff rule. This
# is an internal generation input — see init_outline below.
def init_secondary_arcs(
    novel: dict,
    worldbuilding: dict,
    characters: list[dict],
    primary_thread: list[dict],
    secondary_threads: list[dict],
    model: str = DEFAULTS["secondary_arcs"],
    reasoning: bool = False,
    correction: str | None = None,
) -> list[dict]:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    user_prompt = outline_prompts.INIT_SECONDARY_ARCS_USER_PROMPT.format(
        novel_metadata=json.dumps(novel, indent=2),
        worldbuilding=_worldbuilding_json(worldbuilding),
        characters=json.dumps(characters, indent=2),
        primary_thread=json.dumps(primary_thread, indent=2),
        secondary_threads=json.dumps(secondary_threads, indent=2),
        schema=json.dumps(outline_prompts.INIT_SECONDARY_ARCS_SCHEMA, indent=2),
    )
    # Retry path — names the threads that came back malformed last attempt.
    if correction:
        user_prompt += outline_prompts.INIT_SECONDARY_ARCS_CORRECTION_TEMPLATE.format(
            problems=correction
        )

    data = _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=SECONDARY_ARCS_MAX_TOKENS
    )
    return data.get("secondary_arcs", [])


# Calls the LLM to write the final, detailed, user-facing outline — weaving
# the primary thread's beats and the secondary arcs' plot points into one
# continuous, ordered sequence of prose beats. This is the first step whose
# output is actually persisted as something the user reads and edits;
# init_primary_thread and init_secondary_arcs are internal inputs to it.
# Runs after both — its job is to combine and narrate, not invent new plot.
# Name-only projections of the cast/entities, shared by init_outline and
# init_outline_audit — both need the same CAST/LOCATIONS/GROUPS/ITEMS/
# WORLDBUILDING FACTS name lists to place people and things in scenes and to
# validate beats' entity-presence lists against, so this stays in one place
# rather than being duplicated between the two prompts' call sites.
def _outline_entity_names(characters: list[dict], worldbuilding: dict, entities: dict) -> dict:
    return {
        "characters": [
            {"name": c.get("name"), "role": c.get("role"), "occupation": c.get("occupation")}
            for c in characters
        ],
        "locations": [e.get("name") for e in entities.get("locations", [])],
        "groups": [e.get("name") for e in entities.get("groups", [])],
        "items": [e.get("name") for e in entities.get("items", [])],
        "worldbuilding_facts": [f.get("title") for f in worldbuilding.get("facts", [])],
    }


# Step 1 of 2: a rough outline in one continuous pass. Not the final
# result — init_outline_audit reviews it afterward for the structural and
# continuity issues a single unbroken generation reliably misses at this
# length (timeline order, entity-list exactness, pacing math, POV rules,
# secondary-thread distribution). This step's own prompt asks for real,
# concrete, well-imagined content rather than self-checking every rule, since
# that's what the second pass is for.
def init_outline(
    novel: dict,
    worldbuilding: dict,
    primary_thread: list[dict],
    secondary_arcs: list[dict],
    characters: list[dict],
    entities: dict,
    model: str = DEFAULTS["outline"],
    reasoning: bool = False,
) -> tuple[list[dict], list[dict]]:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    names = _outline_entity_names(characters, worldbuilding, entities)
    user_prompt = outline_prompts.INIT_OUTLINE_USER_PROMPT.format(
        worldbuilding=_worldbuilding_json(worldbuilding),
        primary_thread=json.dumps(primary_thread, indent=2),
        secondary_arcs=json.dumps(secondary_arcs, indent=2),
        characters=json.dumps(names["characters"], indent=2),
        locations=json.dumps(names["locations"], indent=2),
        groups=json.dumps(names["groups"], indent=2),
        items=json.dumps(names["items"], indent=2),
        worldbuilding_facts=json.dumps(names["worldbuilding_facts"], indent=2),
        word_count=novel.get("word_count"),
        schema=json.dumps(outline_prompts.INIT_OUTLINE_SCHEMA, indent=2),
    )

    data = _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=OUTLINE_MAX_TOKENS
    )
    # skipped_threads: secondary threads the model judged physically/temporally
    # impossible to place (see outline_prompts' SKIPPED THREADS section) —
    # carried alongside the outline rather than folded into it, since it
    # describes what's absent rather than a chapter. Fed into the audit pass
    # below, which has final say over the skip decision.
    return data.get("outline", []), data.get("skipped_threads", [])


# Step 2 of 2: reviews init_outline's rough result against the structural
# checklist that used to be crammed into init_outline's own "before
# returning, validate" paragraph — timeline/continuity, character
# positioning, opening conventions, secondary-thread merging, chapter-level
# pacing/POV/title rules, and entity-presence-list exactness. Returns a full
# replacement chapter list in the same schema, not a diff, since a beat that
# needs re-cutting across a chapter boundary can't be expressed as an edit to
# one chapter in isolation.
def init_outline_audit(
    novel: dict,
    worldbuilding: dict,
    primary_thread: list[dict],
    secondary_arcs: list[dict],
    characters: list[dict],
    entities: dict,
    rough_outline: list[dict],
    rough_skipped_threads: list[dict],
    model: str = DEFAULTS["outline_audit"],
    reasoning: bool = False,
) -> tuple[list[dict], list[dict]]:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    names = _outline_entity_names(characters, worldbuilding, entities)
    user_prompt = outline_editing_prompts.INIT_OUTLINE_AUDIT_USER_PROMPT.format(
        worldbuilding=_worldbuilding_json(worldbuilding),
        primary_thread=json.dumps(primary_thread, indent=2),
        secondary_arcs=json.dumps(secondary_arcs, indent=2),
        characters=json.dumps(names["characters"], indent=2),
        locations=json.dumps(names["locations"], indent=2),
        groups=json.dumps(names["groups"], indent=2),
        items=json.dumps(names["items"], indent=2),
        worldbuilding_facts=json.dumps(names["worldbuilding_facts"], indent=2),
        word_count=novel.get("word_count"),
        rough_outline=json.dumps(rough_outline, indent=2),
        rough_skipped_threads=json.dumps(rough_skipped_threads, indent=2),
        schema=json.dumps(outline_prompts.INIT_OUTLINE_SCHEMA, indent=2),
    )

    data = _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=OUTLINE_AUDIT_MAX_TOKENS
    )
    return data.get("outline", []), data.get("skipped_threads", [])


# Calls the LLM to generate side characters, locations, items, groups, and
# events in a single call from the novel's metadata, worldbuilding rules,
# characters, primary thread, and secondary arcs — side characters are drawn
# from what the threads actually need, and events are expected to map onto
# real primary thread plot points rather than being invented independently.
def init_entities(
    novel: dict,
    worldbuilding: dict,
    characters: list[dict],
    primary_thread: list[dict],
    secondary_arcs: list[dict],
    model: str = DEFAULTS["entities"],
    reasoning: bool = False,
) -> dict:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    # Roughly one side character per 2500 words, computed here rather than left
    # to the model to work out from the metadata. Clamped to 2-8: a very short
    # story still needs a couple of people, and past 8 the reader loses track.
    word_count = novel.get("word_count") or 0
    side_character_target = max(2, min(8, round(word_count / 2500)))
    user_prompt = outline_prompts.INIT_ENTITIES_USER_PROMPT.format(
        novel_metadata=json.dumps(novel, indent=2),
        worldbuilding=_worldbuilding_json(worldbuilding),
        characters=json.dumps(characters, indent=2),
        primary_thread=json.dumps(primary_thread, indent=2),
        secondary_arcs=json.dumps(secondary_arcs, indent=2),
        word_count=word_count,
        side_character_target=side_character_target,
        schema=json.dumps(outline_prompts.INIT_ENTITIES_SCHEMA, indent=2),
    )

    return _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=ENTITIES_MAX_TOKENS
    )


# Calls the LLM to generate the starting relationship graph — character/group
# to character, item, location, group, or worldbuilding fact — from
# everything generated so far. Runs last, since it needs entities
# (locations/items/groups/worldbuilding_facts) to exist first. Only
# relationships that actually exist at story-start are emitted; see
# outline_prompts.INIT_RELATIONSHIPS_USER_PROMPT for the asymmetry and
# character-vs-group priority rules.
def init_relationships(
    novel: dict,
    characters: list[dict],
    worldbuilding: dict,
    model: str = DEFAULTS["initial_state"],
    reasoning: bool = False,
) -> dict:
    system_prompt = outline_prompts.SYSTEM_PROMPT.format(intro_prompt=novel.get("prompt", ""))
    user_prompt = outline_prompts.INIT_RELATIONSHIPS_USER_PROMPT.format(
        novel_metadata=json.dumps(novel, indent=2),
        characters=json.dumps(characters, indent=2),
        locations=json.dumps(worldbuilding.get("locations", []), indent=2),
        items=json.dumps(worldbuilding.get("items", []), indent=2),
        groups=json.dumps(worldbuilding.get("groups", []), indent=2),
        worldbuilding_facts=json.dumps(worldbuilding.get("worldbuilding_facts", []), indent=2),
        events=json.dumps(worldbuilding.get("events", []), indent=2),
        schema=json.dumps(outline_prompts.INIT_RELATIONSHIPS_SCHEMA, indent=2),
    )

    return _call_and_parse(
        model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=RELATIONSHIPS_MAX_TOKENS
    )
