#!/usr/bin/env python3
"""Tests that each test file under scripts/ passes under python3 -OO and
python3 -O, and that each process a test file starts through the subprocess
module has a timeout.

Run from anywhere:  python3 scripts/test_stripped_docstrings.py

Standard library only. python3 -OO strips the docstrings of the files under
scripts/, so a test that reads one must skip under it. python3 -O keeps
them, so no test may skip for that reason under it. The tests run each
scripts/test_*.py file, this one included, once in its own python3 -OO
process and once in its own python3 -O process, and check that the python3
-O run starts no python3 -OO process; they write no tracked file.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent

# Set in the environment of each python3 -O run that the -O test starts.
PYTHON3_O_RUN = "ABGS_PYTHON3_O_RUN"
# The -O test reports each skip under python3 -O whose reason names python3 -OO, so this reason names neither.
NESTED_SKIP = "the run of this file that started this one runs each test file with docstrings stripped"
# Runs the test file its second argument names as python3 runs a file, and appends the arguments of each process that
# file starts to the file its first argument names, one JSON list per line.
RECORD_STARTS = "\n".join([
    "import json, os, runpy, sys",
    "log, sys.argv = sys.argv[1], sys.argv[2:]",
    "def record(event, args):",
    "    if event == 'subprocess.Popen':",
    "        with open(log, 'a', encoding='utf-8') as out:",
    "            out.write(json.dumps([os.fsdecode(arg) for arg in args[1]]) + '\\n')",
    "sys.addaudithook(record)",
    "sys.path[0] = os.path.dirname(os.path.abspath(sys.argv[0]))",
    "runpy.run_path(sys.argv[0], run_name='__main__')",
])

# The subprocess functions that take a timeout, and those that start a process and take none.
TIMED = {"run", "call", "check_call", "check_output"}
UNTIMED = {"Popen", "getoutput", "getstatusoutput"}


def scripts_test_files(test):
    """The scripts/test_*.py files, which must include this one."""
    files = sorted(SCRIPTS.glob("test_*.py"))
    # This file is among them, so a pattern that matches nothing fails instead of passing with no run.
    test.assertIn(Path(__file__).resolve(), files)
    return files


def untimed_runs(source):
    """The (line, problem) pairs for each process the source starts through subprocess with no timeout, and whether
    it calls a subprocess function that takes one."""
    tree = ast.parse(source)
    calls = {id(node.func): node for node in ast.walk(tree) if isinstance(node, ast.Call)}
    problems = []
    has_runs = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            problems += [(node.lineno, "imports subprocess as " + alias.asname) for alias in node.names
                         if alias.name == "subprocess" and alias.asname not in (None, "subprocess")]
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            problems.append((node.lineno, "imports names from subprocess"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "subprocess":
            if node.attr in UNTIMED:
                problems.append((node.lineno, f"subprocess.{node.attr} takes no timeout"))
            elif node.attr in TIMED:
                has_runs = True
                # A reference that is not called, for example one passed to functools.partial, is reported too.
                call = calls.get(id(node))
                timeout = None if call is None else next(
                    (keyword.value for keyword in call.keywords if keyword.arg == "timeout"), None)
                if timeout is None or (isinstance(timeout, ast.Constant) and timeout.value is None):
                    problems.append((node.lineno, f"subprocess.{node.attr} has no timeout"))
                # A name or an expression can hold None, for example T = None then timeout=T, so only a number
                # written in the call counts.
                elif not (isinstance(timeout, ast.Constant) and type(timeout.value) in (int, float)):
                    problems.append((node.lineno, f"subprocess.{node.attr} has a timeout that is not a number"))
    return sorted(problems), has_runs


class StrippedDocstrings(unittest.TestCase):
    def test_each_test_file_passes_under_python3_OO(self):
        # The run of this file that the test starts is under -OO, where the test skips, so it starts no further run.
        if sys.flags.optimize >= 2:
            self.skipTest("this run is already under python3 -OO")
        # The python3 -O run of this file that the -O test starts would otherwise run each test file under -OO a
        # second time. A python3 -O run without the marker, started by hand, still runs them.
        if sys.flags.optimize == 1 and PYTHON3_O_RUN in os.environ:
            self.skipTest(NESTED_SKIP)
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
        recorded = []
        for path in scripts_test_files(self):
            with self.subTest(file=path.name), tempfile.TemporaryDirectory() as directory:
                log = Path(directory) / "started.jsonl"
                result = subprocess.run([sys.executable, "-O", "-c", RECORD_STARTS, str(log), str(path), "-v"],
                                        env={**os.environ, PYTHON3_O_RUN: "1"},
                                        capture_output=True, text=True, timeout=300)
                self.assertEqual(0, result.returncode, result.stderr)
                started = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] \
                    if log.exists() else []
                recorded += started
                # The test above runs each test file under python3 -OO, so a test file that runs itself under -OO
                # skips that run where PYTHON3_O_RUN is set; otherwise a discover run starts a third -OO run of it.
                self.assertEqual([], [args for args in started if "-OO" in args])
                skips = [line for line in result.stderr.splitlines()
                         if " ... skipped " in line and "-OO" in line.split(" ... skipped ", 1)[1]]
                self.assertEqual([], skips)
                if path == Path(__file__).resolve():
                    # The python3 -O run of this file starts no python3 -OO run of each test file.
                    outcomes = [line.split(" ... ", 1)[-1] for line in result.stderr.splitlines()
                                if line.startswith("test_each_test_file_passes_under_python3_OO ")]
                    self.assertEqual([f"skipped {NESTED_SKIP!r}"], outcomes)
        # The test files start git runs under -O too, so a recorder that records nothing fails instead of passing with
        # no process checked.
        self.assertNotEqual([], recorded)


class NestedRuns(unittest.TestCase):
    def test_the_python3_O_run_of_this_file_starts_no_python3_OO_run(self):
        result = unittest.TestResult()
        with mock.patch.object(sys, "flags", mock.Mock(optimize=1)), \
                mock.patch.dict(os.environ, {PYTHON3_O_RUN: "1"}), \
                mock.patch.object(subprocess, "run", side_effect=self.failureException("started a run")) as run:
            StrippedDocstrings("test_each_test_file_passes_under_python3_OO").run(result)
        run.assert_not_called()
        self.assertEqual([NESTED_SKIP], [reason for _, reason in result.skipped])
        self.assertNotIn("-OO", NESTED_SKIP)

    def test_a_python3_O_run_without_the_marker_runs_each_test_file_under_python3_OO(self):
        result = unittest.TestResult()
        environment = {name: value for name, value in os.environ.items() if name != PYTHON3_O_RUN}
        with mock.patch.object(sys, "flags", mock.Mock(optimize=1)), \
                mock.patch.dict(os.environ, environment, clear=True), \
                mock.patch.object(subprocess, "run", return_value=mock.Mock(returncode=0, stderr="")) as run:
            StrippedDocstrings("test_each_test_file_passes_under_python3_OO").run(result)
        self.assertEqual(([], [], []), (result.skipped, result.failures, result.errors))
        self.assertEqual(len(scripts_test_files(self)), run.call_count)


class ChildRuns(unittest.TestCase):
    def test_each_process_that_a_test_file_starts_through_subprocess_has_a_timeout(self):
        # A run that stops responding then fails its own test instead of stalling the whole suite.
        files_with_runs = set()
        for path in scripts_test_files(self):
            problems, has_runs = untimed_runs(path.read_text(encoding="utf-8"))
            if has_runs:
                files_with_runs.add(path.name)
            with self.subTest(file=path.name):
                self.assertEqual([], problems)
        # The files that start a process are found, so a change to the form of the call fails instead of passing with
        # nothing checked.
        self.assertLessEqual({"test_check_crosswalks.py", "test_check_docs_prose.py", "test_github_action.py",
                              "test_gitignore.py", "test_gitlab_ci.py", "test_integrations.py", Path(__file__).name},
                             files_with_runs)

    def test_a_run_of_a_command_held_in_a_name_and_a_popen_are_reported(self):
        source = "\n".join([
            "import subprocess",
            "cmd = [sys.executable, '-c', 'pass']",
            "subprocess.run(cmd)",
            "subprocess.Popen([sys.executable, '-c', 'pass']).wait()",
            "subprocess.check_output(['git', '--version'], timeout=None)",
            "subprocess.run(['bash', '-c', 'true'], timeout=60)",
        ])
        self.assertEqual(([(3, "subprocess.run has no timeout"), (4, "subprocess.Popen takes no timeout"),
                           (5, "subprocess.check_output has no timeout")], True), untimed_runs(source))

    def test_a_timeout_that_is_not_a_number_written_in_the_call_is_reported(self):
        source = "\n".join([
            "import subprocess",
            "T = None",
            "subprocess.run(['true'], timeout=T)",
            "subprocess.call(['true'], timeout=True)",
            "subprocess.check_call(['true'], timeout=60.0)",
        ])
        self.assertEqual(([(3, "subprocess.run has a timeout that is not a number"),
                           (4, "subprocess.call has a timeout that is not a number")], True), untimed_runs(source))

    def test_a_subprocess_function_reached_without_the_module_name_is_reported(self):
        source = "\n".join([
            "import subprocess as sp",
            "from subprocess import run",
            "import functools",
            "functools.partial(subprocess.call, ['true'])",
        ])
        self.assertEqual(([(1, "imports subprocess as sp"), (2, "imports names from subprocess"),
                           (4, "subprocess.call has no timeout")], True), untimed_runs(source))


if __name__ == "__main__":
    unittest.main()
