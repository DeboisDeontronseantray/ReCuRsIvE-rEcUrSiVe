import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db import get_connection
from app.model_routing import DEFAULTS, list_models
from app.novels.chapters import extract_chapter_state, generate_chapter_prose  # edit_chapter_prose disabled — see _run_chapter_pipeline
from app.novels.generation import (
    _post_characters_prompt,
    calculate_word_count,
    init_characters,
    init_entities,
    init_genre_conventions,
    init_novel,
    init_outline,
    init_outline_audit,
    init_relationships,
    init_primary_thread,
    init_secondary_arcs,
    init_worldbuilding,
    select_genre_conventions,
    truncate_secondary_arc,
)
from app.novels.names import build_name_pool
from app.novels.models import (
    Chapter,
    ChapterGenerate,
    ChapterSummary,
    Character,
    CharacterRelationship,
    CharacterUpdate,
    GroupRelationship,
    Event,
    EventUpdate,
    Item,
    ItemUpdate,
    Location,
    LocationUpdate,
    Novel,
    NovelCreate,
    NovelCreateResponse,
    NovelSummary,
    NovelUpdate,
    Group,
    GroupUpdate,
    OutlineBeat,
    OutlineBeatUpdate,
    OutlineRegenerate,
    RawOutlineBeat,
    SecondaryThread,
    SecondaryThreadCreate,
    SecondaryThreadUpdate,
    Worldbuilding,
    WorldbuildingFact,
    WorldbuildingFactUpdate,
    WorldbuildingRegenerate,
    WorldbuildingUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["novels"])

# Novel columns that hold JSON (lists), serialized to/from TEXT in sqlite.
_JSON_COLUMNS = {"sub_genres", "themes", "constraints", "character_seeds", "genre_conventions"}

_NOVEL_COLUMNS = [
    "id",
    "prompt",
    "title",
    "summary",
    "author",
    "word_count",
    "premise",
    "setting_context",
    "primary_genre",
    "region",
    "character_seeds",
    "sub_genres",
    "genre_conventions",
    "tone",
    "themes",
    "spice_level",
    "literary_voice",
    "tense",
    "perspective",
    "forbidden_element",
    "story_type",
    "time_period",
    "anchor_location",
    "anchor_location_description",
    "constraints",
    "tone_notes",
    "characters_notes",
    "worldbuilding_notes",
    "character_generation_notes",
    "primary_thread",
    "primary_word_count",
    "metadata_model",
    "genre_conventions_model",
    "characters_model",
    "worldbuilding_model",
    "primary_thread_model",
    "secondary_arcs_model",
    "outline_model",
    "outline_audit_model",
    "entities_model",
    "initial_state_model",
    "metadata_reasoning",
    "genre_conventions_reasoning",
    "characters_reasoning",
    "worldbuilding_reasoning",
    "primary_thread_reasoning",
    "secondary_arcs_reasoning",
    "outline_reasoning",
    "outline_audit_reasoning",
    "entities_reasoning",
    "initial_state_reasoning",
    "locked",
    "locked_at",
    "generate_model",
    "edit_model",
    "state_model",
    "generate_reasoning",
    "edit_reasoning",
    "state_reasoning",
]

# Novel columns stored as sqlite INTEGER (0/1) but exposed as bool.
_BOOL_COLUMNS = {
    "metadata_reasoning",
    "genre_conventions_reasoning",
    "characters_reasoning",
    "worldbuilding_reasoning",
    "primary_thread_reasoning",
    "secondary_arcs_reasoning",
    "outline_reasoning",
    "outline_audit_reasoning",
    "entities_reasoning",
    "initial_state_reasoning",
    "locked",
    "generate_reasoning",
    "edit_reasoning",
    "state_reasoning",
}


def _row_to_novel(row) -> Novel:
    data = dict(row)
    for col in _JSON_COLUMNS:
        data[col] = json.loads(data[col]) if data[col] else []
    for col in _BOOL_COLUMNS:
        data[col] = bool(data[col])
    return Novel(**data)


# Character columns that hold JSON (lists), serialized to/from TEXT in sqlite.
_CHARACTER_JSON_COLUMNS = {
    "physical_characteristics",
    "personality",
    "fears",
    "flaws",
    "contradictions",
    "hobbies",
    "spiritual_beliefs",
    "character_voice",
    "speech_patterns",
}

_CHARACTER_COLUMNS = [
    "id",
    "novel_id",
    "name",
    "role",
    "age",
    "gender",
    "sexuality",
    "occupation",
    "appearance",
    "physical_characteristics",
    "personality",
    "backstory",
    "fears",
    "flaws",
    "contradictions",
    "hobbies",
    "spiritual_beliefs",
    "character_voice",
    "speech_patterns",
]


def _character_row_to_dict(row) -> dict:
    data = dict(row)
    for col in _CHARACTER_JSON_COLUMNS:
        data[col] = json.loads(data[col]) if data[col] else []
    return data


def _row_to_character(row) -> Character:
    return Character(**_character_row_to_dict(row))


_OUTLINE_BEAT_COLUMNS = [
    "id",
    "novel_id",
    "sort_order",
    "content",
    "word_count",
    "title",
    "pov_character",
    "pov_voice_note",
    "tone",
    "characters_present",
    "items_present",
    "locations_present",
    "groups_present",
    "worldbuilding_facts_present",
]

_OUTLINE_BEAT_JSON_COLUMNS = {
    "characters_present",
    "items_present",
    "locations_present",
    "groups_present",
    "worldbuilding_facts_present",
}


def _row_to_outline_beat(row) -> OutlineBeat:
    data = dict(row)
    for col in _OUTLINE_BEAT_JSON_COLUMNS:
        data[col] = json.loads(data[col]) if data[col] else []
    return OutlineBeat(**data)


_RAW_OUTLINE_BEAT_COLUMNS = _OUTLINE_BEAT_COLUMNS


def _row_to_raw_outline_beat(row) -> RawOutlineBeat:
    data = dict(row)
    for col in _OUTLINE_BEAT_JSON_COLUMNS:
        data[col] = json.loads(data[col]) if data[col] else []
    return RawOutlineBeat(**data)


