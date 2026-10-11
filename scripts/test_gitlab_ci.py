#!/usr/bin/env python3
"""Tests for the governance-scan job in integrations/gitlab-ci.yml.

Run from anywhere:  python3 scripts/test_gitlab_ci.py

Standard library only. The tests read the job and integrations/README.md, run
the job's script with bash -eo pipefail, as the GitLab runner does, against a
stand-in for `npx hackmyagent@latest scan-soul` that accepts the scanner's
options and rejects any other option, and check what the job prints, the exit
status, and the files its artifacts name. They write only to a temporary
directory.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
JOB = ROOT / "integrations" / "gitlab-ci.yml"
GUIDE = ROOT / "integrations" / "README.md"
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
DOTENV_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# The governance file names `hackmyagent scan-soul --help` (hackmyagent 0.33.2)
# says the scanner searches, in its priority order.
SCANNED_NAMES = [
    "SOUL.md",
    "system-prompt.md",
    "SYSTEM_PROMPT.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    "CLAUDE.md",
    ".clinerules",
    "instructions.md",
    "constitution.md",
    "agent-config.yaml",
]

# Stands in for `npx hackmyagent@latest scan-soul`. The option lists are the
# ones `hackmyagent scan-soul --help` (hackmyagent 0.33.2) prints. Like the
# scanner, the stand-in writes an unknown option error to stderr and exits 1,
# and with --json it prints the scan result as JSON on stdout.
SCANNER = """#!@PYTHON@
import json
import os
import sys

FLAGS = ("--json", "-v", "--verbose", "--deep", "--static-only", "--publish",
         "--contribute", "--no-contribute", "--ci", "--explain", "-h", "--help")
VALUE_OPTIONS = ("--tier", "--profile", "--fail-below", "--registry-url")

args = sys.argv[1:]
if args[:2] != ["hackmyagent@latest", "scan-soul"]:
    sys.exit("stand-in: unexpected command: " + " ".join(args))
args = args[2:]
as_json = False
while args:
    option = args.pop(0)
    if option.split("=", 1)[0] in VALUE_OPTIONS:
        if "=" not in option and args:
            args.pop(0)
    elif option in FLAGS:
        as_json = as_json or option == "--json"
    elif option.startswith("-"):
        sys.stderr.write("error: unknown option '" + option + "'\\n(run with --help for usage)\\n")
        sys.exit(1)
score = int(os.environ["SCAN_SCORE"])
grade = os.environ["SCAN_GRADE"]
if as_json:
    print(json.dumps(dict(file="SOUL.md", score=score, grade=grade), indent=2))
else:
    print("SOUL.md: " + str(score) + "/100 (" + grade + ")")
sys.exit(int(os.environ["SCAN_EXIT"]))
"""


def nested(lines, key):
    """The lines under the first `key:` or `- key:` line, up to the next line at its indent or less."""
    for i, line in enumerate(lines):
        if line.strip() in (f"{key}:", f"- {key}:"):
            indent = len(line) - len(line.lstrip())
            body = []
            for following in lines[i + 1:]:
                if following.strip() and len(following) - len(following.lstrip()) <= indent:
                    break
                body.append(following)
            return body
    return []


def items(body):
    """The entries of a block sequence; a `- |` entry is its literal block, dedented."""
    content = [line for line in body if line.strip()]
    if not content:
        return []
    indent = min(len(line) - len(line.lstrip()) for line in content)
    entries = []
    literal = None
    for line in body:
        stripped = line.strip()
        if line.strip() and len(line) - len(line.lstrip()) == indent and stripped.startswith("- "):
            literal = None
            value = stripped[2:].strip()
            if value == "|":
                literal = []
                entries.append(literal)
            else:
                entries.append(value)
        elif literal is not None:
            literal.append(line)
    result = []
    for entry in entries:
        if isinstance(entry, list):
            margin = min(len(line) - len(line.lstrip()) for line in entry if line.strip())
            entry = "\n".join(line[margin:] for line in entry).strip("\n")
        result.append(entry)
    return result


def job_lines():
    return JOB.read_text(encoding="utf-8").splitlines()


def dotenv_reports(lines):
    """The files the job's artifacts:reports:dotenv names."""
    reports = nested(nested(lines, "artifacts"), "reports")
    for line in reports:
        key, _, value = line.strip().partition(":")
        if key == "dotenv":
            value = value.strip()
            return [value] if value else items(nested(reports, "dotenv"))
    return []


