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
    """A secrets file is never committed by accident, at the root or in a subdirectory."""

    def test_secrets_json_is_ignored_at_any_depth(self):
        paths = ["secrets.json", "integrations/secrets.json"]
        self.assertEqual(paths, ignored(self, paths))

    def test_the_pattern_matches_only_that_file_name(self):
        # controls.json is the tracked control export; a template for a secrets file is committed on purpose.
        paths = ["controls.json", "secrets.json.example"]
        self.assertEqual([], ignored(self, paths))


if __name__ == "__main__":
    unittest.main()
