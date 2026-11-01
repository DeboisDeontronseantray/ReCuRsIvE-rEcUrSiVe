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
DRYRUN = V5 / "out" / "dryrun"

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


@pytest.fixture
def v5():
    """Resolve system-v5-draft modules by name at test time.

    The assembler modules do not exist until later steps of docs/IMPLEMENTATION-STEPS-v1.md,
    so the skipped acceptance specs must still collect without them."""
    return importlib.import_module
