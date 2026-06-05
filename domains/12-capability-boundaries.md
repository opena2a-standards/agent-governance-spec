# Domain 12: Capability Boundaries

## Purpose

The Capability Boundaries domain governs what the agent is and is not allowed to do. It defines the agent's operational scope, including allowed actions, denied actions, filesystem and network boundaries, and the principle of least privilege.

## Rationale

An agent without declared capability boundaries has an implicit scope of "everything the underlying model and tools can do." This creates risk: a coding assistant that can also send emails, a research agent that can also modify files, or a customer service bot that can also access internal databases. Declaring explicit boundaries limits the blast radius of bugs, prompt injection, and misuse.

Capability boundaries are the behavioral counterpart to the principle of least privilege in traditional security. Just as a microservice should only have the database permissions it needs, an agent should only have the capabilities its purpose requires.

## Controls

### SOUL-CB-001: Allowed Actions Declared

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-001 |
| **Severity** | HIGH |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file explicitly lists the actions the agent is allowed to perform. This is a positive allowlist -- any action not listed is implicitly denied. The list should be specific to the agent's purpose (e.g., "read files, write files in the project directory, run tests" rather than "do anything helpful").

**Detection keywords**: `allow`, `permit`, `can do`, `authorized`, `capabilities`, `actions`, `tools`, `functions`, `enabled actions`, `may perform`, `allowlist`, `scope`

**Example compliant text**:
```
## Allowed Actions
This agent is authorized to perform the following actions:
- Read and write files within the current project directory
- Execute shell commands for building, testing, and linting
- Search the web for documentation and reference material
- Create and modify git commits on the current branch
```

---

### SOUL-CB-002: Denied Actions Declared

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-002 |
| **Severity** | HIGH |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file explicitly lists actions the agent must never perform. This is a denylist that serves as a safety net -- even if an action seems to fall within the agent's purpose, it is blocked if it appears on this list. The denylist should cover high-risk actions relevant to the agent's capabilities.

**Detection keywords**: `deny`, `prohibit`, `must not`, `cannot`, `forbidden`, `restricted`, `disallow`, `never`, `not allowed`, `blocked`, `denylist`, `must never`

**Example compliant text**:
```
## Denied Actions
This agent must never:
- Access files outside the current project directory
- Execute commands that modify system configuration
- Install packages or dependencies without user approval
- Push code to remote repositories without explicit instruction
- Access or modify environment variables containing credentials
```

---

### SOUL-CB-003: Filesystem/Network Scope

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-003 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file defines the filesystem paths and network endpoints the agent is allowed to access. This constrains the agent's reach beyond just what actions it can take, specifying where it can take them.

**Detection keywords**: `file`, `directory`, `path`, `network`, `endpoint`, `url`, `api`, `domain`, `port`, `filesystem`, `sandbox`, `boundary`, `working directory`

**Example compliant text**:
```
## Scope Boundaries
Filesystem:
- Read/write access: Current project directory and subdirectories only
- Read-only access: /usr/local/share/documentation/
- No access: Home directory dotfiles, /etc/, /var/, other projects

Network:
- Allowed: api.github.com, registry.npmjs.org, docs.python.org
- Denied: All other external endpoints unless explicitly approved by the user
```

---

### SOUL-CB-004: Least Privilege

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-004 |
| **Severity** | LOW |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a principle of least privilege -- the agent should request and use only the minimum permissions necessary to accomplish its task. When multiple approaches exist, the agent should prefer the one requiring fewer privileges.

**Detection keywords**: `least privilege`, `minimal`, `only needed`, `minimum necessary`, `principle of least`, `minimal access`, `narrowest`, `reduce privilege`

**Example compliant text**:
```
## Least Privilege
This agent operates under the principle of least privilege:
- Use read-only access when write access is not required
- Prefer targeted file reads over recursive directory scans
- Request user approval before escalating to higher-privilege operations
- Release temporary permissions after the task completes
```

---

### SOUL-CB-005: Permission Revocation Process Defined

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-005 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file defines a process to revoke and remove permissions granted to the agent. It must declare how access is disabled and how access is withdrawn promptly when a permission is no longer needed or is rescinded.

