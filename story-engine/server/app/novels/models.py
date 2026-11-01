from pydantic import BaseModel, Field


class Novel(BaseModel):
    id: str
    prompt: str
    title: str
    summary: str | None = None
    author: str | None = None
    word_count: int | None = None
    premise: str
    setting_context: str | None = None
    primary_genre: str | None = None
    region: str | None = None
    character_seeds: list[dict] = []
    sub_genres: list[str] = []
    # Selected from init_genre_conventions' common/deep_cuts pools by
    # generation.select_genre_conventions (2-4 per genre, random mix of both
    # pools) — persisted once at creation, read-only afterward. Not part of
    # NovelCreate (never user-supplied) or NovelUpdate (not editable); exists
    # on Novel only so API responses expose it to the frontend.
    genre_conventions: list[dict] = []
    tone: str | None = None
    themes: list[str] = []
    spice_level: str | None = None
    literary_voice: str | None = None
    tense: str | None = None
    perspective: str | None = None
    forbidden_element: str | None = None
    story_type: str | None = None
    time_period: str | None = None
    anchor_location: str | None = None
    anchor_location_description: str | None = None
    constraints: list[str] = []
    tone_notes: str | None = None
    characters_notes: str | None = None
    worldbuilding_notes: str | None = None
    # Freeform instructions scoped to the character-casting step only (e.g.
    # "every character must be married; make sure those marriages matter to
    # the plot") — distinct from characters_notes, which folds into the
    # system-prompt-wide intro prompt every step sees. Optional.
    character_generation_notes: str | None = None
    primary_thread: str | None = None
    # Decided by init_primary_thread (10000-14000), based on how much plot
    # the protagonist's arc actually needs. Null until that step runs.
    primary_word_count: int | None = None
    # Model alias actually used for each pipeline step at creation time (the
    # chosen alias, or the step default if none was chosen). Persisted so the
    # Prompts tab can preload the same choices for regeneration.
    metadata_model: str | None = None
    genre_conventions_model: str | None = None
    characters_model: str | None = None
    worldbuilding_model: str | None = None
    primary_thread_model: str | None = None
    secondary_arcs_model: str | None = None
    outline_model: str | None = None
    outline_audit_model: str | None = None
    entities_model: str | None = None
    initial_state_model: str | None = None
    metadata_reasoning: bool = False
    genre_conventions_reasoning: bool = False
    characters_reasoning: bool = False
    worldbuilding_reasoning: bool = False
    primary_thread_reasoning: bool = False
    secondary_arcs_reasoning: bool = False
    outline_reasoning: bool = False
    outline_audit_reasoning: bool = False
    entities_reasoning: bool = False
    initial_state_reasoning: bool = False
    # Flips to true the moment chapter one is generated. From then on every
    # table upstream of chapters (this novel's own fields, characters,
    # worldbuilding, locations, items, groups, events, outline_beats,
    # secondary_threads) is read-only — see router._require_unlocked.
    locked: bool = False
    locked_at: str | None = None
    generate_model: str | None = None
    edit_model: str | None = None
    state_model: str | None = None
    generate_reasoning: bool = False
    edit_reasoning: bool = False
    state_reasoning: bool = False


class NovelSummary(BaseModel):
    id: str
    title: str
    premise: str


# Subplot seed attached to a novel. length is the percentage of that
# storyline actually resolved in this story (the rest is left open for a
# later story). priority is narrative weight; heat is romantic/sexual
# intensity specific to that thread. All three range 0-100. word_count is
# decided by init_secondary_arcs (2000-4000) and is null until that step runs.
class SecondaryThread(BaseModel):
    id: str
    novel_id: str
    description: str
    length: int
    priority: int
    heat: int
    word_count: int | None = None


class SecondaryThreadCreate(BaseModel):
    description: str
    length: int
    priority: int
    heat: int


class SecondaryThreadUpdate(BaseModel):
    description: str | None = None
    length: int | None = None
    priority: int | None = None
    heat: int | None = None
    word_count: int | None = None


