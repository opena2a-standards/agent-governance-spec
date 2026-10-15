# OASB-2 Overview

The gap OASB-2 fills, its nine domains, the agent tiers and profiles, how coverage is scored, and an adoption path. The [README](../README.md) links here; [`specification.md`](../specification.md) is the normative text.

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

OASB-2 fills the layer between model specifications (what the model can do) and deployment behavior (what the agent actually does). It is the agent's own declared behavioral contract: what it will and will not do, who it trusts, how it handles sensitive data, and when it requires human approval. OASB-2 coverage is measured through automated scanning and CI/CD checks of the governance file. Enforcing the declared behavior at runtime is the responsibility of runtime platforms, outside the scope of OASB-2.

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
| Agentic Safety | 16 | 10 | Iteration limits, budget caps, timeouts; for MULTI-AGENT only, reversibility |
| Honesty and Transparency | 17 | 8 | Uncertainty acknowledgment, factual accuracy, identity disclosure |
| Human Oversight | 18 | 8 | Approval gates, override mechanisms, monitoring requirements |
| Harm Avoidance | 19 | 4 | Pre-action risk assessment, proportional response, unintended impact, ambiguity resolution |

Each control has a severity level (CRITICAL, HIGH, MEDIUM, or LOW) and a set of detection keywords for automated scanning. See [specification.md](../specification.md) for the full formal specification, and the [domains/](../domains/) directory for detailed control definitions.

The three conformance levels (Essential, Standard and Hardened) and their audit procedures are in [conformance.md](../conformance.md).

---

## Agent Tiers

Not all agents need all controls. OASB-2 defines four tiers based on agent capability:

| Tier | Description | Applicable Controls (profile skips no domain) | Example |
|------|-------------|-------------------|---------|
| BASIC | Conversational agents with no tool access | 29 controls | Customer service chatbot |
| TOOL-USING | Agents that call APIs or use tools | 57 controls | Research assistant with web search |
| AGENTIC | Autonomous agents with multi-step execution | 69 controls | Coding assistant with file system access |
| MULTI-AGENT | Orchestrators that delegate to other agents | 72 controls (all) | Multi-agent pipeline coordinator |

The tier is not the only input. The agent profile names the agent's purpose and skips the domains that purpose does not use: `conversational` skips five domains, `code-assistant` skips Capability Boundaries, Agentic Safety, and Human Oversight, `tool-agent` skips Agentic Safety, and `autonomous`, `orchestrator`, and `custom` skip none. A TOOL-USING agent under `code-assistant` is measured on 40 controls, not 57. The scanner infers the profile from the file unless you declare it with `<!-- soul:profile=NAME -->` or `scan-soul --profile NAME`, and `scan-soul --json` reports it as `agentProfile` with the skipped domains in `skippedDomains`.

See [specification.md](../specification.md) Section 3 for tier definitions and the control applicability matrix, and Section 3.6 for the profiles and the applicable count for every tier and profile.

---

## Scoring

Governance coverage is scored per domain and rolled up into an overall score:

- **Per-domain score**: (controls detected / total applicable controls) x 100, where the tier and the profile decide which controls are applicable
- **Overall score**: Average of all applicable domain scores; a domain the profile skips is excluded
- **Tier and profile**: a published score names both the tier and the profile it was measured under, because the same file has 57 applicable controls as TOOL-USING under a profile that skips no domain and 40 under `code-assistant`
- **Grade**: A (80-100), B (60-79), C (40-59), D (20-39), F (0-19)
- **Critical floor**: If any applicable CRITICAL control is missing, the maximum grade is C, regardless of the calculated score. The cap applies to the grade only: the overall score is reported as calculated, so a score of 60 or more can appear beside grade C

Grades measure coverage; they are not the conformance levels. The Essential / Standard / Hardened conformance levels are requirements-based and are defined in [conformance.md](../conformance.md): Essential requires a governance file of at least 500 characters of content and at least 3 section headings ([specification.md](../specification.md) section 2.3) in which every applicable CRITICAL control passes, Standard adds every applicable HIGH control and an overall score of at least 60, and Hardened adds every applicable control and an overall score of at least 75.

See [scoring.md](../scoring.md) for the full scoring methodology with worked examples.

---

## Adoption Path

**For individual developers** (10 minutes):
1. `npx hackmyagent harden-soul` adds a template section for each missing domain to the governance file, and creates SOUL.md only when the directory holds none (see the [Quick Start](../README.md#quick-start))
2. Edit that file to match your agent's actual constraints
3. `npx hackmyagent scan-soul` verifies coverage
4. Copy [GitHub Action](../integrations/github-action.yml) to enforce on PRs
5. Add badge to README ([README Badge](ci.md#readme-badge))

**For teams**:
1. Add `scan-soul` to the CI pipeline with `--fail-below 40` to keep grade C or better. Without the flag, the scanner already fails the job when a CRITICAL control is missing. A passing job does not show the Essential level: Essential also requires at least 500 characters of content and at least 3 section headings ([specification.md](../specification.md) section 2.3), and hackmyagent 0.33.2 checks neither (it exits 0 on a 114-byte `SOUL.md` with three headings, and on a 79-byte one with none), so check those two in the file itself
2. Adopt SOUL.md as a required file alongside README.md
3. Raise the threshold over time: 60 is the minimum score for Standard and 75 for Hardened. Each level also names the controls that must pass. The `conformance` field of the `--json` output does not show a level by itself: every level requires at least 500 characters of content and at least 3 section headings ([specification.md](../specification.md) section 2.3), and hackmyagent 0.33.2 reports `essential` there for a 79-byte `SOUL.md` with no headings, so read the field together with those two counts taken from the file itself

**For organizations**:
1. Set minimum OASB-2 conformance level per agent risk tier
2. Use JSON output (`--json`) for compliance dashboards
3. Integrate with existing GRC tooling via structured scan results
