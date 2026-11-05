"""Batch 1 integration guards. All receipts and bytes are offline fixtures."""
import ast
import importlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from astra_lifecycle import GuardError, digest
from astra_lifecycle.adapters import Adapters
from astra_lifecycle.fixture import plan, render, approve, yes
from astra_lifecycle.integration import audit_source
from astra_lifecycle.legacy import read_pure
from astra_lifecycle.repo import aired_projection, lifecycle_store
from lineage.air_status import source_indicates_aired
from lineage.aired import build_aired_index, clip_id_aired
from lineage.derive_aired import (
    append_aired_derivation_for_clip, derive_aired_append_patches,
    derive_aired_enriched_copy,
)
from tests.lifecycle_support import authority

REPO = Path(__file__).resolve().parents[1]
FOUNDATION = REPO / 'vendor/astra-final-20261103/astra_lifecycle'
CALLERS = [
    'lineage/air_status.py', 'lineage/aired.py', 'lineage/derive_aired.py',
    'charmeta/promote.py', 'prompts/system-v4-20261030/tools/layers_v4.py',
    *[f'prompts/system-v5-draft/{name}.py' for name in ('aired', 'assemble_next', 'intake', 'memory', 'placement')],
]


@pytest.fixture
def life():
    with authority() as (store, ref, media):
        yield store, ref, media


@pytest.fixture
def v5_modules():
    # Independent of sibling conftest collection or the compiler test double.
    for path in ('prompts/system-v5-draft', 'prompts/system-v4-20261030/tools', 'story-engine/engine'):
        value = str(REPO / path)
        if value not in sys.path:
            sys.path.insert(0, value)
    return {n: importlib.import_module('prompts.system-v5-draft.intake' if n == 'intake' else n) for n in ('aired', 'assemble_next', 'intake', 'memory', 'placement', 'layers_v4')}


def spy_calls():
    original = Adapters.call
    calls = []
    def call(self, machine, action, **payload):
        calls.append((machine, action, payload))
        return original(self, machine, action, **payload)
    return calls, patch.object(Adapters, 'call', call)


def ready(life, media, cid='clip-1'):
    plan(life, cid)
    render(life, cid, media)  # mock transport of existing bytes, no renderer
    return approve(life, cid)


def test_foundation_is_vendored_verbatim():
    sources = list(FOUNDATION.glob('*.py'))
    assert sources
    for source in sources:
        assert (REPO / 'astra_lifecycle' / source.name).read_bytes() == source.read_bytes(), source.name


@pytest.mark.parametrize('source', [
    'from checker import approve as old_approve\nold_approve(x)',
    'from lineage.air_status import source_indicates_aired as old\nold(row)',
    'import intake as old\nold.mark_consumed(path, keys, clip_id=c)',
    'from layers_v4 import tier_alive',
    'import memory as old\ngetattr(old, "summon")(state)',
    'from pickup import clip_airing',
    'import comment_prompts as old\nold.set_status(x, "AIRED")',
])
def test_legacy_imports_aliases_and_reflected_setters_fail_audit(source):
    assert audit_source(source)


@pytest.mark.parametrize('name', ['approve', 'mark_consumed', 'set_state', 'summon', 'source_indicates_aired'])
def test_legacy_extractor_refuses_transition_symbols(name):
    with pytest.raises(GuardError, match='forbidden'):
        read_pure(name)


