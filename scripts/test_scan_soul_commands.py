#!/usr/bin/env python3
"""Tests for the scan-soul commands in the documentation and CI examples.

Run from anywhere:  python3 scripts/test_scan_soul_commands.py

Standard library only. The tests read the Markdown and YAML files of the
repository and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SUFFIXES = {".md", ".yml", ".yaml"}
# The changelog names options that were wrong, so it is not read.
SKIPPED = {"CHANGELOG.md"}
# The options that `hackmyagent scan-soul --help` lists in hackmyagent 0.33.2.
SCANNER_OPTIONS = {
    "--json", "-v", "--verbose", "--tier", "--profile", "--fail-below",
    "--deep", "--static-only", "--publish", "--registry-url", "--contribute",
    "--no-contribute", "--ci", "--explain", "-h", "--help",
}
COMMAND = re.compile(r"\bhackmyagent(?:@\S+)? scan-soul\b(.*)$")
# The CI examples, which run the scanner on every pull request.
CI_EXAMPLES = ("integrations/github-action.yml", "integrations/gitlab-ci.yml")
SCANNER_SPEC = re.compile(r"\bnpx hackmyagent(?:@(\S+))? scan-soul\b")
EXACT_VERSION = re.compile(r"\d+\.\d+\.\d+")
# The arguments end at a closing quote or backtick, or at a shell operator.
ARGS_END = re.compile(r"[`\"'>|&;]")
STDERR_INTO_OUTPUT = re.compile(r"2>&1|&>")


def files():
    """Each (relative path, text) of the Markdown and YAML files outside hidden directories."""
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if path.suffix in SUFFIXES and path.name not in SKIPPED and not any(p.startswith(".") for p in rel.parts):
            yield rel.as_posix(), path.read_text(encoding="utf-8")


def scan_commands(text):
    """Each (line number, text after `scan-soul`) of a scan-soul command in text."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = COMMAND.search(line)
        if match:
            found.append((number, match.group(1)))
    return found


def options(rest):
    """The options given to scan-soul in the text that follows it."""
    args = ARGS_END.split(rest, 1)[0]
    return [token.split("=", 1)[0] for token in args.split() if token.startswith("-")]


def json_mixed_with_stderr(rest):
    """True when a --json command sends stderr where its JSON goes."""
    return "--json" in options(rest) and STDERR_INTO_OUTPUT.search(rest) is not None


class ScanSoulCommands(unittest.TestCase):
    def setUp(self):
        self.commands = [(path, number, rest) for path, text in files() for number, rest in scan_commands(text)]

    def test_commands_are_read_from_the_readme_and_the_ci_examples(self):
        paths = {path for path, _, _ in self.commands}
        for path in ("README.md", "integrations/README.md", "integrations/github-action.yml", "integrations/gitlab-ci.yml"):
            self.assertIn(path, paths)

    def test_every_option_is_one_the_scanner_lists(self):
        for path, number, rest in self.commands:
            with self.subTest(at=f"{path}:{number}"):
                self.assertLessEqual(set(options(rest)), SCANNER_OPTIONS)

    def test_json_output_is_not_mixed_with_stderr(self):
        for path, number, rest in self.commands:
            with self.subTest(at=f"{path}:{number}"):
                self.assertFalse(json_mixed_with_stderr(rest))

    def test_ci_examples_pin_one_scanner_release_that_the_guide_names(self):
        # An unpinned npx install takes whatever release is current on each run.
        guide = (ROOT / "integrations" / "README.md").read_text(encoding="utf-8")
        versions = set()
        for path in CI_EXAMPLES:
            specs = SCANNER_SPEC.findall((ROOT / path).read_text(encoding="utf-8"))
            with self.subTest(path=path):
                self.assertEqual(len(specs), 1)
                self.assertRegex(specs[0], f"^{EXACT_VERSION.pattern}$")
            versions.update(specs)
        self.assertEqual(len(versions), 1)
        (version,) = versions
        self.assertIn(f"pin hackmyagent {version}", guide)

    def test_unknown_option_is_reported(self):
        (_, rest), = scan_commands("npx hackmyagent@latest scan-soul --format json > scan-result.json || true\n")
        self.assertEqual(options(rest), ["--format"])
        self.assertNotIn("--format", SCANNER_OPTIONS)

    def test_stderr_in_the_json_file_is_reported(self):
        (_, rest), = scan_commands("npx hackmyagent@latest scan-soul --json > scan-result.json 2>&1 || true\n")
        self.assertTrue(json_mixed_with_stderr(rest))

    def test_text_after_the_command_is_not_read_as_options(self):
        (_, prose), = scan_commands("3. `npx hackmyagent scan-soul` verifies coverage -- see below\n")
        self.assertEqual(options(prose), [])
        (_, script), = scan_commands('"pretest": "hackmyagent scan-soul --fail-below 40"\n')
        self.assertEqual(options(script), ["--fail-below"])


if __name__ == "__main__":
    unittest.main()
