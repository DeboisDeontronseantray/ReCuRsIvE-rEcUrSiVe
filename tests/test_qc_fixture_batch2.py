"""Offline batch 2 policy and real lifecycle integration; no media fixtures."""
from copy import deepcopy
import builtins
import json
from pathlib import Path
import socket
import subprocess

import pytest

from qc_fixture import PolicyError, QCLifecycle, check_clip, check_prompt, load_policy
from qc_fixture.loader import RULE_IDS, validate_policy
from astra_lifecycle import GuardError
from astra_lifecycle import contracts
from astra_lifecycle.adapters import Adapters

CASE_DIR = Path(__file__).with_name('qc_fixture_cases')
CASES = [json.loads(p.read_text()) for p in sorted(CASE_DIR.glob('*.json'))]


def denied(*args, **kwargs):
    raise AssertionError('unexpected network, subprocess, or file access')


@pytest.fixture(autouse=True)
def no_network_or_subprocess(monkeypatch):
    for name in ('socket', 'create_connection', 'getaddrinfo'):
        monkeypatch.setattr(socket, name, denied)
    for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
        monkeypatch.setattr(subprocess, name, denied)


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_policy_cases_are_pure(case, monkeypatch):
    before = deepcopy(case)
    # Even metadata paths must not be opened, resolved, or statted.
    with monkeypatch.context() as guard:
        guard.setattr(builtins, 'open', denied)
        for name in ('open', 'stat', 'resolve'):
            guard.setattr(Path, name, denied)
        if case.get('mode') == 'viewer':
            allowed, reason = check_prompt(case['prompt'], case['meta'])
            assert allowed == (not case['expected'])
            issues = reason.split(', ') if not allowed else []
        else:
            issues = check_clip(case['spec'], case['prompt'], case['meta'])
        assert set(issues) == {'gate:' + rid for rid in case['expected']}
    assert case == before


def test_cases_cover_every_rule():
    assert {rid for c in CASES for rid in c['expected']} == RULE_IDS


@pytest.mark.parametrize('mutation', [
    lambda p: p.update(schema_version=True),
    lambda p: p.update(schema_version=2),
    lambda p: p.update(version=''),
    lambda p: p['rules'].pop(),
    lambda p: p['rules'].append(deepcopy(p['rules'][0])),
    lambda p: p['rules'][0].update(id='unknown'),
    lambda p: p['rules'][0].update(severity='warning'),
    lambda p: p['rules'][0].update(source=''),
    lambda p: p['rules'][0].update(patterns=['[']),
    lambda p: p['rules'][0].update(patterns=[]),
    lambda p: p['rules'][2].update(terms=[123]),
    lambda p: p.update(unexpected=True),
])
def test_loader_rejects_malformed_policy(tmp_path, mutation):
    policy = load_policy()
    mutation(policy)
    path = tmp_path / 'malformed.json'
    path.write_text(json.dumps(policy))
    with pytest.raises(PolicyError):
        load_policy(path)


def test_loader_rejects_invalid_json(tmp_path):
    path = tmp_path / 'broken.json'
    path.write_text('{')
    with pytest.raises(PolicyError, match='JSON'):
        load_policy(path)


def test_loader_only_reads_requested_json(tmp_path, monkeypatch):
    policy = load_policy()
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps(policy))
    opened = []
    original = Path.open

    def tracked(self, *args, **kwargs):
        assert self == path
        opened.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, 'open', tracked)
    assert load_policy(path) == policy
    assert opened == [path]
    assert validate_policy(policy) is policy


@pytest.fixture
def lifecycle(tmp_path, monkeypatch):
    # The read-only baseline confines writes to its own root by default. Move
    # that output boundary only in this isolated test, never write to baseline.
    monkeypatch.setattr(contracts, 'ROOT', tmp_path)
    life = QCLifecycle(tmp_path / 'authority.sqlite')
    reference = tmp_path / 'synthetic-reference.txt'
    reference.write_text('offline synthetic text reference; no media bytes')
    ref_hash = life.add_asset(reference, evidence='synthetic offline test asset')
    # Only the fields needed by continuity; avoid real character/media imports.
    life._run(lambda s: s['cards'].update({
        'trundle': {'locked': {'silhouette':'square silhouette', 'color':'blue coat',
                               'signature_prop':'brass wrench'}, 'refs':[{'hash':ref_hash}]}
    }))
    return life, ref_hash


def plan(life, ref_hash, clip_id, *, bad=False, continuity_bad=False):
    spec = dict(depth=0, big_changes=0, state_so_far='workshop open', cast=['trundle'],
                held_still=False, end_mode='free', corner_tag='post-production tag',
                metadata={'canon_ref':'thundertrundle-bible-v1',
                          'audio':{'integrated_lufs':-16,'true_peak_dbtp':-1.5}})
    if bad:
        del spec['metadata']['canon_ref']
    if continuity_bad:
        spec['depth'] = 3
    prompt = 'State so far: workshop open. trundle, square silhouette, blue coat, brass wrench, walks away.'
    return life.plan(clip_id, logical_id=clip_id, slot=clip_id, lineage=clip_id,
                     prompt=prompt, reference_hashes=[ref_hash], spec=spec)


