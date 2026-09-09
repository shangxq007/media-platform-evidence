"""Fresh affected-closure qualification on disposable real files."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "executor"))

import bookkeeping_v3 as bk
import boundary
import capture
import observe
import executor_adapter
import candidate_binding
import policy_builder


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def usage_record(**changes):
    value = {
        "view_count": 1,
        "use_count": 2,
        "last_viewed_at": None,
        "last_used_at": "2026-09-08T00:00:00+00:00",
        "state": "active",
        "pinned": False,
        "generation": 7,
    }
    value.update(changes)
    return value


class Fixture(unittest.TestCase):
    def setUp(self):
        fixture_root = os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT")
        self.temp = tempfile.TemporaryDirectory(dir=fixture_root)
        self.addCleanup(self.temp.cleanup)
        self.skills = Path(self.temp.name) / "skills"
        self.skills.mkdir(mode=0o700)
        self.package = self.skills / "alpha"
        self.package.mkdir()
        (self.package / "SKILL.md").write_text("---\nname: alpha\n---\nfixture\n")
        (self.package / "support.txt").write_text("strict support\n")
        self.usage = self.skills / bk.USAGE_NAME
        dump(self.usage, {"alpha": usage_record(), "orphan": usage_record()})
        os.chmod(self.usage, 0o600)
        self.lock = self.skills / bk.LOCK_NAME
        self.lock.touch(mode=0o644)
        self.ledger = self.skills / bk.LEDGER_NAME
        self.ledger.write_bytes(b'{"id":"000000000000","legacy":true}\n')
        os.chmod(self.ledger, 0o600)
        self.policy = bk.create_policy(
            self.skills, owner_sha256="4" * 64, dependency_sha256="5" * 64,
            eligible_names=["alpha"], fixture=True)
        self.engine = boundary.Engine(
            self.policy,
            window_start=datetime(2026, 9, 8, tzinfo=timezone.utc),
            window_end=datetime(2026, 9, 10, tzinfo=timezone.utc),
        )

    def record(self, ident="111111111111", action="patch", **updates):
        manifest = deepcopy(self.policy["eligible_map"]["alpha"]["manifest"])
        value = {"id": ident, "ts": "2026-09-09T00:00:00.000000+00:00",
                 "actor": "agent", "action": action, "skill": "alpha",
                 "evidence": {}, "before": manifest, "after": deepcopy(manifest)}
        value.update(updates)
        return value

    def append(self, *records):
        with self.ledger.open("ab") as stream:
            for record in records:
                stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n")

    def decision(self, phase="GATE", events=(), **kwargs):
        return self.engine.check(phase, events=events, **kwargs)

    def assertReject(self, result, reason):
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any(reason in item for item in result["reasons"] + result["event_reasons"]), result)


class PositiveControls(Fixture):
    def test_unchanged_passes_all_eight_actual_boundary_adapters(self):
        for phase in ("BASELINE", "PREFLIGHT", "PRESTART", "COMMAND", "GATE", "FINAL", "COVERAGE", "SEAL"):
            with self.subTest(phase=phase):
                result = self.decision(phase)
                self.assertEqual(result["decision"], "PASS", result)
                self.assertEqual(result["OLD_STRICT_PRESERVATION_RESULT"], "PASS")

    def test_baseline_approved_usage_variation_keeps_old_strict_red(self):
        dump(self.usage, {"alpha": usage_record(view_count=2, use_count=3,
                                                last_viewed_at="2026-09-09T00:00:00+00:00"),
                          "orphan": usage_record()})
        result = self.decision("BASELINE")
        self.assertEqual(result["decision"], "PASS", result)
        self.assertEqual(result["OLD_STRICT_PRESERVATION_RESULT"], "OLD_STRICT_REJECT")
        self.assertEqual(result["APPROVED_BOOKKEEPING_SEMANTICS"], "PASS")

    def test_usage_v2_change_with_real_observer_passes(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            dump(self.usage, {"alpha": usage_record(view_count=4, use_count=5,
                                                    last_used_at="2026-09-09T01:00:00+00:00"),
                              "orphan": usage_record()})
            events, errors = watcher.boundary_events()
        result = self.decision(events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)
        self.assertTrue(result["usage"]["changed_json_pointers"])

    def test_usage_atomic_replacement_passes_v2_with_events(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            temp = self.skills / ".usage_abc12_3z.tmp"
            dump(temp, {"alpha": usage_record(view_count=2), "orphan": usage_record()})
            os.chmod(temp, 0o600)
            watcher.drain()
            os.replace(temp, self.usage)
            events, errors = watcher.boundary_events()
        result = self.decision(events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)
        self.assertEqual(result["usage"]["old_strict"], "OLD_STRICT_REJECT")

    def test_exact_empty_lock_close_write_real_event_passes(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            with self.lock.open("ab"):
                pass
            events, errors = watcher.boundary_events()
        result = self.decision(events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)
        self.assertIn("ACCEPTED_EXACT_EMPTY_LOCK_CLOSE_WRITE", {e["category"] for e in result["events"]})

    def test_single_ledger_append_real_events_passes(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            self.append(self.record())
            events, errors = watcher.boundary_events()
        result = self.decision(events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)
        self.assertEqual(result["ledger"]["appended_this_boundary"], 1)

    def test_multiple_and_previous_prefix_ledger_appends_pass(self):
        for index, identifiers in enumerate((("111111111111", "222222222222"), ("333333333333",))):
            with observe.BoundaryObserver(self.policy) as watcher:
                self.append(*(self.record(value, action="edit") for value in identifiers))
                events, errors = watcher.boundary_events()
            result = self.decision("COMMAND" if index == 0 else "FINAL", events=events, coverage_errors=errors)
            self.assertEqual(result["decision"], "PASS", result)
        self.assertEqual(self.engine.session["appended_records"], 3)

    def test_close_only_unchanged_ledger_passes(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            with self.ledger.open("ab"):
                pass
            events, errors = watcher.boundary_events()
        self.assertEqual(self.decision(events=events, coverage_errors=errors)["decision"], "PASS")

    def test_private_evidence_contains_same_raw_source_and_owner_modes(self):
        evidence = Path(self.temp.name) / "evidence"
        result = self.decision("SEAL", evidence_dir=evidence)
        self.assertEqual(result["decision"], "PASS")
        private = Path(result["evidence"]["private"])
        public = Path(result["evidence"]["public"])
        self.assertEqual(private.stat().st_mode & 0o777, 0o600)
        self.assertEqual(public.stat().st_mode & 0o777, 0o400)
        stored = json.loads(private.read_text())
        self.assertEqual(stored["capture_bundle"]["usage"]["capture_id"], result["usage"]["capture_id"])
        self.assertIn("raw_base64", stored["capture_bundle"]["ledger"])


class UsageNegativeControls(Fixture):
    def test_usage_record_membership_rejects(self):
        data = {"alpha": usage_record(), "orphan": usage_record(), "new": usage_record()}
        dump(self.usage, data)
        self.assertReject(self.decision("BASELINE"), "USAGE_RECORD_MEMBERSHIP_CHANGED")

    def test_usage_field_membership_rejects(self):
        data = {"alpha": usage_record(extra=True), "orphan": usage_record()}
        dump(self.usage, data)
        self.assertReject(self.decision("BASELINE"), "USAGE_FIELD_MEMBERSHIP_CHANGED")

    def test_usage_strict_value_rejects(self):
        dump(self.usage, {"alpha": usage_record(state="inactive"), "orphan": usage_record()})
        self.assertReject(self.decision("BASELINE"), "USAGE_STRICT_VALUE_CHANGED")

    def test_usage_bool_count_type_rejects(self):
        dump(self.usage, {"alpha": usage_record(use_count=True), "orphan": usage_record()})
        self.assertReject(self.decision("BASELINE"), "COUNT_TYPE_OR_RANGE")

    def test_usage_count_decrease_rejects(self):
        dump(self.usage, {"alpha": usage_record(use_count=1), "orphan": usage_record()})
        self.assertReject(self.decision("BASELINE"), "USAGE_COUNT_DECREASE")

    def test_usage_timestamp_backwards_rejects(self):
        dump(self.usage, {"alpha": usage_record(last_used_at="2026-09-07T00:00:00+00:00"),
                          "orphan": usage_record()})
        self.assertReject(self.decision("BASELINE"), "USAGE_TIMESTAMP_BACKWARDS")

    def test_ineligible_orphan_mutable_field_remains_strict(self):
        dump(self.usage, {"alpha": usage_record(), "orphan": usage_record(view_count=9)})
        self.assertReject(self.decision("BASELINE"), "USAGE_STRICT_VALUE_CHANGED")

    def test_usage_duplicate_key_rejects(self):
        self.usage.write_bytes(b'{"alpha":{},"alpha":{}}')
        self.assertReject(self.decision("BASELINE"), "DUPLICATE_JSON_KEY")

    def test_usage_invalid_utf8_rejects(self):
        self.usage.write_bytes(b"\xff")
        self.assertReject(self.decision("BASELINE"), "INVALID_UTF8")

    def test_usage_variation_without_covered_event_rejects_after_baseline(self):
        dump(self.usage, {"alpha": usage_record(view_count=2), "orphan": usage_record()})
        self.assertReject(self.decision("GATE"), "USAGE_VARIATION_WITHOUT_COVERED_EVENT")


class LockNegativeControls(Fixture):
    def test_nonempty_lock_rejects(self):
        self.lock.write_text("x")
        self.assertReject(self.decision(), "LOCK_NOT_EMPTY")

    def test_nonempty_lock_with_close_event_cannot_resolve_pending(self):
        self.lock.write_text("x")
        event = {"path": str(self.lock), "mask": observe.IN_CLOSE_WRITE, "cookie": 0}
        result = self.decision(events=[event])
        self.assertReject(result, "LOCK_PENDING_ENDPOINT_UNDECIDABLE")
        self.assertIn("REJECT_LOCK_PENDING_UNRESOLVED", {item["category"] for item in result["events"]})

    def test_lock_mode_change_rejects(self):
        os.chmod(self.lock, 0o600)
        self.assertReject(self.decision(), "LOCK_NINE_FIELDS_OR_CONTENT_CHANGED")

    def test_lock_replacement_rejects(self):
        replacement = self.skills / "replacement"
        replacement.touch()
        os.replace(replacement, self.lock)
        self.assertReject(self.decision(), "LOCK_NINE_FIELDS_OR_CONTENT_CHANGED")

    def test_lock_modify_event_even_if_restored_rejects(self):
        event = {"path": str(self.lock), "mask": observe.IN_MODIFY, "cookie": 0}
        self.assertReject(self.decision(events=[event]), "REJECT_LOCK_EVENT")

    def test_lock_combined_or_unknown_event_rejects(self):
        event = {"path": str(self.lock), "mask": observe.IN_CLOSE_WRITE | observe.IN_MODIFY, "cookie": 0}
        self.assertReject(self.decision(events=[event]), "REJECT_LOCK_EVENT")

    def test_lock_nonzero_cookie_rejects(self):
        event = {"path": str(self.lock), "mask": observe.IN_CLOSE_WRITE, "cookie": 1}
        self.assertReject(self.decision(events=[event]), "REJECT_LOCK_EVENT")


class LedgerNegativeControls(Fixture):
    def append_raw(self, raw):
        with self.ledger.open("ab") as stream:
            stream.write(raw)

    def ledger_events(self):
        return [{"path": str(self.ledger), "mask": observe.IN_MODIFY, "cookie": 0},
                {"path": str(self.ledger), "mask": observe.IN_CLOSE_WRITE, "cookie": 0}]

    def test_original_prefix_change_rejects(self):
        raw = self.ledger.read_bytes()
        self.ledger.write_bytes(raw.replace(b"true", b"null"))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_ORIGINAL_PREFIX_CHANGED")

    def test_previous_prefix_change_rejects(self):
        self.append(self.record())
        self.assertEqual(self.decision(events=self.ledger_events())["decision"], "PASS")
        raw = self.ledger.read_bytes()
        self.ledger.write_bytes(raw.replace(b'"action":"patch"', b'"action":"edit" ', 1))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_PREVIOUS_PREFIX_CHANGED")

    def test_shrink_rejects(self):
        self.ledger.write_bytes(b"")
        self.assertReject(self.decision(), "LEDGER_SHRINK")

    def test_replacement_inode_rejects(self):
        other = self.skills / "ledger-new"
        other.write_bytes(self.ledger.read_bytes())
        os.chmod(other, 0o600)
        os.replace(other, self.ledger)
        self.assertReject(self.decision(), "LEDGER_STRICT_METADATA_CHANGED st_ino")

    def test_unknown_record_key_rejects(self):
        self.append(self.record(extra=True))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_RECORD_SCHEMA_KEYS")

    def test_duplicate_json_key_rejects(self):
        row = self.record()
        raw = json.dumps(row, separators=(",", ":"))[:-1] + ',"action":"edit"}\n'
        self.append_raw(raw.encode())
        self.assertReject(self.decision(events=self.ledger_events()), "DUPLICATE_JSON_KEY")

    def test_duplicate_id_rejects(self):
        self.append(self.record("000000000000"))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_DUPLICATE_ID")

    def test_invalid_action_rejects(self):
        self.append(self.record(action="rollback"))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_ACTION_SCHEMA")

    def test_nonempty_evidence_rejects(self):
        self.append(self.record(evidence={"session_id": "x"}))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_EVIDENCE_NOT_EMPTY_OBJECT")

    def test_empty_manifest_rejects(self):
        self.append(self.record(before=[], after=[]))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_MANIFEST_SIZE")

    def test_manifest_difference_rejects(self):
        self.append(self.record(after=[]))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_MANIFESTS_DIFFER")

    def test_cross_package_path_rejects(self):
        row = self.record()
        row["before"][0]["path"] = "/tmp/outside"
        row["after"] = deepcopy(row["before"])
        self.append(row)
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_MANIFEST_PATH_SCOPE")

    def test_manifest_not_complete_rejects(self):
        row = self.record()
        row["before"] = row["before"][:1]
        row["after"] = deepcopy(row["before"])
        self.append(row)
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_MANIFEST_NOT_COMPLETE")

    def test_half_line_rejects_at_boundary(self):
        self.append_raw(json.dumps(self.record()).encode())
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_PARTIAL_LINE")

    def test_invalid_utf8_rejects(self):
        self.append_raw(b"\xff\n")
        self.assertReject(self.decision(events=self.ledger_events()), "INVALID_UTF8")

    def test_timestamp_outside_window_rejects(self):
        self.append(self.record(ts="2027-01-01T00:00:00.000000+00:00"))
        self.assertReject(self.decision(events=self.ledger_events()), "LEDGER_TIMESTAMP_OUTSIDE_BOUND_WINDOW")

    def test_growth_without_events_rejects(self):
        self.append(self.record())
        self.assertReject(self.decision(events=[]), "LEDGER_GROWTH_WITHOUT_MODIFY_EVENT")

    def test_modify_without_growth_rejects(self):
        self.assertReject(self.decision(events=[self.ledger_events()[0]]), "LEDGER_MODIFY_WITHOUT_GROWTH")

    def test_combined_mask_rejects(self):
        event = {"path": str(self.ledger), "mask": observe.IN_MODIFY | observe.IN_CLOSE_WRITE, "cookie": 0}
        self.assertReject(self.decision(events=[event]), "REJECT_LEDGER_EVENT")

    def test_nonzero_cookie_rejects(self):
        event = {"path": str(self.ledger), "mask": observe.IN_CLOSE_WRITE, "cookie": 4}
        self.assertReject(self.decision(events=[event]), "REJECT_LEDGER_EVENT")

    def test_appended_record_limit_actual_exact_and_over(self):
        records = [self.record(f"{index:012x}") for index in range(1, 129)]
        self.append(*records)
        self.assertEqual(self.decision(events=self.ledger_events())["decision"], "PASS")
        self.append(self.record("000000000081"))
        self.assertReject(self.decision(events=self.ledger_events()), "APPENDED_RECORDS_MAX_EXCEEDED")


class IntegrityAndFailureControls(Fixture):
    def test_strict_body_write_restore_event_rejects(self):
        skill = self.package / "SKILL.md"
        original = skill.read_bytes()
        with observe.BoundaryObserver(self.policy) as watcher:
            skill.write_text("changed")
            skill.write_bytes(original)
            events, errors = watcher.boundary_events()
        self.assertReject(self.decision(events=events, coverage_errors=errors), "REJECT_STRICT_PACKAGE_EVENT")

    def test_strict_body_changed_without_event_rejects_inventory(self):
        (self.package / "support.txt").write_text("changed")
        self.assertReject(self.decision(), "STRICT_PACKAGE_INVENTORY_CHANGED")

    def test_capture_binding_mismatch_rejects(self):
        bundle = bk.capture_bundle(self.skills, self.policy["eligible_map"])
        bundle["capture_binding"]["usage"] = "0" * 64
        result = self.decision(bundle=bundle)
        self.assertReject(result, "CAPTURE_BINDING_MISMATCH")
        self.assertEqual(result["CAPTURE_BINDING_COHERENT"], "NO")

    def test_missing_capture_rejects(self):
        self.usage.unlink()
        self.assertReject(self.decision(), "STABLE_CAPTURE_FAILED")

    def test_injected_unstable_capture_rejects_without_retry_expansion(self):
        real = bk.capture_file
        def fail(path, **kwargs):
            if Path(path) == self.usage:
                raise capture.CaptureError("CAPTURE_UNSTABLE")
            return real(path, **kwargs)
        with patch.object(bk, "capture_file", side_effect=fail):
            self.assertReject(self.decision(), "CAPTURE_UNSTABLE")

    def test_watch_loss_rejects(self):
        self.assertReject(self.decision(coverage_errors=["WATCH_LOSS"]), "WATCH_LOSS")

    def test_queue_overflow_rejects(self):
        self.assertReject(self.decision(coverage_errors=["QUEUE_OVERFLOW"]), "QUEUE_OVERFLOW")

    def test_coverage_incomplete_rejects(self):
        result = self.decision(coverage_complete=False)
        self.assertEqual(result["decision"], "REJECT")
        self.assertEqual(result["COVERAGE_COMPLETE"], "NO")

    def test_strict_integrity_flag_rejects(self):
        result = self.decision(strict_input_integrity=False)
        self.assertEqual(result["STRICT_INPUT_INTEGRITY"], "REJECT")
        self.assertEqual(result["decision"], "REJECT")

    def test_evidence_write_failure_rejects(self):
        obstruction = Path(self.temp.name) / "obstruction"
        obstruction.write_text("file")
        with self.assertRaisesRegex(boundary.BoundaryReject, "EVIDENCE_WRITE_FAILED"):
            self.decision(evidence_dir=obstruction)

    def test_unknown_phase_rejects(self):
        with self.assertRaisesRegex(boundary.BoundaryReject, "UNKNOWN_BOUNDARY_PHASE"):
            self.decision("AFTER_THE_FACT")

    def test_stale_policy_rejects_before_engine(self):
        stale = deepcopy(self.policy)
        stale["contract_version"] = "OLD"
        with self.assertRaisesRegex(bk.PolicyError, "STALE_OR_UNKNOWN_POLICY"):
            boundary.Engine(stale)

    def test_failed_namespace_cannot_resurrect_or_reach_preflight(self):
        run = Path(self.temp.name) / "run"
        adapter = executor_adapter.RunAdapter(
            run, self.policy,
            window_start=datetime(2026, 9, 8, tzinfo=timezone.utc),
            window_end=datetime(2026, 9, 10, tzinfo=timezone.utc))
        bad = {"path": str(self.lock), "mask": observe.IN_MODIFY, "cookie": 0}
        with self.assertRaisesRegex(boundary.BoundaryReject, "BOUNDARY_REJECT"):
            adapter.baseline(events=[bad])
        with self.assertRaisesRegex(executor_adapter.NamespaceConsumed, "CANNOT_REACH_BOUNDARY"):
            adapter.preflight()
        replacement = executor_adapter.RunAdapter(run, self.policy)
        with self.assertRaisesRegex(executor_adapter.NamespaceConsumed, "CANNOT_RESURRECT"):
            replacement.consume_for_baseline()


class BindingAndLimitControls(Fixture):
    def valid_binding(self):
        return {"schema": "ep19-approved-candidate-binding-v3",
                "candidate_sha": "a29864343ed4f630b052c20d86c23b240f13cfd0",
                "ledger_use": "OBSERVATION_INTEGRITY_ONLY",
                "ledger_consumers": [], "unbound_dynamic_readers": []}

    def test_valid_dependency_binding_passes(self):
        self.assertTrue(boundary.validate_runtime_binding(self.valid_binding(), {
            "candidate_sha": "a29864343ed4f630b052c20d86c23b240f13cfd0"}))

    def test_nested_prebound_package_map_is_supported_without_discovery(self):
        nested = self.skills / "category" / "nested"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("---\nname: nested\n---\n")
        bound = bk.bind_eligible_packages(self.skills, {"nested": nested})
        self.assertEqual(bound["nested"]["package"], str(nested))
        self.assertEqual(len(bound), 1)

    def test_parent_applicability_adapter_is_finite_explicit_map(self):
        value = {"eligible_packages": [{"skill": "alpha", "package_root": str(self.package),
                                         "eligible": True, "errors": []}]}
        self.assertEqual(policy_builder.eligible_from_applicability(value), {"alpha": str(self.package)})
        value["eligible_packages"].append(deepcopy(value["eligible_packages"][0]))
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE"):
            policy_builder.eligible_from_applicability(value)

    def test_stale_binding_rejects(self):
        value = self.valid_binding()
        value["candidate_sha"] = "0" * 40
        with self.assertRaisesRegex(boundary.BoundaryReject, "BINDING_MISMATCH"):
            boundary.validate_runtime_binding(value, {"candidate_sha": "a29864343ed4f630b052c20d86c23b240f13cfd0"})

    def test_unbound_dynamic_reader_rejects(self):
        value = self.valid_binding()
        value["unbound_dynamic_readers"] = ["dynamic"]
        with self.assertRaisesRegex(boundary.BoundaryReject, "LEDGER_CONSUMER_DEPENDENCY_REJECT"):
            boundary.validate_runtime_binding(value, {})

    def test_rollback_consumer_rejects(self):
        value = self.valid_binding()
        value["ledger_consumers"] = ["rollback"]
        with self.assertRaisesRegex(boundary.BoundaryReject, "LEDGER_CONSUMER_DEPENDENCY_REJECT"):
            boundary.validate_runtime_binding(value, {})

    def test_all_inclusive_resource_limits_exact_and_over(self):
        for name, limit in bk.LIMITS.items():
            with self.subTest(name=name, edge="exact"):
                self.assertTrue(bk.enforce_limit(name, limit))
            with self.subTest(name=name, edge="over"):
                with self.assertRaises(bk.PolicyError):
                    bk.enforce_limit(name, limit + 1)

    def test_stable_capture_attempt_limit_exact_and_over(self):
        self.assertEqual(capture.capture_file(self.usage, attempts=3)["attempt"], 1)
        with self.assertRaisesRegex(capture.CaptureError, "ATTEMPT_LIMIT_INVALID"):
            capture.capture_file(self.usage, attempts=4)

    def test_stable_capture_time_limit_exact_and_over(self):
        self.assertEqual(capture.capture_file(self.usage, max_seconds=5)["attempt"], 1)
        with self.assertRaisesRegex(capture.CaptureError, "TIME_LIMIT_INVALID"):
            capture.capture_file(self.usage, max_seconds=5.001)

    def test_pending_event_limit_exact_and_over(self):
        event = {"path": str(self.lock), "mask": observe.IN_CLOSE_WRITE, "cookie": 0}
        exact = observe.reduce_events(self.policy, [event] * 4096, ledger_growth=False)
        self.assertEqual(exact["result"], "PASS")
        over = observe.reduce_events(self.policy, [event] * 4097, ledger_growth=False)
        self.assertEqual(over["result"], "REJECT")
        self.assertIn("PENDING_EVENT_LIMIT_EXCEEDED", over["reasons"])

    def test_actual_candidate_binding_builder_checks_fixed_identity_and_patch(self):
        tooling_root = ROOT
        sources = {**candidate_binding.source_manifest(tooling_root / "executor"),
                   **candidate_binding.source_manifest(tooling_root / "qualification")}
        qualification = Path(self.temp.name) / "qualification.json"
        dump(qualification, {"schema": "ep19-approved-bookkeeping-qualification-v3",
                             "result": "PASS", "source_binding": sources})
        dependency = Path(self.temp.name) / "dependency.json"
        dump(dependency, {"schema": "ep19-writer-ledger-dependency-binding-v1",
                          "result": "PASS", "ledger_role": "OBSERVATION_INTEGRITY_ONLY",
                          "ledger_consumers": [], "unbound_dynamic_readers": []})
        owner = ROOT.parents[1] / "OWNER_AUTHORIZATION.verbatim.txt"
        matrix = ROOT / "candidate-inputs-v3" / "GATE_EXECUTION_MATRIX.json"
        checkout = ROOT.parents[2] / "checkout"
        value = candidate_binding.build(checkout, owner, dependency, qualification, matrix, tooling_root)
        self.assertEqual(value["candidate_sha"], candidate_binding.CANDIDATE)
        self.assertEqual(value["candidate_tree"], candidate_binding.TREE)
        self.assertEqual(value["product_patch_sha256"], candidate_binding.PATCH_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
