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
script is checked. --help or -h prints the usage message and exits 0.

Standard library only. Exit 0 when the prose is clean; exit 1 after printing
one "file:line: message" line per finding; exit 2 after printing a usage
message when ROOT is not a directory or more than one argument is given.

Checked: every file git tracks that ends in .md or .mdx, except these, each
given with the reason it is not read:
  * CHANGELOG.md and changelog.d/ at the root of the checked directory:
    history is not rewritten.
  * LICENSE files: a license is legal text reproduced word for word from its
    publisher, and rewording it would change the terms it grants.
  * anything under node_modules/, vendor/, dist/ or build/ at the root of the
    checked directory: the files there are third-party or generated, so a fix
    belongs in their source, not here.
  * anything in a test, tests, fixture, fixtures, corpus, golden, snapshot,
    snapshots, example or examples directory: that text is data a tool reads,
    not prose a person reads. A README.md or README.mdx in an example or
    examples directory is read, since it describes the examples to a person,
    unless a directory of this item other than example or examples holds it
    or another item of this list excludes its path.
  * the crosswalk .md files that scripts/check_crosswalks.py renders from the
    CSV sources (crosswalks/oasb-2-to-*.md at the root of the checked
    directory): their text quotes the mapped frameworks verbatim and is
    compared byte for byte.

Outside git, the working tree is walked with the same rules.

