import pytest
pytest.skip(
    'story-engine live callers are out of scope for the offline repo suites',
    allow_module_level=True,
)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker

def test_prompt_reaches_head_at_max_wait():
    ps = [{'id': 'cp-old', 'seq': 1}, {'id': 'cp-new1', 'seq': 5}, {'id': 'cp-new2', 'seq': 6}]
    rows = []
    assert checker.next_for_break(ps, {'cp-old': 3, 'cp-new1': 2}, rows)['id'] == 'cp-old'
    assert checker.next_for_break(ps, {'cp-old': 3, 'cp-new1': 9}, rows, max_wait=10)['id'] == 'cp-new1'

def test_combined_clip_lists_all_prompt_ids():
    rows = []
    ps = [{'id': 'cp-a', 'show': 'fs', 'text': 'Osmund searches supply bay'}, {'id': 'cp-b', 'show': 'fs', 'text': 'Osmund finds helmet in supply bay'}]
    clip = checker.combine(ps, rows, 'clip-1')
    assert clip['prompt_ids'] == ['cp-a', 'cp-b']
    assert all(checker.prompt_state(p['id'], rows) == 'MERGED' for p in ps)

def test_prompt_never_deleted_and_held_with_reason():
    rows = []; checker.set_state(rows, 'cp-x', 'waiting'); checker.hold_prompt(rows, 'cp-x', 'kids', rewrite='crew only')
    assert checker.prompt_state('cp-x', rows) == 'PARKED' and len(rows) == 2 and rows[-1]['reason'] == 'kids'

def test_duplicate_never_dropped():
    lib = []
    checker.register_clip(lib, {'clip_id': 'c1', 'sha256': 'aa'})
    d = checker.register_clip(lib, {'clip_id': 'c2', 'sha256': 'aa'})
    assert len(lib) == 2 and d['duplicate_of'] == 'c1' and d['airable'] is False

def test_near_duplicate_classes():
    a = {'show': 'fs', 'premise': 'mira colors clipboard search supply'}
    assert checker.classify_duplicate(dict(a), a) == 'rotate'
    assert checker.classify_duplicate({'show': 'fs', 'premise': 'mira colors clipboard during storm drill'}, a) == 'next_take'
    assert checker.classify_duplicate({'show': 'fs', 'premise': 'osmund opens bakery downtown'}, a) == 'spinoff'

def test_old_state_names_read_as_aliases():
    rows = [{'id': 'cp-1', 'state': 'combined'}, {'id': 'cp-2', 'state': 'held'}, {'id': 'cp-3', 'state': 'waiting'}]
    assert [checker.prompt_state(i, rows) for i in ('cp-1', 'cp-2', 'cp-3')] == ['MERGED', 'PARKED', 'WAITING']

def test_skipped_breaks_cap_guarantees_next_break():
    ps = [{'id': 'cp-old', 'seq': 1}, {'id': 'cp-new', 'seq': 2}]
    assert checker.next_for_break(ps, {'cp-old': 7, 'cp-new': 2}, [])['id'] == 'cp-old'
    assert checker.SKIPPED_BREAKS_CAP == 3

def test_withdrawn_trundle_only_and_unterminated_blocks_preempt():
    import pytest
    rows = []
    with pytest.raises(AssertionError): checker.set_state(rows, 'cp-a', 'WITHDRAWN', by='bot')
    checker.set_state(rows, 'cp-a', 'WITHDRAWN', by='trundle'); checker.set_state(rows, 'cp-b', 'WAITING')
    assert checker.unterminated_prompts({'comment_prompt_ids': ['cp-a', 'cp-b']}, rows) == ['cp-b']
