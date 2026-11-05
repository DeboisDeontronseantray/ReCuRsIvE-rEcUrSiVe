from pathlib import Path
import os
import shutil
import tempfile
import unittest

from astra_lifecycle import Lifecycle, GuardError
from astra_lifecycle.contracts import ROOT
from astra_lifecycle.fixture import setup, plan, render, approve


class FinalBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / 'runtime', prefix='final-'))
        self.life = Lifecycle(self.tmp / 'state.sqlite')
        self.ref, self.media = setup(self.life)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def ready(self, cid='clip-1'):
        plan(self.life, cid)
        render(self.life, cid, self.media)
        return approve(self.life, cid)


class Task01(FinalBase):
    def test_receipt_cannot_cross_independent_databases(self):
        c = self.ready()
        other = Lifecycle(self.tmp / 'other.sqlite')
        _, media = setup(other)
        plan(other)
        render(other, 'clip-1', media)
        c2 = approve(other, 'clip-1')
        with self.assertRaisesRegex(GuardError, 'authority'):
            self.life.transition(c['id'], 'aired', evidence=other.verifier.issue(c2, 'foreign'))
        self.assertEqual([], self.life.snapshot()['commits'])

    def test_closed_receipt_even_with_permissive_verifier(self):
        c = self.ready()
        receipt = self.life.verifier.issue(c, 'r')
        class UnsafeVerifier:
            def verify(self, row):
                return row
        self.life.verifier = UnsafeVerifier()
        for delta in ({'completed': 1}, {'mode': 'production'}, {'extra': True}, {'id': []}):
            with self.subTest(delta=delta), self.assertRaises(GuardError):
                self.life.transition(c['id'], 'aired', evidence=receipt | delta)

    def test_actual_process_death_rolls_back_and_restarts(self):
        c = self.ready()
        receipt = self.life.verifier.issue(c, 'crash')
        before = self.life.snapshot()
        pid = os.fork()
        if pid == 0:
            try:
                Lifecycle(self.life.path).transition(c['id'], 'aired', evidence=receipt,
                                                    crash_hook=lambda: os._exit(17))
            finally:
                os._exit(18)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(17, os.waitstatus_to_exitcode(status))
        restarted = Lifecycle(self.life.path)
        self.assertEqual(before, restarted.snapshot())
        restarted.transition(c['id'], 'aired', evidence=receipt)
        restarted.transition(c['id'], 'aired', evidence=receipt)
        self.assertEqual(1, len(restarted.snapshot()['commits']))


class Task02(unittest.TestCase):
    def test_relative_aliased_and_reflected_legacy_bypasses(self):
        from astra_lifecycle.integration import audit_source
        for source in ('from . import checker', 'from .checker import approve as ok',
                       'from harmless import mark_consumed as done',
                       'getattr(obj, "mark_consumed")(p)',
                       'from . import socket'):
            with self.subTest(source=source):
                self.assertTrue(audit_source(source))
        self.assertEqual([], audit_source('from astra_lifecycle.adapters import Adapters'))


class Task03(FinalBase):
    def test_truthy_filter_is_not_policy_review(self):
        self.life.intake('p', 'keep moving', 'contributor')
        for value in ('false', 'yes', 1, None, []):
            with self.subTest(value=value), self.assertRaises(GuardError):
                self.life.filter_prompt('p', allowed=value, reason='fixture')
        self.assertNotIn('filter', self.life.snapshot()['prompts']['p'])

    def test_revised_review_requires_new_assembly(self):
        self.life.intake('p', 'keep moving', 'contributor')
        self.life.filter_prompt('p', allowed=True, reason='review 1')
        plan(self.life, comments=['keep moving'])
        self.life.place('clip-1', ['p'])
        self.life.filter_prompt('p', allowed=True, reason='review 2')
        with self.assertRaisesRegex(GuardError, 'filter changed'):
            self.life.transition('clip-1', 'queued')
        self.assertEqual('eligible', self.life.eligible()[0]['status'])

    def test_human_release_does_not_reuse_old_filter(self):
        from astra_lifecycle.fixture import yes
        self.life.intake('p', 'keep moving', 'contributor')
        self.life.filter_prompt('p', allowed=True, reason='review')
        self.life.release_prompt('p', yes('release_prompt:released', 'p', 'close'), outcome='released')
        self.life.release_prompt('p', yes('release_prompt:eligible', 'p', 'open'))
        plan(self.life, comments=['keep moving'])
        with self.assertRaisesRegex(GuardError, 'filtered'):
            self.life.place('clip-1', ['p'])


