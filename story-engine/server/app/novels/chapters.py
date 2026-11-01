import json
import re

from app.model_routing import DEFAULTS, call_model
from app.prompts import chapter_editing_prompts, chapter_prose_prompts

# Separate from generation.py (which covers the 8 outline-building pipeline
# steps) — chapters is a self-contained concern reading chapters/
# character_state/group_state, not the worldbuilding/outline generation
# inputs. Same reasoning that already separates names.py out from
# generation.py.
#
# Only step 1 of the 3-call pipeline (raw prose) is implemented right now.
# edit_chapter_prose and extract_chapter_state are stubs — router.py's
# _run_chapter_pipeline still calls all 3 by the same signatures, so those
# stay unchanged until their prompts are written.

GENERATE_CHAPTER_MAX_TOKENS = 12000
EDIT_CHAPTER_MAX_TOKENS = 12000
EXTRACT_STATE_MAX_TOKENS = 8000

# Defaults when a novel predates the tense/perspective metadata fields, or the
# init_novel step left them unset. Matches INIT_NOVEL_SCHEMA's enum values.
DEFAULT_TENSE = "past"
DEFAULT_PERSPECTIVE = "third_person_limited"

# Maps INIT_NOVEL_SCHEMA's perspective enum to the phrasing chapter prompts
# actually want to read (a sentence fragment, not a code), e.g.
# "third_person_limited" -> "third person limited perspective".
_PERSPECTIVE_PHRASING = {
    "first_person": "first person perspective",
    "third_person_limited": "third person limited perspective",
    "third_person_omniscient": "third person omniscient perspective",
}


def _perspective_phrase(perspective: str | None) -> str:
    perspective = perspective or DEFAULT_PERSPECTIVE
    return _PERSPECTIVE_PHRASING.get(perspective, perspective.replace("_", " "))


# --- prompt block builders ---
# Each takes the flat DB-row dicts the router already resolved as "present in
# this beat" (router._present_entities_for_beat) and renders the
# corresponding chapter_prose_prompts.*_BLOCK_TEMPLATE. Only present entities are
# ever passed in here — a 100-character story sends a short prompt for a
# 2-character chapter, since the caller already filtered the list.

def _joined(items: list[str] | None, empty: str = "none") -> str:
    items = [i for i in (items or []) if i]
    return ", ".join(items) if items else empty


def _build_character_block(character: dict) -> str:
    state = character.get("state", {})
    apparent_age_clause = f"A {character['age']}-year-old " if character.get("age") else ""
    occupation_clause = f"{character['occupation']}. " if character.get("occupation") else ""
    physical_characteristics_clause = (
        f"Physical characteristics: {_joined(character.get('physical_characteristics'))}.\n"
        if character.get("physical_characteristics")
        else ""
    )
    fears_clause = f"Fears: {_joined(character.get('fears'))}.\n" if character.get("fears") else ""
    flaws_clause = f"Flaws: {_joined(character.get('flaws'))}.\n" if character.get("flaws") else ""
    speech_patterns_clause = (
        f"Speech patterns: {_joined(character.get('speech_patterns'))}.\n"
        if character.get("speech_patterns")
        else ""
    )

    intensity = state.get("emotional_intensity")
    emotional_intensity_clause = f" (intensity {intensity}/10)" if intensity is not None else ""
    flaw_active_clause = (
        f"Their flaw — {state.get('flaw_note')} — is currently active and should color their choices this episode.\n"
        if state.get("flaw_active") and state.get("flaw_note")
        else ""
    )

    return chapter_prose_prompts.CHARACTER_BLOCK_TEMPLATE.format(
        name=character.get("name", ""),
        apparent_age_clause=apparent_age_clause,
        occupation_clause=occupation_clause,
        role=character.get("role") or "unspecified",
        appearance=character.get("appearance") or "Not specified.",
        physical_characteristics_clause=physical_characteristics_clause,
        personality=_joined(character.get("personality"), "Not specified."),
        backstory=character.get("backstory") or "Not specified.",
        fears_clause=fears_clause,
        flaws_clause=flaws_clause,
        character_voice=_joined(character.get("character_voice"), "Not specified."),
        speech_patterns_clause=speech_patterns_clause,
        physical_state=state.get("physical_state") or "Unremarkable; nothing notable to report.",
        emotional_state=state.get("emotional_state") or "Their baseline temperament.",
        emotional_intensity_clause=emotional_intensity_clause,
        current_location_name=state.get("current_location_name") or "Not established.",
        goals=_joined(state.get("goals"), "Nothing specific yet established."),
        flaw_active_clause=flaw_active_clause,
        knowledge_flags=_joined(state.get("knowledge_flags"), "Nothing beyond their established backstory."),
    )


