"""Put the repo root on sys.path so layers_v4 can import astra_lifecycle."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
