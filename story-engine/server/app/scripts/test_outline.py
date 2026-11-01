"""
Generates an outline for a given novel using several models, so their
results can be compared side by side. Reuses the same DB-loading logic as
router.regenerate_outline, but only reads — nothing is written back to the
novel's own outline/chapters.

Usage (run inside the server container, since it needs the sqlite DB and the
provider API keys from the environment):

    python -m app.scripts.test_outline <novel_id>

Edit the MODELS list below to choose which model aliases to compare (see
model_routing.yaml for valid aliases). Each model's outline (and the audit
pass) is written to app/scripts/output/outline_<novel_id>_<model_alias>.txt
"""

import sys
from pathlib import Path

from app.db import get_connection
from app.novels.generation import (
    _post_characters_prompt,
    init_outline,
    init_outline_audit,
)
from app.novels.router import (
    _CHARACTER_COLUMNS,
    _build_outline_input_arcs,
    _character_row_to_dict,
    _worldbuilding_for_prompt,
)

# Model aliases to generate and compare an outline for — see model_routing.yaml.
# Comment out the ones you don't want to run.
MODELS = [
    "claude-fable",
    "claude-opus",
    "claude-sonnet",
    "claude-sonnet-4-6",
    "claude-haiku",
    "qwen-3-7-max",
    "llama3.3",
    "llama4-scout",
    "llama4-maverick",
    "kimi-k3",
    "mistral-medium",
    "mistral-small",
    "grok-4.7",
    "aion-3.5",
    "glm-5.3",
    "muse-glimmer-30b",
    "mimo-v2.6-pro",
]

OUTPUT_DIR = Path(__file__).parent / "output"

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
]


def _load_novel_inputs(conn, novel_id: str) -> dict:
    row = conn.execute(
        f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (novel_id,)
    ).fetchone()
    if row is None:
        raise SystemExit(f"Novel {novel_id} not found")
    novel_row = dict(row)

    secondary_thread_rows = [
        dict(r)
        for r in conn.execute(
            """SELECT id, novel_id, description, length, priority, heat, word_count
               FROM secondary_threads WHERE novel_id = ?""",
            (novel_id,),
        ).fetchall()
    ]
    primary_thread_rows = [
        dict(r)
        for r in conn.execute(
            """SELECT id, novel_id, sort_order, heros_journey_step, summary, word_count_pct,
                      time_gap_before, forbidden_element_active
               FROM spine_beats WHERE novel_id = ? ORDER BY sort_order""",
            (novel_id,),
        ).fetchall()
    ]
    if not primary_thread_rows:
        raise SystemExit(
            f"Novel {novel_id} has no primary thread — it never finished generating far enough "
            "to build an outline from."
        )

    plot_point_rows = [
        dict(r)
        for r in conn.execute(
            """SELECT id, novel_id, secondary_thread_id, sort_order, summary,
                      characters_involved
               FROM secondary_arc_plot_points WHERE novel_id = ?
               ORDER BY secondary_thread_id, sort_order""",
            (novel_id,),
        ).fetchall()
    ]
    character_rows = [
        _character_row_to_dict(r)
        for r in conn.execute(
            f"SELECT {', '.join(_CHARACTER_COLUMNS)} FROM characters WHERE novel_id = ?",
            (novel_id,),
        ).fetchall()
    ]
    entities = {
        "locations": [
            dict(r)
            for r in conn.execute(
                "SELECT name FROM locations WHERE novel_id = ?", (novel_id,)
            ).fetchall()
        ],
        "groups": [
            dict(r)
            for r in conn.execute(
                "SELECT name FROM groups WHERE novel_id = ?", (novel_id,)
            ).fetchall()
        ],
        "items": [
            dict(r)
            for r in conn.execute(
                "SELECT name FROM items WHERE novel_id = ?", (novel_id,)
            ).fetchall()
        ],
    }

    # novels.prompt holds the ORIGINAL intro prompt (raw character notes and
    # full secondary-thread descriptions). The outline step must see the
    # redacted version instead — see _post_characters_prompt's own docstring
    # and router.regenerate_outline, which rebuilds it the same way.
    novel_row["prompt"] = _post_characters_prompt(novel_row, secondary_thread_rows)

    def _fail(detail: str) -> None:
        raise SystemExit(detail)

    outline_input_arcs = _build_outline_input_arcs(secondary_thread_rows, plot_point_rows, _fail)
    worldbuilding = _worldbuilding_for_prompt(conn, novel_id)

    return {
        "novel_row": novel_row,
        "worldbuilding": worldbuilding,
        "primary_thread_rows": primary_thread_rows,
        "outline_input_arcs": outline_input_arcs,
        "character_rows": character_rows,
        "entities": entities,
    }


def _format_outline(outline: list[dict]) -> str:
    lines = []
    for i, beat in enumerate(outline):
        lines.append(f"--- Chapter {i + 1}: {beat.get('title', 'Untitled')} ---")
        lines.append(f"POV: {beat.get('pov_character', '?')}  |  Tone: {beat.get('tone', '?')}  |  "
                     f"Word count: {beat.get('word_count', '?')}")
        if beat.get("pov_voice_note"):
            lines.append(f"Voice note: {beat['pov_voice_note']}")
        lines.append("")
        lines.append(beat.get("content", ""))
        lines.append("")
        lines.append(f"Characters present: {', '.join(beat.get('characters_present') or [])}")
        lines.append(f"Locations present: {', '.join(beat.get('locations_present') or [])}")
        lines.append(f"Items present: {', '.join(beat.get('items_present') or [])}")
        lines.append(f"Groups present: {', '.join(beat.get('groups_present') or [])}")
        lines.append("")
    return "\n".join(lines)


def run_one(inputs: dict, model_alias: str) -> None:
    print(f"[{model_alias}] generating rough outline...", flush=True)
    rough_outline = init_outline(
        inputs["novel_row"],
        inputs["worldbuilding"],
        inputs["primary_thread_rows"],
        inputs["outline_input_arcs"],
        inputs["character_rows"],
        inputs["entities"],
        model=model_alias,
    )

    print(f"[{model_alias}] auditing outline...", flush=True)
    outline = init_outline_audit(
        inputs["novel_row"],
        inputs["worldbuilding"],
        inputs["primary_thread_rows"],
        inputs["outline_input_arcs"],
        inputs["character_rows"],
        inputs["entities"],
        rough_outline,
        model=model_alias,
    )

    novel_id = inputs["novel_row"]["id"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"outline_{novel_id}_{model_alias}.txt"
    out_path.write_text(_format_outline(outline), encoding="utf-8")
    print(f"[{model_alias}] wrote {out_path}", flush=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m app.scripts.test_outline <novel_id>")
    novel_id = sys.argv[1]

    conn = get_connection()
    try:
        inputs = _load_novel_inputs(conn, novel_id)
    finally:
        conn.close()

    for model_alias in MODELS:
        try:
            run_one(inputs, model_alias)
        except Exception as e:
            print(f"[{model_alias}] FAILED: {e}", flush=True)


if __name__ == "__main__":
    main()
