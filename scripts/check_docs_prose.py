#!/usr/bin/env python3
"""Check the prose of the tracked Markdown files for two writing rules.

  * No dash made of a spaced double hyphen (" -- "), an em dash (U+2014), or a
    spaced en dash (" - " with U+2013) in prose. Rewrite the sentence with a
    period, a comma, a colon, or parentheses. A double hyphen or an en dash
    is spaced when each side of it is a space, a tab, or the edge of the
    line, so a dash that ends or starts a hard-wrapped line is reported.
  * No heading named "Why this exists" or "Why this matters": an ATX heading
    at any indent, a setext heading (the name on one line and a line of "="
    or "-" under it), or a bold label that starts a line. Fold what the
    reader needs into the surrounding prose, or delete the section.

Run from anywhere:  python3 scripts/check_docs_prose.py [ROOT]

ROOT is the directory to check. Without it, the repository that holds this
script is checked.

Standard library only. Exit 0 when the prose is clean; exit 1 after printing
one "file:line: message" line per finding; exit 2 after printing a usage
message when ROOT is not a directory or more than one argument is given.

Checked: every file git tracks that ends in .md or .mdx, except these, each
given with the reason it is not read:
  * CHANGELOG.md and changelog.d/: history is not rewritten.
  * LICENSE files: a license is legal text reproduced word for word from its
    publisher, and rewording it would change the terms it grants.
  * anything under node_modules/, vendor/, dist/ or build/ at the repository
    root: the files there are third-party or generated, so a fix belongs in
    their source, not here.
  * anything in a test, tests, fixture, fixtures, corpus, golden, snapshot,
    snapshots, example or examples directory: that text is data a tool reads,
    not prose a person reads. A README.md or README.mdx in an example or
    examples directory is read, since it describes the examples to a person,
    unless another directory of this item holds it or another item of this
    list excludes its path.
  * the crosswalk .md files that scripts/check_crosswalks.py renders from the
    CSV sources (crosswalks/oasb-2-to-*.md): their text quotes the mapped
    frameworks verbatim and is compared byte for byte.

Outside git, the working tree is walked with the same rules.

Skipped inside a checked file: fenced code blocks (a fence closes at a line
that holds only a run of its own character at least as long as the run that
opened it), inline code spans, YAML front matter, HTML comments, badge lines
(an image link at the start of the line), a table cell whose whole content is
"--", which marks an empty cell and is not a dash, and a line of hyphens
directly under a line of text, which is a setext heading underline.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = "scripts/check_docs_prose.py"
USAGE = f"usage: python3 {SELF} [ROOT]\n  ROOT  the directory to check; without it, the repository that holds this script"

EXCLUDED_FILES = ("CHANGELOG.md",)
EXCLUDED_PREFIXES = ("changelog.d/", "node_modules/", "vendor/", "dist/", "build/")
# Rendered by scripts/check_crosswalks.py from crosswalks/*.csv and byte-checked against that render.
RENDERED_PREFIXES = ("crosswalks/oasb-2-to-",)
EXCLUDED_DIR_NAMES = frozenset(
    ["test", "tests", "fixture", "fixtures", "corpus", "golden", "snapshot", "snapshots", "example", "examples"]
)
# An examples directory holds files a tool reads beside a README a person reads about them.
EXAMPLE_DIR_NAMES = frozenset(["example", "examples"])
README_NAMES = frozenset(["readme.md", "readme.mdx"])

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
BACKTICK_RUN = re.compile(r"`+")
BADGE_LINE = re.compile(r"^\s*(\[!\[|!\[)")
WHY_NAME = r"Why this (?:exists|matters)(?![^\W_])"  # the name ends before anything but a letter or a digit
WHY_HEADING = re.compile(r"^\s*#{1,6}\s*" + WHY_NAME, re.IGNORECASE)
WHY_SETEXT = re.compile(r"^\s*" + WHY_NAME, re.IGNORECASE)
WHY_LABEL = re.compile(r"^\s*(?:\*\*|__)\s*" + WHY_NAME, re.IGNORECASE)
SETEXT_UNDERLINE = re.compile(r"^\s*(?:=+|-+)\s*$")
EMPTY_CELL = re.compile(r"\|\s*--\s*(?=\||$)")

WHY_HEADING_MESSAGE = 'heading named "Why this exists" or "Why this matters"'
WHY_LABEL_MESSAGE = 'bold label named "Why this exists" or "Why this matters"'

# A double hyphen or an en dash is a dash when whitespace or the edge of the line is on each side of it.
DASHES = (
    (re.compile(r"(?<!\S)--(?!\S)"), "spaced double hyphen used as a dash"),
    (re.compile("—"), "em dash"),
    (re.compile(r"(?<!\S)–(?!\S)"), "spaced en dash"),
)


def excluded(rel):
    """True when the repository-relative POSIX path is outside the checked set."""
    if rel in EXCLUDED_FILES or rel.startswith(EXCLUDED_PREFIXES + RENDERED_PREFIXES):
        return True
    parts = rel.split("/")
    if parts[-1].upper().startswith("LICENSE"):
        return True
    data_dirs = {part.lower() for part in parts[:-1]} & EXCLUDED_DIR_NAMES
    if data_dirs <= EXAMPLE_DIR_NAMES and parts[-1].lower() in README_NAMES:
        return False
    return bool(data_dirs)


def listed_markdown(root):
    """Root-relative paths of the Markdown files git tracks under root, or of those in the tree outside git."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md", "*.mdx"],
            check=True, capture_output=True,
        ).stdout
        return [p.decode("utf-8") for p in out.split(b"\0") if p]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return [
            str(p.relative_to(root).as_posix())
            for ext in ("*.md", "*.mdx")
            for p in root.rglob(ext)
            if ".git" not in p.relative_to(root).parts
        ]


