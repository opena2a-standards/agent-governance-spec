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

## Relationship to Model Specifications

Anthropic's model specification addresses capability boundaries through the concept of "operator restrictions" -- operators can restrict model capabilities for their deployment. OASB-2 Capability Boundaries provide the declared format for these restrictions:

- SOUL-CB-001 and SOUL-CB-002 correspond to operator allowlists and denylists
- SOUL-CB-003 extends boundary definitions to filesystem and network scope, which model specifications do not typically address (they operate at a higher level of abstraction)
- SOUL-CB-004 applies the traditional security principle of least privilege to the agent context

OpenAI's function calling and tool use specifications define which tools are available to an agent, but do not standardize how the governance rationale is documented. OASB-2 provides that documentation layer.
