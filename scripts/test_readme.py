#!/usr/bin/env python3
"""Tests for the command blocks in README.md, the scan-soul JSON sample in integrations/README.md,
the conformance badge URLs in README.md, integrations/README.md and conformance.md, and the score
thresholds those three files name.

Run from anywhere:  python3 scripts/test_readme.py

Standard library only. The tests read README.md, integrations/README.md and conformance.md and write nothing.
"""

import json
import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

README = Path(__file__).resolve().parent.parent / "README.md"
INTEGRATIONS = README.parent / "integrations" / "README.md"
CONFORMANCE_DOC = README.parent / "conformance.md"
BADGE_DOCS = (README, INTEGRATIONS, CONFORMANCE_DOC)
BADGE_URL = re.compile(r"https://img\.shields\.io/badge/([^)\s`?]+)")
LEVELS = ("Essential", "Standard", "Hardened")
# A score with a conformance level as its label: "40 (Essential)", "`--fail-below 40` (Essential)".
SCORE_LEVEL_LABEL = re.compile(r"(\d+)`?\s*\((" + "|".join(LEVELS) + r")\)")
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
JSON_FENCE = re.compile(r"^```json\n(.*?)^```", re.MULTILINE | re.DOTALL)
TABLE_KEY = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
COPY_TEMPLATE = re.compile(r"^cp templates/\S+\.md SOUL\.md$")
EDIT_STEP = "# Edit to match your agent's actual constraints"

# The shape `scan-soul --json` of hackmyagent 0.33.2 prints for a scanned governance file.
SCAN_KEYS = {
    "agentProfile", "agentTier", "conformance", "coverage", "criticalFloor", "criticalMissing",
    "criticalMissingDetail", "domains", "file", "fileReadFailed", "fileSize", "gate", "grade",
    "hackmyagentVersion", "level", "profileForced", "rawScore", "score", "scoreClamped",
    "skippedDomains", "tierForced", "totalControls", "totalPassed", "violations", "withheldLinks",
}
DOMAIN_KEYS = {"domain", "domainId", "controls", "passed", "total", "percentage"}
OPTIONAL_DOMAIN_KEYS = {"skippedByProfile"}
CONTROL_KEYS = {"id", "name", "domain", "keywords", "passed"}
CONFORMANCE = {"none", "essential", "standard", "hardened"}
TIERS = {"BASIC", "TOOL-USING", "AGENTIC", "MULTI-AGENT"}


def command_blocks(text):
    """The lines of each fenced block in text, stripped."""
    return [[line.strip() for line in body.splitlines()] for body in FENCE.findall(text)]


def template_scans(text):
    """Each (block, copy line index, scan line index) where a block copies a template and then scans it."""
    found = []
    for block in command_blocks(text):
        for i, line in enumerate(block):
            if COPY_TEMPLATE.match(line):
                scan = next((j for j in range(i + 1, len(block)) if "scan-soul" in block[j]), None)
                if scan is not None:
                    found.append((block, i, scan))
    return found


def scan_sample(text):
    """The first JSON block of text that holds a scan result, parsed, or None."""
    for body in JSON_FENCE.findall(text):
        data = json.loads(body)
        if isinstance(data, dict) and "score" in data:
            return data
    return None


def sample_problems(sample):
    """Each way sample differs from the shape of a scan-soul --json document."""
    problems = [f"top-level key {key} is not printed by the scanner" for key in sorted(set(sample) - SCAN_KEYS)]
    problems += [f"top-level key {key} is missing" for key in sorted(SCAN_KEYS - set(sample))]
    if sample.get("conformance") not in CONFORMANCE:
        problems.append(f"conformance {sample.get('conformance')!r} is not one of {sorted(CONFORMANCE)}")
    if sample.get("agentTier") not in TIERS:
        problems.append(f"agentTier {sample.get('agentTier')!r} is not one of {sorted(TIERS)}")
    domains = sample.get("domains")
    if not isinstance(domains, list):
        return problems + ["domains is not an array"]
    for entry in domains:
        keys = set(entry)
        if not DOMAIN_KEYS <= keys <= DOMAIN_KEYS | OPTIONAL_DOMAIN_KEYS:
            problems.append(f"domain entry {entry.get('domain')!r} has keys {sorted(keys)}")
        for control in entry.get("controls", []):
            if set(control) != CONTROL_KEYS:
                problems.append(f"control {control.get('id')!r} has keys {sorted(control)}")
    return problems


def table_keys(text):
    """The keys named in the first column of the Markdown tables in text."""
    return TABLE_KEY.findall(text)


def in_sample(sample, key):
    """Whether key, a top-level name or a domains[].<name> path, appears in sample."""
    if key.startswith("domains[]."):
        name = key[len("domains[]."):]
        return any(name in entry for entry in sample.get("domains", []))
    return key in sample


def badge_parts(path):
    """The (label, message, colour) shields.io reads from a static badge path, or None when it reads no badge.

    A single dash separates the three parts, and a double dash stands for one dash inside a part.
    """
    parts = [part.replace("\0", "-") for part in path.replace("--", "\0").split("-")]
    return tuple(parts) if len(parts) == 3 and all(parts) else None


def level_colours(texts):
    """For each conformance level, the set of colours its badges in texts use, whether or not the label is escaped."""
    colours = {}
    for text in texts:
        for path in BADGE_URL.findall(text):
            message, colour = path.rsplit("-", 2)[-2:]
            if message in LEVELS:
                colours.setdefault(message, set()).add(colour)
    return colours


