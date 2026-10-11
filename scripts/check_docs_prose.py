#!/usr/bin/env python3
"""Check the prose of the tracked Markdown files for two writing rules.

  * No dash made of a spaced double hyphen (" -- "), an em dash (U+2014), or a
    spaced en dash (" - " with U+2013) in prose. Rewrite the sentence with a
    period, a comma, a colon, or parentheses.
  * No heading named "Why this exists" or "Why this matters". Fold what the
    reader needs into the surrounding prose, or delete the section.

Run from anywhere:  python3 scripts/check_docs_prose.py

Standard library only. Exit 0 when the prose is clean; exit 1 after printing
one "file:line: message" line per finding.

Checked: every file git tracks that ends in .md or .mdx, except CHANGELOG.md
and changelog.d/ (history is not rewritten), LICENSE files, and anything under
node_modules/, vendor/, dist/, build/, or a test, fixture, corpus, golden,
snapshot or examples directory (that text is data a tool reads, not prose a
person reads), and the crosswalk .md files that scripts/check_crosswalks.py
renders from the CSV sources (their text quotes the mapped frameworks verbatim
and is compared byte for byte). Outside git, the working tree is walked with
the same rules.

Skipped inside a checked file: fenced code blocks, inline code spans, YAML
front matter, HTML comments, badge lines (an image link at the start of the
line), and a table cell whose whole content is "--", which marks an empty cell
and is not a dash.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_FILES = ("CHANGELOG.md",)
EXCLUDED_PREFIXES = ("changelog.d/", "node_modules/", "vendor/", "dist/", "build/")
# Rendered by scripts/check_crosswalks.py from crosswalks/*.csv and byte-checked against that render.
RENDERED_PREFIXES = ("crosswalks/oasb-2-to-",)
EXCLUDED_DIR_NAMES = frozenset(
    ["test", "tests", "fixture", "fixtures", "corpus", "golden", "snapshot", "snapshots", "example", "examples"]
)

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)[^`]*?\1")
BADGE_LINE = re.compile(r"^\s*(\[!\[|!\[)")
WHY_HEADING = re.compile(r"^#{1,6}\s*Why this (exists|matters)\b", re.IGNORECASE)
EMPTY_CELL = re.compile(r"\|\s*--\s*(?=\|)")

DASHES = (
    (" -- ", "spaced double hyphen used as a dash"),
    ("—", "em dash"),
    (" – ", "spaced en dash"),
)


def excluded(rel):
    """True when the repository-relative POSIX path is outside the checked set."""
    if rel in EXCLUDED_FILES or rel.startswith(EXCLUDED_PREFIXES + RENDERED_PREFIXES):
        return True
    parts = rel.split("/")
    if parts[-1].upper().startswith("LICENSE"):
        return True
    return any(part.lower() in EXCLUDED_DIR_NAMES for part in parts[:-1])


def tracked_markdown(root):
    """Repository-relative paths of the Markdown files to check, sorted."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md", "*.mdx"],
            check=True, capture_output=True,
        ).stdout
        rels = [p.decode("utf-8") for p in out.split(b"\0") if p]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        rels = [
            str(p.relative_to(root).as_posix())
            for ext in ("*.md", "*.mdx")
            for p in root.rglob(ext)
            if ".git" not in p.relative_to(root).parts
        ]
    return sorted(rel for rel in rels if not excluded(rel))


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
            if line.strip().startswith(fence):
                fence = None
            continue
        m = FENCE.match(line)
        if m:
            fence = m.group(1)[0] * 3
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
        yield number, INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)


def findings(text):
    """(line number, message) for each rule violation in the Markdown text."""
    found = []
    for number, line in prose_lines(text):
        if WHY_HEADING.match(line):
            found.append((number, 'heading named "Why this exists" or "Why this matters"'))
        stripped = EMPTY_CELL.sub("|   ", line) if line.lstrip().startswith("|") else line
        for needle, message in DASHES:
            if needle in stripped:
                found.append((number, message))
    return found


def main(argv=None):
    root = Path(argv[1]).resolve() if argv and len(argv) > 1 else ROOT
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
        print(f"{failures} finding(s); see the rules at the top of {os.path.relpath(__file__, root)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
