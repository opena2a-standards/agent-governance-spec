#!/usr/bin/env python3
"""Tests for the commands .pre-push-review-not-required names as the
repository's checks.

Run from anywhere:  python3 scripts/test_pre_push_note.py

Standard library only. The tests read .pre-push-review-not-required,
CONTRIBUTING.md and the names of the check scripts under scripts/, and write
nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
NOTE = ROOT / ".pre-push-review-not-required"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
TEST_COMMAND = re.compile(r"`(python3 -m unittest discover [^`]+)`")
SCRIPT_COMMAND = re.compile(r"python3 scripts/[A-Za-z0-9_]+\.py")


def test_command():
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
    if test_command() not in note:
        faults.append(f"does not name {test_command()}")
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
        self.assertIn(f"does not name {test_command()}", faults)
        self.assertNotIn("does not name python3 scripts/check_crosswalks.py", faults)

    def test_contributing_names_the_discover_command(self):
        self.assertEqual("python3 -m unittest discover -s scripts -p 'test_*.py'", test_command())


if __name__ == "__main__":
    unittest.main()
