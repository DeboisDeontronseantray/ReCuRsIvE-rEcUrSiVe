"""Home-only comment intake. Providers, airing, and public capture stay disabled."""
import atexit
import fcntl
import html
import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from qc_fixture import check_clip, check_prompt

from .adapters import Adapters
from .contracts import GuardError, now, output_path, require
from .continuity import failures as continuity_failures
from .fixture import setup as fixture_setup, spec as fixture_spec
from .home_channels import (
    CH4_NUMBER,
    ROOT,
    channel_key,
    describe_channel,
    find_clip,
    network_catalog,
    parse_channel_number,
    require_distinct_ch16,
)
from .home_prompt import (
    bind_spec,
    build_candidate,
    check_emitted_args,
    eligible_pickup,
    load_base_spec,
    placement_window_ok,
)
from .home_sources import (
    SourceRoots,
    canon_provenance,
    load_selected_source,
    reference_files_for_channel,
)
from .lifecycle import Lifecycle
from .recipe import assemble

TARGETS = ('alter', 'extend')
HARD_TERMINAL = frozenset({'rejected', 'proposed_render'})
SOFT_TERMINAL = frozenset({'blocked'})
TERMINAL = HARD_TERMINAL | SOFT_TERMINAL
STAGE_RANK = {
    'claimed': 0, 'processing': 0,
    'intake': 1,
    'moderation': 2,
    'resolved': 3,
    'assembled': 4,
    'rejected': 5, 'blocked': 5, 'proposed_render': 5,
}
MAX_TEXT = 2000
MAX_CLIP_ID = 128
MAX_BODY = 8192
MAX_IDEMPOTENCY = 128
CONTRIBUTOR_ID = 'home-viewer'
COOKIE_NAME = 'home_comment_auth'
FORBIDDEN_FIELDS = frozenset({
    'handle', 'handles', 'contributor_handle', 'contributor_handles',
    'commenter_images', 'image', 'images', 'file', 'files', 'media', 'upload',
})
FORBIDDEN_ADAPTERS = frozenset({
    ('render', 'reserve'), ('render', 'dispatch'), ('render', 'rendered'),
    ('D09', 'aired'), ('B01', 'approve'), ('B01', 'preempt'),
})
ALLOWED_ADAPTERS = frozenset({
    ('A07', 'intake'), ('A07', 'filter'), ('A07', 'recover'),
    ('D13', 'place'), ('D14', 'place'), ('D14', 'carry'),
    ('D10', 'propose'), ('D15', 'propose'),
})
HEALTH_STATUSES = ('unknown', 'disconnected', 'mock', 'verified')
DEFAULT_PORT = 8780
DEFAULT_BIND = '127.0.0.1'
LOCK_NAME = 'home-comment-runtime.lock'
REPROCESS_TRUTH = frozenset({True, 'true', '1', 'yes', 'on'})
CANON_ADVANCE = frozenset({'ok', 'pending_director_review'})


class ConflictError(GuardError):
    http_status = 409


class InjectedCrash(RuntimeError):
    pass


class HomeGateway:
    """Adapters gateway that refuses render, spend, approval, and air."""

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self._inner = Adapters(lifecycle)
        self.calls = []
        self.blocked = []

    def call(self, machine, action, **payload):
        item = (machine, action)
        self.calls.append({'machine': machine, 'action': action})
        if item in FORBIDDEN_ADAPTERS:
            self.blocked.append(item)
            raise GuardError('home runtime disables ' + machine + '/' + action)
        require(item in ALLOWED_ADAPTERS, 'home runtime refuses ' + machine + '/' + action)
        return self._inner.call(machine, action, **payload)


def parse_target(value):
    if not isinstance(value, str) or not value.strip():
        raise GuardError('target must be alter or extend')
    target = value.strip().lower()
    if target not in TARGETS:
        raise GuardError('target must be alter or extend')
    return target


def _health_row(value, *, default_reason):
    if value is None:
        return {'status': 'unknown', 'reason': default_reason, 'verified': False}
    if isinstance(value, str):
        status = value
        reason = default_reason
    elif isinstance(value, dict):
        status = value.get('status', 'unknown')
        reason = value.get('reason', default_reason)
    else:
        raise GuardError('health row must be a status string or object')
    if status not in HEALTH_STATUSES:
        raise GuardError('health status must be unknown, disconnected, mock, or verified')
    return {'status': status, 'reason': reason, 'verified': status == 'verified'}


def canonical_payload(channel, target, text, clip_id):
    return json.dumps(
        {'channel': channel, 'clip_id': clip_id, 'target': target, 'text': text},
        sort_keys=True, separators=(',', ':'),
    )


def request_id(channel, canonical, idempotency_key):
    if idempotency_key:
        seed = 'ch|' + str(channel) + '|key|' + idempotency_key
    else:
        seed = 'ch|' + str(channel) + '|body|' + canonical
    return 'home-' + sha256(seed.encode('utf-8')).hexdigest()[:20]


def parse_urlencoded(raw):
    """Decode application/x-www-form-urlencoded from complete percent-encoded bytes."""
    if raw is None:
        data = b''
    elif isinstance(raw, bytes):
        data = raw
    elif isinstance(raw, str):
        data = raw.encode('ascii', 'surrogateescape')
    else:
        raise GuardError('malformed form encoding')
    result = {}
    if not data:
        return result
    for part in data.split(b'&'):
        if not part:
            continue
        if b'=' in part:
            key, value = part.split(b'=', 1)
        else:
            key, value = part, b''
        result[_percent_decode(key)] = _percent_decode(value)
    return result


def _percent_decode(chunk):
    chunk = chunk.replace(b'+', b' ')
    out = bytearray()
    i = 0
    while i < len(chunk):
        if chunk[i] == 37:
            if i + 2 >= len(chunk):
                raise GuardError('malformed form encoding')
            try:
                out.append(int(chunk[i + 1:i + 3], 16))
            except ValueError as exc:
                raise GuardError('malformed form encoding') from exc
            i += 3
            continue
        out.append(chunk[i])
        i += 1
    try:
        return bytes(out).decode('utf-8')
    except UnicodeDecodeError as exc:
        raise GuardError('malformed form encoding') from exc


