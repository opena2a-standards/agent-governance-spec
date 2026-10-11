#!/usr/bin/env python3
"""Tests for the exit codes that integrations/README.md documents for
`hackmyagent scan-soul`.

Run from anywhere:  python3 scripts/test_integrations_readme.py

Standard library only. The tests read integrations/README.md and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

README = Path(__file__).resolve().parent.parent / "integrations" / "README.md"
ITEM = re.compile(r"^- `(\d+)`:")

# The exit code the scanner gives each `gate.reason` it prints with --json,
# measured with hackmyagent 0.33.2: a file missing a CRITICAL control, no
# governance file, an unreadable one, and an empty one.
GATE_REASONS = {
    "critical-control-missing": 1,
    "no-governance-file": 2,
    "governance-file-unreadable": 2,
    "governance-file-empty": 2,
}

# The flags that fail a run with exit 1 on their own, outside `gate`.
FLAGS_THAT_EXIT_1 = ("--fail-below", "--ci")


def exit_codes(text):
    """Each documented exit code mapped to its list item, nested lines included."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith("Exit codes")), None)
    if start is None:
        return {}
    items = {}
    code = None
    for line in lines[start + 1:]:
        if line.startswith("#"):
            break
        match = ITEM.match(line)
        if match:
            code = int(match.group(1))
            items[code] = line
        elif code is not None and line.startswith("  "):
            items[code] += "\n" + line
        else:
            code = None
    return items


class ExitCodes(unittest.TestCase):
    def setUp(self):
        self.items = exit_codes(README.read_text(encoding="utf-8"))

    def test_the_three_exit_codes_are_documented(self):
        self.assertEqual(sorted(self.items), [0, 1, 2])

    def test_each_gate_reason_is_under_its_exit_code_and_no_other(self):
        for reason, code in GATE_REASONS.items():
            with self.subTest(reason=reason):
                self.assertEqual([c for c, item in self.items.items() if f"`{reason}`" in item], [code])

    def test_exit_1_names_each_flag_that_fails_a_run(self):
        for flag in FLAGS_THAT_EXIT_1:
            with self.subTest(flag=flag):
                self.assertIn(f"`{flag}`", self.items[1])

    def test_exit_0_requires_essential_conformance(self):
        self.assertIn("Essential", self.items[0])

    def test_score_threshold_alone_is_reported(self):
        text = (
            "Exit codes:\n"
            "- `0`: Scan completed (check score for pass/fail)\n"
            "- `1`: Score below `--fail-below` threshold\n"
            "- `2`: No governance file found\n"
        )
        items = exit_codes(text)
        self.assertEqual(sorted(items), [0, 1, 2])
        self.assertNotIn("`critical-control-missing`", items[1])
        self.assertNotIn("Essential", items[0])


if __name__ == "__main__":
    unittest.main()
