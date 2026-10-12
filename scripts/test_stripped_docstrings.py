#!/usr/bin/env python3
"""Tests that each test file under scripts/ passes under python3 -OO and
python3 -O, and that each python3 run a test starts has a timeout.

Run from anywhere:  python3 scripts/test_stripped_docstrings.py

Standard library only. python3 -OO strips the docstrings of the files under
scripts/, so a test that reads one must skip under it. python3 -O keeps
them, so no test may skip for that reason under it. The tests run each
scripts/test_*.py file, this one included, in its own python3 -OO process
and in its own python3 -O process; they write no tracked file.
"""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent


def scripts_test_files(test):
    """The scripts/test_*.py files, which must include this one."""
    files = sorted(SCRIPTS.glob("test_*.py"))
    # This file is among them, so a pattern that matches nothing fails instead of passing with no run.
    test.assertIn(Path(__file__).resolve(), files)
    return files


class StrippedDocstrings(unittest.TestCase):
    def test_each_test_file_passes_under_python3_OO(self):
        # The run of this file that the test starts is under -OO, where the test skips, so it starts no further run.
        if sys.flags.optimize >= 2:
            self.skipTest("this run is already under python3 -OO")
        for path in scripts_test_files(self):
            with self.subTest(file=path.name):
                result = subprocess.run([sys.executable, "-OO", str(path)],
                                        capture_output=True, text=True, timeout=300)
                self.assertEqual(0, result.returncode, result.stderr)

    def test_each_test_file_passes_under_python3_O_with_no_python3_OO_skip(self):
        # python3 -O keeps docstrings, so a skip whose reason names python3 -OO must not fire under it: a guard
        # written as sys.flags.optimize >= 1 instead of >= 2 passes every run without -O and every run under -OO.
        # The runs of this file that the tests start are optimized, where this test skips, so it starts no further run.
        if sys.flags.optimize >= 1:
            self.skipTest("this run is already optimized, so it starts no python3 -O run")
        for path in scripts_test_files(self):
            with self.subTest(file=path.name):
                result = subprocess.run([sys.executable, "-O", str(path), "-v"],
                                        capture_output=True, text=True, timeout=300)
                self.assertEqual(0, result.returncode, result.stderr)
                skips = [line for line in result.stderr.splitlines()
                         if " ... skipped " in line and "-OO" in line.split(" ... skipped ", 1)[1]]
                self.assertEqual([], skips)


class ChildRuns(unittest.TestCase):
    def test_each_python3_run_that_a_test_starts_has_a_timeout(self):
        # A run that stops responding then fails its own test instead of stalling the whole suite.
        files_with_runs = set()
        for path in scripts_test_files(self):
            tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and ast.unparse(node.func) == "subprocess.run" and node.args
                        and isinstance(node.args[0], ast.List) and node.args[0].elts
                        and ast.unparse(node.args[0].elts[0]) == "sys.executable"):
                    files_with_runs.add(path.name)
                    with self.subTest(file=path.name, line=node.lineno):
                        self.assertIn("timeout", [keyword.arg for keyword in node.keywords])
        # The files that start a python3 run are found, so a change to the form of the call fails instead of
        # passing with nothing checked.
        self.assertLessEqual({"test_check_docs_prose.py", "test_gitignore.py", Path(__file__).name}, files_with_runs)


if __name__ == "__main__":
    unittest.main()
