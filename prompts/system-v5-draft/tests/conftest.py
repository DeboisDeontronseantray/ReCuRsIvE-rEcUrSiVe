import importlib
import pathlib
import socket
import sys

import pytest

sys.dont_write_bytecode = True  # never drop __pycache__ into the live system-v4 tools/ folder

V5 = pathlib.Path(__file__).resolve().parents[1]
REPO = V5.parents[1]
V4 = REPO / "prompts" / "system-v4-20261030"
V4_TOOLS = V4 / "tools"
SE_ENGINE = REPO / "story-engine" / "engine"
FIX = V5 / "fixtures"
NP16 = FIX / "night-porter" / "NP16"
NP17 = FIX / "night-porter" / "NP17"
CHARMETA = FIX / "character-meta"
LEDGER = FIX / "ledger"
DRYRUN = V5 / "out" / "dryrun"
NOW = "2026-10-31T21:20:00-05:00"

# REPO is inserted last so it stays ahead of V5. Otherwise V5/tests shadows the
# repo tests package and lifecycle_support cannot be imported.
for p in (V5, V4_TOOLS, SE_ENGINE, REPO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


class NetworkBlocked(RuntimeError):
    pass


def _blocked(*_a, **_k):
    raise NetworkBlocked("network access is not allowed in system-v5-draft tests")


@pytest.fixture(scope="session", autouse=True)
def no_network():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(socket.socket, "connect", _blocked)
        mp.setattr(socket.socket, "connect_ex", _blocked)
        mp.setattr(socket, "create_connection", _blocked)
        yield


def fixture_inputs(inputs_dir):
    """Dry-run input sources for a fixture clip folder: its comments.jsonl stands in for the live spool (D4), and the
    fixture ledger stands in for the live slot sheet and LINEAGE."""
    return {"spool_path": inputs_dir / "comments.jsonl", "character_meta_dir": CHARMETA, "now": NOW,
            "slots_path": LEDGER / "slots.jsonl", "lineage_path": LEDGER / "lineage.jsonl"}


@pytest.fixture
def v5():
    """Resolve system-v5-draft modules by name at test time."""
    return lambda name: importlib.import_module("prompts.system-v5-draft.intake" if name == "intake" else name)


@pytest.fixture
def assembly_harness(monkeypatch):
    """Keep compiler/format tests independent of queue authority.

    Previous air uses real signed offline receipts. The planned next clip and
    queue methods are explicit test doubles: v42 fixture prompts do not satisfy
    the new canonical D12 contract. Real gate/transition tests live in
    tests/test_lifecycle_batch1.py and never use this compiler harness.
    """
    from tests.lifecycle_support import authority
    import assemble_next as module
    from adapters.v4_bridge import build_prompt_v42

    with authority('NP01', 'NP09', 'NP15', 'NP16', 'BI01') as (life, _, _):
        class CompilerAuthority:
            def __init__(self):
                self.compiled = {}
                self.calls = []

            def snapshot(self):
                state = life.snapshot()
                state['clips'].update(self.compiled)
                # Test display metadata comes from canonical receipt rows.
                slots = {'NP16': 'ch11-q06'}
                for cid, slot in slots.items():
                    state['clips'][cid]['slot'] = slot
                return state

            def place(self, **payload):
                self.calls.append(('place', payload))

            def carry(self, **payload):
                self.calls.append(('carry', payload))

            def transition(self, clip_id, target, **payload):
                self.calls.append((target, {'clip_id': clip_id}))

        compiler = CompilerAuthority()
        real_build = build_prompt_v42.build
        def build(spec, *args, **kwargs):
            result = real_build(spec, *args, **kwargs)
            cid = spec.get('clip_id')
            if cid not in life.snapshot()['clips']:
                compiler.compiled[cid] = {'state': 'planned', 'prompt': result['args']['prompt'], 'channel': spec['channel'], 'kind': 'segment'}
            return result
        monkeypatch.setattr(build_prompt_v42, 'build', build)
        monkeypatch.setattr(module, 'lifecycle_store', lambda supplied=None: supplied or compiler)
        yield compiler
