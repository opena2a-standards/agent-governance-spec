> **[OpenA2A](https://github.com/opena2a-org/opena2a)**: [CLI](https://github.com/opena2a-org/opena2a) · [HackMyAgent](https://github.com/opena2a-org/hackmyagent) · [Secretless](https://github.com/opena2a-org/secretless-ai) · [AIM](https://github.com/opena2a-org/agent-identity-management) · [Browser Guard](https://github.com/opena2a-org/AI-BrowserGuard) · [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent)
# OASB-2: Agent Behavioral Governance Specification

The first open specification for AI agent behavioral governance.

OASB-2 defines what goes in a governance file (SOUL.md), how to measure governance coverage across nine behavioral domains, and three conformance levels for auditing agent deployments. It is maintained by [OpenA2A](https://opena2a.org) and licensed under Apache-2.0.

---

## Quick Start

Read [`specification.md`](specification.md) first: it defines the governance file, its nine domains and the three conformance levels. Then create a governance file for your agent and validate it:

```bash
# 1. Add a template section to the governance file for each missing domain
npx hackmyagent harden-soul

# 2. Scan the file for governance coverage
npx hackmyagent scan-soul

# 3. Review the report and fill any gaps
```

`harden-soul` writes to the first governance file it finds in the order of [specification.md section 2.2](specification.md#22-file-discovery), and creates `SOUL.md` only when it finds none. In a directory that holds `CLAUDE.md` and no other file of that list, it appends to `CLAUDE.md` and creates no `SOUL.md`. With `--dry-run --json`, its `file` field names the file it would change.

`scan-soul` exits 0 when every CRITICAL control applicable to the agent's tier is detected, 1 when a CRITICAL control is not detected, and 2 when there is nothing to measure (no governance file, or one that is empty or unreadable). Exit 0 alone does not show the Essential level: Essential also requires at least 500 characters of content and at least 3 section headings ([specification.md](specification.md) section 2.3), and hackmyagent 0.33.2 checks neither (it exits 0 on a 154-byte `SOUL.md` with three headings), so check those two in the file itself.

Or start from a template:

```bash
# Copy the template for your agent tier
cp templates/tool-using.md SOUL.md

# Edit to match your agent's actual constraints
# Then scan for coverage
npx hackmyagent scan-soul
```

---

## Use cases

### Your company runs a hundred agents and an auditor asks what each one promised

Every agent's rules live in a prompt somewhere, and no two are written alike. The auditor asks what each agent refuses to do, how it handles personal data and when it stops for a human, and the answer is a folder of prompts nobody can compare.

This specification defines the governance file, `SOUL.md`, that an agent carries: nine behavioral domains, 72 controls and three conformance levels, so "what did this agent commit to" has a checkable answer and a coverage score instead of a recollection.

What you can do today: scan a governance file for coverage.

```bash
npx hackmyagent scan-soul
```

Where it stops today: a scan measures what the file covers. It does not stop a running agent from exceeding what the file says; the authorization layer, the Agent Authorization Protocol (AAP), does not read the governance file today.

### An agent takes an action nobody approved

A tool-using agent can refund an order, delete a record or send mail, and nobody wrote down which of those need a person to say yes. The customer whose order was refunded twice, or whose record is gone, is the one who finds out.

What you can do today: copy the tool-using template, write in your agent's own tools, actions and approvals, then scan it.

```bash
cp templates/tool-using.md SOUL.md

# Edit to match your agent's actual constraints
# Then scan for coverage
npx hackmyagent scan-soul
```

The template is a starting point: scanned as copied, it reports partial coverage.

Where it stops today: the same limit applies; the file is a declared contract measured by a scanner, not a runtime control.

Why you can check this yourself: [`specification.md`](specification.md) is the full text; [`controls.json`](controls.json) is the 72-control export generated from [`domains/`](domains/) and validated by [`scripts/check_crosswalks.py`](scripts/check_crosswalks.py); [`templates/`](templates/) and [`examples/`](examples/) are complete files; [`integrations/github-action.yml`](integrations/github-action.yml) runs the scan on pull requests; and the scanner is [HackMyAgent](https://github.com/opena2a-org/hackmyagent) on npm.

---

## Tools

### HackMyAgent

[HackMyAgent](https://github.com/opena2a-org/hackmyagent) provides automated scanning and hardening for OASB-2 governance files:

```bash
# Scan an existing governance file
npx hackmyagent scan-soul

# Add template sections for missing domains to the governance file, or create SOUL.md if there is none
npx hackmyagent harden-soul

# Scan and output structured JSON
npx hackmyagent scan-soul --json
```

### OASB

[OASB](https://github.com/opena2a-org/oasb) integrates OASB-2 behavioral domains 11-19 alongside OASB-1 technical domains 1-10 for comprehensive agent security benchmarking.

---

## Documentation

- [`specification.md`](specification.md): the full formal specification; [`domains/`](domains/) holds the definition of each control.
- [`docs/overview.md`](docs/overview.md): the gap OASB-2 fills, the nine domains, agent tiers and profiles, scoring, and an adoption path for developers, teams and organizations.
- [`conformance.md`](conformance.md): the three conformance levels, their requirements and the audit procedures.
- [`scoring.md`](scoring.md): the scoring methodology with worked examples.
- [`docs/ci.md`](docs/ci.md): the GitHub Actions setup and the conformance badge; [`integrations/`](integrations/) holds the GitHub Actions, GitLab CI, pre-commit and npm script examples.
- [`docs/related-work.md`](docs/related-work.md): how OASB-2 relates to model specifications, persona and skill formats, AGENTS.md and OASB-1.
- **NIST AI RMF 1.0 and the EU AI Act**: an informative [crosswalk](crosswalks/README.md) lists which OASB-2 controls relate to which AI RMF subcategories and AI Act articles, with the relationship type stated per row. It is not a conformity assessment.
- [`CHANGELOG.md`](CHANGELOG.md): changes by version.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): the repository structure, and guidelines on proposing new controls, modifying severity levels, suggesting domain changes, and other contributions.

---

## License

Apache-2.0. See [LICENSE](LICENSE) for the full text.

Copyright 2026 OpenA2A Contributors.