class Task04(FinalBase):
    def test_candidate_review_primary_retirement_only_on_air(self):
        from astra_lifecycle import digest
        asset = self.tmp / 'synthetic-state-reference.fixture'
        asset.write_bytes(b'fixture bytes only; not visual evidence')
        ref = self.life.add_asset(asset, evidence='synthetic test')
        patch = {'mood': 'resolute'}
        self.life.candidate_still('HERON', ref, patch, evidence='synthetic candidate')
        c = plan(self.life)
        # Planned input is constructed explicitly, never edited after queueing.
        self.life.plan('updated', logical_id='fixture/updated', slot='updated', lineage='updated',
                       prompt=c['prompt'], reference_hashes=[self.ref, ref], spec=c['spec'])
        self.life.propose('updated', proposals=[dict(character_id='HERON', base_version=1, patch=patch,
            ref=ref, attestation=digest(patch), evidence='synthetic observation')])
        render(self.life, 'updated', self.media)
        c = approve(self.life, 'updated')
        receipt = self.life.verifier.issue(c, 'still')
        with self.assertRaisesRegex(GuardError, 'accepted'):
            self.life.transition('updated', 'aired', evidence=receipt)
        self.life.accept_still('HERON', ref, evidence='synthetic review; not real QC')
        self.assertEqual(self.ref, self.life.read_card('HERON')['refs'][0]['hash'])
        self.life.transition('updated', 'aired', evidence=receipt)
        s = self.life.snapshot()
        self.assertEqual(ref, self.life.read_card('HERON')['refs'][0]['hash'])
        self.assertEqual('retired', s['stills']['HERON:' + self.ref]['state'])
        self.assertEqual('primary', s['stills']['HERON:' + ref]['state'])
        self.assertEqual(self.ref, self.life.read_card('HERON', version=1)['refs'][0]['hash'])

    def test_consequence_is_content_hashed_and_incomplete_defaults_short(self):
        self.life.baseline_consequence({'id': 'c', 'text': 'wet coat', 'character_id': 'HERON', 'tier': 'LEGEND'}, channel='Ch4')
        c = self.life.snapshot()['consequences']['c']
        self.assertEqual('FLASH', c['tier'])
        self.assertEqual(64, len(c['content_hash']))


class Task05(FinalBase):
    def test_portal_and_pivot_cannot_use_still_fix(self):
        plan(self.life, override={'pivot': 'whip', 'portal': 'medallion', 'transition_method': 'still-edit'})
        with self.assertRaisesRegex(GuardError, 'portal_pivot'):
            self.life.transition('clip-1', 'queued')
        self.assertEqual('planned', self.life.snapshot()['clips']['clip-1']['state'])
        self.assertEqual('continuity gate', self.life.snapshot()['problems'][-1]['failure_type'])

    def test_malformed_cast_fails_as_guard_not_crash(self):
        plan(self.life, override={'cast': ['HERON', {}]})
        with self.assertRaisesRegex(GuardError, 'cast_required'):
            self.life.transition('clip-1', 'queued')

    def test_prompt_portal_is_candidate_option_not_mandatory(self):
        for cid, overrides in [('plain', {}), ('portal', {'portal': 'medallion', 'pivot': 'whip', 'transition_method': 'prompt'})]:
            plan(self.life, cid, override=overrides)
            self.life.transition(cid, 'queued')


