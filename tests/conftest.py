import pytest

from tests.lifecycle_support import authority


@pytest.fixture
def canonical_history(monkeypatch):
    """Existing history tests now obtain air from signed receipts, never flags."""
    ids = [f'{prefix}-aired-{i}' for prefix in ('test', 'e2e') for i in range(1, 4)]
    with authority(*ids) as (life, _, _):
        monkeypatch.setenv('TT_LIFECYCLE_DB', str(life.path))
        yield life