def score_level_labels(text):
    """Each (score, level) where text labels a score with a conformance level.

    A level is a set of controls that must pass, with a minimum score for Standard and Hardened
    and none for Essential, so a score is not a level.
    """
    return SCORE_LEVEL_LABEL.findall(text)


class TemplateScans(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_readme_copies_a_template_and_scans_it(self):
        self.assertGreaterEqual(len(template_scans(self.text)), 2)

    def test_every_template_copy_is_edited_before_it_is_scanned(self):
        for block, copy, scan in template_scans(self.text):
            with self.subTest(block="\n".join(block)):
                self.assertIn(EDIT_STEP, block[copy + 1:scan])

    def test_block_without_the_edit_step_is_reported(self):
        text = "```bash\ncp templates/tool-using.md SOUL.md\nnpx hackmyagent scan-soul\n```\n"
        (block, copy, scan), = template_scans(text)
        self.assertNotIn(EDIT_STEP, block[copy + 1:scan])


class IntegrationsJsonSample(unittest.TestCase):
    def setUp(self):
        self.text = INTEGRATIONS.read_text(encoding="utf-8")
        self.sample = scan_sample(self.text)

    def test_sample_has_the_scanner_shape(self):
        self.assertIsNotNone(self.sample)
        self.assertEqual(sample_problems(self.sample), [])

    def test_every_key_in_the_table_is_in_the_sample(self):
        keys = table_keys(self.text)
        self.assertGreaterEqual(len(keys), 2)
        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(in_sample(self.sample, key))

    def test_sample_in_another_shape_is_reported(self):
        text = (
            '```json\n{"score": 67, "grade": "C", "conformance": "NONE", "file": "SOUL.md",'
            ' "tier": "AGENTIC", "domains": {"Trust Hierarchy": {"found": 2, "total": 3}},'
            ' "controls": [{"id": "SOUL-TH-001", "name": "Trust chain defined", "passed": true}]}\n```\n'
        )
        problems = sample_problems(scan_sample(text))
        self.assertIn("top-level key tier is not printed by the scanner", problems)
        self.assertIn("top-level key controls is not printed by the scanner", problems)
        self.assertIn("top-level key agentTier is missing", problems)
        self.assertIn("domains is not an array", problems)
        self.assertTrue(any(p.startswith("conformance 'NONE'") for p in problems))

    def test_control_with_other_keys_is_reported(self):
        sample = {"domains": [{"domain": "Trust Hierarchy", "domainId": 11, "passed": 1, "total": 1,
                               "percentage": 100, "controls": [{"id": "SOUL-TH-001", "passed": True}]}]}
        self.assertIn("control 'SOUL-TH-001' has keys ['id', 'passed']", sample_problems(sample))


class ConformanceBadges(unittest.TestCase):
    def setUp(self):
        self.texts = {path.relative_to(README.parent).as_posix(): path.read_text(encoding="utf-8")
                      for path in BADGE_DOCS}

    def test_every_badge_reads_oasb_2_and_a_message(self):
        for name, text in self.texts.items():
            paths = BADGE_URL.findall(text)
            self.assertGreaterEqual(len(paths), 3, name)
            for path in paths:
                with self.subTest(file=name, badge=path):
                    parts = badge_parts(path)
                    self.assertIsNotNone(parts)
                    self.assertEqual(parts[0], "OASB-2")

    def test_each_level_has_one_colour(self):
        colours = level_colours(self.texts.values())
        self.assertEqual(set(colours), set(LEVELS))
        for level in LEVELS:
            with self.subTest(level=level):
                self.assertEqual(len(colours[level]), 1, sorted(colours[level]))

    def test_single_dash_after_oasb_reads_no_badge(self):
        self.assertIsNone(badge_parts("OASB-2-Essential-blue"))
        self.assertEqual(badge_parts("OASB--2-Essential-blue"), ("OASB-2", "Essential", "blue"))

    def test_level_in_two_colours_is_reported(self):
        texts = [
            "![OASB-2 Standard](https://img.shields.io/badge/OASB--2-Standard-teal)",
            "![OASB-2 Standard](https://img.shields.io/badge/OASB-2-Standard-green)",
        ]
        self.assertEqual(level_colours(texts), {"Standard": {"teal", "green"}})


class ScoreThresholds(unittest.TestCase):
    def test_no_score_is_labelled_as_a_conformance_level(self):
        for path in BADGE_DOCS:
            name = path.relative_to(README.parent).as_posix()
            with self.subTest(file=name):
                self.assertEqual(score_level_labels(path.read_text(encoding="utf-8")), [])

    def test_score_labelled_as_a_level_is_reported(self):
        self.assertEqual(
            score_level_labels("1. Add `scan-soul` to CI pipeline with `--fail-below 40` (Essential)\n"),
            [("40", "Essential")],
        )
        self.assertEqual(
            score_level_labels("3. Raise threshold over time: 40 (Essential) -> 60 (Standard) -> 75 (Hardened)\n"),
            [("40", "Essential"), ("60", "Standard"), ("75", "Hardened")],
        )

    def test_minimum_score_of_a_level_is_not_reported(self):
        self.assertEqual(score_level_labels("60 (the minimum score for Standard), overall score >= 75\n"), [])


if __name__ == "__main__":
    unittest.main()
