"""Make the project root importable for the test suite.

Run with ``./bridge/bin/python -m pytest -q`` (or ``make test``) from the repo root.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
