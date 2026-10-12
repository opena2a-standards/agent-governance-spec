#!/usr/bin/env python3
"""Tests that each test file under scripts/ passes under python3 -OO and
python3 -O, that each process a test file starts through the subprocess
module has a timeout, and for the wording of the CHANGELOG.md entry about
the python3 -O runs, of a comment in this file, of the docstring of
written_number and of this docstring.

Run from anywhere:  python3 scripts/test_stripped_docstrings.py

Standard library only. python3 -OO strips the docstrings of the files under
scripts/, so a test that reads one must skip under it. python3 -O keeps
them, so no test may skip for that reason under it. The tests run each
scripts/test_*.py file, this one included, once in its own python3 -OO
process and once in its own python3 -O process, check that the python3 -O
run starts no python3 -OO process, and read CHANGELOG.md and the source of
this file; they write no tracked file.
"""

import ast
import inspect
import json
import math
import operator
import os
import subprocess
import sys
import tempfile
import tokenize
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent
CHANGELOG = SCRIPTS.parent / "CHANGELOG.md"

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
# The operators a timeout written in the call may apply to number literals, for example -1 or 5 * 60. ** is not one,
# since 10 ** 10 ** 10 takes longer to compute than any run it would bound.
UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
BINARY_OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def scripts_test_files(test):
    """The scripts/test_*.py files, which must include this one."""
    files = sorted(SCRIPTS.glob("test_*.py"))
    # This file is among them, so a pattern that matches nothing fails instead of passing with no run.
    test.assertIn(Path(__file__).resolve(), files)
    return files


def written_value(node):
    """The value of an int or float literal, or of the operators above applied to them; None for any other
    expression, and for one that raises when it is evaluated."""
    if isinstance(node, ast.Constant):
        # isinstance(True, int) holds, so the type is compared exactly and timeout=True is reported.
        return node.value if type(node.value) in (int, float) else None
    if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
        operand = written_value(node.operand)
        return None if operand is None else UNARY_OPERATORS[type(node.op)](operand)
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY_OPERATORS:
        left, right = written_value(node.left), written_value(node.right)
        if left is None or right is None:
            return None
        try:
            return BINARY_OPERATORS[type(node.op)](left, right)
        # 60 / 0 raises ZeroDivisionError when the call runs, and a quotient of ints too large for a float raises
        # OverflowError.
        except (ZeroDivisionError, OverflowError):
            return None
    return None


def written_number(node):
    """Whether the expression is a number written in the call: an int or float literal, or the operators above
    applied to them, that evaluates to a finite number that fits in a float."""
    value = written_value(node)
    try:
        # A float that overflows to inf, or inf - inf, bounds no run.
        return value is not None and math.isfinite(value)
    except OverflowError:
        # An int too large for a float raises when the call adds it to the clock.
        return False


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
                # A name or an expression that reads one can hold None, for example T = None then timeout=T, so only
                # a number written in the call counts.
                elif not written_number(timeout):
                    problems.append((node.lineno,
                                     f"subprocess.{node.attr} has a timeout that is not a number written in the call"))
    return sorted(problems), has_runs


