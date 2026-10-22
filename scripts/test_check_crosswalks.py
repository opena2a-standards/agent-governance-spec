#!/usr/bin/env python3
"""Tests for scripts/check_crosswalks.py: the JSON control export, the render
comparison, the domain and control headings, the lines it splits a domain
file into, the attribute tables and the fenced code blocks around them, the
lines of fenced code blocks it does not read in specification.md and
conformance.md and does not take a ruled text from in crosswalks/README.md
and README.md, nor from an indented code block or an HTML block there, a
crosswalk row naming a control no domain file holds, the section 5.3 registry table, the section 3.5 applicability
matrix and the tier counts of section 3, the report on a byte that is not
UTF-8 in a file it reads, and the .gitattributes line-ending pins of the files
it compares byte for byte; the name its message gives a README.md passage it
requires verbatim; that its fence reader is the copy in
scripts/check_docs_prose.py; and the terms README.md and the docs pages that
took its reference text use in their prose.

Run from anywhere:  python3 scripts/test_check_crosswalks.py

Standard library only. The tests read the committed domain files,
controls.json, specification.md, README.md and the pages under docs/, and the source of the two checks, ask git for the eol attribute of the
byte-checked files, and write no tracked file: the synthetic domain files and
the repository copy that main() runs against are written to a temporary
directory, and bytecode caching is turned off before the import.
"""

import contextlib
import inspect
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_crosswalks as cc  # noqa: E402
import check_docs_prose as cdp  # noqa: E402

MEMBERS = ["id", "title", "domain", "severity", "status", "version"]
DEPRECATED_MEMBERS = ["id", "title", "domain", "severity", "status", "replacedBy", "version"]


def domain_file(controls):
    """A minimal domain 11 file holding the given (heading, attribute rows) pairs."""
    lines = ["# Domain 11: Trust Hierarchy", "", "## Controls", ""]
    for heading, rows in controls:
        lines += [heading, "", "| Attribute | Value |", "|-----------|-------|"]
        lines += [f"| **{name}** | {value} |" for name, value in rows]
        lines += ["", "**Description**: Text.", "", "```", "| **Status** | ignored |", "```", "", "---", ""]
    return "\n".join(lines)


def entries_for(controls):
    return entries_for_text(domain_file(controls))


def entries_for_text(text):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "11-trust-hierarchy.md").write_text(text, encoding="utf-8")
        errors = []
        found, _, attributes = cc.load_domains(errors, Path(tmp))
        entries = cc.control_entries(errors, found, attributes)
    return entries, errors


class CommittedExport(unittest.TestCase):
    def setUp(self):
        self.errors = []
        controls, _, attributes = cc.load_domains(self.errors)
        self.controls = controls
        self.entries = cc.control_entries(self.errors, controls, attributes)
        self.tiers = cc.control_tiers(self.errors, self.entries, attributes)

    def test_domain_files_are_valid_input(self):
        self.assertEqual(self.errors, [])

    def test_committed_file_equals_the_render_of_the_domain_files(self):
        committed = cc.read_committed(cc.ROOT / cc.CONTROLS_EXPORT)
        self.assertEqual(committed, cc.render_controls_json(self.entries).encode("utf-8"))

    def test_registry_table_in_the_specification_matches_the_domain_files(self):
        _, domain_order, _ = cc.load_domains([])
        errors = []
        text = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8")
        cc.check_registry_table(errors, cc.SPECIFICATION, text, self.entries, dict(domain_order))
        self.assertEqual(errors, [])

    def test_conformance_levels_list_every_critical_and_high_control_of_the_domain_files(self):
        _, _, attributes = cc.load_domains([])
        errors = []
        text = (cc.ROOT / cc.CONFORMANCE).read_text(encoding="utf-8")
        cc.check_conformance_levels(errors, cc.CONFORMANCE, text, self.entries, attributes)
        self.assertEqual(errors, [])
        for _, _, severity in cc.CONFORMANCE_LEVELS:
            self.assertTrue(any(e["severity"] == severity for e in self.entries), severity)

    def test_applicability_matrix_and_tier_counts_match_the_domain_files(self):
        errors = []
        text = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8")
        cc.check_applicability_matrix(errors, cc.SPECIFICATION, text, self.tiers)
        cc.check_tier_counts(errors, cc.SPECIFICATION, text, self.tiers)
        self.assertEqual(errors, [])

    def test_one_entry_per_control_heading_with_the_section_8_2_members(self):
        exported = json.loads((cc.ROOT / cc.CONTROLS_EXPORT).read_text(encoding="utf-8"))
        self.assertEqual(list(exported), ["controls"])
        entries = exported["controls"]
        self.assertEqual(len(entries), cc.CONTROL_COUNT)
        self.assertEqual(sorted(e["id"] for e in entries), sorted(self.controls))
        for entry in entries:
            expected = DEPRECATED_MEMBERS if entry["status"] == "deprecated" else MEMBERS
            self.assertEqual(list(entry), expected, entry["id"])
            self.assertEqual(entry["title"], self.controls[entry["id"]][0])
            self.assertEqual(entry["domain"], self.controls[entry["id"]][1])
            self.assertIn(entry["severity"], cc.SEVERITIES)
            self.assertIn(entry["status"], cc.STATUSES)

    def test_entries_are_in_domain_order_then_nnn(self):
        keys = [(e["domain"], int(e["id"].rsplit("-", 1)[1])) for e in self.entries]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(self.entries[0]["id"], "SOUL-TH-001")
        self.assertEqual(self.entries[-1]["domain"], 19)


