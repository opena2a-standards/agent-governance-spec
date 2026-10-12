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


TIME_BOUND_SKIP = "the run without -O checks the time bound"


def skip_the_time_bound_when_optimized(test):
    # Tests run this file again under python3 -O and -OO, where a time bound missed on a loaded machine would fail
    # that run and print its whole output, so only the run without -O checks the bound.
    if sys.flags.optimize >= 1:
        test.skipTest(TIME_BOUND_SKIP)


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
        skip_the_time_bound_when_optimized(self)
        distinct = " ".join("`" * n for n in range(2, 600))
        for line in ("x" + "`" * 500000, distinct + " `a`" * 50000, "`a` " * 100000):
            start = time.perf_counter()
            cdp.findings(line)
            self.assertLess(time.perf_counter() - start, 2.0)


def docstring(test, obj):
    """The docstring of obj, or a skip of the test when python3 -OO has stripped it."""
    if obj.__doc__ is None and sys.flags.optimize >= 2:
        test.skipTest("python3 -OO strips docstrings, so {} has none to check".format(obj.__name__))
    return obj.__doc__


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

    def test_paths_are_relative_to_the_checked_directory(self):
        # A run with the ROOT argument sub names sub/b.md as b.md, so the docstrings say root-relative.
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {"sub/b.md": "A clause -- joined.\n"})
            with mock.patch.object(cdp.subprocess, "run", side_effect=OSError("no git")):
                self.assertEqual(["b.md"], cdp.tracked_markdown(Path(tmp) / "sub"))
        for function in (cdp.excluded, cdp.listed_markdown, cdp.tracked_markdown):
            with self.subTest(function=function.__name__):
                self.assertIn("root-relative", docstring(self, function).lower())
                self.assertNotIn("repository-relative", docstring(self, function).lower())

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


def run_git(test, root, command, env):
    """Run the git command in root, and skip the test when git is not installed, or with the command and its error
    when the command fails."""
    try:
        subprocess.run(["git", "-C", str(root), *command], check=True, capture_output=True, env=env, timeout=60)
    except OSError:
        test.skipTest("git is not available")
    except subprocess.CalledProcessError as error:
        reason = error.stderr.decode("utf-8", "replace").strip()
        test.skipTest("git {} failed: {}".format(" ".join(command), reason))


