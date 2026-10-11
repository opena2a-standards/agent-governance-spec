# Changelog

All notable changes to the Agent Behavioral Governance Specification (OASB-2)
are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Added

- `scripts/check_docs_prose.py`, the check for the two prose rules in the
  `CONTRIBUTING.md` style guide: no spaced double hyphen, em dash, or spaced
  en dash used as a dash, and no heading or bold label named "Why this
  exists" or "Why this matters". It reads the tracked Markdown files except
  `CHANGELOG.md`, the files under `examples/`, and the rendered crosswalk
  files, prints one `file:line: message` line per finding, and exits 1. A
  double hyphen or an en dash is a dash when a space, a tab, or the edge of
  the line is on each side of it. A heading is an ATX heading at any indent,
  a setext heading, or a bold label that starts a line. A code fence closes
  only at a run of its own character at least as long as the run that
  opened it. An argument that is not a directory prints a usage message and
  exits 2. Tests in `scripts/test_check_docs_prose.py`.
- `controls.json` at the repository root: the JSON control export named in
  `specification.md` section 8.2, one entry per control ID with `id`,
  `title`, `domain`, `severity`, `status`, `replacedBy` (deprecated entries
  only), and `version`. It is generated from the domain files by
  `scripts/check_crosswalks.py --write`, and the plain run requires the
  committed file to equal that render byte for byte, as it does for the
  rendered crosswalk `.md` files. The validator also checks each control's
  attribute table: the ID matches its heading, the severity and status are
  in their vocabularies, `Replaced by` is present on deprecated entries only
  and names another control, a `Replaced by` chain ends at an active
  control, so a cycle of deprecated controls is red (`specification.md`
  section 8.2), and a version is `MAJOR.MINOR.PATCH` in ASCII digits without
  leading zeros. An attribute table row outside ID, Severity, Applicable
  tiers, Status, Replaced by, and Version, a table row that is not an
  attribute row, an attribute row separated from its table, and a control in
  a domain file with no `# Domain N:` heading are reported. Tests in
  `scripts/test_check_crosswalks.py`.
- Control identifier stability rule (`specification.md` section 8.2): IDs are
  never reused or renumbered; a withdrawn control is deprecated with
  `replacedBy`; the status vocabulary `draft`, `active`, `deprecated` and the
  `version` attribute of an entry are adopted from the AI Agent Threat Matrix
  technique schema; the domain renumbering of 2026-06-05 (pull request #4;
  7 to 15 became 11 to 19) is the last one on record. Section 5.1 gains the
  Status and Replaced by attributes; section 5.3 states that every control is
  active.
- Label mapping (`specification.md` section 9): the single home of the mapping
  from the OASB corpus and Eval vocabularies onto OASB-2 controls, with the row
  shape for sensitivity labels reserved until a label registry is published.
- Export contract for the crosswalk CSV files (`crosswalks/README.md`): header,
  encoding, and how deprecated IDs appear.
- Static crosswalks from OASB-2 controls to NIST AI RMF 1.0 and to the EU AI
  Act (Regulation (EU) 2024/1689) under `crosswalks/`, rendered from canonical
  CSV files and checked by the stdlib validator `scripts/check_crosswalks.py`.
  The plain run requires each rendered crosswalk `.md` file, and
  `controls.json`, to equal its render byte for byte, and `--write` writes
  them with LF line endings on every platform; a crosswalk CSV with the
  header and no rows is rendered, compared, and written like any other.
  `.gitattributes` pins LF line endings for the crosswalk CSV and `.md`
  files and `controls.json`, so a checkout with `core.autocrlf=true` is
  green. A carriage return or a UTF-8
  BOM in one of these files is reported at its line in the words used for
  the CSV files, a byte that is not UTF-8 at its line, and a length
  difference only when the text, read with the BOM removed and CRLF and CR
  as LF, differs in length from the render, and a shorter or longer report
  on a file that had a BOM or a carriage return says the text was read that
  way. The reports that a file differs
  from its render, is shorter or longer than it, or holds a byte that is not
  UTF-8 name `python3 scripts/check_crosswalks.py --write`; the BOM and
  carriage-return reports do not.
- This changelog; version qualified to the spec-family ladder (1.0.0-draft).

### Changed

- README Related Work and `specification.md` section 1.3 state the OASB
  relationship with the OASB-1 count (46, published at oasb.ai) and the
  unified total (118, the sum 72 + 46, not measured on its own).
