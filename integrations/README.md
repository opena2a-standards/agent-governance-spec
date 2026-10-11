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
[![Agent Governance](https://img.shields.io/badge/OASB--2-Conformant-teal)](https://github.com/opena2a-org/agent-governance-spec)
```

After running `scan-soul`, use the appropriate badge for your conformance level:

| Level | Badge |
|-------|-------|
| Essential | `![OASB-2 Essential](https://img.shields.io/badge/OASB--2-Essential-blue)` |
| Standard | `![OASB-2 Standard](https://img.shields.io/badge/OASB--2-Standard-teal)` |
| Hardened | `![OASB-2 Hardened](https://img.shields.io/badge/OASB--2-Hardened-green)` |

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

The sample below is a trimmed `scan-soul --json` run of hackmyagent 0.33.2 on `templates/tool-using.md`, copied to `SOUL.md` without edits. It keeps every top-level key. `domains` keeps two of its nine entries, and the first of them keeps two of its seven controls.

```json
{
  "hackmyagentVersion": "0.33.2",
  "file": "SOUL.md",
  "fileSize": 7542,
  "fileReadFailed": false,
  "agentTier": "TOOL-USING",
  "tierForced": false,
  "agentProfile": "tool-agent",
  "profileForced": false,
  "skippedDomains": ["Agentic Safety"],
  "domains": [
    {
      "domain": "Trust Hierarchy",
      "domainId": 11,
      "controls": [
        {
          "id": "SOUL-TH-001",
          "name": "Trust chain defined",
          "domain": "Trust Hierarchy",
          "keywords": ["trust", "authority", "principal", "hierarchy", "precedence", "priority"],
          "passed": true
        },
        {
          "id": "SOUL-TH-004",
          "name": "Principal identity verification",
          "domain": "Trust Hierarchy",
          "keywords": ["authenticate", "verify identity", "principal source", "identity verification", "authenticated principal", "identity claim"],
          "passed": false
        }
      ],
      "passed": 3,
      "total": 7,
      "percentage": 43
    },
    {
      "domain": "Agentic Safety",
      "domainId": 16,
      "controls": [],
      "passed": 0,
      "total": 0,
      "percentage": 0,
      "skippedByProfile": true
    }
  ],
  "score": 49,
  "rawScore": 49,
  "scoreClamped": false,
  "grade": "C",
  "level": "developing",
  "conformance": "essential",
  "criticalFloor": false,
  "criticalMissing": [],
  "totalControls": 57,
  "totalPassed": 25,
  "violations": [],
  "withheldLinks": [],
  "criticalMissingDetail": [],
  "coverage": {
    "measured": true,
    "examined": 57,
    "total": 57,
    "unit": "governance control"
  },
  "gate": {
    "failed": false,
    "reason": null,
    "exitCode": 0
  }
}
```

The scanner does not version this document. The keys in the table below carry the result, and they are the ones to code against. The other keys describe how the run was made (tier and profile detection, the file read, the score before clamping, coverage, violations), and a scanner release can add, rename or remove them. To read one of them, pin the scanner version (`npx hackmyagent@0.33.2 scan-soul --json`) and check `hackmyagentVersion`.

| Key | Value |
|-----|-------|
| `score` | An integer from 0 to 100. |
| `grade` | `A`, `B`, `C`, `D` or `F`. |
| `conformance` | `none`, `essential`, `standard` or `hardened`, in lower case. |
| `level` | `not-started`, `initial`, `developing`, `standard` or `hardened`. A label taken from the score alone, not a conformance level (see `conformance.md`). |
| `agentTier` | `BASIC`, `TOOL-USING`, `AGENTIC` or `MULTI-AGENT`. |
| `file` | The governance file that was scanned. |
| `criticalMissing` | The IDs of the critical controls that were not found. Any entry makes `conformance` `none`. |
| `gate` | `failed`, `reason` and `exitCode`: the verdict that the exit code reports. |
| `domains` | An array with one entry per domain: `domain`, `domainId`, `controls`, `passed`, `total` and `percentage`. A domain that the agent profile leaves out has `skippedByProfile: true` and no controls. |
| `domains[].controls` | An array with one entry per control the run checked: `id`, `name`, `domain`, `keywords` and `passed`. |

When no governance file is found (exit code 2), `score`, `conformance` and `file` are `null`, and `grade`, `level`, `agentTier`, `domains` and `criticalMissing` are absent.

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
