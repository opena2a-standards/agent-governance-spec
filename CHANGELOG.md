# Changelog

All notable changes to the Agent Behavioral Governance Specification (OASB-2)
are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Added

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
