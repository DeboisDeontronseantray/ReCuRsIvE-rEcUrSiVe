"""Read-only adapter inventory and enforceable audit for lifecycle consumers.

This does not alter legacy installations. It records exact call-site seams and
rejects imports/calls that would bypass the gateway in an integrated consumer.
"""
import ast
from pathlib import Path
import json

from .contracts import ROOT, file_hash


def _repo(rel):
    return str(ROOT / rel)


# Commenter pipeline, de-parity, and the seed clip_render live outside this repo.
# Rows stay so the inventory is complete; tests do not import those callers.
_OUT_OF_SCOPE = 'out-of-scope'

SOURCES = [
    ('D09', _repo('prompts/system-v5-draft/aired.py'), ['build_index', 'require_aired'], 'D09/aired and derive_aired'),
    ('D09', _repo('lineage/aired.py'), ['clip_id_aired', 'build_aired_index'], 'derive_aired reads only the canonical store'),
    ('D09', _repo('lineage/air_status.py'), ['source_indicates_aired'], 'authorization/status booleans cannot establish air'),
    ('D09', _repo('lineage/derive_aired.py'), ['append_aired_derivation_for_clip', 'derive_aired_append_patches'], 'receipt event projection; no independent air latch'),
    ('D13', _repo('prompts/system-v5-draft/intake.py'), ['mark_consumed', 'load_consumed'], 'D13/place; consumption from verified air'),
    ('D14', _repo('prompts/system-v5-draft/placement.py'), ['place'], 'pure placement plus D14/carry and eligible'),
    ('D15', _repo('prompts/system-v5-draft/memory.py'), ['summon', 'proposed_update'], 'D15/propose; receipt reducer commits counters'),
    ('D10', _repo('charmeta/promote.py'), [], 'D10/propose; receipt reducer commits traits'),
    ('B01', _repo('story-engine/live/checker.py'), ['approve', 'rollback', 'slot_head'], 'B01/approve, preempt, head'),
    ('B04', _repo('story-engine/live/checker.py'), ['set_state', 'combine', 'hold_prompt'], 'canonical placement/filter/release; no arbitrary setters'),
    ('B04', _repo(f'{_OUT_OF_SCOPE}/commenter-pipeline/comment_prompts.py'), ['set_status', 'bump_skip', 'current'], 'canonical prompt projection and D14/carry'),
    ('B01', _repo(f'{_OUT_OF_SCOPE}/de-parity/pickup.py'), ['preempt', 'rollback', 'retire', 'clip_airing'], 'canonical preemption and terminal transitions; verified air only'),
    ('B04', _repo(f'{_OUT_OF_SCOPE}/de-parity/pickup.py'), ['prompt_state', 'unterminated', 'prompts_block'], 'canonical eligible/consumed/released projection'),
    ('D08', _repo('story-engine/server/app/tv/pipeline.py'), [], 'D08/local_export and episodes_done projection'),
    ('A07', _repo(f'{_OUT_OF_SCOPE}/commenter-pipeline/pipeline.py'), [], 'A07/intake before seen; filter and recover'),
    ('D09', _repo('story-engine/live/intake.py'), ['pick_end_frame'], 'last frame may derive only from verified canonical air'),
    ('D12', _repo('prompts/system-v5-draft/assemble_next.py'), [], 'D12/assemble gate must succeed before production'),
    ('D16', _repo('prompts/system-v4-20261030/tools/layers_v4.py'), ['tier_alive'], 'canonical consequence clock; D16/propose'),
    ('D17', _repo('prompts/system-v4-20261030/tools/layers_v4.py'), ['carry_text'], 'D17/propose with attested registered still'),
    ('render', _repo(f'{_OUT_OF_SCOPE}/clip_render.py'), ['render'], 'render/reserve, dispatch, rendered; offline adapter only'),
]
LEGACY_MODULES = {'checker', 'intake', 'aired', 'air_status', 'derive_aired', 'promote', 'pipeline',
                  'comment_prompts', 'layers_v4', 'memory', 'clip_render', 'run_seed', 'pickup'}
UNSAFE_CALLS = {'mark_consumed', 'load_consumed', 'set_state', 'set_status', 'bump_skip', 'combine', 'tier_alive', 'carry_text', 'summon',
                'source_indicates_aired', 'build_aired_index', 'append_aired_derivation_for_clip'}
NETWORK_MODULES = {'socket', 'requests', 'urllib', 'http', 'httpx', 'aiohttp', 'subprocess', 'importlib'}


def audit_source(source, *, filename='<consumer>'):
    errors = []
    for node in ast.walk(ast.parse(source, filename)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = set(alias.name.split('.'))
                if parts & (LEGACY_MODULES | NETWORK_MODULES):
                    errors.append(f'{filename}:{node.lineno}: forbidden external import {alias.name}')
        elif isinstance(node, ast.ImportFrom):
            parts = set((node.module or '').split('.'))
            imported = {alias.name for alias in node.names}
            # Internal canonical imports remain allowed. Consumer relative legacy imports do not.
            internal = Path(filename).parent == ROOT / 'astra_lifecycle'
            if (parts | imported) & (LEGACY_MODULES | NETWORK_MODULES) and not (node.level and internal):
                errors.append(f'{filename}:{node.lineno}: forbidden external import {node.module}')
            if imported & UNSAFE_CALLS:
                errors.append(f'{filename}:{node.lineno}: imported legacy transition symbol')
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ''
            if name in UNSAFE_CALLS:
                errors.append(f'{filename}:{node.lineno}: legacy transition call {name}')
            if name in ('exec', 'eval', '__import__') and Path(filename).name != 'legacy.py':
                errors.append(f'{filename}:{node.lineno}: dynamic execution bypass')
            if name == 'getattr' and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and node.args[1].value in UNSAFE_CALLS:
                errors.append(f'{filename}:{node.lineno}: reflected legacy transition call')
    return errors


def source_inventory():
    rows = []
    for machine, path, symbols, replacement in SOURCES:
        p = Path(path)
        row = dict(machine=machine, source=path, replacement=replacement, present=p.is_file(),
                   expected_symbols=symbols, deployment='read-only; overlay not installed upstream')
        if p.is_file():
            row['sha256'] = file_hash(p)
            tree = ast.parse(p.read_text())
            row['definitions'] = [{'name': n.name, 'line': n.lineno} for n in tree.body
                                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not symbols or n.name in symbols)]
        rows.append(row)
    return rows


def run_audit():
    errors = []
    for path in sorted((ROOT / 'astra_lifecycle').glob('*.py')):
        errors.extend(audit_source(path.read_text(), filename=str(path)))
    return {'status': 'PASS' if not errors else 'FAIL', 'errors': errors,
            'scope': 'offline lifecycle package; legacy installations remain read-only',
            'source_inventory': source_inventory()}


if __name__ == '__main__':
    result = run_audit()
    (ROOT / 'reports/adapter-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'errors': result['errors']}))
    raise SystemExit(bool(result['errors']))
