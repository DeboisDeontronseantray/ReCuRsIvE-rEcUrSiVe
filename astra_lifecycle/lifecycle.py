"""Single durable transition authority. SQLite serializes writers and commits atomically.

All public reads are detached snapshots. No external source module is imported or
executed. Human releases affect prompt disposition, never fabricate air or canon.
"""
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path
import json
import sqlite3
from uuid import uuid4

from . import characters, continuity, registry
from .contracts import (EDGES, EXITS, GuardError, MockPlayback, canonical, digest, file_hash,
                        human, integer, now, output_path, require, sha, timestamp, validate_receipt)
from .trusted_receipt import TrustedNoop, adapt_trusted_receipt


def empty_state():
    return dict(version=1, authority_id=str(uuid4()), clips={}, prompts={}, cards={}, card_history={}, consequences={}, clocks={},
                commits=[], events=[], receipts={}, slots={}, stills={}, problems=[], fix_library=deepcopy(registry.FIXES),
                fix_queue=[], assets={}, inventory={}, approvals={}, reservations={}, releases={},
                metadata={}, aliases={}, swaps=[], ledger=[], open_ideas={}, channel_batches={}, budget_cents=0, mode='offline-fixture')


class Lifecycle:
    def __init__(self, path, verifier=None):
        self.path = output_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.verifier = verifier or MockPlayback()
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS authority (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)')
            db.execute('INSERT OR IGNORE INTO authority VALUES (1, ?)', (canonical(empty_state()),))
            state = json.loads(db.execute('SELECT data FROM authority WHERE id=1').fetchone()[0])
            require(state.get('mode') == 'offline-fixture' and state.get('authority_id'),
                    'only final-package offline authorities supported; explicit migration required')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.execute('PRAGMA synchronous=FULL')
        try:
            yield db
        finally:
            db.close()

    def snapshot(self):
        with self._connect() as db:
            return json.loads(db.execute('SELECT data FROM authority WHERE id=1').fetchone()[0])

    def _run(self, fn, *, clip_id=None):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            state = json.loads(db.execute('SELECT data FROM authority WHERE id=1').fetchone()[0])
            try:
                result = fn(state)
                db.execute('UPDATE authority SET data=? WHERE id=1', (canonical(state),))
                db.commit()
                return deepcopy(result)
            except Exception as exc:
                db.rollback()
                if isinstance(exc, GuardError):
                    db.execute('BEGIN IMMEDIATE')
                    clean = json.loads(db.execute('SELECT data FROM authority WHERE id=1').fetchone()[0])
                    kind = 'approval-as-aired' if 'receipt' in str(exc) else 'continuity gate' if 'gate:' in str(exc) else 'transition rejected'
                    registry.record(clean, kind, clip_id, str(exc))
                    db.execute('UPDATE authority SET data=? WHERE id=1', (canonical(clean),))
                    db.commit()
                raise

    @staticmethod
    def _event(s, kind, subject, before, after, evidence=None):
        s['events'].append(dict(id=len(s['events']) + 1, kind=kind, subject=subject,
                                before=before, after=after, timestamp=now(), evidence=evidence))

    def add_asset(self, path, *, evidence):
        p = Path(path).resolve()
        require(p.is_file() and evidence, 'asset needs existing bytes and evidence')
        h = file_hash(p)
        def op(s):
            s['assets'][h] = {'path': str(p), 'hash': h, 'evidence': evidence, 'version': 1}
            return h
        return self._run(op)

    @staticmethod
    def _assets(s, hashes):
        require(bool(hashes), 'at least one real reference required')
        for h in hashes:
            sha(h)
            row = s['assets'].get(h)
            require(row is not None and Path(row['path']).is_file(), 'missing reference bytes')
            require(file_hash(row['path']) == h, 'reference bytes changed')

    def baseline_card(self, card):
        card = deepcopy(card)
        characters.validate_card(card)
        def op(s):
            require(not s['commits'], 'baseline import is closed after first canon commit')
            require(card['id'] not in s['cards'], 'character already exists')
            self._assets(s, [r['hash'] for r in card['refs']])
            card.setdefault('summon_count', 0)
            card.setdefault('writein_level', 0)
            card.setdefault('memory_log', [])
            card['field_versions'] = {**{k: 1 for k in card}, **{'plastic.' + k: 1 for k in card['plastic']}, **{'locked.' + k: 1 for k in card['locked']}}
            s['cards'][card['id']] = card
            s['card_history'][card['id']] = [deepcopy(card)]
            for ref in card['refs']:
                key = card['id'] + ':' + ref['hash']
                s['stills'][key] = dict(character_id=card['id'], hash=ref['hash'], state='primary',
                    state_digest=digest(card['plastic']), evidence=ref['evidence'], version=1)
            self._event(s, 'baseline', card['id'], None, 1, 'fixture import; no canon advancement')
        self._run(op)

    def candidate_still(self, character_id, reference_hash, patch, *, evidence):
        def op(s):
            require(character_id in s['cards'] and evidence, 'known character and still evidence required')
            self._assets(s, [reference_hash])
            key = character_id + ':' + reference_hash
            require(key not in s['stills'], 'still identity already exists')
            s['stills'][key] = dict(character_id=character_id, hash=reference_hash, state='candidate',
                state_digest=digest(patch), evidence=evidence, version=1)
            self._event(s, 'still', key, None, 'candidate', evidence)
        self._run(op)

    def accept_still(self, character_id, reference_hash, *, evidence):
        def op(s):
            key = character_id + ':' + reference_hash
            row = s['stills'].get(key)
            require(row is not None and row['state'] == 'candidate' and evidence, 'candidate still review required')
            self._assets(s, [reference_hash])
            row.update(state='accepted', evidence=evidence, version=row['version'] + 1)
            self._event(s, 'still', key, 'candidate', 'accepted', evidence)
        self._run(op)

    def baseline_consequence(self, raw, *, channel, index=0, episode=1, season=1):
        def op(s):
            require(not s['commits'] and raw['id'] not in s['consequences'], 'baseline import closed or duplicate')
            c = characters.normalize_consequence(raw, index, episode, season, 'baseline')
            c['channel'] = channel
            s['consequences'][c['id']] = c
            self._event(s, 'baseline_consequence', c['id'], None, c['tier'])
        self._run(op)

    def intake(self, prompt_id, text, contributor_id, *, metadata=None, channel='Ch4', received_at=None):
        require(isinstance(text, str) and text.strip() and contributor_id, 'text and contributor ID required')
        row = dict(id=prompt_id, version=1, original_text=text, contributor_id=contributor_id,
                   contributor_metadata=deepcopy(metadata or {}), channel=channel,
                   received_at=received_at or now(), status='eligible', attempts=[], final_outcome=None,
                   votes=0, subject_matter=[], skipped=0)
        timestamp(row['received_at'])
        def op(s):
            existing = s['prompts'].get(prompt_id)
            if existing:
                require(all(existing[k] == row[k] for k in ('original_text', 'contributor_id', 'channel')), 'conflicting intake identity')
                return existing
            s['prompts'][prompt_id] = row
            self._event(s, 'prompt', prompt_id, None, 'eligible', 'durable before seen/wrap')
            return row
        return self._run(op)

    def eligible(self, channel=None):
        rows = self.snapshot()['prompts'].values()
        return sorted((p for p in rows if p['status'] == 'eligible' and (channel is None or p['channel'] == channel)),
                      key=lambda p: (-p['skipped'], p['received_at'], p['id']))

    def carry(self, prompt_ids, *, reason):
        require(reason, 'carry reason required')
        def op(s):
            for pid in dict.fromkeys(prompt_ids):
                p = s['prompts'][pid]
                require(p['status'] == 'eligible', 'only eligible prompts can carry')
                p['skipped'] += 1
                self._event(s, 'carry', pid, 'eligible', 'eligible', reason)
        self._run(op)

    def record_idea(self, idea_id, text):
        require(idea_id and text, 'idea ID and text required')
        def op(s):
            require(idea_id not in s['open_ideas'], 'idea already recorded')
            s['open_ideas'][idea_id] = dict(id=idea_id, text=text, status='open', version=1)
            self._event(s, 'idea', idea_id, None, 'open')
        self._run(op)

    def close_idea(self, idea_id, authorization):
        human(authorization, 'close_idea', idea_id)
        def op(s):
            row = s['open_ideas'][idea_id]
            require(row['status'] == 'open', 'idea already closed')
            row.update(status='closed', version=row['version'] + 1, authorization=deepcopy(authorization))
            self._event(s, 'idea', idea_id, 'open', 'closed', authorization)
        self._run(op)

    def filter_prompt(self, prompt_id, *, allowed, reason):
        require(type(allowed) is bool and isinstance(reason, str) and reason.strip(), 'filter needs boolean decision and evidence')
        def op(s):
            p = s['prompts'][prompt_id]
            require(p['status'] == 'eligible', 'filter only eligible prompts')
            p['filter'] = {'allowed': allowed, 'reason': reason, 'version': p['version'] + 1}
            p['version'] += 1
            if not allowed:
                p['status'] = 'held'
                self._event(s, 'prompt', prompt_id, 'eligible', 'held', reason)
            return p
        return self._run(op)

    def release_prompt(self, prompt_id, authorization, *, outcome='eligible'):
        require(outcome in ('eligible', 'released'), 'invalid release outcome')
        human(authorization, 'release_prompt:' + outcome, prompt_id)
        def op(s):
            require(authorization['id'] not in s['releases'], 'release ID already used')
            p = s['prompts'][prompt_id]
            old = p['status']
            p.update(status=outcome, final_outcome={'release': deepcopy(authorization)})
            p.pop('filter', None)
            p['version'] += 1
            s['releases'][authorization['id']] = deepcopy(authorization)
            self._event(s, 'prompt_release', prompt_id, old, outcome, authorization)
        self._run(op)

    def legacy_prompt_state(self, prompt_id, target):
        raise GuardError('B04 arbitrary prompt setters disabled; use air or explicit release')

    def plan(self, clip_id, *, logical_id, slot, lineage, prompt, reference_hashes, spec,
             channel='Ch4', episode=1, season=1, kind='segment', price_cents=0, dependencies=(), route='offline-existing-media'):
        require(kind in ('segment', 'ad', 'house_ad', 'id'), 'unknown queue item kind')
        integer(price_cents, 'price')
        integer(episode, 'episode', 1)
        integer(season, 'season', 1)
        require(clip_id and logical_id and slot and lineage and prompt, 'clip identity and prompt required')
        require(isinstance(route, str) and route.strip(), 'route required')
        def op(s):
            require(clip_id not in s['clips'], 'clip ID already exists')
            self._assets(s, reference_hashes)
            require(len(set(dependencies)) == len(dependencies), 'duplicate dependency')
            require(all(d in s['clips'] and s['clips'][d]['channel'] == channel for d in dependencies), 'unknown dependency or channel mismatch')
            row = dict(id=clip_id, authority_id=s['authority_id'], version=1, logical_id=logical_id, slot=slot, lineage=lineage,
                       prompt=prompt, prompt_hash=digest(prompt), reference_hashes=list(reference_hashes),
                       spec=deepcopy(spec), channel=channel, episode=episode, season=season, kind=kind,
                       price_cents=price_cents, route=route, state='planned', prompt_ids=[], filter_versions={}, dependencies=list(dependencies),
                       invalidated_by=[], proposals=[], consequences=[], reuses=[], observations={},
                       media_hash=None, manifest=None, air_permission=None)
            s['clips'][clip_id] = row
            self._event(s, 'clip', clip_id, None, 'planned')
            return row
        return self._run(op, clip_id=clip_id)

    def place(self, clip_id, prompt_ids):
        def op(s):
            c = s['clips'][clip_id]
            require(c['state'] == 'planned', 'placement requires planned clip')
            for pid in dict.fromkeys(prompt_ids):
                p = s['prompts'][pid]
                require(p['status'] == 'eligible' and p.get('filter', {}).get('allowed'), 'prompt must be eligible and filtered')
                require(pid not in c['filter_versions'] or c['filter_versions'][pid] == p['filter']['version'],
                        'filter changed; create a new placement attempt')
                require(p['channel'] == c['channel'], 'prompt channel mismatch')
                require(p['original_text'] in c['prompt'], 'comment keywords/text must remain verbatim')
                handle = p['contributor_metadata'].get('handle')
                require(not handle or handle.casefold().lstrip('@') not in c['prompt'].casefold(), 'contributor handle in generation prompt')
                if pid not in c['prompt_ids']:
                    c['prompt_ids'].append(pid)
                    c['filter_versions'][pid] = p['filter']['version']
                    p['attempts'].append({'clip_id': clip_id, 'status': 'placed', 'merged_into': clip_id, 'timestamp': now()})
                    self._event(s, 'placement', pid, 'eligible', 'eligible', {'clip_id': clip_id})
            return c
        return self._run(op, clip_id=clip_id)

    def propose(self, clip_id, *, proposals=(), consequences=(), reuses=()):
        def op(s):
            c = s['clips'][clip_id]
            require(c['state'] == 'planned', 'proposals frozen after queue')
            require(c['kind'] == 'segment' or not (proposals or consequences or reuses), 'ads and IDs cannot advance character canon')
            for p in proposals:
                require(p['character_id'] in s['cards'], 'unknown character')
            c['proposals'] = deepcopy(list(proposals))
            c['consequences'] = deepcopy(list(consequences))
            c['reuses'] = deepcopy(list(reuses))
        self._run(op, clip_id=clip_id)

    @staticmethod
    def _manifest(c):
        return {k: deepcopy(c[k]) for k in ('id', 'logical_id', 'slot', 'lineage', 'prompt_hash', 'reference_hashes',
                'spec', 'channel', 'episode', 'season', 'kind', 'price_cents', 'route', 'prompt_ids', 'filter_versions', 'dependencies', 'proposals', 'consequences', 'reuses')}

    @staticmethod
    def _canonical_id(s, logical_id):
        seen = set()
        while logical_id in s['aliases']:
            require(logical_id not in seen, 'alias cycle')
            seen.add(logical_id)
            logical_id = s['aliases'][logical_id]
        return logical_id

    def inventory_excluded(self, logical_id):
        s = self.snapshot()
        return self._excluded(s, logical_id)

    def _excluded(self, s, logical_id, ignore=None):
        key = self._canonical_id(s, logical_id)
        historical = any(self._canonical_id(s, k) == key for k in s['inventory'])
        active = any(c['id'] != ignore and self._canonical_id(s, c['logical_id']) == key
                     and c['state'] in ('queued', 'rendered', 'approved', 'aired') for c in s['clips'].values())
        return historical or active

    def import_inventory(self, rows):
        def op(s):
            for r in rows:
                require(r['state'] in ('rendered', 'approved', 'aired'), 'inventory evidence state unsupported')
                require(r.get('evidence'), 'inventory needs evidence')
                # An inventory AIRED label excludes duplicates but can never establish canon.
                s['inventory'][r['logical_id']] = deepcopy(r)
        self._run(op)

    def _gate(self, s, c, *, settled=False):
        require(digest(c['prompt']) == c['prompt_hash'], 'prompt bytes changed after planning')
        clock = s['clocks'].get(c['channel'], {'away': 0})
        issues = continuity.failures(c['spec'], c['prompt'], s['cards'], clock['away'])
        require(not issues, 'gate: ' + ', '.join(issues))
        require(not c['invalidated_by'], 'dependent premise invalidated')
        require(all(s['clips'][d]['state'] not in EXITS for d in c['dependencies']), 'dependency terminated')
        if settled:
            require(all(s['clips'][d]['state'] == 'aired' for d in c['dependencies']), 'dependency premise is not settled by air')
        self._assets(s, c['reference_hashes'])
        for p in s['prompts'].values():
            handle = p['contributor_metadata'].get('handle')
            require(not handle or handle.casefold().lstrip('@') not in c['prompt'].casefold(), 'contributor handle in generation prompt')
        for cid in c['spec']['cast']:
            require(any(r['hash'] in c['reference_hashes'] for r in s['cards'][cid]['refs']), 'current character still is primary reference')
        for pid in c['prompt_ids']:
            require(s['prompts'][pid]['status'] == 'eligible', 'prompt no longer eligible')
            reviewed = s['prompts'][pid].get('filter', {})
            require(reviewed.get('allowed') is True and reviewed.get('version') == c['filter_versions'].get(pid),
                    'filter changed since placement; reassembly required')

    def set_fixture_budget(self, cents):
        integer(cents, 'fixture budget')
        def op(s):
            require(not s['reservations'], 'budget frozen after reservations')
            s['budget_cents'] = cents
        self._run(op)

    def authorize_batch(self, clip_ids, authorization, ceiling_cents):
        integer(ceiling_cents, 'ceiling')
        def op(s):
            require(len(set(clip_ids)) == len(clip_ids) and clip_ids, 'unique nonempty batch required')
            clips = [s['clips'][cid] for cid in sorted(clip_ids)]
            require(len({c['channel'] for c in clips}) == 1, 'one priced batch per channel')
            require(all(c['state'] == 'queued' for c in clips), 'batch must be queued')
            manifests = [self._manifest(c) for c in clips]
            batch = digest(manifests)
            human(authorization, 'authorize_batch', batch)
            integer(authorization.get('ceiling_cents'), 'authorization ceiling')
            require(sum(c['price_cents'] for c in clips) <= ceiling_cents, 'price ceiling exceeded')
            require(authorization.get('ceiling_cents') == ceiling_cents, 'human yes must bind exact price ceiling')
            row = dict(id=authorization['id'], batch_digest=batch, manifests=manifests,
                       ceiling_cents=ceiling_cents, authorization=deepcopy(authorization), version=1)
            require(row['id'] not in s['approvals'], 'approval ID already used')
            s['approvals'][row['id']] = row
            channel = clips[0]['channel']
            record = s['channel_batches'].setdefault(channel, dict(channel=channel, version=0, revisions=[], execution_history=[]))
            record['version'] += 1
            record['revisions'].append(dict(version=record['version'], approval_id=row['id'], batch_digest=batch,
                items=manifests, inventory_evidence=deepcopy(s['inventory']), ceiling_cents=ceiling_cents,
                mode='offline-fixture', timestamp=now()))
            return row
        return self._run(op)

    def reserve_batch(self, approval_id):
        def op(s):
            a = s['approvals'][approval_id]
            human(a['authorization'], 'authorize_batch', a['batch_digest'])
            current = [self._manifest(s['clips'][m['id']]) for m in a['manifests']]
            require(digest(current) == a['batch_digest'], 'manifest changed since approval')
            total = sum(m['price_cents'] for m in current)
            require(total <= a['ceiling_cents'], 'approval ceiling exceeded')
            existing = sum(r['price_cents'] for r in s['reservations'].values())
            new = [m for m in current if m['id'] not in s['reservations']]
            require(existing + sum(m['price_cents'] for m in new) <= s['budget_cents'], 'fixture budget exceeded')
            for m in current:
                c = s['clips'][m['id']]
                require(c['state'] == 'queued', 'reservation requires queued lifecycle state')
                self._gate(s, c, settled=True)
                old = s['reservations'].get(c['id'])
                require(old is None or old['approval_id'] == approval_id, 'item already reserved for other approval')
                s['reservations'].setdefault(c['id'], dict(approval_id=approval_id, manifest_digest=digest(m),
                                                          price_cents=c['price_cents'], state='reserved'))
            return {'complete': True, 'batch_digest': a['batch_digest'], 'mode': 'offline-fixture'}
        return self._run(op)

    def dispatch(self, clip_id):
        def op(s):
            c = s['clips'][clip_id]
            require(c['state'] == 'queued', 'dispatch requires queued lifecycle state')
            self._gate(s, c, settled=True)
            r = s['reservations'].get(clip_id)
            require(r is not None and r['state'] == 'reserved', 'reservation absent or already dispatched')
            a = s['approvals'][r['approval_id']]
            current = [self._manifest(s['clips'][m['id']]) for m in a['manifests']]
            require(digest(current) == a['batch_digest'] and digest(self._manifest(c)) == r['manifest_digest'], 'approval does not match current manifest')
            require(all(s['reservations'].get(m['id'], {}).get('approval_id') == a['id'] for m in a['manifests']), 'batch reservation incomplete')
            r['state'] = 'mock_dispatched'
            s['channel_batches'][c['channel']]['execution_history'].append(dict(clip_id=clip_id,
                approval_id=a['id'], mode='offline-fixture', spent_cents=0, timestamp=now()))
            self._event(s, 'mock_dispatch', clip_id, 'reserved', 'mock_dispatched', a['batch_digest'])
            return {'mode': 'offline-fixture', 'network_called': False, 'spent_cents': 0, 'manifest': self._manifest(c)}
        return self._run(op, clip_id=clip_id)

    def diagnose_batch(self, clip_ids, *, inventory_complete, inventory_evidence):
        """Read-only estimate, including blockers. Never reserves or changes content to fit."""
        s = self.snapshot()
        require(type(inventory_complete) is bool and inventory_evidence, 'inventory coverage evidence required')
        require(clip_ids and len(set(clip_ids)) == len(clip_ids), 'unique nonempty batch required')
        clips = [s['clips'][cid] for cid in sorted(clip_ids)]
        blockers = []
        if len({c['channel'] for c in clips}) != 1:
            blockers.append('one priced batch per channel')
        if not inventory_complete:
            blockers.append('inventory coverage incomplete')
        for c in clips:
            if c['state'] != 'queued':
                blockers.append(c['id'] + ': lifecycle is not queued')
            if self._excluded(s, c['logical_id'], ignore=c['id']):
                blockers.append(c['id'] + ': logical content already completed or claimed')
            try:
                self._gate(s, c, settled=True)
            except GuardError as exc:
                blockers.append(c['id'] + ': ' + str(exc))
        return dict(mode='offline-fixture', estimate_cents=sum(c['price_cents'] for c in clips),
                    items=[self._manifest(c) for c in clips], inventory_evidence=inventory_evidence,
                    blockers=blockers, structurally_ready=not blockers, executable=False,
                    reason='diagnostic only; no production authority or provider')

    def observe(self, clip_id, prompt_id, appeared_text, *, score, evidence):
        require(type(score) in (int, float) and 0 <= score <= 1 and isinstance(evidence, str) and evidence.strip(), 'landing score and evidence required')
        require(isinstance(appeared_text, str), 'appeared text must be a string')
        def op(s):
            c = s['clips'][clip_id]
            require(c['state'] in ('rendered', 'approved') and prompt_id in c['prompt_ids'], 'observation requires rendered placement')
            c['observations'][prompt_id] = dict(appeared_text=appeared_text.strip(), score=score, evidence=evidence,
                mode='offline-fixture', media_hash=c['media_hash'], prompt_hash=c['prompt_hash'])
            self._ledger_row(s, c, prompt_id, aired=False)
        self._run(op, clip_id=clip_id)

    @staticmethod
    def _ledger_row(s, c, pid, *, aired, receipt_id=None, aired_at=None):
        p = s['prompts'][pid]
        observed = c['observations'].get(pid, {})
        row = dict(prompt_id=pid, contributor_id=p['contributor_id'], requested_text=p['original_text'],
                   appeared_text=observed.get('appeared_text', ''), clip_id=c['id'], aired=aired,
                   receipt_id=receipt_id, aired_at=aired_at, score=observed.get('score', 0), channel=p['channel'],
                   votes=p['votes'], subject_matter=p['subject_matter'], version=1,
                   requested_hash=digest(p['original_text']), observation_evidence=observed.get('evidence'),
                   landed=bool(aired and observed.get('appeared_text', '').strip()),
                   delivery_status=('appeared' if observed.get('appeared_text', '').strip() else 'missed') if aired else 'pending')
        for existing in s['ledger']:
            if (existing['clip_id'], existing['prompt_id']) == (c['id'], pid):
                row['version'] = existing['version'] + 1
                existing.update(row)
                return
        s['ledger'].append(row)

    def commenter_history(self, contributor_id):
        require(isinstance(contributor_id, str) and contributor_id, 'contributor ID required')
        return [row for row in self.snapshot()['ledger'] if row['contributor_id'] == contributor_id]

    def _invalidate(self, s, source):
        frontier, seen = [source], {source}
        while frontier:
            parent = frontier.pop()
            for child in s['clips'].values():
                if parent in child['dependencies'] and child['id'] not in seen:
                    require(child['state'] != 'aired', 'cannot invalidate an already aired dependent')
                    child['invalidated_by'].append(source)
                    self._event(s, 'dependency', child['id'], 'tentative', 'invalidated', source)
                    seen.add(child['id'])
                    frontier.append(child['id'])

    def _exit(self, s, c, target):
        require(target in EXITS and target in EDGES[c['state']], 'illegal terminal exit')
        self._invalidate(s, c['id'])
        if s['slots'].get(c['slot']) == c['id']:
            del s['slots'][c['slot']]
        for pid in c['prompt_ids']:
            p = s['prompts'][pid]
            for attempt in p['attempts']:
                if attempt['clip_id'] == c['id']:
                    attempt['status'] = target
            p['skipped'] += 1
            self._ledger_row(s, c, pid, aired=False)

    def transition(self, clip_id, target, *, evidence=None, crash_hook=None):
        def op(s):
            c = s['clips'][clip_id]
            proof = evidence
            if target == 'aired':
                proof = adapt_trusted_receipt(self, s, c, evidence)
                if isinstance(proof, TrustedNoop):
                    return c
                validate_receipt(proof)
                require(proof['authority_id'] == s['authority_id'], 'receipt authority mismatch')
            if target == 'aired' and c['state'] == 'aired':
                receipt = self.verifier.verify(proof)
                require(s['receipts'].get(receipt['id']) == proof and receipt['clip_id'] == clip_id, 'conflicting replay receipt')
                return c
            require(target in EDGES.get(c['state'], ()), f'illegal transition {c["state"]} -> {target}')
            old = c['state']
            if target == 'queued':
                self._gate(s, c)
                require(not self._excluded(s, c['logical_id'], ignore=clip_id), 'logical content already queued/rendered/approved/aired')
                c['manifest'] = digest(self._manifest(c))
            elif target == 'rendered':
                self._gate(s, c, settled=True)
                require(s['reservations'].get(clip_id, {}).get('state') == 'mock_dispatched', 'guarded mock dispatch required')
                require(isinstance(evidence, dict) and evidence.get('asset_hash') in s['assets'], 'render needs registered media bytes')
                self._assets(s, [evidence['asset_hash']])
                c['media_hash'] = evidence['asset_hash']
                s['inventory'][c['logical_id']] = dict(logical_id=c['logical_id'], state='rendered', evidence=c['media_hash'])
            elif target == 'approved':
                human(evidence, 'approve_air', clip_id)
                require(evidence.get('media_hash') == c['media_hash'] and evidence.get('manifest') == c['manifest'], 'air approval must bind exact media and manifest')
                require(not c['invalidated_by'], 'invalidated clip cannot be approved')
                occupied = s['slots'].get(c['slot'])
                require(occupied is None or occupied == clip_id, 'slot occupied: explicit preemption required')
                c['air_permission'] = deepcopy(evidence)
                s['slots'][c['slot']] = clip_id
            elif target == 'aired':
                self._gate(s, c, settled=True)
                self._assets(s, [c['media_hash']])
                receipt = self.verifier.verify(proof)
                require(receipt.get('id') and receipt['id'] not in s['receipts'], 'receipt already used')
                require(all(receipt.get(k) == c[v] for k, v in (('clip_id', 'id'), ('slot', 'slot'), ('lineage', 'lineage'), ('media_hash', 'media_hash'))), 'receipt slot/timestamp/lineage join mismatch')
                require(s['slots'].get(c['slot']) == clip_id and c['air_permission'], 'receipt occupant lacks air permission')
                require(timestamp(receipt['timestamp']) >= timestamp(c['air_permission']['timestamp']), 'receipt predates approval')
                previous = [r for r in s['receipts'].values() if s['clips'][r['clip_id']]['channel'] == c['channel']]
                require(all(timestamp(receipt['timestamp']) >= timestamp(r['timestamp']) for r in previous),
                        'receipt would move channel playback time backwards')
                require(c['manifest'] == digest(self._manifest(c)), 'manifest changed after queue')
                if c['kind'] == 'segment':
                    index = s['clocks'].get(c['channel'], {'index': 0})['index'] + 1
                    characters.commit(s, c, index)
                    s['commits'].append({'id': len(s['commits']) + 1, 'clip_id': clip_id, 'receipt_id': receipt['id'], 'index': index, 'channel': c['channel']})
                for pid in c['prompt_ids']:
                    p = s['prompts'][pid]
                    observed = c['observations'].get(pid, {})
                    landed = bool(observed.get('appeared_text'))
                    if landed:
                        p.update(status='consumed', final_outcome={'clip_id': clip_id, 'receipt_id': receipt['id'], 'merged_into': clip_id})
                        self._event(s, 'prompt', pid, 'eligible', 'consumed', receipt['id'])
                    else:
                        p['skipped'] += 1
                        registry.record(s, 'dropped comment', clip_id, {'prompt_id': pid, 'reason': 'no rendered appearance evidence'})
                    for attempt in p['attempts']:
                        if attempt['clip_id'] == clip_id:
                            attempt['status'] = 'aired' if landed else 'missed'
                    self._ledger_row(s, c, pid, aired=True, receipt_id=receipt['id'], aired_at=receipt['timestamp'])
                s['receipts'][receipt['id']] = deepcopy(proof)
            elif target in EXITS:
                require(isinstance(evidence, dict) and evidence.get('reason'), 'terminal exit requires reason')
                self._exit(s, c, target)
            c['state'] = target
            c['version'] += 1
            self._event(s, 'clip', clip_id, old, target, evidence)
            if crash_hook:
                crash_hook()
            return c
        return self._run(op, clip_id=clip_id)

    def preempt(self, old_id, new_id, authorization):
        human(authorization, 'preempt', old_id + ':' + new_id)
        def op(s):
            old, new = s['clips'][old_id], s['clips'][new_id]
            require(old['state'] in ('queued', 'rendered', 'approved') and new['state'] in ('planned', 'queued', 'rendered'), 'invalid preemption state')
            require(old['slot'] == new['slot'] and old['spec'].get('anchors') == new['spec'].get('anchors'), 'preemption anchors or slot differ')
            require(set(old['prompt_ids']) <= set(new['prompt_ids']), 'preemption dropped unseen prompt IDs')
            before = old['state']
            self._exit(s, old, 'pulled')
            old.update(state='pulled', version=old['version'] + 1)
            self._event(s, 'clip', old_id, before, 'pulled', authorization)
        self._run(op, clip_id=old_id)

    def settled_head(self, slot):
        s = self.snapshot()
        return next((deepcopy(s['clips'][e['clip_id']]) for e in reversed(s['commits']) if s['clips'][e['clip_id']]['slot'] == slot), None)

    def watch_after_air(self, clip_id, failure_type, evidence, conditions=()):
        def op(s):
            require(s['clips'][clip_id]['state'] == 'aired', 'seam watcher requires air')
            require(isinstance(evidence, str) and evidence.strip() and failure_type, 'problem evidence required')
            return registry.record(s, failure_type, clip_id, evidence, conditions)
        return self._run(op, clip_id=clip_id)

    def resolve_problem(self, problem_id, *, fix_id, evidence):
        """Record a reviewed offline result; never perform or authorize a repair."""
        def op(s):
            row = next((p for p in s['problems'] if p['id'] == problem_id), None)
            require(row is not None and row['status'] == 'open', 'open problem required')
            fix = next((f for f in s['fix_library'] if f['id'] == fix_id), None)
            require(fix is not None and row['fix_id'] == fix_id, 'resolution must match compatible proposed fix')
            require(isinstance(evidence, str) and evidence.strip(), 'resolution evidence required')
            row.update(status='resolved', version=row['version'] + 1,
                       resolution=dict(fix_id=fix_id, evidence=evidence, timestamp=now(), mode='offline-fixture'))
            for proposal in s['fix_queue']:
                if proposal['problem_id'] == problem_id:
                    proposal['status'] = 'resolved'
            self._event(s, 'problem', str(problem_id), 'open', 'resolved', evidence)
        self._run(op)

    def add_fix(self, row):
        def op(s):
            require(row.get('cost_class') in registry.RANK and row.get('problem_solved') and 'conditions' in row and 'conflicts' in row, 'invalid fix entry')
            require(all(f['id'] != row['id'] for f in s['fix_library']), 'duplicate fix ID')
            s['fix_library'].append(deepcopy(row) | {'version': 1})
        self._run(op)

    def version_metadata(self, identifier, fields, *, kind='layer', role='scaffolding'):
        def op(s):
            require(kind in ('layer', 'metadata', 'term'), 'unsupported metadata kind')
            require(role in ('scaffolding', 'continuous_thread'), 'metadata role required')
            require(isinstance(fields, dict) and fields, 'metadata fields required')
            history = s['metadata'].setdefault(identifier, [])
            require(not history, 'published identifiers are immutable; register a new identifier and an audited alias')
            version = len(history) + 1
            row = dict(id=identifier, version=version, kind=kind, role=role, executable_rule=False, fields=deepcopy(fields),
                       field_versions={k: version for k in fields})
            history.append(row)
            self._event(s, 'metadata', identifier, version - 1, version)
            return row
        return self._run(op)

    def swap_alias(self, old, new, *, reason=None, crossover_test=False, boundary=None, bridge_clip=None):
        """Versioned identifier lookup, not a story-state commit or a general boundary rule.

        Episode/bridge evidence is supported only for explicit character crossover tests.
        Metadata notes never become executable rules by being aliased.
        """
        def op(s):
            require(isinstance(reason, str) and reason.strip(), 'alias change needs audit reason')
            require(old != new and old not in s['aliases'], 'alias already assigned or self alias')
            old_kind = 'card' if old in s['cards'] else s['metadata'].get(old, [{}])[0].get('kind')
            new_kind = 'card' if new in s['cards'] else s['metadata'].get(new, [{}])[0].get('kind')
            require(old_kind is not None and old_kind == new_kind, 'alias endpoints must exist and have same kind')
            proof = reason
            if crossover_test:
                require(old_kind == 'card', 'crossover test is character-specific')
                require(bool(boundary) != bool(bridge_clip), 'choose one crossover evidence option')
                if boundary:
                    require(isinstance(boundary, (list, tuple)) and len(boundary) == 2, 'two boundary clips required')
                    prev, following = (s['clips'].get(k) for k in boundary)
                    require(prev and following and prev['state'] == following['state'] == 'aired', 'episode boundary needs two aired clips')
                    require(prev['channel'] == following['channel'] and (prev['season'], prev['episode']) < (following['season'], following['episode']), 'not an episode boundary')
                    commits = [x['clip_id'] for x in s['commits'] if x['channel'] == prev['channel']]
                    require(commits.index(following['id']) == commits.index(prev['id']) + 1, 'boundary clips must be consecutive')
                    proof = list(boundary)
                else:
                    c = s['clips'].get(bridge_clip)
                    require(c and c['state'] == 'aired' and c['spec'].get('bridge') in ('static flip', 'Depth shift'), 'crossover needs aired explicit in-world bridge')
                    proof = bridge_clip
            else:
                require(old_kind != 'card', 'character aliases require an explicit crossover test')
                require(not boundary and not bridge_clip, 'episode/bridge options are only for character crossover tests')
            s['aliases'][old] = new
            self._canonical_id(s, old)
            s['swaps'].append(dict(old=old, new=new, proof=proof, reason=reason,
                                  crossover_test=crossover_test, version=len(s['swaps']) + 1))
            self._event(s, 'alias', old, old, new, proof)
        self._run(op)

    def read_metadata(self, identifier, *, version=None):
        s = self.snapshot()
        key = identifier if version is not None else self._canonical_id(s, identifier)
        history = s['metadata'][key]
        if version is not None:
            integer(version, 'metadata version', 1)
            require(version <= len(history), 'unknown metadata version')
        return deepcopy(history[-1] if version is None else history[version - 1])

    def read_card(self, identifier, *, version=None):
        s = self.snapshot()
        key = identifier if version is not None else self._canonical_id(s, identifier)
        if version is None:
            return deepcopy(s['cards'][key])
        integer(version, 'card version', 1)
        matches = [c for c in s['card_history'][key] if c['version'] == version]
        require(len(matches) == 1, 'unknown character card version')
        return deepcopy(matches[0])
