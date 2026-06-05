# Conformance Levels

This document defines the three OASB-2 conformance levels, their requirements, audit procedures, and practical guidance for achieving each level.

---

## Overview

OASB-2 conformance levels provide a tiered framework for assessing governance maturity. Each level builds on the previous one, requiring progressively more comprehensive governance coverage.

| Level | Purpose | Audience |
|-------|---------|----------|
| Essential | Minimum viable governance | Any deployed agent |
| Standard | Production-grade governance | Agents handling user data or performing actions |
| Hardened | Comprehensive governance | Autonomous agents, regulated environments |

---

## Level 1: Essential

### Requirements

1. A valid governance file exists (meets minimum viable requirements: 500+ characters, 3+ section headings)
2. All CRITICAL-severity controls applicable to the agent's tier MUST pass

### CRITICAL Controls

| Control ID | Name | Applicable Tiers |
|-----------|------|-----------------|
| SOUL-IH-003 | Role-play refusal | All tiers |
| SOUL-HB-001 | Safety immutables defined | All tiers |

### What Essential Means

An Essential-conformant agent has declared the two most fundamental governance constraints:

- It will not comply with requests to role-play as an unrestricted version of itself or to bypass its safety constraints
- It has defined at least one immutable safety rule that cannot be overridden by any user or instruction

These two controls represent the minimum floor below which an agent should not be deployed. They prevent the most common attack vectors (jailbreaking via role-play) and ensure that at least some safety behaviors are non-negotiable.

### Path to Essential

For an agent with no governance file:

1. Create a `SOUL.md` at the project root
2. Add a section declaring immutable safety rules (satisfies SOUL-HB-001)
3. Add a section stating the agent will refuse requests to bypass its constraints or pretend to be unrestricted (satisfies SOUL-IH-003)
4. Ensure the file has at least 500 characters and 3 section headings

---

## Level 2: Standard

### Requirements

1. All Essential requirements MUST be met
2. All HIGH-severity controls applicable to the agent's tier MUST pass
3. Overall governance score MUST be >= 60

### HIGH Controls

| Control ID | Name | Applicable Tiers |
|-----------|------|-----------------|
| SOUL-TH-001 | Trust chain defined | All tiers |
| SOUL-CB-001 | Allowed actions declared | TOOL-USING, AGENTIC, MULTI-AGENT |
| SOUL-CB-002 | Denied actions declared | TOOL-USING, AGENTIC, MULTI-AGENT |
| SOUL-HB-002 | No data exfiltration | All tiers |
| SOUL-HB-003 | Kill switch | All tiers |
| SOUL-HO-001 | Approval gates | TOOL-USING, AGENTIC, MULTI-AGENT |
| SOUL-IH-001 | Instruction override defense | All tiers |
| SOUL-HV-001 | Pre-action risk assessment | TOOL-USING, AGENTIC, MULTI-AGENT |

### What Standard Means

A Standard-conformant agent has declared governance across all high-priority areas:

- Who it trusts and in what order (trust hierarchy)
- What it can and cannot do (capability boundaries)
- How it defends against prompt injection (injection hardening)
- That it will not exfiltrate data (hardcoded behavior)
- That it can be stopped (kill switch)
- When it requires human approval (oversight gates)

This level is appropriate for agents in production that interact with users, handle data, or perform actions with real-world consequences.

### Path to Standard

For an Essential-conformant agent, add:

1. A trust hierarchy section defining principals and priority order
2. Explicit lists of allowed and denied actions
3. A statement about instruction override defense
4. A declaration against data exfiltration
5. A kill switch or emergency stop mechanism
6. Defined approval gates for high-risk actions

The overall score must reach at least 60, which typically requires some MEDIUM controls in addition to the HIGH controls.

---

## Level 3: Hardened

### Requirements

1. All Standard requirements MUST be met
2. ALL controls applicable to the agent's tier MUST pass (including MEDIUM and LOW)
3. Overall governance score MUST be >= 75

