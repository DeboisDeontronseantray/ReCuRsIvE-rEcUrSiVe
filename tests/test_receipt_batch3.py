"""Trusted playback receipts are the only new way to air. Offline, no playout client."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from astra_lifecycle.adapters import Adapters
from astra_lifecycle.contracts import GuardError
from astra_lifecycle.fixture import approve, plan, render, setup
from astra_lifecycle.lifecycle import Lifecycle
from astra_lifecycle.trusted_receipt import (
    FIELDS, apply_playback_receipt, sign_playback_receipt, verify_playback_receipt,
)

REPO = Path(__file__).resolve().parents[1]
SCHEMA = REPO / 'schemas' / 'trusted-playback-receipt.schema.json'


def _iso(delta):
    return (datetime.now(timezone.utc) + delta).isoformat()


def _fields(item_id='item-1', nonce='nonce-1', playout_id='offline-playout-1', *, start=None, end=None):
    return {
        'item_id': item_id,
        'channel': 'Ch4',
        'start': start or _iso(timedelta(minutes=-5)),
        'end': end or _iso(timedelta(minutes=30)),
        'playout_id': playout_id,
        'nonce': nonce,
    }


@pytest.fixture
def approved():
    folder = TemporaryDirectory(dir=Path(__file__).resolve().parent, prefix='receipt-batch3-')
    life = Lifecycle(Path(folder.name) / 'state.sqlite')
    _ref, media = setup(life)
    plan(life, 'item-1')
    render(life, 'item-1', media)
    approve(life, 'item-1')
    life.media = media
    yield life
    folder.cleanup()


def test_schema_lists_the_trusted_receipt_fields():
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    assert schema['required'] == list(FIELDS)
    assert schema['additionalProperties'] is False


def test_valid_receipt_airs_the_approved_item(approved):
    receipt = sign_playback_receipt(_fields())
    aired = apply_playback_receipt(approved, receipt)
    assert aired['state'] == 'aired'
    assert approved.snapshot()['clips']['item-1']['state'] == 'aired'
    assert len(approved.snapshot()['commits']) == 1


def test_bad_signature_is_rejected(approved):
    receipt = sign_playback_receipt(_fields())
    receipt['signature'] = '0' * 64
    with pytest.raises(GuardError, match='bad signature'):
        apply_playback_receipt(approved, receipt)
    assert approved.snapshot()['clips']['item-1']['state'] == 'approved'


def test_replayed_nonce_is_rejected(approved):
    apply_playback_receipt(approved, sign_playback_receipt(_fields()))
    plan(approved, 'item-2')
    render(approved, 'item-2', approved.media)
    approve(approved, 'item-2')
    replay = sign_playback_receipt(_fields('item-2', playout_id='other-playout'))
    with pytest.raises(GuardError, match='replayed nonce'):
        apply_playback_receipt(approved, replay)
    assert approved.snapshot()['clips']['item-2']['state'] == 'approved'


def test_wrong_state_is_rejected(approved):
    plan(approved, 'item-2')
    render(approved, 'item-2', approved.media)
    with pytest.raises(GuardError, match='wrong state'):
        apply_playback_receipt(approved, sign_playback_receipt(_fields('item-2', nonce='nonce-2')))
    assert approved.snapshot()['clips']['item-2']['state'] == 'rendered'


def test_unknown_item_is_rejected(approved):
    with pytest.raises(GuardError, match='unknown item'):
        apply_playback_receipt(approved, sign_playback_receipt(_fields('missing-item', nonce='nonce-9')))
    assert 'missing-item' not in approved.snapshot()['clips']


def test_expired_receipt_is_rejected(approved):
    receipt = sign_playback_receipt(_fields(
        start=_iso(timedelta(hours=-2)), end=_iso(timedelta(hours=-1))))
    with pytest.raises(GuardError, match='expired receipt'):
        apply_playback_receipt(approved, receipt)
    assert approved.snapshot()['clips']['item-1']['state'] == 'approved'


def test_direct_aired_without_a_receipt_fails(approved):
    with pytest.raises(GuardError):
        approved.transition('item-1', 'aired')
    with pytest.raises(GuardError):
        Adapters(approved).call('D09', 'aired', clip_id='item-1')
    assert approved.snapshot()['clips']['item-1']['state'] == 'approved'


def test_repeat_delivery_is_a_no_op(approved):
    receipt = sign_playback_receipt(_fields())
    apply_playback_receipt(approved, receipt)
    snap = approved.snapshot()
    version = snap['clips']['item-1']['version']
    commits = len(snap['commits'])
    again = apply_playback_receipt(approved, receipt)
    after = approved.snapshot()
    assert again['state'] == 'aired'
    assert after['clips']['item-1']['state'] == 'aired'
    assert after['clips']['item-1']['version'] == version
    assert len(after['commits']) == commits
    assert len(after['receipts']) == 1


def test_key_comes_from_env_or_the_fixture_file(approved, monkeypatch):
    monkeypatch.setenv('TT_PLAYBACK_RECEIPT_KEY', 'env-only-test-key')
    signed = sign_playback_receipt(_fields(nonce='env-nonce'))
    verify_playback_receipt(signed)
    monkeypatch.delenv('TT_PLAYBACK_RECEIPT_KEY', raising=False)
    with pytest.raises(GuardError, match='bad signature'):
        verify_playback_receipt(signed)
    fixture_signed = sign_playback_receipt(_fields(nonce='file-nonce'))
    verify_playback_receipt(fixture_signed)