class Character(BaseModel):
    id: str
    novel_id: str
    name: str
    role: str | None = None
    age: int | None = None
    gender: str | None = None
    sexuality: str | None = None
    occupation: str | None = None
    appearance: str | None = None
    physical_characteristics: list[str] = []
    personality: list[str] = []
    backstory: str | None = None
    fears: list[str] = []
    flaws: list[str] = []
    contradictions: list[str] = []
    hobbies: list[str] = []
    spiritual_beliefs: list[str] = []
    character_voice: list[str] = []
    speech_patterns: list[str] = []


# One beat of the final, user-facing outline, in order. Written by
# init_outline, which weaves the (internal) primary thread and secondary
# arcs into this single detailed sequence. word_count is an absolute
# estimate of how many words this beat will run to once drafted into prose
# (not a percentage — beats vary freely in length, from a brief moment to a
# long scene, so there's no fixed total these need to sum to).
# One beat is one chapter — hence the title/pov/tone fields.
class OutlineBeat(BaseModel):
    id: str
    novel_id: str
    sort_order: int
    content: str
    word_count: int | None = None
    title: str | None = None
    pov_character: str | None = None
    pov_voice_note: str | None = None
    tone: str | None = None
    # Which entities (by id) are present/actively in play in this chapter —
    # resolved from init_outline's own name lists back to real database ids
    # (see router._resolve_beat_entity_columns). Used by chapter generation
    # to pull only the relevant story-bible entries into a chapter's prompt
    # instead of the whole story. Empty on outlines generated before this
    # field existed — those novels can't generate chapters until their
    # outline is regenerated.
    characters_present: list[str] = []
    items_present: list[str] = []
    locations_present: list[str] = []
    groups_present: list[str] = []
    worldbuilding_facts_present: list[str] = []


# One beat of the untouched rough outline — init_outline's raw output,
# before init_outline_audit rewrites it into the OutlineBeat rows the user
# actually sees and edits. Saved once at generate/regenerate time and never
# modified afterward, so the original AI draft stays comparable to whatever
# the outline becomes after audit and manual edits. No id correspondence to
# OutlineBeat is implied — the audit pass can add/remove/reorder beats.
class RawOutlineBeat(BaseModel):
    id: str
    novel_id: str
    sort_order: int
    content: str
    word_count: int | None = None
    title: str | None = None
    pov_character: str | None = None
    pov_voice_note: str | None = None
    tone: str | None = None
    characters_present: list[str] = []
    items_present: list[str] = []
    locations_present: list[str] = []
    groups_present: list[str] = []
    worldbuilding_facts_present: list[str] = []


class OutlineBeatUpdate(BaseModel):
    content: str | None = None
    word_count: int | None = None
    title: str | None = None
    pov_character: str | None = None
    pov_voice_note: str | None = None
    tone: str | None = None


# Body for re-running just the outline step (rough pass + audit pass) on an
# existing novel. All fields fall back to the model/reasoning choice already
# persisted on the novel.
class OutlineRegenerate(BaseModel):
    model: str | None = None
    reasoning: bool | None = None
    audit_model: str | None = None
    audit_reasoning: bool | None = None


# Body for re-running worldbuilding and every step downstream of it
# (characters, primary thread, secondary arcs, entities, outline) on an
# existing novel. Each step's model/reasoning can be overridden independently
# — any field left None falls back to that step's already-stored column on
# the novel, same as OutlineRegenerate does for the outline step alone.
class WorldbuildingRegenerate(BaseModel):
    worldbuilding_model: str | None = None
    worldbuilding_reasoning: bool | None = None
    characters_model: str | None = None
    characters_reasoning: bool | None = None
    primary_thread_model: str | None = None
    primary_thread_reasoning: bool | None = None
    secondary_arcs_model: str | None = None
    secondary_arcs_reasoning: bool | None = None
    entities_model: str | None = None
    entities_reasoning: bool | None = None
    outline_model: str | None = None
    outline_reasoning: bool | None = None
    outline_audit_model: str | None = None
    outline_audit_reasoning: bool | None = None


class Location(BaseModel):
    id: str
    novel_id: str
    name: str
    description: str | None = None


class Item(BaseModel):
    id: str
    novel_id: str
    name: str
    description: str | None = None


