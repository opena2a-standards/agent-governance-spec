#!/usr/bin/env python3
"""Tests for the command blocks in README.md, its statement of scope and its domain table (with the
docs pages that took its reference text), the scan-soul JSON sample and the minimum scores in
integrations/README.md, the conformance badge URLs in docs/ci.md, integrations/README.md and
conformance.md, the score thresholds those files and the README pages name, the list of example
files in examples/README.md, and the scripts the repository structure in CONTRIBUTING.md lists.

Run from anywhere:  python3 scripts/test_readme.py

Standard library only. The tests read README.md, docs/overview.md, docs/related-work.md,
docs/ci.md, CONTRIBUTING.md, integrations/README.md, conformance.md, specification.md,
templates/tool-using.md, the files under examples/ and the names of the scripts under scripts/,
and write nothing.
"""

import fnmatch
import json
import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

README = Path(__file__).resolve().parent.parent / "README.md"
# The docs pages that took the README's reference text; a test of the README's prose reads them with it.
OVERVIEW = README.parent / "docs" / "overview.md"
RELATED_WORK = README.parent / "docs" / "related-work.md"
CI_DOC = README.parent / "docs" / "ci.md"
README_PAGES = (README, OVERVIEW, RELATED_WORK, CI_DOC)
# The repository structure block moved from README.md to CONTRIBUTING.md.
CONTRIBUTING = README.parent / "CONTRIBUTING.md"
INTEGRATIONS = README.parent / "integrations" / "README.md"
CONFORMANCE_DOC = README.parent / "conformance.md"
BADGE_DOCS = (CI_DOC, INTEGRATIONS, CONFORMANCE_DOC)
SCORE_DOCS = README_PAGES + (INTEGRATIONS, CONFORMANCE_DOC)
BADGE_URL = re.compile(r"https://img\.shields\.io/badge/([^)\s`?]+)")
LEVELS = ("Essential", "Standard", "Hardened")
# A score with a conformance level as its label: "40 (Essential)", "`--fail-below 40` (Essential)".
SCORE_LEVEL_LABEL = re.compile(r"(\d+)`?\s*\((" + "|".join(LEVELS) + r")\)")
SPECIFICATION = README.parent / "specification.md"
RUNTIME_EXCLUDED = "- **Runtime enforcement**: That is the responsibility of runtime platforms"
RUNTIME_CLAIM = re.compile(
    r"\b(provides?|performs?|offers?|delivers?|adds?) runtime enforcement\b|\benforces? .{0,40}\bat runtime\b",
    re.IGNORECASE,
)
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
JSON_FENCE = re.compile(r"^```json\n(.*?)^```", re.MULTILINE | re.DOTALL)
TABLE_KEY = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
SPEC_VERSION = re.compile(r"^\*\*Version\*\*:\s*(\S+)", re.MULTILINE)
SPEC_STATUS = re.compile(r"^\*\*Status\*\*:\s*(\S+)", re.MULTILINE)
SPEC_ENTRY = re.compile(r"^specification\.md\s+(.*)$")
# A version claim such as "v1.0", "1.0.0" or "1.0.0-draft".
VERSION_CLAIM = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?(?:-[0-9A-Za-z]+)?")
COPY_TEMPLATE = re.compile(r"^cp templates/\S+\.md SOUL\.md$")
EDIT_STEP = "# Edit to match your agent's actual constraints"
HARDEN_SOUL = re.compile(r"\bharden-soul\b")
# harden-soul asks no questions: it appends template sections for missing
# domains, so no description of it may promise an interactive mode. The words
# are the ones for that mode. "prompt" and "question" alone are not among
# them, because they also name what a section is about ("prompt injection");
# "prompt" counts only as what the command does to the reader.
PROMPT_CLAIM = re.compile(
    r"\b(guided|interactive(ly)?|wizard|asks?|asking|prompt(s|ed|ing)? (you|the user))\b", re.IGNORECASE
)

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

# The template the scan-soul sample in integrations/README.md is a run of, copied without edits.
TEMPLATE = README.parent / "templates" / "tool-using.md"
# A minimum score the guide sets: a `gh variable set` command or a GitLab `variables:` entry.
GUIDE_MINIMUM = re.compile(r"\bMIN_GOVERNANCE_SCORE(?: --body |:\s*\"?)(\d+)")

