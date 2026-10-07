#!/usr/bin/env python3
"""Tests for scripts/check_crosswalks.py: the JSON control export, the render
comparison, the attribute tables, the section 5.3 registry table, and the
.gitattributes line-ending pins of the files it compares byte for byte.

Run from anywhere:  python3 scripts/test_check_crosswalks.py

Standard library only. The tests read the committed domain files,
controls.json, and specification.md, ask git for the eol attribute of the
byte-checked files, and write no tracked file: the synthetic domain files and
the repository copy that main() runs against are written to a temporary
directory, and bytecode caching is turned off before the import.
"""

import contextlib
import io
import json
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
            self.assertEqual(errors, ["RED controls.json:1: carriage return found; LF line endings required"],
                             repr(ending))

    def test_one_crlf_line_among_lf_lines_is_red_at_that_line(self):
        rendered = '{\n  "a": 1,\n  "b": 2\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": 1,\r\n  "b": 2\n}\n', rendered)
        self.assertEqual(errors, ["RED controls.json:2: carriage return found; LF line endings required"])

    def test_line_endings_and_a_content_difference_are_both_red(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b'{\r\n  "a": 2\r\n}\r\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:1: carriage return found; LF line endings required",
            "RED controls.json:2: committed file differs from the render of the domain files; "
            "run python3 scripts/check_crosswalks.py --write",
        ])

    def test_cr_in_place_of_an_lf_before_a_blank_line_is_also_a_difference(self):
        rendered = '{\n  "a": 1,\n\n  "b": 2\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": 1,\r\n  "b": 2\n}\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:2: carriage return found; LF line endings required",
            "RED controls.json:3: committed file differs from the render of the domain files; "
            "run python3 scripts/check_crosswalks.py --write",
        ])

    def test_utf8_byte_order_mark_is_red(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b"\xef\xbb\xbf" + rendered.encode("utf-8"), rendered)
        self.assertEqual(errors, ["RED controls.json:1: file starts with a UTF-8 BOM"])

    def test_invalid_utf8_is_red_without_a_traceback(self):
        rendered = '{\n  "a": 1\n}\n'
        errors = self.compare_committed_bytes(b'{\n  "a": \xff\n}\n', rendered)
        self.assertEqual(errors, [
            "RED controls.json:2: byte 0xFF is not UTF-8; run python3 scripts/check_crosswalks.py --write",
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
            "RED controls.json:1: carriage return found; LF line endings required",
            "RED controls.json:3: committed file, with line endings read as LF, is shorter than its "
            "render of the domain files, which continues here; run python3 scripts/check_crosswalks.py --write",
        ])
        self.assertEqual(self.compare_committed_bytes(b"a\rb\rc\r\r", "a\nb\nc\n"), [
            "RED controls.json:1: carriage return found; LF line endings required",
            "RED controls.json:4: committed file, with line endings read as LF, is longer than its "
            "render of the domain files, which ends here; run python3 scripts/check_crosswalks.py --write",
        ])

    def test_length_difference_names_the_text_with_the_bom_removed(self):
        # 7 committed bytes against a 6-byte render: shorter only once the BOM is removed.
        self.assertEqual(self.compare_committed_bytes(b"\xef\xbb\xbfa\nb\n", "a\nb\nc\n"), [
            "RED controls.json:1: file starts with a UTF-8 BOM",
            "RED controls.json:3: committed file, with its BOM removed, is shorter than its "
            "render of the domain files, which continues here; run python3 scripts/check_crosswalks.py --write",
        ])
        self.assertEqual(self.compare_committed_bytes(b"\xef\xbb\xbfa\r\nb\r\nc\r\n\r\n", "a\nb\nc\n"), [
            "RED controls.json:1: file starts with a UTF-8 BOM",
            "RED controls.json:1: carriage return found; LF line endings required",
            "RED controls.json:4: committed file, with its BOM removed and line endings read as LF, is longer "
            "than its render of the domain files, which ends here; run python3 scripts/check_crosswalks.py --write",
        ])


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

    def test_attribute_row_inside_a_fenced_block_is_not_read(self):
        # domain_file puts "| **Status** | ignored |" in a fenced block after every table.
        self.assertIn("```\n| **Status** | ignored |\n```", domain_file([ACTIVE]))
        entries, errors = entries_for([ACTIVE])
        self.assertEqual(errors, [])
        self.assertEqual(entries[0]["status"], "active")

    def test_long_row_that_does_not_match_is_rejected_in_linear_time(self):
        row = "| **x** | " + "** | " * 20000 + "x"
        start = time.perf_counter()
        self.assertIsNone(cc.ATTRIBUTE_ROW.match(row))
        self.assertLess(time.perf_counter() - start, 1.0)

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
        ]), ["RED specification.md: the registry rows under section 5.3 are not in domain order then NNN"])

    def test_row_with_the_wrong_number_of_cells_is_red(self):
        self.assertEqual(self.check([
            "| SOUL-TH-001 | First Control | Trust Hierarchy |",
            "| SOUL-TH-002 | Second Control | Trust Hierarchy | LOW |",
        ]), [
            "RED specification.md:7: registry row has 3 cells; expected 4",
            "RED specification.md: the registry table under section 5.3 has no row for SOUL-TH-001",
        ])

    def test_missing_heading_is_red(self):
        errors = []
        cc.check_registry_table(errors, "specification.md", "# Spec\n", self.ENTRIES, self.DOMAINS)
        self.assertEqual(errors, ["RED specification.md: heading '### 5.3 Complete Control Registry' not found"])


class LineEndingPins(unittest.TestCase):
    def test_the_byte_checked_files_are_pinned_to_lf(self):
        paths = [f"crosswalks/{spec[kind]}" for spec in cc.CROSSWALK_SET for kind in ("csv", "md")]
        paths.append(cc.CONTROLS_EXPORT)
        try:
            result = subprocess.run(["git", "-C", str(cc.ROOT), "check-attr", "eol", "--"] + paths,
                                    capture_output=True, text=True, check=True)
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git, or a git work tree, is not available")
        self.assertEqual(result.stdout.splitlines(), [f"{p}: eol: lf" for p in paths])


class MainRun(unittest.TestCase):
    """main() against a copy of the repository files it reads, in a temporary directory."""

    def run_main(self, argv, edit=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(cc.DOMAINS, root / "domains")
            shutil.copytree(cc.CROSSWALKS, root / "crosswalks")
            for name in ("README.md", cc.CONTROLS_EXPORT, cc.SPECIFICATION):
                shutil.copyfile(cc.ROOT / name, root / name)
            if edit:
                edit(root)
            out = io.StringIO()
            with mock.patch.multiple(cc, ROOT=root, CROSSWALKS=root / "crosswalks", DOMAINS=root / "domains"), \
                    contextlib.redirect_stdout(out):
                code = cc.main(argv)
            export = (root / cc.CONTROLS_EXPORT).read_bytes()
        return code, out.getvalue(), export

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

    def test_write_restores_controls_json(self):
        rendered = (cc.ROOT / cc.CONTROLS_EXPORT).read_bytes()

        def drift(root):
            (root / cc.CONTROLS_EXPORT).write_bytes(rendered.replace(b"\n", b"\r\n"))
        code, out, export = self.run_main(["--write"], drift)
        self.assertEqual(code, 0, out)
        self.assertEqual(export, rendered)


if __name__ == "__main__":
    unittest.main()
