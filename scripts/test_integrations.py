#!/usr/bin/env python3
"""Tests for the scan and minimum-score steps in integrations/github-action.yml.

Run from anywhere:  python3 scripts/test_integrations.py

Standard library only. The workflow is read as text, not parsed as YAML. The
"Check minimum score" script is run with bash (or sh when bash is missing) to
show that it fails the job below the minimum. The "Run governance scan" script
is run with bash and jq, with a stand-in for npx that prints a recorded scanner
result; those tests write only to a temporary directory and are skipped
without bash or jq.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "integrations" / "github-action.yml"
GUIDE = ROOT / "integrations" / "README.md"
SCAN_STEP = "Run governance scan"
CHECK_STEP = "Check minimum score"
MIN_SCORE_EXPRESSION = "${{ vars.MIN_GOVERNANCE_SCORE || '0' }}"

# The `gate.reason` of each run that measured nothing (exit code 2), with the
# words the check prints for it.
NOT_MEASURED = {
    "no-governance-file": "no governance file was found",
    "governance-file-unreadable": "the governance file could not be read",
    "governance-file-empty": "the governance file is empty",
}

# What `scan-soul --json` prints, trimmed to the keys the scan step reads,
# for a scored file and for a run that found no governance file.
SCORED = {"file": "SOUL.md", "score": 49, "grade": "C", "conformance": "essential",
          "gate": {"failed": False, "reason": None, "exitCode": 0}}
NO_FILE = {"file": None, "score": None, "conformance": None,
           "gate": {"failed": True, "reason": "no-governance-file", "exitCode": 2}}

# Stands in for npx: prints the recorded result and exits with its gate exit code.
FAKE_NPX = '#!/bin/sh\ncat "$SCAN_FIXTURE"\nexit "$SCAN_EXIT"\n'

EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}")
INPUT_REF = re.compile(r"\binputs\.([A-Za-z0-9_-]+)")
VARS_REF = re.compile(r"\bvars\.([A-Za-z0-9_]+)")
KEY = re.compile(r"^(\s*)([A-Za-z0-9_-]+):")


def indent(line):
    return len(line) - len(line.lstrip(" "))


def block(lines, start):
    """The lines after lines[start] that are blank or indented deeper than it."""
    depth = indent(lines[start])
    end = start + 1
    while end < len(lines) and (not lines[end].strip() or indent(lines[end]) > depth):
        end += 1
    return lines[start + 1:end]


def input_refs(text):
    """Each input name that a ${{ }} expression in text reads."""
    return sorted({name for expr in EXPRESSION.findall(text) for name in INPUT_REF.findall(expr)})


def declared_inputs(text):
    """Each input declared under workflow_call or workflow_dispatch in the on: block."""
    lines = text.splitlines()
    on = next((i for i, line in enumerate(lines) if re.match(r"^['\"]?on['\"]?:", line)), None)
    if on is None:
        return set()
    names = set()
    trigger_lines = block(lines, on)
    for i, line in enumerate(trigger_lines):
        match = KEY.match(line)
        if not match or match.group(2) not in ("workflow_call", "workflow_dispatch"):
            continue
        body = block(trigger_lines, i)
        for j, inner in enumerate(body):
            if KEY.match(inner) and KEY.match(inner).group(2) == "inputs":
                children = [l for l in block(body, j) if l.strip()]
                if children:
                    depth = indent(children[0])
                    names.update(KEY.match(l).group(2) for l in children if indent(l) == depth and KEY.match(l))
    return names


def step(text, name):
    """The lines of the step whose name is name, the "- name:" line first."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == f"- name: {name}":
            return [line] + block(lines, i)
    return None


def step_env(lines):
    """The env: mapping of a step, values as written."""
    for i, line in enumerate(lines):
        if line.strip() == "env:":
            return {
                key.strip(): value.strip()
                for key, _, value in (l.partition(":") for l in block(lines, i) if l.strip())
            }
    return {}


