"""Lab 001 test path setup for importlib-compatible collection."""

import sys
from pathlib import Path

_LAB001_TESTS = str(Path(__file__).resolve().parent)
if _LAB001_TESTS not in sys.path:
    sys.path.insert(0, _LAB001_TESTS)