# The tier columns of the applicability matrix in specification.md section 3.5, in order.
TIER_COLUMNS = ("BASIC", "TOOL-USING", "AGENTIC", "MULTI-AGENT")
MATRIX_HEADER = "| Control ID | " + " | ".join(TIER_COLUMNS) + " |"
REVERSIBILITY_CONTROL = "SOUL-AS-004"
REVERSIBILITY = re.compile(r"\breversib", re.IGNORECASE)

SCRIPTS = README.parent / "scripts"
EXAMPLES = README.parent / "examples"
EXAMPLES_README = EXAMPLES / "README.md"
EXAMPLE_ROW = re.compile(r"^\| \[`([^`]+)`\]\(([^)]+)\) \| [^|]+ \| ([A-Z-]+) \|$", re.MULTILINE)
DECLARED_TIER = re.compile(r"\b(" + "|".join(TIER_COLUMNS) + r") tier\b")
BLOCKQUOTE = re.compile(r"^> (.+)$", re.MULTILINE)


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


def harden_soul_descriptions(text):
    """Each line that describes harden-soul.

    In a command block that is the comment above a harden-soul command;
    outside command blocks it is any line that names harden-soul.
    """
    found = []
    for block in command_blocks(text):
        for i, line in enumerate(block):
            if HARDEN_SOUL.search(line) and not line.startswith("#"):
                comment = next((block[j] for j in range(i - 1, -1, -1) if block[j].startswith("#")), None)
                if comment is not None:
                    found.append(comment)
    prose = FENCE.sub("", text)
    found.extend(line.strip() for line in prose.splitlines() if HARDEN_SOUL.search(line))
    return found


def guide_minimums(text):
    """Each MIN_GOVERNANCE_SCORE value that a command or YAML block of text sets."""
    return [int(value) for body in FENCE.findall(text) for value in GUIDE_MINIMUM.findall(body)]


def matrix_tiers(spec, control):
    """The tiers the section 3.5 matrix of spec marks Yes for control."""
    row = re.search(r"^\| " + re.escape(control) + r" \|((?: (?:Yes|--) \|){4})$", spec, re.MULTILINE)
    if MATRIX_HEADER not in spec or row is None:
        return None
    cells = [cell.strip() for cell in row.group(1).strip("|").split("|")]
    return [tier for tier, cell in zip(TIER_COLUMNS, cells) if cell == "Yes"]


def untiered_reversibility(text):
    """Each line of text that names reversibility without naming MULTI-AGENT, the one tier it applies to."""
    return [line for line in text.splitlines() if REVERSIBILITY.search(line) and "MULTI-AGENT" not in line]


def example_rows(text):
    """Each (file name, link target, tier) row of the example table in text."""
    return EXAMPLE_ROW.findall(text)


def declared_tiers(text):
    """The tiers a governance file says its agent is, as "the BASIC tier" or "an AGENTIC tier agent"."""
    return sorted(set(DECLARED_TIER.findall(text)))


def specification_entries(text):
    """The description of specification.md in each repository structure block of text."""
    return [m.group(1) for block in command_blocks(text) for line in block if (m := SPEC_ENTRY.match(line))]


def script_entries(text):
    """The name or pattern of each entry listed under scripts/ in the repository structure blocks of text."""
    names = []
    for body in FENCE.findall(text):
        lines = body.splitlines()
        for i, line in enumerate(lines):
            if line.strip() != "scripts/":
                continue
            indent = len(line) - len(line.lstrip())
            for entry in lines[i + 1:]:
                if not entry.strip() or len(entry) - len(entry.lstrip()) <= indent:
                    break
                names.append(entry.split()[0])
    return names


def unlisted_scripts(files, entries):
    """The file names that no entry names or matches as a pattern."""
    return [name for name in files if not any(fnmatch.fnmatchcase(name, entry) for entry in entries)]


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
        for path in SCORE_DOCS:
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