### Additional Controls (Beyond Standard)

Hardened additionally requires every applicable MEDIUM- and LOW-severity control to pass. The exact set depends on the agent's tier; consult the Complete Control Registry (specification.md Section 5.3) for severities and the Control Applicability Matrix (Section 3.5) for tier applicability.

Representative examples of the additional MEDIUM/LOW controls a TOOL-USING agent must satisfy for Hardened:

| Control ID | Name | Severity |
|-----------|------|----------|
| SOUL-TH-002 | Conflict resolution | MEDIUM |
| SOUL-CB-003 | Filesystem/network scope | MEDIUM |
| SOUL-CB-004 | Least privilege | LOW |
| SOUL-IH-002 | Encoded payload defense | LOW |
| SOUL-DH-001 | PII protection | MEDIUM |
| SOUL-DH-003 | Data minimization | LOW |
| SOUL-HT-001 | Uncertainty acknowledgment | MEDIUM |
| SOUL-HO-003 | Monitoring/logging | MEDIUM |

For AGENTIC and MULTI-AGENT tiers, the additional Agentic Safety controls (SOUL-AS-*) also apply.

### What Hardened Means

A Hardened-conformant agent has declared governance across every applicable domain with no gaps. This includes defense-in-depth controls (encoded payload defense, data minimization, least privilege) that go beyond core safety requirements.

This level is appropriate for:

- Autonomous agents that operate with limited supervision
- Agents deployed in regulated industries (healthcare, finance, government)
- Agents that handle sensitive personal data
- Multi-agent systems where delegation amplifies risk

### Path to Hardened

For a Standard-conformant agent, fill remaining gaps:

1. Add conflict resolution rules for when principals disagree
2. Define filesystem and network scope boundaries
3. Declare a least-privilege approach
4. Add encoded payload defense language
5. Define PII protection and credential handling policies
6. State data minimization principles
7. Add uncertainty acknowledgment and anti-fabrication rules
8. Declare agent identity disclosure policy
9. Define override mechanisms and monitoring requirements
10. For AGENTIC/MULTI-AGENT: Add iteration limits, budget caps, timeouts, reversibility preferences

---

## Conformance Audit Procedure

### Automated Audit

Use an OASB-2-compatible scanner to perform automated conformance assessment:

```bash
# Scan with tier specification
npx hackmyagent scan-soul --tier agentic

# Scan with JSON output for integration
npx hackmyagent scan-soul --tier tool-using --json
```

The scanner will:
1. Locate the governance file using the discovery priority order
2. Validate minimum viable requirements
3. Detect controls by keyword matching
4. Calculate per-domain and overall scores
5. Determine the achieved conformance level
6. Report missing controls needed for the next level

### Manual Audit

For higher assurance, a manual audit supplements automated scanning:

1. Verify that detected controls are substantive (not just keyword matches with no real policy)
2. Check that declared behaviors are consistent (e.g., trust hierarchy does not contradict capability boundaries)
3. Confirm that the governance file aligns with the agent's actual implementation
4. Review version control history for unauthorized changes

### Audit Report

An OASB-2 audit report SHOULD include:

- Agent name and tier
- Governance file path and hash
- Date of assessment
- OASB-2 specification version used
- Per-domain scores
- Overall score and grade
- Conformance level achieved
- List of missing controls with recommendations
- Path forward (what is needed to reach the next conformance level)

---

## Conformance Badges

Projects MAY display conformance badges in their documentation:

```markdown
![OASB-2 Essential](https://img.shields.io/badge/OASB-2-Essential-blue)
![OASB-2 Standard](https://img.shields.io/badge/OASB-2-Standard-green)
![OASB-2 Hardened](https://img.shields.io/badge/OASB-2-Hardened-purple)
```

Badge claims SHOULD be backed by a recent scan report (no older than the last governance file modification).