class Task06(FinalBase):
    def test_blocked_batch_still_estimates_without_mutation(self):
        plan(self.life, price_cents=80)
        before = self.life.snapshot()
        result = self.life.diagnose_batch(['clip-1'], inventory_complete=False, inventory_evidence='partial local scan')
        self.assertEqual(80, result['estimate_cents'])
        self.assertFalse(result['executable'])
        self.assertIn('inventory coverage incomplete', result['blockers'])
        self.assertEqual(before, self.life.snapshot())

    def test_route_change_invalidates_reservation_manifest(self):
        from astra_lifecycle import digest
        from astra_lifecycle.fixture import yes
        plan(self.life)
        self.life.transition('clip-1', 'queued')
        c = self.life.snapshot()['clips']['clip-1']
        batch = digest([self.life._manifest(c)])
        self.life.authorize_batch(['clip-1'], yes('authorize_batch', batch, 'route', ceiling_cents=0), 0)
        self.life._run(lambda s: s['clips']['clip-1'].update(route='different-provider'))
        with self.assertRaisesRegex(GuardError, 'manifest changed'):
            self.life.reserve_batch('route')

    def test_channel_record_retains_revisions_and_execution(self):
        for cid in ('first', 'second'):
            plan(self.life, cid)
            render(self.life, cid, self.media)
        record = self.life.snapshot()['channel_batches']['Ch4']
        self.assertEqual(2, record['version'])
        self.assertEqual(2, len(record['revisions']))
        self.assertEqual(2, len(record['execution_history']))
        self.assertEqual(0, sum(r['spent_cents'] for r in record['execution_history']))

    def test_truthy_price_ceiling_and_unlabelled_approval_rejected(self):
        from astra_lifecycle import digest
        from astra_lifecycle.fixture import yes
        plan(self.life)
        self.life.transition('clip-1', 'queued')
        batch = digest([self.life._manifest(self.life.snapshot()['clips']['clip-1'])])
        a = yes('authorize_batch', batch, 'bool', ceiling_cents=False)
        with self.assertRaises(GuardError):
            self.life.authorize_batch(['clip-1'], a, 0)
        a['ceiling_cents'] = 0
        del a['mode']
        with self.assertRaises(GuardError):
            self.life.authorize_batch(['clip-1'], a, 0)


class Task07(FinalBase):
    def test_fix_resolution_needs_evidence_and_is_durable(self):
        c = self.ready()
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'r'))
        row = self.life.watch_after_air(c['id'], 'seam pop', 'synthetic seam', ['overlap_frames'])
        with self.assertRaises(GuardError):
            self.life.resolve_problem(row['id'], fix_id='zipper', evidence='')
        self.life.resolve_problem(row['id'], fix_id='zipper', evidence='fixture review confirms seam plan; no edit executed')
        self.assertEqual('resolved', Lifecycle(self.life.path).snapshot()['problems'][0]['status'])
        with self.assertRaises(GuardError):
            self.life.resolve_problem(row['id'], fix_id='zipper', evidence='duplicate')

    def test_portal_fix_selector_never_reintroduces_still_seams(self):
        c = self.ready()
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'r'))
        for condition in ('portal', 'pivot'):
            row = self.life.watch_after_air(c['id'], 'style drift', 'fixture',
                                           [condition, 'reference_review', 'bridge_allowed', 'cheaper_fixes_exhausted'])
            self.assertIsNone(row['fix_id'])