def git_repository(test, root, paths):
    """Make root a git repository that tracks paths, and return the environment its git commands ran in.

    `git add -f` adds a path that an ignore file matches, such as a global gitignore that lists vendor/, which
    `git add` refuses with exit 1. The test is skipped as run_git() skips it.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    for command in (["init", "-q"], ["add", "-f", "--", *paths]):
        run_git(test, root, command, env)
    return env


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
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {
                "a.md": "A clause -- joined.\n",
                "b.mdx": "Another clause -- joined.\n",
                "untracked.md": "Not tracked -- not read.\n",
            })
            env = git_repository(self, tmp, ["a.md", "b.mdx"])
            with mock.patch.dict(os.environ, env, clear=True):
                code, out, err = run_main(tmp)
        self.assertEqual(1, code)
        self.assertEqual(
            "a.md:1: spaced double hyphen used as a dash\nb.mdx:1: spaced double hyphen used as a dash\n", out)
        self.assertEqual("2 finding(s); " + self.HINT, err)

    def test_argument_that_is_not_a_directory_prints_usage_and_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {"README.md": "Plain prose.\n"})
            for argument in ("--version", "-x", "", str(Path(tmp) / "README.md"), str(Path(tmp) / "missing")):
                with self.subTest(argument=argument):
                    code, out, err = run_main(argument)
                    self.assertEqual(2, code)
                    self.assertEqual("", out)
                    self.assertEqual(f"scripts/check_docs_prose.py: not a directory: {argument}\n{cdp.USAGE}\n", err)

    def test_help_flag_prints_usage_and_exits_0(self):
        for flag in ("--help", "-h"):
            with self.subTest(flag=flag):
                self.assertEqual((0, f"{cdp.USAGE}\n", ""), run_main(flag))

    def test_more_than_one_argument_prints_usage_and_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = run_main(tmp, tmp)
        self.assertEqual(2, code)
        self.assertEqual("", out)
        self.assertEqual(f"scripts/check_docs_prose.py: expected at most one argument, got 2\n{cdp.USAGE}\n", err)

    def test_usage_and_docstring_name_the_optional_root_argument(self):
        self.assertTrue(cdp.USAGE.startswith("usage: python3 scripts/check_docs_prose.py [ROOT]\n"))
        self.assertIn("python3 scripts/check_docs_prose.py [ROOT]", docstring(self, cdp))
        self.assertIn("exit 2", docstring(self, cdp))


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
NEGATION = re.compile(r"\b(?:not|no|never)\b", re.IGNORECASE)
# A comma, semicolon or colon, or one of these words, starts a new clause. One whitespace character before a
# word, not a run of them, keeps the split linear in the length of the text; each clause is stripped after it.
CLAUSE_WORDS = ("except", "but", "since", "because", "unless", "although", "though", "whereas", "while",
                "other than", "apart from")
CLAUSE_BREAK = re.compile(r"[,;:]|\s(?=(?:{})\b)".format("|".join(CLAUSE_WORDS)))


def readme_exception_clauses(text):
    """The clauses of text that say the checker reads a README in an examples directory, one per statement.

    A clause runs between two clause breaks: the edges of a sentence or parenthetical, a comma, a semicolon,
    a colon, or one of the words of CLAUSE_WORDS. It says so when it names a README file and an examples
    directory, says "checks", "reads", "is read", "are read", "is checked" or "are checked", and holds none
    of "not", "no" and "never". So the README, the directory and the verb have to sit between the same two
    breaks: "is not read, since a tool reads it", "checks every file except `examples/README.md`" and "in an
    examples directory, a README.md is read" each put them in different clauses and are not counted.
    """
    statements = re.split(r"(?<=[.!?])\s+|\s*[()]\s*", " ".join(text.split()))
    found = []
    for statement in statements:
        clauses = [c.strip() for c in CLAUSE_BREAK.split(statement)]
        found += [
            (statement, c) for c in clauses
            if all(p.search(c) for p in (README_PATTERN, EXAMPLE_DIR_PATTERN, READ_VERB)) and not NEGATION.search(c)
        ][:1]
    return found


def readme_exception_statements(text):
    """The sentences and parentheticals of text that say the checker reads a README in an examples directory."""
    return [statement for statement, _ in readme_exception_clauses(text)]


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
        self.assertEqual([], unreasoned_exclusions(docstring(self, cdp)))

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
            readme_exception_statements(checked_list(docstring(self, cdp))),
            "the docstring's Checked list does not say that a README.md in an examples directory is read",
        )

    def test_docstring_names_every_readme_and_directory_the_exception_covers(self):
        # The checker reads README.md and README.mdx, in a directory named example or examples. The names are
        # looked for in the clause that says so, since the rest of its sentence can name "the examples".
        self.assertFalse(cdp.excluded("example/README.mdx"))
        stated = " ".join(clause for _, clause in readme_exception_clauses(checked_list(docstring(self, cdp))))
        for name in sorted(cdp.README_NAMES):
            with self.subTest(name=name):
                self.assertRegex(stated, re.compile(rf"(?<![\w.-]){re.escape(name)}(?!\w)", re.IGNORECASE))
        for name in sorted(cdp.EXAMPLE_DIR_NAMES):
            with self.subTest(name=name):
                self.assertRegex(stated, rf"(?<![\w.-]){re.escape(name)}(?![\w.-])")

    def test_docstring_states_the_limits_of_the_readme_exception(self):
        # A README in an examples directory is not read under another excluded directory or an excluded prefix.
        # An example or examples directory nested in another one does not take the README out.
        self.assertTrue(cdp.excluded("tests/examples/README.md"))
        self.assertTrue(cdp.excluded("vendor/examples/README.md"))
        self.assertFalse(cdp.excluded("examples/pkg/examples/README.md"))
        self.assertFalse(cdp.excluded("examples/example/README.md"))
        stated = " ".join(readme_exception_statements(checked_list(docstring(self, cdp))))
        self.assertRegex(stated, r"\bunless a directory of this item other than example or examples holds it\b")
        self.assertRegex(stated, r"\bunless\b.* another item of this list excludes its path\b")

    def test_changelog_joins_the_limits_of_the_readme_exception_with_or(self):
        # Either limit alone keeps the README from being read, so the entry for #72 joins them as the docstring does.
        self.assertTrue(cdp.excluded("tests/examples/README.md"))
        self.assertTrue(cdp.excluded("vendor/examples/README.md"))
        text = " ".join((cdp.ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split())
        start = text.index("The entry for #70 should have said that a README")
        entry = text[start:text.index("(#72)", start)]
        self.assertIn("holds it or another item of the list excludes its path", entry)
        self.assertNotIn("no other item", entry)

    def test_contributing_states_that_the_readme_exception_yields_to_the_other_exclusions(self):
        described = checker_lines((cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"))
        match = re.search(r"exception does not override the other exclusions, so it does not read `([^`]+)`", described)
        self.assertIsNotNone(match, "CONTRIBUTING.md does not say that the README exception yields to the other exclusions")
        self.assertTrue(cdp.excluded(match.group(1)))
        self.assertFalse(cdp.excluded(match.group(1).split("/", 1)[1]))

    def test_prefix_exclusions_are_stated_at_the_root_of_the_checked_directory(self):
        # The prefixes match only at the start of the path, so a node_modules directory deeper in the tree is read.
        # The path is relative to ROOT, so the docstring names the checked directory. CONTRIBUTING.md gives the
        # command without ROOT, which checks the repository.
        self.assertTrue(cdp.excluded("node_modules/notes.md"))
        self.assertFalse(cdp.excluded("packages/a/node_modules/notes.md"))
        self.assertFalse(cdp.excluded("x/vendor/notes.md"))
        item = next(i for i in checked_list(docstring(self, cdp)).split("\n  * ") if "node_modules/" in i)
        self.assertIn("at the root of the checked directory", " ".join(item.split()))
        self.assertNotIn("repository root", " ".join(item.split()))
        described = checker_lines((cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"))
        self.assertIn("`python3 scripts/check_docs_prose.py` checks", described)
        self.assertIn("`node_modules/`, `vendor/`, `dist/` or `build/` at the repository root", described)

    def test_contributing_states_that_the_changelog_is_skipped_at_the_repository_root(self):
        # A run on the whole repository reads sub/CHANGELOG.md and sub/changelog.d/1.md.
        self.assertTrue(cdp.excluded("CHANGELOG.md") and cdp.excluded("changelog.d/1.md"))
        self.assertFalse(cdp.excluded("sub/CHANGELOG.md") or cdp.excluded("sub/changelog.d/1.md"))
        described = checker_lines((cdp.ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"))
        self.assertIn("`CHANGELOG.md` and `changelog.d/` at the repository root", described)

    def test_each_exclusion_matched_at_the_start_of_the_path_is_stated_at_the_root(self):
        # CHANGELOG.md, the prefixes and the rendered crosswalk prefix match only at the start of the path, so a run on
        # the whole repository reads sub/CHANGELOG.md, sub/changelog.d/1.md and sub/crosswalks/oasb-2-to-a.md. The
        # item of the docstring that names each says so.
        items = [" ".join(i.split()) for i in checked_list(docstring(self, cdp)).split("\n  * ")[1:]]
        for name in cdp.EXCLUDED_FILES + cdp.EXCLUDED_PREFIXES + cdp.RENDERED_PREFIXES:
            with self.subTest(name=name):
                rel = name if name in cdp.EXCLUDED_FILES else name + "a.md"
                self.assertTrue(cdp.excluded(rel))
                self.assertFalse(cdp.excluded("sub/" + rel))
                item, = [i for i in items if re.search(r"(?<![\w./-]){}(?!\w)".format(re.escape(name)), i)]
                self.assertIn("at the root of the checked directory", item)

    def test_prefix_exclusions_apply_at_the_root_given_as_the_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(tmp, {"sub/vendor/a.md": "A clause -- joined.\n", "sub/b.md": "Another clause -- joined.\n"})
            env = git_repository(self, tmp, ["sub/vendor/a.md", "sub/b.md"])
            with mock.patch.dict(os.environ, env, clear=True):
                at_repository = run_main(tmp)
                at_subdirectory = run_main(str(Path(tmp) / "sub"))
        message = ": spaced double hyphen used as a dash\n"
        self.assertEqual((1, f"sub/b.md:1{message}sub/vendor/a.md:1{message}"), at_repository[:2])
        self.assertEqual((1, f"b.md:1{message}"), at_subdirectory[:2])

    def test_each_clause_break_separates_the_verb_from_the_readme(self):
        # One sentence per break, each holding no negation, so it would be counted if its break did not start a clause.
        for text in (
            "A README.md in an examples directory is skipped, and a tool reads it.",
            "A README.md in an examples directory is skipped; a tool reads it.",
            "A README.md in an examples directory is skipped: a tool reads it.",
            "It checks every Markdown file except `examples/README.md`.",
            "A README.md in an examples directory is skipped but a tool reads it.",
            "A README.md in an examples directory is skipped since a tool reads it.",
            "A README.md in an examples directory is skipped because a tool reads it.",
            "A README.md in an examples directory is skipped unless a tool reads it.",
            "A README.md in an examples directory is skipped although a tool reads it.",
            "A README.md in an examples directory is skipped though a tool reads it.",
            "A README.md in an examples directory is skipped whereas a tool reads it.",
            "A README.md in an examples directory is skipped while a tool reads it.",
            "It checks every Markdown file other than `examples/README.md`.",
            "It checks every Markdown file apart from `examples/README.md`.",
        ):
            self.assertIsNone(NEGATION.search(text), text)
            self.assertEqual([], readme_exception_statements(text), text)

    def test_each_negation_word_rejects_a_clause_on_its_own(self):
        # One clause per word, naming the README, the directory and the verb, so it would be counted without the word.
        for text, word in (
            ("A README.md in an examples directory is not read when the checker reads the tree.", "not"),
            ("The checker reads no README.md in an examples directory.", "no"),
            ("No README.md in an examples directory is read.", "No"),
            ("The checker never reads a README.md in an examples directory.", "never"),
        ):
            with self.subTest(text=text):
                self.assertEqual([text], CLAUSE_BREAK.split(text))
                self.assertTrue(all(p.search(text) for p in (README_PATTERN, EXAMPLE_DIR_PATTERN, READ_VERB)))
                self.assertEqual([word], NEGATION.findall(text))
                self.assertEqual([], readme_exception_statements(text))

    def test_readme_exception_split_across_a_break_is_not_counted(self):
        # The README, the directory and the verb have to sit between the same two breaks.
        for text in (
            "In an examples directory, a README.md is read.",
            "A README.md is read because it is in an examples directory.",
        ):
            self.assertEqual([], readme_exception_statements(text), text)

    def test_clause_break_splits_a_run_of_whitespace_in_linear_time(self):
        skip_the_time_bound_when_optimized(self)
        start = time.perf_counter()
        CLAUSE_BREAK.split(" " * 50000)
        self.assertLess(time.perf_counter() - start, 2.0)

    def test_text_without_the_readme_exception_is_reported(self):
        for text in (
            "It does not read `CHANGELOG.md` or the example governance files under `examples/`.",
            "It does not read the files under `examples/`, `examples/README.md` among them.",
            "Anything in an examples directory is data a tool reads. A README.md describes a directory to a person.",
            "A README.md in an examples directory is not read.",
            "A README.md in an examples directory is not read, since only a tool reads it.",
            "A README.md in an examples directory is not read since only a tool reads it.",
            "It checks every Markdown file except `examples/README.md`.",
            "A README.md in an examples directory is not read and only a tool reads it.",
            "A README.md in an examples directory is not read when the checker reads the tree.",
            "It checks every Markdown file other than `examples/README.md`.",
            "It checks every Markdown file apart from `examples/README.md`.",
            "The checker reads no README.md in an examples directory.",
            "No README.md in an examples directory is read.",
            "A README.md in an examples directory is never checked.",
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


def user_environment(home):
    """The environment without GIT_ variables, with home as the user's home and git configuration directory."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(Path(home) / ".config"))
    return env


