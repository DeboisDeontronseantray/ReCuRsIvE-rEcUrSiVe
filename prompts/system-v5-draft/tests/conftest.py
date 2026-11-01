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
DRYRUN = V5 / "out" / "dryrun"
NOW = "2026-10-31T21:20:00-05:00"

for p in (V5, V4_TOOLS, SE_ENGINE):
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
    """Dry-run input sources for a fixture clip folder: its comments.jsonl stands in for the live spool (D4)."""
    return {"spool_path": inputs_dir / "comments.jsonl", "character_meta_dir": CHARMETA, "now": NOW}


@pytest.fixture
def v5():
    """Resolve system-v5-draft modules by name at test time."""
    return importlib.import_module
