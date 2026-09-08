"""Owner V2 controls. Fixtures only; never read or mutate real Skills/Memory."""
from pathlib import Path
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import bookkeeping_v2


FIELDS = ("view_count", "use_count", "last_viewed_at", "last_used_at")


def record(**updates):
    value = {
        "created_by": None,
        "use_count": 1,
        "view_count": 2,
        "last_used_at": "2026-09-07T00:00:00+00:00",
        "last_viewed_at": None,
        "patch_count": 0,
        "patch_generation": 0,
        "last_reused_patch_generation": 0,
        "last_patched_at": None,
        "created_at": "2026-09-01T00:00:00+00:00",
        "state": "active",
        "pinned": False,
        "archived_at": None,
    }
    value.update(updates)
    return value


class V2PolicyControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "skills"
        self.root.mkdir(mode=0o700)
        for name in ("alpha", "name/with~escape"):
            skill = self.root / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: "+name+"\n---\nfixture instruction\n")
        self.usage = self.root / ".usage.json"
        self.lock = self.root / ".usage.json.lock"
        self.lock.touch(mode=0o644)
        self.data = {"alpha": record(), "name/with~escape": record(use_count=0)}
        self.write(self.data)
        os.chmod(self.usage, 0o600)
        self.policy = bookkeeping_v2.create_policy(
            self.usage,
            owner_sha256="1" * 64,
            dependency_sha256="2" * 64,
            selection_binding={"matrix_sha256": "3" * 64, "gate_count": 29},
        )

    def write(self, value):
        self.usage.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

    def evaluate(self):
        return bookkeeping_v2.evaluate(self.policy)

    def assertReject(self, reason):
        result = self.evaluate()
        self.assertEqual(result["V2_INPUT_INTEGRITY_RESULT"], "REJECT")
        self.assertTrue(any(reason in item for item in result["reasons"]), result)

    def test_policy_enumerates_records_fields_schema_and_escaped_pointers(self):
        self.assertEqual(self.policy["schema"], "ep19-scoped-runtime-bookkeeping-v2")
        self.assertEqual(self.policy["privacy"], "PRIVATE_NOT_FOR_PUBLIC_PACKAGE")
        self.assertEqual(self.policy["eligible_record_ids"], sorted(self.data))
        self.assertIn("/name~1with~0escape/view_count", self.policy["eligible_json_pointers"])
        self.assertEqual(self.policy["temporary_namespace"]["regex"], r"^\.usage_[a-z0-9_]{8}\.tmp$")
        self.assertEqual(self.policy["selection_binding"]["gate_count"], 29)

    def test_unchanged_passes_both_policies(self):
        result = self.evaluate()
        self.assertEqual(result["OLD_STRICT_PRESERVATION_RESULT"], "PASS")
        self.assertEqual(result["V2_INPUT_INTEGRITY_RESULT"], "PASS")
        self.assertEqual(result["V2_BOOKKEEPING_EVALUATION"], "PASS")

    def test_approved_counts_and_timestamps_pass_writer_unknown(self):
        changed = json.loads(json.dumps(self.data))
        changed["alpha"].update(use_count=4, view_count=3,
                                last_used_at="2026-09-08T00:00:00+00:00",
                                last_viewed_at="2026-09-08T00:01:00+00:00")
        self.write(changed)
        result = self.evaluate()
        self.assertEqual(result["OLD_STRICT_PRESERVATION_RESULT"], "OLD_STRICT_REJECT")
        self.assertEqual(result["V2_INPUT_INTEGRITY_RESULT"], "PASS")
        self.assertEqual(result["WRITER_ATTRIBUTION"], "NOT_ESTABLISHED")
        self.assertEqual(result["claim"], "STRICT_INPUTS_PRESERVED_WITH_SCOPED_BOOKKEEPING_VARIATION")

    def test_atomic_replacement_and_root_times_are_compatible(self):
        changed = json.loads(json.dumps(self.data)); changed["alpha"]["view_count"] += 1
        temp = self.root / ".usage_abc12_3z.tmp"
        temp.write_text(json.dumps(changed, sort_keys=True, indent=2) + "\n")
        os.chmod(temp, 0o600)
        os.replace(temp, self.usage)
        result = self.evaluate()
        self.assertEqual(result["V2_BOOKKEEPING_EVALUATION"], "PASS")
        self.assertEqual(result["OLD_STRICT_PRESERVATION_RESULT"], "OLD_STRICT_REJECT")
        self.assertIn("st_ino", result["observed_metadata_differences"]["usage_file"])

    def test_record_insertion_and_deletion_reject(self):
        for variant in ("insert", "delete"):
            with self.subTest(variant=variant):
                value = json.loads(json.dumps(self.data))
                if variant == "insert": value["new"] = record()
                else: value.pop("alpha")
                self.write(value); self.assertReject("RECORD_MEMBERSHIP_CHANGED")
                self.write(self.data)

    def test_strict_and_unknown_field_changes_reject(self):
        for field, value in (("state", "stale"), ("patch_generation", 1),
                             ("last_reused_patch_generation", 1), ("pinned", True),
                             ("sync", True), ("unknown", "x")):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(self.data)); changed["alpha"][field] = value
                self.write(changed); self.assertReject("FIELD_MEMBERSHIP_CHANGED" if field in ("sync", "unknown") else "STRICT_VALUE_CHANGED")
                self.write(self.data)

    def test_invalid_types_nonfinite_duplicates_malformed_and_decrease_reject(self):
        cases = []
        for field, value in (("view_count", True), ("use_count", -1),
                             ("last_viewed_at", 7), ("last_used_at", "not-a-time")):
            changed = json.loads(json.dumps(self.data)); changed["alpha"][field] = value
            cases.append((field, json.dumps(changed), "SCHEMA"))
        changed = json.loads(json.dumps(self.data)); changed["alpha"]["use_count"] = 0
        cases.append(("decrease", json.dumps(changed), "COUNT_DECREASE"))
        cases.extend((("nonfinite", '{"alpha":{"view_count":NaN}}', "NONFINITE_JSON"),
                      ("duplicate", '{"alpha":{},"alpha":{}}', "DUPLICATE_JSON_KEY"),
                      ("malformed", '{', "MALFORMED_JSON")))
        for name, raw, reason in cases:
            with self.subTest(name=name):
                self.usage.write_text(raw); self.assertReject(reason); self.write(self.data)

    def test_exponent_overflow_rejects_inside_unknown_nested_value(self):
        nested=json.loads(json.dumps(self.data));nested["alpha"]["nested"]={"protected":1.0};self.write(nested)
        policy=bookkeeping_v2.create_policy(self.usage,owner_sha256="1"*64,dependency_sha256="2"*64,selection_binding={"matrix_sha256":"3"*64,"gate_count":29})
        raw=json.dumps(nested).replace('"protected": 1.0','"protected": 1e999')
        self.usage.write_text(raw)
        result=bookkeeping_v2.evaluate(policy)
        self.assertTrue(any("NONFINITE_JSON EXPONENT_OVERFLOW" in item for item in result["reasons"]),result)

    def test_timestamp_backwards_and_null_regression_reject(self):
        for value in ("2026-09-06T00:00:00+00:00", None):
            with self.subTest(value=value):
                changed = json.loads(json.dumps(self.data)); changed["alpha"]["last_used_at"] = value
                self.write(changed); self.assertReject("TIMESTAMP_"); self.write(self.data)

    def test_permission_symlink_hardlink_and_root_entry_violations_reject(self):
        os.chmod(self.usage, 0o644); self.assertReject("USAGE_MODE_CHANGED"); os.chmod(self.usage, 0o600)
        extra = self.root / "unexpected"; extra.write_text("x"); self.assertReject("ROOT_ENTRY_SET_CHANGED"); extra.unlink()
        hard = self.root / "hard"; os.link(self.usage, hard); self.assertReject("USAGE_LINK_COUNT"); hard.unlink()
        real = self.root / "real"; shutil.copyfile(self.usage, real); self.usage.unlink(); self.usage.symlink_to(real)
        self.assertReject("USAGE_NOT_REGULAR_OR_SYMLINK")

    def test_persistent_temp_and_lock_change_reject(self):
        (self.root / ".usage_abc12_3z.tmp").write_text("short-lived became persistent")
        self.assertReject("ROOT_ENTRY_SET_CHANGED")
        (self.root / ".usage_abc12_3z.tmp").unlink()
        os.chmod(self.lock, 0o600); self.assertReject("LOCK_METADATA_CHANGED")

    def test_persistent_reserved_temp_cannot_be_laundered_into_policy(self):
        (self.root/".usage_abcdefgh.tmp").write_text("persistent")
        with self.assertRaisesRegex(RuntimeError,"PERSISTENT_RESERVED_TEMP_AT_BASELINE"):
            bookkeeping_v2.create_policy(self.usage,owner_sha256="1"*64,dependency_sha256="2"*64,selection_binding={"matrix_sha256":"3"*64,"gate_count":29})

    def test_nested_category_inventory_name_is_eligible_and_orphan_is_strict(self):
        data=json.loads(json.dumps(self.data));data["orphan-record"]=record();self.write(data)
        policy=bookkeeping_v2.create_policy(self.usage,owner_sha256="1"*64,dependency_sha256="2"*64,selection_binding={"matrix_sha256":"3"*64,"gate_count":29})
        self.assertIn("name/with~escape",policy["eligible_record_ids"])
        self.assertIn("orphan-record",policy["ineligible_record_ids"])
        data["orphan-record"]["view_count"]+=1;self.write(data)
        result=bookkeeping_v2.evaluate(policy)
        self.assertTrue(any("STRICT_VALUE_CHANGED orphan-record" in item for item in result["reasons"]),result)

    def test_root_replacement_and_injected_owner_boundary_reject(self):
        moved = self.root.parent / "moved-skills"
        os.rename(self.root, moved); shutil.copytree(moved, self.root, copy_function=shutil.copy2)
        self.assertReject("SKILLS_ROOT_STRICT_METADATA_CHANGED")

    def test_injected_owner_and_filesystem_boundary_controls(self):
        original = bookkeeping_v2._read_stable
        for field, reason in (("st_uid", "USAGE_OWNER_GROUP_CHANGED"), ("st_dev", "USAGE_FILESYSTEM_BOUNDARY_CHANGED")):
            with self.subTest(field=field):
                def altered(path, selected=field):
                    raw, meta = original(path); meta = dict(meta); meta[selected] += 1; return raw, meta
                with patch.object(bookkeeping_v2, "_read_stable", altered):
                    self.assertReject(reason)

    def test_stable_capture_failure_rejects(self):
        original = bookkeeping_v2._read_stable
        def fail(path):
            if Path(path) == self.usage: raise RuntimeError("INJECTED_STRICT_CAPTURE_GAP")
            return original(path)
        with patch.object(bookkeeping_v2, "_read_stable", fail):
            self.assertReject("INJECTED_STRICT_CAPTURE_GAP")


class ObserverClassificationControls(unittest.TestCase):
    def test_only_exact_direct_child_namespace_is_scoped(self):
        root = Path("/fixture/skills")
        self.assertTrue(bookkeeping_v2.is_reserved_temp(root / ".usage_abc12_3z.tmp", root))
        for path in (root / "nested/.usage_abc12_3z.tmp", root / ".usage_bad.tmp",
                     root / "other.tmp", root.parent / ".usage_abc12_3z.tmp"):
            self.assertFalse(bookkeeping_v2.is_reserved_temp(path, root), path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