# Any set of people treated as a unit — a friend group, a band, a company.
# One world fact — many per novel, grouped by category.
class WorldbuildingFact(BaseModel):
    id: str
    novel_id: str
    sort_order: int
    category: str
    title: str | None = None
    description: str | None = None


# The world's fixed core plus its facts. Exactly one per novel.
class Worldbuilding(BaseModel):
    id: str
    novel_id: str
    story_type: str | None = None
    time_period: str | None = None
    anchor_location: str | None = None
    anchor_location_description: str | None = None
    facts: list[WorldbuildingFact] = []


class WorldbuildingUpdate(BaseModel):
    story_type: str | None = None
    time_period: str | None = None
    anchor_location: str | None = None
    anchor_location_description: str | None = None


class WorldbuildingFactUpdate(BaseModel):
    category: str | None = None
    title: str | None = None
    description: str | None = None


class Group(BaseModel):
    id: str
    novel_id: str
    name: str
    description: str | None = None
    associated_characters: list[str] = []


class Event(BaseModel):
    id: str
    novel_id: str
    title: str
    description: str | None = None
    characters_involved: list[str] = []
    groups_involved: list[str] = []


class CharacterRelationship(BaseModel):
    id: str
    novel_id: str
    character_id: str
    target_type: str
    target_id: str
    relationship_type: str | None = None
    status: str | None = None
    emotional_intensity: int | None = None
    open_threads: str | None = None


class GroupRelationship(BaseModel):
    id: str
    novel_id: str
    group_id: str
    target_type: str
    target_id: str
    relationship_type: str | None = None
    status: str | None = None
    emotional_intensity: int | None = None
    open_threads: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    age: int | None = None
    gender: str | None = None
    sexuality: str | None = None
    occupation: str | None = None
    appearance: str | None = None
    physical_characteristics: list[str] | None = None
    personality: list[str] | None = None
    backstory: str | None = None
    fears: list[str] | None = None
    flaws: list[str] | None = None
    contradictions: list[str] | None = None
    hobbies: list[str] | None = None
    spiritual_beliefs: list[str] | None = None
    character_voice: list[str] | None = None
    speech_patterns: list[str] | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    associated_characters: list[str] | None = None


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    characters_involved: list[str] | None = None
    groups_involved: list[str] | None = None


class NovelCreate(BaseModel):
    title: str
    # Base target word count for the primary thread, chosen by the user.
    # calculate_word_count (see generation.py) adds bonuses on top of this
    # for secondary threads — this is a floor, not the final total.
    word_count: int = Field(default=20000, ge=1000, le=20000)
    # The five intro-prompt sections, ported from V2's single-prompt sections
    # (--- Premise ---, --- Tone ---, --- Characters ---, --- Story
    # Structure ---). Stored separately so each has
    # its own dialogue box, then concatenated into intro_prompt for the LLM.
    premise: str
    tone_notes: str | None = None
    characters_notes: str | None = None
    worldbuilding_notes: str | None = None
    character_generation_notes: str | None = None
    primary_thread: str | None = None
    # Up to 3 subplot seeds (enforced client-side), submitted with the rest
    # of the novel and persisted alongside it.
    secondary_threads: list[SecondaryThreadCreate] = []
    primary_genre: str | None = None
    region: str | None = None
    character_seeds: list[dict] = []
    author: str | None = None
    themes: list[str] = []
    # "past" | "present"; "first_person" | "third_person_limited" |
    # "third_person_omniscient" — see INIT_NOVEL_SCHEMA. Left unset, the
    # metadata step infers whichever fits the premise best.
    tense: str | None = None
    perspective: str | None = None
    # Model alias (see model_routing.yaml) to use for each pipeline step.
    metadata_model: str | None = None
    genre_conventions_model: str | None = None
    characters_model: str | None = None
    worldbuilding_model: str | None = None
    primary_thread_model: str | None = None
    secondary_arcs_model: str | None = None
    outline_model: str | None = None
    outline_audit_model: str | None = None
    entities_model: str | None = None
    initial_state_model: str | None = None
    # Whether to enable extended reasoning/thinking for each pipeline step.
    metadata_reasoning: bool = False
    genre_conventions_reasoning: bool = False
    characters_reasoning: bool = False
    worldbuilding_reasoning: bool = False
    primary_thread_reasoning: bool = False
    secondary_arcs_reasoning: bool = False
    outline_reasoning: bool = False
    outline_audit_reasoning: bool = False
    entities_reasoning: bool = False
    initial_state_reasoning: bool = False