class RuntimeEnforcementScope(unittest.TestCase):
    """specification.md section 1.2 places runtime enforcement out of scope; README.md must agree."""

    def test_specification_excludes_runtime_enforcement(self):
        self.assertIn(RUNTIME_EXCLUDED, SPECIFICATION.read_text(encoding="utf-8"))

    def test_readme_does_not_claim_runtime_enforcement(self):
        for path in README_PAGES:
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertEqual([m.group(0) for m in RUNTIME_CLAIM.finditer(text)], [])

    def test_a_runtime_enforcement_claim_is_reported(self):
        claims = (
            "OASB-2 also provides runtime enforcement through automated scanning.",
            "The scanner enforces the governance file at runtime.",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertRegex(claim, RUNTIME_CLAIM)


class HardenSoulDescriptions(unittest.TestCase):
    def setUp(self):
        self.lines = [line for path in README_PAGES for line in harden_soul_descriptions(path.read_text(encoding="utf-8"))]

    def test_readme_describes_harden_soul(self):
        self.assertGreaterEqual(len(self.lines), 3)

    def test_no_description_promises_prompts(self):
        for line in self.lines:
            with self.subTest(line=line):
                self.assertIsNone(PROMPT_CLAIM.search(line))

    def test_description_that_promises_prompts_is_reported(self):
        text = (
            "```bash\n# Generate a governance file interactively\nnpx hackmyagent harden-soul\n```\n"
            "1. `npx hackmyagent harden-soul` asks guided questions\n"
        )
        lines = harden_soul_descriptions(text)
        self.assertEqual(len(lines), 2)
        for line in lines:
            with self.subTest(line=line):
                self.assertIsNotNone(PROMPT_CLAIM.search(line))

    def test_each_wording_of_an_interactive_mode_is_reported(self):
        claims = (
            "`harden-soul` walks through guided prompts",
            "`harden-soul` is interactive",
            "`harden-soul` runs a wizard",
            "`harden-soul` asks which domains to add",
            "`harden-soul` prompts you for each missing domain",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertIsNotNone(PROMPT_CLAIM.search(claim))

    def test_description_of_the_generated_content_is_not_reported(self):
        # "prompt" and "question" also name what a section is about.
        descriptions = (
            "`harden-soul` adds a section on prompt injection",
            "`harden-soul` appends the system prompt boundaries the file lacks",
            "`harden-soul` leaves open questions about scope to the author",
        )
        for description in descriptions:
            with self.subTest(description=description):
                self.assertEqual(harden_soul_descriptions(description + "\n"), [description])
                self.assertIsNone(PROMPT_CLAIM.search(description))


class GuideMinimumScore(unittest.TestCase):
    """The guide's sample is the scan of templates/tool-using.md as copied, so the minimum the
    guide tells a reader to set must not fail the job on that file."""

    def setUp(self):
        self.text = INTEGRATIONS.read_text(encoding="utf-8")
        self.sample = scan_sample(self.text)

    def test_guide_sets_a_minimum_for_github_and_for_gitlab(self):
        self.assertEqual(len(guide_minimums(self.text)), 2)

    def test_sample_is_the_scan_of_the_template(self):
        self.assertIn("`templates/tool-using.md`, copied to `SOUL.md` without edits", self.text)
        size = len(TEMPLATE.read_bytes().replace(b"\r\n", b"\n"))
        self.assertEqual(self.sample["fileSize"], size, "scan the template again and update the sample")

    def test_no_minimum_is_above_the_score_of_the_template(self):
        for minimum in guide_minimums(self.text):
            with self.subTest(minimum=minimum):
                self.assertLessEqual(minimum, self.sample["score"])

    def test_both_ways_of_setting_the_minimum_are_read(self):
        text = (
            "```bash\ngh variable set MIN_GOVERNANCE_SCORE --body 60\n```\n"
            "```yaml\nvariables:\n  MIN_GOVERNANCE_SCORE: \"75\"\n```\n"
            "Set `MIN_GOVERNANCE_SCORE` to 90 later.\n"
        )
        self.assertEqual(guide_minimums(text), [60, 75])


class ReversibilityTier(unittest.TestCase):
    """SOUL-AS-004 (Reversibility Preference) applies to MULTI-AGENT only, so a README line that
    lists reversibility among what a domain governs names the tier."""

    def test_specification_marks_the_control_for_multi_agent_only(self):
        spec = SPECIFICATION.read_text(encoding="utf-8")
        self.assertEqual(matrix_tiers(spec, REVERSIBILITY_CONTROL), ["MULTI-AGENT"])

    def test_readme_names_the_tier_where_it_names_reversibility(self):
        for path in README_PAGES:
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                self.assertEqual(untiered_reversibility(path.read_text(encoding="utf-8")), [])

    def test_line_without_the_tier_is_reported(self):
        line = "| Agentic Safety | 16 | 10 | Iteration limits, budget caps, timeouts, reversibility |"
        self.assertEqual(untiered_reversibility(line + "\n"), [line])

    def test_control_marked_for_two_tiers_is_read_as_two(self):
        spec = MATRIX_HEADER + "\n| SOUL-AS-004 | -- | -- | Yes | Yes |\n"
        self.assertEqual(matrix_tiers(spec, REVERSIBILITY_CONTROL), ["AGENTIC", "MULTI-AGENT"])


class ExamplesReadme(unittest.TestCase):
    """examples/README.md lists each example file with the tier the file declares, and says that
    a scanner reads the files as governance files."""

    def setUp(self):
        self.assertTrue(EXAMPLES_README.is_file(), "examples/README.md is missing")
        self.text = EXAMPLES_README.read_text(encoding="utf-8")
        self.rows = example_rows(self.text)

    def test_every_example_file_has_a_row(self):
        files = sorted(path.name for path in EXAMPLES.glob("*.md") if path != EXAMPLES_README)
        self.assertGreaterEqual(len(files), 3)
        self.assertEqual(sorted(name for name, _, _ in self.rows), files)
        for name, target, _ in self.rows:
            with self.subTest(file=name):
                self.assertEqual(target, name)

    def test_each_row_gives_the_tier_the_file_declares(self):
        for name, _, tier in self.rows:
            with self.subTest(file=name):
                declared = declared_tiers((EXAMPLES / name).read_text(encoding="utf-8"))
                self.assertEqual(declared, [tier])

    def test_readme_says_a_scanner_reads_the_examples(self):
        self.assertIn("scanned and scored on purpose", self.text)

    def test_the_quoted_line_is_a_denied_action_of_the_coding_agent_example(self):
        quotes = BLOCKQUOTE.findall(self.text)
        self.assertEqual(len(quotes), 1)
        source = (EXAMPLES / "coding-agent-soul.md").read_text(encoding="utf-8")
        denied = source.split("### Denied Actions", 1)[1].split("\n#", 1)[0]
        self.assertIn("- " + quotes[0], denied.splitlines())


class SpecificationEntry(unittest.TestCase):
    """The repository structure entry for specification.md states the version and status the file states."""

    def setUp(self):
        spec = SPECIFICATION.read_text(encoding="utf-8")
        self.version = SPEC_VERSION.search(spec).group(1)
        self.status = SPEC_STATUS.search(spec).group(1)
        self.entries = specification_entries(CONTRIBUTING.read_text(encoding="utf-8"))

    def test_repository_structure_lists_specification_once(self):
        self.assertEqual(1, len(self.entries))

    def test_entry_names_the_specification_version_and_status(self):
        for entry in self.entries:
            with self.subTest(entry=entry):
                self.assertEqual([self.version], VERSION_CLAIM.findall(entry))
                self.assertIn(self.status, entry)

    def test_entry_with_a_stale_version_is_reported(self):
        entry, = specification_entries("```\nagent-governance-spec/\n  specification.md    Full formal specification (v1.0)\n```\n")
        self.assertNotEqual([self.version], VERSION_CLAIM.findall(entry))
        self.assertNotIn(self.status, entry)


class ScriptsEntries(unittest.TestCase):
    """The repository structure lists each script under scripts/, by name or by a pattern such as test_*.py, and
    lists nothing that matches no script."""

    def setUp(self):
        self.entries = script_entries(CONTRIBUTING.read_text(encoding="utf-8"))
        self.files = sorted(path.name for path in SCRIPTS.glob("*.py"))

    def test_every_script_is_listed(self):
        self.assertGreaterEqual(len(self.files), 3)
        self.assertEqual([], unlisted_scripts(self.files, self.entries))

    def test_every_entry_matches_a_script(self):
        self.assertGreaterEqual(len(self.entries), 1)
        stale = [entry for entry in self.entries if not any(fnmatch.fnmatchcase(name, entry) for name in self.files)]
        self.assertEqual([], stale)

    def test_a_test_file_named_by_no_entry_is_reported(self):
        entries = script_entries("```\nagent-governance-spec/\n  scripts/\n    check_crosswalks.py  Validates\n"
                                 "    test_readme.py            Tests\n  domains/\n```\n")
        self.assertEqual(["check_crosswalks.py", "test_readme.py"], entries)
        files = ["check_crosswalks.py", "test_readme.py", "test_scoring.py"]
        self.assertEqual(["test_scoring.py"], unlisted_scripts(files, entries))
        self.assertEqual([], unlisted_scripts(files, ["check_crosswalks.py", "test_*.py"]))


if __name__ == "__main__":
    unittest.main()
