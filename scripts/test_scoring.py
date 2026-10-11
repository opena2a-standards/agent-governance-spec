#!/usr/bin/env python3
"""Tests for the "No Governance File Found" edge case in scoring.md.

Run from anywhere:  python3 scripts/test_scoring.py

Standard library only. The tests read scoring.md and integrations/README.md
and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SCORING = ROOT / "scoring.md"
GUIDE = ROOT / "integrations" / "README.md"
HEADING = "### No Governance File Found"
PROMISED_VALUE = re.compile(r"\b(?:score|grade) is (?:\d+|[A-F])\b")
EXIT_CODE = re.compile(r"\bexits? with code (\d+)\b")
GUIDE_EXIT_ENTRY = re.compile(r"^- `(\d+)`: ")
MISSING_FILE = "no governance file"


def missing_file_exit_codes(text):
    """The exit codes in the guide's list whose entry names a missing governance file.

    An entry is a top-level "- `N`: ..." line together with the indented lines
    under it, so the case is found whether the guide names it on the entry
    line or in a sub-bullet such as "`no-governance-file`".
    """
    codes = []
    code = None
    for line in text.splitlines():
        entry = GUIDE_EXIT_ENTRY.match(line)
        if entry:
            code = entry.group(1)
        elif not line.startswith(" "):
            code = None
        if code and MISSING_FILE in line.lower() and code not in codes:
            codes.append(code)
    return codes


def section(text, heading):
    """The prose under heading, up to the next heading or horizontal rule."""
    lines = text.splitlines()
    body = []
    for line in lines[lines.index(heading) + 1:]:
        if line.startswith("#") or line.strip() == "---":
            break
        body.append(line)
    return "\n".join(body).strip()


class NoGovernanceFile(unittest.TestCase):
    def setUp(self):
        self.body = section(SCORING.read_text(encoding="utf-8"), HEADING)

    def test_no_score_or_grade_value_is_promised(self):
        self.assertIsNone(PROMISED_VALUE.search(self.body), self.body)

    def test_score_is_withheld(self):
        self.assertIn("the score is withheld", self.body)

    def test_exit_code_is_the_one_the_integrations_guide_lists(self):
        listed = missing_file_exit_codes(GUIDE.read_text(encoding="utf-8"))
        self.assertEqual(len(listed), 1, listed)
        self.assertEqual(EXIT_CODE.findall(self.body), listed)

    def test_section_that_promises_a_score_and_grade_is_reported(self):
        text = "\n".join([
            "## Edge Cases",
            "",
            HEADING,
            "",
            "If no governance file is found in the search path, the score is 0 and grade is F.",
            "",
            "### Governance File Below Minimum Requirements",
            "",
            "The scanner exits with code 9.",
        ])
        body = section(text, HEADING)
        self.assertEqual(PROMISED_VALUE.findall(body), ["score is 0", "grade is F"])
        self.assertEqual(EXIT_CODE.findall(body), [])


class GuideExitCodes(unittest.TestCase):
    def test_case_named_on_the_entry_line(self):
        text = "\n".join([
            "Exit codes:",
            "- `0`: Scan completed",
            "- `1`: Score below `--fail-below` threshold",
            "- `2`: No governance file found",
        ])
        self.assertEqual(missing_file_exit_codes(text), ["2"])

    def test_case_named_in_a_sub_bullet(self):
        text = "\n".join([
            "When no governance file is found (exit code 3), `score` is `null`.",
            "",
            "Exit codes:",
            "- `0`: Conformance is Essential or better.",
            "- `1`: The run failed for one of these reasons:",
            "  - The score is below the `--fail-below` threshold.",
            "- `2`: Nothing was measured, so no score is reported:",
            "  - `no-governance-file`: no governance file was found.",
            "  - `governance-file-empty`: a governance file was found and is empty.",
        ])
        self.assertEqual(missing_file_exit_codes(text), ["2"])


if __name__ == "__main__":
    unittest.main()
