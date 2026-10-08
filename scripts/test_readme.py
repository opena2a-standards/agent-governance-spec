#!/usr/bin/env python3
"""Tests for the command blocks in README.md.

Run from anywhere:  python3 scripts/test_readme.py

Standard library only. The tests read README.md and write nothing.
"""

import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

README = Path(__file__).resolve().parent.parent / "README.md"
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
COPY_TEMPLATE = re.compile(r"^cp templates/\S+\.md SOUL\.md$")
EDIT_STEP = "# Edit to match your agent's actual constraints"


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


if __name__ == "__main__":
    unittest.main()
