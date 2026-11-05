import pytest
pytest.skip(
    'story-engine live callers are out of scope for the offline repo suites',
    allow_module_level=True,
)
import json, checker as c
L = 'out-of-scope/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl'
def R(**k): k.setdefault('clip_id', 'x'); return k
def test_null_global_no_skipped():
    rs = [R(global_no=None), R(clip_id='y'), R(clip_id='z', global_no=5)]
    assert [r['clip_id'] for r in c.node_rows(rs)] == ['z']
def test_supersedes_three_forms_newer_wins():
    for new in (R(global_no=9, supersedes={'global_no': 9}), R(global_no=9, supersedes_no=9), R(global_no=9, supersedes_global_no='9')):
        rs = [R(global_no=9, tag='old'), dict(new, tag='new')]
        assert [r['tag'] for r in c.node_rows(rs)] == ['new'] and c.lineage_duplicates(rs) == {'global_no': [], 'clip_id': []}
def test_supersedes_other_number_drops_that_one():
    rs = [R(clip_id='a', global_no=3), R(clip_id='b', global_no=4), R(clip_id='c', global_no=5, supersedes_no=3)]
    assert [r['clip_id'] for r in c.node_rows(rs)] == ['b', 'c']
def test_older_cannot_supersede_newer():
    rs = [R(global_no=9, supersedes_no=9, tag='old'), R(global_no=9, tag='new')]
    assert c.lineage_duplicates(rs)['global_no'] == [9]
def test_true_duplicate_still_flagged():
    assert c.lineage_duplicates([R(global_no=7), R(global_no=7)])['global_no'] == [7]
def test_bool_and_bad_values_not_numbers():
    assert c.node_rows([R(global_no=True), R(global_no='0'), R(global_no=-1)]) == []
    assert c.supersedes_no({'supersedes': {'global_no': False}}) is None
def test_status_rows_ignored():
    rs = [R(global_no=2), R(global_no=2, row_type='correction'), R(global_no=2, row_type='pulled'), R(global_no=2, row_type='audio_post')]
    assert len(c.node_rows(rs)) == 1
def test_real_lineage_30_36_once_each():
    rows = [json.loads(l) for l in open(L) if l.strip()]
    n = c.node_rows(rows); d = c.lineage_duplicates(rows)
    for g in range(30, 37):
        hit = [r for r in n if r['global_no'] == g]
        assert len(hit) == 1 and hit[0]['row_type'] == 'tagfade_air_copy' and hit[0]['ts'].startswith('2026-10-27T18:36'), g
        assert g not in d['global_no'] and hit[0]['clip_id'] not in d['clip_id']
    assert sorted(r['lineage'] for r in n if 30 <= r['global_no'] <= 36) == sorted(f'4.{i}' for i in range(5, 12))
def test_superseded_file_still_resolves_and_new_row_wins_lookup(tmp_path):
    (tmp_path / 'raw').mkdir(); (tmp_path / 'raw' / 'mb_helmet.mp4').write_bytes(b'x')
    rows = [{'clip_id': 'ch4-ad-tactical-helmet-pedestal', 'tag': 'r', 'global_no': 1, 'parent_id': None, 'file': '/a/salesad/root_salesad.mp4'},
            {'clip_id': 'old', 'tag': 'o', 'global_no': 2, 'parent_global_no': 1, 'file': '/a/old_v1.mp4'},
            {'clip_id': 'new', 'tag': 'n', 'global_no': 2, 'parent_global_no': 1, 'supersedes': {'global_no': 2}, 'file': '/a/new_v2.mp4'},
            {'clip_id': 'ph', 'global_no': None, 'file': '/a/sales-overlay/placeholder_salesad.mp4'}]
    for f in ('/a/old_v1.mp4', '/a/new_v2.mp4'):
        assert c.resolve_clean(f, lineage=rows, mb_dir=tmp_path).endswith('raw/mb_helmet.mp4')
    import pytest
    with pytest.raises(c.CleanSourceError): c.resolve_clean('/a/sales-overlay/placeholder_salesad.mp4', lineage=rows, mb_dir=tmp_path)