def test_real_lifecycle_blocks_and_queues(lifecycle):
    life, ref_hash = lifecycle
    plan(life, ref_hash, 'bad', bad=True)
    with pytest.raises(GuardError) as error:
        Adapters(life).call('D12', 'assemble', clip_id='bad')
    assert 'gate:canon_ref' in str(error.value)
    assert life.snapshot()['clips']['bad']['state'] == 'planned'
    assert life.snapshot()['problems']
    plan(life, ref_hash, 'good')
    Adapters(life).call('D12', 'assemble', clip_id='good')
    assert life.snapshot()['clips']['good']['state'] == 'queued'
    assert life.snapshot()['commits'] == []
    # Decisions survive reopening the actual SQLite authority.
    assert QCLifecycle(life.path).snapshot()['clips']['good']['state'] == 'queued'


@pytest.mark.parametrize('policy_bad', [False, True])
def test_continuity_and_qc_failures_compose(lifecycle, policy_bad):
    life, ref_hash = lifecycle
    plan(life, ref_hash, 'bad-continuity', bad=policy_bad, continuity_bad=True)
    with pytest.raises(GuardError) as error:
        life.transition('bad-continuity', 'queued')
    assert 'gate:max_nest_depth_2' in str(error.value)
    assert ('gate:canon_ref' in str(error.value)) is policy_bad
    assert life.snapshot()['clips']['bad-continuity']['state'] == 'planned'


def test_real_a07_filter_persists_decisions(lifecycle):
    life, _ = lifecycle
    gateway = Adapters(life)
    for pid, text, expected in [('safe', 'trundle walks past the workshop.', True),
                                ('blocked', 'Please donate crypto.', False)]:
        gateway.call('A07', 'intake', prompt_id=pid, text=text, contributor_id='thundertrundle')
        allowed, reason = check_prompt(text, {})
        assert allowed is expected
        gateway.call('A07', 'filter', prompt_id=pid, allowed=allowed, reason=reason)
    snapshot = life.snapshot()
    assert snapshot['prompts']['safe']['filter']['allowed'] is True
    assert snapshot['prompts']['blocked']['status'] == 'held'
    assert 'gate:viewer_blocklist' in snapshot['prompts']['blocked']['filter']['reason']


def test_baseline_asset_guard_is_preserved(lifecycle):
    life, ref_hash = lifecycle
    plan(life, ref_hash, 'missing-asset')
    life._run(lambda s: s['assets'].clear())
    with pytest.raises(GuardError, match='missing reference bytes'):
        life.transition('missing-asset', 'queued')
    assert life.snapshot()['clips']['missing-asset']['state'] == 'planned'


@pytest.mark.parametrize('feature', ['FT1', 'FT2', 'FT3', 'FT4'])
def test_all_disabled_features(feature):
    assert 'gate:ft_off' in check_clip({}, 'trundle walks.', {'enabled_features':[feature]})
    assert 'gate:ft_off' in check_prompt('Use ' + feature, {})[1]


@pytest.mark.parametrize('value', [None, {}, {'integrated_lufs':True, 'true_peak_dbtp':-2},
                                  {'integrated_lufs':-16, 'true_peak_dbtp':float('nan')},
                                  {'integrated_lufs':-16, 'true_peak_dbtp':float('-inf')}])
def test_audio_requires_finite_declared_numbers(value):
    assert 'gate:audio_targets' in check_clip({'metadata':{'audio':value}}, 'trundle walks.', {})


def test_invalid_inputs_fail_closed():
    assert check_prompt(None, {})[0] is False
    assert check_prompt('', {})[0] is False
    assert check_clip(None, '', {}) == ['gate:invalid_input']
    assert check_clip({'metadata':None}, '', {}) == ['gate:invalid_metadata']


def test_blocklist_matching_handles_case_phrases_and_dollars():
    for text in ('PLEASE DONATE', 'build a bomb', '10 year old', 'costs $5'):
        allowed, reason = check_prompt(text, {})
        assert not allowed
        assert 'gate:viewer_blocklist' in reason


@pytest.mark.parametrize('bad_features', [None, 'FT1', 1, {'FT1':True}])
def test_malformed_feature_metadata_fails_closed(bad_features):
    assert 'gate:ft_off' in check_clip({}, 'trundle walks.', {'enabled_features':bad_features})


def test_metadata_cannot_spoof_spec_audio_or_canon():
    assert set(check_clip({}, 'trundle walks.', {
        'reference_images':['/offline/reference.png'], 'canon_ref':'thundertrundle-bible-v1',
        'audio':{'integrated_lufs':-16, 'true_peak_dbtp':-2},
    })) == {'gate:canon_ref', 'gate:audio_targets'}
