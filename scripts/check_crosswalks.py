#!/usr/bin/env python3
"""Validate and render the OASB-2 static crosswalks under crosswalks/.

The two crosswalk CSV files are canonical. This script:

  * validates each CSV against the committed target-framework source
    allowlists (crosswalks/sources/*.csv) and against the control headings
    in domains/1[1-9]-*.md;
  * enforces the closed basis vocabulary, the note rules, the sort order,
    the exact header, and the file encoding (UTF-8 without BOM, LF line
    endings, RFC 4180 with minimal quoting);
  * scans every authored file under crosswalks/ (the frozen source
    allowlists under crosswalks/sources/ are excluded) for the banned
    vocabulary and for percentage, ratio, grade, or score wording;
  * re-renders each crosswalk .md from its CSV and requires the committed
    file to match byte for byte.

Run from anywhere:  python3 scripts/check_crosswalks.py
Re-render the .md files from the CSVs:  python3 scripts/check_crosswalks.py --write

Standard library only. No network access. Exits 0 when green, 1 when red;
each red line names the file and the row or line concerned.
"""

import csv
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CROSSWALKS = ROOT / "crosswalks"
DOMAINS = ROOT / "domains"

HEADER = ["control_id", "control_title", "target_id", "target_title", "basis", "note"]
BASIS_VOCABULARY = ("partially-addresses", "evidence-for", "related")
NOTE_MAX_CHARS = 200

CONTROL_HEADING = re.compile(r"^### (SOUL-[A-Z]{2}-\d{3}): (.+?)\s*$")
DOMAIN_HEADING = re.compile(r"^# Domain (\d+): (.+?)\s*$")

BANNED_WORDS = (
    "compliant", "compliance", "conforms", "conformity", "certified", "meets",
    "satisfies", "fulfils", "covers", "coverage", "aligned", "alignment",
    "audit-ready", "regulator-ready", "approved", "ensures", "guarantees",
)
QUANTITY_WORDS = (
    "percentage", "percentages", "percent", "ratio", "ratios",
    "grade", "grades", "graded", "grading", "score", "scores", "scored", "scoring",
)
BANNED_PATTERN = re.compile(
    r"(?<![\w-])(" + "|".join(re.escape(w) for w in BANNED_WORDS + QUANTITY_WORDS) + r")(?![\w-])",
    re.IGNORECASE,
)

NIST_STATEMENT = (
    "This crosswalk is an analyst reading of OASB-2 against NIST AI RMF 1.0. "
    "A row records that an analyst read an overlap in subject matter between one "
    "OASB-2 control and one framework subcategory; it does not state that either "
    "text requires, replaces, or stands in for the other. "
    "NIST AI RMF 1.0 is a voluntary framework."
)
EU_STATEMENT = (
    "This crosswalk is an analyst reading of OASB-2 against the EU AI Act "
    "(Regulation (EU) 2024/1689). A row records that an analyst read an overlap in "
    "subject matter between one OASB-2 control and one article or annex; it does not "
    "state that either text requires, replaces, or stands in for the other, and it "
    "does not classify any system under the Regulation. The Regulation applies as "
    "published in the Official Journal of the European Union."
)
NIST_SOURCE_LINE = (
    "Target text: NIST AI 100-1, January 2023 "
    "([DOI 10.6028/NIST.AI.100-1](https://doi.org/10.6028/NIST.AI.100-1); "
    "[NIST AI 100-1 PDF at nvlpubs](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)). "
    "Identifiers and titles come from the "
    "[committed subcategory list](sources/nist-ai-rmf-1.0-subcategories.csv); "
    "see the [crosswalk index](README.md) and the [source provenance](sources.md)."
)
EU_SOURCE_LINE = (
    "Target text: Regulation (EU) 2024/1689, OJ L, 12.7.2024 "
    "([ELI record](http://data.europa.eu/eli/reg/2024/1689/oj); "
    "[Official Journal PDF at EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689)). "
    "Identifiers and titles come from the "
    "[committed article and annex list](sources/eu-ai-act-2024-1689-articles.csv); "
    "see the [crosswalk index](README.md) and the [source provenance](sources.md)."
)