class RenderComparison(unittest.TestCase):
    def test_missing_file_is_red(self):
        errors = []
        cc.compare_render(errors, "controls.json", None, "{}\n", "the domain files")
        self.assertEqual(errors, ["RED controls.json: file is missing"])

    def test_drifted_file_is_red_at_the_first_differing_line(self):
        errors = []
        cc.compare_render(errors, "controls.json", b'{\n  "a": 2\n}\n', '{\n  "a": 1\n}\n', "the domain files")
        self.assertEqual(errors, [
            "RED controls.json:2: committed file differs from the render of the domain files; "
            "run python3 scripts/check_crosswalks.py --write",
        ])

    def test_equal_file_is_green(self):
        errors = []
        cc.compare_render(errors, "controls.json", b"{}\n", "{}\n", "the domain files")
        self.assertEqual(errors, [])

    def compare_committed_bytes(self, data, rendered):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "controls.json"
            path.write_bytes(data)
            errors = []
            cc.compare_render(errors, "controls.json", cc.read_committed(path), rendered, "the domain files")
        return errors

    def test_committed_bytes_equal_to_the_render_are_green(self):
        rendered = '{\n  "a": 1\n}\n'
        self.assertEqual(self.compare_committed_bytes(rendered.encode("utf-8"), rendered), [])

    def test_crlf_or_cr_line_endings_are_red(self):
        rendered = '{\n  "a": 1\n}\n'
        for ending in ("\r\n", "\r"):
            errors = self.compare_committed_bytes(rendered.replace("\n", ending).encode("utf-8"), rendered)
            self.assertEqual(errors, ["RED controls.json:1: carriage return found; LF line endings required; "
                                      "run python3 scripts/check_crosswalks.py --write"], repr(ending))

    def test_one_crlf_line_among_lf_lines_is_red_at_that_line(self):
        rendered = '{\n  "a": 1,\n  "b": 2\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": 1,\r\n  "b": 2\n}\n', rendered)
        self.assertEqual(errors, ["RED controls.json:2: carriage return found; LF line endings required; "
                                  "run python3 scripts/check_crosswalks.py --write"])

    def test_line_endings_and_a_content_difference_are_both_red(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b'{\r\n  "a": 2\r\n}\r\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:1: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:2: committed file differs from the render of the domain files; "
            "run python3 scripts/check_crosswalks.py --write",
        ])

    def test_cr_in_place_of_an_lf_before_a_blank_line_is_also_a_difference(self):
        rendered = '{\n  "a": 1,\n\n  "b": 2\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": 1,\r\n  "b": 2\n}\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:2: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:3: committed file differs from the render of the domain files; "
            "run python3 scripts/check_crosswalks.py --write",
        ])

    def test_cr_in_place_of_an_lf_before_a_final_blank_line_is_shorter(self):
        rendered = '{\n  "a": 1\n}\n\n'
        errors = self.compare_committed_bytes(b'{\n  "a": 1\n}\r\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:3: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:4: committed file, with line endings read as LF, is shorter than its "
            "render of the domain files, which continues here; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_utf8_byte_order_mark_is_red(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b"\xef\xbb\xbf" + rendered.encode("utf-8"), rendered)
        self.assertEqual(errors, [
            "RED controls.json:1: file starts with a UTF-8 BOM; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_invalid_utf8_is_red_without_a_traceback(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": \xff\n}\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:2: byte 0xFF is not UTF-8; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_line_of_a_byte_that_is_not_utf8_is_counted_before_carriage_returns_are_read_as_lf(self):
        # Read as LF, the CR inside line 3 would put the byte on line 4.
        errors = self.compare_committed_bytes(b"a\nb\nc\r\xff\n", "a\nb\nc\nd\n")
        self.assertEqual(errors, [
            "RED controls.json:3: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:3: byte 0xFF is not UTF-8; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_length_difference_is_reported_only_when_the_lengths_differ(self):
        rendered = '{\n  "a": 1\n}\n'
        self.assertEqual(self.compare_committed_bytes(b'{\n  "a": 1\n}', rendered), [
            "RED controls.json:3: committed file is shorter than its render of the domain files, "
            "which continues here; run python3 scripts/check_crosswalks.py --write",
        ])
        self.assertEqual(self.compare_committed_bytes(b'{\n  "a": 1\n}\n\n', rendered), [
            "RED controls.json:4: committed file is longer than its render of the domain files, "
            "which ends here; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_length_difference_names_the_text_read_with_lf_line_endings(self):
        # Both inputs are 6 bytes: the committed file is shorter only once CRLF is read as LF.
        self.assertEqual(self.compare_committed_bytes(b"a\r\nb\r\n", "a\nb\nc\n"), [
            "RED controls.json:1: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:3: committed file, with line endings read as LF, is shorter than its "
            "render of the domain files, which continues here; run python3 scripts/check_crosswalks.py --write",
        ])
        self.assertEqual(self.compare_committed_bytes(b"a\rb\rc\r\r", "a\nb\nc\n"), [
            "RED controls.json:1: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:4: committed file, with line endings read as LF, is longer than its "
            "render of the domain files, which ends here; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_length_difference_names_the_text_with_the_bom_removed(self):
        # 7 committed bytes against a 6-byte render: shorter only once the BOM is removed.
        self.assertEqual(self.compare_committed_bytes(b"\xef\xbb\xbfa\nb\n", "a\nb\nc\n"), [
            "RED controls.json:1: file starts with a UTF-8 BOM; run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:3: committed file, with its BOM removed, is shorter than its "
            "render of the domain files, which continues here; run python3 scripts/check_crosswalks.py --write",
        ])
        self.assertEqual(self.compare_committed_bytes(b"\xef\xbb\xbfa\r\nb\r\nc\r\n\r\n", "a\nb\nc\n"), [
            "RED controls.json:1: file starts with a UTF-8 BOM; run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:1: carriage return found; LF line endings required; "
            "run python3 scripts/check_crosswalks.py --write",
            "RED controls.json:4: committed file, with its BOM removed and line endings read as LF, is longer "
            "than its render of the domain files, which ends here; run python3 scripts/check_crosswalks.py --write",
        ])


TIME_BOUND_SKIP = "the run without -O checks the time bound"


def skip_the_time_bound_when_optimized(test):
    # scripts/test_stripped_docstrings.py runs this file again under python3 -O and -OO, where a missed time bound
    # would fail that run too, so only the run without -O checks the bound.
    if sys.flags.optimize >= 1:
        test.skipTest(TIME_BOUND_SKIP)


def int_digit_limit(test):
    # The most digits int() converts. An interpreter without a limit converts a run of any length, so there is no run
    # that read_int reports and the test is skipped.
    limit = getattr(sys, "get_int_max_str_digits", lambda: 0)()
    if not limit:
        test.skipTest("int() converts a run of any number of digits in this interpreter")
    return limit


def too_long(what, limit):
    # The red message for a run of limit + 1 digits, which int() refuses.
    return f"{what} has {limit + 1} digits, more than the {limit} digits Python converts to an integer; it is not read"


ACTIVE = ("### SOUL-TH-001: First", [("ID", "SOUL-TH-001"), ("Severity", "HIGH")])
# The red line for a line that is not blank directly under the attribute table of SOUL-TH-001.
NOT_BLANK_UNDER_THE_TABLE = ("line directly under the attribute table of SOUL-TH-001 is not blank; "
                             "a blank line must end the table")


class EntryAttributes(unittest.TestCase):
    def test_absent_status_and_version_are_written_as_active_and_1_0_0(self):
        entries, errors = entries_for([ACTIVE])
        self.assertEqual(errors, [])
        self.assertEqual(entries, [{
            "id": "SOUL-TH-001", "title": "First", "domain": 11, "severity": "HIGH",
            "status": "active", "version": "1.0.0",
        }])

    def test_deprecated_entry_carries_replaced_by(self):
        entries, errors = entries_for([
            ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW"),
                                        ("Status", "`deprecated`"), ("Replaced by", "SOUL-TH-001"),
                                        ("Version", "1.1.0")]),
            ACTIVE,
        ])
        self.assertEqual(errors, [])
        self.assertEqual([e["id"] for e in entries], ["SOUL-TH-001", "SOUL-TH-002"])
        self.assertEqual(list(entries[1]), DEPRECATED_MEMBERS)
        self.assertEqual(entries[1]["replacedBy"], "SOUL-TH-001")
        self.assertEqual(entries[1]["version"], "1.1.0")

    def test_draft_entry_is_written_with_its_status(self):
        entries, errors = entries_for([
            ACTIVE, ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "draft")]),
        ])
        self.assertEqual(errors, [])
        self.assertEqual(entries[1]["status"], "draft")
        self.assertEqual(list(entries[1]), MEMBERS)

    def assert_red(self, rows, fragment):
        entries, errors = entries_for([ACTIVE, ("### SOUL-TH-002: Second", rows)])
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(fragment, errors[0])
        self.assertTrue(errors[0].startswith("RED "), errors[0])

    def assert_red_exactly(self, rows, message):
        entries, errors = entries_for([ACTIVE, ("### SOUL-TH-002: Second", rows)])
        self.assertEqual(len(errors), 1, errors)
        self.assertRegex(errors[0], r"^RED .*11-trust-hierarchy\.md:\d+: ")
        self.assertEqual(errors[0].split(": ", 1)[1], message)

    def test_deprecated_without_replaced_by_is_red(self):
        self.assert_red_exactly([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "deprecated")],
                                "SOUL-TH-002 is deprecated and has no Replaced by attribute")

    def test_replaced_by_on_an_entry_that_is_not_deprecated_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Replaced by", "SOUL-TH-001")],
                        "Replaced by")

    def test_replaced_by_must_name_another_control_heading(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "deprecated"),
                         ("Replaced by", "SOUL-TH-009")], "SOUL-TH-009")
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "deprecated"),
                         ("Replaced by", "SOUL-TH-002")], "itself")

    def test_status_outside_the_vocabulary_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "retired")], "retired")

    def test_severity_outside_the_vocabulary_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "Medium")], "Medium")
        self.assert_red([("ID", "SOUL-TH-002")], "Severity")

    def test_version_that_is_not_semantic_is_red(self):
        for version in ("1.1", "1.1.0-rc1", "01.1.0", "1.01.0", "1.1.\u0661", "1.1.0 x"):
            self.assert_red_exactly([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Version", version)],
                                    f"Version {version!r} of SOUL-TH-002 is not MAJOR.MINOR.PATCH")

    def test_version_with_zero_components_is_green(self):
        entries, errors = entries_for([
            ACTIVE, ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Version", "0.10.0")]),
        ])
        self.assertEqual(errors, [])
        self.assertEqual(entries[1]["version"], "0.10.0")

    def test_id_attribute_that_differs_from_the_heading_is_red(self):
        self.assert_red([("ID", "SOUL-TH-003"), ("Severity", "LOW")], "SOUL-TH-003")

    def test_repeated_attribute_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Severity", "HIGH")], "Severity")

    def test_attribute_name_outside_the_known_set_is_red(self):
        self.assert_red_exactly([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Statuss", "deprecated")],
                                f"attribute 'Statuss' of SOUL-TH-002 is outside {cc.ATTRIBUTES}")

    def test_table_row_that_is_not_an_attribute_row_is_red(self):
        text = domain_file([ACTIVE]).replace("| **Severity** | HIGH |", "| **Severity** | HIGH |\n| Status | deprecated |")
        _, errors = entries_for_text(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].endswith(": row of the attribute table of SOUL-TH-001 is not an attribute row"),
                        errors[0])

    def test_attribute_row_separated_from_the_table_is_red(self):
        text = domain_file([ACTIVE]).replace("**Description**: Text.", "| **Status** | deprecated |\n\n**Description**: Text.")
        _, errors = entries_for_text(text)
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].endswith(
            ": attribute row separated from the attribute table of SOUL-TH-001; it is not read"), errors[0])

    def test_indented_attribute_row_after_the_table_is_red(self):
        text = domain_file([ACTIVE])
        for indent in (" ", "   ", "    ", "\t"):
            row = f"{indent}| **Status** | deprecated |"
            for place, variant in (
                    ("after the blank line that ends the table",
                     text.replace("**Description**: Text.", f"{row}\n\n**Description**: Text.")),
                    ("on the line under the last row of the table",
                     text.replace("| **Severity** | HIGH |\n", f"| **Severity** | HIGH |\n{row}\n"))):
                with self.subTest(row=row, place=place):
                    lineno = variant.splitlines().index(row) + 1
                    entries, errors = entries_for_text(variant)
                    self.assertEqual(len(errors), 1, errors)
                    self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: attribute row separated "
                                                       "from the attribute table of SOUL-TH-001; it is not read"),
                                    errors[0])
                    self.assertEqual(entries[0]["status"], "active")

    def test_attribute_row_without_its_leading_pipe_after_the_table_is_red(self):
        # Unindented and directly under the last row of the table, GFM renders such a row as a row of that table.
        text = domain_file([ACTIVE])
        for indent in ("", " ", "   ", "    ", "\t"):
            for row in (f"{indent}**Status** | deprecated |", f"{indent}**Status** | deprecated"):
                for place, variant in (
                        ("on the line under the last row of the table",
                         text.replace("| **Severity** | HIGH |\n", f"| **Severity** | HIGH |\n{row}\n")),
                        ("after the blank line that ends the table",
                         text.replace("**Description**: Text.", f"{row}\n\n**Description**: Text."))):
                    with self.subTest(row=row, place=place):
                        lineno = variant.splitlines().index(row) + 1
                        entries, errors = entries_for_text(variant)
                        self.assertEqual(len(errors), 1, errors)
                        self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: attribute row separated "
                                                           "from the attribute table of SOUL-TH-001; it is not read"),
                                        errors[0])
                        self.assertEqual(entries[0]["status"], "active")

    def test_line_directly_under_the_table_that_is_not_blank_is_red(self):
        # GFM renders a line there that is not blank as a row of the table unless the line starts another block.
        # A line of a no-break space is not blank to GFM, which counts only spaces and tabs as blank.
        text = domain_file([ACTIVE])
        for inserted in ("Status | deprecated |", "**Status**  | deprecated |", "**Status**|deprecated|",
                         "   | **Status** | deprecated", "**Description**: Text.", "\xa0", "---",
                         "~~~~\n| **Status** | ignored |\n~~~~"):
            with self.subTest(inserted=inserted):
                variant = text.replace("| **Severity** | HIGH |\n", f"| **Severity** | HIGH |\n{inserted}\n")
                lineno = variant.splitlines().index("| **Severity** | HIGH |") + 2
                entries, errors = entries_for_text(variant)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: {NOT_BLANK_UNDER_THE_TABLE}"),
                                errors[0])
                self.assertEqual(entries[0]["status"], "active")

    def test_line_under_the_table_that_starts_with_a_character_splitlines_ends_a_line_at_is_red(self):
        # GFM ends a line only at LF, CR LF, or CR, so each inserted line is one line, a row of the table to GFM.
        text = domain_file([ACTIVE])
        for char in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\N{LINE SEPARATOR}", "\N{PARAGRAPH SEPARATOR}"):
            with self.subTest(char=char):
                variant = text.replace("| **Severity** | HIGH |\n",
                                       f"| **Severity** | HIGH |\n{char}Status | deprecated |\n")
                lineno = variant.split("\n").index("| **Severity** | HIGH |") + 2
                entries, errors = entries_for_text(variant)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: {NOT_BLANK_UNDER_THE_TABLE}"),
                                errors[0])
                self.assertEqual(entries[0]["status"], "active")

    def test_control_heading_directly_under_the_table_is_red_and_starts_its_control(self):
        second = ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW")])
        lines = domain_file([ACTIVE, second]).split("\n")
        last = lines.index("| **Severity** | HIGH |")
        entries, errors = entries_for_text("\n".join(lines[:last + 1] + lines[lines.index(second[0]):]))
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{last + 2}: {NOT_BLANK_UNDER_THE_TABLE}"), errors[0])
        self.assertEqual([(e["id"], e["severity"]) for e in entries], [("SOUL-TH-001", "HIGH"), ("SOUL-TH-002", "LOW")])

    def test_line_of_spaces_and_tabs_directly_under_the_table_is_green(self):
        text = domain_file([ACTIVE])
        self.assertIn("| **Severity** | HIGH |\n\n", text)
        for blank in (" ", "   ", "\t", " \t "):
            with self.subTest(blank=blank):
                entries, errors = entries_for_text(text.replace("| **Severity** | HIGH |\n\n",
                                                                f"| **Severity** | HIGH |\n{blank}\n"))
                self.assertEqual(errors, [])
                self.assertEqual(entries[0]["status"], "active")

    def test_table_that_ends_the_file_is_green(self):
        text = domain_file([ACTIVE])
        last = "| **Severity** | HIGH |"
        for end in ("", "\n"):
            with self.subTest(end=end):
                entries, errors = entries_for_text(text[:text.index(last) + len(last)] + end)
                self.assertEqual(errors, [])
                self.assertEqual(entries[0]["severity"], "HIGH")

    def test_attribute_row_without_its_leading_pipe_inside_a_fenced_block_is_not_read(self):
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        entries, errors = entries_for_text(domain_file([ACTIVE]).replace(example, "```\n**Status** | ignored |\n```"))
        self.assertEqual(errors, [])
        self.assertEqual(entries[0]["status"], "active")

    def test_attribute_row_inside_a_fenced_block_is_not_read(self):
        # domain_file puts "| **Status** | ignored |" in a fenced block after every table.
        self.assertIn("```\n| **Status** | ignored |\n```", domain_file([ACTIVE]))
        entries, errors = entries_for([ACTIVE])
        self.assertEqual(errors, [])
        self.assertEqual(entries[0]["status"], "active")

    def test_attribute_row_inside_a_tilde_fenced_block_is_not_read(self):
        text = domain_file([ACTIVE]).replace("```", "~~~")
        self.assertIn("~~~\n| **Status** | ignored |\n~~~", text)
        entries, errors = entries_for_text(text)
        self.assertEqual(errors, [])
        self.assertEqual(entries[0]["status"], "active")

    def test_fence_closes_only_at_a_run_of_its_own_character_at_least_as_long(self):
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block, red in (("~~~\n```\n| **Status** | ignored |\n```\n~~~", False),
                           ("````\n```\n| **Status** | ignored |\n```\n````", False),
                           ("~~~~\n~~~\n| **Status** | ignored |\n~~~\n~~~~", False),
                           ("~~~\n```\n~~~\n| **Status** | ignored |", True)):
            with self.subTest(block=block):
                _, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual([e.split(": ", 1)[1] for e in errors],
                                 ["attribute row separated from the attribute table of SOUL-TH-001; it is not read"]
                                 if red else [])

    def test_fence_opens_and_closes_only_after_at_most_three_spaces(self):
        # Markdown reads a run indented four spaces, or by a tab, as text and not as a fence, whether the run would
        # open the block or close it. A run indented one to three spaces closes the block, so the row under it is red.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block, red in (("   ```\n| **Status** | ignored |\n ```\n| **Status** | deprecated |", True),
                           (" ~~~\n| **Status** | ignored |\n   ~~~\n| **Status** | deprecated |", True),
                           ("    ```\n| **Status** | ignored |\n    ```", True),
                           ("\t~~~\n| **Status** | ignored |\n\t~~~", True),
                           ("   \t```\n| **Status** | ignored |\n   \t```", True),
                           ("```\n    ```\n| **Status** | ignored |\n```", False),
                           ("~~~\n\t~~~\n| **Status** | ignored |\n~~~", False)):
            with self.subTest(block=block):
                _, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual([e.split(": ", 1)[1] for e in errors],
                                 ["attribute row separated from the attribute table of SOUL-TH-001; it is not read"]
                                 if red else [])

    def test_backtick_line_with_a_backtick_after_its_run_opens_no_fence(self):
        # The info string of a backtick fence holds no backtick, so Markdown reads such a line as text. The info string
        # of a tilde fence may hold one.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block, red in (("```a``` b\n| **Status** | ignored |", True),
                           ("```` sh`\n| **Status** | ignored |", True),
                           ("```sh\n| **Status** | ignored |\n```", False),
                           ("~~~ a ``` b\n| **Status** | ignored |\n~~~", False)):
            with self.subTest(block=block):
                _, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual([e.split(": ", 1)[1] for e in errors],
                                 ["attribute row separated from the attribute table of SOUL-TH-001; it is not read"]
                                 if red else [])

    def test_tables_after_a_backtick_line_with_a_backtick_after_its_run_are_read(self):
        second = ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW")])
        text = domain_file([ACTIVE, second]).replace("**Description**: Text.", "```a``` b\n\n**Description**: Text.", 1)
        entries, errors = entries_for_text(text)
        self.assertEqual(errors, [])
        self.assertEqual([(e["id"], e["severity"]) for e in entries], [("SOUL-TH-001", "HIGH"), ("SOUL-TH-002", "LOW")])

    def test_fence_closes_only_at_a_line_with_nothing_but_spaces_and_tabs_after_its_run(self):
        # A no-break space (U+00A0) after the run is text, so the row under that line is inside the block.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block, red in (("```\n```\N{NO-BREAK SPACE}\n| **Status** | ignored |\n```", False),
                           ("~~~\n~~~\N{NO-BREAK SPACE}\n| **Status** | ignored |\n~~~", False),
                           ("```\n``` \t\n| **Status** | ignored |", True)):
            with self.subTest(block=block):
                _, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual([e.split(": ", 1)[1] for e in errors],
                                 ["attribute row separated from the attribute table of SOUL-TH-001; it is not read"]
                                 if red else [])

    def test_attribute_row_inside_a_fenced_block_in_a_list_item_is_not_read(self):
        # Inside a list item Markdown counts the indentation of a fence from the item's content column.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block in ("1. Example:\n\n    ```\n    | **Status** | ignored |\n    ```",
                      "10. Example:\n    ```\n    | **Status** | ignored |\n    ```",
                      "- Example:\n\n  ```\n  | **Status** | ignored |\n      ```\n  | **Status** | ignored |\n     ```",
                      "- ```\n  | **Status** | ignored |\n  ```"):
            with self.subTest(block=block):
                entries, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual(errors, [])
                self.assertEqual(entries[0]["status"], "active")

    def test_fenced_block_in_a_list_item_closes_where_markdown_closes_it(self):
        # A run indented at most three spaces past the content column of the item closes the block, and so does a line
        # that ends the item; the row under the block is then red at its line.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        row = "| **Status** | deprecated |"
        for block in ("- Example:\n\n  ```\n  text\n    ```\n\n" + row,
                      "- Example:\n\n  ```\n  text\n     ```\n  " + row,
                      "1.  Example:\n\n    ```\n    text\n       ```\n\n" + row,
                      "- Example:\n\n  ```\n  text\n\t```\n\n" + row,
                      "- Example:\n\n  ```\n  text\n" + row):
            with self.subTest(block=block):
                variant = domain_file([ACTIVE]).replace(example, block)
                lineno = [line.strip() for line in variant.splitlines()].index(row) + 1
                entries, errors = entries_for_text(variant)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: attribute row separated from the "
                                                   "attribute table of SOUL-TH-001; it is not read"), errors[0])
                self.assertEqual(entries[0]["status"], "active")

    def test_attribute_row_inside_a_fenced_block_after_an_html_block_or_a_block_quote_is_not_read(self):
        # A list marker inside an HTML block opens no list item, and a block quote line ends the list item above it,
        # so the block after them opens outside a list item and its line indented two spaces closes it.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        for block in ("<!-- notes\n- update the table\n-->\n\n  ```\n| **Status** | ignored |\n  ```",
                      "<details>\n- item\n</details>\n\n  ```\n| **Status** | ignored |\n  ```",
                      "- Example:\n> quote\n\n  ```\n| **Status** | ignored |\n  ```"):
            with self.subTest(block=block):
                entries, errors = entries_for_text(domain_file([ACTIVE]).replace(example, block))
                self.assertEqual(errors, [])
                self.assertEqual(entries[0]["status"], "active")

    def test_fence_line_inside_an_html_block_opens_no_fence(self):
        # Markdown reads the lines of an HTML block as HTML, so its fence line opens no code block, and the row, inside
        # the block or after its end, is red at its line.
        example = "```\n| **Status** | ignored |\n```"
        self.assertIn(example, domain_file([ACTIVE]))
        row = "| **Status** | deprecated |"
        for block in ("<div>\n```\n" + row + "\n```\n</div>", "<!--\n```\n-->\n" + row):
            with self.subTest(block=block):
                variant = domain_file([ACTIVE]).replace(example, block)
                lineno = variant.split("\n").index(row) + 1
                entries, errors = entries_for_text(variant)
                self.assertEqual(len(errors), 1, errors)
                self.assertTrue(errors[0].endswith(f"11-trust-hierarchy.md:{lineno}: attribute row separated from the "
                                                   "attribute table of SOUL-TH-001; it is not read"), errors[0])
                self.assertEqual(entries[0]["status"], "active")

    def test_domain_or_control_heading_inside_a_fenced_block_is_not_read(self):
        # Markdown reads the lines of a fenced block as code, so a heading there starts no domain and no control, and
        # the attribute table under it sets no attribute.
        example = "```\n| **Status** | ignored |\n```"
        second = ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW")])
        text = domain_file([ACTIVE, second])
        self.assertIn(example, text)
        table = "\n\n| Attribute | Value |\n|-----------|-------|\n| **Status** | deprecated |"
        for heading in ("### SOUL-TH-001: First", "### SOUL-TH-002: Second", "### SOUL-TH-003: Third",
                        "# Domain 11: Trust Hierarchy", "# Domain 12: Capability Boundaries"):
            for block in (f"```markdown\n{heading}\n```", f"~~~\n{heading}{table}\n~~~"):
                with self.subTest(block=block), tempfile.TemporaryDirectory() as tmp:
                    (Path(tmp) / "11-trust-hierarchy.md").write_text(text.replace(example, block, 1), encoding="utf-8")
                    errors = []
                    found, domain_order, attributes = cc.load_domains(errors, Path(tmp))
                    entries = cc.control_entries(errors, found, attributes)
                    self.assertEqual(errors, [])
                    self.assertEqual(domain_order, [(11, "Trust Hierarchy")])
                    self.assertEqual([(e["id"], e["domain"], e["severity"], e["status"]) for e in entries],
                                     [("SOUL-TH-001", 11, "HIGH", "active"), ("SOUL-TH-002", 11, "LOW", "active")])

    def test_heading_that_ends_a_list_item_holding_a_fenced_block_is_read(self):
        # A line that is not indented ends the list item above it and the fenced block the item holds, so Markdown
        # reads the heading of SOUL-TH-002 under a block that no line closes as a heading.
        second = ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW")])
        example = "```\n| **Status** | ignored |\n```\n\n---\n\n"
        text = domain_file([ACTIVE, second])
        self.assertIn(example + second[0], text)
        block = "- Example:\n\n  ```\n  | **Status** | ignored |\n"
        entries, errors = entries_for_text(text.replace(example, block, 1))
        self.assertEqual(errors, [])
        self.assertEqual([(e["id"], e["severity"]) for e in entries], [("SOUL-TH-001", "HIGH"), ("SOUL-TH-002", "LOW")])

    def test_long_row_that_does_not_match_is_rejected_in_linear_time(self):
        skip_the_time_bound_when_optimized(self)
        row = "| **x** | " + "** | " * 20000 + "x"
        start = time.perf_counter()
        self.assertIsNone(cc.ATTRIBUTE_ROW.match(row))
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_heading_with_a_long_run_of_interior_spaces_is_read_in_linear_time(self):
        skip_the_time_bound_when_optimized(self)
        title = "a" + " " * 40000 + "b"
        for pattern, line in ((cc.CONTROL_HEADING, f"### SOUL-TH-001: {title}"),
                              (cc.DOMAIN_HEADING, f"# Domain 11: {title}")):
            with self.subTest(pattern=pattern.pattern):
                start = time.perf_counter()
                m = pattern.match(line)
                elapsed = time.perf_counter() - start
                self.assertLess(elapsed, 1.0)
                self.assertEqual(m.group(2), title)

    def test_heading_title_is_read_up_to_its_last_character_that_is_not_a_space(self):
        # A title of spaces alone is read as its first space, as the earlier (.+?)\s*$ form read it.
        for title, read in (("Title", "Title"), ("Two  words \t ", "Two  words"), ("  Indented", "  Indented"),
                            ("   ", " "), ("", None)):
            for pattern, prefix in ((cc.CONTROL_HEADING, "### SOUL-TH-001: "), (cc.DOMAIN_HEADING, "# Domain 11: ")):
                with self.subTest(title=title, pattern=pattern.pattern):
                    m = pattern.match(prefix + title)
                    self.assertEqual(m and m.group(2), read)

    def test_control_in_a_domain_file_without_a_domain_heading_is_red_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "11-trust-hierarchy.md").write_text(domain_file([ACTIVE]), encoding="utf-8")
            (Path(tmp) / "12-capability-boundaries.md").write_text(
                domain_file([("### SOUL-CB-001: Other", [("ID", "SOUL-CB-001"), ("Severity", "LOW")])])
                .replace("# Domain 11: Trust Hierarchy\n", ""), encoding="utf-8")
            errors = []
            found, _, attributes = cc.load_domains(errors, Path(tmp))
            entries = cc.control_entries(errors, found, attributes)
        self.assertEqual([e["id"] for e in entries], ["SOUL-TH-001", "SOUL-CB-001"])
        self.assertEqual(len(errors), 1, errors)
        self.assertTrue(errors[0].endswith("12-capability-boundaries.md: control SOUL-CB-001 before domain heading"),
                        errors[0])

    def test_domain_number_longer_than_int_converts_is_red_at_its_line_without_a_traceback(self):
        limit = int_digit_limit(self)
        heading = f"# Domain {'1' * (limit + 1)}: Long"
        second = ("### SOUL-TH-002: Second", [("ID", "SOUL-TH-002"), ("Severity", "LOW")])
        text = domain_file([ACTIVE, second])
        # The heading in place of the domain heading of the file, and added above the second control. The controls under
        # it have no domain number, and are not red as above every domain heading.
        for variant, order, domains in (
                (text.replace("# Domain 11: Trust Hierarchy", heading, 1), [], [None, None]),
                (text.replace("### SOUL-TH-002", f"{heading}\n\n### SOUL-TH-002", 1), [(11, "Trust Hierarchy")],
                 [11, None])):
            lineno = variant.split("\n").index(heading) + 1
            with self.subTest(line=lineno), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "11-trust-hierarchy.md"
                path.write_text(variant, encoding="utf-8")
                errors = []
                found, domain_order, attributes = cc.load_domains(errors, Path(tmp))
                entries = cc.control_entries(errors, found, attributes)
                self.assertEqual(errors, [f"RED {cc.display(path)}:{lineno}: {too_long('domain number', limit)}"])
                self.assertEqual(domain_order, order)
                self.assertEqual([(e["id"], e["domain"]) for e in entries],
                                 [("SOUL-TH-001", domains[0]), ("SOUL-TH-002", domains[1])])


