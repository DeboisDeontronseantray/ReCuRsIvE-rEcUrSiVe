"""Repository wiring; the vendored foundation modules remain byte-for-byte intact.

Supply a Lifecycle explicitly, or point TT_LIFECYCLE_DB at an existing offline
store. No implicit database, fixture approvals, receipt issuance or migration.
"""
import os
from pathlib import Path

from .adapters import Adapters
from .contracts import GuardError, require
from .lifecycle import Lifecycle


def lifecycle_store(lifecycle=None, *, required=True):
    if lifecycle is not None:
        return lifecycle
    path = os.environ.get('TT_LIFECYCLE_DB')
    if path:
        require(Path(path).is_file(), 'TT_LIFECYCLE_DB must name an existing lifecycle store')
        return Lifecycle(path)
    if required:
        raise GuardError('canonical lifecycle store required (TT_LIFECYCLE_DB or lifecycle=)')
    return None


def gateway(lifecycle=None):
    return Adapters(lifecycle_store(lifecycle))


def aired_projection(rows, lifecycle=None):
    life = lifecycle_store(lifecycle, required=False)
    ids = {r['clip_id'] for r in rows if isinstance(r.get('clip_id'), str) and r['clip_id']}
    verified = Adapters(life).derive_aired(rows) if life is not None else {}
    return {cid: verified.get(cid, False) for cid in ids}


def propose_changes(machine, clip_id, *, lifecycle=None, **changes):
    """Supply a complete proposal bundle without erasing other proposal seams."""
    life = lifecycle_store(lifecycle)
    clip = life.snapshot()['clips'].get(clip_id)
    require(clip is not None, 'proposals require an existing planned clip')
    require(set(changes) <= {'proposals', 'consequences', 'reuses'}, 'unknown proposal field')
    payload = {key: changes.get(key) if changes.get(key) is not None else clip[key]
               for key in ('proposals', 'consequences', 'reuses')}
    return Adapters(life).call(machine, 'propose', clip_id=clip_id, **payload)
