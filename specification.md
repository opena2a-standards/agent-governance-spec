# OASB-2: Agent Behavioral Governance Specification

**Version**: 1.0.0-draft (spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`)
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

Counts. OASB-2 has 72 controls in nine domains; the count is machine checked against the `### SOUL-XX-NNN:` headings under [domains/](domains/) by `scripts/check_crosswalks.py`. OASB-1 has 46 controls, published at oasb.ai; that count is not checked by this repository's validator. The unified total, 118, is the sum 72 + 46 and is not measured on its own; it changes when either term changes. OASB Eval scenarios are a separate count and are not part of any control total.

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
| **Status** | `draft`, `active`, or `deprecated`; absent means `active` (Section 8.2) |
| **Replaced by** | The ID of the successor control, present if and only if the status is `deprecated` (Section 8.2) |

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
| SOUL-TH-001 | Trust Chain Defined | Trust Hierarchy | HIGH |
| SOUL-TH-002 | Conflict Resolution | Trust Hierarchy | MEDIUM |
| SOUL-TH-003 | Operator/User Distinction | Trust Hierarchy | LOW |
| SOUL-TH-004 | Principal Identity Verification | Trust Hierarchy | MEDIUM |
| SOUL-TH-005 | Trust Hierarchy Documentation Complete | Trust Hierarchy | LOW |
| SOUL-TH-006 | Principal Authority Scope Defined | Trust Hierarchy | MEDIUM |
| SOUL-TH-007 | Trust Boundary Enforcement | Trust Hierarchy | MEDIUM |
| SOUL-TH-008 | Trust Policy Update Protocol | Trust Hierarchy | LOW |
| SOUL-CB-001 | Allowed Actions Declared | Capability Boundaries | HIGH |
| SOUL-CB-002 | Denied Actions Declared | Capability Boundaries | HIGH |
| SOUL-CB-003 | Filesystem/Network Scope | Capability Boundaries | MEDIUM |
| SOUL-CB-004 | Least Privilege | Capability Boundaries | LOW |
| SOUL-CB-005 | Permission Revocation Process Defined | Capability Boundaries | MEDIUM |
| SOUL-CB-006 | Capability Exposure Minimized | Capability Boundaries | MEDIUM |
| SOUL-CB-007 | Tool Integration Boundaries Declared | Capability Boundaries | MEDIUM |
| SOUL-CB-008 | Rate And Resource Limits Enforced | Capability Boundaries | MEDIUM |
| SOUL-CB-009 | Scope Validation At Invocation | Capability Boundaries | MEDIUM |
| SOUL-CB-010 | Capability Audit Trail Maintained | Capability Boundaries | LOW |
| SOUL-IH-001 | Instruction Override Defense | Injection Hardening | HIGH |
| SOUL-IH-002 | Encoded Payload Defense | Injection Hardening | LOW |
| SOUL-IH-003 | Role-Play Refusal | Injection Hardening | CRITICAL |
| SOUL-IH-004 | Input Validation And Sanitization | Injection Hardening | HIGH |
| SOUL-IH-005 | Output Encoding And Escaping | Injection Hardening | MEDIUM |
| SOUL-IH-006 | Multi-Layer Injection Defense | Injection Hardening | MEDIUM |
| SOUL-IH-007 | Injection Detection And Alerting | Injection Hardening | MEDIUM |
| SOUL-IH-008 | Adversarial Input Testing | Injection Hardening | LOW |
| SOUL-DH-001 | PII Protection | Data Handling | MEDIUM |
| SOUL-DH-002 | Credential Handling | Data Handling | MEDIUM |
| SOUL-DH-003 | Data Minimization | Data Handling | LOW |
| SOUL-DH-004 | Data Retention And Deletion Policy | Data Handling | MEDIUM |
| SOUL-DH-005 | Data Classification Framework | Data Handling | LOW |
| SOUL-DH-006 | Data Access Control Enforcement | Data Handling | MEDIUM |
| SOUL-DH-007 | Data Encryption Requirements | Data Handling | MEDIUM |
| SOUL-DH-008 | Data Breach Response Procedure | Data Handling | LOW |
| SOUL-HB-001 | Safety Immutables Defined | Hardcoded Behaviors | CRITICAL |
| SOUL-HB-002 | No Data Exfiltration | Hardcoded Behaviors | HIGH |
| SOUL-HB-003 | Kill Switch / Emergency Stop | Hardcoded Behaviors | HIGH |
| SOUL-HB-004 | Behavior Integrity Verification | Hardcoded Behaviors | MEDIUM |
| SOUL-HB-005 | Constraint Immutability Guarantee | Hardcoded Behaviors | HIGH |
| SOUL-HB-006 | Tamper Detection Mechanism | Hardcoded Behaviors | MEDIUM |
| SOUL-HB-007 | Safety Behavior Audit | Hardcoded Behaviors | LOW |
| SOUL-HB-008 | Enforcement Resilience Under Pressure | Hardcoded Behaviors | HIGH |
| SOUL-AS-001 | Iteration/Loop Limits | Agentic Safety | MEDIUM |
| SOUL-AS-002 | Budget/Cost Caps | Agentic Safety | LOW |
| SOUL-AS-003 | Timeout Defined | Agentic Safety | LOW |
| SOUL-AS-004 | Reversibility Preference | Agentic Safety | LOW |
| SOUL-AS-005 | Tool Dependency Limits | Agentic Safety | MEDIUM |
| SOUL-AS-006 | State Management Limits | Agentic Safety | MEDIUM |
| SOUL-AS-007 | Error Recovery Protocol | Agentic Safety | MEDIUM |
| SOUL-AS-008 | Task Isolation And Sandboxing | Agentic Safety | MEDIUM |
| SOUL-AS-009 | Resource Cleanup On Completion | Agentic Safety | LOW |
| SOUL-AS-010 | Concurrent Execution Coordination | Agentic Safety | LOW |
| SOUL-HT-001 | Uncertainty Acknowledgment | Honesty and Transparency | MEDIUM |
| SOUL-HT-002 | No Fabrication Rule | Honesty and Transparency | MEDIUM |
| SOUL-HT-003 | Identity Disclosure | Honesty and Transparency | MEDIUM |
| SOUL-HT-004 | Knowledge Boundaries Documented | Honesty and Transparency | MEDIUM |
| SOUL-HT-005 | Confidence Level Disclosure | Honesty and Transparency | LOW |
| SOUL-HT-006 | Training Data Recency Disclosed | Honesty and Transparency | LOW |
| SOUL-HT-007 | Limitations Acknowledged In Responses | Honesty and Transparency | MEDIUM |
| SOUL-HT-008 | Source Verification Practices | Honesty and Transparency | MEDIUM |
| SOUL-HO-001 | Approval Gates | Human Oversight | HIGH |
| SOUL-HO-002 | Override Mechanism | Human Oversight | MEDIUM |
| SOUL-HO-003 | Monitoring/Logging | Human Oversight | MEDIUM |
| SOUL-HO-004 | Approval Workflow And Escalation | Human Oversight | MEDIUM |
| SOUL-HO-005 | Action Notification Protocol | Human Oversight | MEDIUM |
| SOUL-HO-006 | Operator Identity Verification | Human Oversight | MEDIUM |
| SOUL-HO-007 | Audit Log Retention And Access | Human Oversight | LOW |
| SOUL-HO-008 | Escalation Triggers For Runaway Detection | Human Oversight | HIGH |
| SOUL-HV-001 | Pre-Action Risk Assessment | Harm Avoidance | HIGH |
| SOUL-HV-002 | Proportional Response | Harm Avoidance | MEDIUM |
| SOUL-HV-003 | Unintended Impact Awareness | Harm Avoidance | MEDIUM |
| SOUL-HV-004 | Ambiguity Resolution | Harm Avoidance | MEDIUM |

Every control in this registry is `active`. No control has been deprecated as of this version, so no `Replaced by` value exists yet (Section 8.2).

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

### 8.2 Control identifier stability

Section 8.1 makes a control ID permanent. This section states what permanence means for a reference held outside this repository, such as a crosswalk row, a scanner finding, or a machine readable governance entry that cites a control by ID.

- Form. An ID is `SOUL-XX-NNN`: `XX` is the letter code of the domain (TH, CB, IH, DH, HB, AS, HT, HO, HV) and `NNN` is assigned in sequence within the domain. The letter code is fixed per domain and is independent of the domain number, so a domain renumbering does not touch any control ID.
- No reuse, no renumbering. An ID that has appeared in a published version of this specification is never reassigned to a different control, never renumbered, and never removed from the registry in Section 5.3 or from its domain file. A new control takes the next unused `NNN` in its domain.
- Deprecation instead of deletion. A control that is withdrawn keeps its ID and its entry. Its status becomes `deprecated` and its entry carries `replacedBy`, the ID of the control that supersedes it. `replacedBy` is present if and only if the status is `deprecated`, and it names a control in the registry. Following `replacedBy` from a deprecated control, through any successor that is itself deprecated, ends at an `active` control: a chain that returns to a control already on it, or that ends at a `draft` control, is invalid. A deprecated control is not an applicable control for scoring (Section 6) or conformance (Section 7); the control its `replacedBy` names is, subject to that control's own status.
- Status vocabulary. `draft` (ID reserved and entry published; not applicable to any tier until it becomes `active`), `active` (in force), `deprecated` (withdrawn, with `replacedBy`). Absent means `active`. An entry may also carry `version`, the semantic version of the entry, where absent means 1.0.0. This vocabulary, the presence rule for `replacedBy`, and the `version` field are those of the AI Agent Threat Matrix technique schema (`schema/threat-matrix-v1.2.schema.json` in the agent-threat-matrix repository), adopted here so that a control ID and a technique ID follow one rule.
- Export. The machine readable JSON export of the controls is [controls.json](controls.json) at the repository root. Its `controls` array carries one entry per ID, in domain order and then by `NNN`, with the members `id`, `title` (the heading title), `domain` (the domain number), `severity`, `status`, `replacedBy` (deprecated entries only), and `version`, as camelCase members. `status` and `version` are written on every entry: an entry whose domain file gives no Status is written as `active`, and one that gives no version as `1.0.0`. The file is generated from the control headings and attribute tables of the domain files by `python3 scripts/check_crosswalks.py --write` and is not edited by hand. The crosswalk CSV files under [crosswalks/](crosswalks/) are the export of the crosswalk rows; their contract, including how deprecated IDs appear, is stated in [crosswalks/README.md](crosswalks/README.md).
- Validation. `scripts/check_crosswalks.py` holds the number of `### SOUL-XX-NNN:` headings under [domains/](domains/) to a constant (72 at this version) and requires every crosswalk row to name one of them. A deprecated control keeps its heading, so the constant counts every published ID, active or deprecated, and it moves only in the commit that adds a control. The same script requires each heading's attribute table to give its ID and a severity, a status from the vocabulary above where it gives one, and a version in `MAJOR.MINOR.PATCH` form where it gives one, and to carry no row other than ID, Severity, Applicable tiers, Status, Replaced by, and Version; requires `replacedBy` on every deprecated entry and on no other, naming another control heading, with the chain of successors ending at an `active` control; requires the registry table in Section 5.3 to give each control's ID, heading title, domain name, and severity as the domain files do, in the order of the export; and requires the committed [controls.json](controls.json) to equal its render from the domain files byte for byte.
- Record of renumberings. The behavioral domains were numbered 7 to 15 until pull request #4 (merged 2026-06-05), which made them domains 11 to 19 and adopted the OASB-2 name; no control heading changed in that commit, because the letter codes carried every ID across unchanged. The control set grew from 30 to 72 in pull request #5 (merged the same day) by adding IDs; none was removed or reassigned. The renumbering in pull request #4 is the last one on record. Section 8.1 makes domain numbers and control IDs permanent; a structural change is expressed by adding domains or controls and deprecating old ones, never by renumbering.

---

## 9. Label mapping

The Open Agent Security Benchmark (OASB) repository (`github.com/opena2a-org/oasb`) carries the vocabularies that name what a corpus sample or an Eval scenario is about. This section is the single home of the mapping from those vocabularies onto OASB-2 controls. The OASB repository cites this section in place of a copy of these tables; a row changes here or not at all.

### 9.1 Vocabularies

| Vocabulary | Values | Where defined |
|---|---|---|
| `label`, the ground truth class of a corpus sample | `malicious`, `benign`, `edge_case` | `src/benchmark/types.ts` (`GroundTruthLabel`) and the `label` member of every sample in `corpus/v2.json` |
| `category`, the attack category of a malicious sample | the nine values in Section 9.3 | `src/benchmark/types.ts` (`AttackCategory`, `ATTACK_CATEGORIES`) and `categoryCounts` in `corpus/v2.json` |
| Eval scenario family | `AT-AI`, `AT-PROC`, `AT-NET`, `AT-FS`, `AT-INT`, `AT-ENF`, `INT`, `BL`, `E2E` | the scenario ID prefixes of the test files under `src/`, indexed in the OASB README (What Gets Tested) |
| Sensitivity label | none published | Section 9.5 |

Ground truth classes carry no mapping: they state a verdict about a sample, not a subject that a control governs.

### 9.2 Mapping rule

- A row names one vocabulary value, the control IDs it maps to, and the basis of each mapping.
- Basis is one of two values. `declares`: the control requires the governance file to declare a rule whose subject is the value, that is, a defense or limit against the attack category, or the behavior the scenario family exercises. `related`: topical overlap only, not to be cited as evidence.
- A value with no control in either column is listed as unmapped, not omitted.
- Rows are informative. A row changes no control, severity, tier, scoring rule, or conformance level, and it does not state that a control detects or prevents the attack. Detection is what OASB measures of a security product; a control states what a governance file declares.
- Control IDs follow Section 8.2. A row entry for a deprecated control is kept and its successor is added beside it.
- A machine readable rendering of one mapping uses camelCase members: `{"vocabulary": "category", "value": "prompt_injection", "controlIds": ["SOUL-IH-001"], "basis": "declares"}`.

### 9.3 Attack categories

| Category | Declares | Related | Note |
|---|---|---|---|
| `prompt_injection` | SOUL-IH-001, SOUL-IH-006, SOUL-IH-007 | SOUL-IH-004, SOUL-TH-001, SOUL-TH-002 | Instruction override defense, defense in depth against injection, and injection detection; input validation and the trust chain that ranks instruction sources are related. |
| `unicode_stego` | SOUL-IH-002 | none | Encoded payload defense names Unicode homoglyphs and other obfuscation. |
| `social_engineering` | SOUL-IH-003, SOUL-TH-004, SOUL-HO-006 | none | Role play refusal, principal identity verification, and operator verification before privileged instructions. |
| `credential_exfiltration` | SOUL-DH-002, SOUL-HB-002 | none | Credential handling and the rule against transmitting data to unauthorized endpoints. |
| `data_exfiltration` | SOUL-HB-002 | SOUL-DH-001, SOUL-DH-003, SOUL-CB-003 | The rule against transmitting user data, conversation content, or retrieved information to unauthorized endpoints; PII handling, data minimization, and the endpoint scope are related. |
| `heartbeat_rce` | SOUL-CB-003 | SOUL-CB-002, SOUL-CB-007, SOUL-AS-008 | The network endpoints the agent may reach; denied actions, tool boundaries, and sandboxing are related. |
| `privilege_escalation` | SOUL-CB-004 | SOUL-CB-001, SOUL-CB-002, SOUL-CB-009, SOUL-TH-006 | Least privilege; the allowed and denied action lists, scope validation at invocation, and per principal authority scope are related. |
| `persistence` | SOUL-CB-003 | SOUL-HB-006, SOUL-HB-004, SOUL-AS-009 | The filesystem paths the agent may access; tamper detection and integrity verification of the agent's own safety rules, and cleanup on completion, are related. |
| `supply_chain` | none | SOUL-CB-007, SOUL-AS-005, SOUL-CB-006 | No control's subject is the provenance of a tool or skill package; tool integration boundaries, tool dependency limits, and minimized capability exposure are related. |

### 9.4 Eval scenario families

| Family | Scenarios exercise (OASB README, What Gets Tested) | Declares | Related |
|---|---|---|---|
| `AT-FS` | sensitive path access, access outside allowed paths, credential files, mass file creation, shell config modification | SOUL-CB-003 | SOUL-DH-002, SOUL-CB-008, SOUL-HB-006 |
| `AT-NET` | outbound connections, suspicious hosts, connection bursts, allowlist bypass, exfiltration destinations | SOUL-CB-003, SOUL-HB-002 | SOUL-CB-008 |
| `AT-PROC` | child process spawn, suspicious binaries, high CPU, privilege escalation, process termination | SOUL-CB-001, SOUL-CB-002 | SOUL-CB-004, SOUL-CB-008, SOUL-AS-008 |
| `AT-AI` | prompt input and output scanning, MCP tool call validation, A2A message scanning, pattern coverage | SOUL-IH-001, SOUL-IH-004, SOUL-CB-007, SOUL-TH-003 | SOUL-IH-005, SOUL-IH-007, SOUL-CB-009, SOUL-TH-004, SOUL-TH-007, SOUL-HB-002, SOUL-DH-002 |
| `AT-INT` | rule matching, anomaly scoring, LLM escalation, budget exhaustion, baseline learning | SOUL-IH-007, SOUL-HO-008 | SOUL-AS-002, SOUL-HO-003 |
| `AT-ENF` | log, alert, pause, kill, resume | SOUL-HB-003, SOUL-HO-003, SOUL-HO-005 | SOUL-HO-002 |
| `INT` | multi step chains: data exfiltration, MCP tool abuse, prompt injection, A2A trust exploitation, evasion, multi monitor correlation, budget exhaustion, kill switch and recovery | SOUL-HB-002, SOUL-CB-007, SOUL-IH-001, SOUL-TH-003, SOUL-HB-003 | SOUL-IH-007, SOUL-HO-003, SOUL-TH-007, SOUL-AS-007, SOUL-AS-002 |
| `BL` | false positive rates, anomaly injection, baseline persistence | none | none |
| `E2E` | live filesystem, process and network detection; interception of spawn, connect, read and write | the `AT-FS`, `AT-PROC`, and `AT-NET` rows | the `AT-FS`, `AT-PROC`, and `AT-NET` rows |

`BL` is unmapped: its scenarios measure whether a security product stays quiet during normal operation, which no governance declaration is about.

### 9.5 Sensitivity labels

A sensitivity label names a class of data (personal data, credentials, payment data, and so on) that a governance file declares rules for and that a grant or a served resource can carry. The normative home of sensitivity labels is the Agent Authorization Protocol: label semantics in AAP-SPEC section 4.4.2 and the label vocabulary in `registries/labels.json` of the agent-authorization-protocol repository, when published. Neither is published as of this version, so this section reserves the row shape and names the anchor controls; it carries no label rows. When the registry is published, its version is recorded here, and each of its entries receives a row of the form `label | control ids | basis` against these anchor controls, whose subjects are classes of data:

- SOUL-DH-001 (personally identifiable information)
- SOUL-DH-002 (credentials, secrets, and authentication material)
- SOUL-DH-005 (classification of data by sensitivity level)
- SOUL-DH-006 (data access control)
- SOUL-DH-007 (encryption of handled data)
- SOUL-HB-002 (no transmission to unauthorized endpoints)

A label value that is not in the published registry is not valid in a row.

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