def _build_location_block(location: dict) -> str:
    return chapter_prose_prompts.LOCATION_BLOCK_TEMPLATE.format(
        name=location.get("name", ""),
        description=location.get("description") or "Not specified.",
    )


def _build_item_block(item: dict) -> str:
    return chapter_prose_prompts.ITEM_BLOCK_TEMPLATE.format(
        name=item.get("name", ""),
        description=item.get("description") or "Not specified.",
    )


def _build_group_block(group: dict) -> str:
    state = group.get("state", {})
    cohesion = state.get("cohesion")
    cohesion_clause = f" (cohesion {cohesion}/10)" if cohesion is not None else ""
    return chapter_prose_prompts.GROUP_BLOCK_TEMPLATE.format(
        name=group.get("name", ""),
        description=group.get("description") or "Not specified.",
        status=state.get("status") or "Nothing notable to report.",
        disposition=state.get("disposition") or "Its established baseline stance.",
        cohesion_clause=cohesion_clause,
        open_threads=_joined(state.get("open_threads")),
        knowledge_flags=_joined(state.get("knowledge_flags")),
    )


def _build_worldbuilding_fact_block(fact: dict) -> str:
    return chapter_prose_prompts.WORLDBUILDING_FACT_BLOCK_TEMPLATE.format(
        title=fact.get("title") or "Untitled",
        category=fact.get("category") or "general",
        description=fact.get("description") or "",
    )


# State-only blocks for extract_chapter_state — just "what changed going into
# this episode," not the full character/group bible, since the state pass
# isn't deciding who someone is, only what's different about them now.

def _build_state_character_block(character: dict) -> str:
    state = character.get("state", {})
    intensity = state.get("emotional_intensity")
    emotional_intensity_clause = f" (intensity {intensity}/10)" if intensity is not None else ""
    return chapter_editing_prompts.STATE_CHARACTER_BLOCK_TEMPLATE.format(
        name=character.get("name", ""),
        physical_state=state.get("physical_state") or "Unremarkable; nothing notable to report.",
        emotional_state=state.get("emotional_state") or "Their baseline temperament.",
        emotional_intensity_clause=emotional_intensity_clause,
        current_location_name=state.get("current_location_name") or "Not established.",
        goals=_joined(state.get("goals"), "Nothing specific yet established."),
        knowledge_flags=_joined(state.get("knowledge_flags"), "Nothing beyond their established backstory."),
    )


def _build_state_group_block(group: dict) -> str:
    state = group.get("state", {})
    cohesion = state.get("cohesion")
    cohesion_clause = f" (cohesion {cohesion}/10)" if cohesion is not None else ""
    return chapter_editing_prompts.STATE_GROUP_BLOCK_TEMPLATE.format(
        name=group.get("name", ""),
        status=state.get("status") or "Nothing notable to report.",
        disposition=state.get("disposition") or "Its established baseline stance.",
        cohesion_clause=cohesion_clause,
        open_threads=_joined(state.get("open_threads")),
        knowledge_flags=_joined(state.get("knowledge_flags")),
    )


