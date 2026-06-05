> **[OpenA2A](https://github.com/opena2a-org/opena2a)**: [CLI](https://github.com/opena2a-org/opena2a) · [HackMyAgent](https://github.com/opena2a-org/hackmyagent) · [Secretless](https://github.com/opena2a-org/secretless-ai) · [AIM](https://github.com/opena2a-org/agent-identity-management) · [Browser Guard](https://github.com/opena2a-org/AI-BrowserGuard) · [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent)
# OASB-2: Agent Behavioral Governance Specification

The first open specification for AI agent behavioral governance.

OASB-2 defines what goes in a governance file (SOUL.md), how to measure governance coverage across nine behavioral domains, and three conformance levels for auditing agent deployments. It is maintained by [OpenA2A](https://opena2a.org) and licensed under Apache-2.0.

---

## The Gap

The AI agent ecosystem has standards for several layers of the stack, but behavioral governance at the deployment level has been unaddressed:

| Layer | What Exists | What It Covers |
|-------|-------------|----------------|
| Foundation model | [Anthropic Soul](https://www.anthropic.com/research/claude-character), [OpenAI Model Spec](https://cdn.openai.com/spec/model-spec-2024-05-08.html) | How the base model should behave |
| Agent persona | [SoulSpec](https://soulspec.org) | Personality, tone, and character traits |
| Agent capabilities | [Agent Skills](https://agentskills.io) | Procedural knowledge and tools |
| Infrastructure | [NIST AI Agent Standards](https://www.nist.gov/artificial-intelligence) | Identity, interoperability, and infrastructure |
| Coding instructions | [AGENTS.md](https://agents.md) | Instructions for AI coding agents |
| **Behavioral governance** | **OASB-2 (this specification)** | **Per-agent safety constraints, scope boundaries, oversight requirements** |

OASB-2 fills the layer between model specifications (what the model can do) and deployment behavior (what the agent actually does). It is the agent's own declared behavioral contract: what it will and will not do, who it trusts, how it handles sensitive data, and when it requires human approval. OASB-2 also provides runtime enforcement through automated scanning and CI/CD integration.

---

## Quick Start

Create a governance file for your agent and validate it:

```bash
# 1. Generate a governance file with guided prompts
npx hackmyagent harden-soul

# 2. Scan the file for governance coverage
npx hackmyagent scan-soul

# 3. Review the report and fill any gaps
```

Or start from a template:

```bash
# Copy the template for your agent tier
cp templates/tool-using.md SOUL.md

# Edit to match your agent's actual constraints
# Then scan for coverage
npx hackmyagent scan-soul
```

---

## Specification Overview

OASB-2 defines **9 governance domains** containing **72 controls** that cover the behavioral surface area of an AI agent deployment.

| Domain | ID | Controls | What It Governs |
|--------|-----|----------|----------------|
| Trust Hierarchy | 11 | 8 | Who the agent trusts, priority order, conflict resolution |
| Capability Boundaries | 12 | 10 | Allowed and denied actions, scope, least privilege |
| Injection Hardening | 13 | 8 | Prompt injection defense, encoded payloads, role-play refusal |
| Data Handling | 14 | 8 | PII protection, credential handling, data minimization |
| Hardcoded Behaviors | 15 | 8 | Immutable safety rules, exfiltration prevention, kill switch |
| Agentic Safety | 16 | 10 | Iteration limits, budget caps, timeouts, reversibility |
| Honesty and Transparency | 17 | 8 | Uncertainty acknowledgment, factual accuracy, identity disclosure |
| Human Oversight | 18 | 8 | Approval gates, override mechanisms, monitoring requirements |
| Harm Avoidance | 19 | 4 | Pre-action risk assessment, proportional response, unintended impact, ambiguity resolution |

Each control has a severity level (CRITICAL, HIGH, MEDIUM, or LOW) and a set of detection keywords for automated scanning. See [specification.md](specification.md) for the full formal specification, and the [domains/](domains/) directory for detailed control definitions.

---

## Conformance Levels

OASB-2 defines three conformance levels for auditing governance coverage:

| Level | Requirements | Typical Use Case |
|-------|-------------|-----------------|
| **Essential** | All CRITICAL controls pass | Minimum viable governance for any deployed agent |
| **Standard** | All CRITICAL and HIGH controls pass, overall score >= 60 | Production agents handling user data or performing actions |
| **Hardened** | All controls pass, overall score >= 75 | Autonomous agents, agents in regulated environments |

See [conformance.md](conformance.md) for detailed requirements and audit procedures.

---

## Agent Tiers

Not all agents need all controls. OASB-2 defines four tiers based on agent capability:

| Tier | Description | Applicable Controls | Example |
|------|-------------|-------------------|---------|
| BASIC | Conversational agents with no tool access | 29 controls | Customer service chatbot |
| TOOL-USING | Agents that call APIs or use tools | 57 controls | Research assistant with web search |
| AGENTIC | Autonomous agents with multi-step execution | 69 controls | Coding assistant with file system access |
| MULTI-AGENT | Orchestrators that delegate to other agents | 72 controls (all) | Multi-agent pipeline coordinator |

See [specification.md](specification.md) Section 3 for tier definitions and the control applicability matrix.

---

## Scoring

Governance coverage is scored per domain and rolled up into an overall score:

- **Per-domain score**: (controls detected / total applicable controls) x 100
- **Overall score**: Average of all applicable domain scores
- **Level**: Hardened (80-100), Standard (60-79), Developing (40-59), Initial (20-39), Unscored (0-19)
- **Critical floor**: If any CRITICAL control is missing, maximum level is Developing regardless of score

See [scoring.md](scoring.md) for the full scoring methodology with worked examples.

---

## Related Work

OASB-2 is designed to complement, not compete with, existing specifications:

- **Anthropic Soul / OpenAI Model Spec**: These govern the foundation model's behavior. OASB-2 governs the deployed agent built on top of that model. An agent can comply with OASB-2 regardless of which model it uses.
- **SoulSpec (soulspec.org)**: Defines agent persona and personality. OASB-2 defines agent governance. A SOUL.md can coexist with a SoulSpec persona file -- they address different concerns.
- **Agent Skills (agentskills.io)**: Defines agent capabilities and procedural knowledge. OASB-2 defines behavioral constraints. Skills say what the agent can do; OASB-2 says what it must not do.
- **NIST AI Agent Standards**: Covers infrastructure, identity, and interoperability. OASB-2 covers behavioral safety. They are complementary layers.
- **AGENTS.md**: Instructions for AI coding agents about how to work with a codebase. OASB-2 defines safety and governance boundaries. An agent can follow both AGENTS.md (for coding conventions) and SOUL.md (for safety constraints).
- **OASB (Open Agent Security Benchmark)**: OASB-1 covers technical security (domains 1-10). OASB-2 covers behavioral governance (domains 11-19). Together they form the unified OASB (domains 1-19) for full-stack agent security assessment.
- **Awesome Agent Souls**: A [curated collection of 100+ SOUL.md templates](https://github.com/opena2a-org/awesome-agent-souls) organized by role, industry, organization type, and fleet. Use these as starting points instead of writing governance files from scratch.

---

## Tools

### HackMyAgent

[HackMyAgent](https://github.com/opena2a-org/hackmyagent) provides automated scanning and hardening for OASB-2 governance files:

```bash
# Scan an existing governance file
npx hackmyagent scan-soul

# Generate a governance file interactively
npx hackmyagent harden-soul

# Scan and output structured JSON
npx hackmyagent scan-soul --json
```

### OASB

[OASB](https://github.com/opena2a-org/oasb) integrates OASB-2 behavioral domains 11-19 alongside OASB-1 technical domains 1-10 for comprehensive agent security benchmarking.

---

## CI/CD Integration

Enforce governance in your pipeline with zero configuration:

**GitHub Actions** -- add `.github/workflows/governance.yml`:

```yaml
# Scans SOUL.md on PRs, comments with governance score
# See integrations/github-action.yml for the full workflow
name: Agent Governance Scan
on:
  pull_request:
    paths: ['SOUL.md', 'system-prompt.md', 'CLAUDE.md']
jobs:
  scan-soul:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npx hackmyagent@latest scan-soul --fail-below 40
```

**GitLab CI**, **pre-commit hooks**, and **npm scripts** examples are in [integrations/](integrations/).

### README Badge

Show your governance conformance:

```markdown
[![OASB-2 Conformant](https://img.shields.io/badge/OASB--2-Standard-teal)](https://github.com/opena2a-org/agent-governance-spec)
```

| Level | Badge |
|-------|-------|
| Essential | ![OASB-2 Essential](https://img.shields.io/badge/OASB--2-Essential-blue) |
| Standard | ![OASB-2 Standard](https://img.shields.io/badge/OASB--2-Standard-teal) |
| Hardened | ![OASB-2 Hardened](https://img.shields.io/badge/OASB--2-Hardened-green) |

---

## Adoption Path

**For individual developers** (10 minutes):
1. `npx hackmyagent harden-soul` -- generates SOUL.md from templates
2. Edit SOUL.md to match your agent's actual constraints
3. `npx hackmyagent scan-soul` -- verify coverage
4. Copy [GitHub Action](integrations/github-action.yml) to enforce on PRs
5. Add badge to README

**For teams**:
1. Add `scan-soul` to CI pipeline with `--fail-below 40` (Essential)
2. Adopt SOUL.md as a required file alongside README.md
3. Raise threshold over time: 40 (Essential) -> 60 (Standard) -> 75 (Hardened)

**For organizations**:
1. Set minimum OASB-2 conformance level per agent risk tier
2. Use JSON output (`--format json`) for compliance dashboards
3. Integrate with existing GRC tooling via structured scan results

---

## Repository Structure

```
agent-governance-spec/
  README.md                   Overview and quickstart
  LICENSE                     Apache-2.0
  CONTRIBUTING.md             How to contribute
  specification.md            Full formal specification (v1.0)
  scoring.md                  Scoring methodology
  conformance.md              Conformance levels
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
    chatbot-soul.md           Customer service bot
    coding-agent-soul.md      AI coding assistant
    data-pipeline-soul.md     Data processing agent
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on proposing new controls, modifying severity levels, suggesting domain changes, and other contributions.

---

## License

Apache-2.0. See [LICENSE](LICENSE) for the full text.

Copyright 2026 OpenA2A Contributors.
