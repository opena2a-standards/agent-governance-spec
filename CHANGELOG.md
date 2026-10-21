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
  a setext heading, or a bold label that starts a line. A code fence opens
  at a run of three or more backticks or tildes after at most three spaces,
  where no backtick follows a run of backticks on the line, and closes at a
  line that holds, after at most three spaces, only a run of its own
  character at least as long as the run that opened it, then nothing but
  spaces and tabs. Inside a list item or a block quote the spaces are counted
  from the column where its content starts, and the block ends with it; a
  line inside an HTML block opens no fence. An argument that is
  not a directory prints a usage message and exits 2. Tests in
  `scripts/test_check_docs_prose.py`.
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
  attribute row, an attribute row separated from its table, indented or not
  and with or without its leading pipe, and a control in a domain file with
  no `# Domain N:` heading are reported; a `# Domain N:` heading, a control
  heading or an attribute row inside a code block fenced by backticks or
  tildes is not read. In a domain file such a fence
  opens and closes only at a line indented by at most three spaces, counted
  inside a list item or a block quote from the column where its content
  starts, and closes only at a line with nothing but spaces and tabs after
  its run; a block inside a list item or a block quote ends with it, none
  opens inside an HTML block, and a run of backticks with a backtick after
  it on the line opens none. The line
  directly under the last row of an attribute table must be blank (empty, or
  spaces and tabs only): GFM renders a line there that is not blank as a row
  of the table unless the line starts another block, so such a line is
  reported at its line, a heading or a fence included. A domain file,
  `specification.md` and `conformance.md` are split into lines where GFM ends
  a line, at LF, CR LF, or CR, so a vertical tab, a form feed, U+001C to
  U+001E, U+0085, U+2028, or U+2029 does not end a line in them. A byte that
  is not UTF-8 in a domain file, `specification.md` or
  `conformance.md` is reported at its line, and the rest of the file is read
  with U+FFFD in its place. A domain or control heading with a long run of
  spaces inside its title is read in time linear in the length of the line.
  A `# Domain N:` heading, or an Applicable controls line of
  `specification.md` sections 3.1 to 3.4, whose number has more digits than
  Python converts to an integer (4300 unless the interpreter is configured
  otherwise) is reported at its line, and the number is not read. Tests in
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
  the CSV files, a byte that is not UTF-8 at its line, counted before
  carriage returns are read as LF, and a length
  difference only when the text, read with the BOM removed and CRLF and CR
  as LF, differs in length from the render, and a shorter or longer report
  on a file that had a BOM or a carriage return says the text was read that
  way. A crosswalk CSV that holds a byte that is not UTF-8 is not rendered.
  On a rendered `.md` file or `controls.json`, the reports of a BOM, a
  carriage return, a byte that is not UTF-8, a difference from the render,
  and a shorter or longer text name
  `python3 scripts/check_crosswalks.py --write`; the reports on a CSV file
  do not, as `--write` does not write the CSV files. The index statement,
  the basis definitions and the scope block are required verbatim in
  `crosswalks/README.md`, and the crosswalk bullet of the Documentation list
  in README.md, each in lines outside a code block fenced by backticks or
  tildes, which GFM renders as code; a fence there opens and closes as in a
  domain file. A copy inside such a block satisfied the requirement, so the
  bullet could be altered in the list GFM renders while a fenced copy of the
  unchanged bullet at the end of the file kept the run green. When the file
  holds such a text and each copy of it has a line inside such a block, the
  report says the text is missing or altered outside a fenced code block.
- `scripts/test_readme.py` reads the numbers the README states against
  their sources: each count of domains, controls and conformance levels
  ("nine behavioral domains", "72 controls", "the 72-control export",
  "three conformance levels") against the domain headings under `domains/`,
  the entries of `controls.json` and the `## Level N:` headings of
  `conformance.md`; the OASB-2 domain range against the domain headings and
  the OASB-1 range against `specification.md`; and the exit code the quick
  start gives `scan-soul` for each case against the exit code list in
  `integrations/README.md`.
