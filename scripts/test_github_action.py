#!/usr/bin/env python3
"""Tests for integrations/github-action.yml: the script that comments on the
pull request, run on JSON in the shape `hackmyagent scan-soul --json` prints.

Run from anywhere:  python3 scripts/test_github_action.py

Standard library only. The tests that run the comment script need node on
PATH and are skipped without it; they write only to a temporary directory.
The tests that read the comment step's text run without node.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ACTION = Path(__file__).resolve().parent.parent / "integrations" / "github-action.yml"
COMMENT_STEP = "Comment on PR"
OUTPUT = re.compile(r"^\$\{\{\s*steps\.scan\.outputs\.(\w+)\s*\}\}$")
OUTPUTS = {"score": "67", "grade": "C", "conformance": "NONE", "file": "SOUL.md", "reason": ""}

# A domain the agent profile leaves out, as the scanner prints it for
# templates/tool-using.md (profile tool-agent).
SKIPPED_DOMAIN = {
    "domain": "Agentic Safety", "domainId": 16, "controls": [],
    "passed": 0, "total": 0, "percentage": 0, "skippedByProfile": True,
}

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

# The login of a comment posted with the default GITHUB_TOKEN.
BOT = "github-actions[bot]"

# Runs the comment script as actions/github-script does, as the body of an
# async function, with stand-ins for the GitHub client and the run context.
# The comments already on the pull request are read from the file the third
# argument names. Like the REST API, listComments returns one page of them,
# 30 when per_page is not given; like octokit, paginate reads each page until
# one is not full. Each create or update call is printed as JSON.
HARNESS = """
const fs = require('fs');
const script = fs.readFileSync(process.argv[2], 'utf8');
const posted = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const calls = [];
const listComments = async ({ per_page = 30, page = 1 }) =>
  ({ data: posted.slice((page - 1) * per_page, page * per_page) });
const paginate = async (method, params) => {
  const all = [];
  for (let page = 1; ; page++) {
    const { data } = await method({ ...params, page });
    all.push(...data);
    if (data.length < (params.per_page || 30)) return all;
  }
};
const github = { paginate, rest: { issues: {
  listComments,
  createComment: async (args) => { calls.push({ action: 'create', body: args.body }); return { data: {} }; },
  updateComment: async (args) => { calls.push({ action: 'update', id: args.comment_id, body: args.body }); return { data: {} }; },
} } };
const context = { repo: { owner: 'owner', repo: 'repo' }, issue: { number: 1 } };
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
new AsyncFunction('require', 'github', 'context', script)(require, github, context)
  .then(() => process.stdout.write(JSON.stringify(calls)))
  .catch((err) => { console.error(err); process.exit(1); });
"""


def indent(line):
    return len(line) - len(line.lstrip())


def block(lines, start):
    """The lines after lines[start] that are blank or indented deeper than it."""
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or indent(lines[end]) > indent(lines[start])):
        end += 1
    return lines[start + 1:end]


def comment_step(text):
    """The lines of the step that posts the comment, the "- name:" line first."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == f"- name: {COMMENT_STEP}")
    return [lines[start]] + block(lines, start)


def comment_script(text):
    """The `script: |` block of the comment step, with its indentation removed as YAML reads it."""
    lines = comment_step(text)
    start = next(i for i, line in enumerate(lines) if line.strip() == "script: |")
    body = block(lines, start)
    first = next(line for line in body if line.strip())
    return "\n".join(line[indent(first):] for line in body).rstrip() + "\n"


def comment_env(text):
    """The env: mapping of the comment step: variable name to the scan output it reads."""
    lines = comment_step(text)
    start = next((i for i, line in enumerate(lines) if line.strip() == "env:"), None)
    if start is None:
        return {}
    names = {}
    for line in block(lines, start):
        if line.strip():
            name, _, value = line.strip().partition(":")
            match = OUTPUT.match(value.strip())
            if not match:
                raise AssertionError(f"env {name} does not read a scan output: {value.strip()}")
            names[name] = match.group(1)
    return names


def comment_calls(scan_result, outputs=OUTPUTS, posted=()):
    """The create and update calls the action makes when scan-result.json holds scan_result, the scan
    step gave outputs, and the pull request already has the comments posted, oldest first."""
    text = ACTION.read_text(encoding="utf-8")
    env = {name: outputs[output] for name, output in comment_env(text).items()}
    env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "scan-result.json").write_text(scan_result, encoding="utf-8")
        (work / "comment.js").write_text(comment_script(text), encoding="utf-8")
        (work / "harness.js").write_text(HARNESS, encoding="utf-8")
        (work / "posted.json").write_text(json.dumps(list(posted)), encoding="utf-8")
        run = subprocess.run(
            ["node", str(work / "harness.js"), str(work / "comment.js"), str(work / "posted.json")],
            cwd=work, env=env, capture_output=True, text=True, timeout=60,
        )
    if run.returncode != 0:
        raise AssertionError(f"comment script failed:\n{run.stderr}")
    calls = json.loads(run.stdout)
    if len(calls) != 1:
        raise AssertionError(f"expected one comment, got {len(calls)}")
    return calls


