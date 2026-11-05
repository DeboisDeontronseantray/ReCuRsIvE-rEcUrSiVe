"""Export JSON Schema contracts locally; no remote schema resolution is needed."""
import json
from .contracts import ROOT, STATES, EDGES, TIERS

S = {'type': 'string', 'minLength': 1}
TEXT = {'type': 'string'}
N = {'type': 'integer', 'minimum': 0}
V = {'type': 'integer', 'minimum': 1}
BOOL = {'type': 'boolean'}
HASH = {'type': 'string', 'pattern': '^[0-9a-f]{64}$'}
TIME = {'type': 'string', 'format': 'date-time'}
ANY = {}


def arr(item, **kw):
    return {'type': 'array', 'items': item, **kw}


def obj(properties, required=None, closed=False):
    return {'type': 'object', 'properties': properties,
            'required': list(properties) if required is None else required,
            'additionalProperties': not closed}


def mapping(value):
    return {'type': 'object', 'additionalProperties': value}


def ref(name):
    return {'$ref': '#/$defs/' + name}


def nullable(value):
    return {'anyOf': [value, {'type': 'null'}]}


def definitions():
    d = {}
    d['human'] = obj(dict(id=S, mode={'const': 'offline-fixture'}, actor={'const': 'trundle'}, decision={'const': 'yes'}, action=S,
                          subject=S, timestamp=TIME, reason=S))
    d['receipt'] = obj(dict(id=S, mode={'const': 'offline-fixture'}, authority_id=S, clip_id=S, slot=S, lineage=S,
                            media_hash=HASH, timestamp=TIME, completed={'const': True}, signature=HASH), closed=True)
    d['spec'] = obj(dict(depth={'type': 'integer', 'minimum': 0, 'maximum': 2}, big_changes={'type': 'integer', 'minimum': 0, 'maximum': 1},
                         state_so_far=S, cast=arr(S, minItems=1, uniqueItems=True), held_still={'const': False},
                         end_mode={'enum': ['free', 'pinned']}, pin_reason=nullable(TEXT), corner_tag=S,
                         anchors=arr(S)), required=['depth', 'big_changes', 'state_so_far', 'cast', 'held_still', 'end_mode', 'corner_tag'])
    d['spec']['allOf'] = [{'if': {'properties': {'end_mode': {'const': 'pinned'}}}, 'then': {'properties': {'pin_reason': S}, 'required': ['pin_reason']}}]
    d['proposal'] = obj(dict(character_id=S, base_version=V, patch={'type': 'object', 'properties': {k: ANY for k in ('health', 'mood', 'gear', 'relationships')}, 'additionalProperties': False},
                             ref=HASH, attestation=HASH, evidence=S), closed=True)
    d['reuse'] = obj(dict(id=S, evidence=S, ref=HASH), closed=True)
    d['clip'] = obj(dict(id=S, authority_id=S, version=V, logical_id=S, slot=S, lineage=S, prompt=S, prompt_hash=HASH,
                         reference_hashes=arr(HASH, minItems=1, uniqueItems=True), spec={'type': 'object'},
                         channel=S, episode=V, season=V, kind={'enum': ['segment', 'ad', 'house_ad', 'id']},
                         price_cents=N, route=S, state={'enum': list(STATES)}, prompt_ids=arr(S, uniqueItems=True), filter_versions=mapping(V),
                         dependencies=arr(S, uniqueItems=True), invalidated_by=arr(S), proposals=arr(ref('proposal')),
                         consequences=arr({'type': 'object'}), reuses=arr(ref('reuse')), observations=mapping(ref('observation')),
                         media_hash=nullable(HASH), manifest=nullable(HASH), air_permission=nullable(ref('human'))), closed=True)
    d['clip']['allOf'] = [{'if': {'properties': {'state': {'enum': ['queued', 'rendered', 'approved', 'aired']}}},
                          'then': {'properties': {'spec': ref('spec')}}},
                         {'if': {'properties': {'state': {'enum': ['rendered', 'approved', 'aired']}}},
                          'then': {'properties': {'media_hash': HASH, 'manifest': HASH}}},
                         {'if': {'properties': {'state': {'enum': ['approved', 'aired']}}},
                          'then': {'properties': {'air_permission': ref('human')}}}]
    d['clip']['x-legal-transitions'] = {k: sorted(v) for k, v in EDGES.items()}
    d['attempt'] = obj(dict(clip_id=S, status={'enum': ['placed', 'aired', 'missed', 'pulled', 'failed', 'held', 'rejected']}, merged_into=S, timestamp=TIME), closed=True)
    d['prompt'] = obj(dict(id=S, version=V, original_text=S, contributor_id=S, contributor_metadata={'type': 'object'},
                           channel=S, received_at=TIME, status={'enum': ['eligible', 'held', 'consumed', 'released']},
                           attempts=arr(ref('attempt')), final_outcome=nullable({'type': 'object'}), votes=N,
                           subject_matter=arr(S), skipped=N, filter=obj({'allowed': BOOL, 'reason': S, 'version': V})),
                       required=['id', 'version', 'original_text', 'contributor_id', 'contributor_metadata', 'channel',
                                 'received_at', 'status', 'attempts', 'final_outcome', 'votes', 'subject_matter', 'skipped'], closed=True)
    d['reference'] = obj({'hash': HASH, 'evidence': S, 'state_digest': HASH}, required=['hash', 'evidence'])
    d['still'] = obj(dict(character_id=S, hash=HASH, state={'enum': ['candidate', 'accepted', 'primary', 'retired']},
                         state_digest=HASH, evidence=S, version=V), closed=True)
    d['plastic'] = obj(dict(health=S, mood=S, gear=arr(S), relationships={'type': 'object'}, carried_consequences=arr(S)), closed=True)
    d['card'] = obj(dict(id=S, name=S, version=V, locked=obj(dict(silhouette=S, color=S, signature_prop=S), closed=True),
                         plastic=ref('plastic'), refs=arr(ref('reference'), minItems=1, maxItems=2),
                         voice=S, abilities=arr(S), summon_count=N, writein_level={'type': 'integer', 'minimum': 0, 'maximum': 3},
                         memory_log=arr({'type': 'object'}), field_versions=mapping(V)), closed=True)
    d['consequence'] = obj(dict(id=S, text=S, tier={'enum': list(TIERS)}, since_index=N, episode=V, season=V,
                                source=S, active=BOOL, version=V, channel=S, character_id=S),
                           required=['id', 'text', 'tier', 'since_index', 'episode', 'season', 'source', 'active', 'version', 'channel', 'character_id'])
    d['clock'] = obj(dict(index=N, episode=V, season=V, away={'type': 'integer', 'minimum': 0, 'maximum': 2}), closed=True)
    d['problem'] = obj(dict(id=V, version=V, failure_type=S, clip_id=nullable(S), evidence=ANY, timestamp=TIME,
                          fix_id=nullable(S), status={'enum': ['open', 'resolved']}, resolution=nullable({'type': 'object'})), closed=True)
    d['fix'] = obj(dict(id=S, version=V, problem_solved=arr(S, minItems=1), conditions=arr(S),
                        cost_class={'enum': ['free ffmpeg', 'still', 'full regen']}, conflicts=arr(S)), closed=True)
    d['observation'] = obj(dict(appeared_text=TEXT, score={'type': 'number', 'minimum': 0, 'maximum': 1}, evidence=S,
                              mode={'const': 'offline-fixture'}, media_hash=HASH, prompt_hash=HASH), closed=True)
    d['ledger'] = obj(dict(prompt_id=S, contributor_id=S, requested_text=S, appeared_text=TEXT, clip_id=S,
                           aired=BOOL, receipt_id=nullable(S), aired_at=nullable(TIME), score={'type': 'number', 'minimum': 0, 'maximum': 1},
                           channel=S, votes=N, subject_matter=arr(S), version=V, requested_hash=HASH,
                           observation_evidence=nullable(S), landed=BOOL, delivery_status={'enum': ['pending', 'appeared', 'missed']}), closed=True)
    d['metadata'] = obj(dict(id=S, version=V, kind={'enum': ['layer', 'metadata', 'term']},
                           role={'enum': ['scaffolding', 'continuous_thread']}, executable_rule={'const': False},
                           fields={'type': 'object'}, field_versions=mapping(V)), closed=True)
    d['approval'] = obj(dict(id=S, batch_digest=HASH, manifests=arr({'type': 'object'}, minItems=1), ceiling_cents=N,
                             authorization=ref('human'), version=V), closed=True)
    d['reservation'] = obj(dict(approval_id=S, manifest_digest=HASH, price_cents=N, state={'enum': ['reserved', 'mock_dispatched']}), closed=True)
    d['swap'] = obj(dict(old=S, new=S, proof={'anyOf': [S, arr(S, minItems=2, maxItems=2)]}, reason=S, crossover_test=BOOL, version=V), closed=True)
    d['event'] = obj(dict(id=V, kind=S, subject=S, before=ANY, after=ANY, timestamp=TIME, evidence=ANY), closed=True)
    d['commit'] = obj(dict(id=V, clip_id=S, receipt_id=S, index=V, channel=S), closed=True)
    d['asset'] = obj(dict(path=S, hash=HASH, evidence=S, version=V), closed=True)
    d['inventory'] = obj(dict(logical_id=S, state={'enum': ['rendered', 'approved', 'aired']}, evidence=S), closed=True)
    d['fix_queue'] = obj(dict(problem_id=V, fix_id=S, status={'enum': ['proposed', 'resolved']}), closed=True)
    d['idea'] = obj(dict(id=S, text=S, status={'enum': ['open', 'closed']}, version=V, authorization=ref('human')),
                    required=['id', 'text', 'status', 'version'], closed=True)
    d['snapshot'] = obj(dict(version={'const': 1}, authority_id=S, mode={'const': 'offline-fixture'}, clips=mapping(ref('clip')),
                             prompts=mapping(ref('prompt')), cards=mapping(ref('card')), card_history=mapping(arr(ref('card'))), stills=mapping(ref('still')),
                             consequences=mapping(ref('consequence')), clocks=mapping(ref('clock')), commits=arr(ref('commit')),
                             events=arr(ref('event')), receipts=mapping(ref('receipt')), slots=mapping(S), problems=arr(ref('problem')),
                             fix_library=arr(ref('fix')), fix_queue=arr(ref('fix_queue')), assets=mapping(ref('asset')),
                             inventory=mapping(ref('inventory')), approvals=mapping(ref('approval')), reservations=mapping(ref('reservation')),
                             releases=mapping(ref('human')), metadata=mapping(arr(ref('metadata'))), aliases=mapping(S), swaps=arr(ref('swap')),
                             ledger=arr(ref('ledger')), open_ideas=mapping(ref('idea')), channel_batches=mapping({'type': 'object'}), budget_cents=N), closed=True)
    return d


def schema(kind='snapshot'):
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': 'Astra offline ' + kind,
            '$defs': definitions(), '$ref': '#/$defs/' + kind}


def export():
    for kind, name in (('snapshot', 'records.schema.json'), ('clip', 'lifecycle.schema.json'), ('receipt', 'playback-receipt.schema.json')):
        (ROOT / 'schemas' / name).write_text(json.dumps(schema(kind), indent=2) + '\n')


if __name__ == '__main__':
    export()
