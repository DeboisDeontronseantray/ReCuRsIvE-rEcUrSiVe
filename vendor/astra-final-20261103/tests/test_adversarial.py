from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest

from astra_lifecycle import Lifecycle, GuardError, digest
from astra_lifecycle.contracts import ROOT
from astra_lifecycle.fixture import setup, plan, render, air, approve, yes
from astra_lifecycle.integration import audit_source, run_audit
from astra_lifecycle.recipe import route


class AdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / 'runtime', prefix='adversarial-'))
        self.life = Lifecycle(self.tmp / 'state.sqlite')
        self.ref, self.media = setup(self.life)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_direct_legacy_imports_fail_consumer_audit(self):
        for source in ('from checker import approve\napprove(slot, versions, new, when)',
                       'import intake\nintake.mark_consumed(path, keys, clip_id=c)',
                       'from layers_v4 import tier_alive', 'import requests',
                       'exec(source)', 'import importlib'):
            with self.subTest(source=source):
                self.assertTrue(audit_source(source))
        self.assertEqual([], audit_source('from astra_lifecycle import Lifecycle\nlife.transition(cid, "queued")'))
        self.assertEqual('PASS', run_audit()['status'])

    def test_every_present_mapped_source_kept_read_only(self):
        inventory = run_audit()['source_inventory']
        self.assertTrue(all(r['present'] for r in inventory))
        self.assertEqual({'D09', 'D13', 'D14', 'D15', 'D10', 'B01', 'B04', 'D08', 'A07', 'D12', 'D16', 'D17', 'render'}, {r['machine'] for r in inventory})

    def test_atomic_batch_reservation_rolls_back_on_second_item_failure(self):
        plan(self.life, 'a')
        plan(self.life, 'premise')
        plan(self.life, 'b', dependencies=['premise'])
        for cid in ('a', 'b'):
            self.life.transition(cid, 'queued')
        s = self.life.snapshot()
        batch = digest([self.life._manifest(s['clips'][cid]) for cid in ('a', 'b')])
        self.life.authorize_batch(['a', 'b'], yes('authorize_batch', batch, 'batch', ceiling_cents=0), 0)
        with self.assertRaises(GuardError):
            self.life.reserve_batch('batch')
        self.assertEqual({}, self.life.snapshot()['reservations'])

    def test_changed_prompt_bytes_and_ref_manifest_rejected_at_dispatch(self):
        for key, value in (('prompt', 'modified'), ('reference_hashes', ['0' * 64])):
            cid = 'changed-' + key
            plan(self.life, cid)
            self.life.transition(cid, 'queued')
            c = self.life.snapshot()['clips'][cid]
            batch = digest([self.life._manifest(c)])
            auth = 'batch-' + key
            self.life.authorize_batch([cid], yes('authorize_batch', batch, auth, ceiling_cents=0), 0)
            self.life.reserve_batch(auth)
            # Fault injection models a buggy integration mutating storage out of band.
            self.life._run(lambda s: s['clips'][cid].update({key: value}))
            with self.assertRaises(GuardError):
                self.life.dispatch(cid)

    def test_receipt_id_cannot_be_used_for_other_clip_or_changed_replay(self):
        for cid in ('a', 'b'):
            plan(self.life, cid)
            render(self.life, cid, self.media)
            approve(self.life, cid)
        a, b = (self.life.snapshot()['clips'][cid] for cid in ('a', 'b'))
        r = self.life.verifier.issue(a, 'one-id')
        self.life.transition('a', 'aired', evidence=r)
        with self.assertRaises(GuardError):
            self.life.transition('b', 'aired', evidence=self.life.verifier.issue(b, 'one-id'))
        with self.assertRaises(GuardError):
            self.life.transition('a', 'aired', evidence=self.life.verifier.issue(a, 'new-id'))
        self.assertEqual(1, len(self.life.snapshot()['commits']))

    def test_two_placements_cannot_consume_one_prompt_twice(self):
        self.life.intake('p', 'keep moving', 'fixture-contributor')
        self.life.filter_prompt('p', allowed=True, reason='fixture')
        for cid in ('a', 'b'):
            plan(self.life, cid, comments=['keep moving'])
            self.life.place(cid, ['p'])
            render(self.life, cid, self.media)
            self.life.observe(cid, 'p', 'kept moving', score=1, evidence='fixture')
            approve(self.life, cid)
        a, b = (self.life.snapshot()['clips'][cid] for cid in ('a', 'b'))
        self.life.transition('a', 'aired', evidence=self.life.verifier.issue(a, 'air-a'))
        with self.assertRaises(GuardError):
            self.life.transition('b', 'aired', evidence=self.life.verifier.issue(b, 'air-b'))
        self.assertEqual(1, len(self.life.snapshot()['commits']))

    def test_full_tier_machine_requires_three_later_aired_reuses(self):
        self.life.baseline_consequence({'id': 'wet', 'text': 'wet coat', 'character_id': 'HERON'}, channel='Ch4')
        for i, expected in enumerate(('SCAR', 'MARK', 'LEGEND'), 1):
            cid = 'reuse-' + str(i)
            plan(self.life, cid, comments=['wet coat'])
            self.life.propose(cid, reuses=[{'id': 'wet', 'evidence': 'wet coat', 'ref': self.ref}])
            render(self.life, cid, self.media)
            air(self.life, cid)
            self.assertEqual(expected, self.life.snapshot()['consequences']['wet']['tier'])
        plan(self.life, 'future', episode=1, season=2)
        render(self.life, 'future', self.media)
        air(self.life, 'future')
        self.assertTrue(self.life.snapshot()['consequences']['wet']['active'])

    def test_expired_consequence_cannot_be_resurrected_by_reuse(self):
        self.life.baseline_consequence({'id': 'wet', 'text': 'wet coat', 'character_id': 'HERON'}, channel='Ch4')
        plan(self.life, 'expire')
        render(self.life, 'expire', self.media)
        air(self.life, 'expire')
        plan(self.life, 'resurrect', comments=['wet coat'])
        self.life.propose('resurrect', reuses=[{'id': 'wet', 'evidence': 'wet coat', 'ref': self.ref}])
        render(self.life, 'resurrect', self.media)
        c = approve(self.life, 'resurrect')
        with self.assertRaises(GuardError):
            self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'resurrect'))
        self.assertFalse(self.life.snapshot()['consequences']['wet']['active'])

    def test_unrelated_text_cannot_advance_consequence(self):
        self.life.baseline_consequence({'id': 'wet', 'text': 'wet coat', 'character_id': 'HERON'}, channel='Ch4')
        plan(self.life)
        self.life.propose('clip-1', reuses=[{'id': 'wet', 'evidence': 'HERON', 'ref': self.ref}])
        render(self.life, 'clip-1', self.media)
        c = approve(self.life, 'clip-1')
        with self.assertRaises(GuardError):
            self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'unrelated'))

    def test_old_card_version_remains_readable(self):
        plan(self.life)
        patch = {'mood': 'resolute'}
        self.life.propose('clip-1', proposals=[dict(character_id='HERON', base_version=1, patch=patch,
            ref=self.ref, attestation=digest(patch), evidence='fixture')])
        render(self.life, 'clip-1', self.media)
        air(self.life, 'clip-1')
        self.assertEqual('watchful', self.life.read_card('HERON', version=1)['plastic']['mood'])
        self.assertEqual('resolute', self.life.read_card('HERON')['plastic']['mood'])
        self.assertEqual(2, self.life.read_card('HERON')['field_versions']['plastic.mood'])

    def test_open_idea_survives_silence_and_only_explicit_release_closes(self):
        self.life.record_idea('idea', 'Keep the canister callback open.')
        restarted = Lifecycle(self.life.path)
        self.assertEqual('open', restarted.snapshot()['open_ideas']['idea']['status'])
        with self.assertRaises(GuardError):
            restarted.close_idea('idea', {'actor': 'trundle'})
        restarted.close_idea('idea', yes('close_idea', 'idea', 'close'))
        self.assertEqual('closed', restarted.snapshot()['open_ideas']['idea']['status'])

    def test_carried_age_priority_and_compatible_batching(self):
        for pid, text, channel in (('old', 'keep moving', 'Ch4'), ('new', 'HERON moves', 'Ch4'), ('other', 'HERON moves', 'Ch2')):
            self.life.intake(pid, text, 'fixture-contributor-' + pid, channel=channel)
            self.life.filter_prompt(pid, allowed=True, reason='fixture')
        self.life.carry(['old'], reason='previous beat budget full')
        result = route(self.life.eligible(), ['HERON'], duration=10)
        self.assertEqual('old', result['placed'][0]['id'])
        self.assertTrue(all(p['channel'] == 'Ch4' for p in result['placed']))
        self.assertEqual(['other'], [p['id'] for p in result['carried']])

    def test_unknown_dependency_cannot_enter_graph(self):
        with self.assertRaises(GuardError):
            plan(self.life, dependencies=['missing'])
        self.assertEqual({}, self.life.snapshot()['clips'])

    def test_filter_hold_is_not_consumption_and_needs_explicit_release(self):
        self.life.intake('held', 'fixture review request', 'fixture-contributor')
        self.life.filter_prompt('held', allowed=False, reason='uncertain; needs review')
        self.assertEqual([], self.life.eligible())
        self.assertIsNone(self.life.snapshot()['prompts']['held']['final_outcome'])
        self.life.release_prompt('held', yes('release_prompt:eligible', 'held', 'release'))
        self.life.filter_prompt('held', allowed=True, reason='fixture review complete')
        self.assertEqual('held', self.life.eligible()[0]['id'])


if __name__ == '__main__':
    unittest.main()
