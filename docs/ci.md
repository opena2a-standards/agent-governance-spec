# CI/CD Integration

Run the OASB-2 scan in a pipeline and show the conformance badge. The [README](../README.md) links here; [integrations/README.md](../integrations/README.md) is the full guide.

Enforce governance in your pipeline with zero configuration:

**GitHub Actions**. Add `.github/workflows/governance.yml`:

```yaml
# Scans SOUL.md on PRs, comments with governance score
# See integrations/github-action.yml for the full workflow; both pin the
# scanner release, so a new release changes the result only through a commit
name: Agent Governance Scan
on:
  pull_request:
    paths: ['SOUL.md', 'system-prompt.md', 'CLAUDE.md']
jobs:
  scan-soul:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npx hackmyagent@0.33.2 scan-soul --fail-below 40
```

**GitLab CI**, **pre-commit hooks**, and **npm scripts** examples are in [integrations/](../integrations/).

---

## README Badge

Show your governance conformance:

```markdown
[![OASB-2 Conformant](https://img.shields.io/badge/OASB--2-Standard-teal)](https://github.com/opena2a-org/agent-governance-spec)
```

| Level | Badge |
|-------|-------|
| Essential | ![OASB-2 Essential](https://img.shields.io/badge/OASB--2-Essential-blue) |
| Standard | ![OASB-2 Standard](https://img.shields.io/badge/OASB--2-Standard-teal) |
| Hardened | ![OASB-2 Hardened](https://img.shields.io/badge/OASB--2-Hardened-green) |
