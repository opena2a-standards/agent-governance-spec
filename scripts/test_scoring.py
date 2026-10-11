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
GUIDE_EXIT_CODE = re.compile(r"^- `(\d+)`: No governance file found$", re.MULTILINE)


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
        (listed,) = GUIDE_EXIT_CODE.findall(GUIDE.read_text(encoding="utf-8"))
        self.assertEqual(EXIT_CODE.findall(self.body), [listed])

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


if __name__ == "__main__":
    unittest.main()
