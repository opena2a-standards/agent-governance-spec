#!/usr/bin/env python3
"""Tests for the critical floor rule as README.md, specification.md and scoring.md state it.

Run from anywhere:  python3 scripts/test_critical_floor.py

The critical floor caps the grade at C when an applicable CRITICAL control is
missing. The overall score is reported as calculated, so the documents must
not promise a score cap the scanner does not apply.

Standard library only. The tests read the documents and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = ("README.md", "specification.md", "scoring.md")
SCORE_CAP = re.compile(
    r"effective maximum score|\(score 60\)|capped at C \(60\)|score (is )?capped",
    re.IGNORECASE,
)
SCORE_KEPT = "the overall score is reported as calculated"
EXAMPLE_HEADING = "### Example 3: Critical Floor in Action"


def floor_passage(name, text):
    """The text in which a document states the critical floor rule."""
    if name == "README.md":
        match = re.search(r"^- \*\*Critical floor\*\*:.*$", text, re.MULTILINE)
    elif name == "specification.md":
        match = re.search(r"^### 6\.4 Critical Floor Rule\n(.*?)(?=^#)", text, re.MULTILINE | re.DOTALL)
    else:
        match = re.search(r"^## Critical Floor Rule\n(.*?)(?=^---)", text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None


def section(text, heading):
    """The body under heading, up to the next horizontal rule or heading."""
    match = re.search(re.escape(heading) + r"\n(.*?)(?=^---|^#)", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


class CriticalFloor(unittest.TestCase):
    def setUp(self):
        self.texts = {name: (ROOT / name).read_text(encoding="utf-8") for name in DOCUMENTS}

    def test_no_document_caps_the_score(self):
        for name, text in self.texts.items():
            with self.subTest(document=name):
                self.assertEqual([m.group(0) for m in SCORE_CAP.finditer(text)], [])

    def test_each_document_states_the_score_is_kept(self):
        for name, text in self.texts.items():
            with self.subTest(document=name):
                passage = floor_passage(name, text)
                self.assertIsNotNone(passage)
                self.assertIn(SCORE_KEPT, passage.lower())

    def test_worked_example_keeps_the_calculated_score_beside_grade_c(self):
        body = section(self.texts["scoring.md"], EXAMPLE_HEADING)
        self.assertIsNotNone(body)
        self.assertIn("**Calculated overall score**: 86", body)
        self.assertRegex(body, r"\*\*Final score and grade\*\*: 86, grade C \(capped from A\)")

    def test_a_score_cap_claim_is_reported(self):
        claims = (
            "the maximum grade is C (effective maximum score 60)",
            "the maximum grade is capped at **C** (score 60)",
            "Maximum grade capped at C (60).",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIsNotNone(SCORE_CAP.search(claim))


if __name__ == "__main__":
    unittest.main()
