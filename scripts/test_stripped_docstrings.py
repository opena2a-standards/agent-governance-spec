#!/usr/bin/env python3
"""Tests that each test file under scripts/ passes under python3 -OO.

Run from anywhere:  python3 scripts/test_stripped_docstrings.py

Standard library only. python3 -OO strips the docstrings of the files under
scripts/, so a test that reads one must skip under it. The test
runs each scripts/test_*.py file, this one included, in its own python3 -OO
process; it writes no tracked file.
"""

import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent


class StrippedDocstrings(unittest.TestCase):
    def test_each_test_file_passes_under_python3_OO(self):
        # The run of this file that the test starts is under -OO, where the test skips, so it starts no further run.
        if sys.flags.optimize >= 2:
            self.skipTest("this run is already under python3 -OO")
        files = sorted(SCRIPTS.glob("test_*.py"))
        # This file is among them, so a pattern that matches nothing fails instead of passing with no run.
        self.assertIn(Path(__file__).resolve(), files)
        for path in files:
            with self.subTest(file=path.name):
                result = subprocess.run([sys.executable, "-OO", str(path)],
                                        capture_output=True, text=True, timeout=300)
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
