#!/usr/bin/env python3
"""Tests for the agent profiles as specification.md, scoring.md and docs/overview.md state them.

Run from anywhere:  python3 scripts/test_agent_profiles.py

The set of controls a scan evaluates is decided by the tier and the agent
profile together: the profile removes whole domains from the tier's controls.
specification.md section 3.6 defines the profiles and gives the applicable
count for each tier and profile. These tests hold those counts to the section
3.5 matrix, hold the tier counts of sections 3.1 to 3.4 to the profiles that
skip no domain, and require the scoring text to name both tier and profile.

Standard library only. The tests read the documents and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SPECIFICATION = ROOT / "specification.md"
SCORING = ROOT / "scoring.md"
OVERVIEW = ROOT / "docs" / "overview.md"

TIERS = ("BASIC", "TOOL-USING", "AGENTIC", "MULTI-AGENT")
TIER_SECTIONS = ("### 3.1 BASIC", "### 3.2 TOOL-USING", "### 3.3 AGENTIC", "### 3.4 MULTI-AGENT")
PROFILES = ("conversational", "code-assistant", "tool-agent", "autonomous", "orchestrator", "custom")
DOMAINS = frozenset(range(11, 20))
DOMAIN_OF_CODE = {"TH": 11, "CB": 12, "IH": 13, "DH": 14, "HB": 15, "AS": 16, "HT": 17, "HO": 18, "HV": 19}
# The domains of the two CRITICAL controls, SOUL-IH-003 and SOUL-HB-001 (section 6.4).
CRITICAL_DOMAINS = frozenset([13, 15])
MATRIX_ROW = re.compile(r"^\| SOUL-([A-Z]{2})-\d{3} \|((?: (?:Yes|--) \|){4})$", re.MULTILINE)
TIER_COUNT = re.compile(r"^\*\*Applicable controls\*\*: (\d+)\b", re.MULTILINE)
NAMES_TIER_AND_PROFILE = re.compile(r"\bnames? both (?:the|its) tier and (?:the|its) profile\b")


def section(text, heading):
    """The text from heading up to the next heading of the same or a higher level, or a rule."""
    level = len(heading) - len(heading.lstrip("#"))
    start = text.find(heading + "\n")
    if start < 0:
        return None
    rest = text[start + len(heading) + 1:]
    end = re.search(r"^(?:#{1,%d} |---$)" % level, rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


def table(text, header):
    """The cells of each body row of the table whose header row starts with header."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                rows.append([cell.strip() for cell in row.strip().strip("|").split("|")])
            return rows
    return None


def matrix(spec):
    """(domain, applicable per tier) for each row of the section 3.5 matrix."""
    body = section(spec, "### 3.5 Control Applicability Matrix") or ""
    return [
        (DOMAIN_OF_CODE[code], [cell.strip() == "Yes" for cell in cells.strip().strip("|").split("|")])
        for code, cells in MATRIX_ROW.findall(body)
    ]


def domain_list(cell):
    """The domain numbers in a cell such as "13, 15, 17, 19", or none for "none"."""
    return frozenset() if cell == "none" else frozenset(int(n) for n in cell.split(","))


def profile_domains(spec):
    """{profile: (included, skipped)} from the profile table of section 3.6."""
    rows = table(section(spec, "### 3.6 Agent Profiles") or "", "| Profile | Agent purpose |") or []
    return {row[0].strip("`"): (domain_list(row[2]), domain_list(row[3])) for row in rows}


def profile_counts(spec):
    """{profile: [count per tier]} from the count table of section 3.6."""
    rows = table(section(spec, "### 3.6 Agent Profiles") or "", "| Profile | BASIC |") or []
    return {row[0].strip("`"): [int(cell) for cell in row[1:]] for row in rows}


def expected_counts(rows, included):
    """The number of matrix rows applicable to each tier whose domain is in included."""
    return [sum(1 for domain, applies in rows if applies[t] and domain in included) for t in range(len(TIERS))]


class ProfileTables(unittest.TestCase):
    def setUp(self):
        self.spec = SPECIFICATION.read_text(encoding="utf-8")
        self.rows = matrix(self.spec)
        self.profiles = profile_domains(self.spec)
        self.counts = profile_counts(self.spec)

    def test_matrix_has_every_control(self):
        self.assertEqual(len(self.rows), 72)

    def test_specification_defines_each_profile(self):
        self.assertEqual(sorted(self.profiles), sorted(PROFILES))
        self.assertEqual(sorted(self.counts), sorted(PROFILES))

    def test_included_and_skipped_domains_divide_the_nine_domains(self):
        for name, (included, skipped) in self.profiles.items():
            with self.subTest(profile=name):
                self.assertEqual(included | skipped, DOMAINS)
                self.assertEqual(included & skipped, frozenset())

    def test_every_profile_includes_the_domains_of_the_critical_controls(self):
        for name, (included, _) in self.profiles.items():
            with self.subTest(profile=name):
                self.assertLessEqual(CRITICAL_DOMAINS, included)

    def test_counts_are_the_matrix_restricted_to_the_profile_domains(self):
        for name, (included, _) in self.profiles.items():
            with self.subTest(profile=name):
                self.assertEqual(self.counts[name], expected_counts(self.rows, included))

    def test_tier_counts_are_those_of_a_profile_that_skips_no_domain(self):
        stated = []
        for heading in TIER_SECTIONS:
            match = TIER_COUNT.search(section(self.spec, heading) or "")
            self.assertIsNotNone(match, heading)
            stated.append(int(match.group(1)))
        self.assertEqual(stated, expected_counts(self.rows, DOMAINS))
        for name, (_, skipped) in self.profiles.items():
            if not skipped:
                with self.subTest(profile=name):
                    self.assertEqual(self.counts[name], stated)

    def test_a_count_that_ignores_the_profile_is_reported(self):
        text = self.spec.replace("| `code-assistant` | 29 | 40 |", "| `code-assistant` | 29 | 57 |")
        self.assertNotEqual(text, self.spec)
        included, _ = profile_domains(text)["code-assistant"]
        self.assertNotEqual(profile_counts(text)["code-assistant"], expected_counts(self.rows, included))


class ScoresNameTierAndProfile(unittest.TestCase):
    def test_specification_scoring_names_tier_and_profile(self):
        spec = SPECIFICATION.read_text(encoding="utf-8")
        self.assertRegex(section(spec, "## 6. Scoring Methodology") or "", NAMES_TIER_AND_PROFILE)

    def test_scoring_document_names_tier_and_profile(self):
        self.assertRegex(SCORING.read_text(encoding="utf-8"), NAMES_TIER_AND_PROFILE)

    def test_overview_names_tier_and_profile(self):
        overview = OVERVIEW.read_text(encoding="utf-8")
        self.assertRegex(section(overview, "## Agent Tiers") or "", r"Section 3\.6")
        self.assertRegex(section(overview, "## Scoring") or "", NAMES_TIER_AND_PROFILE)

    def test_a_score_without_its_profile_is_reported(self):
        self.assertNotRegex("A published score names the tier it was measured under.", NAMES_TIER_AND_PROFILE)


if __name__ == "__main__":
    unittest.main()
