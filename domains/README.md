# Governance Domains

OASB-2 defines 9 behavioral governance domains, numbered 11-19. They extend OASB-1's technical security domains (1-10) to form the unified OASB domain set (1-19).

---

## Domain Index

| # | Domain | File | Controls | Focus |
|---|--------|------|----------|-------|
| 11 | Trust Hierarchy | [11-trust-hierarchy.md](11-trust-hierarchy.md) | 3 | Who the agent trusts and how it resolves conflicts between principals |
| 12 | Capability Boundaries | [12-capability-boundaries.md](12-capability-boundaries.md) | 4 | What the agent is allowed and denied to do |
| 13 | Injection Hardening | [13-injection-hardening.md](13-injection-hardening.md) | 3 | Defenses against prompt injection and instruction manipulation |
| 14 | Data Handling | [14-data-handling.md](14-data-handling.md) | 3 | Treatment of PII, credentials, and sensitive data |
| 15 | Hardcoded Behaviors | [15-hardcoded-behaviors.md](15-hardcoded-behaviors.md) | 3 | Immutable safety rules that cannot be overridden |
| 16 | Agentic Safety | [16-agentic-safety.md](16-agentic-safety.md) | 4 | Operational limits for autonomous execution |
| 17 | Honesty and Transparency | [17-honesty-transparency.md](17-honesty-transparency.md) | 3 | Truthfulness, uncertainty, and identity disclosure |
| 18 | Human Oversight | [18-human-oversight.md](18-human-oversight.md) | 3 | Approval gates, overrides, and monitoring |
| 19 | Harm Avoidance | [19-harm-avoidance.md](19-harm-avoidance.md) | 4 | Pre-action risk assessment, proportional response, unintended impact, ambiguity resolution |

---

## Severity Distribution

| Severity | Count | Controls |
|----------|-------|----------|
| CRITICAL | 2 | SOUL-IH-003, SOUL-HB-001 |
| HIGH | 8 | SOUL-TH-001, SOUL-CB-001, SOUL-CB-002, SOUL-IH-001, SOUL-HB-002, SOUL-HB-003, SOUL-HO-001, SOUL-HV-001 |
| MEDIUM | 13 | SOUL-TH-002, SOUL-CB-003, SOUL-DH-001, SOUL-DH-002, SOUL-AS-001, SOUL-HT-001, SOUL-HT-002, SOUL-HT-003, SOUL-HO-002, SOUL-HO-003, SOUL-HV-002, SOUL-HV-003, SOUL-HV-004 |
| LOW | 7 | SOUL-TH-003, SOUL-CB-004, SOUL-IH-002, SOUL-DH-003, SOUL-AS-002, SOUL-AS-003, SOUL-AS-004 |

---

## Relationship Between Domains

The 9 domains are designed to be orthogonal -- each addresses a distinct governance concern. However, some natural relationships exist:

- **Trust Hierarchy (11)** informs **Human Oversight (18)**: The trust hierarchy defines who can override whom, which determines the approval gate structure.
- **Capability Boundaries (12)** connect to **Hardcoded Behaviors (15)**: Denied actions (12) may overlap with safety immutables (15), but they serve different purposes. Denied actions can potentially be changed by operators; hardcoded behaviors cannot.
- **Injection Hardening (13)** supports **Trust Hierarchy (11)**: Injection defenses protect the trust chain from manipulation by untrusted inputs.
- **Data Handling (14)** connects to **Hardcoded Behaviors (15)**: The "no data exfiltration" rule (15) is a specific case of data handling policy (14), elevated to hardcoded status because of its severity.
- **Agentic Safety (16)** extends **Capability Boundaries (12)**: While capability boundaries define what the agent can do, agentic safety limits how much it can do in a single execution.
- **Harm Avoidance (19)** occupies a distinct position relative to existing domains:
  - **Capability Boundaries (12)** define what the agent _can_ do. **Harm Avoidance (19)** governs whether it _should_ in a specific context.
  - **Hardcoded Behaviors (15)** define absolute prohibitions. **Harm Avoidance (19)** governs the gray area between permitted and prohibited.
  - **Human Oversight (18)** defines when to ask a human. **Harm Avoidance (19)** governs the agent's own judgment before the question of human approval arises.
  - **Agentic Safety (16)** limits operational scope (iterations, budget, time). **Harm Avoidance (19)** assesses the qualitative risk of individual actions within those operational limits.