class GfmLines(unittest.TestCase):
    def test_lines_end_at_lf_cr_lf_and_cr_only(self):
        line = "d\ve\ff\x1cg\x1dh\x1ei\x85j\N{LINE SEPARATOR}k\N{PARAGRAPH SEPARATOR}l"
        self.assertEqual(cc.gfm_lines(f"a\r\nb\rc\n{line}\n"), ["a", "b", "c", line])

    def test_line_ending_at_the_end_of_the_text_starts_no_further_line_as_with_splitlines(self):
        for text, lines in (("", []), ("a", ["a"]), ("a\n", ["a"]), ("a\r", ["a"]), ("a\r\n", ["a"]),
                            ("\n", [""]), ("a\n\n", ["a", ""]), ("a\r\r\n", ["a", ""])):
            with self.subTest(text=text):
                self.assertEqual(cc.gfm_lines(text), lines)
                self.assertEqual(text.splitlines(), lines)


class FencedLines(unittest.TestCase):
    def test_lines_from_the_line_that_opens_a_block_to_the_line_that_closes_it_are_fenced(self):
        lines = ["a", "```markdown", "### b", "~~~", "   ```", "c", "~~~~", "```", "~~~~~", "d"]
        self.assertEqual(cc.fenced_lines(lines), [False, True, True, True, True, False, True, True, True, False])
        # A run indented four spaces or by a tab closes no block.
        lines = ["```", "    ```", "\t```", "### b", "```", "c"]
        self.assertEqual(cc.fenced_lines(lines), [True, True, True, True, True, False])

    def test_block_that_no_line_closes_runs_to_the_end_of_the_text(self):
        self.assertEqual(cc.fenced_lines(["a", "~~~", "b", "```"]), [False, True, True, True])
        self.assertEqual(cc.fenced_lines(["````", "```"]), [True, True])

    def test_line_that_markdown_does_not_read_as_a_fence_opens_no_block(self):
        for line in ("    ```", "\t~~~", "```a``` b", "``", "~~"):
            with self.subTest(line=line):
                self.assertEqual(cc.fenced_lines([line, "### b"]), [False, False])

    def test_fence_in_a_list_item_is_read_as_in_a_domain_file(self):
        # The reader of load_domains (CodeFences): a fence indented four spaces under "1. " opens a block, counted from
        # the item's content column, and a line that ends the item ends the block it holds, so "### c" is a heading.
        lines = ["1. Example:", "", "    ```", "    ### b", "    ```", "### c"]
        self.assertEqual(cc.fenced_lines(lines), [False, False, True, True, True, False])
        lines = ["- a", "  ```", "  ### b", "### c", "```"]
        self.assertEqual(cc.fenced_lines(lines), [False, True, True, False, True])


class UnfencedRuns(unittest.TestCase):
    def test_runs_are_the_lines_between_fenced_blocks_joined_by_lf(self):
        # The tilde block that no line closes runs to the end of the text, so "e" is part of it.
        lines = ["a", "", "b", "```", "c", "```", "d", "~~~", "e"]
        self.assertEqual(cc.unfenced_runs(lines), ["a\n\nb", "d"])
        self.assertEqual(cc.unfenced_runs(["```", "a"]), [])
        self.assertEqual(cc.unfenced_runs([]), [])

    def test_fence_in_a_list_item_is_read_as_by_fenced_lines(self):
        # The line "c" ends the list item, and with it the block the item holds.
        self.assertEqual(cc.unfenced_runs(["- a", "  ```", "  b", "c"]), ["- a", "c"])


class TextRuns(unittest.TestCase):
    def test_lines_of_code_blocks_and_html_blocks_are_left_out(self):
        lines = ["a", "", "    code", "", "<!--", "b", "-->", "c", "```", "d", "```", "<div>", "e", "", "f"]
        # The blank line that ends the <div> block is the line that holds the end of its kind, as CodeFences reads it.
        self.assertEqual(cc.text_runs(lines), ["a\n", "", "c", "f"])

    def test_indented_line_that_continues_a_paragraph_or_a_list_item_is_text(self):
        self.assertEqual(cc.text_runs(["a", "    b"]), ["a\n    b"])
        self.assertEqual(cc.text_runs(["- a", "", "    b"]), ["- a\n\n    b"])
        # Four spaces past the content column of the item open an indented code block inside it.
        self.assertEqual(cc.text_runs(["- a", "", "      b"]), ["- a\n"])

    def test_html_comment_after_text_on_its_line_is_not_an_html_block(self):
        self.assertEqual(cc.text_runs(["a <!-- b -->"]), ["a <!-- b -->"])
        # A comment at the start of a line opens an HTML block, which interrupts a paragraph.
        self.assertEqual(cc.text_runs(["a", "<!-- b -->"]), ["a"])


def deprecated(cid, successor):
    return (f"### {cid}: Withdrawn", [("ID", cid), ("Severity", "LOW"), ("Status", "deprecated"),
                                       ("Replaced by", successor)])


class ReplacementChains(unittest.TestCase):
    def test_chain_through_a_deprecated_successor_to_an_active_control_is_green(self):
        _, errors = entries_for([ACTIVE, deprecated("SOUL-TH-002", "SOUL-TH-003"),
                                 deprecated("SOUL-TH-003", "SOUL-TH-001")])
        self.assertEqual(errors, [])

    def test_cycle_of_deprecated_controls_is_red(self):
        _, errors = entries_for([ACTIVE, deprecated("SOUL-TH-002", "SOUL-TH-003"),
                                 deprecated("SOUL-TH-003", "SOUL-TH-002")])
        self.assertEqual([e.split(": ", 1)[1] for e in errors], [
            "Replaced by chain SOUL-TH-002 -> SOUL-TH-003 -> SOUL-TH-002 returns to SOUL-TH-002 "
            "without reaching an active control",
            "Replaced by chain SOUL-TH-003 -> SOUL-TH-002 -> SOUL-TH-003 returns to SOUL-TH-003 "
            "without reaching an active control",
        ])

    def test_chain_ending_at_a_draft_control_is_red(self):
        _, errors = entries_for([
            ACTIVE, deprecated("SOUL-TH-002", "SOUL-TH-003"),
            ("### SOUL-TH-003: Draft", [("ID", "SOUL-TH-003"), ("Severity", "LOW"), ("Status", "draft")]),
        ])
        self.assertEqual([e.split(": ", 1)[1] for e in errors], [
            "Replaced by chain SOUL-TH-002 -> SOUL-TH-003 ends at a draft control; "
            "it must end at an active control",
        ])


# The characters other than LF and CR at which str.splitlines ends a line. GFM ends a line only at LF, CR LF, or CR.
SPLITLINES_ONLY = ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\N{LINE SEPARATOR}", "\N{PARAGRAPH SEPARATOR}")

REGISTRY = """# Spec

### 5.3 Complete Control Registry

| ID | Name | Domain | Severity |
|----|------|--------|----------|
{rows}

Text after the table.
"""


