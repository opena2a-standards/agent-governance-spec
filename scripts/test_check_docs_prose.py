#!/usr/bin/env python3
"""Tests for scripts/check_docs_prose.py: the prose rules, what the checker
skips, which tracked files it covers, and that the repository itself passes.

Run from anywhere:  python3 scripts/test_check_docs_prose.py

Standard library only. The tests use Markdown held in this file and read the
committed Markdown files; they write no tracked file.
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_docs_prose as cdp  # noqa: E402

SAMPLE = "\n".join([
    "---",
    "title: front matter -- not prose",
    "---",
    "# Title",
    "",
    "A clause -- joined with a double hyphen.",
    "An em dash—inside a sentence.",
    "A spaced en dash – inside a sentence.",
    "An unspaced en dash 2024–2025 is a range and stays.",
    "A command `git log -- path` keeps its separator.",
    "Two spans `a -- b` and `c -- d` on one line.",
    "```sh",
    "cmd -- arg # a fence -- is code",
    "```",
    "~~~",
    "tilde fence -- also code",
    "~~~",
    "<!-- a comment -- is not prose -->",
    "<!-- a comment that spans",
    "several -- lines -->",
    "[![Badge](https://img.example/badge.svg)](https://example.com) -- badge line",
    "| ID | A | B |",
    "|----|---|---|",
    "| X-1 | -- | Yes |",
    "| X-2 | -- | a -- b |",
    "## Why this exists",
    "### Why This Matters",
    "## Why this is different",
    "end-to-end and a single - hyphen are fine.",
])


class Findings(unittest.TestCase):
    def setUp(self):
        self.found = cdp.findings(SAMPLE)
        self.lines = sorted(number for number, _ in self.found)

    def test_each_dash_form_is_reported_once_at_its_line(self):
        self.assertEqual(
            [(6, "spaced double hyphen used as a dash"), (7, "em dash"), (8, "spaced en dash")],
            [f for f in self.found if f[0] in (6, 7, 8)],
        )

    def test_why_headings_are_reported_case_insensitively(self):
        self.assertIn((26, 'heading named "Why this exists" or "Why this matters"'), self.found)
        self.assertIn((27, 'heading named "Why this exists" or "Why this matters"'), self.found)
        self.assertNotIn(28, self.lines)

    def test_table_cell_dash_in_text_is_reported_but_empty_cell_is_not(self):
        self.assertNotIn(24, self.lines)
        self.assertIn(25, self.lines)

    def test_skipped_regions_report_nothing(self):
        for line in (2, 9, 10, 11, 13, 16, 18, 20, 21, 29):
            self.assertNotIn(line, self.lines, f"line {line} should be skipped")

    def test_clean_text_has_no_findings(self):
        self.assertEqual([], cdp.findings("# Title\n\nPlain prose, with a colon: and a comma.\n"))


class Scope(unittest.TestCase):
    def test_excluded_paths(self):
        for rel in (
            "CHANGELOG.md", "changelog.d/123.md", "LICENSE.md", "licenses/LICENSE-MIT.md",
            "node_modules/x/README.md", "vendor/x.md", "dist/x.md", "build/x.md",
            "test/fixtures/a.md", "tests/a.md", "corpus/a.md", "golden/a.md",
            "snapshots/a.md", "examples/chatbot-soul.md",
            "crosswalks/oasb-2-to-nist-ai-rmf-1.0.md", "crosswalks/oasb-2-to-eu-ai-act-2024-1689.md",
        ):
            self.assertTrue(cdp.excluded(rel), rel)

    def test_included_paths(self):
        for rel in (
            "README.md", "specification.md", "domains/README.md", "templates/basic.md",
            "crosswalks/README.md", "crosswalks/sources.md",
        ):
            self.assertFalse(cdp.excluded(rel), rel)

    def test_tracked_set_is_the_committed_markdown_minus_exclusions(self):
        rels = cdp.tracked_markdown(cdp.ROOT)
        self.assertIn("README.md", rels)
        self.assertIn("specification.md", rels)
        self.assertNotIn("CHANGELOG.md", rels)
        self.assertFalse([r for r in rels if r.startswith("examples/")])


class Repository(unittest.TestCase):
    def test_committed_prose_passes(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cdp.main(["check_docs_prose.py"])
        self.assertEqual(0, code, out.getvalue() + err.getvalue())
        self.assertEqual("", out.getvalue())


if __name__ == "__main__":
    unittest.main()