def run_script(lines):
    """The body of a step's "run: |" block, dedented."""
    for i, line in enumerate(lines):
        if line.strip() == "run: |":
            return textwrap.dedent("\n".join(block(lines, i))) + "\n"
    return None


def check_result(script, score, minimum, reason=""):
    """script run with SCORE, MIN_SCORE and REASON set, as the step's env: sets them."""
    shell = shutil.which("bash") or shutil.which("sh")
    return subprocess.run(
        [shell, "-e", "-c", script],
        env={"PATH": "/usr/bin:/bin", "SCORE": score, "MIN_SCORE": minimum, "REASON": reason},
        capture_output=True,
        text=True,
        timeout=60,
    )


def run_check(script, score, minimum, reason=""):
    """The exit status of the check script."""
    return check_result(script, score, minimum, reason).returncode


def scan_outputs(script, result, exit_code):
    """The step outputs the scan script writes when the scanner prints result and exits with exit_code."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        bin_dir = work / "bin"
        bin_dir.mkdir()
        npx = bin_dir / "npx"
        npx.write_text(FAKE_NPX, encoding="utf-8")
        npx.chmod(0o755)
        (work / "fixture.json").write_text(result, encoding="utf-8")
        output = work / "github-output"
        output.write_text("", encoding="utf-8")
        run = subprocess.run(
            [shutil.which("bash"), "-e", "-c", script],
            cwd=work,
            env={
                "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
                "GITHUB_OUTPUT": str(output),
                "SCAN_FIXTURE": str(work / "fixture.json"),
                "SCAN_EXIT": str(exit_code),
            },
            capture_output=True,
            text=True,
            timeout=60,
        )
        if run.returncode != 0:
            raise AssertionError(f"scan step failed:\n{run.stderr}")
        return dict(line.partition("=")[::2] for line in output.read_text(encoding="utf-8").splitlines())


class MinimumScore(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.step = step(self.text, CHECK_STEP)
        self.assertIsNotNone(self.step, f"no step named {CHECK_STEP!r} in {WORKFLOW.name}")

    def test_every_input_the_workflow_reads_is_declared(self):
        # pull_request and push runs have no inputs context, so an undeclared
        # input is always empty and a threshold read from one never applies.
        declared = declared_inputs(self.text)
        for name in input_refs(self.text):
            with self.subTest(input=name):
                self.assertIn(name, declared)

    def test_minimum_comes_from_the_repository_variable(self):
        self.assertEqual(step_env(self.step).get("MIN_SCORE"), MIN_SCORE_EXPRESSION)

    def test_check_script_reads_values_from_env_only(self):
        script = run_script(self.step)
        self.assertIsNotNone(script)
        self.assertNotIn("${{", script)

    def test_check_fails_below_the_minimum_and_passes_at_or_above_it(self):
        script = run_script(self.step)
        cases = (
            ("59", "60", False),
            ("60", "60", True),
            ("72", "60", True),
            ("0", "0", True),
            ("72", "0", True),
            ("", "60", False),
            ("72", "60%", False),
            ("72", "", False),
        )
        for score, minimum, passes in cases:
            with self.subTest(score=score, minimum=minimum):
                self.assertEqual(run_check(script, score, minimum) == 0, passes)

    def test_check_reads_the_gate_reason_of_the_scan(self):
        self.assertEqual(step_env(self.step).get("REASON"), "${{ steps.scan.outputs.reason }}")

    def test_run_that_measured_nothing_names_the_reason_instead_of_a_score(self):
        script = run_script(self.step)
        for reason, words in NOT_MEASURED.items():
            with self.subTest(reason=reason):
                result = check_result(script, "", "60", reason)
                self.assertEqual(result.returncode, 1)
                self.assertIn(words, result.stdout)
                self.assertIn(reason, result.stdout)
                self.assertNotIn("below minimum", result.stdout)

    def test_run_that_measured_nothing_passes_without_a_minimum(self):
        script = run_script(self.step)
        for reason in NOT_MEASURED:
            with self.subTest(reason=reason):
                result = check_result(script, "", "0", reason)
                self.assertEqual(result.returncode, 0)
                self.assertIn(NOT_MEASURED[reason], result.stdout)

    def test_gate_reason_is_tested_before_the_score(self):
        # A score of 0 next to a not-measured reason is the old `// 0` default, not a measurement.
        result = check_result(run_script(self.step), "0", "60", "governance-file-empty")
        self.assertEqual(result.returncode, 1)
        self.assertIn(NOT_MEASURED["governance-file-empty"], result.stdout)
        self.assertNotIn("below minimum", result.stdout)

    def test_scored_run_with_a_failing_gate_reason_is_still_compared(self):
        script = run_script(self.step)
        self.assertEqual(run_check(script, "72", "60", "critical-control-missing"), 0)
        self.assertEqual(run_check(script, "52", "60", "critical-control-missing"), 1)

    def test_guide_names_the_variable_the_workflow_reads(self):
        guide = GUIDE.read_text(encoding="utf-8")
        (variable,) = VARS_REF.findall(step_env(self.step)["MIN_SCORE"])
        self.assertIn(f"`{variable}`", guide)
        self.assertIn(variable, self.text.split("\nname:", 1)[0])
        self.assertNotIn("fail-below` input", guide)


@unittest.skipUnless(shutil.which("bash") and shutil.which("jq"), "bash or jq is not on PATH")
class ScanStep(unittest.TestCase):
    def setUp(self):
        lines = step(WORKFLOW.read_text(encoding="utf-8"), SCAN_STEP)
        self.assertIsNotNone(lines, f"no step named {SCAN_STEP!r} in {WORKFLOW.name}")
        self.script = run_script(lines)

    def test_scored_run_outputs_its_score(self):
        outputs = scan_outputs(self.script, json.dumps(SCORED), 0)
        self.assertEqual(outputs["score"], "49")
        self.assertEqual(outputs["grade"], "C")
        self.assertEqual(outputs["reason"], "")

    def test_run_that_measured_nothing_outputs_no_score_and_its_reason(self):
        outputs = scan_outputs(self.script, json.dumps(NO_FILE), 2)
        self.assertEqual(outputs["score"], "")
        self.assertEqual(outputs["reason"], "no-governance-file")

    def test_output_that_is_not_json_outputs_no_score(self):
        outputs = scan_outputs(self.script, "error: unknown option '--format'\n", 1)
        self.assertEqual(outputs["score"], "")
        self.assertEqual(outputs["reason"], "")

    def test_scan_and_check_together_name_the_missing_file(self):
        outputs = scan_outputs(self.script, json.dumps(NO_FILE), 2)
        check = run_script(step(WORKFLOW.read_text(encoding="utf-8"), CHECK_STEP))
        result = check_result(check, outputs["score"], "60", outputs["reason"])
        self.assertEqual(result.returncode, 1)
        self.assertIn(NOT_MEASURED["no-governance-file"], result.stdout)
        self.assertNotIn("score 0", result.stdout)


class Helpers(unittest.TestCase):
    def test_undeclared_input_is_reported(self):
        text = "on:\n  push:\njobs:\n  a:\n    steps:\n      - run: echo ${{ inputs.fail-below || '0' }}\n"
        self.assertEqual(input_refs(text), ["fail-below"])
        self.assertEqual(declared_inputs(text), set())

    def test_workflow_call_input_is_declared(self):
        text = (
            "on:\n"
            "  workflow_call:\n"
            "    inputs:\n"
            "      fail-below:\n"
            "        type: number\n"
            "        default: 0\n"
            "jobs: {}\n"
        )
        self.assertEqual(declared_inputs(text), {"fail-below"})


if __name__ == "__main__":
    unittest.main()
