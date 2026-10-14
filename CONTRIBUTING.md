# Contributing to the Agent Behavioral Governance Specification

Thank you for your interest in contributing to the Agent Behavioral Governance Specification (OASB-2). This document explains how to propose changes, what the review process looks like, and how decisions are made.

---

## Repository Structure

```
agent-governance-spec/
  README.md                   Overview and quickstart
  LICENSE                     Apache-2.0
  CONTRIBUTING.md             How to contribute
  specification.md            Full formal specification (version 1.0.0-draft, status Draft)
  scoring.md                  Scoring methodology
  conformance.md              Conformance levels
  CHANGELOG.md                Changes by version
  controls.json               JSON control export, generated from domains/ (specification.md section 8.2)
  crosswalks/                 Static crosswalks to NIST AI RMF 1.0 and the EU AI Act
  docs/
    overview.md               The gap OASB-2 fills, the domains, agent tiers, scoring and adoption path
    related-work.md           How OASB-2 relates to other specifications
    ci.md                     CI/CD integration and the conformance badge
  scripts/
    check_crosswalks.py       Validates crosswalks/, controls.json and the control registry; --write re-renders
    check_docs_prose.py       Checks the Markdown prose for the dash and heading rules in CONTRIBUTING.md
    test_*.py                 Tests for the scripts, the docs and the CI examples; CONTRIBUTING.md gives the command that runs them
  domains/
    README.md                 Domain overview
    11-trust-hierarchy.md     Domain 11: Trust Hierarchy
    12-capability-boundaries.md  Domain 12: Capability Boundaries
    13-injection-hardening.md    Domain 13: Injection Hardening
    14-data-handling.md          Domain 14: Data Handling
    15-hardcoded-behaviors.md    Domain 15: Hardcoded Behaviors
    16-agentic-safety.md         Domain 16: Agentic Safety
    17-honesty-transparency.md   Domain 17: Honesty and Transparency
    18-human-oversight.md        Domain 18: Human Oversight
    19-harm-avoidance.md         Domain 19: Harm Avoidance
  templates/
    basic.md                  Minimal SOUL.md for chatbots
    tool-using.md             SOUL.md for tool-using agents
    agentic.md                SOUL.md for autonomous agents
    multi-agent.md            SOUL.md for orchestrators
  examples/
    README.md                 The example files, and what a scanner reports on them
    chatbot-soul.md           Customer service bot
    coding-agent-soul.md      AI coding assistant
    data-pipeline-soul.md     Data processing agent
  integrations/
    README.md                 CI integration guide
    github-action.yml         GitHub Actions workflow
    gitlab-ci.yml             GitLab CI job
```

---

## Types of Contributions

### 1. Proposing a New Control

If you believe a governance behavior is missing from the specification, open an issue with:

- **Control name**: A short, descriptive name (e.g., "Rate limiting disclosure")
- **Proposed domain**: Which of the 9 domains it belongs to
- **Severity**: CRITICAL, HIGH, MEDIUM, or LOW, with justification
- **Description**: What the control requires and why it matters
- **Detection keywords**: What automated scanners should look for
- **Applicable tiers**: Which agent tiers (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) need this control
- **Example compliant text**: A sample passage that would satisfy the control

### 2. Modifying a Control Severity

Severity changes affect conformance levels and scoring, so they require clear justification. Open an issue with:

- **Control ID**: The control being modified (e.g., SOUL-TH-002)
- **Current severity**: What it is now
- **Proposed severity**: What it should be
- **Rationale**: Why the change is warranted, ideally with references to real-world incidents or risk analysis

### 3. Domain Changes

Proposing a new domain or merging/splitting existing domains is a significant structural change. Open an issue with:

- **Proposed change**: What domain to add, remove, or restructure
- **Rationale**: Why the current structure is insufficient
- **Impact assessment**: How the change affects existing controls, scoring, and conformance levels

### 4. Template and Example Improvements

Templates and examples should be practical and realistic. Contributions that improve clarity, fix inaccuracies, or add coverage for new agent types are welcome as pull requests.

### 5. Tooling Integration

If you are building a tool that implements OASB-2 scanning or enforcement, we welcome documentation contributions that describe the integration.

---

## Process

1. **Open an issue** describing the proposed change before submitting a pull request. This allows community discussion before implementation work begins.

2. **Discussion period**: Issues remain open for at least 14 days to allow community input. Severity changes and new domains require 30 days.

3. **Pull request**: After discussion converges, submit a pull request implementing the change. Reference the issue number. A change to a control heading or its attribute table also regenerates `controls.json` with `python3 scripts/check_crosswalks.py --write`, and updates the control's row in the registry table of `specification.md` section 5.3, and for a change to `Applicable tiers` its row in the section 3.5 matrix and the Applicable controls counts in sections 3.1 to 3.4, all of which `python3 scripts/check_crosswalks.py` holds to the domain files, in the same pull request. Before opening it, run the tests of the scripts and of the integration examples with `python3 -m unittest discover -s scripts -p 'test_*.py'` from the repository root. The GitLab job tests in `scripts/test_gitlab_ci.py` need bash and node on PATH; without them they fail and name the missing program.

4. **Review**: Pull requests require at least one maintainer review. Changes to control definitions, severities, or domains require two maintainer reviews.

5. **Merge**: Approved pull requests are squash-merged into main.

---

## Versioning

OASB-2 follows semantic versioning:

- **Patch** (1.0.x): Typo fixes, clarifications, example improvements. No changes to control definitions or scoring.
- **Minor** (1.x.0): New controls, severity changes, new templates. Backward-compatible: existing compliant agents remain compliant.
- **Major** (x.0.0): Domain restructuring, scoring algorithm changes, breaking changes to conformance levels.

---

## Style Guide

- Use clear, technical language. Avoid marketing jargon or subjective qualifiers.
- Control descriptions should be specific enough that two independent scanners would produce the same result.
- Detection keywords should be concrete terms that appear in governance files, not abstract concepts.
- Examples should use realistic agent scenarios, not placeholder text.
- All Markdown files should use ATX-style headings (#, ##, ###).
- In prose, do not use a spaced double hyphen, an em dash, or a spaced en dash as a dash. Rewrite the sentence with a period, a comma, a colon, or parentheses. Code blocks, inline code, and the rendered crosswalk files are exempt. The check below lists the files it does not read.
- Do not name a heading or section "Why this exists" or "Why this matters". State what the reader needs under the existing heading.
- `python3 scripts/check_docs_prose.py` checks the last two rules across the tracked Markdown files and names each `file:line` that breaks them. It does not read `CHANGELOG.md` and `changelog.d/` at the repository root, LICENSE files, the rendered crosswalk files `crosswalks/oasb-2-to-*.md`, the example governance files under `examples/`, anything under `node_modules/`, `vendor/`, `dist/` or `build/` at the repository root, or anything in a directory named `test`, `tests`, `fixture`, `fixtures`, `corpus`, `golden`, `snapshot`, `snapshots`, `example` or `examples`, except a `README.md` or `README.mdx` that is in no directory of those names other than `example` or `examples`, so it checks `examples/README.md`. That exception does not override the other exclusions, so it does not read `vendor/examples/README.md`. The script's docstring gives the reason for each exclusion. Run it, with `python3 scripts/check_crosswalks.py`, before opening a pull request.

---

## Code of Conduct

Contributors are expected to engage respectfully and constructively. Focus on technical merit. Disagreements about severity levels and domain boundaries are expected and healthy. Resolve them with evidence and reasoning, not authority or volume.

---

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0, consistent with the project license.
