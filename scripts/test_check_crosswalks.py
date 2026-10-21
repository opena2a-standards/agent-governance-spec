#!/usr/bin/env python3
"""Tests for scripts/check_crosswalks.py: the JSON control export, the render
comparison, the domain and control headings, the attribute tables, the
section 5.3 registry table, the section 3.5 applicability matrix and the tier
counts of section 3, the report on a byte that is not UTF-8 in a file it
reads, and the .gitattributes line-ending pins of the files it compares byte
for byte; the name its message gives a README.md passage it requires
verbatim; and the terms README.md and the docs pages that took its reference
text use in their prose.

Run from anywhere:  python3 scripts/test_check_crosswalks.py

Standard library only. The tests read the committed domain files,
controls.json, specification.md, README.md and the pages under docs/, ask git for the eol attribute of the
byte-checked files, and write no tracked file: the synthetic domain files and
the repository copy that main() runs against are written to a temporary
directory, and bytecode caching is turned off before the import.
"""

import contextlib
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


ACTIVE = ("### SOUL-TH-001: First", [("ID", "SOUL-TH-001"), ("Severity", "HIGH")])


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

    def check(self, rows):
        errors = []
        cc.check_registry_table(errors, "specification.md", REGISTRY.format(rows="\n".join(rows)),
                                self.ENTRIES, self.DOMAINS)
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

    def check(self, rows=ROWS, steps=STEPS):
        errors = []
        text = CONFORMANCE.format(rows="\n".join(rows), steps="\n".join(steps))
        cc.check_conformance_levels(errors, "conformance.md", text, self.ENTRIES, self.ATTRIBUTES)
        return errors

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

    def check(self, rows, tiers=None):
        errors = []
        cc.check_applicability_matrix(errors, "specification.md", MATRIX.format(rows="\n".join(rows)),
                                      tiers or self.TIERS)
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

    def test_missing_heading_or_header_is_red(self):
        errors = []
        cc.check_applicability_matrix(errors, "specification.md", "# Spec\n", self.TIERS)
        self.assertEqual(errors, ["RED specification.md: heading '### 3.5 Control Applicability Matrix' not found"])
        errors = []
        cc.check_applicability_matrix(errors, "specification.md",
                                      MATRIX.format(rows="").replace("| MULTI-AGENT |", "| MULTI |"), self.TIERS)
        self.assertEqual(errors, ["RED specification.md: the matrix under section 3.5 must have the header "
                                  "| Control ID | BASIC | TOOL-USING | AGENTIC | MULTI-AGENT |"])


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

    def check(self, text, tiers=None):
        errors = []
        cc.check_tier_counts(errors, "specification.md", text, tiers or self.TIERS)
        return errors

    def test_counts_equal_to_the_attributes_are_green(self):
        self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, 2, 3)), [])

    def test_count_that_differs_is_red_at_its_line(self):
        self.assertEqual(self.check(TIER_SECTIONS.format(1, 1, 3, 3)), [
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

    def test_unreadable_crosswalk_csv_is_red_without_a_render(self):
        spec = cc.CROSSWALK_SET[0]

        def drift(root):
            (root / "crosswalks" / spec["csv"]).write_bytes(b"control_id,control_title\n")
        code, out, _ = self.run_main([], drift)
        self.assertEqual(code, 1, out)
        self.assertIn(f"RED crosswalks/{spec['csv']}:1: header must be exactly {','.join(cc.HEADER)}\n", out)
        self.assertNotIn(f"crosswalks/{spec['csv']}: ", out)
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
