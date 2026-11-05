"""Receipt-backed canonical air projections; slot snapshots never establish air."""
import contracts

AIRED = "AIRED"
SEGMENT = "segment"
AD_OR_BREAK = {"ad", "commercial", "house_ad", "break", "station_break", "commercial_break", "bumper", "id", "ident",
               "interstitial"}


class PreviousClipNotAired(RuntimeError):
    pass


def build_index(slots, lineage, *, lifecycle=None):
    """Canonical commits alone establish air; slot snapshots are descriptive input."""
    from astra_lifecycle.repo import aired_projection, lifecycle_store
    clip_of = {}
    for row in lineage:
        g, cid = row.get("global_no"), row.get("clip_id")
        if type(g) is int and isinstance(cid, str) and cid:
            if clip_of.setdefault(g, cid) != cid:
                raise contracts.ContractError(f"LINEAGE global_no {g} names two clips")
    verified = aired_projection(lineage, lifecycle)
    life = lifecycle_store(lifecycle, required=False)
    if life is None:
        return {}
    state = life.snapshot()
    globals_by_clip = {cid: g for g, cid in clip_of.items()}
    return {r["clip_id"]: {"slot_id": state["clips"][r["clip_id"]]["slot"], "global_no": globals_by_clip.get(r["clip_id"]),
                            "aired_at": state["receipts"][r["receipt_id"]]["timestamp"]}
            for r in state["commits"] if verified.get(r["clip_id"])}


def not_trait_evidence(slots, lineage):
    """Clip ids that played (or will play) as an ad or break item. They may show cast, but they are never trait
    evidence (trundle, Nov 1 2026). A slot of any kind other than `segment` marks its occupant; so does a LINEAGE
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

def load(slots_path, lineage_path, *, lifecycle=None):
    return build_index(contracts.read_jsonl(slots_path), contracts.read_jsonl(lineage_path), lifecycle=lifecycle)


def require_aired(index, clip_id, *, lifecycle=None):
    from astra_lifecycle.repo import aired_projection
    if not aired_projection([{"clip_id": clip_id}], lifecycle).get(clip_id) or clip_id not in index:
        raise PreviousClipNotAired(f"{clip_id} has not aired (no verified canonical receipt joins it "
                                   f"through LINEAGE); an unaired render is never the previous clip")
    return {"clip_id": clip_id} | index[clip_id]


def canon_memories(cast_meta, index, *, lifecycle=None):
    """Keep only memories whose source clip aired. A memory without a source clip_id counts as unaired."""
    from astra_lifecycle.repo import aired_projection
    verified = aired_projection(cast_meta["memories"], lifecycle)
    kept, dropped = [], []
    for m in cast_meta["memories"]:
        cid = m.get("clip_id")
        if cid in index and verified.get(cid):
            kept.append(m)
        else:
            dropped.append({"clip_id": cid, "since_index": m["since_index"],
                            "reason": "no source clip" if cid is None else "not aired"})
    return cast_meta | {"memories": kept}, dropped
