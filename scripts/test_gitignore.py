#!/usr/bin/env python3
"""Tests for the patterns .gitignore holds for credential files.

Run from anywhere:  python3 scripts/test_gitignore.py

Standard library only. The tests copy .gitignore into a new git repository
under a temporary directory, with an empty home and no system configuration,
so only the committed patterns decide what git ignores. They write no tracked
file.
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


def ignored(test, paths):
    """The paths of the list that the committed .gitignore makes git ignore."""
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
                                capture_output=True, text=True)
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


if __name__ == "__main__":
    unittest.main()
