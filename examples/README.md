# Examples

Three governance files for fictional agents, written out in full with no placeholders. They show how a finished `SOUL.md` reads. To start a file of your own, copy a template from [`templates/`](../templates/).

| File | Agent | Tier the file declares |
|------|-------|------------------------|
| [`chatbot-soul.md`](chatbot-soul.md) | Meridian Support, a customer service assistant for a health insurer | BASIC |
| [`coding-agent-soul.md`](coding-agent-soul.md) | Forge, a coding assistant in the developer's terminal | AGENTIC |
| [`data-pipeline-soul.md`](data-pipeline-soul.md) | Nexus, a data processing agent for a financial services firm | TOOL-USING |

## Scanner findings on these files

These files are governance files, and they are scanned and scored on purpose: a scanner pointed at the repository root reads them as it reads any governance file. A finding reported under `examples/` describes that example file. This repository runs no agent and has no governance file of its own.

A governance file states a prohibition by naming what it prohibits, and a scanner can report the named pattern as if the file used it. `npx hackmyagent@0.33.2 secure --ci`, run at the repository root, does this once. It reports this denied action of `coding-agent-soul.md` as CRITICAL, Remote Instruction Fetch:

> Execute minified, obfuscated, or downloaded-and-run code from untrusted sources (no curl | bash patterns)

The line forbids running downloaded code, so the finding is a false positive, and the line stays as it is. Report a finding like it to the scanner, [HackMyAgent](https://github.com/opena2a-org/hackmyagent/issues), not to this repository.

The same run reports the allowed shell commands of that file as HIGH, Broad Capabilities Without Consent Mechanism. The approvals the example requires are under its Approval Gates heading.
