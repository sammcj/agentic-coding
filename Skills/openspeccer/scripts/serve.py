#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run the openspeccer dashboard for an OpenSpec repository. Stdlib only."""

import sys
from pathlib import Path

# Kept parseable by old interpreters so an outdated python3 gets a usable message instead of an
# ImportError from deep inside the package.
if sys.version_info < (3, 11):
    found = "%d.%d" % sys.version_info[:2]
    sys.exit("openspeccer needs Python 3.11+ (found " + found + "). Run: uv run " + __file__)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from openspeccer.cli import main

if __name__ == "__main__":
    sys.exit(main())