class RegistryTable(unittest.TestCase):
    ENTRIES = [
        {"id": "SOUL-TH-001", "title": "First Control", "domain": 11, "severity": "HIGH"},
        {"id": "SOUL-TH-002", "title": "Second Control", "domain": 11, "severity": "LOW"},
    ]
    DOMAINS = {11: "Trust Hierarchy"}
    GREEN = ["| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
             "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |"]
    # A row of SOUL-TH-001 with a severity other than that of its attribute table, and the red line it gives.
    LOW_ROW = "| SOUL-TH-001 | First Control | Trust Hierarchy | LOW |"
    LOW_RED = "Severity 'LOW' of SOUL-TH-001 differs from the attribute table 'HIGH'"

    def check(self, rows):
        errors = []
        cc.check_registry_table(errors, "specification.md", REGISTRY.format(rows="\n".join(rows)),
                                self.ENTRIES, self.DOMAINS)
        return errors

    def check_text(self, text):
        errors = []
        cc.check_registry_table(errors, "specification.md", text, self.ENTRIES, self.DOMAINS)
        return errors

    def test_rows_equal_to_the_domain_files_are_green(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), [])

    def test_name_that_differs_from_the_heading_is_red(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First control | Trust Hierarchy | HIGH |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), ["RED specification.md:7: Name 'First control' of SOUL-TH-001 differs from the domain heading "
             "'First Control'"])

    def test_domain_and_severity_that_differ_are_red(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust | HIGH |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | MEDIUM |",
        ]), [
            "RED specification.md:7: Domain 'Trust' of SOUL-TH-001 differs from the domain heading "
            "'Trust Hierarchy'",
            "RED specification.md:8: Severity 'MEDIUM' of SOUL-TH-002 differs from the attribute table 'LOW'",
        ])

    def test_missing_unknown_and_reordered_rows_are_red(self):
        self.assertEqual(self.check(["| SOUL-TH-009 | Ninth | Trust Hierarchy | LOW |",
                                     "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |"]), [
            "RED specification.md:7: registry row 'SOUL-TH-009' is not a control heading in domains/",
            "RED specification.md: the registry table under section 5.3 has no row for SOUL-TH-002",
        ])
        self.assertEqual(self.check([
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
        ]), ["RED specification.md:8: registry row SOUL-TH-001 follows SOUL-TH-002; the rows under section 5.3 must be "
             "in domain order then NNN"])

    def test_repeated_row_is_red(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), ["RED specification.md:8: registry row SOUL-TH-001 is repeated"])

    def test_row_with_the_wrong_number_of_cells_is_red(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), [
            "RED specification.md:7: registry row has 3 cells; expected 4",
            "RED specification.md: the registry table under section 5.3 has no row for SOUL-TH-001",
        ])

    def test_row_with_no_closing_pipe_is_red_and_not_read(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), [
            "RED specification.md:7: registry row has no closing pipe; it is not read",
            "RED specification.md: the registry table under section 5.3 has no row for SOUL-TH-001",
        ])
        # Spaces after the closing pipe are not part of the row.
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |  ",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |\t",
        ]), [])

    def test_line_under_the_last_row_without_a_leading_pipe_is_red_and_not_read(self):
        rows = ["| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
                "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |"]
        # None of these lines is blank, and none starts with a pipe.
        for line in ("SOUL-TH-001 | First Control | Trust Hierarchy | LOW |", "SOUL-TH-001 | First Control",
                     "SOUL-TH-001", "   | SOUL-TH-001 | First Control | Trust Hierarchy | LOW |", "\N{NO-BREAK SPACE}"):
            with self.subTest(line=line):
                self.assertEqual(self.check(rows + [line]), [
                    "RED specification.md:9: line directly under the last row of the registry table under section "
                    "5.3 is not blank and does not start with a pipe; GFM renders it as a row of that table unless "
                    "it starts another block, and it is not read"])

    def test_line_under_the_last_row_that_starts_with_a_character_splitlines_ends_a_line_at_is_red(self):
        # Each character leads the line, or is the whole line with the row on the line after it.
        rows = ["| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
                "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |"]
        row = "SOUL-TH-001 | First Control | Trust Hierarchy | LOW |"
        for char in SPLITLINES_ONLY:
            for lines in ([char + row], [char, row]):
                with self.subTest(lines=lines):
                    self.assertEqual(self.check(rows + lines), [
                        "RED specification.md:9: line directly under the last row of the registry table under section "
                        "5.3 is not blank and does not start with a pipe; GFM renders it as a row of that table unless "
                        "it starts another block, and it is not read"])

    def test_line_of_spaces_and_tabs_under_the_last_row_ends_the_table(self):
        rows = ["| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
                "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |"]
        for blank in ("", " ", "\t", " \t "):
            with self.subTest(blank=blank):
                # The line after the blank line is neither read nor reported.
                self.assertEqual(self.check(rows + [blank, "SOUL-TH-001 | First Control | Trust Hierarchy | LOW |"]),
                                 [])
        # A table that ends the file is green.
        text = REGISTRY.format(rows="\n".join(rows))
        errors = []
        cc.check_registry_table(errors, "specification.md", text[:text.index("\n\nText after the table.")],
                                self.ENTRIES, self.DOMAINS)
        self.assertEqual(errors, [])

    def test_missing_heading_is_red(self):
        errors = []
        cc.check_registry_table(errors, "specification.md", "# Spec\n", self.ENTRIES, self.DOMAINS)
        self.assertEqual(errors, ["RED specification.md: heading '### 5.3 Complete Control Registry' not found"])

    def test_table_without_the_header_is_red(self):
        rows = "\n".join(["| SOUL-TH-001 | First Control | Trust Hierarchy | HIGH |",
                          "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |"])
        header = "| ID | Name | Domain | Severity |"
        texts = {
            "a column renamed": REGISTRY.format(rows=rows).replace(header, "| ID | Title | Domain | Severity |"),
            "a column missing": REGISTRY.format(rows=rows).replace(header, "| ID | Name | Domain |"),
            "the header row alone": REGISTRY.format(rows="").replace("|----|------|--------|----------|\n", ""),
            "no table": "### 5.3 Complete Control Registry\n\nNo table.\n",
        }
        for case, text in texts.items():
            with self.subTest(case=case):
                errors = []
                cc.check_registry_table(errors, "specification.md", text, self.ENTRIES, self.DOMAINS)
                self.assertEqual(errors, ["RED specification.md: the registry table under section 5.3 must have the "
                                          "header | ID | Name | Domain | Severity |"])

    def test_heading_and_table_repeated_in_a_fenced_block_above_the_heading_are_not_read(self):
        # The block repeats the heading and the table as they stand, as an example would. The table GFM renders under
        # the heading gives SOUL-TH-001 the severity LOW.
        green = REGISTRY.format(rows="\n".join(self.GREEN))
        example = green[green.index(cc.REGISTRY_HEADING):green.index("\n\nText after the table.")]
        red = REGISTRY.format(rows="\n".join([self.LOW_ROW, self.GREEN[1]]))
        for opening, closing in (("```markdown", "```"), ("~~~", "~~~"), ("````", "`````")):
            text = red.replace(cc.REGISTRY_HEADING, f"{opening}\n{example}\n\n{closing}\n\n{cc.REGISTRY_HEADING}", 1)
            lineno = text.split("\n").index(self.LOW_ROW) + 1
            with self.subTest(opening=opening):
                self.assertEqual(self.check_text(text), [f"RED specification.md:{lineno}: {self.LOW_RED}"])

    def test_table_in_a_fenced_block_between_the_heading_and_the_table_is_not_read(self):
        green = REGISTRY.format(rows="\n".join(self.GREEN))
        example = green[green.index("| ID |"):green.index("\n\nText after the table.")]
        red = REGISTRY.format(rows="\n".join([self.LOW_ROW, self.GREEN[1]]))
        # The closing fence directly under the last row of the example, or after a blank line.
        for gap in ("", "\n"):
            text = red.replace(f"{cc.REGISTRY_HEADING}\n\n",
                               f"{cc.REGISTRY_HEADING}\n\n```markdown\n{example}\n{gap}```\n\n", 1)
            lineno = text.split("\n").index(self.LOW_ROW) + 1
            with self.subTest(gap=gap):
                self.assertEqual(self.check_text(text), [f"RED specification.md:{lineno}: {self.LOW_RED}"])

    def test_heading_only_inside_a_fenced_block_is_not_found(self):
        green = REGISTRY.format(rows="\n".join(self.GREEN))
        # A block that no line closes runs to the end of the text.
        for case, text in (("closed", f"```markdown\n{green}```\n"), ("never closed", f"~~~\n{green}")):
            with self.subTest(case=case):
                self.assertEqual(self.check_text(text),
                                 ["RED specification.md: heading '### 5.3 Complete Control Registry' not found"])


CONFORMANCE = """# Conformance Levels

### CRITICAL Controls

| Control ID | Name | Applicable Tiers |
|-----------|------|-----------------|
| SOUL-TH-001 | First control | All tiers |

### Path to Essential

1. A first step (satisfies SOUL-TH-001)

### HIGH Controls

| Control ID | Name | Applicable Tiers |
|-----------|------|-----------------|
{rows}

### Path to Standard

{steps}

---

## Level 3: Hardened

Mentions SOUL-TH-003 outside the path section.
"""


class ConformanceLevels(unittest.TestCase):
    ENTRIES = [
        {"id": "SOUL-TH-001", "title": "First Control", "domain": 11, "severity": "CRITICAL", "status": "active"},
        {"id": "SOUL-TH-002", "title": "Second Control", "domain": 11, "severity": "HIGH", "status": "active"},
        {"id": "SOUL-TH-003", "title": "Third Control", "domain": 11, "severity": "HIGH", "status": "active"},
        {"id": "SOUL-TH-004", "title": "Fourth Control", "domain": 11, "severity": "HIGH", "status": "deprecated"},
        {"id": "SOUL-TH-005", "title": "Fifth Control", "domain": 11, "severity": "HIGH", "status": "draft"},
        {"id": "SOUL-TH-006", "title": "Sixth Control", "domain": 11, "severity": "MEDIUM", "status": "active"},
    ]
    ATTRIBUTES = {
        "SOUL-TH-001": ("x", {"Applicable tiers": "All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT)"}),
        "SOUL-TH-002": ("x", {"Applicable tiers": "All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT)"}),
        "SOUL-TH-003": ("x", {"Applicable tiers": "AGENTIC, MULTI-AGENT"}),
        "SOUL-TH-004": ("x", {"Applicable tiers": "AGENTIC, MULTI-AGENT"}),
        "SOUL-TH-005": ("x", {"Applicable tiers": "AGENTIC, MULTI-AGENT"}),
        "SOUL-TH-006": ("x", {"Applicable tiers": "AGENTIC, MULTI-AGENT"}),
    }
    ROWS = [
        "| SOUL-TH-002 | Second control | All tiers |",
        "| SOUL-TH-003 | Third control | AGENTIC, MULTI-AGENT |",
    ]
    STEPS = ["1. A second step (satisfies SOUL-TH-002)", "2. A third step (satisfies SOUL-TH-003)"]
    # (heading, the text that follows the lines under it, the line under it that names the control named there last,
    # that control) for the two tables and the two path sections.
    TABLES = (("### CRITICAL Controls", "\n\n### Path to Essential", "| SOUL-TH-001 | First control | All tiers |",
               "SOUL-TH-001"),
              ("### HIGH Controls", "\n\n### Path to Standard", ROWS[1], "SOUL-TH-003"))
    PATHS = (("### Path to Essential", "\n\n### HIGH Controls", "1. A first step (satisfies SOUL-TH-001)",
              "SOUL-TH-001"),
             ("### Path to Standard", "\n\n---", STEPS[1], "SOUL-TH-003"))

    def check(self, rows=ROWS, steps=STEPS):
        errors = []
        text = CONFORMANCE.format(rows="\n".join(rows), steps="\n".join(steps))
        cc.check_conformance_levels(errors, "conformance.md", text, self.ENTRIES, self.ATTRIBUTES)
        return errors

    def check_text(self, text):
        errors = []
        cc.check_conformance_levels(errors, "conformance.md", text, self.ENTRIES, self.ATTRIBUTES)
        return errors

    def without_last(self, text, line):
        """text without its last copy of the line, which is the copy under the heading GFM renders."""
        index = text.rindex(line + "\n")
        return text[:index] + text[index + len(line) + 1:]

    def test_every_active_control_of_the_severity_listed_and_named_in_the_path_is_green(self):
        self.assertEqual(self.check(), [])

    def test_missing_high_control_is_red_in_the_table_and_the_path(self):
        self.assertEqual(self.check(rows=self.ROWS[:1], steps=self.STEPS[:1]), [
            "RED conformance.md: the table under '### HIGH Controls' has no row for SOUL-TH-003",
            "RED conformance.md: the section '### Path to Standard' names no step for SOUL-TH-003",
        ])

    def test_deprecated_draft_and_other_severity_rows_are_red(self):
        rows = self.ROWS + [
            "| SOUL-TH-004 | Fourth control | AGENTIC, MULTI-AGENT |",
            "| SOUL-TH-005 | Fifth control | AGENTIC, MULTI-AGENT |",
            "| SOUL-TH-001 | First control | All tiers |",
        ]
        self.assertEqual(self.check(rows=rows), [
            "RED conformance.md:19: 'SOUL-TH-004' under '### HIGH Controls' is not an active HIGH control in domains/",
            "RED conformance.md:20: 'SOUL-TH-005' under '### HIGH Controls' is not an active HIGH control in domains/",
            "RED conformance.md:21: 'SOUL-TH-001' under '### HIGH Controls' is not an active HIGH control in domains/",
        ])

    def test_name_and_tiers_that_differ_from_the_domain_files_are_red(self):
        self.assertEqual(self.check(rows=[
            "| SOUL-TH-002 | Second | All tiers |",
            "| SOUL-TH-003 | Third control | All tiers |",
        ]), [
            "RED conformance.md:17: Name 'Second' of SOUL-TH-002 differs from the domain heading 'Second Control'",
            "RED conformance.md:18: Applicable Tiers 'All tiers' of SOUL-TH-003 differs from the attribute table "
            "'AGENTIC, MULTI-AGENT'",
        ])

    def test_repeated_reordered_and_short_rows_are_red(self):
        self.assertEqual(self.check(rows=list(reversed(self.ROWS)) + [self.ROWS[0], "| SOUL-TH-003 | Third |"]), [
            "RED conformance.md:19: SOUL-TH-002 is repeated under '### HIGH Controls'",
            "RED conformance.md:20: row has 2 cells; expected 3",
            "RED conformance.md: the rows under '### HIGH Controls' are not in domain order then NNN",
        ])

    def test_line_under_the_last_row_without_a_leading_pipe_is_red_and_not_read(self):
        # SOUL-TH-006 is an active MEDIUM control.
        self.assertEqual(self.check(rows=self.ROWS + ["SOUL-TH-006 | Sixth control | AGENTIC, MULTI-AGENT |"]), [
            "RED conformance.md:19: line directly under the last row of the table under '### HIGH Controls' is not "
            "blank and does not start with a pipe; GFM renders it as a row of that table unless it starts another "
            "block, and it is not read"])
        critical = "| SOUL-TH-001 | First control | All tiers |\n"
        text = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        self.assertEqual(text.count(critical), 1)
        errors = []
        cc.check_conformance_levels(errors, "conformance.md",
                                    text.replace(critical, critical + "SOUL-TH-002 | Second control | All tiers |\n"),
                                    self.ENTRIES, self.ATTRIBUTES)
        self.assertEqual(errors, [
            "RED conformance.md:8: line directly under the last row of the table under '### CRITICAL Controls' is not "
            "blank and does not start with a pipe; GFM renders it as a row of that table unless it starts another "
            "block, and it is not read"])

    def test_line_under_the_last_row_that_starts_with_a_character_splitlines_ends_a_line_at_is_red(self):
        # Each character leads the line, or is the whole line with the row on the line after it.
        critical = "| SOUL-TH-001 | First control | All tiers |\n"
        text = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        self.assertEqual(text.count(critical), 1)
        row = "SOUL-TH-006 | Sixth control | AGENTIC, MULTI-AGENT |"
        for char in SPLITLINES_ONLY:
            for lines in ([char + row], [char, row]):
                with self.subTest(table="HIGH", lines=lines):
                    self.assertEqual(self.check(rows=self.ROWS + lines), [
                        "RED conformance.md:19: line directly under the last row of the table under '### HIGH "
                        "Controls' is not blank and does not start with a pipe; GFM renders it as a row of that table "
                        "unless it starts another block, and it is not read"])
                with self.subTest(table="CRITICAL", lines=lines):
                    errors = []
                    variant = text.replace(critical, critical + "\n".join(lines) + "\n")
                    cc.check_conformance_levels(errors, "conformance.md", variant, self.ENTRIES, self.ATTRIBUTES)
                    self.assertEqual(errors, [
                        "RED conformance.md:8: line directly under the last row of the table under '### CRITICAL "
                        "Controls' is not blank and does not start with a pipe; GFM renders it as a row of that table "
                        "unless it starts another block, and it is not read"])

    def test_control_named_only_outside_the_path_section_is_red(self):
        self.assertEqual(self.check(steps=self.STEPS[:1]), [
            "RED conformance.md: the section '### Path to Standard' names no step for SOUL-TH-003",
        ])

    def test_missing_headings_and_header_are_red(self):
        errors = []
        cc.check_conformance_levels(errors, "conformance.md", "# Conformance Levels\n", self.ENTRIES, self.ATTRIBUTES)
        self.assertEqual(errors, [
            "RED conformance.md: heading '### CRITICAL Controls' not found",
            "RED conformance.md: heading '### HIGH Controls' not found",
        ])
        text = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        errors = []
        cc.check_conformance_levels(errors, "conformance.md", text.replace("| Control ID | Name |", "| ID | Name |"),
                                    self.ENTRIES, self.ATTRIBUTES)
        self.assertEqual(errors, [
            "RED conformance.md: the table under '### CRITICAL Controls' must have the header "
            "| Control ID | Name | Applicable Tiers |",
            "RED conformance.md: the table under '### HIGH Controls' must have the header "
            "| Control ID | Name | Applicable Tiers |",
        ])

    def test_heading_and_table_repeated_in_a_fenced_block_above_the_heading_are_not_read(self):
        # The block repeats the heading and the table as they stand. The table GFM renders under the heading has no
        # row for the control the block lists last.
        green = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        for heading, end, row, cid in self.TABLES:
            example = green[green.index(heading):green.index(end)]
            text = self.without_last(green.replace(heading, f"```markdown\n{example}\n\n```\n\n{heading}", 1), row)
            with self.subTest(heading=heading):
                self.assertEqual(self.check_text(text),
                                 [f"RED conformance.md: the table under {heading!r} has no row for {cid}"])

    def test_table_in_a_fenced_block_between_the_heading_and_the_table_is_not_read(self):
        green = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        for heading, end, row, cid in self.TABLES:
            table = green[green.index("| Control ID |", green.index(heading)):green.index(end)]
            text = self.without_last(green.replace(f"{heading}\n\n", f"{heading}\n\n```markdown\n{table}\n```\n\n", 1),
                                     row)
            with self.subTest(heading=heading):
                self.assertEqual(self.check_text(text),
                                 [f"RED conformance.md: the table under {heading!r} has no row for {cid}"])

    def test_path_section_repeated_in_a_fenced_block_above_its_heading_is_not_read(self):
        # The block repeats the heading and the steps as they stand. The section GFM renders under the heading names
        # no step for the control the block names last.
        green = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        for heading, end, step, cid in self.PATHS:
            example = green[green.index(heading):green.index(end)]
            text = self.without_last(green.replace(heading, f"```markdown\n{example}\n\n```\n\n{heading}", 1), step)
            with self.subTest(heading=heading):
                self.assertEqual(self.check_text(text),
                                 [f"RED conformance.md: the section {heading!r} names no step for {cid}"])

    def test_line_that_starts_with_a_hash_inside_a_fenced_block_does_not_end_the_path_section(self):
        green = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        for heading, _, _, _ in self.PATHS:
            for opening, closing in (("```sh", "```"), ("~~~", "~~~")):
                text = green.replace(f"{heading}\n\n",
                                     f"{heading}\n\n{opening}\n# A comment in an example\n{closing}\n\n", 1)
                with self.subTest(heading=heading, opening=opening):
                    self.assertEqual(self.check_text(text), [])

    def test_heading_only_inside_a_fenced_block_is_not_found(self):
        green = CONFORMANCE.format(rows="\n".join(self.ROWS), steps="\n".join(self.STEPS))
        for heading in ("### CRITICAL Controls", "### Path to Essential", "### HIGH Controls", "### Path to Standard"):
            with self.subTest(heading=heading):
                self.assertEqual(self.check_text(green.replace(heading, f"```\n{heading}\n```", 1)),
                                 [f"RED conformance.md: heading {heading!r} not found"])