class NovelUpdate(BaseModel):
    title: str | None = None
    summary: str | None = None
    author: str | None = None
    premise: str | None = None
    setting_context: str | None = None
    primary_genre: str | None = None
    region: str | None = None
    character_seeds: list[dict] | None = None
    sub_genres: list[str] | None = None
    tone: str | None = None
    themes: list[str] | None = None
    spice_level: str | None = None
    literary_voice: str | None = None
    tense: str | None = None
    perspective: str | None = None
    forbidden_element: str | None = None
    story_type: str | None = None
    time_period: str | None = None
    anchor_location: str | None = None
    anchor_location_description: str | None = None
    constraints: list[str] | None = None
    tone_notes: str | None = None
    characters_notes: str | None = None
    worldbuilding_notes: str | None = None
    character_generation_notes: str | None = None
    primary_thread: str | None = None
    primary_word_count: int | None = None


class NovelCreateResponse(BaseModel):
    id: str


# Per-chapter character state snapshot. "Current state as of chapter N" is
# the latest row for a character with sort_order <= N — see
# chapters.get_character_state. chapter_id is null only for the one seeded
# baseline row per character (sort_order = -1), written when chapter one
# generates.
class CharacterState(BaseModel):
    id: str
    novel_id: str
    character_id: str
    chapter_id: str | None = None
    sort_order: int
    physical_state: str | None = None
    emotional_state: str | None = None
    emotional_intensity: int | None = None
    current_location_id: str | None = None
    goals: list[str] = []
    flaw_active: bool = False
    flaw_note: str | None = None
    knowledge_flags: list[str] = []


# Same append-only, as-of-chapter-N snapshot shape as CharacterState, for a
# group's collective standing/mood/cohesion instead of one character's.
class GroupState(BaseModel):
    id: str
    novel_id: str
    group_id: str
    chapter_id: str | None = None
    sort_order: int
    status: str | None = None
    disposition: str | None = None
    cohesion: int | None = None
    open_threads: list[str] = []
    knowledge_flags: list[str] = []


# Generated chapter prose. raw_prose is generate_chapter_prose's output,
# kept for diffing/debug; edited_prose is edit_chapter_prose's output and
# what the reader actually sees. summary is this chapter's own contribution
# to the running summary (concatenated at prompt-build time, never stored as
# its own blob — see chapters.py).
class Chapter(BaseModel):
    id: str
    novel_id: str
    outline_beat_id: str
    sort_order: int
    raw_prose: str
    edited_prose: str
    word_count: int | None = None
    summary: str


class ChapterSummary(BaseModel):
    id: str
    outline_beat_id: str
    sort_order: int
    title: str | None = None
    word_count: int | None = None


# Body for generating or regenerating one chapter. Any field left unset falls
# back to the alias already stored on the novel for that step, or the step's
# default — same fallback pattern as WorldbuildingRegenerate.
class ChapterGenerate(BaseModel):
    generate_model: str | None = None
    generate_reasoning: bool | None = None
    edit_model: str | None = None
    edit_reasoning: bool | None = None
    state_model: str | None = None
    state_reasoning: bool | None = None


# --- Season / Episode aliases (thunder trundle Story Bot terminology) ---
# Prefer these names in new code. Underlying fields still use novel_id/chapter_id
# in the SQLite schema for compatibility with the adapted pipeline.

class Season(Novel):
    """Alias for Novel — one season of a show."""


class SeasonSummary(NovelSummary):
    pass


class SeasonCreate(NovelCreate):
    pass


class SeasonUpdate(NovelUpdate):
    pass


class Episode(Chapter):
    """Alias for Chapter — one episode."""


class EpisodeSummary(ChapterSummary):
    pass


class EpisodeGenerate(ChapterGenerate):
    pass
