#!/usr/bin/env python3
"""Tests for scripts/check_docs_prose.py: the prose rules, what the checker
skips, which tracked files it covers, the command line, and that the
repository itself passes.

Run from anywhere:  python3 scripts/test_check_docs_prose.py

Standard library only. The tests use Markdown held in this file and read the
committed Markdown files; they write no tracked file. The command-line tests
write small trees under a temporary directory.
"""

import contextlib
import fnmatch
import io
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

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


def lines(*text):
    return "\n".join(text)


class Fences(unittest.TestCase):
    DASH = "spaced double hyphen used as a dash"

    def test_shorter_fence_inside_a_four_backtick_fence_does_not_close_it(self):
        self.assertEqual([], cdp.findings(lines("````md", "```sh", "in code -- x", "```", "````")))

    def test_prose_after_a_four_backtick_fence_is_read(self):
        self.assertEqual([(4, self.DASH)], cdp.findings(lines("````md", "```", "````", "After -- y")))

    def test_longer_run_closes_a_fence(self):
        self.assertEqual([(4, self.DASH)], cdp.findings(lines("```", "code -- a", "`````", "After -- y")))

    def test_tilde_line_does_not_close_a_backtick_fence(self):
        text = lines("```", "code -- a", "~~~", "still code -- b", "```", "After -- y")
        self.assertEqual([(6, self.DASH)], cdp.findings(text))

    def test_backtick_line_does_not_close_a_tilde_fence(self):
        text = lines("~~~", "code -- a", "```", "still code -- b", "~~~", "After -- y")
        self.assertEqual([(6, self.DASH)], cdp.findings(text))

    def test_fence_line_with_text_after_the_run_does_not_close_a_fence(self):
        text = lines("```md", "```sh", "still code -- a", "```", "After -- y")
        self.assertEqual([(5, self.DASH)], cdp.findings(text))


class DashEdges(unittest.TestCase):
    def test_double_hyphen_at_a_line_edge_or_set_off_by_tabs_is_reported(self):
        for text in ("A clause that ends the line --", "-- starts the line", "x\t--\ty", "  --  "):
            with self.subTest(text=text):
                self.assertEqual([(1, "spaced double hyphen used as a dash")], cdp.findings(text))

    def test_en_dash_at_a_line_edge_or_set_off_by_tabs_is_reported(self):
        for text in ("A clause that ends the line –", "– starts the line", "x\t–\ty"):
            with self.subTest(text=text):
                self.assertEqual([(1, "spaced en dash")], cdp.findings(text))

    def test_hyphens_that_are_not_a_dash_are_not_reported(self):
        for text in (
            "--flag starts the line", "ends with a--", "an arrow --> here", "a rule\n\n---\n\nmore",
            "| A | B |\n|--|--|\n| x | -- |", "| A | B\n|--|--\n| x | --",
            "Setext title\n--", "Setext title\n-----",
        ):
            with self.subTest(text=text):
                self.assertEqual([], cdp.findings(text))

    def test_double_hyphen_alone_on_a_line_under_no_text_is_reported(self):
        self.assertEqual([(3, "spaced double hyphen used as a dash")], cdp.findings("Text.\n\n--"))


class WhyHeadings(unittest.TestCase):
    HEADING = 'heading named "Why this exists" or "Why this matters"'
    LABEL = 'bold label named "Why this exists" or "Why this matters"'

    def test_indented_atx_heading_is_reported(self):
        for text in ("  ## Why this exists", "   # Why this matters", "\t### Why This Exists"):
            with self.subTest(text=text):
                self.assertEqual([(1, self.HEADING)], cdp.findings(text))

    def test_setext_heading_is_reported_at_the_line_that_names_it(self):
        for number, text in (
            (1, "Why this exists\n==="), (1, "Why this matters\n---"), (3, "Intro.\n\n  Why This Exists\n  =======\n"),
        ):
            with self.subTest(text=text):
                self.assertEqual([(number, self.HEADING)], cdp.findings(text))

    def test_bold_label_is_reported(self):
        for text in (
            "**Why this matters**", "**Why this exists:**", "__Why this matters__",
            "  **Why this matters:** the sentence goes on.",
        ):
            with self.subTest(text=text):
                self.assertEqual([(1, self.LABEL)], cdp.findings(text))

    def test_other_text_is_not_reported(self):
        for text in (
            "Why this exists is explained below.", "Why this exists\n\n===", "Why this is different\n===",
            "**Why this is different**", "The section on **why this matters** is short.", "*Why this matters*",
        ):
            with self.subTest(text=text):
                self.assertEqual([], cdp.findings(text))


