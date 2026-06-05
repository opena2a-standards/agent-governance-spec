# Domain 16: Agentic Safety

## Purpose

The Agentic Safety domain governs operational limits for agents that execute autonomously -- running multi-step workflows, iterating on tasks, invoking tools in loops, and operating over extended periods without continuous human supervision. It defines guardrails that prevent runaway execution, unbounded resource consumption, and irreversible actions.

## Rationale

A conversational agent that responds to one message at a time has natural limits: the user controls the pace and can stop at any point. An agentic system that plans and executes multi-step workflows loses this natural constraint. Without explicit operational limits, an agent can enter infinite retry loops, consume unbounded API tokens, run for hours without producing useful output, or take irreversible actions that cannot be undone.

These failures are not hypothetical. Agents that retry failing API calls indefinitely, agents that spend hundreds of dollars in token costs on a single task, and agents that delete production data while attempting to "clean up" are well-documented failure modes.

Agentic Safety controls provide the governance-level guardrails that complement runtime enforcement. Even if the runtime does not enforce these limits, declaring them in the governance file makes the agent's operational boundaries explicit and testable.

## Controls

### SOUL-AS-001: Iteration/Loop Limits

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-001 |
| **Severity** | MEDIUM |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a maximum number of iterations or loop cycles the agent may execute before pausing for human review or terminating. This prevents infinite loops, unbounded retries, and runaway execution. The limit should be specific to the agent's use case -- a code generation agent might allow 10 retry cycles, while a monitoring agent might allow 1000 check cycles.

**Detection keywords**: `iteration`, `loop`, `limit`, `maximum`, `cycle`, `repeat`, `bounded`, `max attempts`, `retry limit`, `loop limit`, `iteration cap`, `max iterations`, `max retries`

**Example compliant text**:
```
## Iteration Limits
This agent enforces the following iteration limits:
- Maximum 10 retry attempts for any single failing operation before reporting failure to the user
- Maximum 50 tool invocations per task before pausing for user review
- If a subtask fails 3 consecutive times with the same error, escalate to the user rather than retrying
- When operating in autonomous mode, report progress every 25 iterations
```

---

### SOUL-AS-002: Budget/Cost Caps

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-002 |
| **Severity** | LOW |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares cost or resource consumption limits for the agent's execution. This may include token budgets, API call limits, compute time caps, or monetary spending limits. The purpose is to prevent a single task from consuming unbounded resources.

**Detection keywords**: `budget`, `cost`, `spending`, `cap`, `token`, `expense`, `resource limit`, `cost limit`, `spending cap`, `token budget`, `resource budget`, `cost ceiling`

**Example compliant text**:
```
## Cost Controls
This agent operates within the following resource limits:
- Maximum 100,000 tokens per task (input + output combined)
- Maximum 20 external API calls per task execution
- If approaching 80% of any resource limit, notify the user and request approval to continue
- When a task exceeds its budget, save progress and present a summary of completed work rather than terminating abruptly
```

---

### SOUL-AS-003: Timeout Defined

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-003 |
| **Severity** | LOW |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a maximum execution duration for autonomous tasks. The agent should not run indefinitely without producing output or checking in with the user. The timeout should account for the agent's use case -- a quick code fix might have a 5-minute timeout, while a research task might allow 30 minutes.

**Detection keywords**: `timeout`, `time limit`, `duration`, `deadline`, `max time`, `time cap`, `time bound`, `execution time`, `wall clock`, `time constraint`, `maximum duration`

**Example compliant text**:
```
## Timeouts
This agent enforces the following time limits:
- Maximum 10 minutes of autonomous execution before reporting status to the user
- Individual tool calls time out after 60 seconds
- If a task cannot be completed within the time limit, save progress and present partial results
- Long-running tasks provide progress updates at regular intervals rather than running silently
```

---

### SOUL-AS-004: Reversibility Preference

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-004 |
| **Severity** | LOW |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares that the agent should prefer reversible actions over irreversible ones. When multiple approaches can accomplish a task, the agent should choose the approach that can be undone. Before taking irreversible actions (deleting files, sending emails, deploying code, modifying production data), the agent should seek explicit user confirmation.

**Detection keywords**: `reversible`, `undo`, `rollback`, `revert`, `non-destructive`, `recoverable`, `reversibility`, `undoable`, `backup`, `restore`, `destructive`, `irreversible`

**Example compliant text**:
```
## Reversibility
This agent prefers reversible actions:
- Before deleting files, create a backup or use version control to ensure recovery is possible
- Prefer git branches over direct commits to main; prefer staging environments over production
- Before executing destructive operations (drop table, rm -rf, force push), require explicit user confirmation with a description of what will be affected
- When modifying configuration files, preserve the original as a backup before writing changes
- If a reversible and irreversible approach both accomplish the task, choose the reversible approach
```

---

## Relationship to Model Specifications

Anthropic's model specification addresses agentic safety through its guidance on autonomous operation: agents should operate with appropriate caution, maintain human oversight, and avoid taking actions with large irreversible consequences. OASB-2 Agentic Safety provides the declared format for these principles:

- SOUL-AS-001 corresponds to Anthropic's guidance that agents should not take unbounded sequences of actions without human oversight
- SOUL-AS-002 extends the concept to resource consumption, which model specifications generally do not address because they operate at the behavioral level rather than the operational level
- SOUL-AS-003 complements SOUL-AS-001 with time-based limits in addition to iteration-based limits
- SOUL-AS-004 corresponds directly to Anthropic's principle of preferring reversible actions, which is explicitly called out in the model specification as a key agentic safety property

OpenAI's best practices for agentic systems recommend similar guardrails: bounded execution, human-in-the-loop for high-stakes actions, and graceful degradation when limits are reached. OASB-2 Agentic Safety controls standardize how these guardrails are documented.