@pytest.mark.parametrize('relative', CALLERS)
def test_production_callers_do_not_call_transition_authority_directly(relative):
    tree = ast.parse((REPO / relative).read_text())
    forbidden = {'transition', 'legacy_prompt_state', '_run', '_connect', 'set_state', 'set_status', 'mark_consumed'}
    legacy_modules = {'checker', 'pickup', 'comment_prompts', 'clip_render', 'pipeline'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden, (relative, node.lineno)
            if node.func.attr == 'update':
                assert not any(k.arg == 'state' for k in node.keywords), (relative, node.lineno)
        if isinstance(node, ast.ImportFrom):
            assert not set((node.module or '').split('.')) & legacy_modules, (relative, node.lineno)
        if isinstance(node, ast.Import):
            assert not any(set(n.name.split('.')) & legacy_modules for n in node.names), (relative, node.lineno)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    assert target.slice.value != 'state', (relative, node.lineno)
                if isinstance(target, ast.Attribute):
                    assert target.attr != 'state', (relative, node.lineno)
    # All persistence is delegated; detached snapshots may be freely inspected.
    assert not any(isinstance(n, ast.ImportFrom) and n.module == 'astra_lifecycle.fixture' for n in ast.walk(tree))


@pytest.mark.parametrize('row', [
    {'aired': True}, {'air_yes': True}, {'status': 'AIRED'},
    {'playout_status': 'AIRED'}, {'queue_state': 'aired'},
])
def test_legacy_air_latches_cannot_establish_air(row, life, v5_modules):
    store, _, _ = life
    plan(store)
    row = {'clip_id': 'clip-1', 'global_no': 1} | row
    assert not clip_id_aired(row, lifecycle=store)
    assert not source_indicates_aired(row, lifecycle=store)
    assert build_aired_index([row], lifecycle=store) == {'clip-1': False}
    assert v5_modules['aired'].build_index(
        [{'status': 'AIRED', 'aired_at': '2026-11-04T12:00:00Z', 'occupant_global_no': 1}],
        [row], lifecycle=store) == {}
    assert store.snapshot()['clips']['clip-1']['state'] == 'planned'


@pytest.mark.parametrize('receipt', [None, True, {'verified': True}, {'air_yes': True}])
def test_approved_clip_still_needs_a_verified_receipt(life, receipt):
    store, _, media = life
    ready(store, media)
    with pytest.raises(GuardError):
        Adapters(store).call('D09', 'aired', clip_id='clip-1', receipt=receipt)
    assert store.snapshot()['clips']['clip-1']['state'] == 'approved'
    assert store.snapshot()['commits'] == []


def test_wrong_signature_and_foreign_receipt_are_rejected(life):
    store, _, media = life
    clip = ready(store, media)
    receipt = store.verifier.issue(clip, 'test-receipt')
    receipt['signature'] = '0' * 64
    with pytest.raises(GuardError):
        Adapters(store).call('D09', 'aired', clip_id=clip['id'], receipt=receipt)
    with authority() as (other, _, other_media):
        foreign = ready(other, other_media)
        with pytest.raises(GuardError, match='authority'):
            Adapters(store).call('D09', 'aired', clip_id=clip['id'], receipt=other.verifier.issue(foreign, 'foreign'))
    assert store.snapshot()['clips'][clip['id']]['state'] == 'approved'


@pytest.mark.parametrize('state,target,machine,action', [
    ('planned', 'aired', 'D09', 'aired'),
    ('planned', 'approved', 'B01', 'approve'),
    ('queued', 'approved', 'B01', 'approve'),
    ('planned', 'rendered', 'render', 'rendered'),
])
def test_illegal_jumps_are_rejected(life, state, target, machine, action):
    store, _, media = life
    clip = plan(store)
    if state == 'queued':
        Adapters(store).call('D12', 'assemble', clip_id=clip['id'])
    payload = {'clip_id': clip['id']}
    if target == 'aired':
        # A correctly signed receipt cannot skip the state graph either.
        simulated = dict(store.snapshot()['clips'][clip['id']], state='approved', media_hash=media)
        payload['receipt'] = store.verifier.issue(simulated, 'jump')
    with pytest.raises(GuardError, match='illegal transition'):
        Adapters(store).call(machine, action, **payload)
    assert store.snapshot()['clips'][clip['id']]['state'] == state


def test_all_normal_transitions_use_gateway_and_receipt_projection(life):
    store, _, media = life
    adapter = Adapters(store)
    c = plan(store)
    adapter.call('D12', 'assemble', clip_id=c['id'])
    c = store.snapshot()['clips'][c['id']]
    batch = digest([store._manifest(c)])
    auth = yes('authorize_batch', batch, 'offline-batch', ceiling_cents=0)
    store.authorize_batch([c['id']], auth, 0)
    adapter.call('render', 'reserve', approval_id=auth['id'])
    adapter.call('render', 'dispatch', clip_id=c['id'])
    adapter.call('render', 'rendered', clip_id=c['id'], evidence={'asset_hash': media})
    c = store.snapshot()['clips'][c['id']]
    adapter.call('B01', 'approve', clip_id=c['id'], authorization=yes(
        'approve_air', c['id'], 'offline-air-permission', media_hash=media, manifest=c['manifest']))
    c = store.snapshot()['clips'][c['id']]
    receipt = store.verifier.issue(c, 'offline-completion')
    adapter.call('D09', 'aired', clip_id=c['id'], receipt=receipt)
    assert aired_projection([{'clip_id': c['id'], 'aired': False}], store) == {c['id']: True}
    assert len(store.snapshot()['commits']) == 1


def test_derivation_callers_project_canon_and_reverify_receipts(life, tmp_path):
    store, _, media = life
    clip = ready(store, media)
    row = {'clip_id': clip['id'], 'air_yes': True}
    output = tmp_path / 'patches.jsonl'
    with pytest.raises(GuardError):
        append_aired_derivation_for_clip(output, row, lifecycle=store, receipt={'verified': True})
    assert not output.exists()
    with pytest.raises(GuardError, match='verified canonical receipt'):
        append_aired_derivation_for_clip(output, row, lifecycle=store)
    receipt = store.verifier.issue(clip, 'projection')
    calls, spy = spy_calls()
    with spy:
        report = append_aired_derivation_for_clip(output, row, lifecycle=store, receipt=receipt)
    assert calls[0][:2] == ('D09', 'aired')
    assert report.appended == [clip['id']]
    before = output.read_bytes()
    append_aired_derivation_for_clip(output, row, lifecycle=store, receipt=receipt)
    assert output.read_bytes() == before
    source = tmp_path / 'source.jsonl'
    source.write_text(json.dumps(row) + '\n' + json.dumps({'clip_id': 'unknown', 'aired': True}) + '\n')
    exported = tmp_path / 'exported.jsonl'
    derive_aired_enriched_copy(input_path=source, output_path=exported, apply=True, lifecycle=store)
    assert [r['aired'] for r in map(json.loads, exported.read_text().splitlines())] == [True, False]
    assert derive_aired_append_patches(input_path=source, output_path=output, apply=True, lifecycle=store).appended == []


def test_comment_setter_raises_and_placement_does_not_consume(life, tmp_path, v5_modules):
    store, _, _ = life
    intake, placement = v5_modules['intake'], v5_modules['placement']
    plan(store, comments=['turn the brass key', 'mind the landing'])
    for pid, text in [('p1', 'turn the brass key'), ('p2', 'mind the landing')]:
        Adapters(store).call('A07', 'intake', prompt_id=pid, text=text, contributor_id='permanent/' + pid)
        Adapters(store).call('A07', 'filter', prompt_id=pid, allowed=True, reason='offline fixture')
    ledger = tmp_path / 'consumed.jsonl'
    with pytest.raises(GuardError, match='direct consumption'):
        intake.mark_consumed(ledger, ['p1'], clip_id='clip-1', lifecycle=store)
    assert not ledger.exists()
    calls, spy = spy_calls()
    with spy:
        intake.place_comments(['p1'], clip_id='clip-1', lifecycle=store)
        placement.place(still=None, comments=[{'id': 'c1', 'key': 'p1', 'text': 'turn the brass key'},
                                             {'id': 'c2', 'key': 'p2', 'text': 'mind the landing'}],
                        memories=[], duration=8, max_comments=1, lifecycle=store, clip_id='clip-1')
    assert [(m, a) for m, a, _ in calls] == [('D13', 'place'), ('D14', 'place'), ('D14', 'carry')]
    assert all(p['status'] == 'eligible' for p in store.snapshot()['prompts'].values())
    assert intake.load_consumed(ledger, clip_id='next', lifecycle=store) == set()


def test_only_observed_comment_is_consumed_after_receipt(life, tmp_path, v5_modules):
    store, _, media = life
    plan(store, comments=['turn the brass key'])
    adapter = Adapters(store)
    adapter.call('A07', 'intake', prompt_id='key', text='turn the brass key', contributor_id='permanent-message')
    adapter.call('A07', 'filter', prompt_id='key', allowed=True, reason='offline fixture')
    v5_modules['intake'].place_comments(['key'], clip_id='clip-1', lifecycle=store)
    render(store, 'clip-1', media)
    store.observe('clip-1', 'key', 'turn the brass key', score=1, evidence='offline fixture appearance')
    clip = approve(store, 'clip-1')
    assert v5_modules['intake'].load_consumed(None, clip_id='next', lifecycle=store) == set()
    adapter.call('D09', 'aired', clip_id='clip-1', receipt=store.verifier.issue(clip, 'comment-playback'))
    assert v5_modules['intake'].load_consumed(None, clip_id='next', lifecycle=store) == {'key'}


def test_memory_and_layer_proposals_route_without_advancing_counters(life, v5_modules):
    store, ref, media = life
    plan(store)
    memory, layers = v5_modules['memory'], v5_modules['layers_v4']
    before = store.snapshot()['cards']['HERON']
    patch_data = {'mood': 'resolute'}
    proposals = [{'character_id': 'HERON', 'base_version': 1, 'patch': patch_data,
                  'ref': ref, 'attestation': digest(patch_data), 'evidence': 'existing fixture still'}]
    calls, spy = spy_calls()
    with spy:
        memory.summon({}, clip_id='clip-1', lifecycle=store, proposals=proposals)
        memory.proposed_update({}, [], clip_id='clip-1', lifecycle=store, proposals=proposals)
        layers.propose_consequences('clip-1', lifecycle=store, proposals=proposals)
        layers.propose_still('clip-1', lifecycle=store, proposals=proposals)
    assert [(m, a) for m, a, _ in calls] == [('D15', 'propose'), ('D15', 'propose'), ('D16', 'propose'), ('D17', 'propose')]
    assert store.snapshot()['cards']['HERON'] == before
    for old in [lambda: memory.summon(before), lambda: memory.proposed_update({}, [])]:
        with pytest.raises(GuardError):
            old()


def test_v5_aired_readers_use_canonical_commits(life, v5_modules):
    store, _, media = life
    clip = ready(store, media)
    Adapters(store).call('D09', 'aired', clip_id=clip['id'], receipt=store.verifier.issue(clip, 'v5-projection'))
    rows = [{'clip_id': clip['id'], 'global_no': 7}]
    aired = v5_modules['aired']
    with patch.object(Adapters, 'derive_aired', autospec=True, wraps=None, return_value={clip['id']: True}) as spy:
        index = aired.build_index([], rows, lifecycle=store)
    assert spy.called
    assert aired.require_aired(index, clip['id'], lifecycle=store)['global_no'] == 7
    with pytest.raises(aired.PreviousClipNotAired):
        aired.require_aired({'forged': {'aired': True}}, 'forged', lifecycle=store)


def test_missing_store_is_not_implicitly_created(monkeypatch, tmp_path):
    monkeypatch.delenv('TT_LIFECYCLE_DB', raising=False)
    with pytest.raises(GuardError, match='canonical lifecycle store required'):
        lifecycle_store()
    assert not clip_id_aired({'clip_id': 'x', 'aired': True})
    path = tmp_path / 'missing.sqlite'
    monkeypatch.setenv('TT_LIFECYCLE_DB', str(path))
    with pytest.raises(GuardError, match='existing'):
        lifecycle_store()
    assert not path.exists()


def test_assembly_cannot_run_without_canonical_authority(tmp_path, monkeypatch, v5_modules):
    monkeypatch.delenv('TT_LIFECYCLE_DB', raising=False)
    fixture = REPO / 'prompts/system-v5-draft/fixtures/night-porter'
    with pytest.raises(GuardError, match='canonical lifecycle store required'):
        v5_modules['assemble_next'].assemble_next(
            inputs_dir=fixture / 'NP17', base_spec=fixture / 'NP16/base_spec.json', out_dir=tmp_path / 'out')
    assert not (tmp_path / 'out').exists()


def test_promote_routes_reviewed_proposals_without_editing_companion(life, tmp_path):
    from charmeta.observations import append_observation
    from charmeta.promote import promote, _append_proposed_item
    from charmeta.store import build_companion_from_bible, save_companion
    from tests.test_support import BIBLE_FIXTURE, CAST_IDS
    store, ref, media = life
    for i in range(1, 4):
        cid = f'test-aired-{i}'
        clip = ready(store, media, cid)
        Adapters(store).call('D09', 'aired', clip_id=cid, receipt=store.verifier.issue(clip, 'promotion/' + cid))
    plan(store, 'next-clip')
    companion = tmp_path / 'companion.yaml'
    observations = tmp_path / 'observations.jsonl'
    lineage = tmp_path / 'lineage.jsonl'
    save_companion(companion, build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS))
    before = companion.read_bytes()
    for i in range(1, 4):
        append_observation(observations, {'clip_id': f'test-aired-{i}', 'character': 'mira_smirin',
                           'field': 'traits.intangible', 'extracted_text': 'patient at the landing', 'method': 'aired_event'})
    lineage.write_text(''.join(json.dumps({'clip_id': f'test-aired-{i}', 'show': 'black-ice'}) + '\n' for i in range(1, 4)))
    patch_data = {'mood': 'patient'}
    proposals = [{'character_id': 'HERON', 'base_version': 1, 'patch': patch_data,
                  'ref': ref, 'attestation': digest(patch_data), 'evidence': 'offline reviewed mapping'}]
    calls, spy = spy_calls()
    with spy:
        result = promote(companion_path=companion, observations_path=observations, lineage_path=lineage,
                         apply=True, lifecycle=store, clip_id='next-clip', proposals=proposals)
    assert len(result.proposals) == 1
    assert [(m, a) for m, a, _ in calls] == [('D10', 'propose')]
    assert store.snapshot()['clips']['next-clip']['proposals'] == proposals
    assert companion.read_bytes() == before
    with pytest.raises(GuardError, match='direct companion mutation'):
        _append_proposed_item({}, 'traits.intangible', 'text', 'clip')
    with pytest.raises(GuardError, match='planned clip'):
        promote(companion_path=companion, observations_path=observations, lineage_path=lineage,
                apply=True, lifecycle=store)


