"""Shared closed contracts and offline evidence verification."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import hmac
import json
import re

ROOT = Path(__file__).resolve().parents[1]
STATES = ('planned', 'queued', 'rendered', 'approved', 'aired', 'pulled', 'failed', 'held', 'rejected')
EXITS = frozenset(('pulled', 'failed', 'held', 'rejected'))
EDGES = {
    'planned': frozenset(('queued',)) | EXITS,
    'queued': frozenset(('rendered',)) | EXITS,
    'rendered': frozenset(('approved',)) | EXITS,
    'approved': frozenset(('aired',)) | EXITS,
    **{s: frozenset() for s in ('aired', *EXITS)},
}
TIERS = ('FLASH', 'SCAR', 'MARK', 'LEGEND')
PLASTIC = frozenset(('health', 'mood', 'gear', 'relationships', 'carried_consequences'))

class GuardError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise GuardError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    require(isinstance(value, str), 'timestamp must be a string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise GuardError('invalid timestamp') from exc
    require(result.tzinfo is not None and result.utcoffset() is not None, 'timestamp needs timezone')
    return result


def sha(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'invalid SHA-256')
    return value


def integer(value, name, minimum=0):
    require(type(value) is int and value >= minimum, name + ' must be a nonnegative integer')
    return value


def output_path(path):
    p = Path(path).resolve()
    require(p.is_relative_to(ROOT), 'all writes must stay under the lifecycle folder')
    return p


def human(record, action, subject):
    require(isinstance(record, dict), 'structured human authorization required')
    require(record.get('mode') == 'offline-fixture', 'only explicitly synthetic offline authorization accepted')
    require(record.get('actor') == 'trundle' and record.get('decision') == 'yes', 'explicit trundle yes required')
    require(record.get('action') == action and record.get('subject') == subject, 'human authorization scope mismatch')
    require(bool(record.get('id')) and bool(record.get('reason')), 'authorization needs ID and reason')
    timestamp(record.get('timestamp'))


class MockPlayback:
    """Fixture-only trust boundary. Never accepts production receipts or contacts playout.

    The lifecycle receives an injected verifier; a bare `verified: true` is not evidence.
    A production receipt authority requires a separate reviewed integration.
    """
    def __init__(self, key=b'astra-offline-fixture-authority-v1'):
        self._key = key

    def issue(self, clip, receipt_id, when=None):
        require(clip['state'] == 'approved', 'mock playback requires approved clip')
        row = dict(id=receipt_id, mode='offline-fixture', authority_id=clip['authority_id'], clip_id=clip['id'],
                   slot=clip['slot'], lineage=clip['lineage'], media_hash=clip['media_hash'],
                   timestamp=when or now(), completed=True)
        return row | {'signature': hmac.new(self._key, canonical(row).encode(), hashlib.sha256).hexdigest()}

    def verify(self, receipt):
        validate_receipt(receipt)
        row = {k: v for k, v in receipt.items() if k != 'signature'}
        sig = hmac.new(self._key, canonical(row).encode(), hashlib.sha256).hexdigest()
        require(hmac.compare_digest(str(receipt.get('signature', '')), sig), 'untrusted playback receipt')
        require(row.get('mode') == 'offline-fixture' and row.get('completed') is True, 'completed fixture playback required')
        require(timestamp(row.get('timestamp')) <= datetime.now(timezone.utc), 'future playback receipt')
        return row


def validate_receipt(receipt):
    """Closed wire contract, also enforced independently of the injected verifier."""
    fields = {'id', 'mode', 'authority_id', 'clip_id', 'slot', 'lineage', 'media_hash',
              'timestamp', 'completed', 'signature'}
    require(isinstance(receipt, dict) and set(receipt) == fields, 'closed playback receipt required')
    for name in ('id', 'authority_id', 'clip_id', 'slot', 'lineage'):
        require(isinstance(receipt[name], str) and receipt[name].strip(), 'invalid receipt ' + name)
    require(receipt['mode'] == 'offline-fixture' and receipt['completed'] is True,
            'completed offline receipt required')
    sha(receipt['media_hash'])
    sha(receipt['signature'])
    require(timestamp(receipt['timestamp']) <= datetime.now(timezone.utc), 'future playback receipt')
