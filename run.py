#!/usr/bin/env python3
"""Run with Python 3.10+. No pip install, account, or API key needed."""
import sys

if sys.version_info < (3, 10):
    raise SystemExit("Lumen needs Python 3.10 or newer. No other packages are required.")

from lumen.server import main

if __name__ == "__main__":
    main()
