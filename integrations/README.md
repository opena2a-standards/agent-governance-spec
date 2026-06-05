# OASB-2 Integrations

Ready-to-use integrations for enforcing the Agent Behavioral Governance Specification in your CI/CD pipeline.

## GitHub Actions

Copy `github-action.yml` to `.github/workflows/governance.yml` in your repo.

Features:
- Scans SOUL.md on every PR that modifies governance files
- Comments on PRs with governance score and domain breakdown
- Optional minimum score enforcement (set `fail-below` input)
- Updates existing comments instead of creating duplicates

```yaml
# Minimal setup -- just copy the file:
cp integrations/github-action.yml .github/workflows/governance.yml
```

To set a minimum score, add to your workflow:

```yaml
- name: Check minimum score
  env:
    MIN_SCORE: 60  # Require at least Standard conformance
```

## GitLab CI

Add the contents of `gitlab-ci.yml` to your `.gitlab-ci.yml`.

Set `MIN_GOVERNANCE_SCORE` variable to enforce a minimum:

```yaml
variables:
  MIN_GOVERNANCE_SCORE: "60"
```

## README Badge

Add a governance badge to your README:

```markdown
[![Agent Governance](https://img.shields.io/badge/OASB-2-Conformant-teal)](https://github.com/opena2a-org/agent-governance-spec)
```

After running `scan-soul`, use the appropriate badge for your conformance level:

| Level | Badge |
|-------|-------|
| Essential | `![OASB-2 Essential](https://img.shields.io/badge/OASB-2-Essential-blue)` |
| Standard | `![OASB-2 Standard](https://img.shields.io/badge/OASB-2-Standard-teal)` |
| Hardened | `![OASB-2 Hardened](https://img.shields.io/badge/OASB-2-Hardened-green)` |

## Pre-commit Hook

Add governance scanning to your git pre-commit hooks:

```bash
#!/bin/sh
# .git/hooks/pre-commit
# Scan SOUL.md if it was modified in this commit

if git diff --cached --name-only | grep -qE '^(SOUL\.md|system-prompt\.md|CLAUDE\.md)$'; then
  npx hackmyagent scan-soul --fail-below 40
fi
```

## npm Scripts

Add governance scanning to your package.json:

```json
{
  "scripts": {
    "governance": "hackmyagent scan-soul",
    "governance:fix": "hackmyagent harden-soul",
    "pretest": "hackmyagent scan-soul --fail-below 40"
  }
}
```

## Custom Integration

For any CI system, the core command is:

```bash
npx hackmyagent@latest scan-soul --format json
```

The JSON output includes:

```json
{
  "score": 67,
  "grade": "C",
  "conformance": "NONE",
  "file": "SOUL.md",
  "tier": "AGENTIC",
  "domains": {
    "Trust Hierarchy": { "found": 2, "total": 3 },
    "Capability Boundaries": { "found": 3, "total": 4 }
  },
  "controls": [
    { "id": "SOUL-TH-001", "name": "Trust chain defined", "passed": true },
    { "id": "SOUL-TH-002", "name": "Conflict resolution", "passed": false }
  ]
}
```

Exit codes:
- `0` -- Scan completed (check score for pass/fail)
- `1` -- Score below `--fail-below` threshold
- `2` -- No governance file found
