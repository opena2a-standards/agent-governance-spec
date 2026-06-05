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

### SOUL-AS-005: Tool Dependency Limits

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-005 |
| **Severity** | MEDIUM |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a dependency limit that bounds the dependency depth and the length of any dependency chain the agent may build between tools. It requires tool dependency to be made explicit, with dependency tracking and a dependency count so chained tool invocations remain bounded and observable.

**Detection keywords**: `dependency limit`, `dependency depth`, `dependency chain`, `tool dependency`, `dependency tracking`, `dependency count`

**Example compliant text**:
```
## Tool Dependency Limits
This agent bounds tool dependencies:
- Maximum dependency depth of 5 for any tool dependency chain
- Dependency tracking records the dependency count for each task
- If a dependency chain exceeds the dependency limit, pause and report to the user
```

---

### SOUL-AS-006: State Management Limits

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-006 |
| **Severity** | MEDIUM |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a state limit governing the agent's state management. It requires an explicit memory limit, context limit, and session state limit so that accumulated state, context, and per-session data remain bounded over long-running execution.

**Detection keywords**: `state limit`, `state management`, `memory limit`, `context limit`, `state size`, `session state limit`

**Example compliant text**:
```
## State Management Limits
This agent bounds its state:
- State management enforces a maximum state size per task
- Memory limit and context limit cap accumulated working state
- Session state limit bounds data retained across a single session
```

---

### SOUL-AS-007: Error Recovery Protocol

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-007 |
| **Severity** | MEDIUM |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file defines an error recovery approach with an explicit recovery protocol. It requires error handling that specifies retry logic and an error fallback so that failures are handled deterministically rather than left to undefined behavior.

**Detection keywords**: `error recovery`, `recovery protocol`, `error handling`, `retry logic`, `error fallback`, `recovery mechanism`

**Example compliant text**:
```
## Error Recovery Protocol
This agent defines a recovery mechanism:
- Error handling follows a documented recovery protocol for each failure class
- Retry logic bounds reattempts before invoking an error fallback
- On unrecoverable error, halt and report the failure to the user
```

---

### SOUL-AS-008: Task Isolation And Sandboxing

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-008 |
| **Severity** | MEDIUM |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file requires task isolation enforced through a sandbox and sandboxing of agent execution. It declares that tasks run as isolated execution within a defined execution boundary, with the isolation level stated explicitly so untrusted operations cannot affect other tasks or the host.

**Detection keywords**: `task isolation`, `sandbox`, `sandboxing`, `isolated execution`, `execution boundary`, `isolation level`

**Example compliant text**:
```
## Task Isolation and Sandboxing
This agent isolates execution:
- Each task runs as isolated execution inside a sandbox
- The execution boundary prevents one task from accessing another's resources
- The isolation level is documented for every tool that performs untrusted operations
```

---

### SOUL-AS-009: Resource Cleanup On Completion

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-009 |
| **Severity** | LOW |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file requires cleanup and resource cleanup when a task completes. It declares a finalization step and graceful shutdown carried out through a documented cleanup procedure and resource release so that temporary files, connections, and other resources do not leak between tasks.

**Detection keywords**: `cleanup`, `resource cleanup`, `finalization`, `resource release`, `graceful shutdown`, `cleanup procedure`

**Example compliant text**:
```
## Resource Cleanup on Completion
This agent cleans up after each task:
- A cleanup procedure runs on completion to perform resource release
- Finalization closes open connections and removes temporary files
- On termination, graceful shutdown ensures resource cleanup before exit
```

---

### SOUL-AS-010: Concurrent Execution Coordination

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-AS-010 |
| **Severity** | LOW |
| **Applicable tiers** | MULTI-AGENT |

**Description**: The governance file declares a concurrent limit governing concurrency across the fleet. It requires coordination to synchronize concurrent execution between agents and a parallel limit so that simultaneous tasks remain bounded and conflicting work can be serialized.

**Detection keywords**: `concurrent limit`, `concurrency`, `concurrent execution`, `coordination`, `serialize task`, `synchronize`, `parallel limit`

**Example compliant text**:
```
## Concurrent Execution Coordination
This agent bounds concurrency:
- A concurrent limit and parallel limit cap simultaneous concurrent execution
- Coordination across agents uses a shared lock to synchronize shared state
- Conflicting operations serialize task execution rather than running in parallel
```

---

## Relationship to Model Specifications

Anthropic's model specification addresses agentic safety through its guidance on autonomous operation: agents should operate with appropriate caution, maintain human oversight, and avoid taking actions with large irreversible consequences. OASB-2 Agentic Safety provides the declared format for these principles:

- SOUL-AS-001 corresponds to Anthropic's guidance that agents should not take unbounded sequences of actions without human oversight
- SOUL-AS-002 extends the concept to resource consumption, which model specifications generally do not address because they operate at the behavioral level rather than the operational level
- SOUL-AS-003 complements SOUL-AS-001 with time-based limits in addition to iteration-based limits
- SOUL-AS-004 corresponds directly to Anthropic's principle of preferring reversible actions, which is explicitly called out in the model specification as a key agentic safety property

OpenAI's best practices for agentic systems recommend similar guardrails: bounded execution, human-in-the-loop for high-stakes actions, and graceful degradation when limits are reached. OASB-2 Agentic Safety controls standardize how these guardrails are documented.
