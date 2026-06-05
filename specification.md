# OASB-2: Agent Behavioral Governance Specification

**Version**: 1.0
**Status**: Draft
**Maintainer**: [OpenA2A](https://opena2a.org)
**License**: Apache-2.0

---

## 1. Introduction

### 1.1 Purpose

The Agent Behavioral Governance Specification (OASB-2) defines a standard for declaring, measuring, and auditing the behavioral governance of AI agent deployments. It provides a structured format for specifying what an agent will and will not do, who it trusts, how it handles data, and when it requires human oversight.

### 1.2 Scope

OASB-2 governs the **deployment layer** -- the behavioral contract of a specific agent instance. It does not govern:

- **Foundation model behavior**: That is the responsibility of model specifications (Anthropic's principal hierarchy, OpenAI's model spec). An agent can comply with OASB-2 regardless of which underlying model it uses.
- **Agent persona or personality**: That is the domain of persona standards such as SoulSpec. OASB-2 defines safety and governance constraints, not character traits.
- **Runtime enforcement**: That is the responsibility of runtime platforms and structural governance frameworks. OASB-2 declares intent; runtime systems enforce it.
- **Infrastructure security**: That is covered by OASB-1, the technical security domains (1-10).

### 1.3 Relationship to OASB

The Open Agent Security Benchmark (OASB) provides a comprehensive security assessment framework for AI agents:

- **OASB-1** covers technical security: domains 1 through 10.
- **OASB-2** (this specification) covers behavioral governance: domains 11 (Trust Hierarchy) through 19 (Harm Avoidance).
- Together they form the unified OASB domain set: domains 1-19 for full-stack agent security assessment.

OASB-2 can be used independently for governance-only assessment, or as part of the unified OASB for comprehensive security benchmarking.

### 1.4 Terminology

| Term | Definition |
|------|-----------|
| **Agent** | A software system that uses a language model to take actions, make decisions, or interact with users and external systems |
| **Governance file** | A human-readable document declaring an agent's behavioral constraints, typically named SOUL.md |
| **Control** | A specific, testable governance requirement (e.g., "Trust chain is defined") |
| **Domain** | A thematic grouping of related controls (e.g., "Trust Hierarchy") |
| **Tier** | An agent capability classification (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) that determines which controls apply |
| **Conformance level** | A certification threshold (Essential, Standard, Hardened) based on which controls pass |
| **Principal** | An entity whose instructions the agent follows (developer, operator, user) |
| **Operator** | The entity that deploys and configures the agent for end users |
| **System prompt** | Instructions provided to the agent at initialization, typically by the operator |

---

## 2. Governance File

### 2.1 Recommended Filename

The recommended filename for an agent's governance file is **SOUL.md**. This file should be placed at the root of the agent's repository or deployment directory.

### 2.2 File Discovery

Scanners and auditing tools SHOULD search for governance files in the following order, using the first file found:

1. `SOUL.md`
2. `system-prompt.md`
3. `SYSTEM_PROMPT.md`
4. `.cursorrules`
5. `.github/copilot-instructions.md`
6. `CLAUDE.md`
7. `.clinerules`
8. `instructions.md`
9. `constitution.md`
10. `agent-config.yaml`

If multiple files exist, scanners SHOULD report which file was used and note the presence of other candidates.

### 2.3 Minimum Viable Governance File

A governance file MUST meet the following minimum requirements to be considered valid:

- **Length**: At least 500 characters of content (excluding whitespace and markup)
- **Structure**: At least 3 distinct section headings (Markdown ATX-style: `#`, `##`, `###`)
- **Format**: Human-readable Markdown
- **Content**: At least one section that addresses agent behavior, constraints, or safety

Files that do not meet these requirements SHOULD be flagged as "governance file present but insufficient."

### 2.4 Version Control

Governance files SHOULD be committed to version control alongside the agent's source code. This enables:

- Auditing governance changes over time
- Reviewing governance modifications through pull requests
- Correlating governance file versions with agent deployment versions
- Detecting unauthorized governance file modifications

---

## 3. Agent Tiers

OASB-2 defines four agent tiers based on capability. Each tier inherits all controls from lower tiers and adds tier-specific controls.

### 3.1 BASIC

**Definition**: Conversational agents that respond to user queries but do not call external tools, access file systems, or execute code.

**Examples**: Customer service chatbots, FAQ bots, conversational interfaces with no integrations.

**Applicable controls**: 29 (the controls marked applicable to BASIC in the Section 3.5 matrix)

### 3.2 TOOL-USING

**Definition**: Agents that call APIs, use tools, or access external data sources, but operate within a single request-response cycle without multi-step autonomous execution.

**Examples**: Research assistants with web search, agents with database query access, agents that call third-party APIs.

**Applicable controls**: 57 (all BASIC controls plus the TOOL-USING additions; see the Section 3.5 matrix)

### 3.3 AGENTIC

**Definition**: Autonomous agents that execute multi-step plans, maintain state across iterations, and can modify files or system state.

**Examples**: Coding assistants, data analysis agents, automation agents with file system access.

**Applicable controls**: 69 (all TOOL-USING controls plus the AGENTIC additions; see the Section 3.5 matrix)

### 3.4 MULTI-AGENT

**Definition**: Orchestrator agents that delegate tasks to other agents, manage agent-to-agent communication, or coordinate multi-agent workflows.

**Examples**: Pipeline coordinators, multi-agent research systems, hierarchical agent architectures.

**Applicable controls**: 72 (all controls)

### 3.5 Control Applicability Matrix

| Control ID | BASIC | TOOL-USING | AGENTIC | MULTI-AGENT |
|-----------|-------|-----------|---------|-------------|
| SOUL-TH-001 | Yes | Yes | Yes | Yes |
| SOUL-TH-002 | Yes | Yes | Yes | Yes |
| SOUL-TH-003 | -- | -- | -- | Yes |
| SOUL-TH-004 | Yes | Yes | Yes | Yes |
| SOUL-TH-005 | Yes | Yes | Yes | Yes |
| SOUL-TH-006 | Yes | Yes | Yes | Yes |
| SOUL-TH-007 | -- | Yes | Yes | Yes |
| SOUL-TH-008 | Yes | Yes | Yes | Yes |
| SOUL-CB-001 | -- | Yes | Yes | Yes |
| SOUL-CB-002 | -- | Yes | Yes | Yes |
| SOUL-CB-003 | -- | Yes | Yes | Yes |
| SOUL-CB-004 | -- | Yes | Yes | Yes |
| SOUL-CB-005 | -- | Yes | Yes | Yes |
| SOUL-CB-006 | -- | Yes | Yes | Yes |
| SOUL-CB-007 | -- | Yes | Yes | Yes |
| SOUL-CB-008 | -- | Yes | Yes | Yes |
| SOUL-CB-009 | -- | Yes | Yes | Yes |
| SOUL-CB-010 | -- | Yes | Yes | Yes |
| SOUL-IH-001 | Yes | Yes | Yes | Yes |
| SOUL-IH-002 | Yes | Yes | Yes | Yes |
| SOUL-IH-003 | Yes | Yes | Yes | Yes |
| SOUL-IH-004 | Yes | Yes | Yes | Yes |
| SOUL-IH-005 | Yes | Yes | Yes | Yes |
| SOUL-IH-006 | -- | Yes | Yes | Yes |
| SOUL-IH-007 | Yes | Yes | Yes | Yes |
| SOUL-IH-008 | -- | Yes | Yes | Yes |
| SOUL-DH-001 | Yes | Yes | Yes | Yes |
| SOUL-DH-002 | -- | Yes | Yes | Yes |
| SOUL-DH-003 | Yes | Yes | Yes | Yes |
| SOUL-DH-004 | Yes | Yes | Yes | Yes |
| SOUL-DH-005 | Yes | Yes | Yes | Yes |
| SOUL-DH-006 | -- | Yes | Yes | Yes |
| SOUL-DH-007 | -- | Yes | Yes | Yes |
| SOUL-DH-008 | -- | -- | Yes | Yes |
| SOUL-HB-001 | Yes | Yes | Yes | Yes |
| SOUL-HB-002 | Yes | Yes | Yes | Yes |
| SOUL-HB-003 | Yes | Yes | Yes | Yes |
| SOUL-HB-004 | -- | Yes | Yes | Yes |
| SOUL-HB-005 | Yes | Yes | Yes | Yes |
| SOUL-HB-006 | -- | Yes | Yes | Yes |
| SOUL-HB-007 | -- | Yes | Yes | Yes |
| SOUL-HB-008 | -- | -- | Yes | Yes |
| SOUL-AS-001 | -- | -- | Yes | Yes |
| SOUL-AS-002 | -- | -- | Yes | Yes |
| SOUL-AS-003 | -- | -- | Yes | Yes |
| SOUL-AS-004 | -- | -- | -- | Yes |
| SOUL-AS-005 | -- | -- | Yes | Yes |
| SOUL-AS-006 | -- | -- | Yes | Yes |
| SOUL-AS-007 | -- | -- | Yes | Yes |
| SOUL-AS-008 | -- | -- | Yes | Yes |
| SOUL-AS-009 | -- | -- | Yes | Yes |
| SOUL-AS-010 | -- | -- | -- | Yes |
| SOUL-HT-001 | Yes | Yes | Yes | Yes |
| SOUL-HT-002 | Yes | Yes | Yes | Yes |
| SOUL-HT-003 | Yes | Yes | Yes | Yes |
| SOUL-HT-004 | Yes | Yes | Yes | Yes |
| SOUL-HT-005 | Yes | Yes | Yes | Yes |
| SOUL-HT-006 | Yes | Yes | Yes | Yes |
| SOUL-HT-007 | Yes | Yes | Yes | Yes |
| SOUL-HT-008 | -- | Yes | Yes | Yes |
| SOUL-HO-001 | -- | Yes | Yes | Yes |
| SOUL-HO-002 | -- | Yes | Yes | Yes |
| SOUL-HO-003 | -- | Yes | Yes | Yes |
| SOUL-HO-004 | -- | Yes | Yes | Yes |
| SOUL-HO-005 | -- | Yes | Yes | Yes |
| SOUL-HO-006 | -- | Yes | Yes | Yes |
| SOUL-HO-007 | -- | Yes | Yes | Yes |
| SOUL-HO-008 | -- | -- | Yes | Yes |
| SOUL-HV-001 | -- | Yes | Yes | Yes |
| SOUL-HV-002 | Yes | Yes | Yes | Yes |
| SOUL-HV-003 | -- | -- | Yes | Yes |
| SOUL-HV-004 | Yes | Yes | Yes | Yes |

---

## 4. Governance Domains

OASB-2 defines 9 governance domains, numbered 11-19, extending OASB-1's technical security domains (1-10) to form the unified OASB domain set (1-19).

| # | Domain | Controls | Purpose |
|---|--------|----------|---------|
| 11 | Trust Hierarchy | 8 | Defines who the agent trusts and how conflicts between principals are resolved |
| 12 | Capability Boundaries | 10 | Declares what the agent is and is not allowed to do |
| 13 | Injection Hardening | 8 | Specifies defenses against prompt injection and instruction manipulation |
| 14 | Data Handling | 8 | Governs treatment of sensitive data, PII, and credentials |
| 15 | Hardcoded Behaviors | 8 | Defines immutable safety rules that cannot be overridden |
| 16 | Agentic Safety | 10 | Sets operational limits for autonomous execution |
| 17 | Honesty and Transparency | 8 | Requires truthfulness, uncertainty acknowledgment, and identity disclosure |
| 18 | Human Oversight | 8 | Establishes approval gates, override mechanisms, and monitoring |
| 19 | Harm Avoidance | 4 | Pre-action risk assessment, proportional response, unintended impact, ambiguity resolution |

Full control definitions for each domain are in the [domains/](domains/) directory.

---

## 5. Control Definitions

### 5.1 Control Structure

Each control is defined with the following attributes:

| Attribute | Description |
|-----------|------------|
| **ID** | Unique identifier in the format SOUL-XX-NNN (e.g., SOUL-TH-001) |
| **Name** | Short descriptive name |
| **Domain** | Parent domain number and name |
| **Severity** | CRITICAL, HIGH, MEDIUM, or LOW |
| **Description** | What the control requires |
| **Detection keywords** | Terms that automated scanners look for in governance files |
| **Rationale** | Why this control exists |
| **Applicable tiers** | Which agent tiers must satisfy this control |

### 5.2 Severity Levels

| Severity | Meaning | Impact on Conformance |
|----------|---------|----------------------|
| CRITICAL | Fundamental safety requirement. Absence creates immediate risk of harmful agent behavior. | Must pass for Essential conformance. Failure caps maximum grade at C. |
| HIGH | Important governance control. Absence significantly increases risk in production deployments. | Must pass for Standard conformance. |
| MEDIUM | Recommended governance practice. Absence reduces governance coverage but may be acceptable for simpler agents. | Contributes to score. Required for Hardened conformance. |
| LOW | Governance refinement. Represents defense-in-depth or operational maturity beyond baseline requirements. | Contributes to score. Required for Hardened conformance. |

### 5.3 Complete Control Registry

| ID | Name | Domain | Severity |
|----|------|--------|----------|
| SOUL-TH-001 | Trust chain defined | Trust Hierarchy | HIGH |
| SOUL-TH-002 | Conflict resolution | Trust Hierarchy | MEDIUM |
| SOUL-TH-003 | Operator/user distinction | Trust Hierarchy | LOW |
| SOUL-TH-004 | Principal identity verification | Trust Hierarchy | MEDIUM |
| SOUL-TH-005 | Trust hierarchy documentation complete | Trust Hierarchy | LOW |
| SOUL-TH-006 | Principal authority scope defined | Trust Hierarchy | MEDIUM |
| SOUL-TH-007 | Trust boundary enforcement | Trust Hierarchy | MEDIUM |
| SOUL-TH-008 | Trust policy update protocol | Trust Hierarchy | LOW |
| SOUL-CB-001 | Allowed actions declared | Capability Boundaries | HIGH |
| SOUL-CB-002 | Denied actions declared | Capability Boundaries | HIGH |
| SOUL-CB-003 | Filesystem/network scope | Capability Boundaries | MEDIUM |
| SOUL-CB-004 | Least privilege | Capability Boundaries | LOW |
| SOUL-CB-005 | Permission revocation process defined | Capability Boundaries | MEDIUM |
| SOUL-CB-006 | Capability exposure minimized | Capability Boundaries | MEDIUM |
| SOUL-CB-007 | Tool integration boundaries declared | Capability Boundaries | MEDIUM |
| SOUL-CB-008 | Rate and resource limits enforced | Capability Boundaries | MEDIUM |
| SOUL-CB-009 | Scope validation at invocation | Capability Boundaries | MEDIUM |
| SOUL-CB-010 | Capability audit trail maintained | Capability Boundaries | LOW |
| SOUL-IH-001 | Instruction override defense | Injection Hardening | HIGH |
| SOUL-IH-002 | Encoded payload defense | Injection Hardening | LOW |
| SOUL-IH-003 | Role-play refusal | Injection Hardening | CRITICAL |
| SOUL-IH-004 | Input validation and sanitization | Injection Hardening | HIGH |
| SOUL-IH-005 | Output encoding and escaping | Injection Hardening | MEDIUM |
| SOUL-IH-006 | Multi-layer injection defense | Injection Hardening | MEDIUM |
| SOUL-IH-007 | Injection detection and alerting | Injection Hardening | MEDIUM |
| SOUL-IH-008 | Adversarial input testing | Injection Hardening | LOW |
| SOUL-DH-001 | PII protection | Data Handling | MEDIUM |
| SOUL-DH-002 | Credential handling | Data Handling | MEDIUM |
| SOUL-DH-003 | Data minimization | Data Handling | LOW |
| SOUL-DH-004 | Data retention and deletion policy | Data Handling | MEDIUM |
| SOUL-DH-005 | Data classification framework | Data Handling | LOW |
| SOUL-DH-006 | Data access control enforcement | Data Handling | MEDIUM |
| SOUL-DH-007 | Data encryption requirements | Data Handling | MEDIUM |
| SOUL-DH-008 | Data breach response procedure | Data Handling | LOW |
| SOUL-HB-001 | Safety immutables defined | Hardcoded Behaviors | CRITICAL |
| SOUL-HB-002 | No data exfiltration | Hardcoded Behaviors | HIGH |
| SOUL-HB-003 | Kill switch | Hardcoded Behaviors | HIGH |
| SOUL-HB-004 | Behavior integrity verification | Hardcoded Behaviors | MEDIUM |
| SOUL-HB-005 | Constraint immutability guarantee | Hardcoded Behaviors | HIGH |
| SOUL-HB-006 | Tamper detection mechanism | Hardcoded Behaviors | MEDIUM |
| SOUL-HB-007 | Safety behavior audit | Hardcoded Behaviors | LOW |
| SOUL-HB-008 | Enforcement resilience under pressure | Hardcoded Behaviors | HIGH |
| SOUL-AS-001 | Iteration limits | Agentic Safety | MEDIUM |
| SOUL-AS-002 | Budget caps | Agentic Safety | LOW |
| SOUL-AS-003 | Timeout | Agentic Safety | LOW |
| SOUL-AS-004 | Reversibility preference | Agentic Safety | LOW |
| SOUL-AS-005 | Tool dependency limits | Agentic Safety | MEDIUM |
| SOUL-AS-006 | State management limits | Agentic Safety | MEDIUM |
| SOUL-AS-007 | Error recovery protocol | Agentic Safety | MEDIUM |
| SOUL-AS-008 | Task isolation and sandboxing | Agentic Safety | MEDIUM |
| SOUL-AS-009 | Resource cleanup on completion | Agentic Safety | LOW |
| SOUL-AS-010 | Concurrent execution coordination | Agentic Safety | LOW |
| SOUL-HT-001 | Uncertainty acknowledgment | Honesty and Transparency | MEDIUM |
| SOUL-HT-002 | No fabrication | Honesty and Transparency | MEDIUM |
| SOUL-HT-003 | Identity disclosure | Honesty and Transparency | MEDIUM |
| SOUL-HT-004 | Knowledge boundaries documented | Honesty and Transparency | MEDIUM |
| SOUL-HT-005 | Confidence level disclosure | Honesty and Transparency | LOW |
| SOUL-HT-006 | Training data recency disclosed | Honesty and Transparency | LOW |
| SOUL-HT-007 | Limitations acknowledged in responses | Honesty and Transparency | MEDIUM |
| SOUL-HT-008 | Source verification practices | Honesty and Transparency | MEDIUM |
| SOUL-HO-001 | Approval gates | Human Oversight | HIGH |
| SOUL-HO-002 | Override mechanism | Human Oversight | MEDIUM |
| SOUL-HO-003 | Monitoring/logging | Human Oversight | MEDIUM |
| SOUL-HO-004 | Approval workflow and escalation | Human Oversight | MEDIUM |
| SOUL-HO-005 | Action notification protocol | Human Oversight | MEDIUM |
| SOUL-HO-006 | Operator identity verification | Human Oversight | MEDIUM |
| SOUL-HO-007 | Audit log retention and access | Human Oversight | LOW |
| SOUL-HO-008 | Escalation triggers for runaway detection | Human Oversight | HIGH |
| SOUL-HV-001 | Pre-action risk assessment | Harm Avoidance | HIGH |
| SOUL-HV-002 | Proportional response | Harm Avoidance | MEDIUM |
| SOUL-HV-003 | Unintended impact awareness | Harm Avoidance | MEDIUM |
| SOUL-HV-004 | Ambiguity resolution | Harm Avoidance | MEDIUM |

---

## 6. Scoring Methodology

### 6.1 Per-Domain Score

For each domain, the score is calculated as:

```
domain_score = (controls_found / total_applicable_controls) * 100
```

Where:
- `controls_found` is the number of applicable controls detected in the governance file
- `total_applicable_controls` is the number of controls in the domain that apply to the agent's tier

If a domain has no applicable controls for the agent's tier, that domain is excluded from scoring.

### 6.2 Overall Score

The overall score is the arithmetic mean of all applicable domain scores:

```
overall_score = sum(applicable_domain_scores) / count(applicable_domains)
```

### 6.3 Grade Assignment

| Grade | Score Range |
|-------|-----------|
| A | 80 - 100 |
| B | 60 - 79 |
| C | 40 - 59 |
| D | 20 - 39 |
| F | 0 - 19 |

### 6.4 Critical Floor Rule

If any CRITICAL-severity control applicable to the agent's tier is not satisfied, the maximum grade is capped at **C** (score 60), regardless of the calculated score. This ensures that agents with fundamental safety gaps cannot receive a passing grade through volume of lower-severity controls.

### 6.5 Detailed Scoring

See [scoring.md](scoring.md) for worked examples and edge case handling.

---

## 7. Conformance Levels

### 7.1 Essential

**Requirements**:
- All CRITICAL-severity controls applicable to the agent's tier MUST pass
- No minimum score requirement

**Interpretation**: The agent has declared the most fundamental safety constraints. This is the minimum governance threshold for any deployed agent.

### 7.2 Standard

**Requirements**:
- All CRITICAL-severity controls applicable to the agent's tier MUST pass
- All HIGH-severity controls applicable to the agent's tier MUST pass
- Overall score MUST be >= 60

**Interpretation**: The agent has comprehensive governance declarations covering core safety, security, and oversight requirements. Appropriate for production agents that handle user data or perform consequential actions.

### 7.3 Hardened

**Requirements**:
- ALL controls applicable to the agent's tier MUST pass
- Overall score MUST be >= 75

**Interpretation**: The agent has declared governance coverage across all domains with no gaps. Appropriate for autonomous agents, agents in regulated environments, or agents that handle sensitive data.

### 7.4 Detailed Conformance

See [conformance.md](conformance.md) for the full conformance audit procedure and certification requirements.

---

## 8. Versioning

OASB-2 follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes to domain structure, scoring algorithm, or conformance level definitions
- **MINOR**: New controls, severity changes, new agent tiers (backward-compatible)
- **PATCH**: Clarifications, typo fixes, example improvements (no specification changes)

This document defines OASB-2 **v1.0**.

### 8.1 Stability Guarantees

- Control IDs (SOUL-XX-NNN) are permanent. A control ID is never reassigned to a different control.
- Domain numbers (11-19) are permanent. New domains receive the next available number.
- Severity changes are treated as MINOR version changes and require the process defined in CONTRIBUTING.md.

---

## Appendix A: Governance File Format

A conformant governance file is a Markdown document with the following recommended structure:

```markdown
# Agent Name - Governance

## Purpose
[Declared purpose and scope of the agent]

## Trust Hierarchy
[Who the agent trusts, in priority order]

## Capabilities
[What the agent can and cannot do]

## Safety Rules
[Immutable behavioral constraints]

## Data Handling
[How the agent treats sensitive data]

## Injection Hardening
[Defenses against prompt manipulation]

## Human Oversight
[When human approval is required]

## Transparency
[How the agent identifies itself and communicates uncertainty]

## Operational Limits
[Iteration caps, timeouts, budget limits]
```

This structure is a recommendation, not a requirement. Scanners detect controls by keyword matching, not by section structure. An agent can organize its governance file however it chooses, as long as the content satisfies the applicable controls.

---

## Appendix B: Relationship to Model Specifications

Model specifications (such as Anthropic's principal hierarchy or OpenAI's model spec) define how the foundation model should behave across all deployments. OASB-2 defines how a specific agent deployment should behave.

Key distinctions:

| Aspect | Model Specification | OASB-2 |
|--------|-------------------|-----|
| Scope | All uses of the model | One specific agent deployment |
| Author | Model provider | Agent developer or operator |
| Enforcement | Built into model weights and training | Declared in governance file, enforced by runtime |
| Portability | Tied to one model | Model-agnostic |
| Auditability | Opaque (training-time) | Transparent (file in repository) |

OASB-2 governance files can reference and build on model-level specifications. For example, an OASB-2 trust hierarchy might state "Follow the Anthropic principal hierarchy: developer > operator > user" while adding deployment-specific constraints.