**Detection keywords**: `revoke`, `revocation`, `remove permission`, `disable access`, `withdraw access`, `permission removal`

**Example compliant text**:
```
## Permission Revocation
This agent supports a defined revocation process:
- Permissions may be revoked by the operator at any time
- On revocation, the agent must disable access and withdraw access promptly
- Permission removal takes effect before the next action is executed
```

---

### SOUL-CB-006: Capability Exposure Minimized

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-006 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file requires that capability exposure be minimized through an exposure limit. It must declare the use of selective exposure and controlled exposure so that only the capabilities required for the task are surfaced.

**Detection keywords**: `exposure limit`, `minimal exposure`, `capability exposure`, `selective exposure`, `controlled exposure`, `unexposed`

**Example compliant text**:
```
## Capability Exposure
This agent minimizes capability exposure:
- An exposure limit caps which capabilities are surfaced per task
- Selective exposure reveals only the tools required for the current request
- Controlled exposure keeps all other capabilities unexposed by default
```

---

### SOUL-CB-007: Tool Integration Boundaries Declared

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-007 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares the boundaries for integrated tools, including a tool boundary, tool scope, and tool limit. It must define the tool interface and the tool access control governing how the agent invokes each tool.

**Detection keywords**: `tool boundary`, `tool scope`, `tool limit`, `tool interface`, `tool access control`, `tool constraint`

**Example compliant text**:
```
## Tool Integration Boundaries
This agent declares boundaries for each integrated tool:
- A tool boundary and tool scope define what each tool may touch
- A tool limit caps invocation frequency and payload size
- The tool interface and tool access control govern every call
```

---

### SOUL-CB-008: Rate And Resource Limits Enforced

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-008 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file requires enforcement of a rate limit and rate limiting on agent operations. It must set a resource limit and declare throttle, quota, and usage limit controls to constrain consumption.

**Detection keywords**: `rate limit`, `rate limiting`, `resource limit`, `throttle`, `quota`, `bandwidth limit`, `usage limit`

**Example compliant text**:
```
## Rate and Resource Limits
This agent enforces rate limiting and resource limits:
- A rate limit caps requests per interval; excess calls throttle
- A resource limit and usage limit bound CPU, memory, and bandwidth
- A quota governs total operations per session
```

---

### SOUL-CB-009: Scope Validation At Invocation

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-009 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file requires that the agent validate scope at invocation. It must declare a scope check and scope validation that run before execution to confirm the requested action falls within declared boundaries.

**Detection keywords**: `validate scope`, `scope check`, `scope validation`, `boundary check`, `scope enforcement`, `permission check`

**Example compliant text**:
```
## Scope Validation
This agent validates scope at invocation:
- A scope check runs before every action is executed
- Scope validation confirms the request falls within declared boundaries
- A boundary check blocks any out-of-scope invocation
```

---

### SOUL-CB-010: Capability Audit Trail Maintained

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-CB-010 |
| **Severity** | LOW |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file requires that the agent maintain a capability audit and an audit trail. It must declare that actions are recorded in a capability log and usage log so that capability use can be reviewed.

**Detection keywords**: `capability audit`, `audit trail`, `capability log`, `usage log`, `execution log`, `action record`

**Example compliant text**:
```
## Capability Audit Trail
This agent maintains a capability audit:
- An audit trail records every capability invocation
- A capability log and usage log retain action records for review
- Each execution log entry includes the action, scope, and timestamp
```

---

## Relationship to Model Specifications

Anthropic's model specification addresses capability boundaries through the concept of "operator restrictions" -- operators can restrict model capabilities for their deployment. OASB-2 Capability Boundaries provide the declared format for these restrictions:

- SOUL-CB-001 and SOUL-CB-002 correspond to operator allowlists and denylists
- SOUL-CB-003 extends boundary definitions to filesystem and network scope, which model specifications do not typically address (they operate at a higher level of abstraction)
- SOUL-CB-004 applies the traditional security principle of least privilege to the agent context

OpenAI's function calling and tool use specifications define which tools are available to an agent, but do not standardize how the governance rationale is documented. OASB-2 provides that documentation layer.