class HomeCommentRuntime:
    def __init__(
        self, path, *, pickup_health=None, playback_health=None, crash_at=None,
        source_roots=None, tt_paths_file=None, lease_seconds=15, environ=None,
        source_manifests=None, time_fn=None,
    ):
        self.path = output_path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.requests_path = self.path / 'requests.sqlite'
        self.crash_at = crash_at
        self.lease_seconds = float(lease_seconds)
        self.time_fn = time_fn or time.time
        self.roots = SourceRoots(
            overrides=source_roots, tt_paths_file=tt_paths_file, environ=environ,
            source_manifests=source_manifests,
        )
        self.pickup_health = _health_row(
            pickup_health,
            default_reason='no pickup process is managed by this runtime',
        )
        self.playback_health = _health_row(
            playback_health,
            default_reason='this runtime does not verify playout; fixture receipts are not production playback',
        )
        self.catalog = network_catalog(self.roots)
        require_distinct_ch16(self.catalog, roots=self.roots)
        self._lives = {}
        self._gateways = {}
        self._mutating = set()
        self._mutating_lock = threading.Lock()
        self._lock_fd = None
        self._acquire_instance_lock()
        self._ensure_schema()

    def _acquire_instance_lock(self):
        path = self.path / LOCK_NAME
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise GuardError(
                'home comment runtime already running for ' + str(self.path)
                + '; one instance per data dir'
            )
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode('utf-8'))
        self._lock_fd = fd
        atexit.register(self.close)

    def close(self):
        fd = self._lock_fd
        if fd is None:
            return
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        self._lock_fd = None
        try:
            atexit.unregister(self.close)
        except ValueError:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def _crash(self, stage):
        if self.crash_at == stage:
            raise InjectedCrash(stage)

    def _ensure_schema(self):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute(
                'CREATE TABLE IF NOT EXISTS requests ('
                'id TEXT PRIMARY KEY, channel INTEGER NOT NULL, canonical TEXT NOT NULL, '
                'idempotency_key TEXT, payload TEXT NOT NULL, created_at TEXT NOT NULL)'
            )
            columns = {row[1] for row in db.execute('PRAGMA table_info(requests)')}
            if 'canonical' not in columns:
                db.execute('ALTER TABLE requests ADD COLUMN canonical TEXT NOT NULL DEFAULT ""')
            if 'idempotency_key' not in columns:
                db.execute('ALTER TABLE requests ADD COLUMN idempotency_key TEXT')
            db.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS requests_channel_idem '
                'ON requests(channel, idempotency_key) WHERE idempotency_key IS NOT NULL'
            )
            db.execute(
                'CREATE TABLE IF NOT EXISTS provider_log ('
                'id INTEGER PRIMARY KEY, machine TEXT, action TEXT, timestamp TEXT NOT NULL)'
            )
            db.commit()

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.requests_path, timeout=30, isolation_level=None)
        try:
            yield db
        finally:
            db.close()

    def _write_row(self, db, row):
        db.execute(
            'INSERT OR REPLACE INTO requests(id, channel, canonical, idempotency_key, payload, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (row['id'], row['channel'], row['canonical'], row.get('idempotency_key'),
             json.dumps(row, sort_keys=True), row['created_at']),
        )

    def _rank(self, row):
        return STAGE_RANK.get(row.get('stage') or row.get('status') or 'claimed', 0)

    def _now(self):
        return self.time_fn()

    def _lease_held(self, row, owner, now_ts):
        until = row.get('lease_until') or 0
        holder = row.get('lease_owner')
        return bool(holder) and holder != owner and until > now_ts

    def _other_owner(self, row, owner):
        holder = row.get('lease_owner')
        return bool(holder) and holder != owner

    def _save(self, row, *, owner=None, renew=False, clear_lease=False):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            found = db.execute('SELECT payload FROM requests WHERE id=?', (row['id'],)).fetchone()
            if found:
                existing = json.loads(found[0])
                if existing.get('status') in HARD_TERMINAL:
                    db.commit()
                    return deepcopy(existing), False
                now_ts = self._now()
                incoming_gen = int(row.get('generation') or 0)
                existing_gen = int(existing.get('generation') or 0)
                if owner and self._other_owner(existing, owner):
                    db.commit()
                    return deepcopy(existing), False
                if incoming_gen != existing_gen:
                    db.commit()
                    return deepcopy(existing), False
                reprocess = row.get('reprocess') and existing.get('status') in {'blocked', 'proposed_render'}
                if not reprocess and self._rank(existing) > self._rank(row) and existing.get('status') in TERMINAL:
                    db.commit()
                    return deepcopy(existing), False
                if clear_lease:
                    row['lease_owner'] = None
                    row['lease_until'] = 0
                elif owner:
                    row['lease_owner'] = owner
                    row['lease_until'] = now_ts + self.lease_seconds
                elif renew:
                    row['lease_until'] = now_ts + self.lease_seconds
                row['generation'] = existing_gen + 1
            else:
                row['generation'] = int(row.get('generation') or 0) + 1
            self._write_row(db, row)
            db.commit()
        return deepcopy(row), True

    def _commit(self, row, owner):
        saved, applied = self._save(row, owner=owner, renew=True)
        if not applied:
            return saved, False
        if owner and saved.get('lease_owner') != owner:
            return saved, False
        return saved, True

    def _wait_for_settled(self, request_id_value, fallback):
        deadline = time.time() + max(2.0, self.lease_seconds)
        latest = fallback
        while time.time() < deadline:
            latest = self._load(request_id_value) or latest
            if latest.get('status') in TERMINAL:
                return deepcopy(latest)
            time.sleep(0.02)
        return deepcopy(self._load(request_id_value) or latest)

    def _load(self, request_id_value):
        with self._db() as db:
            found = db.execute('SELECT payload FROM requests WHERE id=?', (request_id_value,)).fetchone()
        return json.loads(found[0]) if found else None

    def _clear_lease(self, request_id_value, owner):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            found = db.execute('SELECT payload FROM requests WHERE id=?', (request_id_value,)).fetchone()
            if found:
                row = json.loads(found[0])
                if row.get('lease_owner') == owner:
                    row['lease_owner'] = None
                    row['lease_until'] = 0
                    self._write_row(db, row)
            db.commit()

    def _new_claimed(self, fields, owner, now_ts):
        return {
            **fields,
            'status': 'processing',
            'stage': 'claimed',
            'http_status': 202,
            'reason': 'claimed; adapters not finished',
            'pipeline': self._pipeline_shell(fields),
            'playback': deepcopy(self.playback_health),
            'providers': 'disabled',
            'airing': 'disabled',
            'lease_owner': owner,
            'lease_until': now_ts + self.lease_seconds,
            'generation': 0,
            'reprocess': False,
        }

    def _acquire(self, fields, *, reprocess=False):
        owner = str(uuid4())
        deadline = time.time() + max(2.0, self.lease_seconds)
        while True:
            with self._mutating_lock:
                mutating = fields['id'] in self._mutating
            if mutating:
                time.sleep(0.02)
                continue
            if time.time() >= deadline:
                break
            now_ts = self._now()
            with self._db() as db:
                db.execute('BEGIN IMMEDIATE')
                found = db.execute('SELECT payload FROM requests WHERE id=?', (fields['id'],)).fetchone()
                if not found and fields.get('idempotency_key'):
                    found = db.execute(
                        'SELECT payload FROM requests WHERE channel=? AND idempotency_key=?',
                        (fields['channel'], fields['idempotency_key']),
                    ).fetchone()
                if not found:
                    row = self._new_claimed(fields, owner, now_ts)
                    try:
                        self._write_row(db, row)
                    except sqlite3.IntegrityError:
                        db.commit()
                        continue
                    with self._mutating_lock:
                        self._mutating.add(row['id'])
                    db.commit()
                    return row, owner
                row = json.loads(found[0])
                if row.get('canonical') != fields['canonical']:
                    db.commit()
                    raise ConflictError(
                        'idempotency key already bound to a different payload on '
                        + fields['channel_key']
                    )
                if row.get('status') == 'rejected' or (
                    row.get('status') in HARD_TERMINAL and not reprocess
                ):
                    db.commit()
                    return row, None
                if row.get('status') == 'blocked' and not reprocess:
                    db.commit()
                    return row, None
                with self._mutating_lock:
                    mutating = fields['id'] in self._mutating
                    if mutating:
                        db.commit()
                    elif self._lease_held(row, owner, now_ts):
                        db.commit()
                    else:
                        if reprocess and row.get('status') in {'blocked', 'proposed_render'}:
                            row['status'] = 'processing'
                            row['stage'] = 'claimed'
                            row['http_status'] = 202
                            row['reason'] = 're-evaluating after source change'
                            row['reprocess'] = True
                            row['pipeline'] = self._pipeline_shell(fields)
                        row['lease_owner'] = owner
                        row['lease_until'] = now_ts + self.lease_seconds
                        row['generation'] = int(row.get('generation') or 0) + 1
                        self._write_row(db, row)
                        self._mutating.add(row['id'])
                        db.commit()
                        return row, owner
            time.sleep(0.02)
        latest = self._load(fields['id'])
        require(latest is not None, 'lost request claim')
        return latest, None

    def _channel_runtime(self, number):
        key = channel_key(number)
        if key not in self._lives:
            folder = self.path / key
            folder.mkdir(parents=True, exist_ok=True)
            life = Lifecycle(folder / 'lifecycle.sqlite')
            self._lives[key] = life
            self._gateways[key] = HomeGateway(life)
        return self._lives[key], self._gateways[key]

    def channels(self):
        return deepcopy(self.catalog)

    def health(self):
        adapter_calls = []
        blocked = []
        for gateway in self._gateways.values():
            adapter_calls.extend(gateway.calls)
            blocked.extend({'machine': m, 'action': a} for m, a in gateway.blocked)
        with self._db() as db:
            provider_rows = list(db.execute('SELECT machine, action FROM provider_log'))
        matrix = [{
            'number': row['number'],
            'key': row['key'],
            'label': row['label'],
            'capability': row['capability'],
            'blocked_reason': row['blocked_reason'],
            'default_clip_id': row['default_clip_id'],
            'prompt_clips': row['prompt_clips'],
            'reference_missing': row['reference_missing'],
            'bible': row['bible'],
            'selected_clip_id': row.get('selected_clip_id'),
            'mapping_errors': row.get('mapping_errors'),
            'canon_provenance': row.get('canon_provenance'),
        } for row in self.catalog]
        return {
            'mode': 'home-only',
            'providers': 'disabled',
            'airing': 'disabled',
            'generation': 'disabled',
            'outward': 'disabled',
            'spend_cents': 0,
            'network': 'channels 2-22 from repository registry plus documented TT_* roots',
            'ch4': 'Military Boutique; fixture/proof only; not the rest of the network',
            'ch16': '16-dossier; distinct from Ch4; uses TT_STORY_DIR/TT_CHANNELS when mapped',
            'source_roots': {key: row['path'] for key, row in self.roots.resolved.items()},
            'source_mapping_errors': self.roots.mapping_errors(),
            'pickup': deepcopy(self.pickup_health),
            'playback': deepcopy(self.playback_health),
            'provider_calls': adapter_calls,
            'provider_log_rows': len(provider_rows),
            'forbidden_adapter_attempts': blocked,
            'durable_store': str(self.path),
            'capability_matrix': matrix,
            'channels': self.channels(),
        }

    def get(self, request_id_value):
        require(isinstance(request_id_value, str) and request_id_value.strip(), 'request id required')
        row = self._load(request_id_value.strip())
        require(row is not None, 'unknown comment request')
        return deepcopy(row)

    def list_comments(self, channel):
        number = parse_channel_number(channel)
        with self._db() as db:
            rows = db.execute(
                'SELECT payload FROM requests WHERE channel=? ORDER BY created_at, id',
                (number,),
            ).fetchall()
        return [json.loads(payload) for payload, in rows]

    def submit(self, payload):
        fields = self._validate_payload(payload)
        raw_reprocess = payload.get('reprocess')
        if isinstance(raw_reprocess, str):
            raw_reprocess = raw_reprocess.strip().lower()
        reprocess = raw_reprocess in REPROCESS_TRUTH
        row, owner = self._acquire(fields, reprocess=reprocess)
        if owner is None:
            return deepcopy(row)
        try:
            return self._process(row, owner=owner)
        except InjectedCrash:
            self._clear_lease(row['id'], owner)
            raise
        except Exception:
            self._clear_lease(row['id'], owner)
            raise
        finally:
            with self._mutating_lock:
                self._mutating.discard(row['id'])

    def _validate_payload(self, payload):
        if not isinstance(payload, dict):
            raise GuardError('JSON object required')
        extra = FORBIDDEN_FIELDS.intersection(payload)
        if extra:
            raise GuardError(
                'commenter images, contributor handles, and uploads are refused: '
                + ', '.join(sorted(extra))
            )
        try:
            number = parse_channel_number(payload.get('channel'))
            target = parse_target(payload.get('target'))
        except (GuardError, ValueError) as exc:
            raise GuardError(str(exc)) from exc
        text = payload.get('text')
        if not isinstance(text, str) or not text.strip():
            raise GuardError('text is required')
        text = text.strip()
        if len(text) > MAX_TEXT:
            raise GuardError('text exceeds ' + str(MAX_TEXT) + ' characters')
        clip_id = payload.get('clip_id') or payload.get('clip')
        if clip_id in ('', None):
            clip_id = None
        elif not isinstance(clip_id, str) or len(clip_id.strip()) > MAX_CLIP_ID:
            raise GuardError('clip_id must be a short string')
        else:
            clip_id = clip_id.strip()
        idempotency_key = payload.get('idempotency_key')
        if idempotency_key in ('', None):
            idempotency_key = None
        elif not isinstance(idempotency_key, str) or len(idempotency_key) > MAX_IDEMPOTENCY:
            raise GuardError('idempotency_key must be a short string')
        canonical = canonical_payload(number, target, text, clip_id)
        record = describe_channel(number, roots=self.roots)
        return {
            'id': request_id(number, canonical, idempotency_key),
            'channel': number,
            'channel_key': record['key'],
            'channel_label': record['label'],
            'target': target,
            'text': text,
            'clip_id': clip_id,
            'canonical': canonical,
            'contributor_id': CONTRIBUTOR_ID,
            'channel_record': record,
            'idempotency_key': idempotency_key,
            'created_at': now(),
        }

    def _pipeline_shell(self, fields):
        missing = fields['channel_record']['missing_configuration'] if fields.get('channel_record') else ['channel']
        return {
            'intake': {'status': 'pending'},
            'moderation': {'status': 'pending', 'adapter': 'A07/filter + qc_fixture.check_prompt'},
            'target': {'status': 'pending'},
            'canon': {'status': 'pending'},
            'assembly': {'status': 'pending'},
            'propose': {'status': 'pending'},
            'provider': {'status': 'disabled', 'calls': 0, 'reason': 'home runtime fail-closed; no render provider'},
            'airing': {'status': 'disabled', 'reason': 'OUTWARD HOLD / no-unapproved-airing'},
            'missing_configuration': missing,
        }

    def _finish(self, row, *, status, http_status, reason, pipeline, extra=None, owner=None):
        pipeline['provider'] = {
            'status': 'disabled',
            'calls': 0,
            'reason': 'proposed is not approved, queued for playback, rendered, or aired',
        }
        out = {
            **row,
            'status': status,
            'stage': status,
            'http_status': http_status,
            'reason': reason,
            'pipeline': pipeline,
            'playback': deepcopy(self.playback_health),
            'providers': 'disabled',
            'airing': 'disabled',
            'lease_owner': None,
            'lease_until': 0,
            'reprocess': False,
        }
        if extra:
            out.update(extra)
        saved, applied = self._save(out, owner=owner, clear_lease=True)
        if not applied:
            return self._wait_for_settled(out['id'], saved)
        return saved

    def _process(self, row, *, owner=None):
        pipeline = row.get('pipeline') or self._pipeline_shell(row)
        number = row['channel']
        life, gateway = self._channel_runtime(number)
        stage = row.get('stage') or 'claimed'
        row, ok = self._commit(row, owner)
        if not ok:
            return self._wait_for_settled(row['id'], row)
        pipeline = row.get('pipeline') or pipeline
        stage = row.get('stage') or stage
        self._crash('claimed')
        if stage in ('claimed', 'processing'):
            row, ok = self._commit(row, owner)
            if not ok:
                return self._wait_for_settled(row['id'], row)
            existing_prompt = life.snapshot()['prompts'].get(row['id'])
            if existing_prompt:
                prompt = existing_prompt
            else:
                prompt = gateway.call(
                    'A07', 'intake',
                    prompt_id=row['id'],
                    text=row['text'],
                    contributor_id=CONTRIBUTOR_ID,
                    channel=row['channel_key'],
                    metadata={'source': 'home-comment-runtime', 'target': row['target']},
                )
            pipeline['intake'] = {
                'status': 'ok',
                'adapter': 'A07/intake',
                'prompt_id': prompt['id'],
                'channel': prompt['channel'],
            }
            row['stage'] = 'intake'
            row['pipeline'] = pipeline
            row, ok = self._commit(row, owner)
            if not ok:
                return self._wait_for_settled(row['id'], row)
            pipeline = row.get('pipeline') or pipeline
            self._crash('intake')
            stage = 'intake'
        if stage == 'intake':
            snapshot = life.snapshot()['prompts'].get(row['id'], {})
            already = snapshot.get('filter')
            if snapshot.get('status') == 'held' and already:
                allowed, reason = False, already.get('reason', 'held')
            elif already and already.get('allowed') is True:
                allowed, reason = True, already.get('reason', 'already filtered')
            else:
                allowed, reason = check_prompt(row['text'], {'kind': 'segment'})
                try:
                    gateway.call('A07', 'filter', prompt_id=row['id'], allowed=allowed, reason=reason)
                except GuardError:
                    snapshot = life.snapshot()['prompts'].get(row['id'], {})
                    already = snapshot.get('filter')
                    require(already is not None, 'moderation filter could not be recovered')
                    allowed, reason = already.get('allowed') is True, already.get('reason', reason)
            pipeline['moderation'] = {
                'status': 'allowed' if allowed else 'rejected',
                'adapter': 'A07/filter',
                'reason': reason,
            }
            row['stage'] = 'moderation'
            row['pipeline'] = pipeline
            row, ok = self._commit(row, owner)
            if not ok:
                return self._wait_for_settled(row['id'], row)
            pipeline = row.get('pipeline') or pipeline
            self._crash('moderation')
            stage = 'moderation'
        if stage == 'moderation' and pipeline.get('moderation', {}).get('status') == 'rejected':
            reason = pipeline['moderation']['reason']
            return self._finish(
                row, status='rejected', http_status=422, reason=reason, pipeline=pipeline,
                extra={'lifecycle_prompt_status': life.snapshot()['prompts'][row['id']]['status']},
                owner=owner,
            )
        if stage == 'moderation':
            target_info, error = self._resolve_target(row, life)
            if error:
                target_info['reason'] = error
            pipeline['target'] = target_info
            row['resolved'] = target_info
            row['pipeline'] = pipeline
            row['stage'] = 'resolved'
            row, ok = self._commit(row, owner)
            if not ok:
                return self._wait_for_settled(row['id'], row)
            pipeline = row.get('pipeline') or pipeline
            self._crash('resolved')
            stage = 'resolved'
            if error:
                return self._finish(
                    row, status='blocked', http_status=422, reason=error, pipeline=pipeline, owner=owner,
                )
        if stage == 'resolved' and pipeline.get('target', {}).get('status') == 'blocked':
            return self._finish(
                row, status='blocked', http_status=422,
                reason=pipeline['target'].get('reason') or row.get('reason'),
                pipeline=pipeline, owner=owner,
            )
        if stage == 'resolved':
            error = self._assemble(row, pipeline, life, gateway)
            row['pipeline'] = pipeline
            row['stage'] = 'assembled'
            row, ok = self._commit(row, owner)
            if not ok:
                return self._wait_for_settled(row['id'], row)
            pipeline = row.get('pipeline') or pipeline
            self._crash('assembled')
            stage = 'assembled'
            if error:
                return self._finish(
                    row, status='blocked', http_status=422, reason=error, pipeline=pipeline, owner=owner,
                )
        if stage == 'assembled':
            assembly = pipeline.get('assembly') or {}
            canon = pipeline.get('canon') or {}
            if assembly.get('status') == 'blocked' or (
                canon.get('status') and canon.get('status') not in CANON_ADVANCE
            ):
                reason = assembly.get('reason') or canon.get('reason') or 'adapter blocked'
                return self._finish(
                    row, status='blocked', http_status=422, reason=reason, pipeline=pipeline, owner=owner,
                )
            if assembly.get('status') != 'planned' or canon.get('status') not in CANON_ADVANCE:
                error = self._assemble(row, pipeline, life, gateway)
                row['pipeline'] = pipeline
                row, ok = self._commit(row, owner)
                if not ok:
                    return self._wait_for_settled(row['id'], row)
                pipeline = row.get('pipeline') or pipeline
                if error:
                    return self._finish(
                        row, status='blocked', http_status=422, reason=error, pipeline=pipeline, owner=owner,
                    )
        planned_id = pipeline.get('assembly', {}).get('clip_id')
        extra = {'lifecycle_prompt_status': life.snapshot()['prompts'][row['id']]['status']}
        if planned_id and planned_id in life.snapshot()['clips']:
            extra['planned_clip_id'] = planned_id
            extra['planned_state'] = life.snapshot()['clips'][planned_id]['state']
        if (pipeline.get('canon') or {}).get('status') == 'pending_director_review':
            extra['pending_director_review'] = True
        return self._finish(
            row,
            status='proposed_render',
            http_status=201,
            reason='durable proposed-render item; providers remain disabled',
            pipeline=pipeline,
            extra=extra,
            owner=owner,
        )

    def _resolve_target(self, row, life):
        number = row['channel']
        record = row['channel_record']
        requested = row.get('clip_id')
        selected = load_selected_source(number, self.roots, requested=requested)
        mapping = self.roots.mapping_errors('TT_CHANNELS', 'TT_STORY_DIR', 'TT_THUNDER_ROOT')
        constituent_id = None
        if selected.get('status') == 'ok':
            pack = {
                'clip_id': selected['clip_id'],
                'version': selected.get('version'),
                'parent_clip': selected.get('parent_clip'),
                'prompt': selected.get('prompt') or '',
                'source': 'selected-source-manifest',
                'authority': 'explicit-manifest',
                'selected': selected,
                'reference_present': [item['path'] for item in selected.get('references') or []],
                'reference_missing': [],
            }
            segments = selected.get('segments') or []
            if segments:
                ids = [item['id'] for item in segments]
                if row['target'] == 'alter':
                    if requested not in ids:
                        return {'status': 'blocked', 'requested': requested, 'selected': selected}, (
                            'alter requires a requested constituent target among '
                            + ', '.join(ids)
                        )
                    chosen = next(item for item in segments if item['id'] == requested)
                else:
                    chosen = segments[-1]
                constituent_id = chosen['id']
                prompt_obj = chosen.get('prompt') or {}
                pack['prompt'] = prompt_obj.get('text') if isinstance(prompt_obj, dict) else (pack['prompt'])
        elif not requested and number == CH4_NUMBER:
            requested = 'SEED-S1'
            pack = find_clip(number, requested, roots=self.roots)
        elif requested:
            pack = find_clip(number, requested, roots=self.roots)
            if pack and pack.get('source') != 'ch4-fixture':
                pack = None
        else:
            pack = None
        if pack is None:
            reason = (
                (selected.get('reason') if number != CH4_NUMBER else None)
                or (mapping[0] if mapping and number != CH4_NUMBER else None)
                or (
                    'lifecycle-only clip ' + str(requested) + ' on ' + record['key']
                    + ' has no explicit selected-source manifest'
                    if requested and requested in life.snapshot()['clips'] else None
                )
                or (
                    row['target'] + ' requires an explicit selected-source manifest for '
                    + record['key'] + '; will not guess last/current/C3/REVIEW-v3'
                )
            )
            if requested and str(requested) not in reason:
                reason = reason + '; requested ' + str(requested)
            if record['key'] not in reason:
                reason = record['key'] + ': ' + reason
            return {'status': 'blocked', 'requested': requested, 'selected': selected}, reason
        segment_ids = {item['id'] for item in (selected.get('segments') or [])}
        if requested and selected.get('status') == 'ok' and requested not in {
            selected.get('clip_id'), selected.get('version'),
        } | segment_ids and row.get('clip_id') not in {
            None, selected.get('clip_id'), selected.get('version'),
        } | segment_ids:
            return {'status': 'blocked', 'requested': row.get('clip_id')}, (
                'requested clip is not the explicit selected source'
            )
        resolved_id = pack['clip_id']
        snap = life.snapshot()['clips'].get(resolved_id)
        if snap and snap.get('channel') not in {record['key'], 'Ch' + str(number)}:
            return {'status': 'blocked', 'requested': resolved_id}, (
                'clip ' + resolved_id + ' is not on ' + record['key']
            )
        extend_parent = resolved_id if row['target'] == 'extend' else None
        info = {
            'status': 'ok',
            'requested': row.get('clip_id'),
            'resolved_clip_id': resolved_id,
            'version': pack.get('version') or selected.get('version'),
            'target': row['target'],
            'parent_clip': extend_parent,
            'source': pack.get('source'),
            'pack': pack,
            'selected': selected if selected.get('status') == 'ok' else None,
            'endpoints': selected.get('endpoints') if selected.get('status') == 'ok' else {},
            'source_fingerprint': selected.get('source_fingerprint'),
            'sheets': selected.get('references') if selected.get('status') == 'ok' else [],
            'channel': record['key'],
            'constituent_id': constituent_id,
            'duration': selected.get('duration') if selected.get('status') == 'ok' else None,
        }
        if pack.get('source') == 'ch4-fixture':
            sheets, _missing = reference_files_for_channel(number, self.roots)
            info['sheets'] = sheets
        return info, None

    def _assemble(self, row, pipeline, life, gateway):
        number = row['channel']
        record = row['channel_record']
        info = row.get('resolved') or {}
        pack = info.get('pack')
        after = life.snapshot()
        if number != CH4_NUMBER and 'HERON' in after['cards']:
            pipeline['assembly'] = {'status': 'blocked', 'reason': 'Ch4 fixture identity leaked; refused'}
            pipeline['canon'] = {'status': 'blocked', 'reason': 'refusing Ch4 substitution'}
            pipeline['propose'] = {'status': 'skipped', 'reason': 'refusing Ch4 substitution'}
            return pipeline['assembly']['reason']
        if pack and pack.get('source') == 'ch4-fixture':
            return self._assemble_ch4_fixture(row, pipeline, life, gateway, info)
        return self._assemble_source(row, pipeline, life, gateway, info, pack)

    def _assemble_ch4_fixture(self, row, pipeline, life, gateway, info):
        if 'HERON' not in life.snapshot()['cards']:
            try:
                fixture_setup(life)
            except GuardError:
                require('HERON' in life.snapshot()['cards'], 'Ch4 fixture card missing after concurrent setup')
        resolved = info['resolved_clip_id']
        clip_id = 'clip-' + row['id']
        existing = life.snapshot()['clips'].get(clip_id)
        if existing is None:
            card = life.snapshot()['cards']['HERON']
            refs = [item['hash'] for item in card['refs']]
            prompt = assemble(
                cards=[card],
                state_so_far='HERON holds the ferry landing.',
                beats=[{'t': 0.5, 'who': 'HERON', 'what': 'turns past WOLFHOUND',
                        'how': 'using a circular Systema step', 'with': 'the KOLOKOL-7 resonance baton',
                        'causes': 'his grip to open'}],
                comments=[dict(original_text=row['text'], t=3.0)],
            )
            cfg = fixture_spec()
            cfg['metadata'] = {
                'canon_ref': row['channel_record'].get('bible') or 'ch4-military-boutique',
                'audio': {'integrated_lufs': -16, 'true_peak_dbtp': -1.5},
            }
            try:
                life.plan(
                    clip_id,
                    logical_id=row['target'] + '/' + resolved + '/' + row['id'],
                    slot='slot/' + row['id'],
                    lineage=self._lineage_string(row, info, resolved),
                    prompt=prompt,
                    reference_hashes=refs,
                    spec=cfg,
                    channel=row['channel_key'],
                )
            except GuardError:
                require(clip_id in life.snapshot()['clips'], 'Ch4 planned clip missing after concurrent plan')
        if row['id'] not in life.snapshot()['clips'][clip_id]['prompt_ids']:
            gateway.call('D13', 'place', clip_id=clip_id, prompt_ids=[row['id']])
        gateway.call('D10', 'propose', clip_id=clip_id, proposals=[], consequences=[], reuses=[])
        return self._canon_after_plan(row, pipeline, life, clip_id, info)

    def _lineage_string(self, row, info, resolved):
        parts = [row['channel_key'], row['target'], resolved]
        endpoints = info.get('endpoints') or {}
        for key in ('media_hash', 'endpoint', 'prompt_hash'):
            value = endpoints.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip()[:16])
                break
        return '/'.join(parts)

    def _assemble_source(self, row, pipeline, life, gateway, info, pack):
        provenance = canon_provenance(row['channel'], self.roots, selected=info.get('selected'))
        selected = info.get('selected') or {}
        constituent = None
        spec_art = selected.get('base_spec')
        if info.get('constituent_id'):
            for item in selected.get('segments') or []:
                if item.get('id') == info.get('constituent_id'):
                    constituent = item
                    if item.get('base_spec'):
                        spec_art = item['base_spec']
                    break
        carry_meta = None
        if constituent is not None and row['target'] == 'alter':
            fps = float(selected.get('fps') or 24)
            frames = constituent.get('frames')
            if frames and not placement_window_ok(float(frames) / fps):
                pickup = eligible_pickup(selected, requested_id=constituent.get('id'))
                if pickup is None:
                    reason = (
                        'comment carried from ' + str(constituent.get('id'))
                        + ': no legal viewer time window; no eligible pickup'
                    )
                    pipeline['assembly'] = {
                        'status': 'blocked',
                        'reason': reason,
                        'comment_placement': 'carried',
                        'carried_from': constituent.get('id'),
                    }
                    pipeline['canon'] = {
                        'status': 'blocked',
                        'reason': reason,
                        'check': provenance.get('check'),
                    }
                    return reason
                carry_meta = {
                    'carried_from': constituent.get('id'),
                    'pickup_constituent': pickup.get('id'),
                    'carry_reason': 'constituent duration shorter than v5 placement window',
                    'comment_placement': 'carried',
                }
                constituent = pickup
                if pickup.get('base_spec'):
                    spec_art = pickup['base_spec']
                info['constituent_id'] = pickup.get('id')
                info['carry_meta'] = carry_meta
        if not spec_art or not spec_art.get('path'):
            reason = 'selected.base_spec path+sha required; no whole-show prompt fabrication'
            pipeline['assembly'] = {
                'status': 'blocked',
                'reason': reason,
                'source_fingerprint': selected.get('source_fingerprint'),
            }
            pipeline['canon'] = {
                'status': 'blocked',
                'reason': reason,
                'check': provenance.get('check'),
            }
            return reason
        raw_spec, error = load_base_spec(spec_art['path'], spec_art.get('sha256') or spec_art.get('declared_sha256'))
        if error:
            pipeline['assembly'] = {'status': 'blocked', 'reason': error}
            return error
        bound, error = bind_spec(
            raw_spec, selected, number=row['channel'], constituent=constituent,
            extend=row['target'] == 'extend',
        )
        if error:
            pipeline['assembly'] = {
                'status': 'blocked',
                'reason': error,
                'comment_placement': (carry_meta or {}).get('comment_placement'),
                'carried_from': (carry_meta or {}).get('carried_from'),
                'pickup_constituent': (carry_meta or {}).get('pickup_constituent'),
                'carry_reason': (carry_meta or {}).get('carry_reason'),
            }
            return error
        candidate, error = build_candidate(
            bound,
            comment_text=row['text'],
            comment_id=row['id'],
            number=row['channel'],
            cast_ids=selected.get('cast_ids'),
            selected=selected,
        )
        info['candidate'] = candidate
        if error:
            pipeline['assembly'] = {
                'status': 'blocked',
                'reason': error,
                'builder': 'build_prompt_v42',
                'production_report': (candidate or {}).get('report'),
            }
            pipeline['canon'] = {
                'status': 'blocked',
                'reason': error,
                'check': 'production-rules',
                'pending_director_review': False,
            }
            return error
        emitted = check_emitted_args(candidate['args'], selected)
        if emitted:
            pipeline['assembly'] = {'status': 'blocked', 'reason': emitted, 'builder': 'build_prompt_v42'}
            return emitted
        sheets = info.get('sheets') or reference_files_for_channel(
            row['channel'], self.roots, selected=selected,
        )[0]
        hashes = []
        for item in sheets:
            hashes.append(life.add_asset(item['path'], evidence='mapped cast sheet; not inferred side-view'))
        hashes = list(dict.fromkeys(hashes))
        if not hashes:
            reason = 'no mapped cast sheets or present refs for ' + row['channel_key']
            pipeline['assembly'] = {'status': 'blocked', 'reason': reason}
            return reason
        resolved = info['resolved_clip_id']
        fingerprint = info.get('source_fingerprint') or ''
        clip_id = 'clip-' + row['id'] + '-' + (fingerprint[:12] or 'nofp')
        cfg = {
            'metadata': {
                'canon_ref': provenance.get('bible') or row['channel_record'].get('bible') or resolved,
                'audio': {'integrated_lufs': -16, 'true_peak_dbtp': -1.5},
                'source_clip': resolved,
                'source_version': selected.get('version') or info.get('version'),
                'source_fingerprint': fingerprint,
                'builder_args': candidate['args'],
                'builder_sidecar': candidate['sidecar'],
                'production_report': candidate['report'],
                'candidate_prompt_sha256': candidate['prompt_sha256'],
                'pending_director_review': True,
                'constituent_id': info.get('constituent_id'),
                'composite_clip': resolved if selected.get('segments') else None,
                'source_prompt_sha256': candidate.get('source_prompt_sha256') or selected.get('prompt_sha256'),
                'source_prompt_file_sha256': (
                    candidate.get('source_prompt_file_sha256')
                    or candidate.get('source_prompt_sha256')
                    or selected.get('prompt_sha256')
                ),
                'source_prompt_body_sha256': (
                    candidate.get('source_prompt_body_sha256')
                    or selected.get('prompt_body_sha256')
                ),
                'source_media_sha256': candidate.get('source_media_sha256') or (selected.get('media') or {}).get('sha256'),
                'comment_placement': (carry_meta or {}).get('comment_placement') or candidate.get('comment_placement'),
                'carried_from': (carry_meta or {}).get('carried_from'),
                'pickup_constituent': (carry_meta or {}).get('pickup_constituent'),
                'carry_reason': (carry_meta or {}).get('carry_reason'),
            },
        }
        parent = info.get('parent_clip') if row['target'] == 'extend' else None
        dependencies = []
        if parent and parent in life.snapshot()['clips']:
            parent_row = life.snapshot()['clips'][parent]
            if parent_row.get('channel') == row['channel_key']:
                dependencies = [parent]
        if clip_id not in life.snapshot()['clips']:
            try:
                life.plan(
                    clip_id,
                    logical_id=row['target'] + '/' + resolved + '/' + row['id'],
                    slot='slot/' + row['id'],
                    lineage=self._lineage_string(row, info, resolved),
                    prompt=candidate['prompt'],
                    reference_hashes=hashes,
                    spec=cfg,
                    channel=row['channel_key'],
                    dependencies=tuple(dependencies),
                )
            except GuardError:
                require(clip_id in life.snapshot()['clips'], 'planned clip missing after concurrent plan')
        if row['id'] not in life.snapshot()['clips'][clip_id]['prompt_ids']:
            gateway.call('D13', 'place', clip_id=clip_id, prompt_ids=[row['id']])
        gateway.call('D10', 'propose', clip_id=clip_id, proposals=[], consequences=[], reuses=[])
        return self._canon_after_plan(row, pipeline, life, clip_id, info)

    def _canon_after_plan(self, row, pipeline, life, clip_id, info):
        state = life.snapshot()
        planned = state['clips'][clip_id]
        require(planned['state'] == 'planned', 'home runtime must not queue clips for playback')
        require(planned['channel'] == row['channel_key'], 'planned clip channel mismatch')
        provenance = canon_provenance(row['channel'], self.roots, selected=info.get('selected'))
        candidate = info.get('candidate') or {}
        pipeline['assembly'] = {
            'status': 'planned',
            'adapter': 'lifecycle.plan + D13/place',
            'builder': candidate.get('builder'),
            'clip_id': clip_id,
            'clip_state': planned['state'],
            'channel': planned['channel'],
            'resolved_clip_id': info.get('resolved_clip_id'),
            'parent_clip': info.get('parent_clip'),
            'constituent_id': info.get('constituent_id'),
            'duration_s': info.get('duration'),
            'source_fingerprint': info.get('source_fingerprint') or (planned.get('spec') or {}).get('metadata', {}).get('source_fingerprint'),
            'production_report': candidate.get('report') or (planned.get('spec') or {}).get('metadata', {}).get('production_report'),
            'candidate_prompt_sha256': candidate.get('prompt_sha256') or (planned.get('spec') or {}).get('metadata', {}).get('candidate_prompt_sha256'),
            'target': row['target'],
            'lineage': planned.get('lineage'),
            'note': 'planned is not queued, rendered, or aired',
            'comment_placement': (planned.get('spec') or {}).get('metadata', {}).get('comment_placement') or candidate.get('comment_placement'),
            'carried_from': (planned.get('spec') or {}).get('metadata', {}).get('carried_from'),
            'pickup_constituent': (planned.get('spec') or {}).get('metadata', {}).get('pickup_constituent'),
            'carry_reason': (planned.get('spec') or {}).get('metadata', {}).get('carry_reason'),
        }
        pipeline['propose'] = {
            'status': 'ok',
            'adapter': 'D10/propose',
            'note': 'proposal recorded; Director show-bible review pending; not air',
        }
        fixture_ok = info.get('source') == 'ch4-fixture' and 'HERON' in state['cards']
        if fixture_ok:
            continuity_issues = continuity_failures(planned['spec'], planned['prompt'], state['cards'], 0)
            qc_issues = check_clip(planned['spec'], planned['prompt'], {
                'kind': planned['kind'],
                'reference_hashes': planned['reference_hashes'],
            })
            if continuity_issues or qc_issues:
                pipeline['canon'] = {
                    'status': 'blocked',
                    'adapter': 'ch4-fixture continuity + check_clip',
                    'reason': ', '.join(continuity_issues + qc_issues),
                    'authority': 'ch4-fixture',
                    'note': 'nonempty canon_ref is not by itself a pass',
                }
                return pipeline['canon']['reason']
            pipeline['canon'] = {
                'status': 'ok',
                'adapter': 'ch4-fixture HERON locked keys already on the fixture card',
                'authority': 'ch4-fixture',
                'bible': provenance.get('bible') or row['channel_record'].get('bible'),
                'note': 'fixture proof; not external approved bible state',
            }
            return None
        pipeline['provenance'] = {
            'status': provenance.get('status'),
            'check': provenance.get('check'),
            'reason': provenance.get('reason'),
        }
        if provenance.get('status') != 'reference-identity':
            pipeline['canon'] = {
                'status': 'blocked',
                'adapter': provenance.get('adapter') or 'home_sources.canon_provenance',
                'reason': provenance.get('reason') or 'reference-identity not established',
                'bible': provenance.get('bible'),
                'check': 'reference-identity',
                'note': 'provenance is not canon-ok',
            }
            return pipeline['canon']['reason']
        pipeline['canon'] = {
            'status': 'pending_director_review',
            'adapter': 'apply_check_v44 + CURRENT-RULES Director show-bible review',
            'reason': 'production rules recorded; Director show-bible review pending; not canon-complete',
            'bible': provenance.get('bible'),
            'check': 'production-rules',
            'provenance': 'reference-identity',
            'approved': False,
            'canon_complete': False,
            'pending_director_review': True,
            'air_permission': False,
            'warnings': candidate.get('warnings') or {},
        }
        return None


