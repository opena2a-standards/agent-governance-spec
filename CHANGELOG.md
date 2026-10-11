# Changelog

All notable changes to the Agent Behavioral Governance Specification (OASB-2)
are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Added

- `scripts/check_docs_prose.py`, the check for the two prose rules in the
  `CONTRIBUTING.md` style guide: no spaced double hyphen, em dash, or spaced
  en dash used as a dash, and no heading or bold label named "Why this
  exists" or "Why this matters". It reads the tracked Markdown files except
  `CHANGELOG.md`, the files under `examples/`, and the rendered crosswalk
  files, prints one `file:line: message` line per finding, and exits 1. A
  double hyphen or an en dash is a dash when a space, a tab, or the edge of
  the line is on each side of it. A heading is an ATX heading at any indent,
  a setext heading, or a bold label that starts a line. A code fence closes
  only at a run of its own character at least as long as the run that
  opened it. An argument that is not a directory prints a usage message and
  exits 2. Tests in `scripts/test_check_docs_prose.py`.
- `controls.json` at the repository root: the JSON control export named in
  `specification.md` section 8.2, one entry per control ID with `id`,
  `title`, `domain`, `severity`, `status`, `replacedBy` (deprecated entries
  only), and `version`. It is generated from the domain files by
  `scripts/check_crosswalks.py --write`, and the plain run requires the
  committed file to equal that render byte for byte, as it does for the
  rendered crosswalk `.md` files. The validator also checks each control's
  attribute table: the ID matches its heading, the severity and status are
  in their vocabularies, `Replaced by` is present on deprecated entries only
  and names another control, a `Replaced by` chain ends at an active
  control, so a cycle of deprecated controls is red (`specification.md`
  section 8.2), and a version is `MAJOR.MINOR.PATCH` in ASCII digits without
  leading zeros. An attribute table row outside ID, Severity, Applicable
  tiers, Status, Replaced by, and Version, a table row that is not an
  attribute row, an attribute row separated from its table, and a control in
  a domain file with no `# Domain N:` heading are reported. Tests in
  `scripts/test_check_crosswalks.py`.
- Control identifier stability rule (`specification.md` section 8.2): IDs are
  never reused or renumbered; a withdrawn control is deprecated with
  `replacedBy`; the status vocabulary `draft`, `active`, `deprecated` and the
  `version` attribute of an entry are adopted from the AI Agent Threat Matrix
  technique schema; the domain renumbering of 2026-06-05 (pull request #4;
  7 to 15 became 11 to 19) is the last one on record. Section 5.1 gains the
  Status and Replaced by attributes; section 5.3 states that every control is
  active.
- Label mapping (`specification.md` section 9): the single home of the mapping
  from the OASB corpus and Eval vocabularies onto OASB-2 controls, with the row
  shape for sensitivity labels reserved until a label registry is published.
- Export contract for the crosswalk CSV files (`crosswalks/README.md`): header,
  encoding, and how deprecated IDs appear.
- Static crosswalks from OASB-2 controls to NIST AI RMF 1.0 and to the EU AI
  Act (Regulation (EU) 2024/1689) under `crosswalks/`, rendered from canonical
  CSV files and checked by the stdlib validator `scripts/check_crosswalks.py`.
  The plain run requires each rendered crosswalk `.md` file, and
  `controls.json`, to equal its render byte for byte, and `--write` writes
  them with LF line endings on every platform; a crosswalk CSV with the
  header and no rows is rendered, compared, and written like any other.
  `.gitattributes` pins LF line endings for the crosswalk CSV and `.md`
  files and `controls.json`, so a checkout with `core.autocrlf=true` is
  green. A carriage return or a UTF-8
  BOM in one of these files is reported at its line in the words used for
  the CSV files, a byte that is not UTF-8 at its line, and a length
  difference only when the text, read with the BOM removed and CRLF and CR
  as LF, differs in length from the render, and a shorter or longer report
  on a file that had a BOM or a carriage return says the text was read that
  way. The reports that a file differs
  from its render, is shorter or longer than it, or holds a byte that is not
  UTF-8 name `python3 scripts/check_crosswalks.py --write`; the BOM and
  carriage-return reports do not.
