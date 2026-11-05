import concurrent.futures
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from astra_lifecycle import Lifecycle, GuardError, digest
from astra_lifecycle.adapters import Adapters, MACHINES
from astra_lifecycle.contracts import EDGES, ROOT, STATES
from astra_lifecycle.fixture import SEEDS, setup, plan, render, approve, air, yes
from astra_lifecycle.legacy import read_pure
from astra_lifecycle.recipe import assemble, route, sentiment
from astra_lifecycle.characters import alive, normalize_consequence, brief


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / 'runtime', prefix='test-'))
        self.life = Lifecycle(self.tmp / 'state.sqlite')
        self.ref, self.media = setup(self.life)
        self.adapter = Adapters(self.life)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def prompt(self, pid='p1', text='heron should follow him across the bridge'):
        self.adapter.call('A07', 'intake', prompt_id=pid, text=text, contributor_id='contributor-' + pid,
                          metadata={'handle': '@fixture-viewer'}, received_at='2020-01-01T00:00:00+00:00')
        self.adapter.call('A07', 'filter', prompt_id=pid, allowed=True, reason='fixture policy pass')
        return text

    def ready(self, cid='clip-1', *, with_prompt=False, **kwargs):
        text = self.prompt() if with_prompt else None
        plan(self.life, cid, comments=[text] if text else [], **kwargs)
        if text:
            self.adapter.call('D13', 'place', clip_id=cid, prompt_ids=['p1'])
        render(self.life, cid, self.media)
        return approve(self.life, cid)

    def assertNoCanon(self):
        s = self.life.snapshot()
        self.assertEqual([], s['commits'])
        self.assertEqual(0, s['cards']['HERON']['summon_count'])
        self.assertEqual({}, s['clocks'])

    def test_D09_authorization_export_and_assembly_cannot_air(self):
        c = self.ready()
        for bogus in (None, {'air_yes': True}, {'status': 'AIRED'}, {'verified': True}, {'approved': True}):
            with self.subTest(bogus=bogus), self.assertRaises(GuardError):
                self.adapter.call('D09', 'aired', clip_id=c['id'], receipt=bogus)
        self.assertNoCanon()
        self.assertFalse(self.adapter.derive_aired([{'clip_id': c['id'], 'air_yes': True}])[c['id']])
        self.assertTrue(any(p['failure_type'] == 'approval-as-aired' for p in self.life.snapshot()['problems']))

    def test_D09_receipt_join_timestamp_signature_and_completion(self):
        c = self.ready()
        valid = self.life.verifier.issue(c, 'valid')
        for key, value in (('slot', 'wrong'), ('lineage', 'wrong'), ('clip_id', 'wrong'), ('media_hash', '0' * 64),
                           ('timestamp', 'garbage'), ('timestamp', '2026-01-01T00:00:00'), ('timestamp', '2999-01-01T00:00:00Z'), ('completed', False)):
            r = dict(valid, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(GuardError):
                self.life.transition(c['id'], 'aired', evidence=r)
        # Even correctly signed wrong-occupant evidence cannot pass the join.
        wrong = dict(c, slot='other')
        with self.assertRaises(GuardError):
            self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(wrong, 'wrong'))
        with self.assertRaises(GuardError):
            self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'naive', when='2026-01-01T00:00:00'))
        with self.assertRaises(GuardError):
            self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'old', when='2020-01-01T00:00:00Z'))
        self.assertNoCanon()

    def test_atomic_air_replay_restart_exactly_once(self):
        c = self.ready(with_prompt=True)
        self.life.observe(c['id'], 'p1', 'HERON follows him across the bridge', score=1, evidence='synthetic reviewed appearance')
        r = self.life.verifier.issue(c, 'play')
        self.life.transition(c['id'], 'aired', evidence=r)
        reopened = Lifecycle(self.life.path)
        reopened.transition(c['id'], 'aired', evidence=r)
        s = reopened.snapshot()
        self.assertEqual(1, len(s['commits']))
        self.assertEqual(1, len(s['receipts']))
        self.assertEqual('consumed', s['prompts']['p1']['status'])
        self.assertEqual(1, len(s['ledger']))
        self.assertTrue(s['ledger'][0]['aired'])
        self.assertNotIn('handle', s['ledger'][0])

    def test_air_failure_rolls_back_all_projections(self):
        c = self.ready(with_prompt=True)
        self.life.observe(c['id'], 'p1', 'followed', score=1, evidence='fixture')
        r = self.life.verifier.issue(c, 'play')
        before = self.life.snapshot()
        def crash():
            raise RuntimeError('simulated power loss before durable commit')
        with self.assertRaises(RuntimeError):
            self.life.transition(c['id'], 'aired', evidence=r, crash_hook=crash)
        self.assertEqual(before, self.life.snapshot())
        self.life.transition(c['id'], 'aired', evidence=r)
        self.assertEqual(1, len(self.life.snapshot()['commits']))

    def test_concurrent_receipt_callbacks_commit_once(self):
        c = self.ready()
        r = self.life.verifier.issue(c, 'race')
        def callback(_):
            return Lifecycle(self.life.path).transition(c['id'], 'aired', evidence=r)['state']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(['aired'] * 4, list(pool.map(callback, range(4))))
        self.assertEqual(1, len(self.life.snapshot()['commits']))

    def test_closed_table_rejects_every_unlisted_edge(self):
        # Exercise public API against every illegal pair from every state.
        for source in STATES:
            for target in STATES:
                if target in EDGES[source] or source == target == 'aired':
                    continue
                with self.subTest(source=source, target=target):
                    cid = 'edge-' + source + '-' + target
                    plan(self.life, cid)
                    if source in ('queued', 'rendered', 'approved', 'aired'):
                        if source == 'queued':
                            self.life.transition(cid, 'queued')
                        else:
                            render(self.life, cid, self.media)
                            if source == 'approved':
                                approve(self.life, cid)
                            if source == 'aired':
                                air(self.life, cid)
                    elif source in ('pulled', 'held', 'rejected', 'failed'):
                        self.life.transition(cid, source, evidence={'reason': 'fixture exit'})
                    with self.assertRaises(GuardError):
                        self.life.transition(cid, target)

    def test_D13_D14_merged_but_never_aired_and_pulled_after_assembly(self):
        text = self.prompt()
        plan(self.life, comments=[text])
        self.adapter.call('D13', 'place', clip_id='clip-1', prompt_ids=['p1'])
        self.assertEqual('eligible', self.life.snapshot()['prompts']['p1']['status'])
        self.adapter.call('D12', 'assemble', clip_id='clip-1')
        self.life.transition('clip-1', 'pulled', evidence={'reason': 'schedule replacement'})
        p = self.life.eligible()[0]
        self.assertEqual('p1', p['id'])
        self.assertEqual('pulled', p['attempts'][0]['status'])
        self.assertIsNone(p['final_outcome'])
        self.assertNoCanon()

    def test_rendered_then_pulled_retains_unseen_prompt(self):
        self.ready(with_prompt=True)
        self.life.transition('clip-1', 'pulled', evidence={'reason': 'not aired'})
        self.assertEqual(['p1'], [p['id'] for p in self.life.eligible()])
        self.assertFalse(self.life.snapshot()['ledger'][0]['aired'])

    def test_failed_clip_reoffers_prompt_on_new_attempt(self):
        text = self.prompt()
        plan(self.life, 'first', comments=[text])
        self.life.place('first', ['p1'])
        self.life.transition('first', 'failed', evidence={'reason': 'fixture render error'})
        plan(self.life, 'second', comments=[text])
        self.life.place('second', ['p1'])
        self.assertEqual(2, len(self.life.snapshot()['prompts']['p1']['attempts']))
        self.assertEqual('eligible', self.life.eligible()[0]['status'])

    def test_A07_crash_after_seen_before_wrap_recovery_is_idempotent(self):
        text = self.prompt()
        reopened = Lifecycle(self.life.path)
        reopened.intake('p1', text, 'contributor-p1', metadata={'handle': '@fixture-viewer'})
        recovered = Adapters(reopened).call('A07', 'recover', channel='Ch4')
        self.assertEqual(['p1'], [p['id'] for p in recovered])
        self.assertEqual(1, len(reopened.snapshot()['prompts']))
        with self.assertRaises(GuardError):
            reopened.intake('p1', 'changed message', 'contributor-p1')

    def test_carried_prompts_do_not_age_out(self):
        self.prompt()
        self.assertEqual('2020-01-01T00:00:00+00:00', self.adapter.call('D14', 'eligible')[0]['received_at'])
        self.assertEqual(['p1'], [p['id'] for p in route(self.life.eligible(), ['HERON'], duration=2.5)['carried']])

    def test_missed_comment_rolls_forward_even_after_air(self):
        c = self.ready(with_prompt=True)
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'miss'))
        self.assertEqual('p1', self.life.eligible()[0]['id'])
        self.assertEqual(0, self.life.snapshot()['ledger'][0]['score'])
        self.assertTrue(self.life.snapshot()['ledger'][0]['aired'])
        self.assertEqual('dropped comment', self.life.snapshot()['problems'][-1]['failure_type'])

    def test_B04_terminal_cannot_reset_without_explicit_human_release(self):
        c = self.ready(with_prompt=True)
        self.life.observe(c['id'], 'p1', 'followed', score=1, evidence='fixture')
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'release-test'))
        for target in ('WAITING', 'MERGED', 'AIRED', 'WITHDRAWN'):
            with self.assertRaises(GuardError):
                self.life.legacy_prompt_state('p1', target)
        with self.assertRaises(GuardError):
            self.life.release_prompt('p1', {'actor': 'trundle'})
        self.life.release_prompt('p1', yes('release_prompt:eligible', 'p1', 'release-1'))
        self.assertEqual('eligible', self.life.snapshot()['prompts']['p1']['status'])
        self.assertEqual(1, len(self.life.snapshot()['commits']))

    def test_explicit_release_can_close_unseen_prompt_without_canon(self):
        self.prompt()
        self.life.release_prompt('p1', yes('release_prompt:released', 'p1', 'release-2'), outcome='released')
        self.assertEqual([], self.life.eligible())
        self.assertNoCanon()

    def test_B01_approval_does_not_settle_head(self):
        c = self.ready()
        self.assertIsNone(self.adapter.call('B01', 'head', slot=c['slot']))
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'head'))
        self.assertEqual(c['id'], self.adapter.call('B01', 'head', slot=c['slot'])['id'])

    def test_B01_approve_requires_exact_media_and_air_permission(self):
        plan(self.life)
        render(self.life, 'clip-1', self.media)
        for auth in ({'approve': True}, yes('approve_air', 'clip-1', 'a', media_hash='0' * 64, manifest='bad')):
            with self.assertRaises(GuardError):
                self.adapter.call('B01', 'approve', clip_id='clip-1', authorization=auth)
        self.assertNoCanon()

    def test_B01_preemption_rejects_dropped_prompts_and_anchor_changes(self):
        text = self.prompt()
        old = plan(self.life, 'old', comments=[text])
        self.life.place('old', ['p1'])
        self.life.transition('old', 'queued')
        new = plan(self.life, 'new')
        auth = yes('preempt', 'old:new', 'preempt')
        with self.assertRaises(GuardError):
            self.life.preempt('old', 'new', auth)
        self.assertEqual('queued', self.life.snapshot()['clips']['old']['state'])

    def test_dependency_transitive_invalidation_before_settlement(self):
        plan(self.life, 'a')
        plan(self.life, 'b', dependencies=['a'])
        plan(self.life, 'c', dependencies=['b'])
        self.life.transition('b', 'queued')
        self.life.transition('c', 'queued')
        self.life.transition('a', 'failed', evidence={'reason': 'fixture failed'})
        for cid in ('b', 'c'):
            self.assertEqual(['a'], self.life.snapshot()['clips'][cid]['invalidated_by'])
            with self.assertRaises(GuardError):
                self.life.dispatch(cid)
        self.assertNoCanon()

    def test_unsettled_approved_dependency_cannot_dispatch(self):
        self.ready('a')
        plan(self.life, 'b', dependencies=['a'])
        self.life.transition('b', 'queued')
        c = self.life.snapshot()['clips']['b']
        batch = digest([self.life._manifest(c)])
        self.life.authorize_batch(['b'], yes('authorize_batch', batch, 'ab', ceiling_cents=0), 0)
        with self.assertRaises(GuardError):
            self.life.reserve_batch('ab')

    def test_D08_local_export_cannot_advance_episodes(self):
        result = self.adapter.call('D08', 'local_export', path=SEEDS / 'renders/SEED-S1_gen1_480p_parody.mp4')
        self.assertFalse(result['aired'])
        self.assertEqual(0, self.adapter.call('D08', 'episodes_done', channel='Ch4'))
        c = self.ready()
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'episode'))
        self.assertEqual(1, self.adapter.call('D08', 'episodes_done', channel='Ch4'))

    def test_D15_D10_proposals_commit_only_on_air_with_still(self):
        plan(self.life)
        patch = {'mood': 'resolute'}
        self.adapter.call('D15', 'propose', clip_id='clip-1', proposals=[dict(character_id='HERON', base_version=1,
            patch=patch, ref=self.ref, attestation=digest(patch), evidence='synthetic state-still review')])
        render(self.life, 'clip-1', self.media)
        c = approve(self.life, 'clip-1')
        self.assertEqual('watchful', self.life.snapshot()['cards']['HERON']['plastic']['mood'])
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'character'))
        card = self.life.snapshot()['cards']['HERON']
        self.assertEqual('resolute', card['plastic']['mood'])
        self.assertEqual(1, card['summon_count'])
        self.assertEqual(1, card['writein_level'])

    def test_D17_missing_or_unattested_still_rejects_entire_air(self):
        for bad in ('ref', 'attestation', 'base_version', 'locked'):
            with self.subTest(bad=bad):
                cid = 'bad-' + bad
                plan(self.life, cid)
                patch = {'mood': 'resolute'}
                p = dict(character_id='HERON', base_version=1, patch=patch, ref=self.ref,
                         attestation=digest(patch), evidence='fixture')
                if bad == 'locked':
                    p['patch'] = {'silhouette': 'changed'}
                else:
                    p[bad] = 'bad'
                self.life.propose(cid, proposals=[p])
                render(self.life, cid, self.media)
                c = approve(self.life, cid)
                with self.assertRaises(GuardError):
                    self.life.transition(cid, 'aired', evidence=self.life.verifier.issue(c, 'r-' + bad))
        self.assertNoCanon()

    def test_D16_incomplete_consequence_defaults_flash_and_expires(self):
        self.life.baseline_consequence({'id': 'old', 'text': 'rain-slick coat', 'tier': 'LEGEND', 'character_id': 'HERON'}, channel='Ch4')
        self.assertEqual('FLASH', self.life.snapshot()['consequences']['old']['tier'])
        c = self.ready()
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'expiry'))
        self.assertFalse(self.life.snapshot()['consequences']['old']['active'])

    def test_D16_each_tier_expires_at_its_scope(self):
        c = dict(since_index=1, episode=1, season=1)
        for tier, index, episode, season, expected in (
            ('FLASH', 1, 1, 1, True), ('FLASH', 2, 1, 1, False),
            ('SCAR', 2, 1, 1, True), ('SCAR', 3, 2, 1, False),
            ('MARK', 3, 2, 1, True), ('MARK', 4, 1, 2, False), ('LEGEND', 99, 99, 99, True), ('typo', 1, 1, 1, False)):
            with self.subTest(tier=tier, index=index):
                self.assertEqual(expected, alive(dict(c, tier=tier), index, episode, season))
        self.assertFalse(alive({'tier': 'LEGEND'}, 5, 1, 1))

    def test_D16_reuse_advances_exactly_one_tier_on_later_air(self):
        plan(self.life, 'first')
        self.life.propose('first', consequences=[dict(id='wet', text='rain-slick coat', character_id='HERON', ref=self.ref, evidence='fixture')])
        render(self.life, 'first', self.media)
        air(self.life, 'first')
        self.assertEqual('FLASH', self.life.snapshot()['consequences']['wet']['tier'])
        plan(self.life, 'second', comments=['rain-slick coat'])
        self.life.propose('second', reuses=[dict(id='wet', evidence='rain-slick coat', ref=self.ref)])
        render(self.life, 'second', self.media)
        self.assertEqual('FLASH', self.life.snapshot()['consequences']['wet']['tier'])
        air(self.life, 'second')
        self.assertEqual('SCAR', self.life.snapshot()['consequences']['wet']['tier'])
        self.assertTrue(self.life.snapshot()['consequences']['wet']['active'])
        plan(self.life, 'third', episode=2)
        render(self.life, 'third', self.media)
        air(self.life, 'third')
        self.assertFalse(self.life.snapshot()['consequences']['wet']['active'])

    def test_D12_every_continuity_failure_blocks_queue_and_consumption(self):
        cases = ({'depth': 3}, {'big_changes': 2}, {'state_so_far': ''}, {'cast': ['unknown']},
                 {'held_still': True}, {'end_mode': 'pinned', 'pin_reason': ''}, {'corner_tag': ''})
        text = self.prompt()
        for i, overrides in enumerate(cases):
            cid = 'gate-' + str(i)
            plan(self.life, cid, comments=[text], override=overrides)
            self.life.place(cid, ['p1'])
            with self.subTest(overrides=overrides), self.assertRaises(GuardError):
                self.adapter.call('D12', 'assemble', clip_id=cid)
            self.assertEqual('planned', self.life.snapshot()['clips'][cid]['state'])
        self.assertEqual('eligible', self.life.snapshot()['prompts']['p1']['status'])
        self.assertEqual(len(cases), len(self.life.snapshot()['problems']))

    def test_gate_rechecked_when_queued_clip_leaves_queue(self):
        plan(self.life, 'later', override={'depth': 1})
        self.life.transition('later', 'queued')
        for cid in ('away1', 'away2'):
            plan(self.life, cid, override={'depth': 1})
            render(self.life, cid, self.media)
            air(self.life, cid)
        c = self.life.snapshot()['clips']['later']
        batch = digest([self.life._manifest(c)])
        self.life.authorize_batch(['later'], yes('authorize_batch', batch, 'away-batch', ceiling_cents=0), 0)
        with self.assertRaises(GuardError):
            self.life.reserve_batch('away-batch')
        plan(self.life, 'home')
        render(self.life, 'home', self.media)
        air(self.life, 'home')
        self.life.reserve_batch('away-batch')

    def test_existing_Ch4_held_frame_prompt_is_rejected(self):
        from astra_lifecycle.continuity import failures
        raw = (SEEDS / 'prompts/SEED-S1.txt').read_text()
        c = plan(self.life)
        issues = failures(c['spec'], raw, self.life.snapshot()['cards'], 0)
        self.assertIn('no_held_still_ending', issues)

    def test_inventory_excludes_successful_seed_ids_and_approval_without_media(self):
        self.life.import_inventory([{'logical_id': 'SEED-S1', 'state': 'rendered', 'evidence': 'existing lineage'},
                                    {'logical_id': 'approved-missing', 'state': 'approved', 'evidence': 'fixture approval record'}])
        self.assertTrue(self.life.inventory_excluded('SEED-S1'))
        self.assertTrue(self.life.inventory_excluded('approved-missing'))
        self.assertNoCanon()
        c = plan(self.life)
        render(self.life, c['id'], self.media)
        self.life.transition(c['id'], 'pulled', evidence={'reason': 'fixture'})
        self.assertTrue(self.life.inventory_excluded(c['logical_id']))

    def test_inventory_duplicate_logical_content_refused_at_queue(self):
        c = plan(self.life)
        self.life.transition(c['id'], 'queued')
        self.life.plan('dup', logical_id=c['logical_id'], slot='dup-slot', lineage='dup-lineage', prompt=c['prompt'],
                       reference_hashes=c['reference_hashes'], spec=c['spec'])
        with self.assertRaises(GuardError):
            self.life.transition('dup', 'queued')

    def test_dollar_string_is_not_authorization(self):
        plan(self.life)
        self.life.transition('clip-1', 'queued')
        with self.assertRaises(GuardError):
            self.life.authorize_batch(['clip-1'], 'yes $5', 500)
        self.assertEqual({}, self.life.snapshot()['reservations'])

    def test_approval_binds_exact_batch_price_prompt_and_reference_hashes(self):
        plan(self.life)
        self.life.transition('clip-1', 'queued')
        c = self.life.snapshot()['clips']['clip-1']
        m = self.life._manifest(c)
        for key, value in (('prompt_hash', '0' * 64), ('reference_hashes', ['0' * 64]), ('price_cents', 100)):
            bad = deepcopy(m)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(GuardError):
                self.life.authorize_batch(['clip-1'], yes('authorize_batch', digest([bad]), 'bad-' + key, ceiling_cents=0), 0)
        with self.assertRaises(GuardError):
            self.life.authorize_batch(['clip-1'], yes('authorize_batch', digest([m]), 'ceiling', ceiling_cents=1), 0)

    def test_cap_reservation_and_dispatch_idempotency(self):
        self.life.set_fixture_budget(100)
        plan(self.life, price_cents=100)
        self.life.transition('clip-1', 'queued')
        c = self.life.snapshot()['clips']['clip-1']
        batch = digest([self.life._manifest(c)])
        self.life.authorize_batch(['clip-1'], yes('authorize_batch', batch, 'cap', ceiling_cents=100), 100)
        self.life.reserve_batch('cap')
        self.life.reserve_batch('cap')
        self.assertEqual(1, len(self.life.snapshot()['reservations']))
        self.assertEqual(0, self.life.dispatch('clip-1')['spent_cents'])
        with self.assertRaises(GuardError):
            self.life.dispatch('clip-1')
        plan(self.life, 'over', price_cents=1)
        self.life.transition('over', 'queued')
        c = self.life.snapshot()['clips']['over']
        batch = digest([self.life._manifest(c)])
        self.life.authorize_batch(['over'], yes('authorize_batch', batch, 'over-cap', ceiling_cents=1), 1)
        with self.assertRaises(GuardError):
            self.life.reserve_batch('over-cap')

    def test_dispatch_without_approval_or_wrong_lifecycle_fails(self):
        plan(self.life)
        with self.assertRaises(GuardError):
            self.life.dispatch('clip-1')
        self.life.transition('clip-1', 'queued')
        with self.assertRaises(GuardError):
            self.life.dispatch('clip-1')
        with self.assertRaises(GuardError):
            self.life.transition('clip-1', 'rendered', evidence={'asset_hash': self.media})

    def test_changed_reference_bytes_block_dispatch(self):
        local = self.tmp / 'state-still.png'
        shutil.copyfile(SEEDS / 'renders/SEED-S1_last.png', local)
        self.life.add_asset(local, evidence='copy fixture')  # same hash replaces registry path
        plan(self.life)
        self.life.transition('clip-1', 'queued')
        local.write_bytes(b'changed')
        with self.assertRaises(GuardError):
            self.life.dispatch('clip-1')

    def test_price_rejects_bool_negative_nan(self):
        for value in (True, -1, float('nan'), 1.5):
            with self.subTest(value=value), self.assertRaises(GuardError):
                plan(self.life, price_cents=value)

    def test_registry_and_cheapest_compatible_post_air_fix(self):
        c = self.ready()
        with self.assertRaises(GuardError):
            self.life.watch_after_air(c['id'], 'seam pop', 'fixture seam', ['overlap_frames'])
        self.life.transition(c['id'], 'aired', evidence=self.life.verifier.issue(c, 'seam'))
        row = self.life.watch_after_air(c['id'], 'seam pop', 'fixture seam', ['overlap_frames', 'cheaper_fixes_exhausted'])
        self.assertEqual('zipper', row['fix_id'])
        row = self.life.watch_after_air(c['id'], 'seam pop', 'fixture seam', ['overlap_frames', 'identity_mismatch'])
        self.assertIsNone(row['fix_id'])
        self.assertEqual('proposed', self.life.snapshot()['fix_queue'][-1]['status'])

    def test_meta_versions_alias_swap_and_older_clip_readability(self):
        self.life.version_metadata('look-v1', {'style': 'legacy'})
        self.life.version_metadata('look-v2', {'style': 'current'})
        with self.assertRaises(GuardError):
            self.life.swap_alias('look-v1', 'look-v2')
        self.life.swap_alias('look-v1', 'look-v2', reason='scaffolding revision')
        self.assertEqual('current', self.life.read_metadata('look-v1')['fields']['style'])
        self.assertEqual('legacy', self.life.read_metadata('look-v1', version=1)['fields']['style'])
        with self.assertRaises(GuardError):
            self.life.swap_alias('look-v2', 'look-v1', reason='cycle')

    def test_character_crossover_boundary_requires_consecutive_aired_episode_change(self):
        other = deepcopy(self.life.read_card('HERON', version=1))
        other.update(id='HERON-test', name='HERON-test')
        self.life.baseline_card(other)
        for cid, episode in (('a', 1), ('b', 2)):
            plan(self.life, cid, episode=episode)
            render(self.life, cid, self.media)
            air(self.life, cid)
        self.life.swap_alias('HERON', 'HERON-test', reason='offline crossover test', crossover_test=True, boundary=['a', 'b'])
        self.assertEqual('HERON-test', self.life.read_card('HERON')['id'])
        self.assertEqual('HERON', self.life.read_card('HERON', version=1)['id'])

    def test_contributor_handles_never_enter_generation_prompt(self):
        text = self.prompt(text='@fixture-viewer says go')
        plan(self.life, comments=[text])
        with self.assertRaises(GuardError):
            self.life.place('clip-1', ['p1'])
        self.assertEqual(text, self.life.snapshot()['prompts']['p1']['original_text'])

    def test_recipe_beat_density_actions_sentiment_and_style_trigger(self):
        card = self.life.snapshot()['cards']['HERON']
        self.assertLess(len(brief(card).split()), 20)
        c = plan(self.life)
        self.assertNotIn('Correct detected style drift', c['prompt'])
        self.assertIn('cheers', sentiment('great work'))
        self.assertIn('recoils', sentiment('stop now'))
        with self.assertRaises(GuardError):
            assemble(cards=[card], state_so_far='at home', beats=[{'t': 1, 'who': 'HERON'}])
        with self.assertRaises(GuardError):
            assemble(cards=[card], state_so_far='at home', beats=[], comments=[{'t': 1, 'original_text': 'yes'}, {'t': 2, 'original_text': 'no'}])

    def test_all_machine_adapters_reject_direct_legacy_setters(self):
        for machine in MACHINES:
            with self.subTest(machine=machine), self.assertRaises(GuardError):
                self.adapter.call(machine, 'set_state', state='aired')
        for name in ('mark_consumed', 'set_state', 'combine', 'approve', 'rollback', 'tier_alive'):
            with self.subTest(name=name), self.assertRaises(GuardError):
                read_pure(name)

    def test_existing_pure_scoring_and_timing_behavior_preserved(self):
        similarity, proof = read_pure('similarity')
        a = {'show': 'BLACK ICE', 'text': 'HERON carries microfilm across bridge'}
        self.assertEqual(1, similarity(a, a))
        self.assertEqual(0, similarity(a, {'show': 'other', 'text': a['text']}))
        self.assertEqual(64, len(proof['ast_digest']))
        times, _ = read_pure('beat_times')
        self.assertEqual([1.0, 4.0, 7.0], times(3, 8, {'beat_start_s': 1, 'beat_end_margin_s': 1}))

    def test_B15_no_scheduler_dependency_and_ads_stay_separate(self):
        self.prompt()
        self.assertEqual('p1', self.adapter.call('B15', 'eligible')[0]['id'])
        plan(self.life, 'ad', kind='house_ad')
        with self.assertRaises(GuardError):
            self.life.propose('ad', consequences=[{'id': 'illegal'}])
        render(self.life, 'ad', self.media)
        air(self.life, 'ad')
        self.assertNoCanon()
        self.assertEqual('aired', self.life.snapshot()['clips']['ad']['state'])

    def test_snapshot_is_detached_and_writes_stay_scoped(self):
        s = self.life.snapshot()
        s['cards']['HERON']['plastic']['mood'] = 'corrupted'
        self.assertEqual('watchful', self.life.snapshot()['cards']['HERON']['plastic']['mood'])
        with self.assertRaises(GuardError):
            Lifecycle('/tmp/disallowed-astra.sqlite')


if __name__ == '__main__':
    unittest.main()
