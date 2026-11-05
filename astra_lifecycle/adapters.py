"""Transition-facing replacements for legacy machine call sites.

All authority lives in Lifecycle. A caller cannot request an old setter through
this gateway. Existing pure scoring/formatting can be used via legacy.read_pure.
"""
from .contracts import GuardError, require

MACHINES = {
    'D09': ('aired',), 'D13': ('place',), 'D14': ('place', 'eligible', 'carry'),
    'D15': ('propose',), 'D10': ('propose',), 'D16': ('propose',), 'D17': ('propose',),
    'B01': ('approve', 'preempt', 'head'), 'B04': ('release', 'eligible'),
    'D08': ('local_export', 'episodes_done'), 'A07': ('intake', 'recover', 'filter'),
    'D12': ('assemble',), 'B15': ('eligible',),
    'inventory': ('excluded',), 'render': ('reserve', 'dispatch', 'rendered'),
}


class Adapters:
    def __init__(self, lifecycle):
        self.lifecycle = lifecycle

    def call(self, machine, action, **payload):
        require(action in MACHINES.get(machine, ()), 'legacy transition bypass rejected: ' + machine + '/' + action)
        life = self.lifecycle
        if action == 'aired':
            return life.transition(payload['clip_id'], 'aired', evidence=payload.get('receipt'))
        if action in ('place',):
            return life.place(**payload)
        if action == 'carry':
            return life.carry(**payload)
        if action == 'propose':
            return life.propose(**payload)
        if action == 'approve':
            return life.transition(payload['clip_id'], 'approved', evidence=payload.get('authorization'))
        if action == 'preempt':
            return life.preempt(**payload)
        if action == 'head':
            return life.settled_head(**payload)
        if action == 'release':
            return life.release_prompt(**payload)
        if action == 'eligible':
            return life.eligible(**payload)
        if action == 'local_export':
            # Existing export work may supply a registered asset; it never advances continuity.
            return {'asset_hash': life.add_asset(payload['path'], evidence='D08 offline local export'), 'aired': False}
        if action == 'episodes_done':
            s = life.snapshot()
            return len({(s['clips'][r['clip_id']]['season'], s['clips'][r['clip_id']]['episode'])
                        for r in s['commits'] if r['channel'] == payload['channel']
                        and s['clips'][r['clip_id']]['spec'].get('episode_complete')})
        if action == 'intake':
            return life.intake(**payload)
        if action == 'filter':
            return life.filter_prompt(**payload)
        if action == 'recover':
            # No ephemeral seen flag can exclude durable eligible work.
            return life.eligible(payload.get('channel'))
        if action == 'assemble':
            # Assembly must be complete before this gate. A failed queue gate leaves it planned.
            return life.transition(payload['clip_id'], 'queued')
        if action == 'excluded':
            return life.inventory_excluded(**payload)
        if action == 'reserve':
            return life.reserve_batch(**payload)
        if action == 'dispatch':
            return life.dispatch(**payload)
        if action == 'rendered':
            return life.transition(payload['clip_id'], 'rendered', evidence=payload.get('evidence'))
        raise GuardError('unimplemented adapter action')

    def derive_aired(self, rows):
        """Legacy booleans are ignored, even if they say air_yes or AIRED."""
        s = self.lifecycle.snapshot()
        return {r['clip_id']: s['clips'][r['clip_id']]['state'] == 'aired'
                for r in rows if r.get('clip_id') in s['clips']}