# Inserts the untouched rough outline (init_outline's output, before the
# audit pass rewrites it) into raw_outline_beats. Shares _resolve_beat_entity_
# columns/id-lookup discipline with the outline_beats insert below it at each
# call site, since both read the same name-only presence lists off the same
# beat shape.
def _insert_raw_outline_beats(
    conn,
    novel_id: str,
    rough_outline: list[dict],
    character_id_by_name: dict[str, str],
    item_id_by_name: dict[str, str],
    location_id_by_name: dict[str, str],
    group_id_by_name: dict[str, str],
    worldbuilding_fact_id_by_title: dict[str, str],
) -> None:
    for i, beat in enumerate(rough_outline):
        characters_present, items_present, locations_present, groups_present, facts_present = (
            _resolve_beat_entity_columns(
                beat,
                character_id_by_name,
                item_id_by_name,
                location_id_by_name,
                group_id_by_name,
                worldbuilding_fact_id_by_title,
            )
        )
        conn.execute(
            """INSERT INTO raw_outline_beats
               (id, novel_id, sort_order, content, word_count, title,
                pov_character, pov_voice_note, tone, characters_present,
                items_present, locations_present, groups_present,
                worldbuilding_facts_present)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                novel_id,
                i,
                beat.get("content", ""),
                beat.get("word_count"),
                beat.get("title"),
                beat.get("pov_character"),
                beat.get("pov_voice_note"),
                beat.get("tone"),
                characters_present,
                items_present,
                locations_present,
                groups_present,
                facts_present,
            ),
        )


# List selectable model aliases plus the default alias per pipeline step, for
# populating the Metadata/Characters/Worldbuilding dropdowns client-side.
@router.get("/models")
def get_models() -> dict:
    return {"models": list_models(), "defaults": DEFAULTS}


# Get all novels, summary info only.
@router.get("/novels")
def get_novels() -> list[NovelSummary]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, title, premise FROM novels").fetchall()
        return [NovelSummary(**row) for row in rows]
    finally:
        conn.close()


# Get full info for one novel.
@router.get("/novel/{id}")
def get_novel(id: str) -> Novel:
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Novel not found")
        return _row_to_novel(row)
    finally:
        conn.close()


# The 12 stages every secondary arc must contain, in order. Mirrors the
# primary thread's 9 hero's-journey steps — a named, mandatory structure the
# model cannot quietly return less of. See INIT_SECONDARY_ARCS_USER_PROMPT.
SECONDARY_ARC_STAGES = [
    "seed",
    "first_friction",
    "commitment",
    "complication_one",
    "complication_two",
    "midpoint_shift",
    "deepening",
    "setback",
    "forced_choice",
    "crisis",
    "confrontation",
    "landing",
]


# Checks every returned arc carries the full stage skeleton. Returns a list of
# human-readable problems (empty if all arcs are well-formed) used both to
# decide whether to retry and as the corrective text sent on that retry.
def _validate_secondary_arcs(secondary_arcs: list[dict]) -> list[str]:
    problems = []
    for i, arc in enumerate(secondary_arcs):
        points = arc.get("plot_points", [])
        stages = [p.get("arc_stage") for p in points]
        missing = [s for s in SECONDARY_ARC_STAGES if s not in stages]
        if missing:
            problems.append(
                f"Thread {i + 1} returned {len(points)} plot points and is missing these "
                f"required stages: {', '.join(missing)}."
            )
    return problems


# Runs init_secondary_arcs with a retry: a truncated response (finish_reason=
# 'length') and a response missing required stages are the same underlying
# failure (the model ran out of room), so both get one retry with a
# corrective note appended before giving up. Shared by create_novel and
# regenerate_worldbuilding so a future fix to this logic (stage list, retry
# wording, output-budget guidance) only has to be made once. Returns
# (secondary_arcs, error_detail) — error_detail is None on success; callers
# decide what "failed" means for them (create_novel deletes the half-built
# novel, regenerate_worldbuilding rolls back to the novel's prior state).
def _run_secondary_arcs_with_retry(
    arcs_novel_row: dict,
    worldbuilding_data: dict,
    character_rows: list[dict],
    primary_thread_rows: list[dict],
    secondary_thread_rows: list[dict],
    model: str,
    reasoning: bool,
) -> tuple[list[dict], str | None]:
    secondary_arcs: list[dict] = []
    first_attempt_error = None
    if secondary_thread_rows:
        try:
            secondary_arcs = init_secondary_arcs(
                arcs_novel_row,
                worldbuilding_data,
                character_rows,
                primary_thread_rows,
                secondary_thread_rows,
                model=model,
                reasoning=reasoning,
            )
        except RuntimeError as e:
            secondary_arcs = []
            first_attempt_error = str(e)

    # Matched to secondary_thread_rows by array POSITION, not by any string
    # the model echoes back — see INIT_SECONDARY_ARCS_USER_PROMPT. Skipped
    # when the first attempt was truncated — there is nothing to count yet,
    # and the retry below is what recovers it.
    if not first_attempt_error and len(secondary_arcs) != len(secondary_thread_rows):
        return [], (
            f"secondary_arcs step returned {len(secondary_arcs)} arcs, expected "
            f"{len(secondary_thread_rows)} (one per secondary thread) — cannot safely "
            "match arcs to threads by position."
        )

    # Each arc must carry the full 12-stage skeleton. A short arc makes the
    # `length` cut meaningless — at 4 plot points, length=30 keeps 2, which
    # is half the storyline, and the thread reads as resolved. A missing
    # `landing` means the response was cut off mid-generation, which
    # produces the same shape. Retry once naming the offending threads, then
    # give up rather than building a novel whose secondary threads silently
    # over-resolve.
    problems = _validate_secondary_arcs(secondary_arcs)
    if first_attempt_error:
        problems = [
            "Your previous response was cut off before it finished — it exceeded the "
            "output limit. Keep every plot point summary to 2-4 tight sentences so all "
            "12 stages for every thread fit in the response."
        ]
    if not problems:
        return secondary_arcs, None

    try:
        secondary_arcs = init_secondary_arcs(
            arcs_novel_row,
            worldbuilding_data,
            character_rows,
            primary_thread_rows,
            secondary_thread_rows,
            model=model,
            reasoning=reasoning,
            correction="\n".join(problems),
        )
    except RuntimeError as e:
        return [], (
            f"secondary_arcs step failed on retry: {e}. Try a model with a larger "
            "output budget for this step, or fewer secondary threads."
        )
    if len(secondary_arcs) != len(secondary_thread_rows):
        return [], (
            f"secondary_arcs retry returned {len(secondary_arcs)} arcs, expected "
            f"{len(secondary_thread_rows)} — cannot safely match arcs to threads."
        )
    problems = _validate_secondary_arcs(secondary_arcs)
    if problems:
        return [], (
            "secondary_arcs step returned incomplete arcs after a retry: " + "; ".join(problems)
        )
    return secondary_arcs, None


# Deletes a half-built novel, then raises. Used by the secondary-arc checks
# below: a novel whose threads over-resolve is unusable, so it should not be
# left sitting in the user's list. Child rows go via ON DELETE CASCADE.
def _abort_partial_novel(conn, novel_id: str, detail: str) -> None:
    conn.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
    conn.commit()
    raise HTTPException(status_code=502, detail=detail)


# Blocks writes to anything upstream of chapters once prose generation has
# begun. Set the moment chapter one generates (see generate_chapter route) —
# from then on, editing a character/location/item/group/event/worldbuilding
# fact/outline beat/secondary thread, or regenerating worldbuilding/outline,
# could silently invalidate prose and state already generated against the
# old values, so all of it becomes read-only. 423 (Locked) is the precise
# HTTP status for "the resource cannot be modified in its current state."
def _require_unlocked(conn, novel_id: str) -> None:
    row = conn.execute("SELECT locked FROM novels WHERE id = ?", (novel_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    if row["locked"]:
        raise HTTPException(status_code=423, detail="Novel is locked — prose generation has begun")


# The primary thread's own share of the novel: the total target minus whatever
# the secondary threads claim. Only meaningful once init_secondary_arcs has set
# each thread's word_count, so it is computed after that step, not at the
# primary-thread step. Clamped at 0 — a novel whose threads somehow claim more
# than the total should report nothing left rather than a negative figure.
def _primary_word_count(total_word_count, secondary_thread_word_counts) -> int:
    claimed = sum(wc or 0 for wc in secondary_thread_word_counts)
    return max(0, (total_word_count or 0) - claimed)


# The world facts' fixed category vocabulary. Mirrors the sections of
# INIT_WORLDBUILDING_USER_PROMPT.
WORLDBUILDING_CATEGORIES = [
    "society",
    "physical",
    "systems",
    "relationships",
    "conflict",
    "history",
    "daily_life",
    "beliefs",
]


# Rebuilds the worldbuilding dict from the database in the same shape
# init_worldbuilding returns, so any step re-run later sends a byte-identical
# block (see generation._worldbuilding_json — prompt caching depends on it).
def _worldbuilding_for_prompt(conn, novel_id: str) -> dict:
    row = conn.execute(
        """SELECT story_type, time_period, anchor_location, anchor_location_description
           FROM worldbuilding WHERE novel_id = ?""",
        (novel_id,),
    ).fetchone()
    if row is None:
        return {}
    facts = conn.execute(
        """SELECT category, title, description FROM worldbuilding_facts
           WHERE novel_id = ? ORDER BY sort_order""",
        (novel_id,),
    ).fetchall()
    return {**dict(row), "facts": [dict(f) for f in facts]}


# Builds the secondary-arc payload the outline step consumes. Shared by
# create_novel and the outline regenerate route so the two cannot drift.
#
# Iterates secondary_thread_rows — the user's own thread order — rather than the
# plot-point query, which is ordered by secondary_thread_id (a random UUID
# string). That previously made thread_index arbitrary and, worse, silently
# dropped any thread with no plot point rows from the outline input entirely.
#
# `length` is deliberately NOT passed on. The cut has already happened by this
# point, so the number carries no instruction the outline step can act on — it
# only invites the model to reason about how much storyline is missing and write
# toward it. It gets the one fact it needs instead: whether the thread continues
# past this story.
#
# on_empty is called with a message when a thread has no plot points; callers
# decide whether that aborts the novel (create) or just fails the request
# (regenerate).
def _build_outline_input_arcs(secondary_thread_rows, plot_point_rows, on_empty) -> list[dict]:
    plot_points_by_thread_id: dict[str, list[dict]] = {}
    for row in plot_point_rows:
        plot_points_by_thread_id.setdefault(row["secondary_thread_id"], []).append(row)

    outline_input_arcs = []
    for thread_index, thread in enumerate(secondary_thread_rows):
        rows = plot_points_by_thread_id.get(thread["id"], [])
        if not rows:
            on_empty(
                f"secondary thread {thread_index + 1} has no plot points after truncation "
                "— cannot build the outline without dropping the thread silently."
            )
        outline_input_arcs.append(
            {
                "thread_index": thread_index,
                "continues_after_story": thread["length"] < 100,
                "priority": thread["priority"],
                "plot_points": [
                    {
                        "plot_point_index": i,
                        "summary": row["summary"],
                        "characters_involved": json.loads(row["characters_involved"] or "[]"),
                    }
                    for i, row in enumerate(rows)
                ],
            }
        )
    return outline_input_arcs


# Applies init_outline_audit's final skipped_threads verdict (see
# outline_prompts' SKIPPED THREADS section): a thread the model judged
# physically/temporally impossible — e.g. it shares a character with a
# primary beat at the same point in the timeline, with no way to stage both
# — gets no beats in the outline and is marked length=0 in the database, the
# same signal a 0% `length` already carries elsewhere (nothing of this
# thread is told). This is a tracking marker only, read by nothing else in
# the pipeline; the audit step is what actually kept the thread's plot
# points out of the outline. Logs each skip server-side with the model's
# stated reason, since length=0 alone doesn't say why.
def _apply_skipped_threads(
    conn, novel_id: str, secondary_thread_rows: list[dict], skipped_threads: list[dict]
) -> None:
    for skip in skipped_threads:
        thread_index = skip.get("thread_index")
        if not isinstance(thread_index, int) or not (0 <= thread_index < len(secondary_thread_rows)):
            continue
        thread_id = secondary_thread_rows[thread_index]["id"]
        print(
            f"[outline] secondary thread skipped novel_id={novel_id} thread_id={thread_id} "
            f"thread_index={thread_index} reason={skip.get('reason')!r}",
            flush=True,
        )
        conn.execute("UPDATE secondary_threads SET length = 0 WHERE id = ?", (thread_id,))


# Resolves each outline beat's characters_present/items_present/locations_present/
# groups_present/worldbuilding_facts_present name lists (as returned by
# init_outline — the model only ever sees names, never ids) to real database
# ids, and returns the 5 JSON-encoded column values ready for the
# outline_beats INSERT, in column order. Same name->id lookup discipline as
# init_relationships below: build {name: id} maps from the rows just read
# back from the database (the source of truth for ids, never the model's own
# output), and skip a name silently if it doesn't match — an outline that
# named something imprecisely should not fail the whole beat over it.
def _resolve_beat_entity_columns(
    beat: dict,
    character_id_by_name: dict[str, str],
    item_id_by_name: dict[str, str],
    location_id_by_name: dict[str, str],
    group_id_by_name: dict[str, str],
    worldbuilding_fact_id_by_title: dict[str, str],
) -> tuple[str, str, str, str, str]:
    def _ids(names, id_by_name) -> str:
        return json.dumps([id_by_name[n] for n in names or [] if n in id_by_name])

    return (
        _ids(beat.get("characters_present"), character_id_by_name),
        _ids(beat.get("items_present"), item_id_by_name),
        _ids(beat.get("locations_present"), location_id_by_name),
        _ids(beat.get("groups_present"), group_id_by_name),
        _ids(beat.get("worldbuilding_facts_present"), worldbuilding_fact_id_by_title),
    )


# Create a new novel. Runs the generation pipeline in sequence — metadata,
# characters, worldbuilding (world rules), primary thread (protagonist's
# full hero's-journey arc), secondary arcs (one per secondary_thread,
# lighter detail), outline (weaves the primary thread and secondary arcs
# into the final detailed, user-facing outline), entities
# (locations/items/groups/events in one call), then relationships —
# each step using whichever model alias was chosen for it (falling back to
# the step default). Every step commits to the database immediately after
# generating; the next step reads its inputs back from the database rather
# than being passed the previous step's in-memory result, so by the time
# relationships is generated, every name it references already has a real
# row (and id) to resolve against. The primary thread and secondary arcs are
# internal generation inputs only — the outline is the only spine-like
# artifact exposed via the API/UI.
@router.post("/novel")
def create_novel(body: NovelCreate) -> NovelCreateResponse:
    new_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        # --- Metadata ---
        # The primary thread's word count target is computed here, once, from
        # the user's requested base plus a bonus for every secondary thread —
        # see calculate_word_count. Every downstream step that needs a word
        # count target (init_primary_thread) reads it back from the novels
        # row rather than deciding its own.
        secondary_thread_dicts = [t.model_dump() for t in body.secondary_threads]
        word_count = calculate_word_count(body.word_count, secondary_thread_dicts)
        generated = init_novel(
            body.title,
            body.premise,
            word_count,
            tone_notes=body.tone_notes,
            characters_notes=body.characters_notes,
            worldbuilding_notes=body.worldbuilding_notes,
            primary_thread=body.primary_thread,
            secondary_threads=secondary_thread_dicts,
            primary_genre=body.primary_genre,
            author=body.author,
            themes=body.themes,
            tense=body.tense,
            perspective=body.perspective,
            model=body.metadata_model or DEFAULTS["metadata"],
            reasoning=body.metadata_reasoning,
        )
        genre_conventions_raw = init_genre_conventions(
            generated,
            model=body.genre_conventions_model or DEFAULTS["genre_conventions"],
            reasoning=body.genre_conventions_reasoning,
        )
        selected_conventions = select_genre_conventions(genre_conventions_raw)
        conn.execute(
            f"""INSERT INTO novels ({', '.join(_NOVEL_COLUMNS)})
                VALUES ({', '.join(['?'] * len(_NOVEL_COLUMNS))})""",
            (
                new_id,
                generated.get("prompt", ""),
                generated.get("title", body.title),
                generated.get("summary"),
                generated.get("author"),
                word_count,
                generated.get("premise", body.premise),
                generated.get("setting_context"),
                generated.get("primary_genre"),
                body.region,
                json.dumps([dict(seed) for seed in body.character_seeds]),
                json.dumps(generated.get("sub_genres", [])),
                json.dumps(selected_conventions),
                generated.get("tone"),
                json.dumps(generated.get("themes", [])),
                generated.get("spice_level"),
                generated.get("literary_voice"),
                generated.get("tense"),
                generated.get("perspective"),
                generated.get("forbidden_element"),
                None,
                None,
                None,
                None,
                json.dumps([]),
                body.tone_notes,
                body.characters_notes,
                body.worldbuilding_notes,
                body.character_generation_notes,
                body.primary_thread,
                None,
                body.metadata_model or DEFAULTS["metadata"],
                body.genre_conventions_model or DEFAULTS["genre_conventions"],
                body.characters_model or DEFAULTS["characters"],
                body.worldbuilding_model or DEFAULTS["worldbuilding"],
                body.primary_thread_model or DEFAULTS["primary_thread"],
                body.secondary_arcs_model or DEFAULTS["secondary_arcs"],
                body.outline_model or DEFAULTS["outline"],
                body.outline_audit_model or DEFAULTS["outline_audit"],
                body.entities_model or DEFAULTS["entities"],
                body.initial_state_model or DEFAULTS["initial_state"],
                body.metadata_reasoning,
                body.genre_conventions_reasoning,
                body.characters_reasoning,
                body.worldbuilding_reasoning,
                body.primary_thread_reasoning,
                body.secondary_arcs_reasoning,
                body.outline_reasoning,
                body.outline_audit_reasoning,
                body.entities_reasoning,
                body.initial_state_reasoning,
                False,  # locked — flips true once chapter one is generated
                None,  # locked_at
                None,  # generate_model — chosen at chapter-generation time
                None,  # edit_model
                None,  # state_model
                False,  # generate_reasoning
                False,  # edit_reasoning
                False,  # state_reasoning
            ),
        )
        secondary_thread_rows = []
        for thread in body.secondary_threads:
            thread_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO secondary_threads (id, novel_id, description, length, priority, heat)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (thread_id, new_id, thread.description, thread.length, thread.priority, thread.heat),
            )
            secondary_thread_rows.append(
                {
                    "id": thread_id,
                    "description": thread.description,
                    "length": thread.length,
                    "priority": thread.priority,
                    "heat": thread.heat,
                }
            )
        conn.commit()
        novel_row = dict(
            conn.execute(
                f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (new_id,)
            ).fetchone()
        )

        # --- Worldbuilding: the world, generated before the cast ---
        # Runs first so everything after it — characters included — is built to
        # fit a world that is already fixed. Deliberately does NOT see the
        # premise, primary_thread, or plot endings (see
        # generation._worldbuilding_prompt) — those describe concrete plot
        # events and behavior, and a worldbuilding pass that sees them tends to
        # invent "facts" that just rationalize what the story already
        # describes, rather than independently deriving rules the story is
        # then built to obey. It still sees characters_notes (concepts, not
        # plot) so the world fits whatever cast the user described.
        worldbuilding_data = init_worldbuilding(
            novel_row,
            model=body.worldbuilding_model or DEFAULTS["worldbuilding"],
            reasoning=body.worldbuilding_reasoning,
        )
        conn.execute(
            """INSERT INTO worldbuilding
               (id, novel_id, story_type, time_period, anchor_location,
                anchor_location_description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                new_id,
                worldbuilding_data.get("story_type"),
                worldbuilding_data.get("time_period"),
                worldbuilding_data.get("anchor_location"),
                worldbuilding_data.get("anchor_location_description"),
            ),
        )
        for i, fact in enumerate(worldbuilding_data.get("facts", [])):
            conn.execute(
                """INSERT INTO worldbuilding_facts
                   (id, novel_id, sort_order, category, title, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    i,
                    fact.get("category", "society"),
                    fact.get("title"),
                    fact.get("description"),
                ),
            )
        conn.commit()

        # --- Characters ---
        # Real names for the region, so the model picks from a pool instead of
        # inventing (it reaches for the same invented register every time).
        characters = init_characters(
            novel_row,
            worldbuilding_data,
            build_name_pool(novel_row.get("region")),
            model=body.characters_model or DEFAULTS["characters"],
            reasoning=body.characters_reasoning,
        )
        for character in characters:
            conn.execute(
                f"""INSERT INTO characters ({', '.join(_CHARACTER_COLUMNS)})
                    VALUES ({', '.join(['?'] * len(_CHARACTER_COLUMNS))})""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    character.get("name", ""),
                    character.get("role"),
                    character.get("age"),
                    character.get("gender"),
                    character.get("sexuality"),
                    character.get("occupation"),
                    character.get("appearance"),
                    json.dumps(character.get("physical_characteristics", [])),
                    json.dumps(character.get("personality", [])),
                    character.get("backstory"),
                    json.dumps(character.get("fears", [])),
                    json.dumps(character.get("flaws", [])),
                    json.dumps(character.get("contradictions", [])),
                    json.dumps(character.get("hobbies", [])),
                    json.dumps(character.get("spiritual_beliefs", [])),
                    json.dumps(character.get("character_voice", [])),
                    json.dumps(character.get("speech_patterns", [])),
                ),
            )
        conn.commit()
        character_rows = [
            _character_row_to_dict(row)
            for row in conn.execute(
                f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
                (new_id,),
            ).fetchall()
        ]

        # From this point on, every step should see the generated cast
        # instead of the user's raw Characters notes — rebuild the prompt
        # used for system context accordingly and carry it on novel_row.
        # This also drops the raw secondary thread descriptions (see
        # _post_characters_prompt); only init_secondary_arcs re-adds them.
        novel_row["prompt"] = _post_characters_prompt(novel_row, secondary_thread_rows)

        # --- Primary thread: protagonist's full hero's-journey arc ---
        # Internal generation input only — not exposed via the API. The
        # outline step below is what the user actually sees and edits.
        primary_thread = init_primary_thread(
            novel_row,
            worldbuilding_data,
            character_rows,
            model=body.primary_thread_model or DEFAULTS["primary_thread"],
            reasoning=body.primary_thread_reasoning,
        )
        # primary_word_count is NOT set here — it is the novel's total minus
        # what the secondary threads claim, and those word counts don't exist
        # until init_secondary_arcs runs below.
        for i, beat in enumerate(primary_thread):
            conn.execute(
                """INSERT INTO spine_beats
                   (id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                    time_gap_before, forbidden_element_active, intimate_arc_role,
                    intimate_entry_mode)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    i,
                    beat.get("heros_journey_step", ""),
                    beat.get("summary", ""),
                    beat.get("word_count_pct"),
                    beat.get("time_gap_before"),
                    1 if beat.get("forbidden_element_active") else 0,
                    None  # TV-safe: intimate_arc_role unused,
                    None  # TV-safe: intimate_entry_mode unused,
                ),
            )
        conn.commit()
        primary_thread_rows = [
            dict(row)
            for row in conn.execute(
                """SELECT id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                          time_gap_before, forbidden_element_active, intimate_arc_role,
                          intimate_entry_mode
                   FROM spine_beats WHERE novel_id = ? ORDER BY sort_order""",
                (new_id,),
            ).fetchall()
        ]

        # --- Secondary arcs: one lighter-detail arc per secondary_thread ---
        # Internal generation input only — not exposed via the API.
        #
        # The LAST step allowed to see the raw thread descriptions — it needs
        # them to write each arc. Every step after this one gets the redacted
        # prompt carried on novel_row, so build the un-redacted version here
        # rather than mutating novel_row.
        arcs_novel_row = {
            **novel_row,
            "prompt": _post_characters_prompt(
                novel_row, secondary_thread_rows, include_secondary_threads=True
            ),
        }
        secondary_arcs, arcs_error = _run_secondary_arcs_with_retry(
            arcs_novel_row,
            worldbuilding_data,
            character_rows,
            primary_thread_rows,
            secondary_thread_rows,
            model=body.secondary_arcs_model or DEFAULTS["secondary_arcs"],
            reasoning=body.secondary_arcs_reasoning,
        )
        if arcs_error:
            _abort_partial_novel(conn, new_id, arcs_error)
        for thread, arc in zip(secondary_thread_rows, secondary_arcs):
            thread_id = thread["id"]
            conn.execute(
                "UPDATE secondary_threads SET word_count = ? WHERE id = ?",
                (arc.get("word_count"), thread_id),
            )
            # init_secondary_arcs always returns the thread's COMPLETE arc —
            # this is what actually enforces `length`, mechanically, rather
            # than trusting the model to self-truncate (see
            # generation.truncate_secondary_arc and the comment on
            # outline_prompts.INIT_SECONDARY_ARCS_USER_PROMPT for why).
            # Everything past the cutoff is discarded here and never reaches
            # the database or the outline step below.
            kept_points = truncate_secondary_arc(arc.get("plot_points", []), thread["length"])
            for i, point in enumerate(kept_points):
                conn.execute(
                    """INSERT INTO secondary_arc_plot_points
                       (id, novel_id, secondary_thread_id, sort_order, summary, characters_involved)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        new_id,
                        thread_id,
                        i,
                        point.get("summary", ""),
                        json.dumps(point.get("characters_involved", [])),
                    ),
                )
        conn.commit()
        secondary_arc_plot_point_rows = [
            dict(row)
            for row in conn.execute(
                """SELECT id, novel_id, secondary_thread_id, sort_order, summary, characters_involved
                   FROM secondary_arc_plot_points WHERE novel_id = ? ORDER BY secondary_thread_id, sort_order""",
                (new_id,),
            ).fetchall()
        ]

        # Now that each thread has its word_count, the primary thread's own
        # share is knowable. Stored so the UI can show what the main storyline
        # actually gets, rather than the total.
        thread_word_counts = [
            row[0]
            for row in conn.execute(
                "SELECT word_count FROM secondary_threads WHERE novel_id = ?", (new_id,)
            ).fetchall()
        ]
        conn.execute(
            "UPDATE novels SET primary_word_count = ? WHERE id = ?",
            (_primary_word_count(novel_row.get("word_count"), thread_word_counts), new_id),
        )
        conn.commit()

        # --- Secondary arc payload for the entities and outline steps ---
        # Built once and passed to both. The outline weaves the primary
        # thread and secondary arcs into one detailed, ordered outline —
        # the only spine-like artifact persisted for the user to read and
        # edit; the entities step reads the same arcs to work out which
        # side characters the story actually needs.
        #
        # Deliberately does NOT include the user's raw thread `description`
        # here — the outline step must only ever see the AI-generated (and
        # already length-truncated) plot_points for each thread, never the
        # user's short, complete-sounding premise text sitting alongside
        # them, since a model can lean on that framing even when the
        # instructions don't ask it to. Each secondary_arc entry is
        # identified purely by its position in the list (thread_index) —
        # the outline prompt is told to match beats back to threads by that
        # index instead of any text field.
        #
        # Withholding it here is necessary but NOT sufficient: the same
        # descriptions also used to reach this step through the system
        # prompt, which is built from novel_row["prompt"] and rendered the
        # full description of every thread under "this is the north star for
        # the story, do not stray from this". That is now stripped at the
        # source — see _post_characters_prompt in generation.py.
        outline_input_arcs = _build_outline_input_arcs(
            secondary_thread_rows,
            secondary_arc_plot_point_rows,
            lambda detail: _abort_partial_novel(conn, new_id, detail),
        )
        # --- Entities: side characters, locations, items, groups, events ---
        # Runs before the outline so the outline can place real named side
        # characters and locations instead of inventing them beat by beat.
        entities = init_entities(
            novel_row,
            worldbuilding_data,
            character_rows,
            primary_thread_rows,
            outline_input_arcs,
            model=body.entities_model or DEFAULTS["entities"],
            reasoning=body.entities_reasoning,
        )
        # Side characters go in the same table as the main cast with
        # role='side' — only the sketch fields the entities step generates.
        for side_character in entities.get("side_characters", []):
            conn.execute(
                """INSERT INTO characters
                   (id, novel_id, name, role, age, gender, occupation, appearance,
                    personality, speech_patterns)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    side_character.get("name", ""),
                    side_character.get("role") or "side",
                    side_character.get("age"),
                    side_character.get("gender"),
                    side_character.get("occupation"),
                    side_character.get("appearance"),
                    json.dumps(side_character.get("personality", [])),
                    json.dumps(side_character.get("speech_patterns", [])),
                ),
            )
        for location in entities.get("locations", []):
            conn.execute(
                "INSERT INTO locations (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), new_id, location.get("name", ""), location.get("description")),
            )
        for item in entities.get("items", []):
            conn.execute(
                "INSERT INTO items (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), new_id, item.get("name", ""), item.get("description")),
            )
        for group in entities.get("groups", []):
            conn.execute(
                """INSERT INTO groups (id, novel_id, name, description, associated_characters)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    group.get("name", ""),
                    group.get("description"),
                    json.dumps(group.get("associated_characters", [])),
                ),
            )
        for event in entities.get("events", []):
            conn.execute(
                """INSERT INTO events
                   (id, novel_id, title, description, characters_involved, groups_involved)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    event.get("title", ""),
                    event.get("description"),
                    json.dumps(event.get("characters_involved", [])),
                    json.dumps(event.get("groups_involved", [])),
                ),
            )
        conn.commit()
        # Re-read the cast so the outline below sees the side characters too.
        character_rows = [
            _character_row_to_dict(row)
            for row in conn.execute(
                f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
                (new_id,),
            ).fetchall()
        ]

        # --- Outline: rough pass, then an edit/audit pass over it ---
        rough_outline, rough_skipped_threads = init_outline(
            novel_row,
            worldbuilding_data,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            model=body.outline_model or DEFAULTS["outline"],
            reasoning=body.outline_reasoning,
        )
        outline, skipped_threads = init_outline_audit(
            novel_row,
            worldbuilding_data,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            rough_outline,
            rough_skipped_threads,
            model=body.outline_audit_model or DEFAULTS["outline_audit"],
            reasoning=body.outline_audit_reasoning,
        )
        _apply_skipped_threads(conn, new_id, secondary_thread_rows, skipped_threads)
        # Name -> id maps for resolving each beat's entity-presence lists —
        # the model only ever sees names (see init_outline), so this maps
        # them back to the real rows just inserted above. Same discipline as
        # the relationship-graph resolution further down.
        character_id_by_name = {c["name"]: c["id"] for c in character_rows}
        item_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM items WHERE novel_id = ?", (new_id,)).fetchall()
        }
        location_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute(
                "SELECT id, name FROM locations WHERE novel_id = ?", (new_id,)
            ).fetchall()
        }
        group_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM groups WHERE novel_id = ?", (new_id,)).fetchall()
        }
        worldbuilding_fact_id_by_title = {
            r["title"]: r["id"]
            for r in conn.execute(
                "SELECT id, title FROM worldbuilding_facts WHERE novel_id = ?", (new_id,)
            ).fetchall()
            if r["title"]
        }
        for i, beat in enumerate(outline):
            characters_present, items_present, locations_present, groups_present, facts_present = (
                _resolve_beat_entity_columns(
                    beat,
                    character_id_by_name,
                    item_id_by_name,
                    location_id_by_name,
                    group_id_by_name,
                    worldbuilding_fact_id_by_title,
                )
            )
            conn.execute(
                """INSERT INTO outline_beats
                   (id, novel_id, sort_order, content, word_count, title,
                    pov_character, pov_voice_note, tone, characters_present,
                    items_present, locations_present, groups_present,
                    worldbuilding_facts_present)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    i,
                    beat.get("content", ""),
                    beat.get("word_count"),
                    beat.get("title"),
                    beat.get("pov_character"),
                    beat.get("pov_voice_note"),
                    beat.get("tone"),
                    characters_present,
                    items_present,
                    locations_present,
                    groups_present,
                    facts_present,
                ),
            )
        _insert_raw_outline_beats(
            conn,
            new_id,
            rough_outline,
            character_id_by_name,
            item_id_by_name,
            location_id_by_name,
            group_id_by_name,
            worldbuilding_fact_id_by_title,
        )
        conn.commit()

        # --- Initial state: starting relationship graph ---
        # Character- and group-outward relationships to anything (each other,
        # items, locations, groups, or worldbuilding facts). Runs last, since
        # every entity type it can reference must already exist.
        location_rows = [
            dict(row)
            for row in conn.execute(
                "SELECT id, novel_id, name, description FROM locations WHERE novel_id = ?", (new_id,)
            ).fetchall()
        ]
        item_rows = [
            dict(row)
            for row in conn.execute(
                "SELECT id, novel_id, name, description FROM items WHERE novel_id = ?", (new_id,)
            ).fetchall()
        ]
        group_rows = [
            dict(row)
            for row in conn.execute(
                """SELECT id, novel_id, name, description, associated_characters
                   FROM groups WHERE novel_id = ?""",
                (new_id,),
            ).fetchall()
        ]
        worldbuilding_fact_rows = [
            dict(row)
            for row in conn.execute(
                """SELECT id, novel_id, category, title, description
                   FROM worldbuilding_facts WHERE novel_id = ?""",
                (new_id,),
            ).fetchall()
        ]
        event_rows = [
            dict(row)
            for row in conn.execute(
                "SELECT id, novel_id, title, description FROM events WHERE novel_id = ?", (new_id,)
            ).fetchall()
        ]

        # Name -> id maps, built from the rows just read back from the
        # database — the source of truth for ids is the database, not the
        # model's raw output (which never sees ids at all). Worldbuilding
        # facts are keyed by title since that's the only name-like field the
        # model sees for them.
        character_id_by_name = {c["name"]: c["id"] for c in character_rows}
        group_id_by_name = {g["name"]: g["id"] for g in group_rows}
        target_id_by_type_and_name = (
            {("character", c["name"]): c["id"] for c in character_rows}
            | {("location", l["name"]): l["id"] for l in location_rows}
            | {("item", i["name"]): i["id"] for i in item_rows}
            | {("group", g["name"]): g["id"] for g in group_rows}
            | {("worldbuilding_fact", w["title"]): w["id"] for w in worldbuilding_fact_rows}
        )

        initial_state = init_relationships(
            novel_row,
            character_rows,
            {
                "locations": location_rows,
                "items": item_rows,
                "groups": group_rows,
                "worldbuilding_facts": worldbuilding_fact_rows,
                "events": event_rows,
            },
            model=body.initial_state_model or DEFAULTS["initial_state"],
            reasoning=body.initial_state_reasoning,
        )

        for relationship in initial_state.get("character_relationships", []):
            character_id = character_id_by_name.get(relationship.get("character", ""))
            target_type = relationship.get("target_type")
            target_id = target_id_by_type_and_name.get((target_type, relationship.get("target", "")))
            if character_id is None or target_id is None:
                continue
            conn.execute(
                """INSERT INTO character_relationships
                   (id, novel_id, character_id, target_type, target_id, relationship_type,
                    status, emotional_intensity, open_threads)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    character_id,
                    target_type,
                    target_id,
                    relationship.get("relationship_type"),
                    relationship.get("status"),
                    relationship.get("emotional_intensity"),
                    relationship.get("open_threads"),
                ),
            )
        for relationship in initial_state.get("group_relationships", []):
            group_id = group_id_by_name.get(relationship.get("group", ""))
            target_type = relationship.get("target_type")
            target_id = target_id_by_type_and_name.get((target_type, relationship.get("target", "")))
            if group_id is None or target_id is None:
                continue
            conn.execute(
                """INSERT INTO group_relationships
                   (id, novel_id, group_id, target_type, target_id, relationship_type,
                    status, emotional_intensity, open_threads)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    new_id,
                    group_id,
                    target_type,
                    target_id,
                    relationship.get("relationship_type"),
                    relationship.get("status"),
                    relationship.get("emotional_intensity"),
                    relationship.get("open_threads"),
                ),
            )
        conn.commit()

        return NovelCreateResponse(id=new_id)
    finally:
        conn.close()


