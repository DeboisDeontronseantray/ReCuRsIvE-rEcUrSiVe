"""Aired status: only clips that have played are canon for the next assembly; unaired renders are ignored.

Contract (playout queue-mutation PLAN section 3.1 = live slot sheet schema v2, written by pickup.py): a slot row with
`status == "AIRED"` and an `aired_at` timestamp means its occupant has played. The occupant joins LINEAGE on
`occupant_global_no == global_no`, and that LINEAGE row's `clip_id` is the clip that aired. Any other case (no slot
row, another status, a missing status or `aired_at`, no LINEAGE join) is not aired. Aired never reverts, so any
slot row that ever said AIRED for an occupant counts, whether the sheet is a snapshot or an add-only log.

Both files are read-only here. Nothing in system-v5-draft writes the flag."""
import datetime

import contracts

AIRED = "AIRED"


class PreviousClipNotAired(RuntimeError):
    pass


def _aired_at(row):
    ts = row.get("aired_at")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def build_index(slots, lineage):
    """clip_id -> {slot_id, global_no, aired_at} for every aired clip. Unaired clips are absent."""
    clip_of = {}
    for row in lineage:
        g, cid = row.get("global_no"), row.get("clip_id")
        if type(g) is int and isinstance(cid, str) and cid:
            if clip_of.setdefault(g, cid) != cid:
                raise contracts.ContractError(f"LINEAGE global_no {g} names two clips: {clip_of[g]!r} and {cid!r}")
    index = {}
    for row in slots:
        g, when = row.get("occupant_global_no"), _aired_at(row)
        if row.get("status") == AIRED and when and type(g) is int and g in clip_of:
            index.setdefault(clip_of[g], {"slot_id": row.get("slot_id"), "global_no": g, "aired_at": when})
    return index


def load(slots_path, lineage_path):
    return build_index(contracts.read_jsonl(slots_path), contracts.read_jsonl(lineage_path))


def require_aired(index, clip_id):
    if clip_id not in index:
        raise PreviousClipNotAired(f"{clip_id} has not aired (no slot row with status AIRED and aired_at joins it "
                                   f"through LINEAGE); an unaired render is never the previous clip")
    return {"clip_id": clip_id} | index[clip_id]


def canon_memories(cast_meta, index):
    """Keep only memories whose source clip aired. A memory without a source clip_id counts as unaired."""
    kept, dropped = [], []
    for m in cast_meta["memories"]:
        cid = m.get("clip_id")
        if cid in index:
            kept.append(m)
        else:
            dropped.append({"clip_id": cid, "since_index": m["since_index"],
                            "reason": "no source clip" if cid is None else "not aired"})
    return cast_meta | {"memories": kept}, dropped