class CodeSpans(unittest.TestCase):
    def test_span_closes_at_the_next_run_of_the_same_length(self):
        self.assertEqual("a" + " " * 11 + "b", cdp.blank_code_spans("a`` x ` y ``b"))
        self.assertEqual(" " * 3 + " and `` open", cdp.blank_code_spans("`a` and `` open"))
        self.assertEqual("no code here", cdp.blank_code_spans("no code here"))

    def test_dash_inside_a_span_that_holds_a_backtick_is_not_reported(self):
        self.assertEqual([], cdp.findings("Run `` git log -- `path` `` first."))
        self.assertEqual([(1, "spaced double hyphen used as a dash")], cdp.findings("`a` -- `b`"))

    def test_long_runs_of_backticks_are_scanned_in_linear_time(self):
        # A scan that retries from every backtick takes more than ten seconds on the first line.
        distinct = " ".join("`" * n for n in range(2, 600))
        for line in ("x" + "`" * 500000, distinct + " `a`" * 50000, "`a` " * 100000):
            start = time.perf_counter()
            cdp.findings(line)
            self.assertLess(time.perf_counter() - start, 2.0)


class Scope(unittest.TestCase):
    def test_excluded_paths(self):
        for rel in (
            "CHANGELOG.md", "changelog.d/123.md", "LICENSE.md", "licenses/LICENSE-MIT.md",
            "node_modules/x/README.md", "vendor/x.md", "dist/x.md", "build/x.md",
            "test/fixtures/a.md", "tests/a.md", "corpus/a.md", "golden/a.md",
            "snapshots/a.md", "examples/chatbot-soul.md", "example/notes.md",
            "tests/examples/README.md", "examples/fixtures/README.md", "corpus/README.md",
            "crosswalks/oasb-2-to-nist-ai-rmf-1.0.md", "crosswalks/oasb-2-to-eu-ai-act-2024-1689.md",
        ):
            self.assertTrue(cdp.excluded(rel), rel)

    def test_included_paths(self):
        for rel in (
            "README.md", "specification.md", "domains/README.md", "templates/basic.md",
            "crosswalks/README.md", "crosswalks/sources.md",
            "examples/README.md", "example/readme.mdx", "integrations/examples/README.md",
        ):
            self.assertFalse(cdp.excluded(rel), rel)

    def test_tracked_set_is_the_committed_markdown_minus_exclusions(self):
        rels = cdp.tracked_markdown(cdp.ROOT)
        self.assertIn("README.md", rels)
        self.assertIn("specification.md", rels)
        self.assertNotIn("CHANGELOG.md", rels)
        self.assertEqual(["examples/README.md"], [r for r in rels if r.startswith("examples/")])

    def test_contributing_names_every_tracked_file_the_check_skips(self):
        text = (cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        bullet, = [line for line in text.split("\n") if line.startswith("- `python3 scripts/check_docs_prose.py`")]
        named = re.findall(r"`([^`]+)`", bullet)
        skipped = [rel for rel in cdp.listed_markdown(cdp.ROOT) if cdp.excluded(rel)]
        self.assertTrue(skipped)
        for rel in skipped:
            covered = [n for n in named if rel == n or fnmatch.fnmatchcase(rel, n) or (n.endswith("/") and rel.startswith(n))]
            self.assertTrue(covered, f"CONTRIBUTING.md does not name {rel} among the files the check skips")


def run_main(*args):
    """(exit code, stdout, stderr) of main() with the arguments after the program name."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cdp.main(["check_docs_prose.py", *args])
    return code, out.getvalue(), err.getvalue()


def write_tree(root, files):
    for rel, text in files.items():
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class CommandLine(unittest.TestCase):
    HINT = "see the rules at the top of scripts/check_docs_prose.py\n"

    def test_findings_are_printed_as_file_line_message_and_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {
                "README.md": "# Title\n\nPlain prose.\nA clause -- joined.\n",
                "docs/guide.mdx": "## Why this exists\n",
                "docs/clean.md": "Nothing to report.\n",
                "examples/sample.md": "Not read -- an example.\n",
                "notes.txt": "Not Markdown -- not read.\n",
            })
            with mock.patch.object(cdp.subprocess, "run", side_effect=OSError("no git")):
                code, out, err = run_main(tmp)
        self.assertEqual(1, code)
        self.assertEqual(
            "README.md:4: spaced double hyphen used as a dash\n"
            'docs/guide.mdx:1: heading named "Why this exists" or "Why this matters"\n',
            out,
        )
        self.assertEqual("2 finding(s); " + self.HINT, err)

    def test_clean_tree_prints_nothing_and_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {"README.md": "# Title\n\nPlain prose.\n"})
            with mock.patch.object(cdp.subprocess, "run", side_effect=OSError("no git")):
                self.assertEqual((0, "", ""), run_main(tmp))

    def test_tracked_md_and_mdx_files_are_read_and_untracked_ones_are_not(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {
                "a.md": "A clause -- joined.\n",
                "b.mdx": "Another clause -- joined.\n",
                "untracked.md": "Not tracked -- not read.\n",
            })
            try:
                for command in (["init", "-q"], ["add", "a.md", "b.mdx"]):
                    subprocess.run(["git", "-C", tmp, *command], check=True, capture_output=True, env=env)
            except (OSError, subprocess.CalledProcessError):
                self.skipTest("git is not available")
            with mock.patch.dict(os.environ, env, clear=True):
                code, out, err = run_main(tmp)
        self.assertEqual(1, code)
        self.assertEqual(
            "a.md:1: spaced double hyphen used as a dash\nb.mdx:1: spaced double hyphen used as a dash\n", out)
        self.assertEqual("2 finding(s); " + self.HINT, err)

    def test_argument_that_is_not_a_directory_prints_usage_and_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {"README.md": "Plain prose.\n"})
            for argument in ("--help", "-h", "", str(Path(tmp) / "README.md"), str(Path(tmp) / "missing")):
                with self.subTest(argument=argument):
                    code, out, err = run_main(argument)
                    self.assertEqual(2, code)
                    self.assertEqual("", out)
                    self.assertEqual(f"scripts/check_docs_prose.py: not a directory: {argument}\n{cdp.USAGE}\n", err)

    def test_more_than_one_argument_prints_usage_and_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = run_main(tmp, tmp)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(f"scripts/check_docs_prose.py: expected at most one argument, got 2\n{cdp.USAGE}\n", err)

    def test_usage_and_docstring_name_the_optional_root_argument(self):
        self.assertTrue(cdp.USAGE.startswith("usage: python3 scripts/check_docs_prose.py [ROOT]\n"))
        self.assertIn("python3 scripts/check_docs_prose.py [ROOT]", cdp.__doc__)
        self.assertIn("exit 2", cdp.__doc__)


def checker_lines(text):
    """The lines of text that name the checker, joined into one."""
    return " ".join(line for line in text.splitlines() if "check_docs_prose.py" in line)


def checked_list(doc):
    """The Checked list of the docstring: the paragraph that names what the checker does not read."""
    return doc.split("Checked:", 1)[-1].split("\n\n", 1)[0]


def unnamed_exclusions(text):
    """The exclusions of the checker that the lines of text naming the checker leave out."""
    described = checker_lines(text)
    wanted = [("LICENSE", "LICENSE")]
    wanted += [(name, "`" + name) for name in cdp.EXCLUDED_FILES + cdp.EXCLUDED_PREFIXES + cdp.RENDERED_PREFIXES]
    wanted += [(name, "`" + name + "`") for name in sorted(cdp.EXCLUDED_DIR_NAMES)]
    return [name for name, form in wanted if form not in described]


README_PATTERN = re.compile(
    r"(?<![\w.-])(?:{})(?!\w)".format("|".join(re.escape(name) for name in sorted(cdp.README_NAMES))), re.IGNORECASE
)
EXAMPLE_DIR_PATTERN = re.compile(
    r"(?<![\w.-])(?:{})(?![\w.-])".format("|".join(re.escape(name) for name in sorted(cdp.EXAMPLE_DIR_NAMES)))
)
READ_VERB = re.compile(r"\b(?:checks|reads|(?:is|are) (?:checked|read))\b")
# A comma, semicolon or colon, or one of these words, starts a new clause.
CLAUSE_BREAK = re.compile(r"\s*[,;:]\s*|\s+(?=\b(?:except|but|since|because|unless|although|though|whereas|while)\b)")


def readme_exception_statements(text):
    """The sentences and parentheticals of text that say the checker reads a README in an examples directory.

    One says so when one of its clauses names a README file and an examples directory and says "checks",
    "reads", "is read", "are read", "is checked" or "are checked". "does not read" and "is not checked" hold
    none of those forms, and a verb in another clause ("is not read, since a tool reads it") or a README
    named after "except" ("checks every file except `examples/README.md`") is a different clause.
    """
    statements = re.split(r"(?<=[.!?])\s+|\s*[()]\s*", " ".join(text.split()))
    return [
        s for s in statements
        if any(all(p.search(c) for p in (README_PATTERN, EXAMPLE_DIR_PATTERN, READ_VERB)) for c in CLAUSE_BREAK.split(s))
    ]


def unreasoned_exclusions(doc):
    """The exclusions of the checker that no "subject: reason" item of the docstring's Checked list gives a reason for."""
    checked = checked_list(doc)
    items = [" ".join(item.split()) for item in checked.split("\n  * ")[1:]]
    reasoned = [item.split(": ", 1)[0] for item in items if ": " in item and item.split(": ", 1)[1].strip(" .")]
    names = ["LICENSE"] + list(cdp.EXCLUDED_FILES + cdp.EXCLUDED_PREFIXES + cdp.RENDERED_PREFIXES)
    names += sorted(cdp.EXCLUDED_DIR_NAMES)
    pattern = r"(?<![\w./-]){}(?![\w])"
    return [n for n in names if not any(re.search(pattern.format(re.escape(n)), s) for s in reasoned)]


def readme_exception_gaps(text):
    """The parts of the README exception that the sentence naming the excluded directories leaves out.

    The checker reads a README in an example or examples directory, so the sentence of the lines of text
    naming the checker that says nothing "in a directory named" one of the excluded names is read has to
    state the exception itself: the README names, and after them the directory names it applies to.
    """
    described = checker_lines(text)
    sentence = re.split(r"\.(?:\s|$)", described.partition("in a directory named")[2], maxsplit=1)[0].lower()
    start = sentence.find("`readme")
    exception = sentence[start:] if start >= 0 else ""
    wanted = sorted(cdp.README_NAMES) + sorted(cdp.EXAMPLE_DIR_NAMES)
    return [name for name in wanted if "`" + name + "`" not in exception]


class Contributing(unittest.TestCase):
    """CONTRIBUTING.md names every path the checker does not read, and the README it reads among them."""

    def test_contributing_names_every_exclusion(self):
        text = (cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertEqual([], unnamed_exclusions(text))

    def test_docstring_gives_the_reason_for_each_exclusion(self):
        # CONTRIBUTING.md tells the reader the docstring gives the reason for each exclusion.
        self.assertIn("docstring gives the reason for each exclusion",
                      (cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"))
        self.assertEqual([], unreasoned_exclusions(cdp.__doc__))

    def test_exclusion_without_a_reason_is_reported(self):
        doc = (
            "Checked: every tracked .md file, except:\n"
            "  * CHANGELOG.md and changelog.d/: history is not rewritten.\n"
            "  * LICENSE files\n"
            "  * anything under node_modules/, vendor/, dist/ or\n"
            "    build/: not written here.\n"
        )
        missing = unreasoned_exclusions(doc)
        self.assertIn("LICENSE", missing)
        self.assertIn("examples", missing)
        self.assertIn("crosswalks/oasb-2-to-", missing)
        self.assertNotIn("CHANGELOG.md", missing)
        self.assertNotIn("build/", missing)

    def test_partial_list_is_reported(self):
        text = "- `python3 scripts/check_docs_prose.py` skips `CHANGELOG.md` and the files under `examples/`.\n"
        missing = unnamed_exclusions(text)
        self.assertIn("changelog.d/", missing)
        self.assertIn("LICENSE", missing)
        self.assertIn("crosswalks/oasb-2-to-", missing)
        self.assertIn("fixtures", missing)
        self.assertNotIn("CHANGELOG.md", missing)

    def test_contributing_states_the_readme_exception_where_it_names_the_directories(self):
        # A README is read in an example or examples directory at any depth, unless an excluded prefix holds it.
        self.assertFalse(cdp.excluded("docs/examples/README.md"))
        for prefix in cdp.EXCLUDED_PREFIXES + cdp.RENDERED_PREFIXES:
            with self.subTest(prefix=prefix):
                self.assertTrue(cdp.excluded(prefix + "x/examples/README.md"))
        text = (cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertEqual([], readme_exception_gaps(text))

    def test_readme_exception_stated_apart_from_the_directory_names_is_reported(self):
        # The sentence says a file is checked and, where it names the directories, that the same file is not read.
        apart = (
            "- `python3 scripts/check_docs_prose.py` does not read the example governance files under"
            " `examples/` (it checks `examples/README.md`), or anything in a directory named `test`,"
            " `example` or `examples`. The script's docstring gives the reason for each exclusion.\n"
        )
        self.assertEqual(["readme.md", "readme.mdx", "example", "examples"], readme_exception_gaps(apart))
        partial = (
            "- `python3 scripts/check_docs_prose.py` does not read anything in a directory named `test`,"
            " `example` or `examples`, except a `README.md`. It checks `examples/README.md`.\n"
        )
        self.assertEqual(["readme.mdx", "example", "examples"], readme_exception_gaps(partial))

    def test_contributing_states_the_readme_exception(self):
        # The lines that list `examples` among the skipped directories say that the README there is checked.
        text = (cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertTrue(
            readme_exception_statements(checker_lines(text)),
            "CONTRIBUTING.md does not say that the check reads a README.md in an examples directory",
        )

    def test_docstring_states_the_readme_exception(self):
        self.assertTrue(
            readme_exception_statements(checked_list(cdp.__doc__)),
            "the docstring's Checked list does not say that a README.md in an examples directory is read",
        )

    def test_docstring_names_every_readme_and_directory_the_exception_covers(self):
        # The checker reads README.md and README.mdx, in a directory named example or examples.
        self.assertFalse(cdp.excluded("example/README.mdx"))
        stated = " ".join(readme_exception_statements(checked_list(cdp.__doc__)))
        for name in sorted(cdp.README_NAMES):
            with self.subTest(name=name):
                self.assertRegex(stated, re.compile(rf"(?<![\w.-]){re.escape(name)}(?!\w)", re.IGNORECASE))
        for name in sorted(cdp.EXAMPLE_DIR_NAMES):
            with self.subTest(name=name):
                self.assertRegex(stated, rf"(?<![\w.-]){re.escape(name)}(?![\w.-])")

    def test_text_without_the_readme_exception_is_reported(self):
        for text in (
            "It does not read `CHANGELOG.md` or the example governance files under `examples/`.",
            "It does not read the files under `examples/`, `examples/README.md` among them.",
            "Anything in an examples directory is data a tool reads. A README.md describes a directory to a person.",
            "A README.md in an examples directory is not read.",
            "A README.md in an examples directory is not read, since only a tool reads it.",
            "A README.md in an examples directory is not read since only a tool reads it.",
            "It checks every Markdown file except `examples/README.md`.",
        ):
            self.assertEqual([], readme_exception_statements(text), text)
        for text in (
            "It does not read the files under `examples/` (it checks `examples/README.md`).",
            "A README.md in an examples directory\n    is read, since it describes the examples to a person.",
            "A readme.mdx in an example directory is checked.",
            "README.md files in examples directories are read.",
            "README.mdx files in example directories are checked.",
        ):
            self.assertEqual(1, len(readme_exception_statements(text)), text)


class Repository(unittest.TestCase):
    def test_committed_prose_passes(self):
        code, out, err = run_main()
        self.assertEqual(0, code, out + err)
        self.assertEqual("", out)


if __name__ == "__main__":
    unittest.main()