Skipped inside a checked file: fenced code blocks (a fence opens at a line
that starts, after at most three spaces, with a run of three or more
backticks or tildes, where no backtick follows a run of backticks on the
line, and closes at a line that holds, after at most three spaces, only a
run of its own character at least as long as the run that opened it, then
nothing but spaces and tabs; inside a list item or a block quote the spaces
are counted from the column where its content starts, and the block ends
with it, and no fence opens inside an HTML block, as CodeFences describes),
inline code spans, YAML front matter, HTML comments, badge lines
(an image link at the start of the line), a table cell whose whole content is
"--", which marks an empty cell and is not a dash, and a line of hyphens
directly under a line of text, which is a setext heading underline.
"""

import bisect
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

# The CommonMark conditions on the line that opens a fence, from its first character that is not a space or a tab: a
# run of three or more backticks or tildes, with no backtick after a run of backticks on the line. CodeFences reads
# the indentation before it.
FENCE = re.compile(r"`{3,}(?=[^`]*$)|~{3,}")
# The starts of the other blocks that decide where a list item or a block quote ends, each matched from the first
# character of a line that is not a space or a tab (CodeFences): a list marker, an ATX heading, and a setext heading
# underline.
LIST_MARKER = re.compile(r"[-+*]|([0-9]{1,9})[.)]")
ATX_HEADING = re.compile(r"#{1,6}(?:[ \t]|$)")
HEADING_UNDERLINE = re.compile(r"(?:=+|-+)[ \t]*$")
# The start of an HTML block, matched from the first character of a line that is not a space or a tab (CodeFences). Its
# seven groups are the seven kinds of HTML block: a pre, script, style or textarea tag; a comment; a processing
# instruction; a declaration; a CDATA section; the opening or closing tag of a block element; and an open or closing tag
# of any name with nothing but spaces and tabs after it, which does not interrupt a paragraph.
HTML_BLOCK = re.compile(
    r"(<(?:pre|script|style|textarea)(?:[ \t>]|$))|(<!--)|(<\?)|(<![A-Za-z])|(<!\[CDATA\[)"
    r"|(</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div"
    r"|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link"
    r"|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead"
    r"|title|tr|track|ul)(?:[ \t]|/?>|$))"
    r"|((?:<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*(?:[ \t]*=[ \t]*(?:[^ \t\r\n\"'=<>`]+|'[^']*'"
    r"|\"[^\"]*\"))?)*[ \t]*/?>|</[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$)",
    re.ASCII | re.IGNORECASE)
# The line that ends an HTML block of each kind of HTML_BLOCK, matched from its first character that is not a space or
# a tab: a line that holds a closing pre, script, style or textarea tag, "-->", "?>", ">" or "]]>", or a blank line.
HTML_BLOCK_END = tuple(re.compile(end, re.ASCII | re.IGNORECASE) for end in (
    r".*?</(?:pre|script|style|textarea)>", r".*?-->", r".*?\?>", r".*?>", r".*?\]\]>", r"\Z", r"\Z"))
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
    """True when the root-relative POSIX path (relative to the checked directory) is outside the checked set."""
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
    """Root-relative paths (relative to the checked directory) of the Markdown files to check, sorted."""
    return sorted(rel for rel in listed_markdown(root) if not excluded(rel))


def first_character(line, index, column):
    """(index, column) of the first character of line at or after index that is not a space or a tab, or of the end
    of the line. index is at column, and a tab advances the column to the next multiple of four."""
    while index < len(line) and line[index] in " \t":
        column = column + 4 - column % 4 if line[index] == "\t" else column + 1
        index += 1
    return index, column


def closes_fence(fence, rest):
    """True when rest, a line from its first character that is not a space or a tab, holds only a run of the fence's
    own character at least as long as the fence, then nothing but spaces and tabs."""
    run = rest.rstrip(" \t")
    return len(run) >= len(fence) and run == fence[0] * len(run)


def past_quote_marker(line, index, column):
    """(index, column, start) for the block quote marker ">" at index of line, which is at column: the index and the
    column of the first character after the marker that is not a space or a tab, or of the end of the line, and the
    column where the content of the quote starts, which is the column after the marker, or the one after that when a
    space or a tab follows the marker."""
    index, column = index + 1, column + 1
    start = column + 1 if index < len(line) and line[index] in " \t" else column
    index, column = first_character(line, index, column)
    return index, column, start


class CodeFences:
    """Tells which lines of a Markdown file are lines of a fenced code block, given its lines one at a time, in order.

    A fence opens or closes at a line indented at most three spaces past the column where the content of the list item
    or block quote that holds the line starts, or past the start of the line outside them, and a block inside a list
    item or a block quote ends with it. The list items and block quotes are read by the CommonMark rules. An item
    opens at a bullet (-, + or *), or at one to nine digits and a period or a closing parenthesis, indented at most
    three spaces and followed by a space, a tab or the end of the line, unless the line is a thematic break such as
    "- - -". Its content starts at the column after the marker and the one to four spaces that follow it, or at the
    column after the marker and one space when nothing or five spaces or more follow it. An item interrupts a
    paragraph only when text follows its marker, and an ordered item only when its number is 1. A later line continues
    the item when it is indented at least to the column where the item's content starts, when it is blank and the item
    holds a block, or when it continues a paragraph of the item without that indentation. A block quote opens at a ">"
    indented at most three spaces. Its content starts at the column after the ">", or at the one after that when a
    space or a tab follows the ">". A later line continues the quote when it holds such a ">", or when it continues a
    paragraph of the quote without one, so a blank line ends it. Inside a list item or a block quote, the indentation
    of a line is counted from the column where the content of the item or quote starts. A tab advances to the next
    multiple of four columns. The paragraphs, ATX and setext headings, thematic breaks and indented code blocks that
    decide where an item or a quote ends are read too, and so are the HTML blocks. An HTML block opens at a line that
    starts, after at most three spaces, with one of the seven kinds of start of HTML_BLOCK, the last of which does not
    interrupt a paragraph, and no other block opens inside it. It ends at the first line, from the one that opens it,
    that holds the end of its kind (HTML_BLOCK_END), which for the last two kinds is a blank line, or with the list
    item or block quote that holds it. After a line is read, literal is True when the line is part of an HTML block,
    or is a line of an indented code block that is not blank: a line indented four spaces or more past the column
    where the content of its list item or block quote starts, or past the start of the line outside them, that does
    not continue a paragraph. GFM renders neither as Markdown text.
    """

    def __init__(self):
        # The open list items and block quotes, outermost first: 0 for a block quote, and for a list item the number of
        # columns from the column where the content of the item or quote that holds it starts, or from the start of the
        # line, to the column where its own content starts, which is 2 or more.
        self.containers = []
        self.quotes = []  # the index in containers of each open block quote, in order
        # The innermost container is a list item opened at a line that held only its marker, and holds no block yet.
        self.empty = False
        self.paragraph = False  # the last block read is a paragraph, which a line can continue without its containers
        self.fence = None  # the run of backticks or tildes that opened the fenced code block that is open
        self.html = None  # the pattern of HTML_BLOCK_END that ends the HTML block that is open
        self.literal = False  # the last line read is part of an HTML block or an indented code block

    def close(self, depth):
        """Ends the open list items and block quotes past the first depth of them."""
        del self.containers[depth:]
        del self.quotes[bisect.bisect_left(self.quotes, depth):]

    def read(self, line):
        """True when line, the next line of the file, opens, continues or closes a fenced code block."""
        if line.endswith("\r"):  # the carriage return of a CRLF line ending
            line = line[:-1]
        index, column = first_character(line, 0, 0)
        # The open containers the line continues, outermost first, and the column where the content of the innermost
        # of them starts. A list item is continued by a line indented to the column where its content starts, and a
        # block quote by a line that holds its ">". Once the rest of the line is blank, the line continues the list
        # items up to the next block quote, but not that quote, nor an item that holds no block. Each list item a line
        # continues takes two columns or more of its indentation, and each block quote a character, so the containers
        # of a line are read in time linear in its length, with one binary search when the rest of it is blank.
        matched, base = 0, 0
        while matched < len(self.containers):
            if index == len(line):
                quote = bisect.bisect_left(self.quotes, matched)
                matched = (self.quotes[quote] if quote < len(self.quotes)
                           else len(self.containers) - (1 if self.empty else 0))
                break
            indent = self.containers[matched]
            if indent and column - base >= indent:
                base += indent
            elif not indent and line[index] == ">" and column - base <= 3:
                index, column, base = past_quote_marker(line, index, column)
            else:
                break
            matched += 1
        blank = index == len(line)
        if self.fence is not None:
            if matched == len(self.containers):
                if not blank and column - base <= 3 and closes_fence(self.fence, line[index:]):
                    self.fence = None
                return True
            self.fence = None  # the line ends a list item or a block quote that holds the block, and the block with it
        self.literal = False
        if self.html is not None:
            if matched == len(self.containers):
                self.literal = True
                if self.html.match(line, index):
                    self.html = None  # the line holds the end of the block
                return False
            self.html = None  # the line ends a list item or a block quote that holds the block, and the block with it
        lazy = self.paragraph and matched < len(self.containers)
        in_paragraph = self.paragraph and not lazy
        opened = False  # the line opens a list item or a block quote
        leaf = None  # the run of a fence the line opens, or "" for a heading, a thematic break or an HTML block
        html = None  # the pattern of HTML_BLOCK_END that ends the HTML block the line opens
        # No thematic break of mark starts before stop, where a scan from an earlier index ended without one. Each scan
        # starts at or after the index where the one before it ended, so a line is read in time linear in its length,
        # however many list markers and block quote markers it holds.
        mark, stop = "", 0
        while not blank and column - base <= 3:
            fence = FENCE.match(line, index)
            if fence:
                leaf = fence.group()
                break
            if ATX_HEADING.match(line, index) or (in_paragraph and HEADING_UNDERLINE.match(line, index)):
                leaf = ""
                break
            if line[index] == "<":
                # The last kind of HTML block does not interrupt a paragraph, so it does not open on a line that would
                # continue one.
                start = HTML_BLOCK.match(line, index)
                if start and (start.lastindex < len(HTML_BLOCK_END) or opened or not self.paragraph):
                    leaf, html = "", HTML_BLOCK_END[start.lastindex - 1]
                break
            if line[index] in "-_*" and (line[index] != mark or index >= stop):
                mark, stop, count = line[index], index, 0
                while stop < len(line) and line[stop] in (mark, " ", "\t"):
                    count += line[stop] == mark
                    stop += 1
                if stop == len(line) and count >= 3:
                    leaf = ""
                    break
            if line[index] == ">":
                if not opened:
                    self.close(matched)
                    opened = True
                self.quotes.append(len(self.containers))
                self.containers.append(0)
                index, column, base = past_quote_marker(line, index, column)
                blank = index == len(line)
                in_paragraph = False
                continue
            marker = LIST_MARKER.match(line, index)
            end = marker.end() if marker else index
            if not marker or (end < len(line) and line[end] not in " \t"):
                break
            after, after_column = first_character(line, end, column + end - index)
            if in_paragraph and (after == len(line) or (marker.group(1) and int(marker.group(1)) != 1)):
                break
            if not opened:
                self.close(matched)
                opened = True
            end_column = column + end - index
            spaced = after < len(line) and after_column - end_column <= 4
            content = after_column if spaced else end_column + 1
            self.containers.append(content - base)
            base = content
            index, column, blank = after, after_column, after == len(line)
            in_paragraph = False
        if leaf is not None or opened:
            if not opened:
                self.close(matched)
            self.paragraph = leaf is None and not blank and column - base <= 3
            self.empty = leaf is None and blank and self.containers[-1] > 0
            self.fence = leaf or None
            self.html = None if html is None or html.match(line, index) else html
            self.literal = html is not None or (leaf is None and not blank and column - base > 3)
            return bool(leaf)
        if lazy and not blank:
            return False  # the line continues the paragraph, and the containers that hold it stay open
        self.close(matched)
        self.literal = not blank and not in_paragraph and column - base > 3
        self.paragraph = not blank and (in_paragraph or column - base <= 3)
        self.empty = False
        return False


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
    fences = CodeFences()
    in_comment = False
    for number, line in enumerate(lines[start:], start + 1):
        if fences.read(line):
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
    if args in (["--help"], ["-h"]):
        print(USAGE)
        return 0
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