def tiers_for(controls):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "11-trust-hierarchy.md").write_text(domain_file(controls), encoding="utf-8")
        errors = []
        found, _, attributes = cc.load_domains(errors, Path(tmp))
        entries = cc.control_entries(errors, found, attributes)
        tiers = cc.control_tiers(errors, entries, attributes)
    return tiers, errors


def with_tiers(cid, value):
    return (f"### {cid}: Control", [("ID", cid), ("Severity", "LOW"), ("Applicable tiers", value)])


class ApplicableTiers(unittest.TestCase):
    def test_all_and_a_list_of_tiers_are_read_in_tier_order(self):
        tiers, errors = tiers_for([with_tiers("SOUL-TH-001", "All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT)"),
                                   with_tiers("SOUL-TH-002", "`AGENTIC, MULTI-AGENT`")])
        self.assertEqual(errors, [])
        self.assertEqual({cid: names for cid, (_, names) in tiers.items()},
                         {"SOUL-TH-001": cc.TIERS, "SOUL-TH-002": ("AGENTIC", "MULTI-AGENT")})
        self.assertRegex(tiers["SOUL-TH-002"][0], r"11-trust-hierarchy\.md:\d+$")

    def test_absent_attribute_is_red(self):
        tiers, errors = tiers_for([ACTIVE])
        self.assertEqual([e.split(": ", 1)[1] for e in errors], ["SOUL-TH-001 has no Applicable tiers attribute"])
        self.assertIsNone(tiers["SOUL-TH-001"][1])

    def test_unknown_repeated_or_reordered_tiers_are_red(self):
        for value in ("AGENTIC, ORCHESTRATOR", "AGENTIC, AGENTIC", "MULTI-AGENT, AGENTIC", "All",
                      "AGENTIC,MULTI-AGENT", ""):
            with self.subTest(value=value):
                tiers, errors = tiers_for([with_tiers("SOUL-TH-001", value)])
                self.assertEqual([e.split(": ", 1)[1] for e in errors], [
                    f"Applicable tiers {value!r} of SOUL-TH-001 is neither "
                    "'All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT)' nor names from BASIC, TOOL-USING, "
                    "AGENTIC, MULTI-AGENT, each once and in that order, separated by ', '"])
                self.assertIsNone(tiers["SOUL-TH-001"][1])


MATRIX = """# Spec

### 3.5 Control Applicability Matrix

| Control ID | BASIC | TOOL-USING | AGENTIC | MULTI-AGENT |
|-----------|-------|-----------|---------|-------------|
{rows}

Text after the table.
"""


class ApplicabilityMatrix(unittest.TestCase):
    TIERS = {
        "SOUL-TH-001": ("domains/11-trust-hierarchy.md:5", cc.TIERS),
        "SOUL-TH-002": ("domains/11-trust-hierarchy.md:20", ("AGENTIC", "MULTI-AGENT")),
    }
    GREEN = ["| SOUL-TH-001 | Yes | Yes | Yes | Yes |", "| SOUL-TH-002 | -- | -- | Yes | Yes |"]
    # A row of SOUL-TH-002 that differs from its Applicable tiers attribute, and the red line it gives.
    MULTI_AGENT_ROW = "| SOUL-TH-002 | -- | -- | -- | Yes |"
    MULTI_AGENT_RED = ("SOUL-TH-002 is marked Yes for MULTI-AGENT; its Applicable tiers attribute at "
                       "domains/11-trust-hierarchy.md:20 names AGENTIC, MULTI-AGENT")

    def check(self, rows, tiers=None):
        errors = []
        cc.check_applicability_matrix(errors, "specification.md", MATRIX.format(rows="\n".join(rows)),
                                      tiers or self.TIERS)
        return errors

    def check_text(self, text):
        errors = []
        cc.check_applicability_matrix(errors, "specification.md", text, self.TIERS)
        return errors

    def test_rows_equal_to_the_applicable_tiers_attributes_are_green(self):
        self.assertEqual(self.check(self.GREEN), [])

    def test_row_that_differs_from_the_attribute_is_red(self):
        self.assertEqual(self.check([self.GREEN[0], "| SOUL-TH-002 | -- | -- | -- | Yes |"]), [
            "RED specification.md:8: SOUL-TH-002 is marked Yes for MULTI-AGENT; its Applicable tiers attribute "
            "at domains/11-trust-hierarchy.md:20 names AGENTIC, MULTI-AGENT"])
        self.assertEqual(self.check(["| SOUL-TH-001 | -- | -- | -- | -- |", self.GREEN[1]]), [
            "RED specification.md:7: SOUL-TH-001 is marked Yes for no tier; its Applicable tiers attribute "
            "at domains/11-trust-hierarchy.md:5 names BASIC, TOOL-USING, AGENTIC, MULTI-AGENT"])

    def test_cell_other_than_yes_or_double_hyphen_is_red(self):
        self.assertEqual(self.check([self.GREEN[0], "| SOUL-TH-002 | -- | -- | yes | Yes |"]),
                         ["RED specification.md:8: matrix row SOUL-TH-002 has a cell other than Yes or --"])

    def test_attribute_already_red_is_not_compared(self):
        tiers = {**self.TIERS, "SOUL-TH-002": ("domains/11-trust-hierarchy.md:20", None)}
        self.assertEqual(self.check([self.GREEN[0], "| SOUL-TH-002 | Yes | -- | -- | -- |"], tiers), [])

    def test_missing_unknown_repeated_and_reordered_rows_are_red(self):
        self.assertEqual(self.check(["| SOUL-TH-009 | -- | -- | -- | Yes |", self.GREEN[0], self.GREEN[0]]), [
            "RED specification.md:7: matrix row 'SOUL-TH-009' is not a control heading in domains/",
            "RED specification.md:9: matrix row SOUL-TH-001 is repeated",
            "RED specification.md: the matrix under section 3.5 has no row for SOUL-TH-002",
        ])
        self.assertEqual(self.check(list(reversed(self.GREEN))),
                         ["RED specification.md: the matrix rows under section 3.5 are not in domain order then NNN"])

    def test_row_with_the_wrong_number_of_cells_is_red(self):
        self.assertEqual(self.check(["| SOUL-TH-001 | Yes | Yes | Yes |", self.GREEN[1]]), [
            "RED specification.md:7: matrix row has 4 cells; expected 5",
            "RED specification.md: the matrix under section 3.5 has no row for SOUL-TH-001",
        ])

    def test_line_under_the_last_row_without_a_leading_pipe_is_red_and_not_read(self):
        self.assertEqual(self.check(self.GREEN + ["SOUL-TH-002 | Yes | Yes | Yes | Yes |"]), [
            "RED specification.md:9: line directly under the last row of the matrix under section 3.5 is not blank "
            "and does not start with a pipe; GFM renders it as a row of that table unless it starts another block, "
            "and it is not read"])

    def test_line_under_the_last_row_that_starts_with_a_character_splitlines_ends_a_line_at_is_red(self):
        # Each character leads the line, or is the whole line with the row on the line after it.
        row = "SOUL-TH-002 | Yes | Yes | Yes | Yes |"
        for char in SPLITLINES_ONLY:
            for lines in ([char + row], [char, row]):
                with self.subTest(lines=lines):
                    self.assertEqual(self.check(self.GREEN + lines), [
                        "RED specification.md:9: line directly under the last row of the matrix under section 3.5 is "
                        "not blank and does not start with a pipe; GFM renders it as a row of that table unless it "
                        "starts another block, and it is not read"])

    def test_missing_heading_or_header_is_red(self):
        errors = []
        cc.check_applicability_matrix(errors, "specification.md", "# Spec\n", self.TIERS)
        self.assertEqual(errors, ["RED specification.md: heading '### 3.5 Control Applicability Matrix' not found"])
        errors = []
        cc.check_applicability_matrix(errors, "specification.md",
                                      MATRIX.format(rows="").replace("| MULTI-AGENT |", "| MULTI |"), self.TIERS)
        self.assertEqual(errors, ["RED specification.md: the matrix under section 3.5 must have the header "
                                  "| Control ID | BASIC | TOOL-USING | AGENTIC | MULTI-AGENT |"])

    def test_heading_and_matrix_repeated_in_a_fenced_block_above_the_heading_are_not_read(self):
        # The block repeats the heading and the matrix as they stand. The matrix GFM renders under the heading marks
        # SOUL-TH-002 for MULTI-AGENT alone.
        green = MATRIX.format(rows="\n".join(self.GREEN))
        example = green[green.index(cc.MATRIX_HEADING):green.index("\n\nText after the table.")]
        text = MATRIX.format(rows="\n".join([self.GREEN[0], self.MULTI_AGENT_ROW]))
        text = text.replace(cc.MATRIX_HEADING, f"```markdown\n{example}\n\n```\n\n{cc.MATRIX_HEADING}", 1)
        lineno = text.split("\n").index(self.MULTI_AGENT_ROW) + 1
        self.assertEqual(self.check_text(text), [f"RED specification.md:{lineno}: {self.MULTI_AGENT_RED}"])

    def test_matrix_in_a_fenced_block_between_the_heading_and_the_matrix_is_not_read(self):
        green = MATRIX.format(rows="\n".join(self.GREEN))
        example = green[green.index("| Control ID |"):green.index("\n\nText after the table.")]
        text = MATRIX.format(rows="\n".join([self.GREEN[0], self.MULTI_AGENT_ROW]))
        text = text.replace(f"{cc.MATRIX_HEADING}\n\n", f"{cc.MATRIX_HEADING}\n\n```markdown\n{example}\n```\n\n", 1)
        lineno = text.split("\n").index(self.MULTI_AGENT_ROW) + 1
        self.assertEqual(self.check_text(text), [f"RED specification.md:{lineno}: {self.MULTI_AGENT_RED}"])

    def test_heading_only_inside_a_fenced_block_is_not_found(self):
        green = MATRIX.format(rows="\n".join(self.GREEN))
        # A block that no line closes runs to the end of the text.
        for case, text in (("closed", f"```markdown\n{green}```\n"), ("never closed", f"~~~\n{green}")):
            with self.subTest(case=case):
                self.assertEqual(self.check_text(text),
                                 ["RED specification.md: heading '### 3.5 Control Applicability Matrix' not found"])


TIER_SECTIONS = """## 3. Agent Tiers

### 3.1 BASIC

**Applicable controls**: {} (the controls marked applicable to BASIC)

### 3.2 TOOL-USING

**Applicable controls**: {}

### 3.3 AGENTIC

**Definition**: Text.

**Applicable controls**: {} (all TOOL-USING controls plus the AGENTIC additions)

### 3.4 MULTI-AGENT

**Applicable controls**: {} (all controls)

### 3.5 Control Applicability Matrix
"""