def run_job(score, grade="C", min_score=None, scanner_exit=0):
    """Run the job's script and return the completed process and the content of each dotenv report file."""
    lines = job_lines()
    script = "\n".join(items(nested(lines, "script"))) + "\n"
    with tempfile.TemporaryDirectory() as work:
        bin_dir = Path(work) / "bin"
        bin_dir.mkdir()
        scanner = bin_dir / "npx"
        scanner.write_text(SCANNER.replace("@PYTHON@", sys.executable), encoding="utf-8")
        scanner.chmod(0o755)
        project = Path(work) / "project"
        project.mkdir()
        env = {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
            "SCAN_SCORE": str(score),
            "SCAN_GRADE": grade,
            "SCAN_EXIT": str(scanner_exit),
        }
        if min_score is not None:
            env["MIN_GOVERNANCE_SCORE"] = str(min_score)
        result = subprocess.run(
            ["bash", "-eo", "pipefail", "-c", script],
            cwd=project, env=env, capture_output=True, text=True,
        )
        reports = {}
        for name in dotenv_reports(lines):
            path = project / name
            reports[name] = path.read_text(encoding="utf-8") if path.is_file() else None
    return result, reports


def guide_minimum():
    """The MIN_GOVERNANCE_SCORE value the integrations guide tells the reader to set."""
    for block in FENCE.findall(GUIDE.read_text(encoding="utf-8")):
        found = re.search(r"MIN_GOVERNANCE_SCORE:\s*\"?(\d+)\"?", block)
        if found:
            return int(found.group(1))
    raise AssertionError("integrations/README.md sets no MIN_GOVERNANCE_SCORE")


@unittest.skipUnless(shutil.which("bash") and shutil.which("node"), "bash or node is not installed")
class GovernanceScanJob(unittest.TestCase):
    def test_job_prints_the_score_and_grade_of_the_scan(self):
        result, _ = run_job(score=72, grade="C")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Governance Score: 72/100 (Grade: C)", result.stdout)

    def test_scanner_exit_1_does_not_end_the_job_before_the_score(self):
        result, _ = run_job(score=72, grade="C", scanner_exit=1)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Governance Score: 72/100 (Grade: C)", result.stdout)

    def test_score_below_minimum_fails_the_job(self):
        result, _ = run_job(score=50, min_score=60)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Score 50 is below minimum 60", result.stdout)

    def test_score_at_or_above_minimum_passes(self):
        for score in (60, 75):
            with self.subTest(score=score):
                result, _ = run_job(score=score, min_score=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_guide_minimum_is_the_variable_the_job_reads(self):
        minimum = guide_minimum()
        result, _ = run_job(score=minimum - 1, min_score=minimum)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        result, _ = run_job(score=minimum, min_score=minimum)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dotenv_reports_hold_key_value_lines(self):
        _, reports = run_job(score=72)
        for name, text in reports.items():
            with self.subTest(report=name):
                self.assertIsNotNone(text, f"{name} is not written by the job")
                lines = [line for line in text.splitlines() if line.strip()]
                self.assertTrue(lines, f"{name} sets no variable")
                for line in lines:
                    self.assertRegex(line, DOTENV_LINE, f"{name} is not KEY=VALUE lines")

    def test_scan_result_is_kept_as_an_artifact(self):
        paths = items(nested(nested(job_lines(), "artifacts"), "paths"))
        self.assertIn("scan-result.json", paths)


class TriggerList(unittest.TestCase):
    def test_changes_list_names_every_file_the_scanner_searches(self):
        self.assertEqual(sorted(items(nested(job_lines(), "changes"))), sorted(SCANNED_NAMES))


if __name__ == "__main__":
    unittest.main()
