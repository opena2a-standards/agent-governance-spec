#!/usr/bin/env python3
"""Tests for the JSON control export written by scripts/check_crosswalks.py.

Run from anywhere:  python3 scripts/test_check_crosswalks.py

Standard library only. The tests read the committed domain files and
controls.json and write nothing inside the repository; the synthetic domain
files they need are written to a temporary directory.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

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
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "11-trust-hierarchy.md").write_text(domain_file(controls), encoding="utf-8")
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
        committed = (cc.ROOT / cc.CONTROLS_EXPORT).read_text(encoding="utf-8")
        self.assertEqual(committed, cc.render_controls_json(self.entries))

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
        cc.compare_render(errors, "controls.json", '{\n  "a": 2\n}\n', '{\n  "a": 1\n}\n', "the domain files")
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("RED controls.json:2: committed file differs"), errors[0])

    def test_equal_file_is_green(self):
        errors = []
        cc.compare_render(errors, "controls.json", "{}\n", "{}\n", "the domain files")
        self.assertEqual(errors, [])


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

    def assert_red(self, rows, fragment):
        entries, errors = entries_for([ACTIVE, ("### SOUL-TH-002: Second", rows)])
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(fragment, errors[0])
        self.assertTrue(errors[0].startswith("RED "), errors[0])

    def test_deprecated_without_replaced_by_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Status", "deprecated")],
                        "Replaced by")

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
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Version", "1.1")], "1.1")

    def test_id_attribute_that_differs_from_the_heading_is_red(self):
        self.assert_red([("ID", "SOUL-TH-003"), ("Severity", "LOW")], "SOUL-TH-003")

    def test_repeated_attribute_is_red(self):
        self.assert_red([("ID", "SOUL-TH-002"), ("Severity", "LOW"), ("Severity", "HIGH")], "Severity")


if __name__ == "__main__":
    unittest.main()