# Get the generated characters for one novel.
@router.get("/novel/{id}/characters")
def get_characters(id: str) -> list[Character]:
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
            (id,),
        ).fetchall()
        return [_row_to_character(row) for row in rows]
    finally:
        conn.close()


# Get the generated locations for one novel.
@router.get("/novel/{id}/locations")
def get_locations(id: str) -> list[Location]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, novel_id, name, description FROM locations WHERE novel_id = ?", (id,)
        ).fetchall()
        return [Location(**row) for row in rows]
    finally:
        conn.close()


# Get the generated items for one novel.
@router.get("/novel/{id}/items")
def get_items(id: str) -> list[Item]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, novel_id, name, description FROM items WHERE novel_id = ?", (id,)
        ).fetchall()
        return [Item(**row) for row in rows]
    finally:
        conn.close()


# Get the worldbuilding for one novel — the fixed core plus all its facts,
# in generated order.
@router.get("/novel/{id}/worldbuilding")
def get_worldbuilding(id: str) -> Worldbuilding:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT id, novel_id, story_type, time_period, anchor_location,
                      anchor_location_description
               FROM worldbuilding WHERE novel_id = ?""",
            (id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Worldbuilding not found")
        facts = conn.execute(
            """SELECT id, novel_id, sort_order, category, title, description
               FROM worldbuilding_facts WHERE novel_id = ? ORDER BY sort_order""",
            (id,),
        ).fetchall()
        return Worldbuilding(
            **dict(row), facts=[WorldbuildingFact(**dict(f)) for f in facts]
        )
    finally:
        conn.close()


# Update the worldbuilding core for one novel. Only provided fields change.
# Keyed by novel_id since there is exactly one row per novel.
@router.patch("/novel/{novel_id}/worldbuilding")
def update_worldbuilding(novel_id: str, body: WorldbuildingUpdate) -> Worldbuilding:
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        row = conn.execute(
            """SELECT id, novel_id, story_type, time_period, anchor_location,
                      anchor_location_description
               FROM worldbuilding WHERE novel_id = ?""",
            (novel_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Worldbuilding not found")

        updated = Worldbuilding(**dict(row)).model_copy(update=updates)
        conn.execute(
            """UPDATE worldbuilding SET story_type = ?, time_period = ?, anchor_location = ?,
               anchor_location_description = ? WHERE novel_id = ?""",
            (
                updated.story_type,
                updated.time_period,
                updated.anchor_location,
                updated.anchor_location_description,
                novel_id,
            ),
        )
        conn.commit()
        facts = conn.execute(
            """SELECT id, novel_id, sort_order, category, title, description
               FROM worldbuilding_facts WHERE novel_id = ? ORDER BY sort_order""",
            (novel_id,),
        ).fetchall()
        return updated.model_copy(
            update={"facts": [WorldbuildingFact(**dict(f)) for f in facts]}
        )
    finally:
        conn.close()


# Update one world fact. Only provided fields are changed.
@router.patch("/novel/{novel_id}/worldbuilding-facts/{entity_id}")
def update_worldbuilding_fact(
    novel_id: str, entity_id: str, body: WorldbuildingFactUpdate
) -> WorldbuildingFact:
    return _update_entity(
        "worldbuilding_facts",
        ["id", "novel_id", "sort_order", "category", "title", "description"],
        novel_id,
        entity_id,
        body,
        WorldbuildingFact,
    )


# Delete one world fact.
@router.delete("/novel/{novel_id}/worldbuilding-facts/{entity_id}")
def delete_worldbuilding_fact(novel_id: str, entity_id: str):
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        cursor = conn.execute(
            "DELETE FROM worldbuilding_facts WHERE id = ? AND novel_id = ?",
            (entity_id, novel_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Worldbuilding fact not found")
        return {"status": "deleted"}
    finally:
        conn.close()


# Get the generated groups for one novel.
@router.get("/novel/{id}/groups")
def get_groups(id: str) -> list[Group]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, novel_id, name, description, associated_characters
               FROM groups WHERE novel_id = ?""",
            (id,),
        ).fetchall()
        groups = []
        for row in rows:
            data = dict(row)
            data["associated_characters"] = (
                json.loads(data["associated_characters"]) if data["associated_characters"] else []
            )
            groups.append(Group(**data))
        return groups
    finally:
        conn.close()


