"""
Generates the first chapter's prose for a given novel using several models,
so their results can be compared side by side. Read-only against the
database — same DB-loading logic as router._run_chapter_pipeline, but never
writes anything back (no baseline character_state/group_state rows are
seeded; a novel with no state rows yet just gets chapters.py's own built-in
fallback text, e.g. "Unremarkable; nothing notable to report.", the same as
any character/group with no state row for another reason).

Requires the novel to already have a persisted, resolved outline (i.e.
regenerate_outline has run at least once) — chapter 1 is outline_beats'
sort_order=0 row, read as-is.

Usage (run inside the server container, since it needs the sqlite DB and the
provider API keys from the environment):

    python -m app.scripts.test_prose <novel_id>

Edit the MODELS list below to choose which model aliases to compare (see
model_routing.yaml for valid aliases). Each model's chapter-one prose is
written to app/scripts/output/prose_<novel_id>_<model_alias>.txt
"""

import sys
from pathlib import Path

from app.db import get_connection
from app.novels.chapters import generate_chapter_prose
from app.novels.router import (
    _OUTLINE_BEAT_COLUMNS,
    _present_entities_for_beat,
    _running_summary,
)
from app.scripts.test_outline import _NOVEL_COLUMNS

# Model aliases to generate and compare chapter-one prose for — see model_routing.yaml.
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


def _load_chapter_one_inputs(conn, novel_id: str) -> dict:
    novel_row = dict(
        conn.execute(
            f"SELECT {', '.join(_NOVEL_COLUMNS)} FROM novels WHERE id = ?", (novel_id,)
        ).fetchone()
        or {}
    )
    if not novel_row:
        raise SystemExit(f"Novel {novel_id} not found")

    beat_row = conn.execute(
        f"SELECT {', '.join(_OUTLINE_BEAT_COLUMNS)} FROM outline_beats "
        "WHERE novel_id = ? ORDER BY sort_order LIMIT 1",
        (novel_id,),
    ).fetchone()
    if beat_row is None:
        raise SystemExit(
            f"Novel {novel_id} has no outline beats — generate/regenerate the outline first "
            "(see app.scripts.test_outline)."
        )
    # Kept as raw JSON strings here — _present_entities_for_beat (below) does
    # its own json.loads on these columns, same as router._run_chapter_pipeline
    # passes beat_row through untouched.
    beat = dict(beat_row)

    if not (beat["characters_present"] or beat["locations_present"]):
        raise SystemExit(
            f"Novel {novel_id}'s first outline beat has no resolved entity-presence data — "
            "regenerate the outline before generating prose."
        )

    present = _present_entities_for_beat(conn, novel_id, beat)
    running_summary = _running_summary(conn, novel_id, beat["sort_order"])

    return {
        "novel_row": novel_row,
        "beat": beat,
        "running_summary": running_summary,
        **present,
    }


def run_one(inputs: dict, model_alias: str) -> None:
    print(f"[{model_alias}] generating chapter one prose...", flush=True)
    prose = generate_chapter_prose(
        inputs["novel_row"],
        inputs["beat"],
        inputs["running_summary"],
        inputs["present_characters"],
        inputs["present_items"],
        inputs["present_locations"],
        inputs["present_groups"],
        inputs["present_worldbuilding_facts"],
        model=model_alias,
    )

    novel_id = inputs["novel_row"]["id"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"prose_{novel_id}_{model_alias}.txt"
    header = f"{inputs['beat'].get('title', 'Untitled')}\n{'=' * 40}\n\n"
    out_path.write_text(header + prose, encoding="utf-8")
    print(f"[{model_alias}] wrote {out_path}", flush=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m app.scripts.test_prose <novel_id>")
    novel_id = sys.argv[1]

    conn = get_connection()
    try:
        inputs = _load_chapter_one_inputs(conn, novel_id)
    finally:
        conn.close()

    for model_alias in MODELS:
        try:
            run_one(inputs, model_alias)
        except Exception as e:
            print(f"[{model_alias}] FAILED: {e}", flush=True)


if __name__ == "__main__":
    main()
