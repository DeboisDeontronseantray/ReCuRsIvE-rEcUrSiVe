"""Locked meta (read-only from static_v41) and per-spot thread holders, turned into hard constraints.

D6: each spot type has a minimal thread_holder, locked before any mutation.
D7: locked threads enter the prompt only as hard constraints, never as soft suggestions.
D8: FT1-FT4 stay OFF until Trundle turns them on; assembly refuses to run if the live config says otherwise."""
import paths
from adapters.v4_bridge import layers_v4
from contracts import ContractError

HARD_PREFIX = "Must hold: "


class FixedThreadsOn(RuntimeError):
    pass


def check_fixed_threads_off():
    on = [t["id"] for t in layers_v4.fixed_threads()["threads"] if t.get("status") != "PENDING"]
    if on:
        raise FixedThreadsOn(f"fixed threads {on} are not PENDING; how they enter a prompt is not decided yet (D8)")


def thread_holder(spot_type, cfg=None):
    cfg = cfg or paths.config("spots")
    if spot_type not in cfg["spot_types"]:
        raise ContractError(f"unknown spot type {spot_type!r}; add it to config/spots.json")
    th = cfg["spot_types"][spot_type]["thread_holder"]
    if th is not None and (not th.strip() or len(th.split()) > cfg["thread_holder_max_words"] or any(c in th for c in "[]@")):
        raise ContractError(f"thread_holder for {spot_type!r} must be short plain text")
    return th


def hard_constraints(lm, spot_type, cfg=None):
    check_fixed_threads_off()
    items = [t["text"].strip().rstrip(".") for t in lm["threads"] if t["locked"] is True]
    th = thread_holder(spot_type, cfg)
    if th:
        items.append(th.strip().rstrip("."))
    return tuple(items)


def thread_slot(constraints):
    return HARD_PREFIX + "; ".join(constraints) if constraints else None
