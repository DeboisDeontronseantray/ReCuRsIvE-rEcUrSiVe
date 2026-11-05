"""Offline metadata/text checks composed with the real continuity authority."""
import importlib
import math
import sys
import re
from pathlib import Path

from .loader import load_policy

BASELINE_PARENT = str(Path(__file__).resolve().parents[1] / 'vendor' / 'astra-final-20261103')


def lifecycle_module():
    """Prefer batch 1's installed package; fall back only when it is absent."""
    try:
        return importlib.import_module('astra_lifecycle')
    except ModuleNotFoundError as exc:
        if exc.name != 'astra_lifecycle':
            raise
        if BASELINE_PARENT not in sys.path:
            sys.path.insert(0, BASELINE_PARENT)
        return importlib.import_module('astra_lifecycle')


_POLICY = load_policy()
_RULES = {r['id']: r for r in _POLICY['rules']}
_lifecycle = lifecycle_module()
from astra_lifecycle import continuity
from astra_lifecycle.contracts import require


def _term_match(text, term):
    # Source entries are literal phrases, except the source's escaped dollar.
    term = '$' if term == r'\$' else term
    left = r'(?<!\w)' if term[0].isalnum() else ''
    right = r'(?!\w)' if term[-1].isalnum() else ''
    return re.search(left + re.escape(term).replace(r'\ ', r'\s+') + right, text, re.I) is not None


def _images_enabled(value):
    return value is not None and value is not False and not (isinstance(value, list) and not value)


def _paths(value):
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value)


def _text_failures(text, meta, *, viewer=False):
    failures = []
    for rid in ('masters_pure', 'overlays_post', 'no_kids', 'no_camera', 'no_handles', 'ft_off', 'viewer_blocklist'):
        if rid == 'viewer_blocklist' and not viewer:
            continue
        if rid in {'masters_pure', 'no_camera'} and meta.get('kind') == 'ad':
            continue
        rule = _RULES[rid]
        hit = any(re.search(p, text, re.I) for p in rule['patterns']) or any(_term_match(text, t) for t in rule['terms'])
        if rid == 'no_handles':
            handles = meta.get('contributor_handles', [])
            if not isinstance(handles, list):
                hit = True
            else:
                hit = hit or any(isinstance(h, str) and h.lstrip('@') and _term_match(text, h.lstrip('@')) for h in handles)
        if hit:
            failures.append('gate:' + rid)
    return failures


def check_prompt(text, meta):
    """Return (allowed, evidence) for A07/filter or Lifecycle.filter_prompt."""
    if not isinstance(text, str) or not text.strip() or not isinstance(meta, dict):
        return False, 'gate:viewer_blocklist:invalid_input'
    issues = _text_failures(text, meta, viewer=True)
    if _images_enabled(meta.get('commenter_images')):
        issues.append('gate:commenter_images_off')
    return not issues, ', '.join(issues) if issues else 'qc:' + _POLICY['version'] + ':allowed'


def check_clip(spec, prompt, meta):
    """Inspect declarations only. Paths/hashes are never opened or probed.

    canon_ref and audio targets belong to spec['metadata']. Other declarations
    may be in that metadata or the supplied meta; supplied values take priority.
    """
    if not isinstance(spec, dict) or not isinstance(prompt, str) or not isinstance(meta, dict):
        return ['gate:invalid_input']
    declared = spec.get('metadata', {})
    if not isinstance(declared, dict):
        return ['gate:invalid_metadata']
    context = {**declared, **meta}
    issues = _text_failures(prompt, context)
    features = context.get('enabled_features', [])
    flags = {
        'masters_pure': context.get('kind') != 'ad' and bool(context.get('contains_ad_text')),
        'overlays_post': bool(context.get('generation_overlays')),
        'no_kids': bool(context.get('contains_kids')),
        'no_camera': context.get('kind') != 'ad' and bool(context.get('looks_into_camera')),
        'commenter_images_off': _images_enabled(context.get('commenter_images')),
        'ft_off': not isinstance(features, list) or any(re.fullmatch(r'FT[- ]?[1-4]', str(f), re.I) for f in features),
    }
    # The held-ad exception is a declaration, not approval or permission to air.
    number = context.get('held_ad_number')
    held_ad = context.get('kind') == 'ad' and context.get('held_ad') is True and type(number) is int and 1 <= number <= 16
    flags['reference_required'] = not held_ad and not (_paths(context.get('reference_images')) or _paths(context.get('reference_hashes')))
    audio = declared.get('audio', {})
    flags['audio_targets'] = not (
        isinstance(audio, dict) and type(audio.get('integrated_lufs')) in (int, float)
        and audio['integrated_lufs'] == -16 and type(audio.get('true_peak_dbtp')) in (int, float)
        and math.isfinite(audio['true_peak_dbtp']) and audio['true_peak_dbtp'] <= -1.5)
    flags['canon_ref'] = not (isinstance(declared.get('canon_ref'), str) and declared['canon_ref'].strip())
    flags['show_me'] = bool(context.get('approval_requested')) and not _paths(context.get('attached_media_paths'))
    issues.extend('gate:' + rid for rid, failed in flags.items() if failed)
    return list(dict.fromkeys(issues))


class QCLifecycle(_lifecycle.Lifecycle):
    """Add QC to continuity; retain every baseline transition/asset guard."""

    def _gate(self, s, c, *, settled=False):
        clock = s['clocks'].get(c['channel'], {'away': 0})
        issues = ['gate:' + f for f in continuity.failures(c['spec'], c['prompt'], s['cards'], clock['away'])]
        issues += check_clip(c['spec'], c['prompt'], {
            'kind': c['kind'], 'reference_hashes': c['reference_hashes'],
            'contributor_handles': [p['contributor_metadata']['handle'] for p in s['prompts'].values()
                                    if p['contributor_metadata'].get('handle')],
        })
        require(not issues, ', '.join(issues))
        super()._gate(s, c, settled=settled)
