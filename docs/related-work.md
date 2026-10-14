# Related Work

How OASB-2 relates to other specifications for AI agents. The [README](../README.md) links here.

OASB-2 is designed to complement, not compete with, existing specifications:

- **Anthropic Soul / OpenAI Model Spec**: These govern the foundation model's behavior. OASB-2 governs the deployed agent built on top of that model. An agent can comply with OASB-2 regardless of which model it uses.
- **SoulSpec (soulspec.org)**: Defines agent persona and personality. OASB-2 defines agent governance. A SOUL.md can coexist with a SoulSpec persona file: they address different concerns.
- **Agent Skills (agentskills.io)**: Defines agent capabilities and procedural knowledge. OASB-2 defines behavioral constraints. Skills say what the agent can do; OASB-2 says what it must not do.
- **NIST AI Agent Standards**: Covers infrastructure, identity, and interoperability. OASB-2 covers behavioral safety. They are complementary layers.
- **AGENTS.md**: Instructions for AI coding agents about how to work with a codebase. OASB-2 defines safety and governance boundaries. An agent can follow both AGENTS.md (for coding conventions) and SOUL.md (for safety constraints).
- **OASB (Open Agent Security Benchmark)**: OASB-1 covers technical security (domains 1-10; 46 controls, published at oasb.ai). OASB-2 covers behavioral governance (domains 11-19; 72 controls, machine checked against the domain files by `scripts/check_crosswalks.py`). Together they form the unified OASB (domains 1-19) for full-stack agent security assessment; the total of 118 controls is the sum 72 + 46, not a separately measured count. OASB Eval scenarios are a separate count and are not part of any control total. The mapping from the OASB corpus and Eval vocabularies onto OASB-2 controls lives in [specification.md](../specification.md) Section 9.
- **Awesome Agent Souls**: A [curated collection of 100+ SOUL.md templates](https://github.com/opena2a-org/awesome-agent-souls) organized by role, industry, organization type, and fleet. Use these as starting points instead of writing governance files from scratch.

The informative crosswalk to NIST AI RMF 1.0 and the EU AI Act is described under Documentation in the [README](../README.md#documentation) and indexed in [crosswalks/README.md](../crosswalks/README.md).
