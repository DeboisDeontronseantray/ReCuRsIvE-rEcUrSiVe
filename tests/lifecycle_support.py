"""Offline test authority using existing bytes; never invokes a renderer."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from astra_lifecycle import Lifecycle
from astra_lifecycle.fixture import setup, plan, render, air


@contextmanager
def authority(*aired_ids):
    # The unchanged foundation confines SQLite writes to its repository root.
    with TemporaryDirectory(dir=Path(__file__).parent, prefix='astra-test-') as folder:
        life = Lifecycle(Path(folder) / 'state.sqlite')
        ref, media = setup(life)
        for cid in aired_ids:
            plan(life, cid)
            render(life, cid, media)
            air(life, cid)
        yield life, ref, media
