import json
import sqlite3
import uuid
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "db"
DB_PATH = DB_DIR / "slopnovels.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Create the db directory, file, and tables if they don't already exist.
def init_db() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS novels (
                id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                author TEXT,
                word_count INTEGER,
                premise TEXT NOT NULL,
                setting_context TEXT,
                primary_genre TEXT,
                region TEXT,
                character_seeds TEXT,
                sub_genres TEXT,
                tone TEXT,
                spice_level TEXT,
                literary_voice TEXT,
                tense TEXT,
                perspective TEXT,
                forbidden_element TEXT,
                themes TEXT,
                story_type TEXT,
                time_period TEXT,
                anchor_location TEXT,
                anchor_location_description TEXT,
                constraints TEXT,
                tone_notes TEXT,
                characters_notes TEXT,
                worldbuilding_notes TEXT,
                character_generation_notes TEXT,
                primary_thread TEXT,
                primary_word_count INTEGER,
                metadata_model TEXT,
                characters_model TEXT,
                worldbuilding_model TEXT,
                primary_thread_model TEXT,
                secondary_arcs_model TEXT,
                outline_model TEXT,
                outline_audit_model TEXT,
                entities_model TEXT,
                initial_state_model TEXT,
                metadata_reasoning INTEGER,
                characters_reasoning INTEGER,
                worldbuilding_reasoning INTEGER,
                primary_thread_reasoning INTEGER,
                secondary_arcs_reasoning INTEGER,
                outline_reasoning INTEGER,
                outline_audit_reasoning INTEGER,
                entities_reasoning INTEGER,
                initial_state_reasoning INTEGER
            )
            """
        )
        # Migrate existing dbs created before these columns were added.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(novels)")}
        if "themes" not in columns:
            conn.execute("ALTER TABLE novels ADD COLUMN themes TEXT")
        for column in (
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
            "region",
            "character_seeds",
            "setting_context",
        ):
            if column not in columns:
                conn.execute(f"ALTER TABLE novels ADD COLUMN {column} TEXT")
        if "primary_word_count" not in columns:
            conn.execute("ALTER TABLE novels ADD COLUMN primary_word_count INTEGER")
        for column in (
            "metadata_model",
            "characters_model",
            "worldbuilding_model",
            "primary_thread_model",
            "secondary_arcs_model",
            "outline_model",
            "outline_audit_model",
            "entities_model",
            "initial_state_model",
        ):
            if column not in columns:
                conn.execute(f"ALTER TABLE novels ADD COLUMN {column} TEXT")
        for column in (
            "metadata_reasoning",
            "characters_reasoning",
            "worldbuilding_reasoning",
            "primary_thread_reasoning",
            "secondary_arcs_reasoning",
            "outline_reasoning",
            "outline_audit_reasoning",
            "entities_reasoning",
            "initial_state_reasoning",
        ):
            if column not in columns:
                conn.execute(f"ALTER TABLE novels ADD COLUMN {column} INTEGER")

        # Subplot seeds attached to a novel at creation time. Up to 3 per
        # novel (enforced client-side). length is the percentage of that
        # storyline actually resolved in this story — the rest is left open
        # for a later story in the series. priority is how much narrative
        # weight the thread gets; heat is a legacy intensity weight; TV-safe mode treats it as comic/dramatic intensity only.
        # Independent of spice_level (also legacy; default none).
        # word_count is decided by init_secondary_arcs (2000-4000, based on
        # how much plot that thread's length actually allows) and is null
        # until that step runs.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secondary_threads (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                description TEXT NOT NULL,
                length INTEGER NOT NULL,
                priority INTEGER NOT NULL,
                heat INTEGER NOT NULL,
                word_count INTEGER
            )
            """
        )
        thread_columns = {row[1] for row in conn.execute("PRAGMA table_info(secondary_threads)")}
        if "word_count" not in thread_columns:
            conn.execute("ALTER TABLE secondary_threads ADD COLUMN word_count INTEGER")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                role TEXT,
                age INTEGER,
                gender TEXT,
                sexuality TEXT,
                occupation TEXT,
                appearance TEXT,
                physical_characteristics TEXT,
                personality TEXT,
                backstory TEXT,
                fears TEXT,
                flaws TEXT,
                contradictions TEXT,
                hobbies TEXT,
                spiritual_beliefs TEXT,
                character_voice TEXT,
                speech_patterns TEXT
            )
            """
        )
        # Migrate existing dbs created before these columns were added.
        character_columns = {row[1] for row in conn.execute("PRAGMA table_info(characters)")}
        for column in (
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
        ):
            if column not in character_columns:
                col_type = "INTEGER" if column == "age" else "TEXT"
                conn.execute(f"ALTER TABLE characters ADD COLUMN {column} {col_type}")

        # Internal generation input — the protagonist's full hero's-journey
        # arc from init_primary_thread, one row per plot point, in order.
        # sort_order preserves the 9-step sequence since sqlite doesn't
        # guarantee row order without it. Not exposed via the API; init_outline
        # reads this to write the actual user-facing outline (see below).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spine_beats (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                heros_journey_step TEXT NOT NULL,
                summary TEXT NOT NULL,
                word_count_pct INTEGER,
                time_gap_before TEXT,
                forbidden_element_active INTEGER,
                intimate_arc_role TEXT,
                intimate_entry_mode TEXT
            )
            """
        )
        # Migrate existing dbs created before this column was added.
        spine_columns = {row[1] for row in conn.execute("PRAGMA table_info(spine_beats)")}
        if "intimate_entry_mode" not in spine_columns:
            conn.execute("ALTER TABLE spine_beats ADD COLUMN intimate_entry_mode TEXT")

        # Internal generation input — one row per plot point of a
        # secondary_thread's arc from init_secondary_arcs, in order. Not
        # exposed via the API; init_outline reads this to write the actual
        # user-facing outline (see below).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secondary_arc_plot_points (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                secondary_thread_id TEXT NOT NULL REFERENCES secondary_threads(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                summary TEXT NOT NULL,
                characters_involved TEXT
            )
            """
        )

        # The final, user-facing outline — one row per beat, in order.
        # Written by init_outline, which weaves the primary thread and
        # secondary arcs into a single detailed prose sequence. This is the
        # only spine-like artifact exposed via the API/UI; spine_beats and
        # secondary_arc_plot_points above are internal inputs to it.
        # word_count is an absolute estimate (not a percentage) of how many
        # words this beat will run to once actually drafted into prose —
        # beats vary freely in length (a brief brooding moment vs. a long
        # scene), so there's no fixed total for these to sum to.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outline_beats (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                title TEXT,
                pov_character TEXT,
                pov_voice_note TEXT,
                tone TEXT
            )
            """
        )
        # Migrate existing dbs: the column used to hold a 0-100 percentage
        # (word_count_pct) that all beats summed to 100 — now it holds an
        # absolute word count estimate per beat, so the old values are
        # meaningless and are not converted, just renamed away from.
        outline_beat_columns = {row[1] for row in conn.execute("PRAGMA table_info(outline_beats)")}
        if "word_count_pct" in outline_beat_columns and "word_count" not in outline_beat_columns:
            conn.execute("ALTER TABLE outline_beats RENAME COLUMN word_count_pct TO word_count")
        # Each beat is a chapter, so it carries the chapter's title, whose head
        # it's told from, how that voice should sound, and its tone.
        # Re-read after the rename above so both migrations can run in one pass.
        outline_beat_columns = {row[1] for row in conn.execute("PRAGMA table_info(outline_beats)")}
        for column in ("title", "pov_character", "pov_voice_note", "tone"):
            if column not in outline_beat_columns:
                conn.execute(f"ALTER TABLE outline_beats ADD COLUMN {column} TEXT")

        # Which entities (by id, JSON-encoded list) are present in this beat —
        # resolved by init_outline's own entity-presence fields, then mapped
        # from the names the model returns to real DB ids (see router.py's
        # _resolve_beat_entities). Chapter generation uses these to pull only
        # the characters/items/locations/groups/worldbuilding_facts actually
        # in a chapter, instead of sending the whole story bible per call.
        # Old novels (outlines generated before this column existed) simply
        # have NULL/empty lists here and can't generate chapters until their
        # outline is regenerated.
        outline_beat_columns = {row[1] for row in conn.execute("PRAGMA table_info(outline_beats)")}
        for column in (
            "characters_present",
            "items_present",
            "locations_present",
            "groups_present",
            "worldbuilding_facts_present",
        ):
            if column not in outline_beat_columns:
                conn.execute(f"ALTER TABLE outline_beats ADD COLUMN {column} TEXT")

        # The untouched output of init_outline (the rough pass), before
        # init_outline_audit rewrites it into the outline_beats rows above.
        # Written once at generate/regenerate time and never touched again —
        # not by the audit step, not by the outline-beat PATCH route — so the
        # original AI draft survives even after the user edits the real
        # outline. Same column shape as outline_beats, minus sort_order
        # guarantees about matching row-for-row: the audit pass can freely
        # add/remove/reorder beats, so there is no correspondence to preserve
        # between a raw row and any particular outline_beats row.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_outline_beats (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER,
                title TEXT,
                pov_character TEXT,
                pov_voice_note TEXT,
                tone TEXT,
                characters_present TEXT,
                items_present TEXT,
                locations_present TEXT,
                groups_present TEXT,
                worldbuilding_facts_present TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT
            )
            """
        )

        # A group is any set of people treated as a unit — a friend group, a
        # band, a crime family, a megacorp. associated_characters is a
        # JSON-encoded list of character names, like events' columns below.
        # The world's fixed core — exactly one row per novel. Generated first in
        # the pipeline, before characters, so everything later is built to fit a
        # world that already exists. The rich detail lives in worldbuilding_facts
        # below; these four fields are the ones referenced by name downstream.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worldbuilding (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL UNIQUE REFERENCES novels(id) ON DELETE CASCADE,
                story_type TEXT,
                time_period TEXT,
                anchor_location TEXT,
                anchor_location_description TEXT
            )
            """
        )

        # Open-ended world detail, many rows per novel, grouped by category
        # (society | physical | systems | relationships | conflict | history |
        # daily_life | beliefs). sort_order preserves the generated order
        # since sqlite doesn't guarantee row order without it.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worldbuilding_facts (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                category TEXT NOT NULL,
                title TEXT,
                description TEXT
            )
            """
        )

        # Migrate novels whose worldbuilding still lives in the old columns on
        # `novels`. Copies the core across and turns each old `constraints`
        # entry into a `systems` fact. The old columns are left in place — they
        # are simply no longer read; dropping them is a separate cleanup.
        for row in conn.execute(
            """SELECT id, story_type, time_period, anchor_location,
                      anchor_location_description, constraints
               FROM novels
               WHERE id NOT IN (SELECT novel_id FROM worldbuilding)
                 AND (story_type IS NOT NULL OR anchor_location IS NOT NULL)"""
        ).fetchall():
            conn.execute(
                """INSERT INTO worldbuilding
                   (id, novel_id, story_type, time_period, anchor_location,
                    anchor_location_description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), row[0], row[1], row[2], row[3], row[4]),
            )
            for i, constraint in enumerate(json.loads(row[5]) if row[5] else []):
                conn.execute(
                    """INSERT INTO worldbuilding_facts
                       (id, novel_id, sort_order, category, title, description)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (str(uuid.uuid4()), row[0], i, "systems", None, constraint),
                )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                description TEXT,
                associated_characters TEXT
            )
            """
        )
        # Migrate dbs created back when groups were called organizations.
        table_names = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "organizations" in table_names:
            conn.execute(
                """INSERT INTO groups (id, novel_id, name, description, associated_characters)
                   SELECT id, novel_id, name, description, NULL FROM organizations"""
            )
            conn.execute("DROP TABLE organizations")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                characters_involved TEXT,
                groups_involved TEXT
            )
            """
        )
        # Migrate dbs created before groups_involved was renamed.
        event_columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        if "organizations_involved" in event_columns and "groups_involved" not in event_columns:
            conn.execute("ALTER TABLE events RENAME COLUMN organizations_involved TO groups_involved")

        # Only characters and groups can hold a relationship — they're the only
        # entities capable of a disposition toward something. Both tables below
        # share this shape; the subject differs. Subject-outward only: Cal's
        # relationship to Thistle and Thistle's relationship to Cal are separate
        # rows since the relationship can be asymmetric. A row's absence means
        # the relationship doesn't exist yet (e.g. they haven't met) — do not
        # use a null status to represent that, just omit the row. No real FK on
        # target_id since it can point into characters, items, locations,
        # groups, or worldbuilding_facts depending on target_type.
        # Migrate dbs created before target_type/target_id replaced
        # target_character_id (character-only targets, NOT NULL). SQLite can't
        # drop a column's NOT NULL constraint in place, so the old table is
        # rebuilt under the new shape rather than altered.
        char_rel_columns = {row[1] for row in conn.execute("PRAGMA table_info(character_relationships)")}
        if "target_character_id" in char_rel_columns:
            conn.execute("ALTER TABLE character_relationships RENAME TO character_relationships_old")
            conn.execute(
                """
                CREATE TABLE character_relationships (
                    id TEXT PRIMARY KEY,
                    novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                    character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT,
                    status TEXT,
                    emotional_intensity INTEGER,
                    open_threads TEXT
                )
                """
            )
            # target_type/target_id may already hold data from a previous,
            # incomplete migration attempt (ADD COLUMN without dropping the old
            # NOT NULL column) — prefer that over target_character_id when set.
            conn.execute(
                """INSERT INTO character_relationships
                   (id, novel_id, character_id, target_type, target_id, relationship_type,
                    status, emotional_intensity, open_threads)
                   SELECT id, novel_id, character_id,
                          COALESCE(target_type, 'character'),
                          COALESCE(target_id, target_character_id),
                          relationship_type, status, emotional_intensity, open_threads
                   FROM character_relationships_old"""
            )
            conn.execute("DROP TABLE character_relationships_old")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS character_relationships (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT,
                status TEXT,
                emotional_intensity INTEGER,
                open_threads TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_character_relationships_lookup "
                     "ON character_relationships (novel_id, character_id, target_type, target_id)")

        # Group-level relationship — e.g. "the Thieves' Guild is at war with the
        # Crown" as a collective stance, distinct from any one member's personal
        # view. A character's own row in character_relationships always takes
        # priority over their group's row here when both exist for the same
        # target; this table only supplies a default for otherwise-unspecified
        # members.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS group_relationships (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT,
                status TEXT,
                emotional_intensity INTEGER,
                open_threads TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_group_relationships_lookup "
                     "ON group_relationships (novel_id, group_id, target_type, target_id)")

        # Migrate dbs that still have the old character-to-item/location-only
        # table; its rows fold into character_relationships with an explicit
        # target_type, then the table is dropped.
        table_names = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "entity_relationships" in table_names:
            conn.execute(
                """INSERT INTO character_relationships
                   (id, novel_id, character_id, target_type, target_id, relationship_type, status, open_threads)
                   SELECT id, novel_id, character_id, entity_type, entity_id, relationship_type, status, open_threads
                   FROM entity_relationships"""
            )
            conn.execute("DROP TABLE entity_relationships")

        # Lock + per-step model/reasoning columns for the chapter-generation
        # pipeline. locked flips to 1 the moment chapter one is generated —
        # from then on, every table upstream of chapters (novels, characters,
        # worldbuilding*, locations, items, groups, events, outline_beats,
        # secondary_threads) is read-only, since chapters already generated
        # reference specific rows/ids that an upstream edit could invalidate.
        # See router.py's _require_unlocked.
        novel_columns = {row[1] for row in conn.execute("PRAGMA table_info(novels)")}
        if "locked" not in novel_columns:
            conn.execute("ALTER TABLE novels ADD COLUMN locked INTEGER DEFAULT 0")
        if "locked_at" not in novel_columns:
            conn.execute("ALTER TABLE novels ADD COLUMN locked_at TEXT")
        for column in ("generate_model", "edit_model", "state_model"):
            if column not in novel_columns:
                conn.execute(f"ALTER TABLE novels ADD COLUMN {column} TEXT")
        for column in ("generate_reasoning", "edit_reasoning", "state_reasoning"):
            if column not in novel_columns:
                conn.execute(f"ALTER TABLE novels ADD COLUMN {column} INTEGER")
        if "genre_conventions" not in novel_columns:
            conn.execute("ALTER TABLE novels ADD COLUMN genre_conventions TEXT")
        if "genre_conventions_model" not in novel_columns:
            conn.execute("ALTER TABLE novels ADD COLUMN genre_conventions_model TEXT")
        if "genre_conventions_reasoning" not in novel_columns:
            conn.execute("ALTER TABLE novels ADD COLUMN genre_conventions_reasoning INTEGER")

        # Generated chapter prose — one row per outline beat, written once
        # that beat's 3-call pipeline (generate -> edit -> extract state) has
        # run. raw_prose is the first call's output, kept for diffing/debug;
        # edited_prose is the edited version and what the reader actually
        # sees. summary is this chapter's own contribution to the running
        # summary (see chapters.py — the running summary is never stored as
        # its own blob, just the concatenation of every prior chapter's
        # summary, computed at prompt-build time).
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chapters (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                outline_beat_id TEXT NOT NULL UNIQUE REFERENCES outline_beats(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                raw_prose TEXT NOT NULL,
                edited_prose TEXT NOT NULL,
                word_count INTEGER,
                summary TEXT NOT NULL,
                generate_model TEXT,
                generate_reasoning INTEGER,
                edit_model TEXT,
                edit_reasoning INTEGER,
                state_model TEXT,
                state_reasoning INTEGER
            )
            """
        )
        # Migrate existing dbs: prose was renamed to edited_prose to
        # disambiguate it from raw_prose.
        chapters_columns = {row[1] for row in conn.execute("PRAGMA table_info(chapters)")}
        if "prose" in chapters_columns and "edited_prose" not in chapters_columns:
            conn.execute("ALTER TABLE chapters RENAME COLUMN prose TO edited_prose")

        # Per-chapter character state snapshots, append-only. A character's
        # "current state as of chapter N" is the latest row for them with
        # sort_order <= N (see chapters.py's get_character_state-style
        # query) — never UPDATEd, only INSERTed, so regenerating a later
        # chapter can never corrupt what an earlier chapter's generation call
        # actually saw. chapter_id is NULL only for the one seeded baseline
        # row per character (sort_order = -1), written the moment chapter one
        # generates, so chapter one's writing call has *something* prior to
        # read instead of a special-cased empty-state branch.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS character_state (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                chapter_id TEXT REFERENCES chapters(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                physical_state TEXT,
                emotional_state TEXT,
                emotional_intensity INTEGER,
                current_location_id TEXT,
                goals TEXT,
                flaw_active INTEGER,
                flaw_note TEXT,
                knowledge_flags TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_character_state_lookup "
                     "ON character_state (novel_id, character_id, sort_order)")

        # Same append-only, as-of-chapter-N snapshot shape as character_state,
        # for groups instead of individual characters — a group's collective
        # standing/mood/cohesion can shift chapter to chapter independently of
        # any one member's own character_state row.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS group_state (
                id TEXT PRIMARY KEY,
                novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
                group_id TEXT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
                chapter_id TEXT REFERENCES chapters(id) ON DELETE CASCADE,
                sort_order INTEGER NOT NULL,
                status TEXT,
                disposition TEXT,
                cohesion INTEGER,
                open_threads TEXT,
                knowledge_flags TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_group_state_lookup "
                     "ON group_state (novel_id, group_id, sort_order)")

        ensure_season_episode_views(conn)
        conn.commit()
    finally:
        conn.close()


def ensure_season_episode_views(conn: sqlite3.Connection) -> None:
    """Read aliases: seasons→novels, episodes→chapters (Story Bot terminology)."""
    conn.execute("CREATE VIEW IF NOT EXISTS seasons AS SELECT * FROM novels")
    # chapters table may not exist yet on brand-new DB before later creates
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "chapters" in tables:
        conn.execute("CREATE VIEW IF NOT EXISTS episodes AS SELECT * FROM chapters")