- This changelog; version qualified to the spec-family ladder (1.0.0-draft).

### Changed

- README Related Work and `specification.md` section 1.3 state the OASB
  relationship with the OASB-1 count (46, published at oasb.ai) and the
  unified total (118, the sum 72 + 46, not measured on its own).
- README Scoring section aligned with `scoring.md` grades and `conformance.md`
  (removes the invented score-band "levels" vocabulary). (#7, 2026-07-02)

### Fixed

- Agent profiles are part of the specification (`specification.md` section
  3.6). The tier counts 29, 57, 69, and 72 hold only under a profile that
  skips no domain; `conversational`, `code-assistant`, and `tool-agent` skip
  whole domains, so a TOOL-USING file under `code-assistant` is measured on
  40 controls. Section 3.6 lists which domains each profile skips and why,
  and the applicable count for every tier and profile; sections 3.1 to 3.4,
  section 6, `scoring.md`, and the README state that the tier and the profile
  together decide the applicable set, and that a published score names both.
  Tests in `scripts/test_agent_profiles.py` hold the counts to the section
  3.5 matrix. (#48)
- The registry table in `specification.md` section 5.3 gives each control's
  heading title as its Name, as `controls.json` does; it differed for all 72
  controls: in wording for SOUL-HB-003, SOUL-AS-001, SOUL-AS-002,
  SOUL-AS-003, and SOUL-HT-002, and in letter case alone for the other 67.
  The validator now holds the table to the domain files.
- README Repository Structure lists `CHANGELOG.md`, `controls.json`,
  `scripts/`, and `integrations/`.
- The README Use cases section expands AAP as the Agent Authorization
  Protocol and no longer names a broker, a component the specification does
  not define. Tests in `scripts/test_check_crosswalks.py` require an acronym
  in parentheses in README.md to follow its expansion.
- The README use case that copies `templates/tool-using.md` includes the
  edit step before the scan, as Quick Start does, and states that an
  unedited template scans as partial coverage. `scripts/test_readme.py`
  checks that every README command block that copies a template edits it
  before scanning. (#27)
- README.md, `integrations/README.md`, and the GitHub Actions and GitLab CI
  examples under `integrations/` request JSON from `scan-soul` with
  `--json`. They passed `--format json`, which the scanner rejects as an
  unknown option, so both CI examples stopped before they read a score. The
  GitHub Actions example no longer writes stderr into `scan-result.json`,
  where the notice npm prints when it installs the scanner on a new runner
  made the file unreadable as JSON. `scripts/test_scan_soul_commands.py`
  checks that every `scan-soul` command in the Markdown and YAML files uses
  an option the scanner lists, and that a `--json` command keeps stderr out
  of its output. (#31)
- The minimum score in `integrations/github-action.yml` is read from the
  `MIN_GOVERNANCE_SCORE` repository variable, so the job fails when the score
  is below it. It was read from a `fail-below` input that the workflow never
  declared and that `pull_request` and `push` runs do not carry, so the
  minimum was always 0 and the check never failed. A minimum that is not a
  whole number fails the job with a message naming the variable, and
  `actionlint` reports nothing on the workflow.
  `integrations/README.md` shows how to set the variable, and
  `scripts/test_integrations.py` runs the check against scores below, at,
  and above the minimum. (#32)
- The domain table in the GitHub Action's pull request comment reads the
  scanner's `domains` array and gives each domain's `passed`/`total` and
  `percentage`. It read `domains` as an object keyed by domain name with a
  `found` count, which the scanner does not print, so every row would have
  shown the array index and `undefined/N (NaN%)`. Tests in
  `scripts/test_github_action.py` run the comment script on JSON in the
  scanner's shape. (#34)
- `integrations/README.md` documents the `scan-soul` exit codes as the
  scanner defines them. Exit `1` also means a CRITICAL control was not
  detected, with no `--fail-below` given, and covers `--ci` findings and
  usage errors; exit `2` covers a governance file that is missing,
  unreadable, or empty; exit `0` requires Essential conformance. Each case
  names its `gate.reason`. `scripts/test_integrations_readme.py` checks that
  each `gate.reason` is listed under the exit code the scanner gives it. (#36)
- The Standard level in `conformance.md` lists all 12 HIGH controls. Its
  table omitted SOUL-IH-004, SOUL-HB-005, SOUL-HB-008, and SOUL-HO-008, and
  the Path to Standard steps omitted those four and SOUL-HV-001; each step
  now names the control it satisfies, grouped by the tiers it applies to.
  `scripts/check_crosswalks.py` now requires the CRITICAL and HIGH tables to
  list every active control of that severity with the domain files' title
  and applicable tiers, in the order of `controls.json`, and each path to
  name every one of them. Tests in `scripts/test_check_crosswalks.py`. (#39)
- The `scan-soul` JSON sample in `integrations/README.md` is a trimmed run
  of hackmyagent 0.33.2. It had a `tier` key for `agentTier`, a top-level
  `controls` list, `domains` as an object, and upper-case conformance, and it
  left out `level`, `gate`, `coverage`, `criticalMissing` and the other keys
  the scanner prints. The guide now names the keys to code against, with
  their values, and the ones a scanner release can change.
  `scripts/test_readme.py` holds the sample to the scanner's key set and
  value vocabularies, and every key the table names to the sample. (#35)
- The conformance badge URLs in `conformance.md` and `integrations/README.md`
  returned "404: badge not found": shields.io splits a static badge path on
  single dashes, so `OASB-2-Essential-blue` had four parts. They now use the
  README's `OASB--2` form, which renders "OASB-2: Essential", and one colour
  per level in all three files: Essential blue, Standard teal, Hardened
  green. `scripts/test_readme.py` checks that every badge URL in the three
  files reads as label `OASB-2`, a message and a colour, and that each level
  has one colour. (#38)
- The README Adoption Path no longer labels `--fail-below 40` as Essential,
  or 60 and 75 as Standard and Hardened. Essential is both CRITICAL controls
  passing, with no minimum score: under hackmyagent 0.33.2 a governance file
  that scores 10 with both present scans as `essential`, and
  `--fail-below 40` fails it. The steps now say that `--fail-below 40` keeps
  grade C or better, that the scanner fails the job on a missing CRITICAL
  control without the flag, which is the Essential gate, that 60 and 75 are
  the minimum scores of Standard and Hardened, and that the level is read
  from the `conformance` field. `scripts/test_readme.py` checks that
  `README.md`, `integrations/README.md` and `conformance.md` label no score
  with a conformance level. (#47)
- The critical floor rule in `README.md`, `specification.md` section 6.4,
  and `scoring.md` caps the grade at C and leaves the overall score as
  calculated, as the scanner reports it. The three documents had promised an
  effective maximum score of 60, which the scanner does not apply: a file
  missing SOUL-HB-001 is reported with score 92 and grade C. Worked example 3
  in `scoring.md` now reports score 86 beside grade C.
  `scripts/test_critical_floor.py` checks that no document claims a score
  cap. (#42)
- The README introduction no longer states that OASB-2 provides runtime
  enforcement, which `specification.md` section 1.2 places out of scope. It
  states that coverage is measured through automated scanning and CI/CD
  checks of the governance file, and that runtime platforms enforce the
  declared behavior. `scripts/test_readme.py` checks that README.md claims no
  runtime enforcement. (#45)
- The GitLab CI example prints `Governance Score: NN/100 (Grade: X)` and
  enforces `MIN_GOVERNANCE_SCORE`. The job no longer declares
  `scan-result.json` as a `dotenv` report, which takes `KEY=VALUE` lines, and
  keeps the file under `artifacts: paths:`. Its `changes:` list adds
  `.github/copilot-instructions.md` and `.clinerules`, so it names all ten
  governance files the scanner searches. `scripts/test_gitlab_ci.py` runs the
  job's script against a stand-in that accepts only the scanner's options.
  (#37)
- SOUL-AS-004 (Reversibility Preference) applies to MULTI-AGENT only, as the
  `specification.md` section 3.5 matrix, the AGENTIC count of 69, and
  `templates/agentic.md` already had it. Its `Applicable tiers` row in
  `domains/16-agentic-safety.md` named AGENTIC as well, and `conformance.md`
  listed reversibility preferences among the AGENTIC additions; both now
  match the matrix. The validator reads the `Applicable tiers` attribute of
  every control, requires the section 3.5 matrix to mark the same tiers,
  and requires the Applicable controls count of each tier in sections 3.1 to
  3.4 to equal the number of controls that name it. Tests in
  `scripts/test_check_crosswalks.py`. (#40)
- The README Quick Start and Tools sections describe `harden-soul` as
  generating SOUL.md from templates, as the Adoption Path already did. They
  called it "guided prompts" and "interactive", but the command asks no
  questions: it appends a template section for each missing domain and
  creates SOUL.md when there is none. `scripts/test_readme.py` checks that
  no README description of `harden-soul` promises prompts or an interactive
  mode. (#46)
- The minimum score in the `integrations/README.md` examples for GitHub
  Actions and GitLab CI is 40, which keeps grade C or better, as the README
  Adoption Path has it. It was 60, the minimum score for Standard, which
  fails the job on `templates/tool-using.md` scanned as copied: hackmyagent
  0.33.2 scores that file 49. The guide says so and says when to raise the
  value. `scripts/test_readme.py` checks that no minimum the guide sets is
  above the score in its `scan-soul` sample, and that the sample's
  `fileSize` is the template's. (#53)
- The README domain table says that reversibility, among what Agentic Safety
  governs, is for MULTI-AGENT only, as SOUL-AS-004 is.
  `scripts/test_readme.py` checks that a README line naming reversibility
  names the tier. (#53)
- `examples/README.md` lists the three example files with the tier each
  declares, and says that a scanner run at the repository root reads them as
  governance files, so a finding under `examples/` describes the example. It
  names the one denied action of `coding-agent-soul.md` that hackmyagent
  0.33.2 `secure --ci` reports as a Remote Instruction Fetch, a false
  positive on a line that forbids the pattern. (#53)
- `scripts/test_gitlab_ci.py` fails, and names the program, when `bash` or
  `node` is not on PATH. It skipped the seven tests that run the job, so a
  machine without node passed the file with the job untested. (#53)
- The `scripts/test_readme.py` check on `harden-soul` descriptions matches
  the wording of an interactive mode (guided, interactive, wizard, asks,
  prompts you). It matched any use of "prompt" or "question", so a
  description such as "adds a section on prompt injection" would have
  failed. (#53)
- The `scoring.md` edge case for a missing governance file states that the
  score is withheld: no score and no grade are reported, the scanner reports
  that no governance file was found, and it exits with code 2, as
  `integrations/README.md` lists. The edge case used to promise a score of 0
  and a grade of F, which the scanner does not report: in its JSON output
  `score` is `null` and there is no `grade` field. `scripts/test_scoring.py`
  checks that the edge case promises no score or grade value and names the
  exit code `integrations/README.md` lists. (#44)
- README Repository Structure gives `specification.md` the version and
  status the file states, 1.0.0-draft and Draft, in place of "v1.0".
  `scripts/test_readme.py` holds the entry to the file's Version and Status
  lines. (#49)
- CONTRIBUTING.md names every path `scripts/check_docs_prose.py` does not
  read: it listed `CHANGELOG.md`, `examples/` and the rendered crosswalk
  files only, and left out `changelog.d/`, LICENSE files, the
  `node_modules/`, `vendor/`, `dist/` and `build/` trees, and the test,
  fixture, corpus, golden and snapshot directories.
  `scripts/test_check_docs_prose.py` checks that CONTRIBUTING.md names each
  exclusion the script defines. (#49)
- The `scripts/test_gitlab_ci.py` tests of a missing `bash` or `node`
  simulate a PATH that lacks exactly the programs they name. They deferred
  to the real PATH for the others, so on a machine with node but not bash
  the test of a missing node failed beside the error it expects. (#55)
- `scripts/check_docs_prose.py` checks a `README.md` in an examples
  directory, such as `examples/README.md`, which describes the examples to a
  person. It skipped every file under a directory named `examples`, so that
  page was never checked. The example governance files stay skipped. (#55)
- `CONTRIBUTING.md` names the command that runs the tests under `scripts/`,
  `python3 -m unittest discover -s scripts -p 'test_*.py'`, and says that
  the GitLab job tests need bash and node on PATH. (#55)
- The docstring of `scripts/check_docs_prose.py` gives the reason for each
  path the check does not read, as CONTRIBUTING.md says it does. It gave
  none for LICENSE files (a license is legal text reproduced word for word)
  or for the `node_modules/`, `vendor/`, `dist/` and `build/` trees
  (third-party or generated files). The exclusions are now a list of
  `path: reason` items, and `scripts/test_check_docs_prose.py` checks that
  every exclusion the script defines has an item with a reason. (#57)
- The `scoring.md` edge case for a governance file below the minimum
  requirements no longer covers an empty file. It said to score any file
  under 500 characters or 3 headings as 0, while `integrations/README.md`
  lists the empty file under exit code 2 as `governance-file-empty`, where
  no score is reported. The edge case now scores as 0 only a file that is
  not empty, and states that an empty file has its score withheld: no score
  and no grade are reported, and the scanner exits with code 2.
  `scripts/test_scoring.py` checks that the edge case withholds the empty
  file's score and names the exit code `integrations/README.md` lists. (#58)
- The `CONTRIBUTING.md` sentence that lists what
  `scripts/check_docs_prose.py` does not read no longer contradicts itself.
  It said the check reads `examples/README.md` and, in the same sentence,
  that it reads nothing in a directory named `example` or `examples`. The
  README exception now sits with the directory names: a `README.md` or
  `README.mdx` is read when the only directories of those names it is in are
  `example` or `examples` and its path is outside `node_modules/`,
  `vendor/`, `dist/`, `build/`, `changelog.d/` and `crosswalks/oasb-2-to-*`.
  `scripts/test_check_docs_prose.py` checks that the sentence naming the
  directories states the exception. (#60)
- `scripts/test_check_docs_prose.py` checks that CONTRIBUTING.md and the
  docstring of `scripts/check_docs_prose.py` both say that a `README.md` in
  an examples directory is read. Either statement could be deleted with
  every test still passing, which would leave a reader to conclude from the
  list of skipped directories that `examples/README.md` is not checked. (#61)
- The docstring of `scripts/check_docs_prose.py` says that a `README.mdx`,
  and a README in a directory named `example`, are read as well as a
  `README.md` in an `examples` directory, and that a path another item of
  its list excludes is not read even then. The test helper that finds a
  statement of the README exception counted a sentence such as "a
  `README.md` in an examples directory is not read, since only a tool reads
  it", where the verb belongs to another clause, and "it checks every file
  except `examples/README.md`". It now requires the verb to be in the
  clause that names the README. `scripts/test_check_docs_prose.py` checks
  that the docstring names both README files and both directory names, and
  that a README under an excluded prefix is not read. (#64)
- The docstring of `scripts/check_docs_prose.py` and `CONTRIBUTING.md` say
  that `node_modules/`, `vendor/`, `dist/` and `build/` are skipped only at
  the repository root, which is where the check matches them. Both now
  state that the README exception does not override the other exclusions,
  so `vendor/examples/README.md` is not read; `CONTRIBUTING.md` did not.
  The test of the README exception helper in
  `scripts/test_check_docs_prose.py` counted "is not read and only a tool
  reads it", "is not read when the checker reads the tree", "reads no
  README.md" and "checks every file other than" or "apart from
  `examples/README.md`" as statements that the README is read. A clause
  now counts only when it names the README, the directory and the verb
  between the same two breaks and holds none of "not", "no" and "never".
  The breaks are the edges of a sentence or parenthetical, a comma, a
  semicolon, a colon, and the words "except", "but", "since", "because",
  "unless", "although", "though", "whereas", "while", "other than" and
  "apart from"; "and" and "when" are not breaks. The test that the
  docstring names both directory names looked at the whole sentence, which
  also says "the examples", so it could not fail; it now looks at the clause
  that states the exception. New tests give one case per break, check that
  the docstring names both limits of the exception, and check that the
  break pattern splits a long run of spaces in linear time. (#66)
- The docstring of `scripts/check_docs_prose.py` says that `node_modules/`,
  `vendor/`, `dist/` and `build/` are skipped at the root of the checked
  directory, not at the repository root: a run with the ROOT argument `sub`
  skips `sub/vendor/`, which a run on the whole repository reads. It says
  that a README in an example or examples directory is read unless a
  directory of the list other than `example` or `examples` holds it; "another
  directory of this item" read as excluding `examples/pkg/examples/README.md`,
  which the check reads. `scripts/test_check_docs_prose.py` adds one case per
  word of the negation rule that only that word rejects, since no test failed
  when "never" was removed from the rule. The entry for #66 is broader than
  that change in two places. The earlier test of the directory names could
  not fail when the docstring dropped `examples`, and did fail when it
  dropped `example`. The new cases of one break each cover the comma, the
  semicolon, the colon and the 11 words; the cases for the edges of a
  sentence or parenthetical predate #66. (#68)
- The two tests in `scripts/test_check_docs_prose.py` that build a git
  repository add their files with `git add -f`. A global gitignore that
  listed `vendor/` made `git add` exit 1, and the test reported that as
  "git is not available" and skipped. A git command that fails now skips
  the test with the command and its error, and a new test runs both tests
  under a global ignore file that matches their files and fails on a skip.
  The docstrings of `excluded()` and `tracked_markdown()` in
  `scripts/check_docs_prose.py` say root-relative (relative to the checked
  directory), not repository-relative: a run with the ROOT argument `sub`
  names `sub/b.md` as `b.md`. The module docstring says that
  `CHANGELOG.md` and `changelog.d/` are skipped at the root of the checked
  directory, since a run on the whole repository reads `sub/CHANGELOG.md`
  and `sub/changelog.d/1.md`. The entry for #68 should have said that a
  README in an example or examples directory is read unless a directory
  named in that item, other than `example` or `examples`, holds it:
  `vendor/` is named in another item, and `examples/vendor/README.md` is
  read. It should also have said that the test adds one case per word,
  and one for a capitalized No. (#70)
- `scripts/test_check_docs_prose.py` adds a test that runs a git-based test
  with a `.gitconfig` git cannot parse and requires its skip reason to start
  with "git init -q failed:"; no test failed when that reason was replaced
  with "git is not available". The test of a global gitignore skips a
  failing git command with the command and its error, as the other git
  tests do, not with "git is not available", and writes
  `core.excludesFile` with `git config --file`. It used to format the path
  into a double-quoted value by hand, so a temporary directory whose path
  holds a backslash, as on Windows, made git reject the file and the test
  skipped; a new test runs it under such a directory. The module docstring
  of `scripts/check_docs_prose.py` says that the rendered crosswalk files
  are skipped at the root of the checked directory, since a run on the
  whole repository reads `sub/crosswalks/oasb-2-to-a.md`, and the test of
  each exclusion matched at the start of the path covers that prefix.
  `CONTRIBUTING.md` says that `CHANGELOG.md` and `changelog.d/` are skipped
  at the repository root. The entry for #70 should have said that a README
  in an example or examples directory is read unless a directory named in
  that item, other than `example` or `examples`, holds it and no other item
  of the list excludes its path: `vendor/examples/README.md` is not read.
  (#72)

## [1.0.0-draft] - 2026-03-03 (evolving draft through 2026-06-05)

### Changed

- Control set expanded from 30 to 72 to match the scanner; three control
  severities recalibrated for rubric consistency. (#5, #6, 2026-06-05)
- Behavioral domains renumbered to 11-19 and OASB-2 naming adopted. (#4)
- Renamed AGS → ABGS across all files. (#2)

### Added

- Domain 15: Harm Avoidance (4 controls). (#1)
- Initial specification: behavioral governance domains, control catalog,
  scoring model, conformance levels, templates, worked examples, and
  integrations. Domains 08-14 added; Honesty/Transparency and Human
  Oversight domains refined during initial drafting. (2026-03-03/04)