def skip_unless_git_is_installed(test):
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True, timeout=60)
    except (OSError, subprocess.CalledProcessError):
        test.skipTest("git is not available")


class GitRepositories(unittest.TestCase):
    """The tests that build a git repository run when an ignore file of the user's matches their files, and say
    which git command failed when one does."""

    def test_a_global_gitignore_that_matches_the_fixture_files_skips_no_test(self):
        # `git add` exits 1 for an ignored path, which these tests used to report as "git is not available".
        # `git config` writes the path, so a backslash in it is escaped as the .gitconfig syntax requires.
        paths = ["a.md", "b.mdx", "sub/vendor/a.md"]
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as repo:
            write_tree(home, {"ignore": "vendor/\n*.md\n*.mdx\n"})
            env = user_environment(home)
            gitconfig = str(Path(home) / ".gitconfig")
            run_git(self, home, ["config", "--file", gitconfig, "core.excludesFile", str(Path(home) / "ignore")], env)
            run_git(self, repo, ["init", "-q"], env)
            ignored = subprocess.run(["git", "-C", repo, "check-ignore", *paths], capture_output=True, env=env,
                                     timeout=60)
            self.assertEqual(paths, ignored.stdout.decode("utf-8").split(), "the global ignore file is not in effect")
            result = unittest.TestResult()
            with mock.patch.dict(os.environ, env, clear=True):
                unittest.TestSuite([
                    CommandLine("test_tracked_md_and_mdx_files_are_read_and_untracked_ones_are_not"),
                    Contributing("test_prefix_exclusions_apply_at_the_root_given_as_the_argument"),
                ]).run(result)
        self.assertEqual([], [(test.id(), reason) for test, reason in result.skipped])
        self.assertEqual([], [test.id() for test, _ in result.failures + result.errors])
        self.assertEqual(2, result.testsRun)

    def test_a_temporary_directory_whose_path_holds_a_backslash_skips_no_test(self):
        # A path formatted into a double-quoted .gitconfig value by hand made git reject the file, as on Windows.
        skip_unless_git_is_installed(self)
        with tempfile.TemporaryDirectory() as base:
            tmp = Path(base) / "x\\q"
            tmp.mkdir(parents=True)
            result = unittest.TestResult()
            with mock.patch.object(tempfile, "tempdir", str(tmp)):
                GitRepositories("test_a_global_gitignore_that_matches_the_fixture_files_skips_no_test").run(result)
        self.assertEqual([], [(test.id(), reason) for test, reason in result.skipped])
        self.assertEqual([], [test.id() for test, _ in result.failures + result.errors])
        self.assertEqual(1, result.testsRun)

    def test_a_failing_git_command_skips_with_the_command_and_its_error(self):
        # A .gitconfig that git cannot parse makes `git init` exit 128 while git is installed.
        skip_unless_git_is_installed(self)
        with tempfile.TemporaryDirectory() as home:
            write_tree(home, {".gitconfig": "[core\nbroken\n"})
            result = unittest.TestResult()
            with mock.patch.dict(os.environ, user_environment(home), clear=True):
                CommandLine("test_tracked_md_and_mdx_files_are_read_and_untracked_ones_are_not").run(result)
        reasons = [reason for _, reason in result.skipped]
        self.assertEqual(1, len(reasons), reasons)
        self.assertTrue(reasons[0].startswith("git init -q failed: "), reasons[0])


