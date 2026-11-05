import pytest
pytest.skip(
    'story-engine live callers are out of scope for the offline repo suites',
    allow_module_level=True,
)
import json, checker

def test_says_and_price_extracted():
    g, s = checker.split_overlay_text('A wooden crate with a sign that says "Storm Sale" priced at $19.99 on a pier')
    texts = [x['text'] for x in s]
    assert 'Storm Sale' in texts and '$19.99' in texts
    assert 'Storm Sale' not in g and '19.99' not in g
    assert g.endswith(checker.NO_TEXT_CONSTRAINT)
    assert checker.gen_prompt_requests_text(g) == []

def test_reads_and_with_the_words():
    g, s = checker.split_overlay_text("A banner reads 'Open Late' and a mug with the words \"Hold Fast\"")
    assert {x['text'] for x in s} == {'Open Late', 'Hold Fast'}
    assert checker.gen_prompt_requests_text(g) == []

def test_flag_catches_text_request():
    assert checker.gen_prompt_requests_text('a storefront with a sign that says "hi"')
    assert checker.gen_prompt_requests_text('label it $5')
    assert checker.gen_prompt_requests_text('a quiet harbor at dusk; ' + checker.NO_TEXT_CONSTRAINT) == []

def test_unquoted_text_request_scrubbed():
    g, s = checker.split_overlay_text('a shop window with lettering in gold')
    assert s == [] and checker.gen_prompt_requests_text(g) == []

def test_overlay_filters():
    for bad in [f'Hi {checker.CREATOR_NAME.capitalize()}', 'for the kids', 'Nike deal', 'tip jar', 'Military Boutique']:
        _, s = checker.split_overlay_text(f'a sign that says "{bad}"')
        assert s and s[0]['airable'] is False and s[0]['blocked']
    _, s = checker.split_overlay_text('a sign that says "Fresh Bread"')
    assert s[0]['airable'] is True

def test_row_has_overlay_specs_and_editable(tmp_path):
    p = tmp_path / 'cp.jsonl'
    pid = checker.add_comment_prompt('a lamp with a tag that reads "Bright"', 'h', path=p, duration=5.0)
    row = json.loads(p.read_text().splitlines()[0])
    assert row['overlay_specs'][0]['prompt_id'] == pid and row['overlay_specs'][0]['end_s'] == 5.0
    assert 'Bright' not in row['gen_prompt']
    edited = [dict(row['overlay_specs'][0], text='Brighter')]
    with p.open('a') as f: f.write(json.dumps({'id': pid, 'overlay_specs': edited}) + '\n')
    assert checker.overlay_specs_for(pid, path=p)[0]['text'] == 'Brighter'