- This changelog; version qualified to the spec-family ladder (1.0.0-draft).

### Changed

- README Related Work and `specification.md` section 1.3 state the OASB
  relationship with the OASB-1 count (46, published at oasb.ai) and the
  unified total (118, the sum 72 + 46, not measured on its own).
- README Scoring section aligned with `scoring.md` grades and `conformance.md`
  (removes the invented score-band "levels" vocabulary). (#7, 2026-07-02)
- The README is shortened to the quick start, the use cases, the tools, a
  Documentation list and the license; the quick start links `specification.md`
  first and states the exit codes of `scan-soul`. Its reference text moved
  as written: The Gap, Specification Overview, Agent Tiers, Scoring and
  Adoption Path to `docs/overview.md`; Related Work to
  `docs/related-work.md` (the crosswalk bullet stays in the README, where
  `scripts/check_crosswalks.py` requires it); CI/CD Integration and the
  badge to `docs/ci.md`; the conformance level table to `conformance.md`;
  and Repository Structure to `CONTRIBUTING.md`. The tests that read those
  passages now read them at their new paths. When that bullet is missing or
  altered, `scripts/check_crosswalks.py` names it the crosswalk bullet of the
  Documentation list, the README section that holds it, rather than the
  Related Work bullet.

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
  The validator now holds the table to the domain files. It reports a row
  with no closing pipe, and names the first row out of domain order, at its
  line, with the row it follows. A line that is not blank and does not start
  with a pipe, directly under the last row of this table, of the CRITICAL or
  HIGH table in `conformance.md` or of the section 3.5 matrix, is reported
  at its line: GFM renders it as a row of that table unless it starts
  another block, and the validator does not read it. The validator reads
  the headings of these four tables, of the Path to Essential and Path to
  Standard sections, and of the tier sections 3.1 to 3.4 only outside a
  code block fenced by backticks or tildes, which GFM renders as code, and
  reads each table from the first line after its heading that starts with
  a pipe outside such a block; a fence there opens and closes as in a
  domain file. A line inside such a block is not read as an Applicable
  controls count, and a line there that starts with `#` ends no path or
  tier section. A fenced example that repeated the section 5.3 heading and
  the registry table directly above that heading was read in place of the
  table GFM renders under it, so a severity changed in that table was not
  reported.
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
  that item, other than `example` or `examples`, holds it or another item
  of the list excludes its path: `vendor/examples/README.md` is not read.
  (#72)
- The entry for #72 joined the two limits of the README exception with
  "and no other item of the list excludes its path", which reads as if a
  README were skipped only when both held; either one keeps the README from
  being read, and the entry now joins them with "or", as the docstring of
  `scripts/check_docs_prose.py` does. A test in
  `scripts/test_check_docs_prose.py` holds the entry to that wording.
  `.gitignore` lists `secrets.json` beside the other credential files it
  ignores, and a test in `scripts/test_gitignore.py` checks that git
  ignores a `secrets.json` at the root and in a subdirectory. (#74)
- The class docstring of the `.gitignore` tests in
  `scripts/test_gitignore.py` said that a secrets file is never committed by
  accident, but the tests check only the name `secrets.json`: git does not
  ignore `secrets.yaml`, and `git add -f` still adds an ignored file. The
  docstring now says that git ignores `secrets.json` at the root and in a
  subdirectory, and a test in the same file holds it to that wording. (#76)
- The test that holds the class docstring of the `.gitignore` tests to its
  wording checked that the sentence was present and that two phrases of the
  docstring that #76 replaced, "never committed" and "A secrets file", were
  absent, so a docstring that appended a broader claim, such as "so no
  secrets file can reach a commit", still passed. The test now requires the
  whitespace-normalised docstring to equal "git ignores secrets.json at the
  root and in a subdirectory." (#80)
- The tests that read a docstring, in `scripts/test_gitignore.py` and
  `scripts/test_check_docs_prose.py`, raised an error under `python3 -OO`,
  which strips docstrings and leaves `__doc__` as `None`. Each now skips
  with the reason that `python3 -OO` strips docstrings, and a test in each
  file runs that file under `python3 -OO` and checks that it passes with
  those skips. The skip applies only under `python3 -OO`: without it, a
  test that reads a docstring missing from the source reports an error,
  and a test in each file sets one docstring to `None` and checks that the
  test reading it reports an error, not a skip.
  `scripts/test_stripped_docstrings.py` runs each `scripts/test_*.py` file
  under `python3 -OO` and checks that it passes. (#81)
- The entry for #80 said that the earlier test of the class docstring of the
  `.gitignore` tests "checked only that the sentence was present". That test
  also checked that the phrases "never committed" and "A secrets file" were
  absent, and the entry now says so. A test in `scripts/test_gitignore.py`
  holds the entry to that wording. (#83)
- `.pre-push-review-not-required` named `python3 scripts/check_crosswalks.py`
  and `python3 scripts/test_check_crosswalks.py` as the repository's checks,
  while `CONTRIBUTING.md` runs every `scripts/test_*.py` file with
  `python3 -m unittest discover -s scripts -p 'test_*.py'` and also asks for
  `python3 scripts/check_docs_prose.py`. The note now names the two check
  scripts and that test command, and `scripts/test_pre_push_note.py` holds
  it to every `scripts/check_*.py` script and to the test command of
  `CONTRIBUTING.md`. (#85)
- The tests in `scripts/test_gitignore.py` and
  `scripts/test_check_docs_prose.py` that run their own file again under
  `python3 -OO` started that run with no timeout, so a run that stopped
  responding stalled the whole suite. Each now passes `timeout=300`, as
  `scripts/test_stripped_docstrings.py` does, and a test there checks that
  each `python3` run a test starts passes a timeout. The two tests in
  `scripts/test_check_docs_prose.py` that hold a scan to 2.0 seconds also
  ran in each `python3 -OO` run of that file, where a loaded machine could
  fail them; they now skip under `python3 -O` and `-OO`, and only the run
  without `-O` checks the bound. The test in
  `scripts/test_check_crosswalks.py` that holds a match to 1.0 second also
  ran when `scripts/test_stripped_docstrings.py` ran that file under
  `python3 -OO`; it now skips under `python3 -O` and `-OO` too, and only
  the run without `-O` checks its bound. `scripts/test_stripped_docstrings.py`
  also runs each `scripts/test_*.py` file under `python3 -O`, which keeps
  docstrings, and checks that it passes with no skip whose reason names
  `python3 -OO`, so a guard written as `sys.flags.optimize >= 1` instead of
  `>= 2` fails. (#87)
- The helper of `scripts/test_pre_push_note.py` that reads the test command
  of `CONTRIBUTING.md` was named `test_command`, so pytest ran it as a test,
  counting one test more than `python3 -m unittest discover` and warning
  that it returned a value. It is now `discover_command`, and a test checks
  that no module-level function of the file has a name that starts with
  `test`. The same file checked that the note held the test command as a
  substring, so a note that narrowed it with `-k crosswalks` passed; the
  text from `python3 -m unittest` up to the next `;` must now equal the
  command. The test of the entry for #80 in `scripts/test_gitignore.py`
  reported a `ValueError` when the opening words of the entry or its
  `(#80)` marker were missing; it now reports a failure that names the
  entry. The module docstring of that file describes each of its test
  classes, says that the tests read the files in the working tree, not the
  committed ones, and a test checks that it names each test class. The
  repository structure in `README.md` listed 7 of the 14
  `scripts/test_*.py` files; one `test_*.py` row now stands for all of
  them, and a test in `scripts/test_readme.py` checks that each script
  under `scripts/` is listed by name or pattern. (#89)
- The tests in `scripts/test_check_crosswalks.py` and
  `scripts/test_check_docs_prose.py` that check that the time bounds skip
  under `python3 -O` and `-OO` checked only that each timed test was
  reported as skipped, so a skip placed after the timed call still passed
  while the bound ran again in those runs. They now replace the clock of
  their file with one that fails the test that reads it, and check that it
  is not read. The test in `scripts/test_check_docs_prose.py` that checks
  that the run without `-O` keeps the time bounds now replaces `skipTest`
  and checks that it is not called, as its counterpart in
  `scripts/test_check_crosswalks.py` does, so a helper that skipped without
  `-O` fails that test instead of being reported as a skip. The entry for
  #87 said that a test in `scripts/test_stripped_docstrings.py` checks that
  each `python3` run a test starts passes a timeout, but it checked only a
  `subprocess.run` call whose command was a list that starts with
  `sys.executable`. It now requires each use of `subprocess.run`, `call`,
  `check_call` and `check_output` in a `scripts/test_*.py` file to be a
  call that passes a timeout, whatever its command, and reports each use
  of `subprocess.Popen`, `getoutput` and `getstatusoutput`, which take no
  timeout, and each import of `subprocess` under another name or of names
  from it. The shell runs in `scripts/test_gitlab_ci.py` and
  `scripts/test_integrations.py` and the git runs in
  `scripts/test_check_crosswalks.py`, `scripts/test_check_docs_prose.py`
  and `scripts/test_gitignore.py` now pass `timeout=60`. The `python3 -O`
  run of `scripts/test_stripped_docstrings.py` that the file starts ran
  each test file under `python3 -OO` a second time; it now starts with
  `ABGS_PYTHON3_O_RUN` set, and the test that runs each file under
  `python3 -OO` skips in a `python3 -O` run where it is set. (#91)
- A `python3 -m unittest discover -s scripts -p 'test_*.py'` run still ran
  `scripts/test_gitignore.py` and `scripts/test_check_docs_prose.py` under
  `python3 -OO` three times: once from the test of each file that runs the
  file again under `python3 -OO`, once from
  `scripts/test_stripped_docstrings.py`, and once more from that same test
  of the file inside the `python3 -O` run that
  `scripts/test_stripped_docstrings.py` starts. That test now skips in a
  `python3 -O` run where `ABGS_PYTHON3_O_RUN` is set, so the discover run
  runs each of the two files under `python3 -OO` twice. The `python3 -O`
  runs that `scripts/test_stripped_docstrings.py` starts now record each
  process the test file starts, and the test checks that none of them is a
  `python3 -OO` run. The check there that each `subprocess` run in a test
  file has a timeout rejected only a literal `timeout=None`, so a timeout
  held in a name bound to `None` passed; it now accepts only a number
  written in the call. The entry for #89 said that a test checks that no
  function of `scripts/test_pre_push_note.py` has a name that starts with
  `test`, but the test checks only module-level functions, and the test
  methods of that file start with `test`. The entry now says "no
  module-level function", and a test in that file holds it to that
  wording. (#93)
- The entry for #93 said that the `python3 -O` runs of
  `scripts/test_stripped_docstrings.py` record each process a test file
  starts, which reads as the runs of that file under `python3 -O`. The
  runs that record are the `python3 -O` runs of each test file that
  `scripts/test_stripped_docstrings.py` starts, and the entry now says so;
  a test in that file holds it to that wording. (#95)
- The check in `scripts/test_stripped_docstrings.py` that each
  `subprocess` run in a test file has a number written in the call as its
  timeout accepted only a single number literal, so `timeout=5 * 60` and
  `timeout=-1` were reported as "a timeout that is not a number". It now
  also accepts unary `+` and `-`, and `+`, `-`, `*` and `/`, applied to
  int and float literals; `**` is not accepted. A timeout held in a name,
  or an expression that reads one, is still reported, now as "a timeout
  that is not a number written in the call". (#96)
- That check accepted unary `+` and `-`, and `+`, `-`, `*` and `/`,
  applied to int and float literals, without evaluating the expression, so
  `timeout=60 / 0`, which raises `ZeroDivisionError` when the call runs,
  passed. It now evaluates the written expression and accepts it only when
  the value is a finite number that fits in a float: a division by zero, a
  float that overflows to infinity or yields NaN, such as `1e400` or
  `1e308 * 10 - 1e308 * 10`, and an int too large for a float are reported
  as "a timeout that is not a number written in the call". (#98)
- The test of that check for a timeout that is not a finite number did
  not hold the evaluation of `/`, binary `+`, or unary `+` and `-`: a
  check that evaluated `/` as `//`, binary `+` as `-`, unary `+` as `-`,
  or unary `-` as `+` passed every test in
  `scripts/test_stripped_docstrings.py` while it accepted
  `timeout=1 / (1 / 2 - 0.5)`, `timeout=1 / (1 + -1)`,
  `timeout=1 / (1 - +1)`, or `timeout=1 / (1 + -1)` respectively, each of
  which raises `ZeroDivisionError` when the call runs. The test now also
  requires `1 / (1 / 2 - 0.5)`, `1 / (1 + -1)` and `1 / (1 - +1)` to be
  reported. (#103)
- The comment on the test for #98 said that none of the runs in that test
  has a number written in the call as its timeout, but the last run,
  `timeout=60 / 2`, bounds the run at 30 seconds, and the test expects it
  to be accepted. The comment now names that run as the accepted control,
  and a test in `scripts/test_stripped_docstrings.py` holds it to that
  wording. (#101)
- The docstring of `written_number` in `scripts/test_stripped_docstrings.py`
  said that it accepts an expression that "evaluates to a finite number",
  but it also rejects an int too large for a float, which is a finite
  number. The docstring now says "a finite number that fits in a float", as
  the entry for #98 does, and a test in the same file holds it to that
  wording. (#102)
- The tests of the timeout check in `scripts/test_stripped_docstrings.py`
  did not hold the evaluation of `*` or of binary `+` and `-`: a check
  that evaluated `*` as `**`, or binary `+` or `-` as `%`, passed every
  test in that file. It accepted `timeout=1 / (5 * 0)`, which raises
  `ZeroDivisionError` when the call runs, and reported
  `timeout=1 / (2 + 1)` or `timeout=1 / (3 - 1)`, which bound the run.
  The tests now require `1 / (5 * 0)` to be reported and
  `1 / (3 - 1)` and `1 / (2 + 1)` to be accepted, and a new test checks
  that evaluating any of `+`, `-`, `*` and `/` as another of `+`, `-`,
  `*`, `/`, `//`, `%` and `**`, or unary `+` and `-` as each other, fails
  one of those tests. The module docstring of that file now names the
  docstring of `written_number` and the module docstring itself among
  the wording the file tests, and a test holds it to that wording. (#105)
- The test added for #105 in `scripts/test_stripped_docstrings.py`, that
  each operator evaluated as another fails one of the two tests of
  timeouts written as arithmetic, could pass when one of those tests
  failed with no operator evaluated as another. With the run
  `timeout=1 / (5 * 0)` deleted from the source of one of them and its
  entry kept in the expected list, that test failed with no swap and
  under each swap as well, so the swap test counted each swap as held
  and passed. It now runs the two tests once with no swap first and fails
  unless both pass, and a new test checks that the swap test fails when
  one of them fails with no swap. (#107)
- The test added for #107 in `scripts/test_stripped_docstrings.py`
  replaced only the test of timeouts that are not a finite number, and
  only with one that fails. A swap test that ran only that test with no
  swap, or that counted only failures and not errors, still passed it,
  so the swap test could stop checking the test of timeouts that are
  accepted, or miss a test that raises, such as one whose source does
  not parse. It now replaces each of the two tests in turn, once with
  one that fails and once with one that raises `SyntaxError`, and
  requires the swap test to fail each time. The two tests are now named
  once, on the test class, where the swap test and its test both read
  them. (#109)
- The CI examples under `integrations/` no longer report a run that
  measured nothing as score 0. A scan that found no governance file, or one
  that is unreadable or empty, has a null score, which both examples turned
  into 0, so with a minimum set the job failed as "score 0 is below minimum".
  They now read `gate.reason` first, print what was missing, and fail only
  when a minimum is set; the GitHub Action's comment shows the score as not
  measured. The comment lists a domain that the agent profile leaves out as
  not applicable instead of "0/0 (0%) Needs work", and its script reads the
  scan outputs through `env:` instead of pasting them into the script
  source. The GitLab CI example keeps `scan-result.json` as an artifact also
  when the job fails. Both examples pin hackmyagent 0.33.2 instead of
  installing the latest release on every run, and `integrations/README.md`
  states the trade-off. `--help` and `-h` print the usage of
  `scripts/check_docs_prose.py` and exit 0; they were read as a directory
  name. Tests in `scripts/test_github_action.py`,
  `scripts/test_integrations.py`, `scripts/test_gitlab_ci.py`,
  `scripts/test_scan_soul_commands.py` and
  `scripts/test_check_docs_prose.py`. (#51)
- In both CI examples under `integrations/`, a run in which the scanner gave
  no result (`npx` could not install or start it, or it printed no score and
  no reason that names a run that measured nothing) fails the job whether or
  not a minimum is set. With no minimum, the GitLab CI job and the GitHub
  Action's check passed it as a run that measured nothing. The GitLab CI job
  fails with a message naming `MIN_GOVERNANCE_SCORE` when the value is set
  to something that is not a whole number, as the GitHub Action does; with
  `60%` or `forty` the bash of its `node:20-slim` image printed "integer
  expression expected" and the job passed. The GitHub Action's pull request
  comment updates only the comment it wrote, found by a hidden marker and
  the `github-actions[bot]` author on every page of the comments; it
  updated the first of the first 30 comments that contained "Agent
  Governance Scan", whoever wrote it, and created a second comment on a
  longer thread. A comment posted by the earlier version has no marker, so
  on a pull request that has one, the first run after the update posts a
  new comment, and later runs update that one. The README's GitHub Actions
  snippet pins hackmyagent 0.33.2, the release the full workflow pins,
  instead of installing the latest release. Tests in
  `scripts/test_github_action.py`, `scripts/test_integrations.py`,
  `scripts/test_gitlab_ci.py` and `scripts/test_scan_soul_commands.py`.
  (#112)
- In the GitHub Action example, the pull request comment shows the
  conformance as `NONE` and the file as `none` when the scanner gave no
  result; `jq` prints nothing for an empty `scan-result.json`, so the
  comment had an empty Conformance line and an empty File code span. The
  workflow uploads `scan-result.json` as the `governance-scan-result`
  artifact, also when the job fails, and the message for a run in which
  the scanner gave no result names that artifact and the "Run governance
  scan" step log; it named `scan-result.json`, which no step uploaded.
  Both CI examples state that an unset or empty `MIN_GOVERNANCE_SCORE` is
  a minimum of 0; the GitLab CI example said that any value other than a
  whole number fails the job. Tests in `scripts/test_github_action.py`,
  `scripts/test_integrations.py` and `scripts/test_gitlab_ci.py`. (#114)
- In the GitHub Action example, a failed artifact upload no longer skips the
  pull request comment or fails the job. The "Keep scan result" step ran
  before "Comment on PR", whose `if:` calls no status check function, so
  GitHub adds `success()` to it: when the upload failed, the comment was
  skipped and the job failed whatever the score. The upload fails when the
  artifact storage quota is used up, and on GitHub Enterprise Server, which
  the README of `actions/upload-artifact@v4` lists as not supported. The
  step is now the last one, after "Check minimum score", and has
  `continue-on-error: true`. The workflow header and
  `integrations/README.md` state the limitation and what to change on
  GitHub Enterprise Server. Tests in `scripts/test_integrations.py`. (#116)
- Both CI examples under `integrations/` fail the job when
  `MIN_GOVERNANCE_SCORE` is a whole number above 100, the highest score,
  with a message naming the variable. A value too long for the shell to
  read as a number (20 digits, for example) passed the whole-number check,
  `[` printed "integer expression expected" (bash 5.2 and earlier; bash 5.3
  prints "integer expected"), the comparison was false, and the job passed
  whatever the score was; a run that measured nothing passed the same way.
  A minimum from 101 up to the largest number the shell reads
  failed every scored run as below the minimum, and now fails with the
  message about the variable. A minimum from 0 to 100 written in up to
  three digits (`060` is 60) is compared as before; one written in more
  digits fails the job like one above 100. The header of each example and
  `integrations/README.md` state the range. Tests in
  `scripts/test_integrations.py` and `scripts/test_gitlab_ci.py`. (#117)
- The `NoResult` tests in `scripts/test_github_action.py`, added for #114,
  gave the comment script the scan step's default outputs as written in
  the test, so they also passed against the workflow from before that fix,
  whose scan step output an empty conformance and file for an empty
  `scan-result.json`. They now run the "Run governance scan" step on an
  empty result, with the stand-in for `npx` from
  `scripts/test_integrations.py`, and give its outputs to the comment
  script, so they fail against that workflow. They need bash and jq as
  well as node, and are skipped without them. (#118)
- In both CI examples under `integrations/`, a `MIN_GOVERNANCE_SCORE`
  written with a leading zero in more than three digits fails the job with
  "MIN_GOVERNANCE_SCORE must be from 0 to 100 in at most three digits"; for
  `0060`, which is 60, the message was "must be 100 or less". The job
  failed before and fails now, and a value above 100 with no leading zero
  keeps the message "must be 100 or less". The entry for #117 above quoted
  "integer expression expected" as what `[` printed for a number too long
  for the shell; that is the wording of bash 5.2 and earlier, bash 5.3
  prints "integer expected", and the entry now gives both. In
  `scripts/test_integrations.py`, the model of which steps start and
  whether the job fails read a `continue-on-error` written as an
  expression, `${{ true }}` for example, as not set, and reported a failed
  job where the runner reports a passed one. A value other than `true` or
  `false` now fails the test that reads it, as an `if:` the model does not
  read already did. Tests in `scripts/test_integrations.py` and
  `scripts/test_gitlab_ci.py`. (#120)
- README.md and the exit code list in `integrations/README.md` said that
  `scan-soul` exit 0 means the Essential level. Essential also requires at
  least 500 characters of content and at least 3 section headings
  (`specification.md` section 2.3, `conformance.md` Level 1 requirement 1),
  and hackmyagent 0.33.2 checks neither: it exits 0 with `conformance`
  `essential` on a 154-byte `SOUL.md` with three headings, and on a
  119-byte one with no heading. Both pages now say that exit 0 means every
  CRITICAL control applicable to the tier was detected, and name the length
  and heading minimum the scanner leaves to the reader. Tests in
  `scripts/test_readme.py` read the minimum from section 2.3 and check that
  a prose line in README.md, the pages under `docs/`,
  `integrations/README.md` or `conformance.md` that says what exit 0 means
  ("exit 0 when" or "exits 0 when", or a "`0`:" list item) and names the Essential level
  also names that minimum and section 2.3. (#123)
- The README Quick Start and Tools sections and the `docs/overview.md`
  Adoption Path describe `harden-soul` as adding template sections to the
  governance file it finds, and creating `SOUL.md` only when it finds none.
  They said it generates or updates `SOUL.md`, but in a directory holding
  only `CLAUDE.md`, hackmyagent 0.33.2 `harden-soul` appends to `CLAUDE.md`
  and creates no `SOUL.md`. The Quick Start links the discovery order of
  `specification.md` section 2.2 and names `--dry-run --json`, whose `file`
  field gives the file the command will change. With two files of that list
  in a directory, hackmyagent 0.33.2 chose the earlier one for each adjacent
  pair tried; `system-prompt.md` and `SYSTEM_PROMPT.md` were not tried as a
  pair, being one file on a case-insensitive file system.
  `scripts/test_readme.py` checks that no sentence describing `harden-soul`
  names `SOUL.md` as the file it writes without saying when. (#124)
- The level table in the `conformance.md` Overview gave Essential as "All
  CRITICAL controls pass", and Standard and Hardened as controls and a
  score, while Level 1 requirement 1 also requires a valid governance file
  of at least 500 characters and 3 section headings (`specification.md`
  section 2.3), and Levels 2 and 3 include every requirement of the level
  below. The Essential row now names that minimum and section 2.3, and the
  Standard and Hardened rows each name the level below. Tests in
  `scripts/test_readme.py` read the minimum from section 2.3 and check that
  the Essential row of the table names it and section 2.3, and that the
  Standard and Hardened rows each name either that minimum and section 2.3
  or the level below. (#126)
- `specification.md` section 7 gave the requirements of Essential (7.1) as
  the CRITICAL controls and no minimum score, and those of Standard (7.2)
  and Hardened (7.3) as controls and a score, without the valid governance
  file of section 2.3 that `conformance.md` requires at every level. Section
  7.1 now requires a governance file valid under section 2.3, naming its
  500-character and 3-heading minimum, and sections 7.2 and 7.3 each
  require every requirement of the level below, as Levels 2 and 3 of
  `conformance.md` do; in 7.2 that item takes the place of the CRITICAL
  controls item, which Essential includes. Tests in `scripts/test_readme.py` read the
  Requirements list of each level subsection of section 7 and check that
  the Essential list names the minimum of section 2.3 and that section, and
  that the Standard and Hardened lists each name either that minimum and
  section 2.3 or the level below. (#128)
- The `docs/overview.md` Adoption Path called the scanner's failure on a
  missing CRITICAL control "the Essential gate", and its Scoring section
  gave the conformance levels as "which controls must pass, plus a minimum
  score". Essential also requires at least 500 characters of content and
  at least 3 section headings (`specification.md` section 2.3) and sets no
  minimum score, and hackmyagent 0.33.2 checks neither the length nor the
  heading count: `scan-soul` exits 0 with `conformance` `essential` on a
  114-byte `SOUL.md` with three headings, and on a 79-byte one with none.
  The Adoption Path now says a passing job does not show the Essential
  level and names that minimum, and the Scoring section gives each level's
  requirements: that minimum and the CRITICAL controls for Essential, and
  the HIGH controls and a score of 60 for Standard, and every control and
  a score of 75 for Hardened. Tests in `scripts/test_readme.py` check that
  a prose line in README.md, the pages under `docs/` or
  `integrations/README.md` that names the Essential level and gives a
  level's requirement as a CRITICAL control or as which controls must pass
  also names that minimum and section 2.3. (#129)
- The `docs/overview.md` Adoption Path said to read the conformance level
  from the `conformance` field of the `scan-soul --json` output. That field
  does not show a level by itself: `scan-soul --json` of hackmyagent 0.33.2
  exits 0 with `conformance` `essential` on a 79-byte `SOUL.md` with no
  headings, and every level requires at least 500 characters of content
  and at least 3 section headings (`specification.md` section 2.3). The
  step now names that minimum and the 79-byte run, and says to read the
  field together with the two counts taken from the file. Tests in
  `scripts/test_readme.py` check that a prose line in README.md, the pages
  under `docs/`, `integrations/README.md` or `conformance.md` that names the
  `conformance` field, key or value also names that minimum and section
  2.3. (#131)
- The terminology table of `specification.md` section 1.4 defined a
  conformance level as a threshold "based on which controls pass", while
  section 7 also requires a governance file valid under section 2.3 at
  every level, and an overall score of at least 60 for Standard and at
  least 75 for Hardened. The definition now names section 7, the
  governance file valid under section 2.3, the controls the level names,
  and those two scores. Tests in `scripts/test_readme.py` read the
  definition from the table and check that it names section 2.3, controls
  and an overall score, and that the scores it gives are the ones section
  7 sets for Standard and Hardened. (#132)

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
