"""Read-only extraction of reviewed pure helpers; never import legacy modules.

This avoids top-level file writes, environment mutation and provider imports.
Only exact allowlisted definitions can be requested; their source digest is
returned for audit. Transition functions are intentionally absent.
"""
import ast
import re
from .contracts import ROOT, digest, require

CHECKER = ROOT / 'story-engine/live/checker.py'
PLACEMENT = ROOT / 'prompts/system-v5-draft/placement.py'
ALLOW = {
    'fingerprint': (CHECKER, ('fingerprint',)),
    'similarity': (CHECKER, ('fingerprint', 'similarity')),
    'classify_duplicate': (CHECKER, ('fingerprint', 'similarity', 'classify_duplicate')),
    'beat_times': (PLACEMENT, ('beat_times',)),
}


def read_pure(name):
    require(name in ALLOW, 'direct legacy transition logic is forbidden')
    path, names = ALLOW[name]
    tree = ast.parse(path.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    require(len(nodes) == len(names), 'legacy helper source changed')
    # Explicitly reject side effects even in a future changed helper.
    forbidden = {'open', 'exec', 'eval', 'compile', '__import__', 'setattr', 'delattr'}
    for node in nodes:
        require(not any(isinstance(n, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)) for n in ast.walk(node)), 'helper imports or global writes forbidden')
        require(not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in forbidden for n in ast.walk(node)), 'helper side effects forbidden')
    unit = ast.Module(body=nodes, type_ignores=[])
    namespace = {'re': re}
    exec(compile(unit, '<reviewed-pure-helper>', 'exec'), namespace)
    return namespace[name], {'source': str(path), 'function': name, 'ast_digest': digest(ast.dump(unit))}