CROSSWALK_SET = (
    {
        "csv": "oasb-2-to-nist-ai-rmf-1.0.csv",
        "md": "oasb-2-to-nist-ai-rmf-1.0.md",
        "allowlist": "sources/nist-ai-rmf-1.0-subcategories.csv",
        "h1": "OASB-2 to NIST AI RMF 1.0 crosswalk",
        "statement": NIST_STATEMENT,
        "source_line": NIST_SOURCE_LINE,
    },
    {
        "csv": "oasb-2-to-eu-ai-act-2024-1689.csv",
        "md": "oasb-2-to-eu-ai-act-2024-1689.md",
        "allowlist": "sources/eu-ai-act-2024-1689-articles.csv",
        "h1": "OASB-2 to the EU AI Act (Regulation (EU) 2024/1689) crosswalk",
        "statement": EU_STATEMENT,
        "source_line": EU_SOURCE_LINE,
    },
)


def fail(errors, location, message):
    errors.append(f"RED {location}: {message}")


def check_bytes(errors, path, data):
    rel = path.relative_to(ROOT)
    if data.startswith(b"\xef\xbb\xbf"):
        fail(errors, f"{rel}:1", "file starts with a UTF-8 BOM")
    if b"\r" in data:
        line = data[: data.index(b"\r")].count(b"\n") + 1
        fail(errors, f"{rel}:{line}", "carriage return found; LF line endings required")
    if data and not data.endswith(b"\n"):
        fail(errors, f"{rel}:{data.count(chr(10).encode()) + 1}", "missing trailing newline")


def load_domains(errors):
    controls = {}
    domain_order = []
    for path in sorted(DOMAINS.glob("1[1-9]-*.md")):
        number = None
        name = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = DOMAIN_HEADING.match(line)
            if m:
                number, name = int(m.group(1)), m.group(2)
                domain_order.append((number, name))
                continue
            m = CONTROL_HEADING.match(line)
            if m:
                cid, title = m.group(1), m.group(2)
                if cid in controls:
                    fail(errors, str(path.relative_to(ROOT)), f"duplicate control heading {cid}")
                if number is None:
                    fail(errors, str(path.relative_to(ROOT)), f"control {cid} before domain heading")
                controls[cid] = (title, number)
    return controls, domain_order


def load_allowlist(errors, rel_path):
    path = CROSSWALKS / rel_path
    targets = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        if header != ["target_id", "target_title"]:
            fail(errors, f"crosswalks/{rel_path}:1", f"unexpected allowlist header {header!r}")
        for row in reader:
            targets[row[0]] = row[1]
    return targets


def canonical_csv_bytes(rows):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(HEADER)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def load_rows(errors, csv_path):
    data = csv_path.read_bytes()
    rel = csv_path.relative_to(ROOT)
    check_bytes(errors, csv_path, data)
    text = data.decode("utf-8")
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        table = list(reader)
    except csv.Error as exc:
        fail(errors, f"{rel}:{reader.line_num}", f"CSV parse error: {exc}")
        return []
    if not table or table[0] != HEADER:
        fail(errors, f"{rel}:1", f"header must be exactly {','.join(HEADER)}")
        return []
    rows = table[1:]
    for i, row in enumerate(rows, start=2):
        if len(row) != len(HEADER):
            fail(errors, f"{rel}:{i}", f"expected {len(HEADER)} fields, found {len(row)}")
            return []
    if canonical_csv_bytes(rows) != data:
        fail(errors, str(rel), "file is not in canonical RFC 4180 form (minimal quoting, LF)")
    return rows


def validate_rows(errors, rel, rows, controls, targets):
    seen_pairs = set()
    for i, (cid, ctitle, tid, ttitle, basis, note) in enumerate(rows, start=2):
        where = f"{rel}:{i}"
        if cid not in controls:
            fail(errors, where, f"control_id {cid!r} is not a control heading in domains/")
        elif ctitle != controls[cid][0]:
            fail(errors, where, f"control_title {ctitle!r} differs from the domain heading {controls[cid][0]!r}")
        if tid not in targets:
            fail(errors, where, f"target_id {tid!r} is not in the committed source allowlist")
        elif ttitle != targets[tid]:
            fail(errors, where, f"target_title differs from the allowlist row for {tid}")
        if basis not in BASIS_VOCABULARY:
            fail(errors, where, f"basis {basis!r} is outside the closed vocabulary {BASIS_VOCABULARY}")
        if not note.strip():
            fail(errors, where, "note is blank")
        elif len(note) > NOTE_MAX_CHARS:
            fail(errors, where, f"note is {len(note)} characters; the maximum is {NOTE_MAX_CHARS}")
        elif not note.endswith(".") or note.count(".") != 1 or note != note.strip():
            fail(errors, where, "note must be one sentence ending in a single full stop")
        if (cid, tid) in seen_pairs:
            fail(errors, where, f"duplicate row for ({cid}, {tid})")
        seen_pairs.add((cid, tid))
    ordered = [(r[0], r[2]) for r in rows]
    if ordered != sorted(ordered):
        fail(errors, str(rel), "rows are not sorted by control_id then target_id")


