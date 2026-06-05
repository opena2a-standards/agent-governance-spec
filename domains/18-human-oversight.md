# Domain 18: Human Oversight

## Purpose

The Human Oversight domain governs the mechanisms by which humans maintain control over AI agent behavior. It defines requirements for approval gates before high-stakes actions, override mechanisms for correcting or halting agent behavior, and monitoring capabilities for observing what the agent is doing.

## Rationale

Autonomous AI agents are designed to act independently, but independence without oversight creates unacceptable risk. An agent that deploys code, sends communications, modifies data, or makes purchases without human review can cause harm that is difficult or impossible to reverse. Even well-governed agents make mistakes -- they misunderstand context, encounter edge cases not covered by their governance, or operate on stale information.

Human oversight is not a limitation on agent capability; it is an architectural requirement for responsible deployment. The goal is not to approve every action (which would eliminate the efficiency gains of automation) but to establish approval gates at high-stakes decision points and maintain the ability to intervene when something goes wrong.

The consequences of insufficient human oversight are material: unauthorized financial transactions, data breaches from misconfigured tools, incorrect communications sent to customers, and production systems damaged by untested changes. These failures become harder to detect and correct the longer an agent operates without oversight.

## Controls

### SOUL-HO-001: Approval Gates

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-HO-001 |
| **Severity** | HIGH |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file defines specific actions or categories of actions that require human approval before execution. The agent must pause and request confirmation before taking these actions. Approval gates should be calibrated to the risk level -- routine operations proceed without approval, while high-stakes operations require explicit confirmation.

**Detection keywords**: `approval`, `confirm`, `human-in-the-loop`, `review`, `authorize`, `sign-off`, `gate`, `confirmation`, `ask before`, `require approval`, `user confirmation`, `explicit consent`, `permission`

**Example compliant text**:
```
## Approval Gates
This agent requires human approval before the following actions:
- Executing any command that modifies production systems or data
- Sending emails, messages, or other communications on behalf of the user
- Making purchases, financial transactions, or resource provisioning requests
- Deleting files, databases, or other persistent storage
- Publishing or deploying code to any environment
- Granting or modifying access permissions

Routine operations that do not require approval:
- Reading files and documentation
- Running tests in development environments
- Searching and retrieving information
- Generating code suggestions for user review
```

---

### SOUL-HO-002: Override Mechanism

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-HO-002 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares that humans can intervene in and override the agent's behavior at any point during execution. The override mechanism should be accessible, immediate, and not require technical expertise to invoke. The agent must respect overrides without resistance, argument, or delay.

**Detection keywords**: `override`, `intervene`, `manual`, `human control`, `takeover`, `escalat`, `hand off`, `correction`, `redirect`, `interrupt`, `course correct`, `manual control`, `human intervention`

**Example compliant text**:
```
## Override and Escalation
This agent supports human override at any point during execution:
- The user can redirect, correct, or cancel any in-progress task
- When overridden, the agent immediately stops its current action and awaits new instructions
- The agent does not argue against overrides or attempt to convince the user to let it continue
- If the agent encounters a situation outside its governance scope, it escalates to the user rather than making assumptions
- In multi-agent contexts, the human operator can override any agent in the system through the orchestrator
```

---

### SOUL-HO-003: Monitoring/Logging

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-HO-003 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares that the agent's actions are observable through monitoring and logging. The agent should produce a record of its actions, decisions, and tool invocations that is sufficient for a human to understand what the agent did and why. Logs should be accessible to operators and should not be suppressible by user instructions.

**Detection keywords**: `monitor`, `log`, `audit`, `track`, `observe`, `record`, `trace`, `accountability`, `audit trail`, `action log`, `observability`, `logging`, `audit log`, `event log`

**Example compliant text**:
```
## Monitoring and Logging
This agent maintains an observable record of its actions:
- Log all tool invocations with their parameters and results
- Log decision points where the agent chose between multiple approaches, including the rationale
- Logs are accessible to the operator and cannot be suppressed or redacted by user instructions
- In autonomous execution mode, produce a structured summary of all actions taken, ordered chronologically
- Sensitive data (credentials, PII) is redacted from logs in accordance with the Data Handling policy
```

---

## Relationship to Model Specifications

Anthropic's model specification places strong emphasis on human oversight as a foundational safety property. The specification states that humans should be able to adjust, correct, retrain, or shut down AI systems as needed. OASB-2 Human Oversight provides the declared format for these principles:

- SOUL-HO-001 (Approval gates) corresponds to Anthropic's guidance that agents should check in with users before taking consequential actions, especially those with irreversible effects
- SOUL-HO-002 (Override mechanism) corresponds to the principle that AI systems should not subvert human control and should be responsive to correction and redirection
- SOUL-HO-003 (Monitoring/logging) supports the broader principle that AI behavior should be transparent and auditable, enabling humans to understand and evaluate what the agent is doing

OpenAI's agentic safety guidelines similarly recommend human-in-the-loop confirmation for high-stakes actions and structured logging for auditability. Both specifications treat human oversight not as a constraint on agent capability but as a requirement for responsible deployment. OASB-2 Human Oversight controls standardize how these mechanisms are documented in governance files.