def test_assembly_routes_through_real_d12_gate_before_writing(life, tmp_path, monkeypatch, v5_modules):
    """Isolate the compiler while exercising real placement, queue gates and SQLite."""
    store, _, media = life
    prototype = plan(store, 'prototype')
    channel = 'Ch11 Fist Theater'
    for cid in ('NP16', 'NP17'):
        store.plan(cid, logical_id='assembly/' + cid, slot='assembly-slot/' + cid, lineage='assembly-lineage/' + cid,
                   prompt=prototype['prompt'], reference_hashes=prototype['reference_hashes'], spec=prototype['spec'],
                   channel=channel)
    render(store, 'NP16', media)
    previous = approve(store, 'NP16')
    Adapters(store).call('D09', 'aired', clip_id='NP16', receipt=store.verifier.issue(previous, 'assembly-previous'))
    module = v5_modules['assemble_next']
    real_build = module.build_prompt_v42.build
    def compile_fixture(spec, *args, **kwargs):
        built = real_build(spec, *args, **kwargs)
        built['args']['prompt'] = prototype['prompt']
        return built
    # Compiler/checker adapters are isolated here; D12 still applies the actual
    # foundation gate to the exact canonical prompt, refs and character cards.
    monkeypatch.setattr(module.build_prompt_v42, 'build', compile_fixture)
    monkeypatch.setattr(module.apply_check_v44, 'check', lambda *a, **k: {})
    fixture = REPO / 'prompts/system-v5-draft/fixtures'
    spool = tmp_path / 'empty.jsonl'
    spool.write_text('')
    out = tmp_path / 'assembled'
    calls, spy = spy_calls()
    with spy:
        module.assemble_next(inputs_dir=fixture / 'night-porter/NP17',
                             base_spec=fixture / 'night-porter/NP16/base_spec.json',
                             out_dir=out, lifecycle=store, spool_path=spool,
                             slots_path=fixture / 'ledger/slots.jsonl', lineage_path=fixture / 'ledger/lineage.jsonl',
                             character_meta_dir=tmp_path / 'no-meta', now='2026-11-04T12:00:00Z')
    assert [(m, a) for m, a, _ in calls] == [('D14', 'place'), ('D13', 'place'), ('D12', 'assemble')]
    assert store.snapshot()['clips']['NP17']['state'] == 'queued'
    assert (out / 'NP17.args.json').is_file()
    assert store.snapshot()['commits'][0]['clip_id'] == 'NP16'
    assert not (out / 'comments.consumed.jsonl').exists()


