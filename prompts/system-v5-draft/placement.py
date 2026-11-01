"""Beat placement for the next clip. Inputs are inserted as given (D4: no semantic parsing); nothing here writes prose.

Order: still continuity first, then comments in timestamp order, then memory beats (already capped by write-in level).
Comments that do not fit the beat budget are carried to the next clip, never dropped."""
import paths


def beat_times(n, duration, cfg):
    start, end = cfg["beat_start_s"], duration - cfg["beat_end_margin_s"]
    if n <= 1:
        return [start] * n
    return [round(start + i * (end - start) / (n - 1), 1) for i in range(n)]


def place(*, still, comments, memories, duration, cfg=None, max_comments=None):
    """still: str or None. comments/memories: lists of {"id", "text"}. Returns beats plus placed/carried comment ids."""
    cfg = cfg or paths.config("assembly")
    fixed = (1 if still else 0) + len(memories)
    if fixed > cfg["max_beats"]:
        raise ValueError(f"still + memory beats ({fixed}) exceed max_beats {cfg['max_beats']}")
    room = cfg["max_beats"] - fixed
    if max_comments is not None:
        room = min(room, max_comments)
    placed, carried = comments[:room], comments[room:]
    items = ([("still", "still", still)] if still else []) + [("comment", c["id"], c["text"]) for c in placed] \
        + [("memory", m["id"], m["text"]) for m in memories]
    beats, sources = [], []
    for t, (kind, sid, text) in zip(beat_times(len(items), duration, cfg), items):
        beats.append({"t": t, "text": f"At {t:g} s, {text.strip().rstrip('.')}.", "requester": kind})
        sources.append({"t": t, "requester": kind, "id": sid})
    return {"beats": beats, "sources": sources, "placed": [c["id"] for c in placed], "carried": [c["id"] for c in carried]}
