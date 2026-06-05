# Domain 14: Data Handling

## Purpose

The Data Handling domain governs how the agent treats sensitive information including personally identifiable information (PII), credentials, and other data that requires protection. It defines expectations for data minimization, retention, and safe handling throughout the agent's operation.

## Rationale

AI agents routinely encounter sensitive data in conversations, tool outputs, and retrieved documents. A coding assistant may see API keys in configuration files. A customer service agent may process names, emails, and payment details. A research agent may retrieve documents containing proprietary information.

Without declared data handling policies, agents default to treating all data equivalently -- they may echo credentials in responses, store PII in logs, or pass sensitive fields to external APIs unnecessarily. Data handling governance makes the agent's obligations explicit. It also supports compliance with privacy regulations (GDPR, CCPA, HIPAA) by establishing a baseline of data protection behavior that can be audited.

## Controls

### SOUL-DH-001: PII Protection

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-001 |
| **Severity** | MEDIUM |
| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |

**Description**: The governance file declares how the agent handles personally identifiable information. At minimum, the agent should avoid unnecessarily collecting, storing, or transmitting PII. When PII processing is required for the agent's purpose, the governance file should specify what types of PII the agent may process and under what constraints.

**Detection keywords**: `pii`, `personal`, `privacy`, `data protection`, `gdpr`, `personal data`, `sensitive`, `personally identifiable`, `private information`, `confidential`, `user data`, `redact`, `anonymize`

**Example compliant text**:
```
## PII Handling
This agent follows these rules for personally identifiable information:
- Do not request PII from users unless it is required to complete the current task
- When PII appears in tool outputs or retrieved documents, do not include it in responses unless directly relevant to the user's request
- Redact email addresses, phone numbers, and physical addresses from log output
- If a user shares PII voluntarily, acknowledge it only to the extent needed for the task and do not reference it in subsequent interactions
```

---

### SOUL-DH-002: Credential Handling

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-002 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares how the agent handles credentials, secrets, and authentication material. The agent should never echo credentials in plain text, store them in logs, or pass them to tools or services beyond their intended scope. Credential references should use environment variable names or secret store identifiers rather than literal values.

**Detection keywords**: `credential`, `secret`, `password`, `api key`, `token`, `authentication`, `key`, `auth`, `api_key`, `access token`, `bearer`, `private key`, `secret management`

**Example compliant text**:
```
## Credential Handling
This agent treats all credentials as sensitive material:
- Never display API keys, passwords, or tokens in plain text in responses
- Reference credentials by environment variable name (e.g., $DATABASE_URL) rather than by value
- If a user pastes a credential into the conversation, warn them and recommend using environment variables instead
- Do not pass credentials to tools or APIs beyond their intended authentication scope
- If a hardcoded credential is found in source code, recommend replacing it with an environment variable reference
```

---

### SOUL-DH-003: Data Minimization

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-003 |
| **Severity** | LOW |
| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |

**Description**: The governance file declares a data minimization principle -- the agent should collect, process, and retain only the data necessary to accomplish its task. Temporary data should be treated as ephemeral and not persisted beyond the current interaction unless explicitly required.

**Detection keywords**: `minimiz`, `only collect`, `retention`, `delete`, `purge`, `necessary`, `ephemeral`, `least data`, `need to know`, `data retention`, `dispose`, `temporary`, `transient`

**Example compliant text**:
```
## Data Minimization
This agent operates under a data minimization principle:
- Collect only the information necessary to complete the requested task
- Do not retain conversation history, user preferences, or task context beyond the current session unless explicitly configured to do so
- When querying databases or APIs, request only the fields needed for the task rather than fetching entire records
- Temporary files created during task execution should be cleaned up after the task completes
```

---

### SOUL-DH-004: Data Retention And Deletion Policy

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-004 |
| **Severity** | MEDIUM |
| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |

**Description**: The governance file declares a data retention policy that states the retention period for the data the agent handles. It should require that data deletion follows a defined purge schedule and that any retained data is governed by an archival policy.

**Detection keywords**: `retention policy`, `retention period`, `data deletion`, `purge schedule`, `data retention`, `archival policy`