def comment_body(scan_result, outputs=OUTPUTS):
    """The comment the action posts when scan-result.json holds scan_result and the scan step gave outputs."""
    (call,) = comment_calls(scan_result, outputs)
    return call["body"]


def comment(comment_id, login, body):
    """A pull request comment as listComments returns it, trimmed to the keys the step reads."""
    return {"id": comment_id, "user": {"login": login}, "body": body}


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


@unittest.skipUnless(shutil.which("node"), "node is not on PATH")
class ProfileSkippedDomain(unittest.TestCase):
    def setUp(self):
        self.body = comment_body(json.dumps(dict(SCAN, domains=SCAN["domains"] + [SKIPPED_DOMAIN])))

    def test_domain_the_profile_leaves_out_is_not_applicable(self):
        self.assertIn("| Agentic Safety | Skipped by profile | Not applicable |", self.body)
        self.assertNotIn("0/0", self.body)

    def test_scored_domains_keep_their_rows(self):
        self.assertIn("| Trust Hierarchy | 3/7 (43%) | Needs work |", self.body)


class StepOutputs(unittest.TestCase):
    def test_comment_script_reads_no_expression(self):
        # The values reach the script through env:, so a quote in one cannot end a string literal.
        self.assertNotIn("${{", comment_script(ACTION.read_text(encoding="utf-8")))

    def test_comment_step_passes_each_scan_output_through_env(self):
        self.assertEqual(
            sorted(comment_env(ACTION.read_text(encoding="utf-8")).values()),
            ["conformance", "file", "grade", "reason", "score"],
        )

    @unittest.skipUnless(shutil.which("node"), "node is not on PATH")
    def test_quotes_in_an_output_are_printed_as_written(self):
        body = comment_body(json.dumps(SCAN), dict(OUTPUTS, file="it's \"SOUL\".md"))
        self.assertIn("**File:** `it's \"SOUL\".md`", body)


@unittest.skipUnless(shutil.which("node"), "node is not on PATH")
class ExistingComment(unittest.TestCase):
    # The comment the step posts on a pull request with no comments, as it would be listed later.
    def setUp(self):
        (call,) = comment_calls(json.dumps(SCAN))
        self.assertEqual(call["action"], "create")
        self.own = call["body"]

    def test_own_comment_is_updated(self):
        (call,) = comment_calls(json.dumps(SCAN), posted=[comment(5, BOT, self.own)])
        self.assertEqual((call["action"], call.get("id")), ("update", 5))

    def test_own_comment_after_the_first_page_is_updated(self):
        # The REST API lists 30 comments per page unless asked for more.
        posted = [comment(i, "reviewer", "Looks good.") for i in range(1, 131)] + [comment(131, BOT, self.own)]
        (call,) = comment_calls(json.dumps(SCAN), posted=posted)
        self.assertEqual((call["action"], call.get("id")), ("update", 131))

    def test_comment_by_someone_else_is_not_overwritten(self):
        # A reviewer who names the scan, or quotes the whole comment, keeps their comment.
        for body in ("Re-run the Agent Governance Scan after the edit.", self.own):
            with self.subTest(body=body[:30]):
                (call,) = comment_calls(json.dumps(SCAN), posted=[comment(7, "reviewer", body)])
                self.assertEqual(call["action"], "create")

    def test_bot_comment_without_the_marker_is_not_overwritten(self):
        # Another workflow that posts with the default token, and names the scan.
        (call,) = comment_calls(json.dumps(SCAN), posted=[comment(8, BOT, "## Agent Governance Scan summary")])
        self.assertEqual(call["action"], "create")


@unittest.skipUnless(shutil.which("node"), "node is not on PATH")
class NotMeasured(unittest.TestCase):
    # A run that found no governance file exits 2 with a null score; the scan step outputs it as empty.
    def setUp(self):
        scan = {"file": None, "score": None, "conformance": None,
                "gate": {"failed": True, "reason": "no-governance-file", "exitCode": 2}}
        self.body = comment_body(json.dumps(scan), dict(OUTPUTS, score="", grade="F", reason="no-governance-file"))

    def test_score_line_names_the_gate_reason(self):
        self.assertIn("**Score:** not measured (`no-governance-file`)", self.body)

    def test_no_score_or_grade_is_shown(self):
        self.assertNotIn("/100", self.body)
        self.assertNotIn("Grade:", self.body)


if __name__ == "__main__":
    unittest.main()
