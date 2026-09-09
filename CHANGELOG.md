# Changelog

All notable changes to the Agent Behavioral Governance Specification (OASB-2)
are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Added

- Control identifier stability rule (`specification.md` section 8.2): ids are
  never reused or renumbered; a withdrawn control is deprecated with
  `replacedBy`; the status vocabulary `draft`, `active`, `deprecated` and the
  per entry `version` are adopted from the AI Agent Threat Matrix technique
  schema; the 2026-06-04 domain renumbering (7 to 15 became 11 to 19) is
  recorded as the last renumbering. Section 5.1 gains the Status and Replaced
  by attributes; section 5.3 states that every control is active.
- Label mapping (`specification.md` section 9): the single home of the mapping
  from the OASB corpus and Eval vocabularies onto OASB-2 controls, with the row
  shape for sensitivity labels reserved until a label registry is published.
- Export contract for the crosswalk CSV files (`crosswalks/README.md`): header,
  encoding, and how deprecated ids appear.
- Static crosswalks from OASB-2 controls to NIST AI RMF 1.0 and to the EU AI
  Act (Regulation (EU) 2024/1689) under `crosswalks/`, rendered from canonical
  CSV files and checked by the stdlib validator `scripts/check_crosswalks.py`.
- This changelog; version qualified to the spec-family ladder (1.0.0-draft).

### Changed

- README Related Work and `specification.md` section 1.3 state the OASB
  relationship with the OASB-1 count as documented (46) and the unified total
  as derived (118 = 72 + 46), not measured.
- README Scoring section aligned with `scoring.md` grades and `conformance.md`
  (removes the invented score-band "levels" vocabulary). (#7, 2026-07-02)

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