# Get the generated events for one novel.
@router.get("/novel/{id}/events")
def get_events(id: str) -> list[Event]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, novel_id, title, description, characters_involved, groups_involved
               FROM events WHERE novel_id = ?""",
            (id,),
        ).fetchall()
        events = []
        for row in rows:
            data = dict(row)
            data["characters_involved"] = (
                json.loads(data["characters_involved"]) if data["characters_involved"] else []
            )
            data["groups_involved"] = (
                json.loads(data["groups_involved"]) if data["groups_involved"] else []
            )
            events.append(Event(**data))
        return events
    finally:
        conn.close()


# Get the final, user-facing outline for one novel, in order. This is the
# only spine-like artifact exposed via the API — the primary thread and
# secondary arcs that fed into it are internal generation inputs.
@router.get("/novel/{id}/outline")
def get_outline(id: str) -> list[OutlineBeat]:
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT {', '.join(_OUTLINE_BEAT_COLUMNS)} FROM outline_beats "
            "WHERE novel_id = ? ORDER BY sort_order",
            (id,),
        ).fetchall()
        return [_row_to_outline_beat(row) for row in rows]
    finally:
        conn.close()


# Get the untouched rough outline (init_outline's output, before the audit
# pass) for one novel, in order. Fixed at generate/regenerate time — never
# affected by outline-beat edits (see update_outline_beat), so this is the
# original AI draft to compare the current outline against.
@router.get("/novel/{id}/outline/raw")
def get_raw_outline(id: str) -> list[RawOutlineBeat]:
    conn = get_connection()
    try:
        rows = conn.execute(
            f"SELECT {', '.join(_RAW_OUTLINE_BEAT_COLUMNS)} FROM raw_outline_beats "
            "WHERE novel_id = ? ORDER BY sort_order",
            (id,),
        ).fetchall()
        return [_row_to_raw_outline_beat(row) for row in rows]
    finally:
        conn.close()


# Re-run worldbuilding and everything generated downstream of it (characters,
# primary thread, secondary arcs, entities, outline) on an existing novel.
# Worldbuilding sits upstream of all of that — characters are cast to fit its
# rules, the plot is built around its locations and social order, and so on —
# so regenerating it alone would leave the rest of the novel describing a
# world that no longer exists. Each step's model/reasoning can be overridden
# independently via the request body; anything left unset reuses that step's
# already-stored column on the novel (see _NOVEL_COLUMNS), same fallback
# pattern as regenerate_outline below.
#
# Unlike create_novel (which commits after every step, and unlike
# regenerate_outline (one step, one commit), this route defers every commit
# to the very end: a failure at ANY point — including late, at entities or
# outline — must roll back to the exact novel the user had before clicking
# the button, not leave it half-regenerated with a new world but a stale
# outline. Deliberately does NOT use _abort_partial_novel — that deletes the
# entire novel, which is right at creation time (nothing to preserve yet) and
# wrong here (the novel already existed).
@router.post("/novel/{id}/regenerate/worldbuilding")
def regenerate_worldbuilding(id: str, body: WorldbuildingRegenerate) -> list[OutlineBeat]:
    conn = get_connection()
    try:
        # Deliberately NOT _require_unlocked: regenerating worldbuilding is the
        # one operation meant to work even after chapters exist — the whole
        # point is invalidating and cascading them away, not being blocked by
        # their presence. See the chapters DELETE below and the locked reset
        # at the end of this transaction.
        row = conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Novel not found")
        novel_row = dict(row)

        # User input — kept as-is. Only word_count (derived by secondary_arcs)
        # gets reset, since it describes plot generated for the OLD world.
        secondary_thread_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, description, length, priority, heat, word_count
                   FROM secondary_threads WHERE novel_id = ?""",
                (id,),
            ).fetchall()
        ]

        # --- Wipe everything downstream of (and including) worldbuilding ---
        # Explicit, leaf-first DELETEs rather than relying on cascade, so the
        # order is legible and doesn't depend on FK pragma state. secondary_
        # threads themselves are NOT deleted (user input); only the derived
        # word_count on them is reset, in the same uncommitted transaction as
        # everything else, so a rollback restores it too.
        # Chapters (and character_state/group_state rows keyed to them) go
        # first — they were written against the world/characters/outline this
        # regenerate is about to erase, so they can't survive it either.
        conn.execute("DELETE FROM chapters WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM outline_beats WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM raw_outline_beats WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM secondary_arc_plot_points WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM events WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM groups WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM items WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM locations WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM spine_beats WHERE novel_id = ?", (id,))
        # All characters, main cast and side characters alike — side
        # characters are added later by entities and would be cast for a
        # world that no longer exists.
        conn.execute("DELETE FROM characters WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM worldbuilding_facts WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM worldbuilding WHERE novel_id = ?", (id,))
        conn.execute("UPDATE secondary_threads SET word_count = NULL WHERE novel_id = ?", (id,))

        # --- Worldbuilding ---
        # Reads directly off novel_row's own columns (title/setting_context/
        # tone_notes/characters_notes/worldbuilding_notes) via
        # generation._worldbuilding_prompt — not off novel_row["prompt"] — so
        # no prompt rebuild is needed before this step, unlike characters/
        # primary_thread/secondary_arcs below.
        worldbuilding_data = init_worldbuilding(
            novel_row,
            model=body.worldbuilding_model or novel_row.get("worldbuilding_model")
            or DEFAULTS["worldbuilding"],
            reasoning=(
                body.worldbuilding_reasoning
                if body.worldbuilding_reasoning is not None
                else bool(novel_row.get("worldbuilding_reasoning"))
            ),
        )
        conn.execute(
            """INSERT INTO worldbuilding
               (id, novel_id, story_type, time_period, anchor_location,
                anchor_location_description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                id,
                worldbuilding_data.get("story_type"),
                worldbuilding_data.get("time_period"),
                worldbuilding_data.get("anchor_location"),
                worldbuilding_data.get("anchor_location_description"),
            ),
        )
        for i, fact in enumerate(worldbuilding_data.get("facts", [])):
            conn.execute(
                """INSERT INTO worldbuilding_facts
                   (id, novel_id, sort_order, category, title, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    i,
                    fact.get("category", "society"),
                    fact.get("title"),
                    fact.get("description"),
                ),
            )

        # --- Characters ---
        characters = init_characters(
            novel_row,
            worldbuilding_data,
            build_name_pool(novel_row.get("region")),
            model=body.characters_model or novel_row.get("characters_model")
            or DEFAULTS["characters"],
            reasoning=(
                body.characters_reasoning
                if body.characters_reasoning is not None
                else bool(novel_row.get("characters_reasoning"))
            ),
        )
        for character in characters:
            conn.execute(
                f"""INSERT INTO characters ({', '.join(_CHARACTER_COLUMNS)})
                    VALUES ({', '.join(['?'] * len(_CHARACTER_COLUMNS))})""",
                (
                    str(uuid.uuid4()),
                    id,
                    character.get("name", ""),
                    character.get("role"),
                    character.get("age"),
                    character.get("gender"),
                    character.get("sexuality"),
                    character.get("occupation"),
                    character.get("appearance"),
                    json.dumps(character.get("physical_characteristics", [])),
                    json.dumps(character.get("personality", [])),
                    character.get("backstory"),
                    json.dumps(character.get("fears", [])),
                    json.dumps(character.get("flaws", [])),
                    json.dumps(character.get("contradictions", [])),
                    json.dumps(character.get("hobbies", [])),
                    json.dumps(character.get("spiritual_beliefs", [])),
                    json.dumps(character.get("character_voice", [])),
                    json.dumps(character.get("speech_patterns", [])),
                ),
            )
        character_rows = [
            _character_row_to_dict(r)
            for r in conn.execute(
                f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
                (id,),
            ).fetchall()
        ]

        # From this point on, every step sees the generated cast instead of
        # the user's raw Characters notes — same as create_novel.
        novel_row["prompt"] = _post_characters_prompt(novel_row, secondary_thread_rows)

        # --- Primary thread: protagonist's full hero's-journey arc ---
        primary_thread = init_primary_thread(
            novel_row,
            worldbuilding_data,
            character_rows,
            model=body.primary_thread_model or novel_row.get("primary_thread_model")
            or DEFAULTS["primary_thread"],
            reasoning=(
                body.primary_thread_reasoning
                if body.primary_thread_reasoning is not None
                else bool(novel_row.get("primary_thread_reasoning"))
            ),
        )
        for i, beat in enumerate(primary_thread):
            conn.execute(
                """INSERT INTO spine_beats
                   (id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                    time_gap_before, forbidden_element_active, intimate_arc_role,
                    intimate_entry_mode)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    i,
                    beat.get("heros_journey_step", ""),
                    beat.get("summary", ""),
                    beat.get("word_count_pct"),
                    beat.get("time_gap_before"),
                    1 if beat.get("forbidden_element_active") else 0,
                    None  # TV-safe: intimate_arc_role unused,
                    None  # TV-safe: intimate_entry_mode unused,
                ),
            )
        primary_thread_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                          time_gap_before, forbidden_element_active, intimate_arc_role,
                          intimate_entry_mode
                   FROM spine_beats WHERE novel_id = ? ORDER BY sort_order""",
                (id,),
            ).fetchall()
        ]

        # --- Secondary arcs ---
        # Last step allowed to see the raw thread descriptions — see
        # create_novel for why the prompt is rebuilt separately here rather
        # than mutating novel_row.
        arcs_novel_row = {
            **novel_row,
            "prompt": _post_characters_prompt(
                novel_row, secondary_thread_rows, include_secondary_threads=True
            ),
        }
        secondary_arcs, arcs_error = _run_secondary_arcs_with_retry(
            arcs_novel_row,
            worldbuilding_data,
            character_rows,
            primary_thread_rows,
            secondary_thread_rows,
            model=body.secondary_arcs_model or novel_row.get("secondary_arcs_model")
            or DEFAULTS["secondary_arcs"],
            reasoning=(
                body.secondary_arcs_reasoning
                if body.secondary_arcs_reasoning is not None
                else bool(novel_row.get("secondary_arcs_reasoning"))
            ),
        )
        if arcs_error:
            conn.rollback()
            raise HTTPException(status_code=502, detail=arcs_error)
        for thread, arc in zip(secondary_thread_rows, secondary_arcs):
            thread_id = thread["id"]
            conn.execute(
                "UPDATE secondary_threads SET word_count = ? WHERE id = ?",
                (arc.get("word_count"), thread_id),
            )
            kept_points = truncate_secondary_arc(arc.get("plot_points", []), thread["length"])
            for i, point in enumerate(kept_points):
                conn.execute(
                    """INSERT INTO secondary_arc_plot_points
                       (id, novel_id, secondary_thread_id, sort_order, summary, characters_involved)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        id,
                        thread_id,
                        i,
                        point.get("summary", ""),
                        json.dumps(point.get("characters_involved", [])),
                    ),
                )
        secondary_arc_plot_point_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, secondary_thread_id, sort_order, summary, characters_involved
                   FROM secondary_arc_plot_points WHERE novel_id = ? ORDER BY secondary_thread_id, sort_order""",
                (id,),
            ).fetchall()
        ]

        # Now that each thread has its word_count, the primary thread's own
        # share is knowable.
        thread_word_counts = [
            r[0]
            for r in conn.execute(
                "SELECT word_count FROM secondary_threads WHERE novel_id = ?", (id,)
            ).fetchall()
        ]
        conn.execute(
            "UPDATE novels SET primary_word_count = ? WHERE id = ?",
            (_primary_word_count(novel_row.get("word_count"), thread_word_counts), id),
        )

        def _fail(detail: str) -> None:
            raise HTTPException(status_code=409, detail=detail)

        outline_input_arcs = _build_outline_input_arcs(
            secondary_thread_rows, secondary_arc_plot_point_rows, _fail
        )

        # --- Entities: side characters, locations, items, groups, events ---
        entities = init_entities(
            novel_row,
            worldbuilding_data,
            character_rows,
            primary_thread_rows,
            outline_input_arcs,
            model=body.entities_model or novel_row.get("entities_model") or DEFAULTS["entities"],
            reasoning=(
                body.entities_reasoning
                if body.entities_reasoning is not None
                else bool(novel_row.get("entities_reasoning"))
            ),
        )
        for side_character in entities.get("side_characters", []):
            conn.execute(
                """INSERT INTO characters
                   (id, novel_id, name, role, age, gender, occupation, appearance,
                    personality, speech_patterns)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    side_character.get("name", ""),
                    side_character.get("role") or "side",
                    side_character.get("age"),
                    side_character.get("gender"),
                    side_character.get("occupation"),
                    side_character.get("appearance"),
                    json.dumps(side_character.get("personality", [])),
                    json.dumps(side_character.get("speech_patterns", [])),
                ),
            )
        for location in entities.get("locations", []):
            conn.execute(
                "INSERT INTO locations (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), id, location.get("name", ""), location.get("description")),
            )
        for item in entities.get("items", []):
            conn.execute(
                "INSERT INTO items (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), id, item.get("name", ""), item.get("description")),
            )
        for group in entities.get("groups", []):
            conn.execute(
                """INSERT INTO groups (id, novel_id, name, description, associated_characters)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    group.get("name", ""),
                    group.get("description"),
                    json.dumps(group.get("associated_characters", [])),
                ),
            )
        for event in entities.get("events", []):
            conn.execute(
                """INSERT INTO events
                   (id, novel_id, title, description, characters_involved, groups_involved)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    event.get("title", ""),
                    event.get("description"),
                    json.dumps(event.get("characters_involved", [])),
                    json.dumps(event.get("groups_involved", [])),
                ),
            )
        # Re-read the cast so the outline below sees the side characters too.
        character_rows = [
            _character_row_to_dict(r)
            for r in conn.execute(
                f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
                (id,),
            ).fetchall()
        ]

        # --- Outline: rough pass, then an edit/audit pass over it ---
        rough_outline, rough_skipped_threads = init_outline(
            novel_row,
            worldbuilding_data,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            model=body.outline_model or novel_row.get("outline_model") or DEFAULTS["outline"],
            reasoning=(
                body.outline_reasoning
                if body.outline_reasoning is not None
                else bool(novel_row.get("outline_reasoning"))
            ),
        )
        outline, skipped_threads = init_outline_audit(
            novel_row,
            worldbuilding_data,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            rough_outline,
            rough_skipped_threads,
            model=body.outline_audit_model or novel_row.get("outline_audit_model") or DEFAULTS["outline_audit"],
            reasoning=(
                body.outline_audit_reasoning
                if body.outline_audit_reasoning is not None
                else bool(novel_row.get("outline_audit_reasoning"))
            ),
        )
        _apply_skipped_threads(conn, id, secondary_thread_rows, skipped_threads)
        character_id_by_name = {c["name"]: c["id"] for c in character_rows}
        item_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM items WHERE novel_id = ?", (id,)).fetchall()
        }
        location_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM locations WHERE novel_id = ?", (id,)).fetchall()
        }
        group_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM groups WHERE novel_id = ?", (id,)).fetchall()
        }
        worldbuilding_fact_id_by_title = {
            r["title"]: r["id"]
            for r in conn.execute(
                "SELECT id, title FROM worldbuilding_facts WHERE novel_id = ?", (id,)
            ).fetchall()
            if r["title"]
        }
        for i, beat in enumerate(outline):
            characters_present, items_present, locations_present, groups_present, facts_present = (
                _resolve_beat_entity_columns(
                    beat,
                    character_id_by_name,
                    item_id_by_name,
                    location_id_by_name,
                    group_id_by_name,
                    worldbuilding_fact_id_by_title,
                )
            )
            conn.execute(
                """INSERT INTO outline_beats
                   (id, novel_id, sort_order, content, word_count, title,
                    pov_character, pov_voice_note, tone, characters_present,
                    items_present, locations_present, groups_present,
                    worldbuilding_facts_present)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    i,
                    beat.get("content", ""),
                    beat.get("word_count"),
                    beat.get("title"),
                    beat.get("pov_character"),
                    beat.get("pov_voice_note"),
                    beat.get("tone"),
                    characters_present,
                    items_present,
                    locations_present,
                    groups_present,
                    facts_present,
                ),
            )
        _insert_raw_outline_beats(
            conn,
            id,
            rough_outline,
            character_id_by_name,
            item_id_by_name,
            location_id_by_name,
            group_id_by_name,
            worldbuilding_fact_id_by_title,
        )

        # Chapters are gone, so whatever locked the novel no longer applies —
        # unlock it so worldbuilding/outline/entities are editable again.
        conn.execute("UPDATE novels SET locked = 0, locked_at = NULL WHERE id = ?", (id,))

        # Everything succeeded — commit the whole cascade as one unit now.
        conn.commit()

        rows = conn.execute(
            f"SELECT {', '.join(_OUTLINE_BEAT_COLUMNS)} FROM outline_beats "
            "WHERE novel_id = ? ORDER BY sort_order",
            (id,),
        ).fetchall()
        return [_row_to_outline_beat(r) for r in rows]
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=502, detail=f"worldbuilding regeneration failed: {e}") from e
    finally:
        conn.close()


