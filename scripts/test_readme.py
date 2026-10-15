#!/usr/bin/env python3
"""Tests for the command blocks in README.md, its statement of scope and its domain table (with the
docs pages that took its reference text), the scan-soul JSON sample and the minimum scores in
integrations/README.md, what those pages say scan-soul exit code 0 means and the controls they say
the Essential level requires, the conformance badge URLs in docs/ci.md, integrations/README.md and
conformance.md, the requirements the level table of conformance.md and section 7 of
specification.md give each level, the score
thresholds those files and the README pages name, the list of example
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
# harden-soul writes to the first governance file it finds in the discovery order of
# specification.md section 2.2 and creates SOUL.md only when it finds none: with CLAUDE.md and no
# SOUL.md it appends to CLAUDE.md. So a sentence that names SOUL.md as the file the command writes
# also says when that holds.
WRITE_VERB = re.compile(
    r"\b(generat(e|es|ed|ing)|creat(e|es|ed|ing)|updat(e|es|ed|ing)|writ(e|es|ten|ing)"
    r"|append(s|ed|ing)?|add(s|ed|ing)?)\b",
    re.IGNORECASE,
)
SOUL_FILE = re.compile(r"\bSOUL\.md\b")
CONDITION = re.compile(r"\b(when|if|unless|only|no|none)\b", re.IGNORECASE)
# A list number such as "1." ends no sentence.
SENTENCE_END = re.compile(r"(?<=[^\s\d][.;:])\s+")
DISCOVERY_SECTION = "### 2.2 File Discovery"
DISCOVERY_LINK = "specification.md#22-file-discovery"
DISCOVERY_ENTRY = re.compile(r"^\d+\. `([^`]+)`$", re.MULTILINE)

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

# What exit code 0 of scan-soul means, as a sentence ("exits 0 when") or as a list item ("- `0`:").
EXIT_0 = re.compile(r"\bexits? `?0`? when\b|^- `0`:")
# The minimum length and heading count of specification.md section 2.3, which Essential requires
# and which hackmyagent 0.33.2 does not check: it exits 0 with `conformance` "essential" for a
# 154-byte SOUL.md with three headings, and for a 119-byte one with none.
MINIMUM_SECTION = "### 2.3 Minimum Viable Governance File"
MINIMUM_LENGTH = re.compile(r"^- \*\*Length\*\*: At least (\d+) characters\b", re.MULTILINE)
MINIMUM_HEADINGS = re.compile(r"^- \*\*Structure\*\*: At least (\d+) distinct section headings\b", re.MULTILINE)
# A requirement of a conformance level given as controls: "when a CRITICAL control is missing",
# "which controls must pass".
CONTROL_REQUIREMENT = re.compile(r"\bCRITICAL controls?\b|\bcontrols must pass\b")
# The `conformance` value of `scan-soul --json`, named as a field or key ("read the level from the
# `conformance` field"). hackmyagent 0.33.2 reports "essential" there for a 79-byte SOUL.md with no
# headings, below the minimum of specification.md section 2.3 that every level requires.
CONFORMANCE_FIELD = re.compile(r"`conformance` (?:field|key|value)\b")
# The level table of conformance.md: one row per level, its Requirements cell second.
LEVEL_TABLE_HEADER = "| Level | Requirements | Typical Use Case |"
LEVEL_ROW = re.compile(r"^\| \*\*(" + "|".join(LEVELS) + r")\*\* \| ([^|\n]+) \|", re.MULTILINE)
# The Requirements list of a level subsection of specification.md section 7: one item per line.
SPEC_LEVEL = re.compile(
    r"^### 7\.\d+ (" + "|".join(LEVELS) + r")\n\n\*\*Requirements\*\*:\n((?:- [^\n]*\n)+)", re.MULTILINE
)


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


def unconditional_soul_targets(lines):
    """Each sentence of lines that names SOUL.md as the file harden-soul writes without saying when."""
    return [
        sentence
        for line in lines
        for sentence in SENTENCE_END.split(line)
        if WRITE_VERB.search(sentence) and SOUL_FILE.search(sentence) and not CONDITION.search(sentence)
    ]


def discovery_order(spec):
    """The file names section 2.2 of spec lists, in order, or [] when spec has no such section."""
    if DISCOVERY_SECTION not in spec:
        return []
    section = spec.split(DISCOVERY_SECTION, 1)[1].split("\n#", 1)[0]
    return DISCOVERY_ENTRY.findall(section)


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


def minimum_viable(spec):
    """The (characters, headings) minimum of specification.md section 2.3 in spec, or None."""
    start = spec.find(MINIMUM_SECTION)
    if start < 0:
        return None
    body = re.split(r"^#", spec[start + len(MINIMUM_SECTION):], maxsplit=1, flags=re.MULTILINE)[0]
    length, headings = MINIMUM_LENGTH.search(body), MINIMUM_HEADINGS.search(body)
    if length is None or headings is None:
        return None
    return int(length.group(1)), int(headings.group(1))


def exit_0_statements(text):
    """Each prose line of text, outside code blocks, that says what scan-soul exit code 0 means."""
    return [line.strip() for line in FENCE.sub("", text).splitlines() if EXIT_0.search(line.strip())]


def unqualified_exit_0(text, minimum):
    """Each exit 0 statement of text that names the Essential level without naming the minimum
    length and heading count of specification.md section 2.3, which the scanner does not check."""
    characters, headings = minimum
    named = (f"{characters} characters", f"{headings} section headings", "section 2.3")
    return [
        line for line in exit_0_statements(text)
        if "Essential" in line and not all(part in line for part in named)
    ]


def essential_controls_without_minimum(text, minimum):
    """Each prose line of text, outside code blocks, that names the Essential level and gives a
    level's requirement as controls (a CRITICAL control, or which controls must pass) without
    naming the minimum length and heading count of specification.md section 2.3, which Essential
    also requires and the scanner does not check."""
    characters, headings = minimum
    named = (f"{characters} characters", f"{headings} section headings", "section 2.3")
    return [
        line.strip() for line in FENCE.sub("", text).splitlines()
        if "Essential" in line and CONTROL_REQUIREMENT.search(line)
        and not all(part in line for part in named)
    ]


def conformance_field_without_minimum(text, minimum):
    """Each prose line of text, outside code blocks, that names the `conformance` field of the
    scanner's JSON output without naming the minimum length and heading count of specification.md
    section 2.3, which every level requires and the scanner does not check."""
    characters, headings = minimum
    named = (f"{characters} characters", f"{headings} section headings", "section 2.3")
    return [
        line.strip() for line in FENCE.sub("", text).splitlines()
        if CONFORMANCE_FIELD.search(line) and not all(part in line for part in named)
    ]


def level_requirements(text):
    """The Requirements cell of each row of the level table in text, by level."""
    start = text.find(LEVEL_TABLE_HEADER)
    if start < 0:
        return {}
    table = re.split(r"\n(?!\|)", text[start:], maxsplit=1)[0]
    return {level: cell.strip() for level, cell in LEVEL_ROW.findall(table)}


def specification_level_requirements(spec):
    """The items of the Requirements list of each level subsection of section 7 in spec, joined
    by spaces, by level."""
    return {
        level: " ".join(line[2:] for line in items.splitlines())
        for level, items in SPEC_LEVEL.findall(spec)
    }


def levels_without_minimum(requirements, minimum, section="section 2.3"):
    """Each level, in LEVELS order, whose Requirements cell leaves out the minimum length, the
    minimum heading count of specification.md section 2.3 or that section (written as section),
    and either does not name the level below it or names that level when it is itself returned,
    and so lets a reader of the table alone take a file below that minimum for the level."""
    characters, headings = minimum
    named = (f"{characters} characters", f"{headings} section headings", section)
    missing = []
    for index, level in enumerate(LEVELS):
        cell = requirements.get(level, "")
        below = LEVELS[index - 1] if index else None
        inherits = below is not None and below not in missing and below in cell
        if not (inherits or all(part in cell for part in named)):
            missing.append(level)
    return missing


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


class HardenSoulTarget(unittest.TestCase):
    """harden-soul writes to the first governance file in the specification.md section 2.2 order and
    creates SOUL.md only when it finds none, so no description names SOUL.md as its file without
    saying when."""

    def setUp(self):
        self.lines = [line for path in README_PAGES for line in harden_soul_descriptions(path.read_text(encoding="utf-8"))]

    def test_no_description_names_soul_md_without_saying_when(self):
        self.assertEqual(unconditional_soul_targets(self.lines), [])

    def test_readme_links_the_discovery_order(self):
        lines = harden_soul_descriptions(README.read_text(encoding="utf-8"))
        self.assertTrue(any(DISCOVERY_LINK in line for line in lines), lines)

    def test_discovery_order_lists_soul_md_first_and_claude_md(self):
        order = discovery_order(SPECIFICATION.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(order), 2)
        self.assertEqual(order[0], "SOUL.md")
        self.assertIn("CLAUDE.md", order)

    def test_each_unconditional_description_is_reported(self):
        claims = (
            "# 1. Generate SOUL.md from templates, one section per missing domain",
            "# Generate or update SOUL.md from templates for missing domains",
            "1. `npx hackmyagent harden-soul` generates SOUL.md from templates",
            "`harden-soul` appends the missing sections to `SOUL.md`",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                self.assertEqual(unconditional_soul_targets([claim]), [claim])

    def test_description_that_says_when_is_not_reported(self):
        descriptions = (
            "`harden-soul` creates `SOUL.md` only when it finds none.",
            "With `CLAUDE.md` and no `SOUL.md`, it appends to `CLAUDE.md`.",
            "# Add template sections to the governance file, or create SOUL.md if there is none",
        )
        self.assertEqual(unconditional_soul_targets(descriptions), [])

    def test_each_sentence_is_read_on_its_own(self):
        line = "`harden-soul` writes SOUL.md. It changes a file only when a domain is missing."
        self.assertEqual(unconditional_soul_targets([line]), ["`harden-soul` writes SOUL.md."])


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


class ExitZeroAndEssential(unittest.TestCase):
    """Essential requires the minimum length and heading count of specification.md section 2.3
    (conformance.md, Level 1 requirement 1), and the scanner exits 0 on a file below them, so a
    page that ties exit 0 to the Essential level names that minimum."""

    def setUp(self):
        self.minimum = minimum_viable(SPECIFICATION.read_text(encoding="utf-8"))

    def test_specification_sets_a_minimum_length_and_heading_count(self):
        self.assertEqual(self.minimum, (500, 3))

    def test_readme_and_guide_say_what_exit_0_means(self):
        for path in (README, INTEGRATIONS):
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                self.assertEqual(len(exit_0_statements(path.read_text(encoding="utf-8"))), 1)

    def test_no_page_ties_exit_0_to_essential_without_the_minimum(self):
        for path in SCORE_DOCS:
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                self.assertEqual(unqualified_exit_0(path.read_text(encoding="utf-8"), self.minimum), [])

    def test_statement_that_equates_exit_0_with_essential_is_reported(self):
        readme = "`scan-soul` exits 0 when the file meets the Essential level, 1 when a CRITICAL control is not detected."
        guide = "- `0`: Conformance is Essential or better, and no flag failed the run."
        for line in (readme, guide):
            with self.subTest(line=line):
                self.assertEqual(unqualified_exit_0(line + "\n", (500, 3)), [line])

    def test_statement_inside_a_code_block_is_not_read(self):
        text = "```text\nscan-soul exits 0 when the file meets the Essential level\n```\n"
        self.assertEqual(exit_0_statements(text), [])

    def test_minimum_read_from_a_section_with_other_values(self):
        spec = (
            MINIMUM_SECTION + "\n\n"
            "- **Length**: At least 800 characters of content\n"
            "- **Structure**: At least 4 distinct section headings\n\n"
            "### 2.4 Next\n\n- **Length**: At least 1 characters\n"
        )
        self.assertEqual(minimum_viable(spec), (800, 4))


class EssentialControlsAndMinimum(unittest.TestCase):
    """A line can tie the Essential level to its CRITICAL controls without saying what exit 0
    means ("the scanner already fails the job when a CRITICAL control is missing, which is the
    Essential gate"), and ExitZeroAndEssential does not read it. Essential also requires the
    minimum of specification.md section 2.3, so a line that names Essential and gives a level's
    requirement as controls names that minimum too."""

    PAGES = README_PAGES + (INTEGRATIONS,)

    def setUp(self):
        self.minimum = minimum_viable(SPECIFICATION.read_text(encoding="utf-8"))

    def test_no_page_gives_essential_as_controls_without_the_minimum(self):
        for path in self.PAGES:
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                self.assertEqual(
                    essential_controls_without_minimum(path.read_text(encoding="utf-8"), self.minimum), []
                )

    def test_line_that_calls_the_critical_control_check_the_essential_gate_is_reported(self):
        gate = (
            "1. Add `scan-soul` to the CI pipeline with `--fail-below 40` to keep grade C or better. Without the"
            " flag, the scanner already fails the job when a CRITICAL control is missing, which is the Essential gate"
        )
        summary = (
            "The Essential / Standard / Hardened conformance levels are requirements-based (which controls must"
            " pass, plus a minimum score) and are defined in [conformance.md](../conformance.md)."
        )
        for line in (gate, summary):
            with self.subTest(line=line):
                self.assertEqual(essential_controls_without_minimum(line + "\n", (500, 3)), [line])

    def test_line_that_names_the_minimum_is_not_reported(self):
        line = (
            "Essential requires a file of at least 500 characters and at least 3 section headings"
            " (section 2.3) in which every CRITICAL control passes."
        )
        self.assertEqual(essential_controls_without_minimum(line + "\n", (500, 3)), [])

    def test_line_without_a_control_requirement_is_not_reported(self):
        line = "The three conformance levels (Essential, Standard and Hardened) are in conformance.md."
        self.assertEqual(essential_controls_without_minimum(line + "\n", (500, 3)), [])

    def test_line_inside_a_code_block_is_not_read(self):
        text = "```text\nEssential: every CRITICAL control passes\n```\n"
        self.assertEqual(essential_controls_without_minimum(text, (500, 3)), [])


class ConformanceFieldAndMinimum(unittest.TestCase):
    """The `conformance` field of `scan-soul --json` does not show a level by itself: hackmyagent
    0.33.2 sets it to "essential" for a 79-byte SOUL.md with no headings, and every level requires
    the minimum of specification.md section 2.3. So a line that points the reader to that field
    names the minimum too."""

    def setUp(self):
        self.minimum = minimum_viable(SPECIFICATION.read_text(encoding="utf-8"))

    def test_no_page_names_the_field_without_the_minimum(self):
        for path in SCORE_DOCS:
            with self.subTest(file=path.relative_to(README.parent).as_posix()):
                self.assertEqual(
                    conformance_field_without_minimum(path.read_text(encoding="utf-8"), self.minimum), []
                )

    def test_line_that_reads_the_level_from_the_field_is_reported(self):
        field = (
            "3. Raise the threshold over time: 60 is the minimum score for Standard and 75 for Hardened. Each"
            " level also names the controls that must pass, so read the level from the `conformance` field of"
            " the `--json` output"
        )
        key = "The `conformance` key of the JSON output is the conformance level of the file."
        for line in (field, key):
            with self.subTest(line=line):
                self.assertEqual(conformance_field_without_minimum(line + "\n", (500, 3)), [line])

    def test_line_that_names_the_minimum_is_not_reported(self):
        line = (
            "The `conformance` field does not check at least 500 characters and at least 3 section headings"
            " (section 2.3), so count those in the file."
        )
        self.assertEqual(conformance_field_without_minimum(line + "\n", (500, 3)), [])

    def test_table_key_and_code_block_are_not_read(self):
        text = (
            "| `conformance` | `none`, `essential`, `standard` or `hardened`, in lower case. |\n"
            "```text\nread the level from the `conformance` field\n```\n"
        )
        self.assertEqual(conformance_field_without_minimum(text, (500, 3)), [])


class LevelTableMinimum(unittest.TestCase):
    """Level 1 requirement 1 of conformance.md makes the minimum of specification.md section 2.3
    part of Essential, and Standard and Hardened include every requirement of the level below, so
    the level table names that minimum in the Essential row and the level below in the others."""

    OLD_TABLE = (
        LEVEL_TABLE_HEADER + "\n"
        "|-------|-------------|-----------------|\n"
        "| **Essential** | All CRITICAL controls pass | Minimum viable governance |\n"
        "| **Standard** | All CRITICAL and HIGH controls pass, overall score >= 60 | Production agents |\n"
        "| **Hardened** | All controls pass, overall score >= 75 | Autonomous agents |\n"
    )

    def setUp(self):
        self.minimum = minimum_viable(SPECIFICATION.read_text(encoding="utf-8"))
        self.requirements = level_requirements(CONFORMANCE_DOC.read_text(encoding="utf-8"))

    def test_table_has_a_row_for_each_level(self):
        self.assertEqual(tuple(self.requirements), LEVELS)

    def test_each_level_of_the_table_carries_the_minimum(self):
        self.assertEqual(levels_without_minimum(self.requirements, self.minimum), [])

    def test_table_that_gives_only_controls_and_scores_is_reported(self):
        self.assertEqual(levels_without_minimum(level_requirements(self.OLD_TABLE), (500, 3)), list(LEVELS))

    def test_level_that_names_a_level_without_the_minimum_is_reported(self):
        requirements = {
            "Essential": "All CRITICAL controls pass",
            "Standard": "Every Essential requirement is met, all HIGH controls pass",
            "Hardened": "Every Standard requirement is met, all controls pass",
        }
        self.assertEqual(levels_without_minimum(requirements, (500, 3)), list(LEVELS))

    def test_levels_that_name_the_level_below_are_not_reported(self):
        requirements = {
            "Essential": "A file of at least 500 characters and 3 section headings (section 2.3)",
            "Standard": "Every Essential requirement is met, overall score >= 60",
            "Hardened": "Every Standard requirement is met, overall score >= 75",
        }
        self.assertEqual(levels_without_minimum(requirements, (500, 3)), [])

    def test_rows_after_the_table_are_not_read(self):
        text = self.OLD_TABLE + "\nText.\n\n| **Essential** | Another table |\n"
        self.assertEqual(level_requirements(text)["Essential"], "All CRITICAL controls pass")


class SpecificationLevelMinimum(unittest.TestCase):
    """Section 7 of specification.md lists the requirements of each conformance level. Essential
    requires the minimum of section 2.3 (conformance.md, Level 1 requirement 1), and Standard and
    Hardened include every requirement of the level below, so the Essential list names that
    minimum and Section 2.3, and the Standard and Hardened lists each name the level below."""

    OLD_SECTION = (
        "## 7. Conformance Levels\n\n"
        "### 7.1 Essential\n\n**Requirements**:\n"
        "- All CRITICAL-severity controls applicable to the agent's tier MUST pass\n"
        "- No minimum score requirement\n\n"
        "### 7.2 Standard\n\n**Requirements**:\n"
        "- All CRITICAL-severity controls applicable to the agent's tier MUST pass\n"
        "- All HIGH-severity controls applicable to the agent's tier MUST pass\n"
        "- Overall score MUST be >= 60\n\n"
        "### 7.3 Hardened\n\n**Requirements**:\n"
        "- ALL controls applicable to the agent's tier MUST pass\n"
        "- Overall score MUST be >= 75\n\n"
    )

    def setUp(self):
        spec = SPECIFICATION.read_text(encoding="utf-8")
        self.minimum = minimum_viable(spec)
        self.requirements = specification_level_requirements(spec)

    def test_section_7_has_a_list_for_each_level(self):
        self.assertEqual(tuple(self.requirements), LEVELS)

    def test_each_level_of_section_7_carries_the_minimum(self):
        self.assertEqual(levels_without_minimum(self.requirements, self.minimum, "Section 2.3"), [])

    def test_section_that_gives_only_controls_and_scores_is_reported(self):
        requirements = specification_level_requirements(self.OLD_SECTION)
        self.assertEqual(levels_without_minimum(requirements, (500, 3), "Section 2.3"), list(LEVELS))

    def test_list_items_are_joined_and_text_after_the_list_is_not_read(self):
        text = (
            "### 7.1 Essential\n\n**Requirements**:\n"
            "- At least 500 characters\n- and 3 section headings\n\n"
            "**Interpretation**: Section 2.3.\n"
        )
        self.assertEqual(
            specification_level_requirements(text),
            {"Essential": "At least 500 characters and 3 section headings"},
        )

    def test_lists_outside_section_7_are_not_read(self):
        text = "### 6.1 Essential\n\n**Requirements**:\n- At least 500 characters\n"
        self.assertEqual(specification_level_requirements(text), {})


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
