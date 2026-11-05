from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from astra_lifecycle import Lifecycle, GuardError, digest, file_hash
from astra_lifecycle.contracts import ROOT
from astra_lifecycle.demo import run
from astra_lifecycle.fixture import setup, plan, render, air, approve, yes
from astra_lifecycle.schemas import schema


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / 'runtime', prefix='contract-'))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_entire_ch4_cycle_and_persisted_snapshot_validate(self):
        state = run(self.tmp / 'cycle')
        validator = Draft202012Validator(schema(), format_checker=FormatChecker())
        validator.validate(state)
        self.assertEqual(1, len(state['commits']))
        self.assertEqual(1, len(state['receipts']))
        self.assertFalse(state['consequences']['old-rain']['active'])
        self.assertEqual('eligible', state['prompts']['ch4-comment-unseen']['status'])
        self.assertEqual('pulled', state['prompts']['ch4-comment-unseen']['attempts'][0]['status'])
        self.assertEqual(state, json.loads((self.tmp / 'cycle/state.json').read_text()))
        history = state['card_history']['HERON']
        self.assertEqual('watchful', history[0]['plastic']['mood'])
        self.assertEqual('resolute', history[-1]['plastic']['mood'])
        sidecar = self.tmp / 'cycle/media.sidecar.json'
        tags = (self.tmp / 'cycle/media.ffmetadata').read_text()
        self.assertIn('astra_sidecar_sha256=' + file_hash(sidecar), tags)
        self.assertEqual('offline-fixture', json.loads(sidecar.read_text())['mode'])

    def test_schema_artifacts_current_and_valid(self):
        for kind, name in (('snapshot', 'records.schema.json'), ('clip', 'lifecycle.schema.json'), ('receipt', 'playback-receipt.schema.json')):
            data = json.loads((ROOT / 'schemas' / name).read_text())
            self.assertEqual(schema(kind), data)
            Draft202012Validator.check_schema(data)

    def test_schema_rejects_terminal_reset_and_malformed_receipt(self):
        validator = Draft202012Validator(schema('receipt'), format_checker=FormatChecker())
        for bad in ({'air_yes': True}, {'verified': True}, {'id': 'r', 'timestamp': 'not-a-timestamp'}):
            with self.assertRaises(ValidationError):
                validator.validate(bad)
        clip_validator = Draft202012Validator(schema('clip'))
        with self.assertRaises(ValidationError):
            clip_validator.validate({'state': 'WAITING'})
        life = Lifecycle(self.tmp / 'rejected-candidate.sqlite')
        setup(life)
        plan(life, override={'depth': 3, 'state_so_far': ''})
        with self.assertRaises(GuardError):
            life.transition('clip-1', 'queued')
        # Failed candidates remain durable and schema-readable for diagnosis.
        Draft202012Validator(schema(), format_checker=FormatChecker()).validate(life.snapshot())

    def test_new_consequence_cannot_start_at_legend(self):
        life = Lifecycle(self.tmp / 'state.sqlite')
        ref, media = setup(life)
        plan(life)
        life.propose('clip-1', consequences=[dict(id='jump', text='instant canon', tier='LEGEND',
            since_index=0, episode=1, season=1, character_id='HERON', ref=ref, evidence='fixture')])
        render(life, 'clip-1', media)
        c = approve(life, 'clip-1')
        with self.assertRaises(GuardError):
            life.transition(c['id'], 'aired', evidence=life.verifier.issue(c, 'jump'))
        self.assertEqual([], life.snapshot()['commits'])

    def test_repeated_reuse_cannot_jump_two_tiers(self):
        life = Lifecycle(self.tmp / 'state.sqlite')
        ref, media = setup(life)
        life.baseline_consequence(dict(id='c', text='wet coat', character_id='HERON'), channel='Ch4')
        plan(life, comments=['wet coat'])
        r = dict(id='c', evidence='wet coat', ref=ref)
        life.propose('clip-1', reuses=[r, r])
        render(life, 'clip-1', media)
        c = approve(life, 'clip-1')
        with self.assertRaises(GuardError):
            life.transition(c['id'], 'aired', evidence=life.verifier.issue(c, 'double'))
        self.assertEqual('FLASH', life.snapshot()['consequences']['c']['tier'])

    def test_versioned_layer_cannot_be_changed_outside_boundary(self):
        life = Lifecycle(self.tmp / 'state.sqlite')
        life.version_metadata('style-v1', {'style': 'locked'})
        with self.assertRaises(GuardError):
            life.version_metadata('style-v1', {'style': 'drift'})
        self.assertEqual('locked', life.read_metadata('style-v1')['fields']['style'])

    def test_successful_preemption_preserves_prompt_and_records_attempt(self):
        life = Lifecycle(self.tmp / 'state.sqlite')
        setup(life)
        text = 'keep moving'
        life.intake('p', text, 'fixture-contributor')
        life.filter_prompt('p', allowed=True, reason='fixture')
        old = plan(life, 'old', comments=[text])
        life.place('old', ['p'])
        life.transition('old', 'queued')
        life.plan('new', logical_id='fixture/new', slot=old['slot'], lineage='new-lineage', prompt=old['prompt'],
                  reference_hashes=old['reference_hashes'], spec=old['spec'])
        life.place('new', ['p'])
        life.preempt('old', 'new', yes('preempt', 'old:new', 'replace'))
        self.assertEqual('pulled', life.snapshot()['clips']['old']['state'])
        self.assertEqual('eligible', life.snapshot()['prompts']['p']['status'])
        self.assertEqual('pulled', life.snapshot()['prompts']['p']['attempts'][0]['status'])
        self.assertFalse(life.snapshot()['ledger'][0]['aired'])

    def test_rendered_appearance_logged_before_air_without_consumption(self):
        life = Lifecycle(self.tmp / 'state.sqlite')
        _, media = setup(life)
        life.intake('p', 'keep moving', 'fixture-contributor')
        life.filter_prompt('p', allowed=True, reason='fixture')
        plan(life, comments=['keep moving'])
        life.place('clip-1', ['p'])
        render(life, 'clip-1', media)
        life.observe('clip-1', 'p', 'HERON keeps moving', score=.8, evidence='fixture')
        s = life.snapshot()
        self.assertFalse(s['ledger'][0]['aired'])
        self.assertEqual('eligible', s['prompts']['p']['status'])
        air(life, 'clip-1')
        self.assertEqual(1, len(life.snapshot()['ledger']))
        self.assertTrue(life.snapshot()['ledger'][0]['aired'])


if __name__ == '__main__':
    unittest.main()