def test_d12_failure_is_persisted_and_keeps_clip_planned(life):
    store, _, _ = life
    plan(store, override={'depth': 3})
    with pytest.raises(GuardError, match='gate:'):
        Adapters(store).call('D12', 'assemble', clip_id='clip-1')
    state = store.snapshot()
    assert state['clips']['clip-1']['state'] == 'planned'
    assert state['problems']
    assert state['commits'] == []


def test_arbitrary_legacy_setters_fail(life):
    store, _, _ = life
    with pytest.raises(GuardError, match='setters disabled'):
        store.legacy_prompt_state('p', 'consumed')
    for machine, action in [('B04', 'set_state'), ('B04', 'set_status'), ('D09', 'air_yes')]:
        with pytest.raises(GuardError, match='bypass rejected'):
            Adapters(store).call(machine, action, clip_id='clip-1')


def test_proposal_seams_preserve_other_planned_changes(life, v5_modules):
    store, ref, _ = life
    plan(store)
    consequence = {'id': 'wet-sleeve', 'text': 'wet sleeve', 'character_id': 'HERON',
                   'ref': ref, 'evidence': 'offline fixture state'}
    v5_modules['layers_v4'].propose_consequences('clip-1', lifecycle=store, consequences=[consequence])
    v5_modules['memory'].summon({}, clip_id='clip-1', lifecycle=store, proposals=[])
    assert store.snapshot()['clips']['clip-1']['consequences'] == [consequence]