# --- call 1: raw prose ---
# Returns plain prose, not JSON (json_mode=False on call_model). present_*
# lists are already filtered by the router to only what this beat's outline
# entry marked as present — nothing from the wider story bible is sent.
# beat["word_count"] is the outline's own per-chapter word-count estimate,
# passed straight through so the model knows the target length.

def generate_chapter_prose(
    novel: dict,
    beat: dict,
    running_summary: str,
    present_characters: list[dict],
    present_items: list[dict],
    present_locations: list[dict],
    present_groups: list[dict],
    present_worldbuilding_facts: list[dict],
    model: str = DEFAULTS["generate"],
    reasoning: bool = False,
) -> str:
    forbidden_element_clause = (
        f" The story's forbidden element: {novel['forbidden_element']}."
        if novel.get("forbidden_element")
        else ""
    )
    constraints = novel.get("constraints") or []
    constraints_clause = (
        f" Hard constraints on what may appear: {_joined(constraints)}." if constraints else ""
    )

    tense = novel.get("tense") or DEFAULT_TENSE
    perspective = _perspective_phrase(novel.get("perspective"))

    system_prompt = chapter_prose_prompts.GEN_STORY_SYSTEM_PROMPT.format(
        literary_voice=novel.get("literary_voice") or "F. Scott Fitzgerald",
        spice_level=novel.get("spice_level") or "none",
        forbidden_element_clause=forbidden_element_clause,
        constraints_clause=constraints_clause,
        tense=tense,
        perspective=perspective,
    )

    characters_block = "".join(_build_character_block(c) for c in present_characters) or "None."
    locations_block = "".join(_build_location_block(loc) for loc in present_locations) or "None."
    items_block = "".join(_build_item_block(i) for i in present_items) or "None."
    groups_block = "".join(_build_group_block(g) for g in present_groups) or "None."
    worldbuilding_facts_block = (
        "".join(_build_worldbuilding_fact_block(f) for f in present_worldbuilding_facts) or "None."
    )

    pov_voice_note_clause = f" {beat['pov_voice_note']}" if beat.get("pov_voice_note") else ""

    user_prompt = chapter_prose_prompts.GEN_STORY_USER_PROMPT.format(
        running_summary=running_summary or "This is the opening chapter — nothing has happened yet.",
        chapter_number=beat.get("sort_order", 0) + 1,
        chapter_title=beat.get("title") or "Untitled",
        chapter_word_count=beat.get("word_count") or 2000,
        pov_character=beat.get("pov_character") or "the protagonist",
        pov_voice_note_clause=pov_voice_note_clause,
        key_events=beat.get("content", ""),
        characters_block=characters_block,
        locations_block=locations_block,
        items_block=items_block,
        groups_block=groups_block,
        worldbuilding_facts_block=worldbuilding_facts_block,
        tense=tense,
        perspective=perspective,
    )

    return call_model(
        model,
        system_prompt,
        user_prompt,
        reasoning=reasoning,
        max_tokens=GENERATE_CHAPTER_MAX_TOKENS,
        json_mode=False,
    )


# --- call 2: edit ---
# Also plain prose (json_mode=False). Takes generate_chapter_prose's raw
# output and edits it — pacing, sentence structure, character voice, and
# temporal/spatial continuity — without re-deciding what happens. Temporal/
# spatial checks are made against this episode's own key events and draft
# text, not a second structured timeline/map source (no such source exists
# yet — this only has the same beat/present_characters/present_groups
# router.py already passes in).