def tracked_markdown(root):
    """Repository-relative paths of the Markdown files to check, sorted."""
    return sorted(rel for rel in listed_markdown(root) if not excluded(rel))


def closes_fence(fence, line):
    """True when the line holds only a run of the fence's own character, at least as long as the fence."""
    run = line.strip()
    return len(run) >= len(fence) and run == fence[0] * len(run)


def blank_code_spans(line):
    """The line with each inline code span replaced by spaces, in time linear in the length of the line.

    A span opens at a run of backticks and closes at the next run of the same length, as in CommonMark.
    """
    runs = [m.span() for m in BACKTICK_RUN.finditer(line)]
    if len(runs) < 2:
        return line
    by_length = {}  # run length -> indexes of the runs of that length, last first
    for index in range(len(runs) - 1, -1, -1):
        by_length.setdefault(runs[index][1] - runs[index][0], []).append(index)
    out = []
    copied = 0
    index = 0
    while index < len(runs):
        start, end = runs[index]
        same = by_length[end - start]
        while same and same[-1] <= index:
            same.pop()
        if same:
            close = runs[same[-1]][1]
            out.append(line[copied:start] + " " * (close - start))
            copied = close
            index = same[-1] + 1
        else:
            index += 1
    out.append(line[copied:])
    return "".join(out)


def prose_lines(text):
    """Yield (line number, line with code spans blanked) for each prose line of text."""
    lines = text.split("\n")
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                start = i + 1
                break
    fence = None
    in_comment = False
    for number, line in enumerate(lines[start:], start + 1):
        if fence is not None:
            if closes_fence(fence, line):
                fence = None
            continue
        m = FENCE.match(line)
        if m:
            fence = m.group(1)
            continue
        if in_comment:
            if "-->" in line:
                line = line.split("-->", 1)[1]
                in_comment = False
            else:
                continue
        while "<!--" in line:
            before, rest = line.split("<!--", 1)
            if "-->" in rest:
                line = before + rest.split("-->", 1)[1]
            else:
                line = before
                in_comment = True
        if BADGE_LINE.match(line):
            continue
        yield number, blank_code_spans(line)


def findings(text):
    """(line number, message) for each rule violation in the Markdown text."""
    found = []
    above_number, above = 0, ""
    for number, line in prose_lines(text):
        underline = bool(SETEXT_UNDERLINE.match(line)) and above_number == number - 1 and above.strip() != ""
        if underline and WHY_SETEXT.match(above):
            found.append((above_number, WHY_HEADING_MESSAGE))
        if WHY_HEADING.match(line):
            found.append((number, WHY_HEADING_MESSAGE))
        elif WHY_LABEL.match(line):
            found.append((number, WHY_LABEL_MESSAGE))
        if not underline:
            stripped = EMPTY_CELL.sub("|   ", line) if line.lstrip().startswith("|") else line
            for dash, message in DASHES:
                if dash.search(stripped):
                    found.append((number, message))
        above_number, above = number, line
    return found


def main(argv=None):
    args = list(argv[1:]) if argv else []
    if len(args) > 1:
        print(f"{SELF}: expected at most one argument, got {len(args)}\n{USAGE}", file=sys.stderr)
        return 2
    if args and not (args[0] and Path(args[0]).is_dir()):
        print(f"{SELF}: not a directory: {args[0]}\n{USAGE}", file=sys.stderr)
        return 2
    root = Path(args[0]).resolve() if args else ROOT
    failures = 0
    for rel in tracked_markdown(root):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        for number, message in findings(text):
            print(f"{rel}:{number}: {message}")
            failures += 1
    if failures:
        print(f"{failures} finding(s); see the rules at the top of {SELF}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