def test_receipt_reducer_alone_advances_summon_counters(life, v5_modules):
    store, ref, media = life
    plan(store)
    patch_data = {'mood': 'resolute'}
    proposals = [{'character_id': 'HERON', 'base_version': 1, 'patch': patch_data,
                  'ref': ref, 'attestation': digest(patch_data), 'evidence': 'offline fixture state'}]
    v5_modules['memory'].summon({}, clip_id='clip-1', lifecycle=store, proposals=proposals)
    render(store, 'clip-1', media)
    clip = approve(store, 'clip-1')
    assert store.snapshot()['cards']['HERON']['summon_count'] == 0
    assert store.snapshot()['cards']['HERON']['writein_level'] == 0
    receipt = store.verifier.issue(clip, 'counter-receipt')
    Adapters(store).call('D09', 'aired', clip_id=clip['id'], receipt=receipt)
    card = store.snapshot()['cards']['HERON']
    assert (card['summon_count'], card['writein_level']) == (1, 1)
    Adapters(store).call('D09', 'aired', clip_id=clip['id'], receipt=receipt)
    assert store.snapshot()['cards']['HERON'] == card


def test_canonical_tier_clock_ignores_unaired_indices(life, v5_modules):
    store, _, _ = life
    store.baseline_consequence({'id': 'rain', 'text': 'rain on the sleeve', 'tier': 'FLASH',
                                'since_index': 0, 'episode': 1, 'season': 1}, channel='Ch4')
    # Until a receipt advances this channel, there is no independent live clock.
    layers = v5_modules['layers_v4']
    assert not layers.tier_alive({'id': 'rain'}, 1, 1, 999, lifecycle=store)
    assert layers.carry_text({'id': 'rain', 'text': 'forged'}, 999, lifecycle=store) is None