class Repository(unittest.TestCase):
    def test_committed_prose_passes(self):
        code, out, err = run_main()
        self.assertEqual(0, code, out + err)
        self.assertEqual("", out)


class StrippedDocstrings(unittest.TestCase):
    def test_docstring_tests_skip_with_a_reason_under_python3_OO(self):
        # python3 -OO strips the docstrings of this file and of check_docs_prose.py, so each test that reads a
        # docstring skips, and the run passes.
        if sys.flags.optimize >= 2:
            self.skipTest("this is the python3 -OO run that the test starts")
        # scripts/test_stripped_docstrings.py runs this file under python3 -OO itself, and sets ABGS_PYTHON3_O_RUN in
        # the python3 -O run of this file that it starts, so that run starts no third python3 -OO run.
        if sys.flags.optimize == 1 and "ABGS_PYTHON3_O_RUN" in os.environ:
            self.skipTest("test_stripped_docstrings.py, which started this run, runs this file with docstrings stripped")
        result = subprocess.run([sys.executable, "-OO", str(Path(__file__).resolve()), "-v"],
                                capture_output=True, text=True, timeout=300)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("skipped 'python3 -OO strips docstrings, so check_docs_prose has none to check'",
                      result.stderr)
        self.assertIn("skipped 'python3 -OO strips docstrings, so excluded has none to check'", result.stderr)

    def test_a_missing_docstring_is_an_error_without_python3_OO(self):
        # A docstring missing from the source, for example because a statement was placed above it, is None without
        # -OO too, and the test that reads it must then report an error, not a skip.
        if sys.flags.optimize >= 2:
            self.skipTest("under python3 -OO the test that reads a docstring skips on purpose")
        result = unittest.TestResult()
        with mock.patch.object(cdp, "__doc__", None):
            CommandLine("test_usage_and_docstring_name_the_optional_root_argument").run(result)
        self.assertEqual([], result.skipped)
        self.assertEqual(1, len(result.errors), result.errors)