# Re-run just the outline step on an existing novel, leaving every earlier step
# untouched. Everything init_outline needs is already persisted, so nothing
# upstream has to be regenerated.
#
# The whole thing runs in one uncommitted transaction: the DELETE and the
# INSERTs share it, so a model failure rolls back to the outline the novel
# already had. Deliberately does NOT use _abort_partial_novel — that deletes the
# entire novel, which is right at creation time and catastrophic here.
@router.post("/novel/{id}/regenerate/outline")
def regenerate_outline(id: str, body: OutlineRegenerate) -> list[OutlineBeat]:
    conn = get_connection()
    try:
        # Deliberately NOT _require_unlocked — same reasoning as
        # regenerate_worldbuilding: this is the operation meant to cascade
        # chapters away, not be blocked by their existing.
        row = conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Novel not found")
        novel_row = dict(row)

        secondary_thread_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, description, length, priority, heat, word_count
                   FROM secondary_threads WHERE novel_id = ?""",
                (id,),
            ).fetchall()
        ]
        primary_thread_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                          time_gap_before, forbidden_element_active, intimate_arc_role,
                          intimate_entry_mode
                   FROM spine_beats WHERE novel_id = ? ORDER BY sort_order""",
                (id,),
            ).fetchall()
        ]
        if not primary_thread_rows:
            raise HTTPException(
                status_code=409,
                detail="This novel has no primary thread — it never finished generating, "
                "so there is nothing to build an outline from.",
            )

        plot_point_rows = [
            dict(r)
            for r in conn.execute(
                """SELECT id, novel_id, secondary_thread_id, sort_order, summary,
                          characters_involved
                   FROM secondary_arc_plot_points WHERE novel_id = ?
                   ORDER BY secondary_thread_id, sort_order""",
                (id,),
            ).fetchall()
        ]
        character_rows = [
            _character_row_to_dict(r)
            for r in conn.execute(
                f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
                (id,),
            ).fetchall()
        ]
        # init_outline reads only the names off these (see generation.init_outline).
        entities = {
            "locations": [
                dict(r)
                for r in conn.execute(
                    "SELECT name FROM locations WHERE novel_id = ?", (id,)
                ).fetchall()
            ],
            "groups": [
                dict(r)
                for r in conn.execute(
                    "SELECT name FROM groups WHERE novel_id = ?", (id,)
                ).fetchall()
            ],
            "items": [
                dict(r)
                for r in conn.execute("SELECT name FROM items WHERE novel_id = ?", (id,)).fetchall()
            ],
        }

        # novels.prompt holds the ORIGINAL intro prompt, including the user's raw
        # characters notes and raw secondary-thread descriptions. create_novel
        # strips those in memory before the outline step and never writes the
        # redacted version back, so it has to be rebuilt here — otherwise a
        # thread's complete, self-resolving description leaks into the system
        # prompt and the outline writes toward an ending it was never given.
        novel_row["prompt"] = _post_characters_prompt(novel_row, secondary_thread_rows)

        def _fail(detail: str) -> None:
            raise HTTPException(status_code=409, detail=detail)

        outline_input_arcs = _build_outline_input_arcs(
            secondary_thread_rows, plot_point_rows, _fail
        )

        # Chapters (and character_state/group_state rows keyed to them) were
        # written against the outline beats this regenerate is about to
        # replace, so they can't survive it either.
        conn.execute("DELETE FROM chapters WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM outline_beats WHERE novel_id = ?", (id,))
        conn.execute("DELETE FROM raw_outline_beats WHERE novel_id = ?", (id,))
        worldbuilding_for_outline = _worldbuilding_for_prompt(conn, id)
        rough_outline, rough_skipped_threads = init_outline(
            novel_row,
            worldbuilding_for_outline,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            model=body.model or novel_row.get("outline_model") or DEFAULTS["outline"],
            reasoning=(
                body.reasoning
                if body.reasoning is not None
                else bool(novel_row.get("outline_reasoning"))
            ),
        )
        outline, skipped_threads = init_outline_audit(
            novel_row,
            worldbuilding_for_outline,
            primary_thread_rows,
            outline_input_arcs,
            character_rows,
            entities,
            rough_outline,
            rough_skipped_threads,
            model=body.audit_model or novel_row.get("outline_audit_model") or DEFAULTS["outline_audit"],
            reasoning=(
                body.audit_reasoning
                if body.audit_reasoning is not None
                else bool(novel_row.get("outline_audit_reasoning"))
            ),
        )
        _apply_skipped_threads(conn, id, secondary_thread_rows, skipped_threads)
        character_id_by_name = {c["name"]: c["id"] for c in character_rows}
        item_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM items WHERE novel_id = ?", (id,)).fetchall()
        }
        location_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM locations WHERE novel_id = ?", (id,)).fetchall()
        }
        group_id_by_name = {
            r["name"]: r["id"]
            for r in conn.execute("SELECT id, name FROM groups WHERE novel_id = ?", (id,)).fetchall()
        }
        worldbuilding_fact_id_by_title = {
            r["title"]: r["id"]
            for r in conn.execute(
                "SELECT id, title FROM worldbuilding_facts WHERE novel_id = ?", (id,)
            ).fetchall()
            if r["title"]
        }
        for i, beat in enumerate(outline):
            characters_present, items_present, locations_present, groups_present, facts_present = (
                _resolve_beat_entity_columns(
                    beat,
                    character_id_by_name,
                    item_id_by_name,
                    location_id_by_name,
                    group_id_by_name,
                    worldbuilding_fact_id_by_title,
                )
            )
            conn.execute(
                """INSERT INTO outline_beats
                   (id, novel_id, sort_order, content, word_count, title,
                    pov_character, pov_voice_note, tone, characters_present,
                    items_present, locations_present, groups_present,
                    worldbuilding_facts_present)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    id,
                    i,
                    beat.get("content", ""),
                    beat.get("word_count"),
                    beat.get("title"),
                    beat.get("pov_character"),
                    beat.get("pov_voice_note"),
                    beat.get("tone"),
                    characters_present,
                    items_present,
                    locations_present,
                    groups_present,
                    facts_present,
                ),
            )
        _insert_raw_outline_beats(
            conn,
            id,
            rough_outline,
            character_id_by_name,
            item_id_by_name,
            location_id_by_name,
            group_id_by_name,
            worldbuilding_fact_id_by_title,
        )

        # Chapters are gone, so whatever locked the novel no longer applies —
        # unlock it so worldbuilding/outline/entities are editable again.
        conn.execute("UPDATE novels SET locked = 0, locked_at = NULL WHERE id = ?", (id,))

        conn.commit()

        rows = conn.execute(
            f"SELECT {', '.join(_OUTLINE_BEAT_COLUMNS)} FROM outline_beats "
            "WHERE novel_id = ? ORDER BY sort_order",
            (id,),
        ).fetchall()
        return [_row_to_outline_beat(r) for r in rows]
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        # The DELETE above is still uncommitted, so this puts the old outline back.
        conn.rollback()
        raise HTTPException(status_code=502, detail=f"outline regeneration failed: {e}") from e
    finally:
        conn.close()


# Get the secondary threads for one novel.
@router.get("/novel/{id}/secondary-threads")
def get_secondary_threads(id: str) -> list[SecondaryThread]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, novel_id, description, length, priority, heat, word_count FROM secondary_threads WHERE novel_id = ?",
            (id,),
        ).fetchall()
        return [SecondaryThread(**row) for row in rows]
    finally:
        conn.close()


# Add a secondary thread to an existing novel. Capped at 3 per novel,
# matching the limit enforced client-side during creation.
@router.post("/novel/{id}/secondary-threads")
def create_secondary_thread(id: str, body: SecondaryThreadCreate) -> SecondaryThread:
    conn = get_connection()
    try:
        _require_unlocked(conn, id)
        count = conn.execute(
            "SELECT COUNT(*) FROM secondary_threads WHERE novel_id = ?", (id,)
        ).fetchone()[0]
        if count >= 3:
            raise HTTPException(status_code=400, detail="A novel may have at most 3 secondary threads")

        new_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO secondary_threads (id, novel_id, description, length, priority, heat)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (new_id, id, body.description, body.length, body.priority, body.heat),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, novel_id, description, length, priority, heat, word_count FROM secondary_threads WHERE id = ?",
            (new_id,),
        ).fetchone()
        return SecondaryThread(**dict(row))
    finally:
        conn.close()


# Delete one secondary thread.
@router.delete("/novel/{novel_id}/secondary-threads/{thread_id}")
def delete_secondary_thread(novel_id: str, thread_id: str):
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        cursor = conn.execute(
            "DELETE FROM secondary_threads WHERE id = ? AND novel_id = ?", (thread_id, novel_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Secondary thread not found")
        return {"status": "deleted"}
    finally:
        conn.close()


# Shared PATCH logic for the simple name/description-style entity tables
# (characters, locations, items). Fetches the row scoped to
# novel_id, merges in only the fields the client actually sent, writes it
# back, and returns the updated row as the given model.
def _update_entity(table: str, columns: list[str], novel_id: str, entity_id: str, body, model_cls):
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        row = conn.execute(
            f"SELECT {', '.join(columns)} FROM {table} WHERE id = ? AND novel_id = ?",
            (entity_id, novel_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"{table[:-1].capitalize()} not found")

        updated = model_cls(**dict(row)).model_copy(update=updates)
        update_columns = [col for col in columns if col not in ("id", "novel_id")]
        set_clause = ", ".join(f"{col} = ?" for col in update_columns)
        values = [getattr(updated, col) for col in update_columns]
        values.extend([entity_id, novel_id])

        conn.execute(f"UPDATE {table} SET {set_clause} WHERE id = ? AND novel_id = ?", values)
        conn.commit()
        return updated
    finally:
        conn.close()


# Update one character. Only provided fields are changed.
@router.patch("/novel/{novel_id}/characters/{entity_id}")
def update_character(novel_id: str, entity_id: str, body: CharacterUpdate) -> Character:
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        row = conn.execute(
            f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE id = ? AND novel_id = ?",
            (entity_id, novel_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Character not found")

        updated = _row_to_character(row).model_copy(update=updates)
        update_columns = [col for col in _CHARACTER_COLUMNS if col not in ("id", "novel_id")]
        set_clause = ", ".join(f"{col} = ?" for col in update_columns)
        values = []
        for col in update_columns:
            value = getattr(updated, col)
            if col in _CHARACTER_JSON_COLUMNS:
                value = json.dumps(value)
            values.append(value)
        values.extend([entity_id, novel_id])

        conn.execute(f"UPDATE characters SET {set_clause} WHERE id = ? AND novel_id = ?", values)
        conn.commit()
        return updated
    finally:
        conn.close()


# Update one location. Only provided fields are changed.
@router.patch("/novel/{novel_id}/locations/{entity_id}")
def update_location(novel_id: str, entity_id: str, body: LocationUpdate) -> Location:
    return _update_entity(
        "locations", ["id", "novel_id", "name", "description"], novel_id, entity_id, body, Location
    )


# Update one item. Only provided fields are changed.
@router.patch("/novel/{novel_id}/items/{entity_id}")
def update_item(novel_id: str, entity_id: str, body: ItemUpdate) -> Item:
    return _update_entity(
        "items", ["id", "novel_id", "name", "description"], novel_id, entity_id, body, Item
    )


# Update one group. Only provided fields are changed. Handled separately from
# _update_entity since its associated_characters column is a JSON-encoded list.
@router.patch("/novel/{novel_id}/groups/{entity_id}")
def update_group(novel_id: str, entity_id: str, body: GroupUpdate) -> Group:
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        row = conn.execute(
            """SELECT id, novel_id, name, description, associated_characters
               FROM groups WHERE id = ? AND novel_id = ?""",
            (entity_id, novel_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Group not found")

        data = dict(row)
        data["associated_characters"] = (
            json.loads(data["associated_characters"]) if data["associated_characters"] else []
        )
        updated = Group(**data).model_copy(update=updates)

        conn.execute(
            """UPDATE groups SET name = ?, description = ?, associated_characters = ?
               WHERE id = ? AND novel_id = ?""",
            (
                updated.name,
                updated.description,
                json.dumps(updated.associated_characters),
                entity_id,
                novel_id,
            ),
        )
        conn.commit()
        return updated
    finally:
        conn.close()


# Update one secondary thread. Only provided fields are changed.
@router.patch("/novel/{novel_id}/secondary-threads/{entity_id}")
def update_secondary_thread(novel_id: str, entity_id: str, body: SecondaryThreadUpdate) -> SecondaryThread:
    return _update_entity(
        "secondary_threads",
        ["id", "novel_id", "description", "length", "priority", "heat", "word_count"],
        novel_id,
        entity_id,
        body,
        SecondaryThread,
    )


# Update one outline beat. Only provided fields are changed. sort_order is
# intentionally not editable — OutlineBeatUpdate has no field for it, since
# reordering beats would need to reflow the whole outline, not a single-field edit.
@router.patch("/novel/{novel_id}/outline-beats/{entity_id}")
def update_outline_beat(novel_id: str, entity_id: str, body: OutlineBeatUpdate) -> OutlineBeat:
    return _update_entity(
        "outline_beats",
        [
            "id",
            "novel_id",
            "sort_order",
            "content",
            "word_count",
            "title",
            "pov_character",
            "pov_voice_note",
            "tone",
        ],
        novel_id,
        entity_id,
        body,
        OutlineBeat,
    )


# Update one event. Only provided fields are changed. Handled separately from
# _update_entity since its characters_involved/groups_involved columns
# are JSON-encoded lists, not plain strings.
@router.patch("/novel/{novel_id}/events/{entity_id}")
def update_event(novel_id: str, entity_id: str, body: EventUpdate) -> Event:
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, novel_id)
        row = conn.execute(
            """SELECT id, novel_id, title, description, characters_involved, groups_involved
               FROM events WHERE id = ? AND novel_id = ?""",
            (entity_id, novel_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Event not found")

        data = dict(row)
        data["characters_involved"] = (
            json.loads(data["characters_involved"]) if data["characters_involved"] else []
        )
        data["groups_involved"] = (
            json.loads(data["groups_involved"]) if data["groups_involved"] else []
        )
        updated = Event(**data).model_copy(update=updates)

        conn.execute(
            """UPDATE events SET title = ?, description = ?, characters_involved = ?,
               groups_involved = ? WHERE id = ? AND novel_id = ?""",
            (
                updated.title,
                updated.description,
                json.dumps(updated.characters_involved),
                json.dumps(updated.groups_involved),
                entity_id,
                novel_id,
            ),
        )
        conn.commit()
        return updated
    finally:
        conn.close()


# Get the character-outward relationship graph for one novel — a character's
# relationship to any target (character, item, location, group, or
# worldbuilding fact).
@router.get("/novel/{id}/character-relationships")
def get_character_relationships(id: str) -> list[CharacterRelationship]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, novel_id, character_id, target_type, target_id, relationship_type,
                      status, emotional_intensity, open_threads
               FROM character_relationships WHERE novel_id = ?""",
            (id,),
        ).fetchall()
        return [CharacterRelationship(**row) for row in rows]
    finally:
        conn.close()


