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
SEGMENT = "segment"
AD_OR_BREAK = {"ad", "commercial", "house_ad", "break", "station_break", "commercial_break", "bumper", "id", "ident",
               "interstitial"}


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


def not_trait_evidence(slots, lineage):
    """Clip ids that played (or will play) as an ad or break item. They may show cast, but they are never trait
    evidence (Trundle, Nov 1 2026). A slot of any kind other than `segment` marks its occupant; so does a LINEAGE
    row whose `kind` or `spot_type` is an ad or break kind."""
    clip_of = {r["global_no"]: r["clip_id"] for r in lineage
               if type(r.get("global_no")) is int and isinstance(r.get("clip_id"), str)}
    out = {r["clip_id"] for r in lineage if isinstance(r.get("clip_id"), str)
           and AD_OR_BREAK & {str(r.get("kind", "")).lower(), str(r.get("spot_type", "")).lower()}}
    for row in slots:
        kind = row.get("kind")
        if isinstance(kind, str) and kind.lower() != SEGMENT and row.get("occupant_global_no") in clip_of:
            out.add(clip_of[row["occupant_global_no"]])
    return out

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