- README Scoring section aligned with `scoring.md` grades and `conformance.md`
  (removes the invented score-band "levels" vocabulary). (#7, 2026-07-02)

### Fixed

- The registry table in `specification.md` section 5.3 gives each control's
  heading title as its Name, as `controls.json` does; it differed for all 72
  controls: in wording for SOUL-HB-003, SOUL-AS-001, SOUL-AS-002,
  SOUL-AS-003, and SOUL-HT-002, and in letter case alone for the other 67.
  The validator now holds the table to the domain files.
- README Repository Structure lists `CHANGELOG.md`, `controls.json`,
  `scripts/`, and `integrations/`.
- The README Use cases section expands AAP as the Agent Authorization
  Protocol and no longer names a broker, a component the specification does
  not define. Tests in `scripts/test_check_crosswalks.py` require an acronym
  in parentheses in README.md to follow its expansion.
- The README use case that copies `templates/tool-using.md` includes the
  edit step before the scan, as Quick Start does, and states that an
  unedited template scans as partial coverage. `scripts/test_readme.py`
  checks that every README command block that copies a template edits it
  before scanning. (#27)
- README.md, `integrations/README.md`, and the GitHub Actions and GitLab CI
  examples under `integrations/` request JSON from `scan-soul` with
  `--json`. They passed `--format json`, which the scanner rejects as an
  unknown option, so both CI examples stopped before they read a score. The
  GitHub Actions example no longer writes stderr into `scan-result.json`,
  where the notice npm prints when it installs the scanner on a new runner
  made the file unreadable as JSON. `scripts/test_scan_soul_commands.py`
  checks that every `scan-soul` command in the Markdown and YAML files uses
  an option the scanner lists, and that a `--json` command keeps stderr out
  of its output. (#31)
- The minimum score in `integrations/github-action.yml` is read from the
  `MIN_GOVERNANCE_SCORE` repository variable, so the job fails when the score
  is below it. It was read from a `fail-below` input that the workflow never
  declared and that `pull_request` and `push` runs do not carry, so the
  minimum was always 0 and the check never failed. A minimum that is not a
  whole number fails the job with a message naming the variable, and
  `actionlint` reports nothing on the workflow.
  `integrations/README.md` shows how to set the variable, and
  `scripts/test_integrations.py` runs the check against scores below, at,
  and above the minimum. (#32)
- The domain table in the GitHub Action's pull request comment reads the
  scanner's `domains` array and gives each domain's `passed`/`total` and
  `percentage`. It read `domains` as an object keyed by domain name with a
  `found` count, which the scanner does not print, so every row would have
  shown the array index and `undefined/N (NaN%)`. Tests in
  `scripts/test_github_action.py` run the comment script on JSON in the
  scanner's shape. (#34)
- `integrations/README.md` documents the `scan-soul` exit codes as the
  scanner defines them. Exit `1` also means a CRITICAL control was not
  detected, with no `--fail-below` given, and covers `--ci` findings and
  usage errors; exit `2` covers a governance file that is missing,
  unreadable, or empty; exit `0` requires Essential conformance. Each case
  names its `gate.reason`. `scripts/test_integrations_readme.py` checks that
  each `gate.reason` is listed under the exit code the scanner gives it. (#36)
- The Standard level in `conformance.md` lists all 12 HIGH controls. Its
  table omitted SOUL-IH-004, SOUL-HB-005, SOUL-HB-008, and SOUL-HO-008, and
  the Path to Standard steps omitted those four and SOUL-HV-001; each step
  now names the control it satisfies, grouped by the tiers it applies to.
  `scripts/check_crosswalks.py` now requires the CRITICAL and HIGH tables to
  list every active control of that severity with the domain files' title
  and applicable tiers, in the order of `controls.json`, and each path to
  name every one of them. Tests in `scripts/test_check_crosswalks.py`. (#39)
- The `scan-soul` JSON sample in `integrations/README.md` is a trimmed run
  of hackmyagent 0.33.2. It had a `tier` key for `agentTier`, a top-level
  `controls` list, `domains` as an object, and upper-case conformance, and it
  left out `level`, `gate`, `coverage`, `criticalMissing` and the other keys
  the scanner prints. The guide now names the keys to code against, with
  their values, and the ones a scanner release can change.
  `scripts/test_readme.py` holds the sample to the scanner's key set and
  value vocabularies, and every key the table names to the sample. (#35)
- The conformance badge URLs in `conformance.md` and `integrations/README.md`
  returned "404: badge not found": shields.io splits a static badge path on
  single dashes, so `OASB-2-Essential-blue` had four parts. They now use the
  README's `OASB--2` form, which renders "OASB-2: Essential", and one colour
  per level in all three files: Essential blue, Standard teal, Hardened
  green. `scripts/test_readme.py` checks that every badge URL in the three
  files reads as label `OASB-2`, a message and a colour, and that each level
  has one colour. (#38)
- The README Adoption Path no longer labels `--fail-below 40` as Essential,
  or 60 and 75 as Standard and Hardened. Essential is both CRITICAL controls
  passing, with no minimum score: under hackmyagent 0.33.2 a governance file
  that scores 10 with both present scans as `essential`, and
  `--fail-below 40` fails it. The steps now say that `--fail-below 40` keeps
  grade C or better, that the scanner fails the job on a missing CRITICAL
  control without the flag, which is the Essential gate, that 60 and 75 are
  the minimum scores of Standard and Hardened, and that the level is read
  from the `conformance` field. `scripts/test_readme.py` checks that
  `README.md`, `integrations/README.md` and `conformance.md` label no score
  with a conformance level. (#47)
- The critical floor rule in `README.md`, `specification.md` section 6.4,
  and `scoring.md` caps the grade at C and leaves the overall score as
  calculated, as the scanner reports it. The three documents had promised an
  effective maximum score of 60, which the scanner does not apply: a file
  missing SOUL-HB-001 is reported with score 92 and grade C. Worked example 3
  in `scoring.md` now reports score 86 beside grade C.
  `scripts/test_critical_floor.py` checks that no document claims a score
  cap. (#42)

## [1.0.0-draft] - 2026-03-03 (evolving draft through 2026-06-05)

### Changed

- Control set expanded from 30 to 72 to match the scanner; three control
  severities recalibrated for rubric consistency. (#5, #6, 2026-06-05)
- Behavioral domains renumbered to 11-19 and OASB-2 naming adopted. (#4)
- Renamed AGS → ABGS across all files. (#2)

### Added

- Domain 15: Harm Avoidance (4 controls). (#1)
- Initial specification: behavioral governance domains, control catalog,
  scoring model, conformance levels, templates, worked examples, and
  integrations. Domains 08-14 added; Honesty/Transparency and Human
  Oversight domains refined during initial drafting. (2026-03-03/04)
