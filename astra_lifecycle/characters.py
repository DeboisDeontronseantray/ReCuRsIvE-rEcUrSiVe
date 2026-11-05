"""Character proposals and consequences, committed only by the aired reducer."""
from copy import deepcopy
from .contracts import PLASTIC, TIERS, digest, require, sha


def validate_card(card):
    require(set(card['locked']) == {'silhouette', 'color', 'signature_prop'}, 'exactly three locked visual keys')
    require(all(isinstance(v, str) and v.strip() for v in card['locked'].values()), 'empty visual key')
    require(set(card['plastic']) == PLASTIC, 'all plastic fields required')
    require(1 <= len(card['refs']) <= 2, 'one or two reference stills required')
    for ref in card['refs']:
        sha(ref['hash'])
        require(ref.get('evidence'), 'reference review evidence required')
    require(card.get('version') == 1, 'baseline card version must be 1')


def brief(card):
    return card['name'] + ': ' + '; '.join(card['locked'].values()) + '.'


def normalize_consequence(raw, index, episode, season, source):
    c = deepcopy(raw)
    complete = all(c.get(k) is not None for k in ('since_index', 'episode', 'season'))
    tier = c.get('tier', 'FLASH') if complete else 'FLASH'
    c.update(tier=tier if tier in TIERS else 'FLASH', since_index=index, episode=episode,
             season=season, source=source, active=True, version=1)
    require(c.get('id') and c.get('text'), 'consequence needs ID and text')
    c['content_hash'] = digest({k: c.get(k) for k in ('text', 'character_id', 'ref')})
    return c


def alive(c, index, episode, season):
    tier = c.get('tier', 'FLASH')
    if not all(k in c for k in ('since_index', 'episode', 'season')) or tier not in TIERS:
        return False
    return {'FLASH': index == c['since_index'], 'SCAR': episode == c['episode'] and season == c['season'],
            'MARK': season == c['season'], 'LEGEND': True}[tier]


def commit(state, clip, index):
    """Runs inside the same transaction as receipt, prompts, event and canon commit."""
    scope = clip['channel']
    prior_versions = {cid: card['version'] for cid, card in state['cards'].items()}
    require(len({p['character_id'] for p in clip['proposals']}) == len(clip['proposals']), 'one proposal per character per clip')
    require(len({r['id'] for r in clip['reuses']}) == len(clip['reuses']), 'one tier advance per consequence per clip')
    clock = state['clocks'].setdefault(scope, {'index': 0, 'episode': clip['episode'], 'season': clip['season'], 'away': 0})
    require((clip['season'], clip['episode']) >= (clock['season'], clock['episode']), 'story clock cannot go backwards')
    for proposal in clip['proposals']:
        card = state['cards'][proposal['character_id']]
        require(card['version'] == proposal['base_version'], 'stale character proposal')
        require(set(proposal['patch']) <= PLASTIC - {'carried_consequences'}, 'locked or managed field update forbidden')
        require(proposal.get('ref') in clip['reference_hashes'], 'proposal still not in current manifest')
        require(proposal.get('attestation') == digest(proposal['patch']), 'still does not attest proposed plastic state')
        require(proposal.get('evidence'), 'plastic persistence needs reviewed still evidence')
        key = card['id'] + ':' + proposal['ref']
        still = state['stills'].get(key)
        require(still is not None and still['state'] in ('accepted', 'primary'), 'state still must be accepted before air')
        if still['state'] == 'accepted':
            require(still['state_digest'] == digest(proposal['patch']), 'reviewed still patch mismatch')
        for old in state['stills'].values():
            if old['character_id'] == card['id'] and old['state'] == 'primary' and old['hash'] != proposal['ref']:
                old.update(state='retired', version=old['version'] + 1)
        if still['state'] != 'primary':
            still.update(state='primary', version=still['version'] + 1)
        card['plastic'].update(deepcopy(proposal['patch']))
        card['refs'] = [{'hash': proposal['ref'], 'evidence': proposal['evidence'], 'state_digest': digest(card['plastic'])}]
        card['version'] += 1
        card['summon_count'] += 1
        card['writein_level'] = min(3, card['writein_level'] + 1)
        card['memory_log'].append({'clip_id': clip['id'], 'index': index, 'patch': deepcopy(proposal['patch'])})
        for k in proposal['patch']:
            card['field_versions']['plastic.' + k] = card['version']
        for k in ('refs', 'summon_count', 'writein_level', 'memory_log'):
            card['field_versions'][k] = card['version']
    for reuse in clip['reuses']:
        c = state['consequences'].get(reuse['id'])
        require(c is not None and c['channel'] == scope and c['active'], 'unknown or expired consequence')
        require(c['content_hash'] == digest({k: c.get(k) for k in ('text', 'character_id', 'ref')}), 'consequence content hash mismatch')
        require(c['source'] != clip['id'] and c['since_index'] < index, 'reuse must be in a later aired clip')
        require(reuse.get('evidence') and c['text'] in reuse['evidence'] and reuse['evidence'] in clip['prompt'], 'reuse needs actual clip or comment evidence for this consequence')
        require(reuse.get('ref') in clip['reference_hashes'], 'reused consequence needs state still')
        tier_index = TIERS.index(c['tier'])
        require(tier_index < 3, 'LEGEND is already maximum tier')
        c.update(tier=TIERS[tier_index + 1], episode=clip['episode'], season=clip['season'], version=c['version'] + 1)
    for c in state['consequences'].values():
        if c['channel'] == scope and c['active']:
            c['active'] = alive(c, index, clip['episode'], clip['season'])
    for raw in clip['consequences']:
        require(raw['id'] not in state['consequences'], 'duplicate consequence ID')
        require(raw.get('tier', 'FLASH') == 'FLASH', 'new consequences start at FLASH; escalation requires later aired reuse')
        require(raw.get('character_id') in clip['spec']['cast'], 'consequence must belong to a present character')
        require(raw.get('ref') in clip['reference_hashes'] and raw.get('evidence'), 'consequence needs attested still')
        c = normalize_consequence(raw, index, clip['episode'], clip['season'], clip['id'])
        c['channel'] = scope
        state['consequences'][c['id']] = c
    for cid, card in state['cards'].items():
        current = [c['id'] for c in state['consequences'].values() if c.get('character_id') == cid and c['active']]
        if current != card['plastic']['carried_consequences']:
            card['plastic']['carried_consequences'] = current
            card['version'] = prior_versions[cid] + 1
            card['field_versions']['plastic.carried_consequences'] = card['version']
        history = state['card_history'][cid]
        if history[-1]['version'] != card['version']:
            history.append(deepcopy(card))
    clock.update(index=index, episode=clip['episode'], season=clip['season'], away=0 if clip['spec']['depth'] == 0 else clock['away'] + 1)
