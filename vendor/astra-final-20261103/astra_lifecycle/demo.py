"""Reproducible offline Ch4 lifecycle proof. Existing bytes; no render or live air."""
import json
from pathlib import Path

from . import Lifecycle, GuardError, digest, file_hash
from .adapters import Adapters
from .capture import ReplayIntake
from .contracts import ROOT, output_path
from .fixture import SEEDS, V5, setup, plan, render, approve
from .recipe import route


def run(directory):
    out = output_path(directory)
    out.mkdir(parents=True, exist_ok=True)
    db = out / 'ch4.sqlite'
    # Preserve prior evidence; callers use a new run directory for reruns.
    if db.exists():
        raise GuardError('run directory already contains a database; choose a new output directory')
    life = Lifecycle(db)
    adapter = Adapters(life)
    ref, media = setup(life)
    comments_source = V5 / 'black-ice/BI02/comments.jsonl'
    base_source = V5 / 'black-ice/BI01/base_spec.json'
    fixture_comment = json.loads(comments_source.read_text().splitlines()[0])
    base_spec = json.loads(base_source.read_text())
    sources = [comments_source, base_source, V5 / 'character-meta/04-military-boutique.yaml',
               SEEDS / 'media/SEED-S1_last.png', SEEDS / 'media/SEED-S1_gen1_480p_parody.mp4',
               SEEDS / 'media/SEED-S2_last.png', SEEDS / 'media/lineage.jsonl', SEEDS / 'prompts/SEED-S1.txt']
    provenance = [{'path': str(p), 'sha256': file_hash(p), 'use': 'read-only source; fixture only'} for p in sources]
    # Read only selected identity/status fields; never copy raw authorization or owner paths.
    inventory = []
    for line in (SEEDS / 'media/lineage.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('clip') in ('SEED-S1', 'SEED-S2', 'SEED-S3') and row.get('status') == 'done':
            inventory.append({'logical_id': row['clip'], 'state': 'rendered', 'evidence': 'Ch4 seed lineage done row'})
    life.import_inventory(inventory)
    assert {r['logical_id'] for r in inventory} == {'SEED-S1', 'SEED-S2', 'SEED-S3'}
    # An incomplete prior record must not live forever.
    life.baseline_consequence({'id': 'old-rain', 'text': 'rain-slick coat', 'tier': 'LEGEND', 'character_id': 'HERON'}, channel='Ch4')
    life.version_metadata('ch4-recipe-v1', {'arc': base_spec['arc_stage'], 'style': 'photoreal winter 1971', 'layer_lifetime': 'durable'})
    life.version_metadata('ch4-recipe-v2', {'arc': base_spec['arc_stage'], 'style': 'photoreal winter 1971', 'layer_lifetime': 'durable', 'saga': 'DEAD AIR: The Lost Remote'})
    life.record_idea('keep-canister-open', 'Keep the microfilm-canister callback open until an explicit decision.')
    replay_event = dict(mode='fixture-replay', id='ch4-comment-1', text=fixture_comment['text'],
                        contributor_id='fixture-contributor-1', channel='Ch4', timestamp=fixture_comment['ts'])
    ReplayIntake(life).ingest(replay_event)
    adapter.call('A07', 'filter', prompt_id='ch4-comment-1', allowed=True, reason='offline fixture policy pass')
    adapter.call('A07', 'intake', prompt_id='ch4-comment-unseen', text='keep the microfilm canister moving',
                 contributor_id='fixture-contributor-2', metadata={'handle': '@fixture-two'})
    adapter.call('A07', 'filter', prompt_id='ch4-comment-unseen', allowed=True, reason='offline fixture policy pass')
    # Simulate restart after intake/seen and before wrapping; both remain durable and eligible.
    life = Lifecycle(db)
    adapter = Adapters(life)
    ReplayIntake(life).ingest(replay_event)  # transport retry after restart
    assert len(adapter.call('A07', 'recover', channel='Ch4')) == 2
    selected = route(life.eligible('Ch4'), ['HERON'], duration=5)
    assert selected['placed'][0]['id'] == 'ch4-comment-1'
    assert selected['carried'][0]['id'] == 'ch4-comment-unseen'
    adapter.call('D14', 'carry', prompt_ids=[p['id'] for p in selected['carried']], reason='beat budget full; preserved for next offer')
    patch = {'mood': 'resolute'}
    next_ref = life.add_asset(SEEDS / 'media/SEED-S2_last.png', evidence='existing bytes; synthetic state-still stand-in only')
    life.candidate_still('HERON', next_ref, patch, evidence='synthetic candidate; no visual QC claim')
    life.accept_still('HERON', next_ref, evidence='fixture review only; no visual QC claim')
    plan(life, 'ch4-proof-1', comments=[fixture_comment['text']], extra_refs=[next_ref])
    adapter.call('D13', 'place', clip_id='ch4-proof-1', prompt_ids=['ch4-comment-1'])
    adapter.call('D10', 'propose', clip_id='ch4-proof-1', proposals=[{
        'character_id': 'HERON', 'base_version': 1, 'patch': patch, 'ref': next_ref,
        'attestation': digest(patch), 'evidence': 'synthetic fixture state-still annotation; not a real visual QC claim'}],
        consequences=[{'id': 'handoff-tension', 'text': 'the handoff sharpens HERON’s resolve', 'character_id': 'HERON',
                       'ref': next_ref, 'evidence': 'synthetic fixture annotation', 'tier': 'FLASH'}])
    render(life, 'ch4-proof-1', media)
    life.observe('ch4-proof-1', 'ch4-comment-1', 'HERON follows him across the bridge', score=1,
                 evidence='mock appearance observation; existing seed media does not establish this action')
    c = approve(life, 'ch4-proof-1')
    assert not life.snapshot()['commits'] and life.eligible()
    receipt = life.verifier.issue(c, 'ch4-mock-playback-1')
    adapter.call('D09', 'aired', clip_id=c['id'], receipt=receipt)
    life = Lifecycle(db)
    adapter = Adapters(life)
    adapter.call('D09', 'aired', clip_id=c['id'], receipt=receipt)  # replay is a no-op
    life.swap_alias('ch4-recipe-v1', 'ch4-recipe-v2', reason='audited offline scaffolding revision; no episode boundary rule')
    life.watch_after_air(c['id'], 'seam pop', 'synthetic seam watcher observation', ['overlap_frames'])
    unseen = life.snapshot()['prompts']['ch4-comment-unseen']['original_text']
    plan(life, 'ch4-pulled', comments=[unseen], dependencies=[c['id']])
    adapter.call('D14', 'place', clip_id='ch4-pulled', prompt_ids=['ch4-comment-unseen'])
    adapter.call('D12', 'assemble', clip_id='ch4-pulled')
    plan(life, 'ch4-dependent', dependencies=['ch4-pulled'])
    adapter.call('D12', 'assemble', clip_id='ch4-dependent')
    life.transition('ch4-pulled', 'pulled', evidence={'reason': 'fixture pull after assembly, before playback'})
    try:
        life.dispatch('ch4-dependent')
    except GuardError:
        pass
    else:
        raise AssertionError('dependent was not blocked')
    final = life.snapshot()
    assert len(final['commits']) == 1
    assert final['prompts']['ch4-comment-1']['status'] == 'consumed'
    assert final['prompts']['ch4-comment-unseen']['status'] == 'eligible'
    assert final['consequences']['old-rain']['tier'] == 'FLASH'
    assert final['consequences']['old-rain']['active'] is False
    assert final['consequences']['handoff-tension']['tier'] == 'FLASH'
    assert final['cards']['HERON']['plastic']['mood'] == 'resolute'
    assert final['cards']['HERON']['refs'][0]['hash'] == next_ref
    assert final['stills']['HERON:' + ref]['state'] == 'retired'
    assert final['stills']['HERON:' + next_ref]['state'] == 'primary'
    assert final['clips']['ch4-pulled']['reference_hashes'] == [next_ref]
    assert final['clips']['ch4-dependent']['invalidated_by'] == ['ch4-pulled']
    snapshot = {k: final[k] for k in ('commits', 'clocks', 'cards', 'stills', 'consequences', 'ledger', 'aliases')}
    (out / 'source-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    (out / 'state.json').write_text(json.dumps(final, indent=2) + '\n')
    (out / 'canon-snapshot.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    (out / 'transition-log.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in final['events']))
    (out / 'prompt.txt').write_text(final['clips'][c['id']]['prompt'] + '\n')
    sidecar = dict(version=1, clip_id=c['id'], mode='offline-fixture', media_hash=media,
                   prompt_hash=final['clips'][c['id']]['prompt_hash'], reference_hashes=final['clips'][c['id']]['reference_hashes'],
                   character_versions={'HERON': final['cards']['HERON']['version']},
                   receipt_id=receipt['id'], lineage=c['lineage'], corner_tag=c['spec']['corner_tag'])
    sidecar['field_versions'] = {key: 1 for key in sidecar}
    (out / 'media.sidecar.json').write_text(json.dumps(sidecar, indent=2) + '\n')
    (out / 'media.ffmetadata').write_text(';FFMETADATA1\ncomment=OFFLINE FIXTURE ONLY\nastra_clip_id=' + c['id'] +
                                        '\nastra_media_sha256=' + media + '\nastra_sidecar_sha256=' + file_hash(out / 'media.sidecar.json') + '\n')
    report = [
        '# Ch4 offline lifecycle proof', '',
        'PASS: exactly one canon commit from one verified mock playback receipt; duplicate receipt was a no-op.', '',
        'No render, network call, live air, bot contact, or spend occurred. Existing Ch4 SEED-S1 bytes supplied the mock transport and reference hashes. Comment/action observations and human approvals are synthetic; this is a state-machine proof, not a visual-content proof.', '',
        'Source recipe: BLACK ICE BI01 handoff and BI02 comment fixture. Placeholder reference paths were replaced by an existing Ch4 last frame. The historical SEED-S1 held-frame prompt was not reused as a new production prompt.', '',
        'Intake → filter → assembly → queue → mock dispatch → registered existing media → fixture approval → mock playback → one atomic canon commit.', '',
        'Fixture input is replayed across intake restart; the receipt is replayed across commit restart. SEED-S2 last-frame bytes stand in for a reviewed new state still: acceptance leaves the primary unchanged, air promotes it and retires SEED-S1, and the next queued clip uses the updated reference. This does not establish that either image depicts the proposed state.', '',
        'Every recorded event:', '', '| # | Kind | Subject | Before | After |', '|---|---|---|---|---|']
    for e in final['events']:
        report.append(f"| {e['id']} | {e['kind']} | {e['subject']} | {e['before']} | {e['after']} |")
    report += ['', 'Final state:', '',
               '- ch4-proof-1: aired in the simulator; HERON mood is resolute, summon count 1.',
               '- ch4-comment-1: consumed after mock appearance and playback evidence.',
               '- ch4-comment-unseen: eligible after pull; original text and placement attempt retained.',
               '- ch4-dependent: queued but invalidated; dispatch refused.',
               '- old-rain: incomplete LEGEND input normalized to FLASH and expired on the next aired clip.',
               '- handoff-tension: FLASH, active for the single committed clip.',
               '- SEED-S1, SEED-S2 and SEED-S3: excluded from generation inventory.',
               '- The seam watcher proposed a free ffmpeg Zipper fix; no repair executed.', '',
               'Final canon snapshot:', '', '```json', json.dumps(snapshot, indent=2), '```', '']
    (out / 'CH4-OFFLINE-CYCLE.md').write_text('\n'.join(report))
    return final


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(ROOT / 'reports/ch4-cycle'))
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({'status': 'PASS', 'canon_commits': len(result['commits']), 'mode': result['mode'], 'spend': 0}))
