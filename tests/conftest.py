"""
conftest.py — Pytest configuration for Lár DMN test suite.
Ensures that both `src/lar` and `src/brain` are importable in all test files.
"""
import sys
import os

# Add the src/ directory to the path so that both `lar` and `brain` packages
# resolve correctly regardless of which directory pytest is invoked from.
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
