import pytest
pytest.skip(
    'story-engine live callers are out of scope for the offline repo suites',
    allow_module_level=True,
)
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker

def _setup(tmp_path):
    pf = tmp_path / 'COMMENT-PROMPTS.jsonl'
    a = checker.add_comment_prompt('Osmund checks the supply bay', '@fogfan', pf)
    root = {'lineage': '4.3', 'gen': 1, 'global_no': 58, 'parent_global_no': None, 'prompt_ids': [a], 'ready': True, 'approved': True, 'slot_id': 'ch4-S3', 'anchors': ['A.jpg', 'B.jpg']}
    slot = {'slot_id': 'ch4-S3', 'lineage': '4.3', 'root': 58, 'head': 58, 'anchors': ['A.jpg', 'B.jpg']}
    return pf, root, slot

def test_supersede_keeps_all_prompt_rows(tmp_path):
    pf, root, slot = _setup(tmp_path)
    before = pf.read_text()
    b = checker.add_comment_prompt('Tim uses his optic as a flashlight', '@timlover', pf)
    v = checker.new_version(root, 64, 'ch4-S3', [b]); v['anchors'] = ['A.jpg', 'B.jpg']
    vs = [root]; checker.approve(slot, vs, v, '2026-10-27T18:05-05:00')
    assert pf.read_text().startswith(before) and len(pf.read_text().splitlines()) == 2
    assert v['prompt_ids'] == root['prompt_ids'] + [b]
    assert root['status'] == 'superseded' and root['superseded_by'] == 64 and root in vs
    assert checker.slot_head(slot, vs)['global_no'] == 64
    assert checker.preemption_fails(slot, vs, pf) == []

def test_rollback_moves_head_back(tmp_path):
    pf, root, slot = _setup(tmp_path)
    v = checker.new_version(root, 64, 'ch4-S3'); vs = [root]
    checker.approve(slot, vs, v, 'now'); checker.rollback(slot, vs)
    assert slot['head'] == 58 and checker.slot_head(slot, vs)['global_no'] == 58 and len(vs) == 2

def test_unapproved_new_version_not_played(tmp_path):
    pf, root, slot = _setup(tmp_path)
    v = checker.new_version(root, 64, 'ch4-S3'); vs = [root, v]; slot['head'] = 64
    assert checker.slot_head(slot, vs)['global_no'] == 58

def test_dropped_prompt_and_anchor_drift_flagged(tmp_path):
    pf, root, slot = _setup(tmp_path)
    v = checker.new_version(root, 64, 'ch4-S3'); v['prompt_ids'] = []; v['anchors'] = ['X.jpg', 'B.jpg']
    errs = checker.preemption_fails(slot, [root, v], pf)
    assert any('dropped' in e for e in errs) and any('anchors' in e for e in errs)