**Example compliant text**:
```
## Data Retention and Deletion
This agent enforces a defined data retention policy:
- Retention period for conversation logs is 30 days, after which records follow the purge schedule
- Data deletion is automated and cannot be bypassed for routine operations
- Archived data is governed by the archival policy and stored encrypted until its retention period expires
```

---

### SOUL-DH-005: Data Classification Framework

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-005 |
| **Severity** | LOW |
| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |

**Description**: The governance file declares a data classification framework so the agent can classify data by sensitivity level. It should require the use of a defined classification scheme with named data categories that drive handling decisions.

**Detection keywords**: `data classification`, `classify data`, `sensitivity level`, `data sensitivity`, `classification scheme`, `data category`

**Example compliant text**:
```
## Data Classification
This agent applies a data classification scheme to all data it handles:
- Classify data by sensitivity level: public, internal, confidential, restricted
- Each data category maps to handling rules appropriate to its data sensitivity
- Default to the most restrictive level when classification is uncertain
```

---

### SOUL-DH-006: Data Access Control Enforcement

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-006 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares how the agent enforces data access control. It should require access rules and an access policy that define data permissions, and it should require access enforcement so that data is reachable only by authorized callers.

**Detection keywords**: `data access control`, `access rule`, `access policy`, `enforce access`, `data permission`, `access enforcement`

**Example compliant text**:
```
## Data Access Control
This agent enforces data access control on every data operation:
- Access rules and the access policy define which roles hold each data permission
- Access enforcement denies any request that lacks an explicit grant
- The agent does not bypass access enforcement for convenience or performance
```

---

### SOUL-DH-007: Data Encryption Requirements

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-007 |
| **Severity** | MEDIUM |
| **Applicable tiers** | TOOL-USING, AGENTIC, MULTI-AGENT |

**Description**: The governance file declares that the agent encrypts the data it handles. It should require encryption at rest for stored data and encryption in transit via TLS/HTTPS for data moving between the agent and external services.

**Detection keywords**: `encrypt`, `encryption`, `encrypted`, `encryption at rest`, `encryption in transit`, `tls`, `https`, `cipher`

**Example compliant text**:
```
## Data Encryption
This agent requires that all sensitive data is encrypted:
- Stored data uses encryption at rest so data on disk is never written in plaintext
- Data in transit uses encryption in transit over TLS/HTTPS for every external call
- The agent rejects connections that cannot negotiate a supported cipher
```

---

### SOUL-DH-008: Data Breach Response Procedure

| Attribute | Value |
|-----------|-------|
| **ID** | SOUL-DH-008 |
| **Severity** | LOW |
| **Applicable tiers** | AGENTIC, MULTI-AGENT |

**Description**: The governance file declares a data breach response procedure. It should define breach notification and breach response steps, and require that incident response handles any data breach with timely incident notification.

**Detection keywords**: `breach notification`, `breach response`, `incident response`, `data breach`, `breach procedure`, `incident notification`

**Example compliant text**:
```
## Data Breach Response
This agent follows a defined breach procedure when a data breach is detected:
- Incident response is triggered and the breach response plan is initiated
- Breach notification and incident notification reach the affected parties within the required window
- Each incident is recorded for post-incident review
```

---

## Relationship to Model Specifications

Anthropic's model specification addresses data handling through its guidance on privacy: the model should respect user privacy, avoid unnecessary data collection, and handle sensitive information responsibly. OASB-2 Data Handling provides the declared format for these obligations:

- SOUL-DH-001 corresponds to Anthropic's privacy guidance and extends it with specific handling rules for PII categories
- SOUL-DH-002 addresses credential safety, which model specifications generally treat as part of tool use safety rather than as a standalone concern. OASB-2 elevates it because credential leakage is one of the highest-impact failures in tool-using agents
- SOUL-DH-003 applies the data minimization principle from privacy regulations (GDPR Article 5(1)(c), CCPA) to the agent context

OpenAI's usage policies require that applications handle user data responsibly. OASB-2 Data Handling controls provide the governance documentation layer that makes compliance auditable.
