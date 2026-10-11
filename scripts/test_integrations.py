#!/usr/bin/env python3
"""Tests for the minimum-score check in integrations/github-action.yml.

Run from anywhere:  python3 scripts/test_integrations.py

Standard library only. The workflow is read as text, not parsed as YAML, and
the tests write nothing. The "Check minimum score" script is run with bash
(or sh when bash is missing) to show that it fails the job below the minimum.
"""

import re
import shutil
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / "integrations" / "github-action.yml"
GUIDE = ROOT / "integrations" / "README.md"
CHECK_STEP = "Check minimum score"
MIN_SCORE_EXPRESSION = "${{ vars.MIN_GOVERNANCE_SCORE || '0' }}"

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


def run_check(script, score, minimum):
    """The exit status of script run with SCORE and MIN_SCORE set, as the step's env: sets them."""
    shell = shutil.which("bash") or shutil.which("sh")
    result = subprocess.run(
        [shell, "-e", "-c", script],
        env={"PATH": "/usr/bin:/bin", "SCORE": score, "MIN_SCORE": minimum},
        capture_output=True,
        text=True,
    )
    return result.returncode


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

    def test_guide_names_the_variable_the_workflow_reads(self):
        guide = GUIDE.read_text(encoding="utf-8")
        (variable,) = VARS_REF.findall(step_env(self.step)["MIN_SCORE"])
        self.assertIn(f"`{variable}`", guide)
        self.assertIn(variable, self.text.split("\nname:", 1)[0])
        self.assertNotIn("fail-below` input", guide)


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