def page_html(catalog, *, bound=None, token_required=False):
    options = []
    for row in catalog:
        label = 'Ch' + str(row['number']) + ' ' + row['name']
        if row['ch4_fixture_only']:
            label += ' (fixture/proof only)'
        if not row.get('proposed_render_ready'):
            label += ' (blocked: ' + (row.get('blocked_reason') or ', '.join(row['missing_configuration'])) + ')'
        options.append('<option value="' + str(row['number']) + '">' + html.escape(label) + '</option>')
    bind_note = html.escape(bound or ('http://' + DEFAULT_BIND + ':' + str(DEFAULT_PORT) + '/'))
    if token_required:
        token_note = (
            'LAN token required once; this form then uses an HttpOnly cookie. '
            'The token is not placed on the form action and must not appear in access logs.'
        )
    else:
        token_note = 'Loopback default; no public bind.'
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Home comment runtime</title>
<style>
body { font-family: Geneva, Verdana, sans-serif; background:#111; color:#ddd; margin:1.5rem; }
main { max-width: 42rem; }
label { display:block; margin:0.8rem 0 0.2rem; }
input, select, textarea, button { font: inherit; width:100%; box-sizing:border-box; }
textarea { min-height: 8rem; }
button { width:auto; padding:0.4rem 0.8rem; margin-top:1rem; }
.note { color:#aaa; font-size:0.9rem; }
code { color:#9f9; }
</style>
</head>
<body>
<main>
<h1>Home comment runtime</h1>
<p class="note">Home rehearsal only. Providers, generation, and airing are disabled.
A comment becomes proposed-render only after intake, viewer moderation, resolved
alter/extend clip, assembly, and canon all actually run. Incomplete adapters return
blocked, not success. This is not playout. Bound at <code>''' + bind_note + '''</code>. ''' + html.escape(token_note) + '''</p>
<form method="post" action="/comments" enctype="application/x-www-form-urlencoded" accept-charset="utf-8">
<label for="channel">Channel (2-22)</label>
<select id="channel" name="channel" required>
''' + '\n'.join(options) + '''
</select>
<label for="target">Target</label>
<select id="target" name="target" required>
<option value="alter">alter existing video</option>
<option value="extend">extend existing video</option>
</select>
<label for="clip_id">Clip id (optional; explicit selected-source manifest only)</label>
<input id="clip_id" name="clip_id" maxlength="128" autocomplete="off">
<label for="text">Comment text</label>
<textarea id="text" name="text" maxlength="2000" required></textarea>
<p class="note">No images, no contributor handles, no public post.</p>
<button type="submit">Submit comment</button>
</form>
<p class="note">JSON API: <code>POST /api/comments</code>, status <code>GET /api/comments/{id}</code>,
health <code>GET /health</code>.</p>
</main>
</body>
</html>
'''


def result_html(row):
    body = html.escape(json.dumps(row, indent=2))
    return '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Comment status</title>
<style>body{font-family:Geneva,Verdana,sans-serif;background:#111;color:#ddd;margin:1.5rem;}
pre{white-space:pre-wrap;}</style></head>
<body><h1>''' + html.escape(str(row.get('status'))) + '''</h1>
<p><a href="/">Back to form</a></p>
<pre>''' + body + '''</pre></body></html>
'''


def _json_bytes(payload, status):
    return status, {'Content-Type': 'application/json; charset=utf-8'}, (
        json.dumps(payload, indent=2) + '\n'
    ).encode('utf-8')


def _html_bytes(payload, status):
    return status, {'Content-Type': 'text/html; charset=utf-8'}, payload.encode('utf-8')


def _split_path(path):
    if not path.startswith('/'):
        path = '/' + path
    if '?' in path:
        path = path.split('?', 1)[0]
    parts = [part for part in path.split('/') if part]
    return path, parts


def dispatch(runtime, method, path, *, query=None, body=b'', content_type='', headers=None, token_required=False):
    query = query or {}
    headers = headers or {}
    path, parts = _split_path(path)
    method = method.upper()
    if len(body) > MAX_BODY:
        return _json_bytes({'error': 'body too large'}, 413)
    try:
        if method == 'GET' and path in ('/', '/index.html'):
            health = runtime.health()
            bound = query.get('bound')
            return _html_bytes(
                page_html(health['channels'], bound=bound, token_required=token_required),
                200,
            )
        if method == 'GET' and path in ('/health', '/status', '/api/health'):
            return _json_bytes(runtime.health(), 200)
        if method == 'GET' and path in ('/channels', '/api/channels'):
            return _json_bytes({'channels': runtime.channels()}, 200)
        if method == 'GET' and path in ('/comments', '/api/comments'):
            channel = query.get('channel')
            require(channel, 'channel query required')
            return _json_bytes({'comments': runtime.list_comments(channel)}, 200)
        if method == 'GET' and len(parts) == 2 and parts[0] == 'comments':
            return _json_bytes(runtime.get(parts[1]), 200)
        if method == 'GET' and len(parts) == 3 and parts[0] == 'api' and parts[1] == 'comments':
            return _json_bytes(runtime.get(parts[2]), 200)
        if method == 'POST' and path in ('/comments', '/api/comments'):
            ctype = (content_type or headers.get('Content-Type') or '').split(';')[0].strip().lower()
            if ctype.startswith('multipart/'):
                raise GuardError('commenter image uploads are refused')
            if ctype in ('application/x-www-form-urlencoded', ''):
                payload = parse_urlencoded(body)
            elif ctype == 'application/json':
                payload = json.loads(body.decode('utf-8') or '{}')
            else:
                raise GuardError('unsupported content type')
            row = runtime.submit(payload)
            if path == '/comments' and ctype != 'application/json':
                return _html_bytes(result_html(row), row.get('http_status', 201))
            return _json_bytes(row, row.get('http_status', 201))
        return _json_bytes({'error': 'not found'}, 404)
    except json.JSONDecodeError:
        return _json_bytes({'error': 'malformed JSON'}, 400)
    except ConflictError as exc:
        return _json_bytes({'error': str(exc), 'status': 'conflict'}, 409)
    except (GuardError, ValueError) as exc:
        return _json_bytes({'error': str(exc)}, 400)
