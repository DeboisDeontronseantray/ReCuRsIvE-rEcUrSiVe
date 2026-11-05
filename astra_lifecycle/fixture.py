"""Small Ch4 fixture helpers shared by the demo and tests. All media are existing."""
from .contracts import ROOT, digest, now
from .recipe import assemble

SEEDS = ROOT / 'fixtures/ch4-seeds-20261029'
V5 = ROOT / 'prompts/system-v5-draft/fixtures'


def yes(action, subject, identifier, **extra):
    # Synthetic authorization for the offline simulator only, never a real priced yes.
    return dict(actor='trundle', mode='offline-fixture', decision='yes', id=identifier, action=action, subject=subject,
                reason='offline synthetic fixture authorization; no live authority', timestamp=now(), **extra)


def setup(life):
    ref = life.add_asset(SEEDS / 'media/SEED-S1_last.png', evidence='existing Ch4 SEED-S1 last frame; fixture state reference')
    media = life.add_asset(SEEDS / 'media/SEED-S1_gen1_480p_parody.mp4', evidence='existing Ch4 seed media; mock transport only')
    card = dict(id='HERON', name='HERON', version=1,
                locked=dict(silhouette='dark fur greatcoat', color='dark coat', signature_prop='KOLOKOL-7 resonance baton'),
                plastic=dict(health='steady', mood='watchful', gear=['baton'], relationships={}, carried_consequences=[]),
                refs=[{'hash': ref, 'evidence': 'fixture current-state baseline'}], voice='unassigned', abilities=['Systema turn'])
    life.baseline_card(card)
    return ref, media


def spec(**changes):
    return dict(depth=0, big_changes=1, state_so_far='HERON holds the ferry landing.', cast=['HERON'],
                held_still=False, end_mode='free', pin_reason=None, corner_tag='Ch4 / D0', anchors=['ferry landing'],
                episode_complete=True, **changes)


def plan(life, cid='clip-1', *, comments=(), dependencies=(), override=None, episode=1, season=1, price_cents=0, kind='segment', extra_refs=()):
    s = life.snapshot()
    card = s['cards']['HERON']
    refs = list(dict.fromkeys([r['hash'] for r in card['refs']] + list(extra_refs)))
    prompt = assemble(cards=[card], state_so_far='HERON holds the ferry landing.',
        beats=[{'t': 0.5, 'who': 'HERON', 'what': 'turns past WOLFHOUND', 'how': 'using a circular Systema step',
                'with': 'the KOLOKOL-7 resonance baton', 'causes': 'his grip to open'}],
        comments=[dict(original_text=t, t=3.0 + i * 2.5) for i, t in enumerate(comments)])
    cfg = spec()
    cfg.update(override or {})
    return life.plan(cid, logical_id='fixture/' + cid, slot='fixture-slot/' + cid, lineage='Ch4-fixture/' + cid,
                     prompt=prompt, reference_hashes=refs, spec=cfg, dependencies=dependencies, episode=episode,
                     season=season, price_cents=price_cents, kind=kind)


def render(life, cid, media):
    life.transition(cid, 'queued')
    c = life.snapshot()['clips'][cid]
    batch = digest([life._manifest(c)])
    auth = yes('authorize_batch', batch, 'batch/' + cid, ceiling_cents=c['price_cents'])
    life.authorize_batch([cid], auth, c['price_cents'])
    life.reserve_batch(auth['id'])
    life.dispatch(cid)
    return life.transition(cid, 'rendered', evidence={'asset_hash': media})


def approve(life, cid):
    c = life.snapshot()['clips'][cid]
    return life.transition(cid, 'approved', evidence=yes('approve_air', cid, 'air/' + cid,
                            media_hash=c['media_hash'], manifest=c['manifest']))


def air(life, cid):
    c = approve(life, cid)
    receipt = life.verifier.issue(c, 'playback/' + cid)
    life.transition(cid, 'aired', evidence=receipt)
    return receipt
