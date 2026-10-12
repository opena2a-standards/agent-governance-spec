#!/usr/bin/env python3
"""Tests for the patterns .gitignore holds for credential files, for the run
of this file under python3 -OO, for the wording of the CHANGELOG.md entry
about the test of the class docstring, and for this docstring.

Run from anywhere:  python3 scripts/test_gitignore.py

Standard library only. The tests read the files in the working tree, which
may differ from what is committed. CredentialFiles copies .gitignore into a
new git repository under a temporary directory, with an empty home and no
system configuration, so only the patterns of .gitignore decide what git
ignores, and holds its own class docstring to one sentence.
StrippedDocstrings runs this file in a python3 -OO process and checks that
it passes with the test of the class docstring skipped, and checks that
without -OO a missing class docstring is an error, not a skip.
ChangelogEntry reads CHANGELOG.md and checks the entry for #80, and checks
that a missing entry is a failure that names it, not an error.
ModuleDocstring checks that this docstring names each test class of the
file. No test writes a tracked file.
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
GITIGNORE = ROOT / ".gitignore"
CHANGELOG = ROOT / "CHANGELOG.md"


def ignored(test, paths):
    """The paths of the list that .gitignore makes git ignore."""
    with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as repo:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(HOME=home, XDG_CONFIG_HOME=str(Path(home) / ".config"), GIT_CONFIG_NOSYSTEM="1")
        try:
            subprocess.run(["git", "-C", repo, "init", "-q"], check=True, capture_output=True, env=env)
        except OSError:
            test.skipTest("git is not available")
        except subprocess.CalledProcessError as error:
            test.skipTest("git init -q failed: " + error.stderr.decode("utf-8", "replace").strip())
        (Path(repo) / ".gitignore").write_bytes(GITIGNORE.read_bytes())
        result = subprocess.run(["git", "-C", repo, "check-ignore", *paths], capture_output=True, env=env)
        test.assertIn(result.returncode, (0, 1), result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("utf-8").split()


class CredentialFiles(unittest.TestCase):
    """git ignores secrets.json at the root and in a subdirectory."""

    def test_secrets_json_is_ignored_at_any_depth(self):
        paths = ["secrets.json", "integrations/secrets.json"]
        self.assertEqual(paths, ignored(self, paths))

    def test_the_pattern_matches_only_that_file_name(self):
        # controls.json is the tracked control export; a template such as secrets.json.example would be committed on purpose.
        paths = ["controls.json", "secrets.json.example"]
        self.assertEqual([], ignored(self, paths))

    def test_docstring_claims_only_what_the_tests_check(self):
        # The tests check one file name, and git add -f still adds an ignored file, so the docstring names that
        # file and says git ignores it, not that every secrets file is kept out of a commit. It must equal that
        # sentence, so a clause appended to it, such as "so no secrets file can reach a commit", fails.
        if CredentialFiles.__doc__ is None and sys.flags.optimize >= 2:
            self.skipTest("python3 -OO strips docstrings, so CredentialFiles has none to check")
        doc = " ".join(CredentialFiles.__doc__.split())
        self.assertEqual("git ignores secrets.json at the root and in a subdirectory.", doc)


class StrippedDocstrings(unittest.TestCase):
    def test_docstring_test_skips_with_a_reason_under_python3_OO(self):
        # python3 -OO strips the docstrings of this file, so the test that reads the class docstring skips, and
        # the run passes.
        if sys.flags.optimize >= 2:
            self.skipTest("this is the python3 -OO run that the test starts")
        result = subprocess.run([sys.executable, "-OO", str(Path(__file__).resolve()), "-v"],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("skipped 'python3 -OO strips docstrings, so CredentialFiles has none to check'", result.stderr)

    def test_a_missing_docstring_is_an_error_without_python3_OO(self):
        # A class docstring missing from the source, for example because a statement was placed above it, is None
        # without -OO too, and the test that reads it must then report an error, not a skip.
        if sys.flags.optimize >= 2:
            self.skipTest("under python3 -OO the test that reads the class docstring skips on purpose")
        result = unittest.TestResult()
        with mock.patch.object(CredentialFiles, "__doc__", None):
            CredentialFiles("test_docstring_claims_only_what_the_tests_check").run(result)
        self.assertEqual([], result.skipped)
        self.assertEqual(1, len(result.errors), result.errors)


class ChangelogEntry(unittest.TestCase):
    """The wording of the CHANGELOG.md entry for #80."""

    def test_entry_says_the_earlier_test_checked_the_sentence_and_two_absent_phrases(self):
        # Before #80 the docstring test asserted that the sentence was in the docstring and that "never committed"
        # and "A secrets file" were not, so the entry names both checks and does not say it checked only the first.
        text = " ".join(CHANGELOG.read_text(encoding="utf-8").split())
        opening = "The test that holds the class docstring of the `.gitignore` tests"
        self.assertIn(opening, text, f"CHANGELOG.md has no entry for #80 that opens with: {opening}")
        start = text.index(opening)
        end = text.find("(#80)", start)
        self.assertNotEqual(-1, end, f"the CHANGELOG.md entry for #80 that opens with {opening!r} has no (#80) after it")
        entry = text[start:end]
        self.assertIn(
            "checked that the sentence was present and that two phrases of the docstring that #76 replaced, "
            '"never committed" and "A secrets file", were absent',
            entry,
        )
        self.assertNotIn("checked only", entry)

    def test_a_missing_entry_is_a_failure_that_names_it(self):
        # Without its opening words or its (#80) marker, the entry is reported as a failure that names it, not as
        # the ValueError of str.index.
        text = CHANGELOG.read_text(encoding="utf-8")
        cases = {
            "opening words": (text.replace("The test that holds", "The test that pins"),
                              "CHANGELOG.md has no entry for #80 that opens with"),
            "(#80) marker": (text.replace("(#80)", ""), "has no (#80) after it"),
        }
        for removed, (changed, message) in cases.items():
            with self.subTest(removed=removed):
                self.assertNotEqual(text, changed)
                result = unittest.TestResult()
                changelog = mock.Mock(**{"read_text.return_value": changed})
                with mock.patch.object(sys.modules[__name__], "CHANGELOG", changelog):
                    ChangelogEntry("test_entry_says_the_earlier_test_checked_the_sentence_and_two_absent_phrases").run(result)
                self.assertEqual([], result.errors)
                self.assertEqual(1, len(result.failures), result.failures)
                self.assertIn(message, result.failures[0][1])


class ModuleDocstring(unittest.TestCase):
    """The module docstring names each test class of the file."""

    def test_module_docstring_names_each_test_class(self):
        doc = sys.modules[__name__].__doc__
        if doc is None and sys.flags.optimize >= 2:
            self.skipTest("python3 -OO strips docstrings, so this module has none to check")
        classes = [name for name, value in vars(sys.modules[__name__]).items()
                   if isinstance(value, type) and issubclass(value, unittest.TestCase) and value.__module__ == __name__]
        self.assertIn("ModuleDocstring", classes)
        self.assertEqual([], [name for name in classes if name not in doc.split()])


if __name__ == "__main__":
    unittest.main()
