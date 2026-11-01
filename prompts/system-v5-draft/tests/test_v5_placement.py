"""Step 7: beat placement and budget."""
import pytest

import paths

CFG = paths.config("assembly")
STILL = "MARLO stands on the top step; cracked glass on the cabinet door"


def _c(n):
    return [{"id": f"c{i}", "text": f"comment {i}"} for i in range(1, n + 1)]


MEM = [{"id": "MARLO_QUILL#0", "text": "MARLO QUILL remembers: lost a button in the stairwell fight"}]


def test_order_still_comments_memory(v5):
    r = v5("placement").place(still=STILL, comments=_c(2), memories=MEM, duration=9)
    assert [b["requester"] for b in r["beats"]] == ["still", "comment", "comment", "memory"]
    assert [s["id"] for s in r["sources"]] == ["still", "c1", "c2", "MARLO_QUILL#0"]


def test_overflow_is_carried_never_dropped(v5):
    r = v5("placement").place(still=STILL, comments=_c(9), memories=MEM, duration=9)
    assert len(r["beats"]) == CFG["max_beats"] == 6
    assert r["placed"] == ["c1", "c2", "c3", "c4"] and r["carried"] == ["c5", "c6", "c7", "c8", "c9"]


def test_max_comments_moves_tail_to_carried(v5):
    r = v5("placement").place(still=None, comments=_c(3), memories=[], duration=9, max_comments=1)
    assert r["placed"] == ["c1"] and r["carried"] == ["c2", "c3"]


def test_times_are_spread_and_preformatted(v5):
    r = v5("placement").place(still=STILL, comments=_c(4), memories=MEM, duration=9)
    assert [b["t"] for b in r["beats"]] == [0.5, 2.0, 3.5, 5.0, 6.5, 8.0]
    assert r["beats"][1]["text"] == "At 2 s, comment 1."
    assert all(b["text"].startswith("At ") for b in r["beats"])


def test_comment_text_is_inserted_verbatim(v5):
    text = "marlo should block with the brass luggage trolley"
    r = v5("placement").place(still=None, comments=[{"id": "c1", "text": text}], memories=[], duration=9)
    assert r["beats"][0]["text"] == f"At 0.5 s, {text}."


def test_deterministic(v5):
    pl = v5("placement").place
    assert pl(still=STILL, comments=_c(7), memories=MEM, duration=9) == pl(still=STILL, comments=_c(7), memories=MEM, duration=9)


def test_fixed_beats_over_budget_rejected(v5):
    with pytest.raises(ValueError):
        v5("placement").place(still=STILL, comments=[], memories=MEM * 6, duration=9)