# Get the group-outward relationship graph for one novel — a group's
# collective stance toward any target. See character_relationships for the
# per-member view, which takes priority over a group's row for the same
# target when both exist.
@router.get("/novel/{id}/group-relationships")
def get_group_relationships(id: str) -> list[GroupRelationship]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, novel_id, group_id, target_type, target_id, relationship_type,
                      status, emotional_intensity, open_threads
               FROM group_relationships WHERE novel_id = ?""",
            (id,),
        ).fetchall()
        return [GroupRelationship(**row) for row in rows]
    finally:
        conn.close()


# Update one novel. Only provided fields are changed.
@router.patch("/novel/{id}")
def update_novel(id: str, body: NovelUpdate) -> Novel:
    updates = body.model_dump(exclude_unset=True)
    conn = get_connection()
    try:
        _require_unlocked(conn, id)
        row = conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Novel not found")

        updated = _row_to_novel(row).model_copy(update=updates)
        update_columns = [col for col in _NOVEL_COLUMNS if col != "id"]
        set_clause = ", ".join(f"{col} = ?" for col in update_columns)

        values = []
        for col in update_columns:
            value = getattr(updated, col)
            if col in _JSON_COLUMNS:
                value = json.dumps(value)
            values.append(value)
        values.append(id)

        conn.execute(f"UPDATE novels SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return updated
    finally:
        conn.close()


# Delete one novel.
@router.delete("/novel/{id}")
def delete_novel(id: str):
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM novels WHERE id = ?", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Novel not found")
        return {"status": "deleted"}
    finally:
        conn.close()


# Picks "{base}_1" if free, else the next free "{base}_N" — mirrors how
# duplicate_novel is asked to name a copy. Checked against every existing
# title so repeated duplicates ("Foo", "Foo_1", "Foo_2", ...) don't collide.
def _next_duplicate_title(conn, base_title: str) -> str:
    existing = {
        row[0] for row in conn.execute("SELECT title FROM novels").fetchall()
    }
    n = 1
    while f"{base_title}_{n}" in existing:
        n += 1
    return f"{base_title}_{n}"


# Deep-copies one novel and every row that hangs off it, across all 17
# tables, under a brand new novel id — a true 1-for-1 duplicate the user can
# freely diverge from without touching the original. Every table's own id
# gets a fresh uuid; every foreign key pointing at one of those old ids
# (novel_id everywhere, plus character_id/secondary_thread_id/group_id/
# outline_beat_id/chapter_id/current_location_id/target_id) is rewritten to
# the matching new id via the remap dicts built as each table is copied, so
# insert order below follows the FK dependency chain (parents before
# children). Columns that hold entity NAMES rather than ids (associated_
# characters, characters_involved/groups_involved, secondary_arc_plot_points.
# characters_involved) are copied verbatim — they're just text, not references
# that could go stale.
@router.post("/novel/{id}/duplicate")
def duplicate_novel(id: str) -> NovelCreateResponse:
    conn = get_connection()
    try:
        novel_row = conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (id,)
        ).fetchone()
        if novel_row is None:
            raise HTTPException(status_code=404, detail="Novel not found")
        novel_row = dict(novel_row)

        new_id = str(uuid.uuid4())
        new_title = _next_duplicate_title(conn, novel_row["title"])

        novel_columns = [col for col in _NOVEL_COLUMNS if col not in ("id", "title")]
        conn.execute(
            f"""INSERT INTO novels (id, title, {', '.join(novel_columns)})
                VALUES (?, ?, {', '.join(['?'] * len(novel_columns))})""",
            (new_id, new_title, *(novel_row[col] for col in novel_columns)),
        )

        # --- secondary_threads: id -> new id ---
        secondary_thread_id_map: dict[str, str] = {}
        for row in conn.execute(
            """SELECT id, description, length, priority, heat, word_count
               FROM secondary_threads WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            new_thread_id = str(uuid.uuid4())
            secondary_thread_id_map[row["id"]] = new_thread_id
            conn.execute(
                """INSERT INTO secondary_threads
                   (id, novel_id, description, length, priority, heat, word_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (new_thread_id, new_id, row["description"], row["length"], row["priority"],
                 row["heat"], row["word_count"]),
            )

        # --- characters: id -> new id ---
        character_id_map: dict[str, str] = {}
        for row in conn.execute(
            f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?", (id,)
        ).fetchall():
            row = dict(row)
            new_character_id = str(uuid.uuid4())
            character_id_map[row["id"]] = new_character_id
            cols = [col for col in _CHARACTER_COLUMNS if col not in ("id", "novel_id")]
            conn.execute(
                f"""INSERT INTO characters (id, novel_id, {', '.join(cols)})
                    VALUES (?, ?, {', '.join(['?'] * len(cols))})""",
                (new_character_id, new_id, *(row[col] for col in cols)),
            )

        # --- spine_beats: id -> new id (novel_id only FK) ---
        for row in conn.execute(
            """SELECT id, sort_order, heros_journey_step, summary, word_count_pct,
                      time_gap_before, forbidden_element_active, intimate_arc_role,
                      intimate_entry_mode
               FROM spine_beats WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO spine_beats
                   (id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                    time_gap_before, forbidden_element_active, intimate_arc_role,
                    intimate_entry_mode)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, row["sort_order"], row["heros_journey_step"],
                 row["summary"], row["word_count_pct"], row["time_gap_before"],
                 row["forbidden_element_active"], row["intimate_arc_role"],
                 row["intimate_entry_mode"]),
            )

        # --- secondary_arc_plot_points: id -> new id, secondary_thread_id remapped ---
        for row in conn.execute(
            """SELECT id, secondary_thread_id, sort_order, summary, characters_involved
               FROM secondary_arc_plot_points WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO secondary_arc_plot_points
                   (id, novel_id, secondary_thread_id, sort_order, summary, characters_involved)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, secondary_thread_id_map[row["secondary_thread_id"]],
                 row["sort_order"], row["summary"], row["characters_involved"]),
            )

        # --- worldbuilding (one row, novel_id only FK) ---
        worldbuilding_row = conn.execute(
            """SELECT story_type, time_period, anchor_location, anchor_location_description
               FROM worldbuilding WHERE novel_id = ?""",
            (id,),
        ).fetchone()
        if worldbuilding_row is not None:
            conn.execute(
                """INSERT INTO worldbuilding
                   (id, novel_id, story_type, time_period, anchor_location,
                    anchor_location_description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, worldbuilding_row["story_type"],
                 worldbuilding_row["time_period"], worldbuilding_row["anchor_location"],
                 worldbuilding_row["anchor_location_description"]),
            )

        # --- worldbuilding_facts: id -> new id (novel_id only FK), keyed by title for outline remap ---
        worldbuilding_fact_id_map: dict[str, str] = {}
        for row in conn.execute(
            """SELECT id, sort_order, category, title, description
               FROM worldbuilding_facts WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            new_fact_id = str(uuid.uuid4())
            worldbuilding_fact_id_map[row["id"]] = new_fact_id
            conn.execute(
                """INSERT INTO worldbuilding_facts
                   (id, novel_id, sort_order, category, title, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (new_fact_id, new_id, row["sort_order"], row["category"], row["title"],
                 row["description"]),
            )

        # --- locations: id -> new id ---
        location_id_map: dict[str, str] = {}
        for row in conn.execute(
            "SELECT id, name, description FROM locations WHERE novel_id = ?", (id,)
        ).fetchall():
            new_location_id = str(uuid.uuid4())
            location_id_map[row["id"]] = new_location_id
            conn.execute(
                "INSERT INTO locations (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (new_location_id, new_id, row["name"], row["description"]),
            )

        # --- items: id -> new id ---
        item_id_map: dict[str, str] = {}
        for row in conn.execute(
            "SELECT id, name, description FROM items WHERE novel_id = ?", (id,)
        ).fetchall():
            new_item_id = str(uuid.uuid4())
            item_id_map[row["id"]] = new_item_id
            conn.execute(
                "INSERT INTO items (id, novel_id, name, description) VALUES (?, ?, ?, ?)",
                (new_item_id, new_id, row["name"], row["description"]),
            )

        # --- groups: id -> new id (associated_characters is names, copied as-is) ---
        group_id_map: dict[str, str] = {}
        for row in conn.execute(
            """SELECT id, name, description, associated_characters
               FROM groups WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            new_group_id = str(uuid.uuid4())
            group_id_map[row["id"]] = new_group_id
            conn.execute(
                """INSERT INTO groups (id, novel_id, name, description, associated_characters)
                   VALUES (?, ?, ?, ?, ?)""",
                (new_group_id, new_id, row["name"], row["description"],
                 row["associated_characters"]),
            )

        # --- events: id -> new id (characters_involved/groups_involved are names) ---
        for row in conn.execute(
            """SELECT id, title, description, characters_involved, groups_involved
               FROM events WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO events
                   (id, novel_id, title, description, characters_involved, groups_involved)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, row["title"], row["description"],
                 row["characters_involved"], row["groups_involved"]),
            )

        # Remaps one JSON-encoded id list (e.g. outline_beats.characters_present)
        # using the given old-id -> new-id map, dropping any id that map doesn't
        # cover (shouldn't happen — every id here was copied above).
        def _remap_ids(json_text: str | None, id_map: dict[str, str]) -> str:
            ids = json.loads(json_text) if json_text else []
            return json.dumps([id_map[i] for i in ids if i in id_map])

        # --- outline_beats: id -> new id, presence columns remapped ---
        outline_beat_id_map: dict[str, str] = {}
        for row in conn.execute(
            """SELECT id, sort_order, content, word_count, title, pov_character,
                      pov_voice_note, tone, characters_present, items_present,
                      locations_present, groups_present, worldbuilding_facts_present
               FROM outline_beats WHERE novel_id = ? ORDER BY sort_order""",
            (id,),
        ).fetchall():
            new_beat_id = str(uuid.uuid4())
            outline_beat_id_map[row["id"]] = new_beat_id
            conn.execute(
                """INSERT INTO outline_beats
                   (id, novel_id, sort_order, content, word_count, title,
                    pov_character, pov_voice_note, tone, characters_present,
                    items_present, locations_present, groups_present,
                    worldbuilding_facts_present)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    new_beat_id, new_id, row["sort_order"], row["content"], row["word_count"],
                    row["title"], row["pov_character"], row["pov_voice_note"], row["tone"],
                    _remap_ids(row["characters_present"], character_id_map),
                    _remap_ids(row["items_present"], item_id_map),
                    _remap_ids(row["locations_present"], location_id_map),
                    _remap_ids(row["groups_present"], group_id_map),
                    _remap_ids(row["worldbuilding_facts_present"], worldbuilding_fact_id_map),
                ),
            )

        # --- raw_outline_beats: id -> new id, presence columns remapped (no
        # correspondence to outline_beats rows — see the table's own comment) ---
        for row in conn.execute(
            """SELECT id, sort_order, content, word_count, title, pov_character,
                      pov_voice_note, tone, characters_present, items_present,
                      locations_present, groups_present, worldbuilding_facts_present
               FROM raw_outline_beats WHERE novel_id = ? ORDER BY sort_order""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO raw_outline_beats
                   (id, novel_id, sort_order, content, word_count, title,
                    pov_character, pov_voice_note, tone, characters_present,
                    items_present, locations_present, groups_present,
                    worldbuilding_facts_present)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), new_id, row["sort_order"], row["content"], row["word_count"],
                    row["title"], row["pov_character"], row["pov_voice_note"], row["tone"],
                    _remap_ids(row["characters_present"], character_id_map),
                    _remap_ids(row["items_present"], item_id_map),
                    _remap_ids(row["locations_present"], location_id_map),
                    _remap_ids(row["groups_present"], group_id_map),
                    _remap_ids(row["worldbuilding_facts_present"], worldbuilding_fact_id_map),
                ),
            )

        # target_id's table depends on target_type — resolve against whichever
        # id map matches, same polymorphic discipline the original INSERT
        # (see create_novel's initial_state block) reads out of the database.
        target_id_maps = {
            "character": character_id_map,
            "location": location_id_map,
            "item": item_id_map,
            "group": group_id_map,
            "worldbuilding_fact": worldbuilding_fact_id_map,
        }

        # --- character_relationships: id -> new id, character_id + target_id remapped ---
        for row in conn.execute(
            """SELECT id, character_id, target_type, target_id, relationship_type,
                      status, emotional_intensity, open_threads
               FROM character_relationships WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            new_target_id = target_id_maps.get(row["target_type"], {}).get(row["target_id"])
            if row["character_id"] not in character_id_map or new_target_id is None:
                continue
            conn.execute(
                """INSERT INTO character_relationships
                   (id, novel_id, character_id, target_type, target_id, relationship_type,
                    status, emotional_intensity, open_threads)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, character_id_map[row["character_id"]],
                 row["target_type"], new_target_id, row["relationship_type"], row["status"],
                 row["emotional_intensity"], row["open_threads"]),
            )

        # --- group_relationships: id -> new id, group_id + target_id remapped ---
        for row in conn.execute(
            """SELECT id, group_id, target_type, target_id, relationship_type,
                      status, emotional_intensity, open_threads
               FROM group_relationships WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            new_target_id = target_id_maps.get(row["target_type"], {}).get(row["target_id"])
            if row["group_id"] not in group_id_map or new_target_id is None:
                continue
            conn.execute(
                """INSERT INTO group_relationships
                   (id, novel_id, group_id, target_type, target_id, relationship_type,
                    status, emotional_intensity, open_threads)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), new_id, group_id_map[row["group_id"]],
                 row["target_type"], new_target_id, row["relationship_type"], row["status"],
                 row["emotional_intensity"], row["open_threads"]),
            )

        # --- chapters: id -> new id, outline_beat_id remapped ---
        chapter_id_map: dict[str, str] = {}
        for row in conn.execute(
            f"SELECT {', '.join(_CHAPTER_COLUMNS)} FROM chapters WHERE novel_id = ?", (id,)
        ).fetchall():
            row = dict(row)
            new_chapter_id = str(uuid.uuid4())
            chapter_id_map[row["id"]] = new_chapter_id
            cols = [col for col in _CHAPTER_COLUMNS if col not in ("id", "novel_id", "outline_beat_id")]
            conn.execute(
                f"""INSERT INTO chapters (id, novel_id, outline_beat_id, {', '.join(cols)})
                    VALUES (?, ?, ?, {', '.join(['?'] * len(cols))})""",
                (new_chapter_id, new_id, outline_beat_id_map[row["outline_beat_id"]],
                 *(row[col] for col in cols)),
            )

        # --- character_state: id -> new id, character_id/chapter_id/current_location_id remapped ---
        for row in conn.execute(
            """SELECT id, character_id, chapter_id, sort_order, physical_state, emotional_state,
                      emotional_intensity, current_location_id, goals, flaw_active, flaw_note,
                      knowledge_flags
               FROM character_state WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO character_state
                   (id, novel_id, character_id, chapter_id, sort_order, physical_state,
                    emotional_state, emotional_intensity, current_location_id, goals,
                    flaw_active, flaw_note, knowledge_flags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), new_id, character_id_map[row["character_id"]],
                    chapter_id_map[row["chapter_id"]] if row["chapter_id"] else None,
                    row["sort_order"], row["physical_state"], row["emotional_state"],
                    row["emotional_intensity"],
                    location_id_map.get(row["current_location_id"]) if row["current_location_id"] else None,
                    row["goals"], row["flaw_active"], row["flaw_note"], row["knowledge_flags"],
                ),
            )

        # --- group_state: id -> new id, group_id/chapter_id remapped ---
        for row in conn.execute(
            """SELECT id, group_id, chapter_id, sort_order, status, disposition, cohesion,
                      open_threads, knowledge_flags
               FROM group_state WHERE novel_id = ?""",
            (id,),
        ).fetchall():
            conn.execute(
                """INSERT INTO group_state
                   (id, novel_id, group_id, chapter_id, sort_order, status, disposition,
                    cohesion, open_threads, knowledge_flags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), new_id, group_id_map[row["group_id"]],
                    chapter_id_map[row["chapter_id"]] if row["chapter_id"] else None,
                    row["sort_order"], row["status"], row["disposition"], row["cohesion"],
                    row["open_threads"], row["knowledge_flags"],
                ),
            )

        conn.commit()
        return NovelCreateResponse(id=new_id)
    finally:
        conn.close()


