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
        # controls.json is the tracked control export; a template for a secrets file is committed on purpose.
        paths = ["controls.json", "secrets.json.example"]
        self.assertEqual([], ignored(self, paths))

    def test_docstring_claims_only_what_the_tests_check(self):
        # The tests check one file name, and git add -f still adds an ignored file, so the docstring names that
        # file and says git ignores it, not that every secrets file is kept out of a commit.
        doc = " ".join(CredentialFiles.__doc__.split())
        self.assertIn("git ignores secrets.json at the root and in a subdirectory", doc)
        self.assertNotIn("never committed", doc)
        self.assertNotIn("A secrets file", doc)


if __name__ == "__main__":
    unittest.main()