class TierCounts(unittest.TestCase):
    TIERS = {
        "SOUL-TH-001": ("a.md:1", cc.TIERS),
        "SOUL-TH-002": ("a.md:2", ("AGENTIC", "MULTI-AGENT")),
        "SOUL-TH-003": ("a.md:3", ("MULTI-AGENT",)),
    }
    # The counts of sections 3.1 to 3.4 that equal TIERS, and the four count lines of TIER_SECTIONS.
    COUNTS = (1, 1, 2, 3)
    COUNT_LINES = [line for line in TIER_SECTIONS.split("\n") if line.startswith("**Applicable controls**")]

    def check(self, text, tiers=None):
        errors = []
        cc.check_tier_counts(errors, "specification.md", text, tiers or self.TIERS)
        return errors

    def one_more(self, i):
        """The tier sections with tier i stating one control more than names it, that count line, and its red line."""
        values = list(self.COUNTS)
        values[i] += 1
        tier = cc.TIERS[i]
        return (TIER_SECTIONS.format(*values), self.COUNT_LINES[i].format(values[i]),
                f"Applicable controls {values[i]} of {tier} differs from the {self.COUNTS[i]} controls whose "
                f"Applicable tiers attribute names {tier}")

    def test_counts_equal_to_the_attributes_are_green(self):
        self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, 2, 3)), [])

    def test_count_that_differs_is_red_at_its_line(self):
        self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, 3, 3)), [
            "RED specification.md:15: Applicable controls 3 of AGENTIC differs from the 2 controls whose "
            "Applicable tiers attribute names AGENTIC"])

    def test_count_that_differs_is_red_at_its_line_counted_where_gfm_ends_a_line(self):
        # GFM ends a line only at LF, CR LF, or CR, so the count stays on line 15 with any of these characters in a
        # line above it.
        text = TIER_SECTIONS.format(1, 1, 3, 3)
        self.assertIn("**Definition**: Text.", text)
        for char in SPLITLINES_ONLY:
            with self.subTest(char=char):
                variant = text.replace("**Definition**: Text.", f"**Definition**: Text.{char}More.")
                self.assertEqual(self.check(variant), [
                    "RED specification.md:15: Applicable controls 3 of AGENTIC differs from the 2 controls whose "
                    "Applicable tiers attribute names AGENTIC"])

    def test_counts_are_not_compared_when_an_attribute_is_red(self):
        tiers = {**self.TIERS, "SOUL-TH-003": ("a.md:3", None)}
        self.assertEqual(self.check(TIER_SECTIONS.format(9, 9, 9, 9), tiers), [])

    def test_missing_heading_or_count_line_is_red(self):
        text = TIER_SECTIONS.format(1, 1, 2, 3)
        self.assertEqual(self.check(text.replace("### 3.2 TOOL-USING", "### 3.2 Tool-using")),
                         ["RED specification.md: section 3 has no heading '### 3.n TOOL-USING'"])
        self.assertEqual(self.check(text.replace("**Applicable controls**: 3 (all controls)", "All controls.")),
                         ["RED specification.md: the section on MULTI-AGENT has no '**Applicable controls**: N' line"])

    def test_count_longer_than_int_converts_is_red_at_its_line_and_not_compared(self):
        limit = int_digit_limit(self)
        red = f"RED specification.md:15: {too_long('Applicable controls of AGENTIC', limit)}"
        # int() counts leading zeros, so a run of limit + 1 digits whose value is the expected 2 is red too.
        for digits in ("1" * (limit + 1), "0" * limit + "2"):
            with self.subTest(digits=f"{digits[0]}...{digits[-1]}"):
                self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, digits, 3)), [red])
                # The other counts are still compared, and the count is red when an attribute is red too.
                self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, digits, 4)), [
                    red, "RED specification.md:19: Applicable controls 4 of MULTI-AGENT differs from the 3 controls "
                         "whose Applicable tiers attribute names MULTI-AGENT"])
                self.assertEqual(self.check(TIER_SECTIONS.format(9, 9, digits, 9),
                                            {**self.TIERS, "SOUL-TH-003": ("a.md:3", None)}), [red])

    def test_tier_section_repeated_in_a_fenced_block_above_its_heading_is_not_read(self):
        # The block repeats the heading and the section as they stand. The section GFM renders under the heading
        # states one control more than names the tier.
        green = TIER_SECTIONS.format(*self.COUNTS)
        for i, tier in enumerate(cc.TIERS):
            heading = f"### 3.{i + 1} {tier}"
            start = green.index(heading)
            example = green[start:green.index("\n\n###", start)]
            text, count, red = self.one_more(i)
            text = text.replace(heading, f"```markdown\n{example}\n\n```\n\n{heading}", 1)
            lineno = text.split("\n").index(count) + 1
            with self.subTest(tier=tier):
                self.assertEqual(self.check(text), [f"RED specification.md:{lineno}: {red}"])

    def test_line_inside_a_fenced_block_under_a_tier_heading_is_not_read(self):
        # A line there that starts with # does not end the section, and a count line there is not its count. The
        # count line under the block states one control more than names the tier.
        for i, tier in enumerate(cc.TIERS):
            heading = f"### 3.{i + 1} {tier}"
            for line in ("# A comment in an example", f"**Applicable controls**: {self.COUNTS[i]}"):
                for opening, closing in (("```sh", "```"), ("~~~", "~~~")):
                    text, count, red = self.one_more(i)
                    text = text.replace(f"{heading}\n\n", f"{heading}\n\n{opening}\n{line}\n{closing}\n\n", 1)
                    lineno = text.split("\n").index(count) + 1
                    with self.subTest(tier=tier, line=line, opening=opening):
                        self.assertEqual(self.check(text), [f"RED specification.md:{lineno}: {red}"])

    def test_tier_heading_only_inside_a_fenced_block_is_not_found(self):
        text = TIER_SECTIONS.format(*self.COUNTS)
        for i, tier in enumerate(cc.TIERS):
            heading = f"### 3.{i + 1} {tier}"
            with self.subTest(tier=tier):
                self.assertEqual(self.check(text.replace(heading, f"```\n{heading}\n```", 1)),
                                 [f"RED specification.md: section 3 has no heading '### 3.n {tier}'"])


class LineEndingPins(unittest.TestCase):
    def test_the_byte_checked_files_are_pinned_to_lf(self):
        paths = [f"crosswalks/{spec[kind]}" for spec in cc.CROSSWALK_SET for kind in ("csv", "md")]
        paths.append(cc.CONTROLS_EXPORT)
        try:
            result = subprocess.run(["git", "-C", str(cc.ROOT), "check-attr", "eol", "--"] + paths,
                                    capture_output=True, text=True, check=True, timeout=60)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git, or a git work tree, is not available")
        self.assertEqual(result.stdout.splitlines(), [f"{p}: eol: lf" for p in paths])


class FenceReader(unittest.TestCase):
    def test_the_fence_reader_is_the_one_in_the_prose_check(self):
        # Each check is a file of its own, so each holds a copy of the reader. scripts/test_check_docs_prose.py tests the
        # lines its copy reads as code, and EntryAttributes the attribute rows this copy leaves unread.
        for name in ("first_character", "closes_fence", "past_quote_marker", "CodeFences"):
            with self.subTest(name=name):
                self.assertEqual(inspect.getsource(getattr(cc, name)), inspect.getsource(getattr(cdp, name)))
        for name in ("FENCE", "LIST_MARKER", "ATX_HEADING", "HEADING_UNDERLINE", "HTML_BLOCK"):
            with self.subTest(name=name):
                self.assertEqual((getattr(cc, name).pattern, getattr(cc, name).flags),
                                 (getattr(cdp, name).pattern, getattr(cdp, name).flags))
        self.assertEqual([(end.pattern, end.flags) for end in cc.HTML_BLOCK_END],
                         [(end.pattern, end.flags) for end in cdp.HTML_BLOCK_END])