def comment_text(function):
    """The comments in the source of the function, without their # marks, joined by single spaces."""
    lines, _ = inspect.getsourcelines(function)
    tokens = tokenize.generate_tokens(iter(lines).__next__)
    return " ".join(" ".join(token.string.lstrip("#").split()) for token in tokens if token.type == tokenize.COMMENT)


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
        self.assertEqual(([(3, "subprocess.run has a timeout that is not a number written in the call"),
                           (4, "subprocess.call has a timeout that is not a number written in the call")], True),
                         untimed_runs(source))

    def test_a_timeout_written_as_arithmetic_on_numbers_is_accepted(self):
        source = "\n".join([
            "import subprocess",
            "T = 60",
            "subprocess.run(['true'], timeout=5 * 60)",
            "subprocess.call(['true'], timeout=-1)",
            "subprocess.check_call(['true'], timeout=+(2.5 * 60 + 30) / 2 - 1)",
            "subprocess.call(['true'], timeout=1 / (3 - 1))",
            "subprocess.check_call(['true'], timeout=1 / (2 + 1))",
            "subprocess.check_output(['true'], timeout=5 * T)",
            "subprocess.run(['true'], timeout=-True)",
            "subprocess.run(['true'], timeout=10 ** 10 ** 10)",
            "subprocess.run(['true'], timeout=60 if T else None)",
            "subprocess.run(['true'], timeout=not 0)",
        ])
        problem = "has a timeout that is not a number written in the call"
        self.assertEqual(([(8, f"subprocess.check_output {problem}"), (9, f"subprocess.run {problem}"),
                           (10, f"subprocess.run {problem}"), (11, f"subprocess.run {problem}"),
                           (12, f"subprocess.run {problem}")], True), untimed_runs(source))

    def test_a_timeout_written_as_arithmetic_that_is_not_a_finite_number_is_reported(self):
        # Each run but the last raises when the call runs, or bounds no run, so none is a number written in the call.
        # The last, timeout=60 / 2, is the accepted control: it bounds the run at 30 seconds.
        source = "\n".join([
            "import subprocess",
            "subprocess.run(['true'], timeout=60 / 0)",
            "subprocess.call(['true'], timeout=60 / (1 - 1.0))",
            "subprocess.check_call(['true'], timeout=1e400)",
            "subprocess.check_output(['true'], timeout=1e308 * 10 - 1e308 * 10)",
            "subprocess.run(['true'], timeout=" + "9" * 400 + " / 1)",
            "subprocess.run(['true'], timeout=" + "9" * 400 + ")",
            "subprocess.call(['true'], timeout=1 / (1 / 2 - 0.5))",
            "subprocess.check_call(['true'], timeout=1 / (1 + -1))",
            "subprocess.check_output(['true'], timeout=1 / (1 - +1))",
            "subprocess.run(['true'], timeout=1 / (5 * 0))",
            "subprocess.run(['true'], timeout=60 / 2)",
        ])
        problem = "has a timeout that is not a number written in the call"
        self.assertEqual(([(2, f"subprocess.run {problem}"), (3, f"subprocess.call {problem}"),
                           (4, f"subprocess.check_call {problem}"), (5, f"subprocess.check_output {problem}"),
                           (6, f"subprocess.run {problem}"), (7, f"subprocess.run {problem}"),
                           (8, f"subprocess.call {problem}"), (9, f"subprocess.check_call {problem}"),
                           (10, f"subprocess.check_output {problem}"), (11, f"subprocess.run {problem}")], True),
                         untimed_runs(source))

    def test_each_operator_evaluated_as_another_fails_a_test_of_the_timeout_check(self):
        # A check that evaluated one of the operators above as another, for example * as ** or binary - as %, could
        # accept a timeout that raises when the call runs, or report one that bounds the run, so the two tests of
        # timeouts written as arithmetic must not both pass under any such swap.
        tests = ["test_a_timeout_written_as_arithmetic_on_numbers_is_accepted",
                 "test_a_timeout_written_as_arithmetic_that_is_not_a_finite_number_is_reported"]
        binary = (operator.add, operator.sub, operator.mul, operator.truediv, operator.floordiv, operator.mod,
                  operator.pow)
        swaps = [(BINARY_OPERATORS, op, other) for op in BINARY_OPERATORS for other in binary
                 if other is not BINARY_OPERATORS[op]]
        swaps += [(UNARY_OPERATORS, op, other) for op in UNARY_OPERATORS for other in (operator.pos, operator.neg)
                  if other is not UNARY_OPERATORS[op]]
        # Both tests pass with no swap, so a swap that fails one of them is the swap's doing. Without this check, this
        # test would pass when one of them failed with no swap and under each swap as well.
        failing = []
        for name in tests:
            result = unittest.TestResult()
            ChildRuns(name).run(result)
            if not result.wasSuccessful():
                failing.append(name)
        self.assertEqual([], failing)
        passed = []
        for table, op, other in swaps:
            result = unittest.TestResult()
            with mock.patch.dict(table, {op: other}):
                for name in tests:
                    ChildRuns(name).run(result)
            if result.wasSuccessful():
                passed.append(f"ast.{op.__name__} as operator.{other.__name__}")
        # The swaps are found, so a change to the tables fails instead of passing with no swap checked.
        self.assertEqual(4 * 6 + 2, len(swaps))
        self.assertEqual([], passed)

    def test_the_operator_swap_test_fails_when_a_test_it_runs_fails_with_no_swap(self):
        # An expected list that is wrong with no swap can be wrong under each swap as well, as one that keeps the entry
        # for a run deleted from the source is, so the swap test must fail on it instead of counting each swap as held.
        name = "test_a_timeout_written_as_arithmetic_that_is_not_a_finite_number_is_reported"
        result = unittest.TestResult()
        with mock.patch.object(ChildRuns, name, lambda test: test.fail("wrong with no swap")):
            ChildRuns("test_each_operator_evaluated_as_another_fails_a_test_of_the_timeout_check").run(result)
        self.assertEqual([], result.errors)
        self.assertEqual(1, len(result.failures))
        self.assertIn(repr(name), result.failures[0][1])

    def test_the_comment_on_the_finite_number_cases_names_the_last_run_as_the_accepted_control(self):
        # That test expects its last run, timeout=60 / 2, to be accepted, so its comment says that each run but the
        # last is reported, not that each of them is.
        comment = comment_text(ChildRuns.test_a_timeout_written_as_arithmetic_that_is_not_a_finite_number_is_reported)
        self.assertIn("Each run but the last raises when the call runs", comment)
        self.assertIn("The last, timeout=60 / 2, is the accepted control", comment)
        self.assertNotIn("Each of these", comment)

    def test_written_number_docstring_says_the_number_fits_in_a_float(self):
        # An int too large for a float, such as the 400 nines above, is a finite number that written_number rejects,
        # so its docstring says the number fits in a float. It must equal that sentence, so a docstring that drops
        # the clause fails.
        if written_number.__doc__ is None and sys.flags.optimize >= 2:
            self.skipTest("python3 -OO strips docstrings, so written_number has none to check")
        self.assertEqual("Whether the expression is a number written in the call: an int or float literal, or the "
                         "operators above applied to them, that evaluates to a finite number that fits in a float.",
                         " ".join(written_number.__doc__.split()))

    def test_module_docstring_names_each_docstring_whose_wording_this_file_tests(self):
        # The test above checks the docstring of written_number and this test checks the module docstring, so the
        # module docstring names both among the wording that this file tests.
        if __doc__ is None and sys.flags.optimize >= 2:
            self.skipTest("python3 -OO strips docstrings, so this file has no module docstring to check")
        self.assertIn("for the wording of the CHANGELOG.md entry about the python3 -O runs, of a comment in this file, "
                      "of the docstring of written_number and of this docstring.", " ".join(__doc__.split()))

    def test_a_subprocess_function_reached_without_the_module_name_is_reported(self):
        source = "\n".join([
            "import subprocess as sp",
            "from subprocess import run",
            "import functools",
            "functools.partial(subprocess.call, ['true'])",
        ])
        self.assertEqual(([(1, "imports subprocess as sp"), (2, "imports names from subprocess"),
                           (4, "subprocess.call has no timeout")], True), untimed_runs(source))


class ChangelogEntry(unittest.TestCase):
    def test_changelog_entry_says_the_python3_O_runs_that_this_file_starts_record(self):
        # The -O test records in the python3 -O run of each test file that it starts, so the entry for #93 names the
        # runs this file starts, not the python3 -O runs of this file.
        text = " ".join(CHANGELOG.read_text(encoding="utf-8").split())
        opening = "A `python3 -m unittest discover -s scripts -p 'test_*.py'` run still ran"
        self.assertIn(opening, text, f"CHANGELOG.md has no entry for #93 that opens with: {opening}")
        start = text.index(opening)
        end = text.find("(#93)", start)
        self.assertNotEqual(-1, end, f"the CHANGELOG.md entry for #93 that opens with {opening!r} has no (#93) after it")
        entry = text[start:end]
        self.assertIn("The `python3 -O` runs that `scripts/test_stripped_docstrings.py` starts now record each process "
                      "the test file starts", entry)
        self.assertNotIn("runs of `scripts/test_stripped_docstrings.py`", entry)


if __name__ == "__main__":
    unittest.main()