class Task08(FinalBase):
    def test_scaffolding_alias_does_not_require_episode_or_air(self):
        self.life.version_metadata('old', {'note': 'candidate wording'})
        self.life.version_metadata('new', {'note': 'revised candidate wording'})
        self.life.swap_alias('old', 'new', reason='clarify candidate; no creative authorization')
        self.assertEqual('new', self.life.read_metadata('old')['id'])
        self.assertFalse(self.life.read_metadata('old')['executable_rule'])
        self.assertEqual([], self.life.snapshot()['commits'])
        for version in (0, -1, True, 2):
            with self.assertRaises(GuardError):
                self.life.read_metadata('old', version=version)

    def test_boundary_cannot_become_general_metadata_mechanism(self):
        self.life.version_metadata('old', {'note': 'old'})
        self.life.version_metadata('new', {'note': 'new'})
        with self.assertRaisesRegex(GuardError, 'only for character'):
            self.life.swap_alias('old', 'new', reason='bad generalization', bridge_clip='anything')
        with self.assertRaisesRegex(GuardError, 'character-specific'):
            self.life.swap_alias('old', 'new', reason='bad scope', crossover_test=True, bridge_clip='anything')

    def test_crossover_bridge_requires_air(self):
        from copy import deepcopy
        other = deepcopy(self.life.read_card('HERON', version=1))
        other.update(id='HERON-test', name='HERON-test')
        self.life.baseline_card(other)
        plan(self.life, override={'bridge': 'Depth shift'})
        render(self.life, 'clip-1', self.media)
        c = approve(self.life, 'clip-1')
        with self.assertRaises(GuardError):
            self.life.swap_alias('HERON', 'HERON-test', reason='fixture crossover', crossover_test=True, bridge_clip=c['id'])
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'crossover'))
        self.life.swap_alias('HERON', 'HERON-test', reason='fixture crossover', crossover_test=True, bridge_clip=c['id'])


class Task09(FinalBase):
    def test_empty_observation_never_consumes_and_ledger_distinguishes_air_from_landing(self):
        for pid, text in [('seen', 'keep moving'), ('missed', 'carry the canister')]:
            self.life.intake(pid, text, 'contributor-' + pid)
            self.life.filter_prompt(pid, allowed=True, reason='fixture')
        plan(self.life, comments=['keep moving', 'carry the canister'])
        self.life.place('clip-1', ['seen', 'missed'])
        render(self.life, 'clip-1', self.media)
        self.life.observe('clip-1', 'seen', 'kept moving', score=.8, evidence='synthetic observation')
        self.life.observe('clip-1', 'missed', '   ', score=0, evidence='synthetic miss')
        c = approve(self.life, 'clip-1')
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'ledger'))
        seen = self.life.commenter_history('contributor-seen')[0]
        missed = self.life.commenter_history('contributor-missed')[0]
        self.assertTrue(seen['aired'] and seen['landed'])
        self.assertTrue(missed['aired'])
        self.assertFalse(missed['landed'])
        self.assertEqual('missed', missed['delivery_status'])
        self.assertEqual('eligible', self.life.snapshot()['prompts']['missed']['status'])
        self.assertNotIn('handle', seen)
        self.assertEqual(64, len(seen['requested_hash']))

    def test_nontext_observation_cannot_fake_landing(self):
        self.life.intake('p', 'keep moving', 'contributor')
        self.life.filter_prompt('p', allowed=True, reason='fixture')
        plan(self.life, comments=['keep moving'])
        self.life.place('clip-1', ['p'])
        render(self.life, 'clip-1', self.media)
        with self.assertRaises(GuardError):
            self.life.observe('clip-1', 'p', {'claimed': True}, score=1, evidence='fixture')


class Task10(FinalBase):
    def test_replay_intake_is_durable_idempotent_and_has_no_live_mode(self):
        from astra_lifecycle.capture import ReplayIntake
        event = dict(mode='fixture-replay', id='message-1', text='keep moving', contributor_id='viewer-1',
                     channel='Ch4', timestamp='2020-01-01T00:00:00Z')
        ReplayIntake(self.life).ingest(event)
        restarted = Lifecycle(self.life.path)
        ReplayIntake(restarted).ingest(event)
        self.assertEqual(1, len(restarted.eligible()))
        self.assertEqual([], restarted.snapshot()['commits'])
        for delta in ({'mode': 'live'}, {'text': 'changed'}):
            with self.assertRaises(GuardError):
                ReplayIntake(restarted).ingest(event | delta)