class TimeBounds(unittest.TestCase):
    def test_runs_under_python3_O_and_OO_skip_the_time_bounds(self):
        # The python3 -OO run started above, and those under -O and -OO started by test_stripped_docstrings.py,
        # skip each test that times a scan, so only the run without -O can fail on a loaded machine. A skip placed
        # after the timed call still reports a skip, so the clock of this module fails the test that reads it.
        # unittest times each test with time.perf_counter too, so only this module's name is replaced.
        for optimize in (1, 2):
            result = unittest.TestResult()
            clock = mock.Mock(perf_counter=mock.Mock(side_effect=self.failureException("timed before the skip")))
            with self.subTest(optimize=optimize), mock.patch.object(sys, "flags", mock.Mock(optimize=optimize)), \
                    mock.patch.object(sys.modules[__name__], "time", clock):
                unittest.TestSuite([
                    CodeSpans("test_long_runs_of_backticks_are_scanned_in_linear_time"),
                    Contributing("test_clause_break_splits_a_run_of_whitespace_in_linear_time"),
                ]).run(result)
                clock.perf_counter.assert_not_called()
                self.assertEqual([TIME_BOUND_SKIP] * 2, [reason for _, reason in result.skipped])

    def test_the_run_without_python3_O_checks_the_time_bounds(self):
        # A skip here would report this test as skipped, not failed, so skipTest is replaced and must not be called.
        with mock.patch.object(sys, "flags", mock.Mock(optimize=0)), mock.patch.object(self, "skipTest") as skip:
            skip_the_time_bound_when_optimized(self)
        skip.assert_not_called()


if __name__ == "__main__":
    unittest.main()
