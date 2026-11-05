"""Trusted offline playback receipts. Air requires one verified receipt.

The test key comes from TT_PLAYBACK_RECEIPT_KEY or fixtures/playback/test_key.txt.
This module does not call playout, the network, or a live registry.
"""
import hmac
import hashlib
import os
from datetime import datetime, timezone

from .contracts import ROOT, GuardError, canonical, digest, require, timestamp

ENV_KEY = 'TT_PLAYBACK_RECEIPT_KEY'
KEY_PATH = ROOT / 'fixtures' / 'playback' / 'test_key.txt'
FIELDS = ('item_id', 'channel', 'start', 'end', 'playout_id', 'nonce', 'signature')
BODY = FIELDS[:-1]


class TrustedNoop:
    """The same verified receipt was already applied."""


def load_test_key():
    override = os.environ.get(ENV_KEY, '').strip()
    if override:
        return override.encode()
    require(KEY_PATH.is_file(), 'playback test key fixture missing')
    key = KEY_PATH.read_text(encoding='utf-8').strip()
    require(bool(key), 'playback test key fixture is empty')
    return key.encode()


def _body(receipt):
    return {name: receipt[name] for name in BODY}


def _signature(body, key):
    return hmac.new(key, canonical(body).encode(), hashlib.sha256).hexdigest()


def _token(verified):
    return verified['nonce'] + ':' + digest(_body(verified))


def sign_playback_receipt(fields, *, key=None):
    """Return a closed receipt. `fields` omits the signature."""
    require(isinstance(fields, dict), 'playback receipt must be an object')
    require(set(fields) == set(BODY), 'playback receipt fields required')
    body = _body(fields)
    _check_window(body)
    return body | {'signature': _signature(body, key or load_test_key())}


def verify_playback_receipt(receipt, *, key=None):
    """Check the closed schema, HMAC, and expiry. State and replay are separate."""
    require(isinstance(receipt, dict) and set(receipt) == set(FIELDS), 'closed playback receipt required')
    for name in BODY:
        require(isinstance(receipt[name], str) and receipt[name].strip(), 'invalid receipt ' + name)
    _check_window(receipt)
    require(datetime.now(timezone.utc) <= timestamp(receipt['end']), 'expired receipt')
    expected = _signature(_body(receipt), key or load_test_key())
    require(hmac.compare_digest(str(receipt.get('signature', '')), expected), 'bad signature')
    return _body(receipt)


def _check_window(receipt):
    start = timestamp(receipt['start'])
    end = timestamp(receipt['end'])
    require(end > start, 'invalid playback window')


def _nonce_seen(state, nonce):
    prefix = nonce + ':'
    return any(str(rid).startswith(prefix) for rid in state['receipts'])


def adapt_trusted_receipt(life, state, clip, evidence):
    """Turn a trusted receipt into the fixture receipt the aired edge already stores.

    Fixture receipts pass through unchanged. A repeat of the same trusted receipt
    is a no-op. Every other trusted receipt raises.
    """
    if not (isinstance(evidence, dict) and 'nonce' in evidence and 'playout_id' in evidence):
        return evidence
    verified = verify_playback_receipt(evidence)
    require(verified['item_id'] == clip['id'], 'unknown item')
    require(verified['channel'] == clip['channel'], 'receipt channel mismatch')
    token = _token(verified)
    stored = state['receipts'].get(token)
    if clip['state'] == 'aired' and stored and stored.get('clip_id') == clip['id']:
        return TrustedNoop()
    if _nonce_seen(state, verified['nonce']):
        raise GuardError('replayed nonce')
    require(clip['state'] == 'approved', 'wrong state')
    return life.verifier.issue(clip, token)


def apply_playback_receipt(life, receipt):
    """Verify a trusted receipt and air that item, or no-op if it was already applied."""
    verified = verify_playback_receipt(receipt)
    if verified['item_id'] not in life.snapshot()['clips']:
        raise GuardError('unknown item')
    return life.transition(verified['item_id'], 'aired', evidence=receipt)