# ============================================================================
# Chapters — prose generation
# ============================================================================

_CHAPTER_COLUMNS = [
    "id",
    "novel_id",
    "outline_beat_id",
    "sort_order",
    "raw_prose",
    "edited_prose",
    "word_count",
    "summary",
    "generate_model",
    "generate_reasoning",
    "edit_model",
    "edit_reasoning",
    "state_model",
    "state_reasoning",
]

_CHARACTER_STATE_JSON_COLUMNS = {"goals", "knowledge_flags"}
_GROUP_STATE_JSON_COLUMNS = {"open_threads", "knowledge_flags"}


# Current state (as of the given chapter's opening, i.e. the latest row with
# sort_order <= that chapter's sort_order - 1 — equivalently, sort_order <
# the requested chapter's own sort_order) for every character in the novel.
# One row per character, the latest as-of-that-point row — never the full
# history. as_of_sort_order is the chapter about to be generated; state
# strictly BEFORE it is what a writer needs.
def _current_character_states(conn, novel_id: str, as_of_sort_order: int) -> dict[str, dict]:
    rows = conn.execute(
        """SELECT cs.* FROM character_state cs
           INNER JOIN (
               SELECT character_id, MAX(sort_order) AS max_sort_order
               FROM character_state
               WHERE novel_id = ? AND sort_order < ?
               GROUP BY character_id
           ) latest
           ON cs.character_id = latest.character_id AND cs.sort_order = latest.max_sort_order
           WHERE cs.novel_id = ?""",
        (novel_id, as_of_sort_order, novel_id),
    ).fetchall()
    by_character_id = {}
    for row in rows:
        data = dict(row)
        for col in _CHARACTER_STATE_JSON_COLUMNS:
            data[col] = json.loads(data[col]) if data[col] else []
        data["flaw_active"] = bool(data["flaw_active"])
        by_character_id[data["character_id"]] = data
    return by_character_id


def _current_group_states(conn, novel_id: str, as_of_sort_order: int) -> dict[str, dict]:
    rows = conn.execute(
        """SELECT gs.* FROM group_state gs
           INNER JOIN (
               SELECT group_id, MAX(sort_order) AS max_sort_order
               FROM group_state
               WHERE novel_id = ? AND sort_order < ?
               GROUP BY group_id
           ) latest
           ON gs.group_id = latest.group_id AND gs.sort_order = latest.max_sort_order
           WHERE gs.novel_id = ?""",
        (novel_id, as_of_sort_order, novel_id),
    ).fetchall()
    by_group_id = {}
    for row in rows:
        data = dict(row)
        for col in _GROUP_STATE_JSON_COLUMNS:
            data[col] = json.loads(data[col]) if data[col] else []
        by_group_id[data["group_id"]] = data
    return by_group_id


