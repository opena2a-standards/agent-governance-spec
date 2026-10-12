#!/usr/bin/env python3
"""Tests for the commands .pre-push-review-not-required names as the
repository's checks, for the names of the helpers of this file, and for the
wording of the CHANGELOG.md entry about the test of those names.

Run from anywhere:  python3 scripts/test_pre_push_note.py

Standard library only. The tests read .pre-push-review-not-required,
CONTRIBUTING.md, CHANGELOG.md, the names of the check scripts under scripts/
and the names of the functions of this file, and write nothing.
"""

import inspect
import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / ".pre-push-review-not-required"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
CHANGELOG = ROOT / "CHANGELOG.md"
TEST_COMMAND = re.compile(r"`(python3 -m unittest discover [^`]+)`")
SCRIPT_COMMAND = re.compile(r"python3 scripts/[A-Za-z0-9_]+\.py")
# The note ends each command it names with ";", so a unittest command runs up to the next ";" or the end of the note.
NOTE_TEST_COMMAND = re.compile(r"python3 -m unittest[^;]*")


def discover_command():
    """The command CONTRIBUTING.md gives for running the tests of the scripts."""
    commands = TEST_COMMAND.findall(CONTRIBUTING.read_text(encoding="utf-8"))
    if len(commands) != 1:
        raise AssertionError(f"CONTRIBUTING.md names {len(commands)} unittest discover commands, expected 1: {commands}")
    return commands[0]


def missing(note):
    """What the note fails to name or names wrongly, one message per fault; empty when it is right."""
    checks = {f"python3 scripts/{path.name}" for path in sorted((ROOT / "scripts").glob("check_*.py"))}
    named = set(SCRIPT_COMMAND.findall(note))
    faults = [f"does not name {command}" for command in sorted(checks - named)]
    # The discover command runs every scripts/test_*.py file, so a single test file named as a check is stale.
    faults += [f"names {command}, which is not a check script" for command in sorted(named - checks)]
    # Each unittest command of the note must equal the command, so one narrowed with an option such as -k is reported.
    command = discover_command()
    test_commands = [found.strip() for found in NOTE_TEST_COMMAND.findall(note)]
    faults += [f"names {found}, which is not the test command of CONTRIBUTING.md"
               for found in test_commands if found != command]
    if command not in test_commands:
        faults.append(f"does not name {command}")
    return faults


class PrePushNote(unittest.TestCase):
    """The note names each check script and the test command of CONTRIBUTING.md, and no other script."""

    def test_note_names_the_checks_and_the_test_command(self):
        self.assertEqual([], missing(NOTE.read_text(encoding="utf-8")))

    def test_note_that_names_one_test_file_is_reported(self):
        note = "Its checks are python3 scripts/check_crosswalks.py and python3 scripts/test_check_crosswalks.py."
        faults = missing(note)
        self.assertIn("does not name python3 scripts/check_docs_prose.py", faults)
        self.assertIn("names python3 scripts/test_check_crosswalks.py, which is not a check script", faults)
        self.assertIn(f"does not name {discover_command()}", faults)
        self.assertNotIn("does not name python3 scripts/check_crosswalks.py", faults)

    def test_note_that_narrows_the_test_command_is_reported(self):
        # The narrowed command holds the command of CONTRIBUTING.md as a prefix, but runs only the tests -k selects.
        command = discover_command()
        note = NOTE.read_text(encoding="utf-8")
        self.assertIn(command + ";", note)
        faults = missing(note.replace(command + ";", command + " -k crosswalks;"))
        self.assertIn(f"names {command} -k crosswalks, which is not the test command of CONTRIBUTING.md", faults)
        self.assertIn(f"does not name {command}", faults)

    def test_contributing_names_the_discover_command(self):
        self.assertEqual("python3 -m unittest discover -s scripts -p 'test_*.py'", discover_command())


class Helpers(unittest.TestCase):
    def test_no_helper_has_a_name_pytest_collects_as_a_test(self):
        # pytest runs a module-level function whose name starts with "test" as a test, while unittest does not, so
        # such a helper makes the two runners count different tests.
        module = sys.modules[__name__]
        functions = [name for name, value in vars(module).items()
                     if inspect.isfunction(value) and value.__module__ == __name__ and name.startswith("test")]
        self.assertEqual([], functions)

    def test_changelog_entry_says_the_test_checks_module_level_functions(self):
        # The test above reads only the functions of the module namespace, and the test methods of this file start
        # with "test", so the entry for #89 says "no module-level function", not "no function".
        text = " ".join(CHANGELOG.read_text(encoding="utf-8").split())
        opening = "The helper of `scripts/test_pre_push_note.py` that reads the test command"
        self.assertIn(opening, text, f"CHANGELOG.md has no entry for #89 that opens with: {opening}")
        start = text.index(opening)
        end = text.find("(#89)", start)
        self.assertNotEqual(-1, end, f"the CHANGELOG.md entry for #89 that opens with {opening!r} has no (#89) after it")
        entry = text[start:end]
        self.assertIn("a test checks that no module-level function of the file has a name that starts with `test`",
                      entry)
        self.assertNotIn("no function of the file", entry)


if __name__ == "__main__":
    unittest.main()
