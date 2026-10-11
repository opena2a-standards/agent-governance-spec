# OASB-2 Integrations

Ready-to-use integrations for enforcing the Agent Behavioral Governance Specification in your CI/CD pipeline.

## GitHub Actions

Copy `github-action.yml` to `.github/workflows/governance.yml` in your repo.

Features:
- Scans SOUL.md on every PR that modifies governance files
- Comments on PRs with governance score and domain breakdown
- Optional minimum score enforcement (set the `MIN_GOVERNANCE_SCORE` repository variable)
- Updates existing comments instead of creating duplicates

```yaml
# Minimal setup -- just copy the file:
cp integrations/github-action.yml .github/workflows/governance.yml
```

To set a minimum score, create the repository variable `MIN_GOVERNANCE_SCORE` (Settings > Secrets and variables > Actions > Variables), or from the command line:

```bash
gh variable set MIN_GOVERNANCE_SCORE --body 60
```

The "Check minimum score" step then fails the job when the score is below 60. Without the variable the minimum is 0, and the job reports the score without failing.

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
npx hackmyagent@latest scan-soul --json
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

Exit codes (the same with and without `--json`):
- `0`: Conformance is Essential or better (every CRITICAL control applicable to the tier was detected; see [conformance.md](../conformance.md)), and no flag failed the run. A low score alone does not fail a run; pass `--fail-below` to set a score floor.
- `1`: The run failed for one of these reasons:
  - A CRITICAL control was not detected, so conformance is none. `gate.reason` is `critical-control-missing`. This needs no `--fail-below` and is not a score threshold: a file that scores well above zero still exits `1` when a CRITICAL control is missing.
  - The score is below the `--fail-below` threshold.
  - With `--ci`, the scan reported a HIGH-severity SOUL finding: a governance violation, a profile mismatch, or an unrecognized `--profile` value.
  - A usage error, such as an unknown option.
- `2`: Nothing was measured, so no score is reported. This is not a failing grade. `gate.reason` names the case:
  - `no-governance-file`: no governance file was found.
  - `governance-file-unreadable`: a governance file was found but could not be read.
  - `governance-file-empty`: a governance file was found and is empty.

`gate` in the `--json` output reports the conformance check and the cases where nothing was measured. A run that fails only on `--fail-below` or `--ci` exits `1` while `gate.exitCode` is `0`, so gate a pipeline on the process exit status.