# Seeds one sort_order=-1 baseline character_state/group_state row per
# character/group, so chapter one's writing call has something to read
# instead of a special-cased empty-state branch. Derives a light default from
# each entity's existing static bible fields where a reasonable mapping
# exists; left blank otherwise. No-op (idempotent) if baseline rows already
# exist for this novel.
def _seed_baseline_state(conn, novel_id: str) -> None:
    existing = conn.execute(
        "SELECT COUNT(*) FROM character_state WHERE novel_id = ? AND sort_order = -1", (novel_id,)
    ).fetchone()[0]
    if existing:
        return
    for row in conn.execute(
        "SELECT id, flaws FROM characters WHERE novel_id = ?", (novel_id,)
    ).fetchall():
        flaws = json.loads(row["flaws"]) if row["flaws"] else []
        conn.execute(
            """INSERT INTO character_state
               (id, novel_id, character_id, chapter_id, sort_order, flaw_active, flaw_note,
                goals, knowledge_flags)
               VALUES (?, ?, ?, NULL, -1, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                novel_id,
                row["id"],
                1 if flaws else 0,
                flaws[0] if flaws else None,
                json.dumps([]),
                json.dumps([]),
            ),
        )
    for row in conn.execute("SELECT id FROM groups WHERE novel_id = ?", (novel_id,)).fetchall():
        conn.execute(
            """INSERT INTO group_state
               (id, novel_id, group_id, chapter_id, sort_order, open_threads, knowledge_flags)
               VALUES (?, ?, ?, NULL, -1, ?, ?)""",
            (str(uuid.uuid4()), novel_id, row["id"], json.dumps([]), json.dumps([])),
        )


# Builds the present_characters/present_items/present_locations/present_groups/
# present_worldbuilding_facts argument lists chapters.generate_chapter_prose
# needs, by resolving a beat's own *_present id lists (see OutlineBeat) against
# the real rows, merging in each present character's/group's current state
# (as of the chapter about to be generated) under the "state" key, and
# resolving current_location_id to a location name for display.
def _present_entities_for_beat(conn, novel_id: str, beat: dict) -> dict:
    def _ids(col: str) -> list[str]:
        return json.loads(beat[col]) if beat[col] else []

    character_states = _current_character_states(conn, novel_id, beat["sort_order"])
    group_states = _current_group_states(conn, novel_id, beat["sort_order"])
    location_names_by_id = {
        r["id"]: r["name"]
        for r in conn.execute("SELECT id, name FROM locations WHERE novel_id = ?", (novel_id,)).fetchall()
    }

    present_characters = []
    for cid in _ids("characters_present"):
        row = conn.execute(
            f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE id = ? AND novel_id = ?",
            (cid, novel_id),
        ).fetchone()
        if row is None:
            continue
        character = _character_row_to_dict(row)
        state = character_states.get(cid, {})
        if state.get("current_location_id"):
            state = {**state, "current_location_name": location_names_by_id.get(state["current_location_id"])}
        character["state"] = state
        present_characters.append(character)

    present_items = [
        dict(r)
        for cid in _ids("items_present")
        for r in conn.execute(
            "SELECT id, name, description FROM items WHERE id = ? AND novel_id = ?", (cid, novel_id)
        ).fetchall()
    ]
    present_locations = [
        dict(r)
        for cid in _ids("locations_present")
        for r in conn.execute(
            "SELECT id, name, description FROM locations WHERE id = ? AND novel_id = ?", (cid, novel_id)
        ).fetchall()
    ]
    present_groups = []
    for gid in _ids("groups_present"):
        row = conn.execute(
            "SELECT id, name, description FROM groups WHERE id = ? AND novel_id = ?", (gid, novel_id)
        ).fetchone()
        if row is None:
            continue
        group = dict(row)
        group["state"] = group_states.get(gid, {})
        present_groups.append(group)
    present_worldbuilding_facts = [
        dict(r)
        for cid in _ids("worldbuilding_facts_present")
        for r in conn.execute(
            "SELECT id, title, category, description FROM worldbuilding_facts WHERE id = ? AND novel_id = ?",
            (cid, novel_id),
        ).fetchall()
    ]

    return {
        "present_characters": present_characters,
        "present_items": present_items,
        "present_locations": present_locations,
        "present_groups": present_groups,
        "present_worldbuilding_facts": present_worldbuilding_facts,
    }


# name+role rosters (never full bibles) for every character/group NOT
# present in this chapter — extract_chapter_state's offscreen-change
# lookup, kept minimal so that call's context stays bounded.
def _full_roster_excluding(conn, novel_id: str, present_ids: set[str], table: str, extra_cols: str = "") -> list[dict]:
    cols = f"id, name{extra_cols}"
    rows = conn.execute(f"SELECT {cols} FROM {table} WHERE novel_id = ?", (novel_id,)).fetchall()
    return [dict(r) for r in rows if r["id"] not in present_ids]


# The running summary for the chapter about to be generated: every prior
# chapter's own summary, in order, joined with blank lines. Never stored as
# its own blob — recomputed fresh here every time, so regenerating an earlier
# chapter's summary can never desync a later chapter's prompt (see
# chapters.py's module docstring).
def _running_summary(conn, novel_id: str, before_sort_order: int) -> str:
    rows = conn.execute(
        """SELECT summary FROM chapters WHERE novel_id = ? AND sort_order < ?
           ORDER BY sort_order""",
        (novel_id, before_sort_order),
    ).fetchall()
    return "\n\n".join(r["summary"] for r in rows)


def _row_to_chapter(row) -> Chapter:
    data = dict(row)
    data["generate_reasoning"] = bool(data.pop("generate_reasoning", False))
    data["edit_reasoning"] = bool(data.pop("edit_reasoning", False))
    data["state_reasoning"] = bool(data.pop("state_reasoning", False))
    return Chapter(**{k: v for k, v in data.items() if k in Chapter.model_fields})


# List the chapters generated so far for one novel — light payload (no
# prose) for the sidebar. Combine with GET /novel/{id}/outline client-side to
# know the full chapter count including not-yet-generated ones.
@router.get("/novel/{id}/chapters")
def get_chapters(id: str) -> list[ChapterSummary]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT c.id, c.outline_beat_id, c.sort_order, c.word_count, ob.title
               FROM chapters c JOIN outline_beats ob ON ob.id = c.outline_beat_id
               WHERE c.novel_id = ? ORDER BY c.sort_order""",
            (id,),
        ).fetchall()
        return [ChapterSummary(**dict(r)) for r in rows]
    finally:
        conn.close()


# Full detail (including prose) for one generated chapter.
@router.get("/novel/{id}/chapters/{beat_id}")
def get_chapter(id: str, beat_id: str) -> Chapter:
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {', '.join(_CHAPTER_COLUMNS)} FROM chapters "
            "WHERE novel_id = ? AND outline_beat_id = ?",
            (id, beat_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Chapter not generated yet")
        return _row_to_chapter(row)
    finally:
        conn.close()


# Runs the 3-call pipeline (generate -> edit -> extract state) for one
# outline beat and persists the result. Only the next ungenerated beat in
# sort_order may be generated — chapters are written strictly in order, one
# at a time, matching the client's single-column "generate next" flow. The
# whole thing is one uncommitted transaction: if any of the 3 calls fails,
# everything rolls back rather than leaving a chapter with prose but no
# state (same discipline as regenerate_outline's rollback-on-failure).
def _run_chapter_pipeline(conn, novel_id: str, beat_id: str, body: ChapterGenerate, is_regenerate: bool) -> Chapter:
    novel_row = dict(
        conn.execute(f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (novel_id,)).fetchone()
        or {}
    )
    if not novel_row:
        raise HTTPException(status_code=404, detail="Novel not found")

    beat_row = conn.execute(
        f"SELECT {', '.join(_OUTLINE_BEAT_COLUMNS)} FROM outline_beats WHERE id = ? AND novel_id = ?",
        (beat_id, novel_id),
    ).fetchone()
    if beat_row is None:
        raise HTTPException(status_code=404, detail="Outline beat not found")
    beat = dict(beat_row)

    existing_chapter = conn.execute(
        "SELECT id FROM chapters WHERE outline_beat_id = ? AND novel_id = ?", (beat_id, novel_id)
    ).fetchone()
    last_sort_order_row = conn.execute(
        "SELECT MAX(sort_order) FROM chapters WHERE novel_id = ?", (novel_id,)
    ).fetchone()
    last_sort_order = last_sort_order_row[0]

    if is_regenerate:
        if existing_chapter is None:
            raise HTTPException(status_code=404, detail="Chapter not generated yet — nothing to regenerate")
        if last_sort_order is not None and beat["sort_order"] != last_sort_order:
            raise HTTPException(
                status_code=409,
                detail="Only the most recently generated chapter can be regenerated",
            )
    else:
        if existing_chapter is not None:
            raise HTTPException(status_code=409, detail="This chapter has already been generated")
        expected_next = 0 if last_sort_order is None else last_sort_order + 1
        if beat["sort_order"] != expected_next:
            raise HTTPException(
                status_code=409,
                detail=f"Chapters must be generated in order — chapter {expected_next + 1} is next",
            )

    if not (beat["characters_present"] or beat["locations_present"]):
        raise HTTPException(
            status_code=409,
            detail="This outline has no resolved entity-presence data — regenerate the outline "
            "before generating chapters",
        )

    _seed_baseline_state(conn, novel_id)

    present = _present_entities_for_beat(conn, novel_id, beat)
    running_summary = _running_summary(conn, novel_id, beat["sort_order"])

    generate_model = body.generate_model or novel_row.get("generate_model") or DEFAULTS["generate"]
    generate_reasoning = (
        body.generate_reasoning if body.generate_reasoning is not None else bool(novel_row.get("generate_reasoning"))
    )
    edit_model = body.edit_model or novel_row.get("edit_model") or DEFAULTS["edit"]
    edit_reasoning = body.edit_reasoning if body.edit_reasoning is not None else bool(novel_row.get("edit_reasoning"))
    state_model = body.state_model or novel_row.get("state_model") or DEFAULTS["state"]
    state_reasoning = body.state_reasoning if body.state_reasoning is not None else bool(novel_row.get("state_reasoning"))

    raw_prose = generate_chapter_prose(
        novel_row,
        beat,
        running_summary,
        present["present_characters"],
        present["present_items"],
        present["present_locations"],
        present["present_groups"],
        present["present_worldbuilding_facts"],
        model=generate_model,
        reasoning=generate_reasoning,
    )
    # Edit step disabled for now — edit_chapter_prose needs new prompts written
    # (see chapter_editing_prompts.py). raw_prose is stored as edited_prose
    # directly so the rest of the pipeline/schema/frontend (which reads
    # edited_prose) needs no other change while this step is off.
    # edited_prose = edit_chapter_prose(
    #     novel_row,
    #     beat,
    #     raw_prose,
    #     present["present_characters"],
    #     present["present_groups"],
    #     model=edit_model,
    #     reasoning=edit_reasoning,
    # )
    edited_prose = raw_prose

    present_character_ids = {c["id"] for c in present["present_characters"]}
    present_group_ids = {g["id"] for g in present["present_groups"]}
    full_character_roster = _full_roster_excluding(
        conn, novel_id, present_character_ids, "characters", ", role"
    )
    full_group_roster = _full_roster_excluding(conn, novel_id, present_group_ids, "groups")

    state_result = extract_chapter_state(
        novel_row,
        beat,
        edited_prose,
        present["present_characters"],
        full_character_roster,
        present["present_groups"],
        full_group_roster,
        model=state_model,
        reasoning=state_reasoning,
    )

    word_count = len(edited_prose.split())
    now = datetime.now(timezone.utc).isoformat()

    if is_regenerate:
        chapter_id = existing_chapter["id"]
        conn.execute("DELETE FROM character_state WHERE chapter_id = ?", (chapter_id,))
        conn.execute("DELETE FROM group_state WHERE chapter_id = ?", (chapter_id,))
        conn.execute(
            """UPDATE chapters SET raw_prose = ?, edited_prose = ?, word_count = ?, summary = ?,
               generate_model = ?, generate_reasoning = ?, edit_model = ?, edit_reasoning = ?,
               state_model = ?, state_reasoning = ?
               WHERE id = ?""",
            (
                raw_prose,
                edited_prose,
                word_count,
                state_result.get("chapter_summary", ""),
                generate_model,
                int(generate_reasoning),
                edit_model,
                int(edit_reasoning),
                state_model,
                int(state_reasoning),
                chapter_id,
            ),
        )
    else:
        chapter_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO chapters
               (id, novel_id, outline_beat_id, sort_order, raw_prose, edited_prose, word_count, summary,
                generate_model, generate_reasoning, edit_model, edit_reasoning, state_model, state_reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                chapter_id,
                novel_id,
                beat_id,
                beat["sort_order"],
                raw_prose,
                edited_prose,
                word_count,
                state_result.get("chapter_summary", ""),
                generate_model,
                int(generate_reasoning),
                edit_model,
                int(edit_reasoning),
                state_model,
                int(state_reasoning),
            ),
        )

    # Name -> id maps for resolving extract_chapter_state's character_name/
    # group_name/current_location back to real ids — same discipline as
    # everywhere else in this file (see init_relationships).
    character_id_by_name = {
        r["name"]: r["id"]
        for r in conn.execute("SELECT id, name FROM characters WHERE novel_id = ?", (novel_id,)).fetchall()
    }
    group_id_by_name = {
        r["name"]: r["id"]
        for r in conn.execute("SELECT id, name FROM groups WHERE novel_id = ?", (novel_id,)).fetchall()
    }
    location_id_by_name = {
        r["name"]: r["id"]
        for r in conn.execute("SELECT id, name FROM locations WHERE novel_id = ?", (novel_id,)).fetchall()
    }

    for cs in state_result.get("character_states", []):
        if not cs.get("changed"):
            continue
        character_id = character_id_by_name.get(cs.get("character_name", ""))
        if character_id is None:
            continue
        current_location_id = location_id_by_name.get(cs.get("current_location") or "")
        print(
            f"[state change] chapter sort_order={beat['sort_order']} character={cs.get('character_name')} "
            f"physical={cs.get('physical_state')!r} emotional={cs.get('emotional_state')!r} "
            f"({cs.get('emotional_intensity')}) location={cs.get('current_location')!r}",
            flush=True,
        )
        conn.execute(
            """INSERT INTO character_state
               (id, novel_id, character_id, chapter_id, sort_order, physical_state, emotional_state,
                emotional_intensity, current_location_id, goals, flaw_active, flaw_note, knowledge_flags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                novel_id,
                character_id,
                chapter_id,
                beat["sort_order"],
                cs.get("physical_state"),
                cs.get("emotional_state"),
                cs.get("emotional_intensity"),
                current_location_id,
                json.dumps(cs.get("goals", [])),
                1 if cs.get("flaw_active") else 0,
                cs.get("flaw_note"),
                json.dumps(cs.get("knowledge_flags", [])),
            ),
        )

    for gs in state_result.get("group_states", []):
        if not gs.get("changed"):
            continue
        group_id = group_id_by_name.get(gs.get("group_name", ""))
        if group_id is None:
            continue
        print(
            f"[state change] chapter sort_order={beat['sort_order']} group={gs.get('group_name')} "
            f"status={gs.get('status')!r} disposition={gs.get('disposition')!r} cohesion={gs.get('cohesion')}",
            flush=True,
        )
        conn.execute(
            """INSERT INTO group_state
               (id, novel_id, group_id, chapter_id, sort_order, status, disposition, cohesion,
                open_threads, knowledge_flags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                novel_id,
                group_id,
                chapter_id,
                beat["sort_order"],
                gs.get("status"),
                gs.get("disposition"),
                gs.get("cohesion"),
                json.dumps(gs.get("open_threads", [])),
                json.dumps(gs.get("knowledge_flags", [])),
            ),
        )

    # Chapter one generating for the first time locks the whole story bible —
    # see _require_unlocked. Not set on regenerate (already locked by then).
    if not is_regenerate and beat["sort_order"] == 0:
        print(f"[state change] novel_id={novel_id} locked=1 locked_at={now}", flush=True)
        conn.execute("UPDATE novels SET locked = 1, locked_at = ? WHERE id = ?", (now, novel_id))

    row = conn.execute(
        f"SELECT {', '.join(_CHAPTER_COLUMNS)} FROM chapters WHERE id = ?", (chapter_id,)
    ).fetchone()
    return _row_to_chapter(row)


@router.post("/novel/{id}/chapters/{beat_id}/generate")
def generate_chapter(id: str, beat_id: str, body: ChapterGenerate) -> Chapter:
    conn = get_connection()
    try:
        chapter = _run_chapter_pipeline(conn, id, beat_id, body, is_regenerate=False)
        conn.commit()
        return chapter
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=502, detail=f"chapter generation failed: {e}") from e
    finally:
        conn.close()


@router.post("/novel/{id}/chapters/{beat_id}/regenerate")
def regenerate_chapter(id: str, beat_id: str, body: ChapterGenerate) -> Chapter:
    conn = get_connection()
    try:
        chapter = _run_chapter_pipeline(conn, id, beat_id, body, is_regenerate=True)
        conn.commit()
        return chapter
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=502, detail=f"chapter regeneration failed: {e}") from e
    finally:
        conn.close()
