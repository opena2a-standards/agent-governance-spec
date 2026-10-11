#!/usr/bin/env python3
"""Tests for integrations/github-action.yml: the script that comments on the
pull request, run on JSON in the shape `hackmyagent scan-soul --json` prints.

Run from anywhere:  python3 scripts/test_github_action.py

Standard library only. The tests need node on PATH to run the comment script
and are skipped without it; they write only to a temporary directory.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ACTION = Path(__file__).resolve().parent.parent / "integrations" / "github-action.yml"
OUTPUT = re.compile(r"\$\{\{\s*steps\.scan\.outputs\.(\w+)\s*\}\}")
OUTPUTS = {"score": "67", "grade": "C", "conformance": "NONE", "file": "SOUL.md"}

# The scanner prints `domains` as an array, one entry per domain. The counts
# are from a scan of examples/coding-agent-soul.md; controls are left out.
SCAN = {
    "file": "SOUL.md",
    "score": 67,
    "grade": "C",
    "conformance": "NONE",
    "domains": [
        {"domain": "Trust Hierarchy", "domainId": 11, "passed": 3, "total": 7, "percentage": 43, "controls": []},
        {"domain": "Capability Boundaries", "domainId": 12, "passed": 5, "total": 10, "percentage": 50, "controls": []},
        {"domain": "Harm Avoidance", "domainId": 19, "passed": 4, "total": 4, "percentage": 100, "controls": []},
    ],
}

# Runs the comment script as actions/github-script does, as the body of an
# async function, with stand-ins for the GitHub client and the run context.
HARNESS = """
const fs = require('fs');
const script = fs.readFileSync(process.argv[2], 'utf8');
const bodies = [];
const record = async (args) => { bodies.push(args.body); return { data: {} }; };
const github = { rest: { issues: {
  listComments: async () => ({ data: [] }),
  createComment: record,
  updateComment: record,
} } };
const context = { repo: { owner: 'owner', repo: 'repo' }, issue: { number: 1 } };
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction('require', 'github', 'context', script)(require, github, context)
  .then(() => process.stdout.write(JSON.stringify(bodies)))
  .catch((err) => { console.error(err); process.exit(1); });
"""


def comment_script(text):
    """The `script: |` block of the action, with its indentation removed as YAML reads it."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "script: |")
    key_indent = len(lines[start]) - len(lines[start].lstrip())
    block = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= key_indent:
            break
        block.append(line)
    first = next(line for line in block if line.strip())
    indent = len(first) - len(first.lstrip())
    return "\n".join(line[indent:] for line in block).rstrip() + "\n"


def comment_body(scan_result):
    """The comment the action posts when scan-result.json holds scan_result."""
    script = OUTPUT.sub(lambda m: OUTPUTS[m.group(1)], comment_script(ACTION.read_text(encoding="utf-8")))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "scan-result.json").write_text(scan_result, encoding="utf-8")
        (work / "comment.js").write_text(script, encoding="utf-8")
        (work / "harness.js").write_text(HARNESS, encoding="utf-8")
        run = subprocess.run(
            ["node", str(work / "harness.js"), str(work / "comment.js")],
            cwd=work, capture_output=True, text=True, timeout=60,
        )
    if run.returncode != 0:
        raise AssertionError(f"comment script failed:\n{run.stderr}")
    bodies = json.loads(run.stdout)
    if len(bodies) != 1:
        raise AssertionError(f"expected one comment, got {len(bodies)}")
    return bodies[0]


@unittest.skipUnless(shutil.which("node"), "node is not on PATH")
class DomainTable(unittest.TestCase):
    def setUp(self):
        self.body = comment_body(json.dumps(SCAN))

    def test_one_row_per_domain_with_passed_total_and_percentage(self):
        for row in [
            "| Trust Hierarchy | 3/7 (43%) | Needs work |",
            "| Capability Boundaries | 5/10 (50%) | Partial |",
            "| Harm Avoidance | 4/4 (100%) | Pass |",
        ]:
            self.assertIn(row, self.body)

    def test_no_row_reads_a_missing_field(self):
        self.assertNotIn("undefined", self.body)
        self.assertNotIn("NaN", self.body)

    def test_score_line_is_kept(self):
        self.assertIn("**Score:** 67/100 (Grade: C)", self.body)


@unittest.skipUnless(shutil.which("node"), "node is not on PATH")
class NoDomains(unittest.TestCase):
    def test_output_that_is_not_scanner_json_posts_the_comment_without_a_table(self):
        body = comment_body("error: unknown option '--format'\n")
        self.assertIn("## Agent Governance Scan", body)
        self.assertNotIn("| Domain |", body)

    def test_domains_that_are_not_an_array_give_no_table(self):
        body = comment_body(json.dumps({"domains": {"Trust Hierarchy": {"found": 2, "total": 3}}}))
        self.assertNotIn("| Domain |", body)
        self.assertNotIn("undefined", body)


if __name__ == "__main__":
    unittest.main()