def edit_chapter_prose(
    novel: dict,
    beat: dict,
    raw_prose: str,
    present_characters: list[dict],
    present_groups: list[dict],
    model: str = DEFAULTS["edit"],
    reasoning: bool = False,
) -> str:
    system_prompt = chapter_editing_prompts.EDIT_SYSTEM_PROMPT.format(
        literary_voice=novel.get("literary_voice") or "F. Scott Fitzgerald",
        tone=novel.get("tone") or "unspecified",
        spice_level=novel.get("spice_level") or "none",
        tense=novel.get("tense") or DEFAULT_TENSE,
        perspective=_perspective_phrase(novel.get("perspective")),
    )

    characters_block = "".join(
        chapter_editing_prompts.EDIT_CHARACTER_BLOCK_TEMPLATE.format(
            name=c.get("name", ""),
            character_voice=_joined(c.get("character_voice"), "Not specified."),
            speech_patterns_clause=(
                f"Speech patterns: {_joined(c.get('speech_patterns'))}.\n"
                if c.get("speech_patterns")
                else ""
            ),
        )
        for c in present_characters
    ) or "None."
    groups_block = "".join(
        chapter_editing_prompts.EDIT_GROUP_BLOCK_TEMPLATE.format(
            name=g.get("name", ""), description=g.get("description") or "Not specified."
        )
        for g in present_groups
    ) or "None."

    user_prompt = chapter_editing_prompts.EDIT_USER_PROMPT.format(
        key_events=beat.get("content", ""),
        pov_character=beat.get("pov_character") or "the protagonist",
        characters_block=characters_block,
        groups_block=groups_block,
        raw_prose=raw_prose,
    )

    return call_model(
        model,
        system_prompt,
        user_prompt,
        reasoning=reasoning,
        max_tokens=EDIT_CHAPTER_MAX_TOKENS,
        json_mode=False,
    )


# --- call 3: state extraction ---
# Structured (json_mode defaults True). full_character_roster/
# full_group_roster are name(+role)-only for every character/group NOT
# present in this episode — kept minimal so this call's context stays
# bounded even for a large cast, per the requirement that an offscreen
# entity's state can still change without ever sending their full bible.

def extract_chapter_state(
    novel: dict,
    beat: dict,
    edited_prose: str,
    present_characters: list[dict],
    full_character_roster: list[dict],
    present_groups: list[dict],
    full_group_roster: list[dict],
    model: str = DEFAULTS["state"],
    reasoning: bool = False,
) -> dict:
    system_prompt = chapter_editing_prompts.STATE_EXTRACTION_SYSTEM_PROMPT

    present_characters_block = (
        "".join(_build_state_character_block(c) for c in present_characters) or "None."
    )
    full_character_roster_block = "\n".join(
        f"- {c.get('name')} ({c.get('role') or 'unspecified role'})" for c in full_character_roster
    ) or "None."

    present_groups_block = "".join(_build_state_group_block(g) for g in present_groups) or "None."
    full_group_roster_block = "\n".join(f"- {g.get('name')}" for g in full_group_roster) or "None."

    user_prompt = chapter_editing_prompts.STATE_EXTRACTION_USER_PROMPT.format(
        edited_prose=edited_prose,
        present_characters_block=present_characters_block,
        full_character_roster_block=full_character_roster_block,
        present_groups_block=present_groups_block,
        full_group_roster_block=full_group_roster_block,
        schema=json.dumps(chapter_editing_prompts.EXTRACT_STATE_SCHEMA, indent=2),
    )

    # Same retry-once-on-malformed-JSON discipline as generation._call_and_parse
    # — a large chapter's prose sitting right before the model needs to also
    # emit clean, escaped JSON is exactly the kind of context that produces an
    # occasional escaping slip, and this call previously had no retry at all,
    # so any single bad parse failed the whole chapter regeneration outright.
    for attempt in (1, 2):
        text = call_model(
            model, system_prompt, user_prompt, reasoning=reasoning, max_tokens=EXTRACT_STATE_MAX_TOKENS
        )
        try:
            return _extract_json(text, model)
        except RuntimeError:
            if attempt == 2:
                raise
            print(f"[{model}] malformed JSON, retrying once", flush=True)
    raise RuntimeError(f"unreachable: {model}")  # pragma: no cover


# Same first-{...}-block extraction as generation._extract_json — duplicated
# rather than imported to keep chapters.py independent of generation.py's
# outline-pipeline internals.
def _extract_json(text: str, label: str) -> dict:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"No JSON found in {label} response: {text[:200]}")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Malformed JSON in {label} response: {e}") from e
