"""Read and validate the versioned, local policy snapshot (stdlib only)."""
import json
from pathlib import Path
import re

POLICY_PATH = Path(__file__).with_name('policy.json')
RULE_IDS = frozenset({
    'masters_pure', 'overlays_post', 'no_kids', 'no_camera', 'reference_required',
    'commenter_images_off', 'no_handles', 'ft_off', 'audio_targets',
    'show_me', 'canon_ref', 'viewer_blocklist',
})


class PolicyError(ValueError):
    """The snapshot is incomplete or incompatible with this evaluator."""


def validate_policy(policy):
    """Reject unknown/missing rules and malformed evaluator configuration."""
    def need(ok, message):
        if not ok:
            raise PolicyError(message)

    need(isinstance(policy, dict), 'policy must be an object')
    need(set(policy) == {'schema_version', 'version', 'rules', 'blocklist_note'}, 'invalid policy fields')
    need(type(policy['schema_version']) is int and policy['schema_version'] == 1, 'unsupported schema_version')
    need(isinstance(policy['version'], str) and bool(policy['version'].strip()), 'version required')
    need(isinstance(policy['blocklist_note'], str) and bool(policy['blocklist_note'].strip()), 'blocklist note required')
    rules = policy['rules']
    need(isinstance(rules, list), 'rules must be a list')
    seen = set()
    for rule in rules:
        need(isinstance(rule, dict), 'rule must be an object')
        need(set(rule) == {'id', 'source', 'severity', 'description', 'patterns', 'terms'}, 'invalid rule fields')
        rid = rule['id']
        need(isinstance(rid, str) and rid in RULE_IDS and rid not in seen, 'unknown or duplicate rule id')
        seen.add(rid)
        need(rule['severity'] == 'error', 'all fixture rules must block')
        for key in ('source', 'description'):
            need(isinstance(rule[key], str) and bool(rule[key].strip()), key + ' required')
        for key in ('patterns', 'terms'):
            need(isinstance(rule[key], list) and all(isinstance(v, str) and v.strip() for v in rule[key]), key + ' must contain strings')
            need(len(set(rule[key])) == len(rule[key]), 'duplicate ' + key)
        for pattern in rule['patterns']:
            try:
                re.compile(pattern, re.I)
            except re.error as exc:
                raise PolicyError('invalid pattern: ' + rid) from exc
        if rid in {'masters_pure', 'overlays_post', 'no_camera', 'no_handles', 'ft_off'}:
            need(bool(rule['patterns']), 'patterns required: ' + rid)
        if rid in {'no_kids', 'viewer_blocklist'}:
            need(bool(rule['terms']), 'terms required: ' + rid)
    need(seen == RULE_IDS, 'missing policy rules')
    return policy


def load_policy(path=POLICY_PATH):
    """Only this JSON file is read; no source files or media are consulted."""
    try:
        with Path(path).open(encoding='utf-8') as stream:
            return validate_policy(json.load(stream))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise PolicyError('invalid policy JSON') from exc