def md_cell(text):
    return text.replace("|", "\\|")


def render_md(spec, rows, controls, domain_order):
    mapped = {}
    for row in rows:
        mapped.setdefault(row[0], []).append(row)
    unmapped = sorted(cid for cid in controls if cid not in mapped)
    n_rows = len(rows)
    n_mapped = len(mapped)
    n_total = len(controls)
    lines = [f"# {spec['h1']}", ""]
    lines += [spec["statement"], ""]
    lines += [spec["source_line"], ""]
    lines += [
        f"{n_rows} rows; {n_mapped} of {n_total} controls have at least one row; "
        f"{len(unmapped)} are listed under no mapping asserted.",
        "",
    ]
    for number, name in domain_order:
        lines += [f"## Domain {number}: {name}", ""]
        domain_rows = [r for r in rows if controls[r[0]][1] == number]
        if domain_rows:
            lines += ["| Control | Target | Basis | Note |", "| --- | --- | --- | --- |"]
            for cid, ctitle, tid, ttitle, basis, note in domain_rows:
                lines.append(
                    f"| {md_cell(cid)}: {md_cell(ctitle)} | {md_cell(tid)}: {md_cell(ttitle)} "
                    f"| {md_cell(basis)} | {md_cell(note)} |"
                )
        else:
            lines.append("No rows are asserted in this domain.")
        lines.append("")
    lines += ["## Controls with no mapping asserted", ""]
    for cid in unmapped:
        lines.append(f"- {cid}: {controls[cid][0]}")
    return "\n".join(lines) + "\n"


def scan_banned(errors):
    for path in sorted(CROSSWALKS.rglob("*")):
        if not path.is_file():
            continue
        if CROSSWALKS / "sources" in path.parents:
            continue
        rel = path.relative_to(ROOT)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            m = BANNED_PATTERN.search(line)
            if m:
                fail(errors, f"{rel}:{lineno}", f"banned word {m.group(1)!r}")
            if "%" in line:
                fail(errors, f"{rel}:{lineno}", "percent sign found")


def main(argv):
    write = "--write" in argv
    errors = []
    controls, domain_order = load_domains(errors)
    if len(controls) != 72:
        fail(errors, "domains/", f"expected 72 control headings, found {len(controls)}")
    for spec in CROSSWALK_SET:
        csv_path = CROSSWALKS / spec["csv"]
        md_path = CROSSWALKS / spec["md"]
        if not csv_path.is_file():
            fail(errors, f"crosswalks/{spec['csv']}", "file is missing")
            continue
        targets = load_allowlist(errors, spec["allowlist"])
        rows = load_rows(errors, csv_path)
        if not rows:
            continue
        validate_rows(errors, csv_path.relative_to(ROOT), rows, controls, targets)
        rendered = render_md(spec, rows, controls, domain_order)
        if write:
            md_path.write_text(rendered, encoding="utf-8")
            print(f"wrote crosswalks/{spec['md']}")
        elif not md_path.is_file():
            fail(errors, f"crosswalks/{spec['md']}", "file is missing")
        else:
            committed = md_path.read_text(encoding="utf-8")
            if committed != rendered:
                for lineno, (a, b) in enumerate(
                    zip(committed.splitlines() + [""], rendered.splitlines() + [""]), start=1
                ):
                    if a != b:
                        fail(
                            errors,
                            f"crosswalks/{spec['md']}:{lineno}",
                            "committed file differs from the render of its CSV",
                        )
                        break
                else:
                    fail(errors, f"crosswalks/{spec['md']}", "committed file length differs from its render")
        mapped = {r[0] for r in rows}
        print(
            f"crosswalks/{spec['csv']}: {len(rows)} rows, {len(mapped)} of "
            f"{len(controls)} controls mapped, {len(controls) - len(mapped)} with no mapping asserted"
        )
    if not write:
        scan_banned(errors)
    if errors:
        print()
        for line in errors:
            print(line)
        print(f"\n{len(errors)} problem(s) found")
        return 1
    print("crosswalks: all checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