class MainRun(unittest.TestCase):
    """main() against a copy of the repository files it reads, in a temporary directory."""

    def run_main(self, argv, edit=None, keep=cc.CONTROLS_EXPORT):
        """Run main() on the copy; return its exit code, its output, and the bytes left at keep."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(cc.DOMAINS, root / "domains")
            shutil.copytree(cc.CROSSWALKS, root / "crosswalks")
            for name in ("README.md", cc.CONTROLS_EXPORT, cc.SPECIFICATION, cc.CONFORMANCE):
                shutil.copyfile(cc.ROOT / name, root / name)
            if edit:
                edit(root)
            out = io.StringIO()
            with mock.patch.multiple(cc, ROOT=root, CROSSWALKS=root / "crosswalks", DOMAINS=root / "domains"), \
                    contextlib.redirect_stdout(out):
                code = cc.main(argv)
            kept = (root / keep).read_bytes()
        return code, out.getvalue(), kept

    def test_unmodified_copy_is_green(self):
        code, out, _ = self.run_main([])
        self.assertEqual(code, 0, out)
        self.assertIn("crosswalks: all checks green", out)

    def test_drifted_controls_json_is_red(self):
        def drift(root):
            path = root / cc.CONTROLS_EXPORT
            path.write_bytes(path.read_bytes().replace(b'"title": "Trust Chain Defined"', b'"title": "Trust chain"', 1))
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn("RED controls.json:5: committed file differs from the render of the domain files; "
                      "run python3 scripts/check_crosswalks.py --write\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_drifted_registry_table_is_red(self):
        row = "| SOUL-TH-001 | Trust Chain Defined | Trust Hierarchy | HIGH |"
        lineno = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").splitlines().index(row) + 1

        def drift(root):
            path = root / cc.SPECIFICATION
            path.write_text(path.read_text(encoding="utf-8").replace(row, row.replace("Trust Chain", "Trust chain"), 1),
                            encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED specification.md:{lineno}: Name 'Trust chain Defined' of SOUL-TH-001 differs from the "
                      "domain heading 'Trust Chain Defined'\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_high_control_missing_from_conformance_is_red(self):
        row = "| SOUL-IH-004 | Input validation and sanitization | All tiers |"
        self.assertIn(row, (cc.ROOT / cc.CONFORMANCE).read_text(encoding="utf-8").splitlines())

        def drift(root):
            path = root / cc.CONFORMANCE
            path.write_text(path.read_text(encoding="utf-8").replace(row + "\n", "", 1), encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn("RED conformance.md: the table under '### HIGH Controls' has no row for SOUL-IH-004\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_attribute_row_without_its_leading_pipe_under_an_attribute_table_is_red(self):
        rel = "domains/11-trust-hierarchy.md"
        last = "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |"
        lines = (cc.ROOT / rel).read_text(encoding="utf-8").splitlines()
        index = lines.index(last, lines.index("### SOUL-TH-001: Trust Chain Defined"))
        self.assertEqual(lines[index + 1], "")

        def drift(root):
            path = root / rel
            text = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join(text[:index + 1] + ["**Status** | deprecated |"] + text[index + 1:]) + "\n",
                            encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED {rel}:{index + 2}: attribute row separated from the attribute table of SOUL-TH-001; "
                      "it is not read\n", out)
        # The row is not read, so the render of controls.json keeps SOUL-TH-001 active and equal to the committed file.
        self.assertIn("\n1 problem(s) found", out)
        self.assertNotIn("all checks green", out)

    def test_line_that_is_not_blank_directly_under_an_attribute_table_is_red(self):
        rel = "domains/11-trust-hierarchy.md"
        last = "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |"
        lines = (cc.ROOT / rel).read_text(encoding="utf-8").splitlines()
        index = lines.index(last, lines.index("### SOUL-TH-001: Trust Chain Defined"))
        self.assertEqual(lines[index + 1], "")
        for inserted in ("Status | deprecated |", "**Status**  | deprecated |", "**Status**|deprecated|",
                         "   | **Status** | deprecated", "**Description**: Text."):
            def drift(root, inserted=inserted):
                path = root / rel
                text = path.read_text(encoding="utf-8").splitlines()
                path.write_text("\n".join(text[:index + 1] + [inserted] + text[index + 1:]) + "\n", encoding="utf-8")
            with self.subTest(inserted=inserted):
                code, out, _ = self.run_main([], drift)
                self.assertEqual(code, 1, out)
                self.assertIn(f"RED {rel}:{index + 2}: {NOT_BLANK_UNDER_THE_TABLE}\n", out)
                self.assertIn("\n1 problem(s) found", out)
                self.assertNotIn("all checks green", out)

    def test_line_without_a_leading_pipe_under_the_last_row_of_a_table_it_reads_is_red(self):
        # SOUL-TH-001 is a HIGH control and SOUL-TH-002 a MEDIUM one in the domain files.
        for rel, heading, line, name in (
                (cc.SPECIFICATION, cc.REGISTRY_HEADING, "SOUL-TH-001 | Trust Chain Defined | Trust Hierarchy | LOW |",
                 "the registry table under section 5.3"),
                (cc.CONFORMANCE, "### HIGH Controls", "SOUL-TH-002 | Conflict Resolution | All |",
                 "the table under '### HIGH Controls'"),
                (cc.SPECIFICATION, cc.MATRIX_HEADING, "SOUL-TH-001 | Yes | Yes | Yes | -- |",
                 "the matrix under section 3.5")):
            lines = (cc.ROOT / rel).read_text(encoding="utf-8").splitlines()
            start = next(i for i in range(lines.index(heading), len(lines)) if lines[i].startswith("|"))
            under = next(i for i in range(start, len(lines)) if not lines[i].startswith("|"))
            self.assertEqual(lines[under], "")

            def drift(root, rel=rel, line=line, under=under):
                path = root / rel
                text = path.read_text(encoding="utf-8").splitlines()
                path.write_text("\n".join(text[:under] + [line] + text[under:]) + "\n", encoding="utf-8")
            with self.subTest(table=name):
                code, out, _ = self.run_main([], drift)
                self.assertEqual(code, 1, out)
                self.assertIn(f"RED {rel}:{under + 1}: line directly under the last row of {name} is not blank and "
                              "does not start with a pipe; GFM renders it as a row of that table unless it starts "
                              "another block, and it is not read\n", out)
                self.assertIn("\n1 problem(s) found", out)
                self.assertNotIn("all checks green", out)

    def test_registry_table_repeated_in_a_fenced_block_above_its_heading_is_not_read(self):
        # Directly above the heading of section 5.3, a fenced block holds the heading, a blank line, the lines of the
        # registry table as they stand, and a blank line; the real table gives SOUL-TH-001 the severity LOW.
        lines = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").splitlines()
        start = lines.index(cc.REGISTRY_HEADING)
        self.assertEqual(lines[start + 1], "")
        end = next(i for i in range(start + 2, len(lines)) if not lines[i].startswith("|"))
        table = lines[start + 2:end]
        self.assertEqual(len(table), 2 + cc.CONTROL_COUNT)
        row = lines.index("| SOUL-TH-001 | Trust Chain Defined | Trust Hierarchy | HIGH |")
        block = ["```markdown", cc.REGISTRY_HEADING, ""] + table + ["", "```", ""]

        def drift(root):
            path = root / cc.SPECIFICATION
            text = path.read_text(encoding="utf-8").splitlines()
            text[row] = text[row].replace("| HIGH |", "| LOW |")
            path.write_text("\n".join(text[:start] + block + text[start:]) + "\n", encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED specification.md:{row + 1 + len(block)}: Severity 'LOW' of SOUL-TH-001 differs from the "
                      "attribute table 'HIGH'\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_missing_conformance_file_is_red(self):
        code, out, _ = self.run_main([], lambda root: (root / cc.CONFORMANCE).unlink())
        self.assertEqual(code, 1, out)
        self.assertIn("RED conformance.md: file is missing\n", out)

    def test_missing_specification_file_is_red(self):
        code, out, _ = self.run_main([], lambda root: (root / cc.SPECIFICATION).unlink())
        self.assertEqual(code, 1, out)
        self.assertIn("RED specification.md: file is missing\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_byte_that_is_not_utf8_in_a_file_it_reads_is_red_at_its_line(self):
        csv_rel = f"crosswalks/{cc.CROSSWALK_SET[0]['csv']}"
        for rel in (cc.SPECIFICATION, cc.CONFORMANCE, "domains/11-trust-hierarchy.md", csv_rel):
            def drift(root, rel=rel):
                path = root / rel
                lines = path.read_bytes().split(b"\n")
                lines[2] += b" \xff"
                path.write_bytes(b"\n".join(lines))
            with self.subTest(file=rel):
                code, out, _ = self.run_main([], drift)
                self.assertEqual(code, 1, out)
                self.assertIn(f"RED {rel}:3: byte 0xFF is not UTF-8\n", out)
                self.assertIn("\n1 problem(s) found", out)
                if rel == csv_rel:
                    # The CSV is not read, so its .md is neither rendered nor compared.
                    self.assertNotIn(f"{csv_rel}: ", out)

    def test_rest_of_the_file_is_read_after_a_byte_that_is_not_utf8(self):
        row = "| SOUL-TH-001 | Trust Chain Defined | Trust Hierarchy | HIGH |"
        lineno = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").splitlines().index(row) + 1

        def drift(root):
            path = root / cc.SPECIFICATION
            data = row.encode("utf-8")
            path.write_bytes(path.read_bytes().replace(data, data.replace(b"Defined", b"Defined\xff"), 1))
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED specification.md:{lineno}: byte 0xFF is not UTF-8\n", out)
        # The byte is read as U+FFFD, REPLACEMENT CHARACTER.
        self.assertIn(f"RED specification.md:{lineno}: Name 'Trust Chain Defined" "\N{REPLACEMENT CHARACTER}" "' of "
                      "SOUL-TH-001 differs from the domain heading 'Trust Chain Defined'\n", out)
        self.assertIn("\n2 problem(s) found", out)

    def test_attribute_row_under_a_line_that_markdown_does_not_read_as_a_fence_is_red_at_its_line(self):
        # The lines go after the blank line that ends the attribute table of SOUL-TH-001. Markdown reads none of their
        # backtick lines as a fence, so the attribute row is outside a code block and the tables after it are read.
        rel = "domains/11-trust-hierarchy.md"
        table_end = ("| **ID** | SOUL-TH-001 |\n| **Severity** | HIGH |\n"
                     "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |\n\n")
        text = (cc.ROOT / rel).read_text(encoding="utf-8")
        self.assertIn(table_end, text)
        first = text[:text.index(table_end) + len(table_end)].count("\n") + 1
        row = "| **Status** | deprecated |"
        for lines in (["    ```", row, "    ```"], ["\t```", row, "\t```"], ["```a``` b", row]):
            def drift(root, lines=lines):
                path = root / rel
                path.write_text(path.read_text(encoding="utf-8").replace(table_end, table_end + "\n".join(lines) + "\n",
                                                                         1), encoding="utf-8")
            with self.subTest(lines=lines):
                code, out, _ = self.run_main([], drift)
                self.assertEqual(code, 1, out)
                self.assertIn(f"RED {rel}:{first + lines.index(row)}: attribute row separated from the attribute table "
                              "of SOUL-TH-001; it is not read\n", out)
                self.assertIn("\n1 problem(s) found", out)

    def test_attribute_row_after_a_fenced_block_in_a_list_item_is_red_at_its_line(self):
        # The lines go after the blank line that ends the attribute table of SOUL-TH-001. Inside a list item Markdown
        # counts the indentation of a fence from the item's content column: the block of the first item closes at its
        # line indented four spaces, so the row under it is red, and the block of the second opens at its line indented
        # four spaces, so the row inside it is not read.
        rel = "domains/11-trust-hierarchy.md"
        table_end = ("| **ID** | SOUL-TH-001 |\n| **Severity** | HIGH |\n"
                     "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |\n\n")
        text = (cc.ROOT / rel).read_text(encoding="utf-8")
        self.assertIn(table_end, text)
        first = text[:text.index(table_end) + len(table_end)].count("\n") + 1
        row = "| **Status** | deprecated |"
        for lines, red in ((["- Example:", "", "  ```", "  text", "    ```", "", row], True),
                           (["1. Example:", "", "    ```", "    " + row, "    ```", ""], False)):
            def drift(root, lines=lines):
                path = root / rel
                path.write_text(path.read_text(encoding="utf-8").replace(table_end, table_end + "\n".join(lines) + "\n",
                                                                         1), encoding="utf-8")
            with self.subTest(lines=lines):
                code, out, _ = self.run_main([], drift)
                if red:
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"RED {rel}:{first + lines.index(row)}: attribute row separated from the attribute "
                                  "table of SOUL-TH-001; it is not read\n", out)
                    self.assertIn("\n1 problem(s) found", out)
                else:
                    self.assertEqual(code, 0, out)
                    self.assertIn("crosswalks: all checks green", out)

    def test_fenced_block_after_an_html_block_or_a_block_quote_closes_where_markdown_closes_it(self):
        # The lines go after the blank line that ends the attribute table of SOUL-TH-001. A list marker inside an HTML
        # block opens no list item, and a block quote line ends the list item above it, so the block after them opens
        # outside a list item and closes at its line indented two spaces: the row inside it is not read, the row after
        # it is red at its line, and the tables after it are read.
        rel = "domains/11-trust-hierarchy.md"
        table_end = ("| **ID** | SOUL-TH-001 |\n| **Severity** | HIGH |\n"
                     "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |\n\n")
        text = (cc.ROOT / rel).read_text(encoding="utf-8")
        self.assertIn(table_end, text)
        first = text[:text.index(table_end) + len(table_end)].count("\n") + 1
        row = "| **Status** | deprecated |"
        for lines, red in ((["<!-- notes", "- update the table", "-->", "", "  ```", row, "  ```", ""], False),
                           (["- Example:", "> quote", "", "  ```", row, "  ```", ""], False),
                           (["<!-- notes", "- update the table", "-->", "", "  ```", "text", "  ```", "", row], True)):
            def drift(root, lines=lines):
                path = root / rel
                path.write_text(path.read_text(encoding="utf-8").replace(table_end, table_end + "\n".join(lines) + "\n",
                                                                         1), encoding="utf-8")
            with self.subTest(lines=lines):
                code, out, _ = self.run_main([], drift)
                if red:
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"RED {rel}:{first + lines.index(row)}: attribute row separated from the attribute "
                                  "table of SOUL-TH-001; it is not read\n", out)
                    self.assertIn("\n1 problem(s) found", out)
                else:
                    self.assertEqual(code, 0, out)
                    self.assertIn("crosswalks: all checks green", out)

    def test_heading_inside_a_fenced_block_of_a_domain_file_is_not_read(self):
        # The lines go after the blank line that ends the attribute table of SOUL-TH-001. Markdown reads the lines of a
        # fenced block as code, so the heading there starts no control and no domain, and the copy stays green.
        rel = "domains/11-trust-hierarchy.md"
        table_end = ("| **ID** | SOUL-TH-001 |\n| **Severity** | HIGH |\n"
                     "| **Applicable tiers** | All (BASIC, TOOL-USING, AGENTIC, MULTI-AGENT) |\n\n")
        self.assertIn(table_end, (cc.ROOT / rel).read_text(encoding="utf-8"))
        for heading in ("### SOUL-TH-001: Trust Chain Defined", "# Domain 12: Capability Boundaries"):
            def drift(root, heading=heading):
                path = root / rel
                lines = ["```markdown", heading, "```", ""]
                path.write_text(path.read_text(encoding="utf-8").replace(table_end, table_end + "\n".join(lines) + "\n",
                                                                         1), encoding="utf-8")
            with self.subTest(heading=heading):
                code, out, _ = self.run_main([], drift)
                self.assertEqual(code, 0, out)
                self.assertIn("crosswalks: all checks green", out)

    def test_carriage_return_in_a_crosswalk_csv_is_red_without_the_write_hint(self):
        spec = cc.CROSSWALK_SET[0]

        def drift(root):
            path = root / "crosswalks" / spec["csv"]
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED crosswalks/{spec['csv']}:1: carriage return found; LF line endings required\n", out)
        self.assertIn(f"RED crosswalks/{spec['csv']}: file is not in canonical RFC 4180 form (minimal quoting, LF)\n",
                      out)
        self.assertIn("\n2 problem(s) found", out)

    def test_applicable_tiers_that_differ_from_the_matrix_are_red(self):
        domain = "16-agentic-safety.md"
        table = "| **ID** | SOUL-AS-004 |\n| **Severity** | LOW |\n| **Applicable tiers** | MULTI-AGENT |\n"
        heading = (cc.DOMAINS / domain).read_text(encoding="utf-8").splitlines().index(
            "### SOUL-AS-004: Reversibility Preference") + 1
        spec = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").splitlines()
        row = spec.index("| SOUL-AS-004 | -- | -- | -- | Yes |") + 1
        count = next(i for i in range(spec.index("### 3.3 AGENTIC"), len(spec)) if cc.TIER_COUNT.match(spec[i]))
        stated = int(cc.TIER_COUNT.match(spec[count]).group(1))

        def drift(root):
            path = root / "domains" / domain
            text = path.read_text(encoding="utf-8")
            self.assertIn(table, text)
            path.write_text(text.replace(table, table.replace("| MULTI-AGENT |", "| AGENTIC, MULTI-AGENT |")),
                            encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED specification.md:{row}: SOUL-AS-004 is marked Yes for MULTI-AGENT; its Applicable tiers "
                      f"attribute at domains/{domain}:{heading} names AGENTIC, MULTI-AGENT\n", out)
        self.assertIn(f"RED specification.md:{count + 1}: Applicable controls {stated} of AGENTIC differs from the "
                      f"{stated + 1} controls whose Applicable tiers attribute names AGENTIC\n", out)
        self.assertIn("\n2 problem(s) found", out)

    def long_number(self, rel, line, pattern, digits):
        # An edit that writes digits in place of the number that pattern reads on line, which rel holds once.
        def edit(root):
            path = root / rel
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count(line), 1)
            m = pattern.match(line)
            path.write_text(text.replace(line, line[:m.start(1)] + digits + line[m.end(1):]), encoding="utf-8")
        return edit

    def test_count_longer_than_int_converts_is_red_at_its_line(self):
        limit = int_digit_limit(self)
        spec = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").splitlines()
        count = next(i for i in range(spec.index("### 3.1 BASIC"), len(spec)) if cc.TIER_COUNT.match(spec[i]))
        code, out, _ = self.run_main([], self.long_number(cc.SPECIFICATION, spec[count], cc.TIER_COUNT,
                                                          "1" * (limit + 1)))
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED specification.md:{count + 1}: {too_long('Applicable controls of BASIC', limit)}\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_domain_number_longer_than_int_converts_is_red_at_its_line(self):
        limit = int_digit_limit(self)
        rel = "domains/11-trust-hierarchy.md"
        heading = (cc.ROOT / rel).read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(heading, "# Domain 11: Trust Hierarchy")
        code, out, _ = self.run_main([], self.long_number(rel, heading, cc.DOMAIN_HEADING, "1" * (limit + 1)))
        self.assertEqual(code, 1, out)
        # The red lines after it follow from it: the controls under the heading have no domain number.
        self.assertEqual(next(line for line in out.splitlines() if line.startswith("RED ")),
                         f"RED {rel}:1: {too_long('domain number', limit)}")
        self.assertNotIn("before domain heading", out)

    def test_write_restores_controls_json(self):
        rendered = (cc.ROOT / cc.CONTROLS_EXPORT).read_bytes()

        def drift(root):
            (root / cc.CONTROLS_EXPORT).write_bytes(rendered.replace(b"\n", b"\r\n"))
        code, out, export = self.run_main(["--write"], drift)
        self.assertEqual(code, 0, out)
        self.assertEqual(export, rendered)

    def header_only(self, spec, md):
        def edit(root):
            path = root / "crosswalks" / spec["csv"]
            path.write_bytes(path.read_bytes().split(b"\n", 1)[0] + b"\n")
            (root / "crosswalks" / spec["md"]).write_bytes(md)
        return edit

    def test_header_only_crosswalk_csv_still_compares_its_md(self):
        spec = cc.CROSSWALK_SET[0]
        code, out, _ = self.run_main([], self.header_only(spec, b"anything at all\r\n"))
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED crosswalks/{spec['md']}:1: carriage return found; LF line endings required; "
                      "run python3 scripts/check_crosswalks.py --write\n", out)
        self.assertIn(f"RED crosswalks/{spec['md']}:1: committed file differs from the render of its CSV; "
                      "run python3 scripts/check_crosswalks.py --write\n", out)
        self.assertIn("\n2 problem(s) found", out)

    def test_write_renders_the_md_of_a_header_only_crosswalk_csv(self):
        spec = cc.CROSSWALK_SET[0]
        controls, domain_order, _ = cc.load_domains([], cc.DOMAINS)
        code, out, md = self.run_main(["--write"], self.header_only(spec, b"anything at all\r\n"),
                                      keep=f"crosswalks/{spec['md']}")
        self.assertEqual(code, 0, out)
        self.assertIn(f"wrote crosswalks/{spec['md']}\n", out)
        self.assertIn(f"crosswalks/{spec['csv']}: 0 rows, 0 of {cc.CONTROL_COUNT} controls mapped, "
                      f"{cc.CONTROL_COUNT} with no mapping asserted\n", out)
        self.assertEqual(md, cc.render_md(spec, [], controls, domain_order).encode("utf-8"))
        self.assertIn(f"\n0 rows; 0 of {cc.CONTROL_COUNT} controls have at least one row; "
                      f"{cc.CONTROL_COUNT} are listed under no mapping asserted.\n", md.decode("utf-8"))

    def test_readme_without_the_crosswalk_bullet_names_the_list_that_holds_it(self):
        def drop(root):
            path = root / "README.md"
            text = path.read_text(encoding="utf-8")
            self.assertIn(cc.README_BULLET, text)
            path.write_text(text.replace(cc.README_BULLET, "", 1), encoding="utf-8")
        code, out, _ = self.run_main([], drop)
        self.assertEqual(code, 1, out)
        self.assertIn("RED README.md: the ruled crosswalk bullet of the Documentation list is missing or altered; "
                      "it is required verbatim\n", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_crosswalk_bullet_altered_in_the_list_with_an_unchanged_copy_in_a_fenced_block_is_red(self):
        # "RMF" becomes "RMFX" in the bullet of the Documentation list, and a block fenced at the end of the file holds
        # the unchanged bullet, which GFM renders as code.
        def drift(root):
            path = root / "README.md"
            text = path.read_text(encoding="utf-8")
            self.assertIn(cc.README_BULLET, text)
            text = text.replace(cc.README_BULLET, cc.README_BULLET.replace("RMF", "RMFX", 1), 1)
            path.write_text(text + "```text\n" + cc.README_BULLET + "\n```\n", encoding="utf-8")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn("RED README.md: the ruled crosswalk bullet of the Documentation list is missing or altered "
                      "outside a fenced code block, which GFM renders as code; it is required verbatim outside one\n",
                      out)
        self.assertIn("\n1 problem(s) found", out)
        self.assertNotIn("all checks green", out)

    def test_ruled_text_held_only_inside_a_fenced_block_is_red(self):
        # Each text of REQUIRED_PROSE fills lines of its own in its file. Here a block fenced by backticks or by tildes
        # wraps those lines, so the file holds the text only as code.
        for rel, name, ruled in cc.REQUIRED_PROSE:
            for opening, closing in (("```text", "```"), ("~~~", "~~~")):
                def wrap(root, rel=rel, ruled=ruled, opening=opening, closing=closing):
                    path = root / rel
                    text = path.read_text(encoding="utf-8")
                    self.assertIn(f"\n{ruled}\n", text)
                    path.write_text(text.replace(f"\n{ruled}\n", f"\n{opening}\n{ruled}\n{closing}\n", 1),
                                    encoding="utf-8")
                with self.subTest(text=name, fence=opening):
                    code, out, _ = self.run_main([], wrap)
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"RED {rel}: the ruled {name} is missing or altered outside a fenced code block, "
                                  "which GFM renders as code; it is required verbatim outside one\n", out)
                    self.assertIn("\n1 problem(s) found", out)
                    self.assertNotIn("all checks green", out)

    def test_ruled_text_held_only_inside_a_fenced_block_is_red_in_a_file_with_crlf_or_cr_line_endings(self):
        # A block fenced by backticks wraps the lines of each text of REQUIRED_PROSE, as in the test above, and the file
        # is then saved with CRLF or CR line endings, as an editor may save a working copy: .gitattributes pins LF for
        # crosswalks/README.md only in a checkout, and not at all for README.md. GFM ends a line at LF, CR LF or CR, so
        # the report is the one a file with LF line endings gives. The three lines of the basis definitions are joined
        # by the file's line ending, which is not LF here.
        for rel, name, ruled in cc.REQUIRED_PROSE:
            for ending in ("\r\n", "\r"):
                def wrap(root, rel=rel, ruled=ruled, ending=ending):
                    path = root / rel
                    text = path.read_text(encoding="utf-8")
                    self.assertIn(f"\n{ruled}\n", text)
                    text = text.replace(f"\n{ruled}\n", f"\n```\n{ruled}\n```\n", 1)
                    path.write_bytes(text.replace("\n", ending).encode("utf-8"))
                with self.subTest(text=name, ending=ending):
                    code, out, _ = self.run_main([], wrap)
                    self.assertEqual(code, 1, out)
                    self.assertIn(f"RED {rel}: the ruled {name} is missing or altered outside a fenced code block, "
                                  "which GFM renders as code; it is required verbatim outside one\n", out)
                    self.assertIn("\n1 problem(s) found", out)
                    self.assertNotIn("all checks green", out)

    def test_ruled_text_with_one_of_its_lines_inside_a_fenced_block_is_red(self):
        # The first of the three lines of the basis definitions becomes the last line of a block fenced in the list item
        # "- item". The next line ends the item, and the block with it, so GFM renders that first line as code and the
        # other two as list items.
        def wrap(root):
            path = root / "crosswalks" / "README.md"
            text = path.read_text(encoding="utf-8")
            ruled = cc.BASIS_DEFINITIONS
            self.assertIn(f"\n{ruled}\n", text)
            path.write_text(text.replace(f"\n{ruled}\n", f"\n- item\n  ```\n  {ruled}\n", 1), encoding="utf-8")
        code, out, _ = self.run_main([], wrap)
        self.assertEqual(code, 1, out)
        self.assertIn("RED crosswalks/README.md: the ruled basis definitions is missing or altered outside a fenced "
                      "code block, which GFM renders as code; it is required verbatim outside one\n", out)
        self.assertIn("\n1 problem(s) found", out)
        self.assertNotIn("all checks green", out)

    def test_ruled_text_with_a_copy_in_a_fenced_block_too_is_green(self):
        def copy(root):
            for rel, _, ruled in cc.REQUIRED_PROSE:
                path = root / rel
                path.write_text(path.read_text(encoding="utf-8") + "\n```text\n" + ruled + "\n```\n", encoding="utf-8")
        code, out, _ = self.run_main([], copy)
        self.assertEqual(code, 0, out)
        self.assertIn("crosswalks: all checks green", out)

    def test_unreadable_crosswalk_csv_is_red_without_a_render(self):
        spec = cc.CROSSWALK_SET[0]

        def drift(root):
            (root / "crosswalks" / spec["csv"]).write_bytes(b"control_id,control_title\n")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED crosswalks/{spec['csv']}:1: header must be exactly {','.join(cc.HEADER)}\n", out)
        self.assertNotIn(f"crosswalks/{spec['csv']}: ", out)
        self.assertIn("\n1 problem(s) found", out)

    def test_row_naming_a_control_no_domain_file_holds_is_red_in_the_report(self):
        spec = cc.CROSSWALK_SET[0]

        def unknown(root):
            path = root / "crosswalks" / spec["csv"]
            lines = path.read_text(encoding="utf-8").split("\n")
            lines[1] = "SOUL-TH-000" + lines[1][lines[1].index(","):]
            path.write_text("\n".join(lines), encoding="utf-8")
        code, out, _ = self.run_main([], unknown)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED crosswalks/{spec['csv']}:2: control_id 'SOUL-TH-000' is not a control heading in "
                      "domains/\n", out)
        self.assertRegex(out, r"\n\d+ problem\(s\) found")

    def test_row_whose_control_heading_is_deleted_or_fenced_is_red_in_the_report(self):
        def delete(root):
            path = root / "domains" / "11-trust-hierarchy.md"
            text = path.read_text(encoding="utf-8")
            path.write_text("\n".join(line for line in text.split("\n") if not line.startswith("### SOUL-TH-002: ")),
                            encoding="utf-8")

        def unclosed(root):
            # A fence that no line closes, after the blank line that ends the attribute table of SOUL-TH-001: the
            # control headings after it are inside the block.
            path = root / "domains" / "11-trust-hierarchy.md"
            lines = path.read_text(encoding="utf-8").split("\n")
            i = lines.index(next(line for line in lines if line.startswith("### SOUL-TH-001: ")))
            while not lines[i].startswith("|"):
                i += 1
            while lines[i].startswith("|"):
                i += 1
            self.assertEqual(lines[i], "")
            lines.insert(i + 1, "```")
            path.write_text("\n".join(lines), encoding="utf-8")
        for name, edit in (("deleted", delete), ("unclosed fence", unclosed)):
            with self.subTest(heading=name):
                code, out, _ = self.run_main([], edit)
                self.assertEqual(code, 1, out)
                self.assertIn("control_id 'SOUL-TH-002' is not a control heading in domains/\n", out)
                self.assertRegex(out, r"\n\d+ problem\(s\) found")

    def test_ruled_text_held_only_in_an_indented_code_block_or_an_html_block_is_red(self):
        # The ruled text GFM renders is altered, and an unchanged copy is appended in a block GFM does not render as
        # Markdown text.
        for rel, name, ruled in cc.REQUIRED_PROSE:
            first = ruled.split("\n")[0]
            for kind, copy in (("indented code block", "\n" + "\n".join("    " + line for line in ruled.split("\n"))),
                               ("HTML comment", "\n<!--\n" + ruled + "\n-->"),
                               ("HTML block", "\n<div>\n" + ruled + "\n</div>")):
                def alter(root, rel=rel, ruled=ruled, first=first, copy=copy):
                    path = root / rel
                    text = path.read_text(encoding="utf-8")
                    self.assertIn(f"\n{ruled}\n", text)
                    altered = first[:-1] + "X" + first[-1] + ruled[len(first):]
                    path.write_text(text.replace(f"\n{ruled}\n", f"\n{altered}\n", 1) + copy + "\n",
                                    encoding="utf-8")
                with self.subTest(text=name, copy=kind):
                    code, out, _ = self.run_main([], alter)
                    self.assertEqual(code, 1, out)
                    if kind == "indented code block" and "\n" in ruled:
                        # Each line of the copy starts with four spaces, so the file no longer holds the text.
                        self.assertIn(f"RED {rel}: the ruled {name} is missing or altered; it is required verbatim\n",
                                      out)
                    else:
                        self.assertIn(f"RED {rel}: the ruled {name} is missing or altered outside a code block or an "
                                      "HTML block, which GFM does not render as Markdown text; it is required verbatim "
                                      "outside one\n", out)
                    # The banned scan also reads the altered text of crosswalks/README.md, which is no ruled constant.
                    self.assertNotIn("all checks green", out)

    def test_ruled_text_with_a_copy_in_an_indented_code_block_or_an_html_block_too_is_green(self):
        def copy(root):
            for rel, _, ruled in cc.REQUIRED_PROSE:
                path = root / rel
                indented = "\n".join("    " + line for line in ruled.split("\n"))
                path.write_text(path.read_text(encoding="utf-8") + "\n" + indented + "\n\n<!--\n" + ruled + "\n-->\n",
                                encoding="utf-8")
        code, out, _ = self.run_main([], copy)
        self.assertEqual(code, 0, out)
        self.assertIn("crosswalks: all checks green", out)

    def test_byte_that_is_not_utf8_in_a_readme_it_requires_prose_from_is_red_at_its_line(self):
        for rel in ("README.md", "crosswalks/README.md"):
            def append(root, rel=rel):
                path = root / rel
                lineno = path.read_bytes().count(b"\n") + 1
                path.write_bytes(path.read_bytes() + b"\xff\n")
                return lineno
            lines = []
            with self.subTest(file=rel):
                code, out, _ = self.run_main([], lambda root, rel=rel: lines.append(append(root)))
                self.assertEqual(code, 1, out)
                self.assertIn(f"RED {rel}:{lines[0]}: byte 0xFF is not UTF-8\n", out)
                self.assertEqual(out.count("is not UTF-8"), 1, out)
                self.assertIn("\n1 problem(s) found", out)


def section_above(text, passage):
    """The title of the last H2 heading outside a code fence above passage, or None."""
    end = text.find(passage)
    if end < 0:
        return None
    title, fence = None, False
    for line in text[:end].splitlines():
        if re.match(r"\s*(```|~~~)", line):
            fence = not fence
        elif not fence and line.startswith("## "):
            title = line[3:].strip()
    return title


class RequiredProseLabels(unittest.TestCase):
    """The name the message gives a README.md passage names the section of README.md that holds it, so a
    reader of a red run finds the passage where the message sends them."""

    def test_label_names_the_readme_section_of_the_passage(self):
        readme = (cc.ROOT / "README.md").read_text(encoding="utf-8")
        passages = [(name, text) for rel, name, text in cc.REQUIRED_PROSE if rel == "README.md"]
        self.assertNotEqual(passages, [])
        for name, text in passages:
            with self.subTest(label=name):
                section = section_above(readme, text)
                self.assertIsNotNone(section, f"no section of README.md holds the {name}")
                self.assertIn(section, name, f"the {name} sits under '## {section}' in README.md")

    def test_passage_is_read_under_the_heading_above_it_outside_a_fence(self):
        text = "# Title\n\n## Related Work\n\n```\n## Not a section\n```\n\n- the bullet\n\n## Documentation\n"
        self.assertEqual(section_above(text, "- the bullet"), "Related Work")
        self.assertIsNone(section_above(text, "- another bullet"))


class ReadmeTerms(unittest.TestCase):
    """README.md prose, and the prose of the docs pages that took its reference
    text: an acronym in parentheses follows its expansion, and a component the
    specification and domain files never name is not named."""

    PAGES = ("README.md", "docs/overview.md", "docs/related-work.md", "docs/ci.md")

    def setUp(self):
        self.pages = {name: (cc.ROOT / name).read_text(encoding="utf-8") for name in self.PAGES}

    def test_an_acronym_in_parentheses_follows_its_expansion(self):
        for name, text in self.pages.items():
            for match in re.finditer(r" \(([A-Z][A-Z0-9]{1,5})\)", text):
                acronym = match.group(1)
                words = re.findall(r"[A-Za-z0-9]+", text[:match.start()])[-len(acronym):]
                with self.subTest(page=name, acronym=acronym):
                    self.assertEqual("".join(word[0] for word in words).upper(), acronym,
                                     f"{name}: ({acronym}) follows {' '.join(words)!r}, not its expansion")

    def test_no_component_the_specification_does_not_name(self):
        defined = (cc.ROOT / cc.SPECIFICATION).read_text(encoding="utf-8").lower()
        defined += "".join(path.read_text(encoding="utf-8").lower() for path in sorted(cc.DOMAINS.glob("*.md")))
        for term in ("broker",):
            for name, text in self.pages.items():
                with self.subTest(term=term, page=name):
                    if term not in defined:
                        lines = [n for n, line in enumerate(text.splitlines(), 1) if term in line.lower()]
                        self.assertEqual(lines, [], f"{name} names {term!r}, which the specification does not")


class TimeBound(unittest.TestCase):
    TIMED_TESTS = ("test_long_row_that_does_not_match_is_rejected_in_linear_time",
                   "test_heading_with_a_long_run_of_interior_spaces_is_read_in_linear_time")

    def test_runs_under_python3_O_and_OO_skip_the_time_bound(self):
        # A skip placed after the timed call still reports a skip, so the clock of this module fails the test that
        # reads it. unittest times each test with time.perf_counter too, so only this module's name is replaced.
        for name in self.TIMED_TESTS:
            for optimize in (1, 2):
                result = unittest.TestResult()
                clock = mock.Mock(perf_counter=mock.Mock(side_effect=self.failureException("timed before the skip")))
                with self.subTest(test=name, optimize=optimize), \
                        mock.patch.object(sys, "flags", mock.Mock(optimize=optimize)), \
                        mock.patch.object(sys.modules[__name__], "time", clock):
                    EntryAttributes(name).run(result)
                    clock.perf_counter.assert_not_called()
                    self.assertEqual([TIME_BOUND_SKIP], [reason for _, reason in result.skipped])

    def test_the_run_without_python3_O_checks_the_time_bound(self):
        # A skip here would report this test as skipped, not failed, so skipTest is replaced and must not be called.
        with mock.patch.object(sys, "flags", mock.Mock(optimize=0)), mock.patch.object(self, "skipTest") as skip:
            skip_the_time_bound_when_optimized(self)
        skip.assert_not_called()


if __name__ == "__main__":
    unittest.main()
