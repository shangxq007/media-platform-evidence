import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "canonical_publication_control.py"
SPEC = importlib.util.spec_from_file_location("canonical_publication_control", SCRIPT)
cpc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cpc)

AUDIT_ROOT = Path("/REVIEW_ONLY/home/Documents/workspace/audit-runs/MEDIA_PLATFORM_CANONICAL_INTEGRATION_CONTROL_PLANE_UPGRADE_V1")
INVENTORY = AUDIT_ROOT / "inventory" / "in-flight-task-inventory.json"


def slot_available(path):
    cpc.atomic_write_json(path, {
        "RESOURCE_NAME": cpc.SLOT_RESOURCE,
        "PROTOCOL_VERSION": cpc.PROTOCOL_VERSION,
        "MAX_HOLDERS": 1,
        "STATUS": "AVAILABLE",
        "HOLDER": None,
        "QUEUE_ENTRY_ID": None,
        "FRESH_CANONICAL_MAIN": None,
        "ACQUIRED_AT": None,
        "RELEASED_AT": None,
        "RELEASE_REASON": None,
    })


def queue_entry(state="ENGINEERING", dependencies=None):
    return {
        "QUEUE_ENTRY_ID": "entry-1",
        "LANE_ID": "lane-1",
        "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "candidate-1",
        "CANDIDATE_TREE": "candidate-tree-1",
        "CURRENT_STATE": state,
        "DEPENDENCIES": [] if dependencies is None else dependencies,
        "READY_TIMESTAMP": None,
        "PUBLICATION_PRIORITY": 1,
        "SLOT_HOLDER": None,
        "CANONICAL_PARENT_1": None,
        "INTEGRATION_SHA": None,
        "INTEGRATION_TREE": None,
        "INDEPENDENT_REVIEW_STATUS": "NOT_STARTED",
        "PUBLICATION_STATUS": "NOT_AUTHORIZED",
        "FAILURE_REASON": None,
    }


def acquirable_entry(entry_id="entry-1"):
    item = queue_entry(state="QUEUED")
    item["QUEUE_ENTRY_ID"] = entry_id
    return item


def evidence(kind="CANDIDATE_EVIDENCE", gate="BACKEND_CI", sha="candidate-1", tree="candidate-tree-1"):
    return {
        "EVIDENCE_CLASS": kind,
        "GATE_NAME": gate,
        "SUBJECT_SHA": sha,
        "SUBJECT_TREE": tree,
        "RESULT": "PASS",
        "TIMESTAMP": "2026-08-30T00:00:00Z",
        "PROTOCOL_VERSION": cpc.PROTOCOL_VERSION,
        "EVIDENCE_SOURCE": "receipt.json",
    }


class ClassifierAndMatrixTests(unittest.TestCase):
    def test_exact_classifier_fixtures_cover_all_twelve_categories(self):
        classifier = cpc.DeltaClassifier()
        fixtures = classifier.definition["fixtures"]
        self.assertEqual(12, len(classifier.categories))
        for category in classifier.categories:
            with self.subTest(category=category):
                self.assertIn(category, classifier.classify_path(fixtures[category]))

    def test_empty_invalid_and_unclassified_are_unknown(self):
        classifier = cpc.DeltaClassifier()
        for path in ("", "/absolute/path", "../escape", "unmapped/file.xyzzy"):
            with self.subTest(path=path):
                self.assertEqual(["UNKNOWN"], classifier.classify_path(path))
        self.assertEqual({"": ["UNKNOWN"]}, classifier.classify_paths([]))

    def test_multi_category_fixtures(self):
        classifier = cpc.DeltaClassifier()
        for path, expected in classifier.definition["multi_category_fixtures"].items():
            with self.subTest(path=path):
                self.assertEqual(expected, classifier.classify_path(path))

    def test_matrix_is_exactly_twelve_by_seventeen(self):
        result = cpc.GateImpactMatrix().validate()
        self.assertEqual("YES", result["GATE_IMPACT_MATRIX_COMPLETE"])
        self.assertEqual(12, result["CATEGORY_COUNT"])
        self.assertEqual(17, result["GATE_COUNT"])
        self.assertEqual(204, result["CELL_COUNT"])

    def test_unknown_is_never_harmless(self):
        matrix = cpc.GateImpactMatrix()
        matrix.validate()
        for gate in matrix.data["gates"][3:]:
            self.assertEqual("UNKNOWN_RERUN_REQUIRED", matrix.impact("UNKNOWN", gate))


class FingerprintTests(unittest.TestCase):
    def populate(self, root):
        files = {
            "settings.gradle.kts": "rootProject.name='pilot'\n",
            "backend/build.gradle.kts": "plugins {}\n",
            "backend/src/main/h1/One.java": "class One {}\n",
            "backend/src/main/h2/Two.java": "class Two {}\n",
            "backend/src/main/service/Service.java": "class Service {}\n",
            "backend/src/test/ConcurrencyTest.java": "class ConcurrencyTest {}\n",
            "backend/src/test/BoundaryTest.java": "class BoundaryTest {}\n",
            "backend/src/main/resources/schema.sql": "select 1;\n",
            "formal/spec.tla": "---- MODULE spec ----\n",
            "formal/tests/model.txt": "pass\n",
            "formal/models/state.txt": "state\n",
            "formal/Makefile": "check:\n\ttrue\n",
            "frontend/package.json": "{}\n",
            "frontend/package-lock.json": "{}\n",
            "frontend/src/App.tsx": "export const App=()=>null;\n",
            "frontend/test/App.test.tsx": "test('x',()=>{});\n",
            "frontend/public/index.html": "<html></html>\n",
            ".github/workflows/frontend-ci.yml": "name: frontend\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def test_all_five_fingerprints_are_deterministic_and_move_on_input_change(self):
        mutation = {
            "H7_POSTGRESQL_CONCURRENCY": "backend/src/test/ConcurrencyTest.java",
            "BACKEND_FULL_SERIAL": "backend/src/main/service/Service.java",
            "H2_H1_BOUNDARY": "backend/src/main/h1/One.java",
            "FORMAL_VERIFICATION": "formal/spec.tla",
            "FRONTEND_CI": "frontend/src/App.tsx",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.populate(root)
            for gate, changed_path in mutation.items():
                with self.subTest(gate=gate):
                    before = cpc.compute_gate_fingerprint(gate, root)
                    same = cpc.compute_gate_fingerprint(gate, root)
                    self.assertEqual(before["INPUT_FINGERPRINT"], same["INPUT_FINGERPRINT"])
                    path = root / changed_path
                    original = path.read_text(encoding="utf-8")
                    path.write_text(original + "changed\n", encoding="utf-8")
                    after = cpc.compute_gate_fingerprint(gate, root)
                    self.assertNotEqual(before["INPUT_FINGERPRINT"], after["INPUT_FINGERPRINT"])
                    path.write_text(original, encoding="utf-8")

    def test_missing_required_fingerprint_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(cpc.ControlError):
                cpc.compute_gate_fingerprint("FRONTEND_CI", temporary)


class EvidenceTests(unittest.TestCase):
    def test_unclassified_evidence_is_rejected(self):
        bad = evidence()
        del bad["EVIDENCE_CLASS"]
        with self.assertRaises(cpc.ControlError):
            cpc.validate_evidence(bad)
        bad["EVIDENCE_CLASS"] = "OTHER"
        with self.assertRaises(cpc.ControlError):
            cpc.validate_evidence(bad)

    def test_candidate_reuse_only_for_unchanged_sha_and_tree(self):
        item = evidence()
        allowed = cpc.evidence_reuse_receipt(item, current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1")
        self.assertEqual("ALLOWED", allowed["REUSE_DECISION"])
        self.assertEqual("FULL", allowed["REUSE_LEVEL"])
        for sha, tree in (("changed", "candidate-tree-1"), ("candidate-1", "changed")):
            denied = cpc.evidence_reuse_receipt(item, current_candidate_sha=sha, current_candidate_tree=tree)
            self.assertEqual("DENIED", denied["REUSE_DECISION"])

    def test_main_advance_preserves_candidate_evidence_but_stales_merge(self):
        candidate = cpc.evidence_reuse_receipt(evidence(), current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1")
        merge = cpc.evidence_reuse_receipt(evidence("INTEGRATION_EVIDENCE", sha="merge-1", tree="merge-tree"), current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1", stale_merge=True)
        self.assertEqual("ALLOWED", candidate["REUSE_DECISION"])
        self.assertEqual("DENIED", merge["REUSE_DECISION"])
        self.assertIn("never reusable", merge["REUSE_REASON"])

    def test_integration_reuse_requires_justification(self):
        item = evidence("INTEGRATION_EVIDENCE", gate="BACKEND_CI", sha="merge-1", tree="merge-tree")
        denied = cpc.evidence_reuse_receipt(item, current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1")
        allowed = cpc.evidence_reuse_receipt(item, current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1", old_fingerprint="same", new_fingerprint="same")
        self.assertEqual("DENIED", denied["REUSE_DECISION"])
        self.assertEqual("ALLOWED", allowed["REUSE_DECISION"])

    def test_always_fresh_gate_denies_even_equal_fingerprint(self):
        item = evidence("INTEGRATION_EVIDENCE", gate="MERGE_OBJECT_IDENTITY", sha="merge-1", tree="merge-tree")
        receipt = cpc.evidence_reuse_receipt(item, current_candidate_sha="candidate-1", current_candidate_tree="candidate-tree-1", old_fingerprint="same", new_fingerprint="same")
        self.assertEqual("DENIED", receipt["REUSE_DECISION"])


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.queue_path = self.root / "queue.json"

    def tearDown(self):
        self.temporary.cleanup()

    def write_entry(self, entry):
        cpc.atomic_write_json(self.queue_path, {"SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1", "PROTOCOL_VERSION": cpc.PROTOCOL_VERSION, "ENTRIES": [entry]})
        cpc.atomic_write_json(self.root / "transition-ledger.json", {"SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1", "EVENTS": []})
        slot_available(self.root / "slot.json")
        return cpc.QueueControl(self.queue_path)

    def test_strict_positive_transition_path(self):
        queue = self.write_entry(queue_entry())
        queue.transition("entry-1", "PREVALIDATING", actor="test")
        queue.transition("entry-1", "READY_FOR_CANONICAL_QUEUE", actor="test")
        queue.transition("entry-1", "QUEUED", actor="test")
        self.assertEqual("QUEUED", queue.get("entry-1")["CURRENT_STATE"])

    def test_illegal_skip_is_rejected(self):
        queue = self.write_entry(queue_entry(state="PREVALIDATING"))
        with self.assertRaises(cpc.ControlError):
            queue.transition("entry-1", "SLOT_ACQUIRED", actor="test")

    def test_unresolved_dependency_prohibits_queueing(self):
        queue = self.write_entry(queue_entry(state="READY_FOR_CANONICAL_QUEUE", dependencies=[{"NAME": "proof", "STATUS": "UNRESOLVED"}]))
        with self.assertRaises(cpc.ControlError):
            queue.transition("entry-1", "QUEUED", actor="test")

    def test_candidate_mutation_after_prevalidation_fails_closed(self):
        queue = self.write_entry(queue_entry(state="PREVALIDATING"))
        with self.assertRaises(cpc.ControlError):
            queue.transition("entry-1", "READY_FOR_CANONICAL_QUEUE", actor="test", candidate_sha="different")


class SlotAndPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        slot_available(self.root / "slot.json")
        cpc.atomic_write_json(self.root / "queue.json", {"SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1", "PROTOCOL_VERSION": cpc.PROTOCOL_VERSION, "ENTRIES": [acquirable_entry()]})
        cpc.atomic_write_json(self.root / "transition-ledger.json", {"SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1", "EVENTS": []})
        self.slot = cpc.SlotControl(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def approved_entry():
        item = queue_entry(state="APPROVED_FOR_PUBLICATION")
        item.update({"CANONICAL_PARENT_1": "main-1", "INTEGRATION_SHA": "merge-1", "INTEGRATION_TREE": "merge-tree-1", "INDEPENDENT_REVIEW_STATUS": "APPROVED"})
        return item

    def acquire_and_freeze(self):
        self.slot.acquire("owner-1", acquirable_entry(), "main-1")
        queue = cpc.QueueControl(self.root / "queue.json")
        queue.transition("entry-1", "INTEGRATING", actor="owner-1")
        queue.transition("entry-1", "VALIDATING_INTEGRATION", actor="owner-1")
        validating = queue_entry(state="VALIDATING_INTEGRATION")
        gates = {gate: "PASS" for gate in json.loads((cpc.REFERENCE_DIR / "protocol-v1.json").read_text(encoding="utf-8"))["always_fresh_integration_gates"]}
        self.slot.freeze_integration(owner="owner-1", entry=validating, integration_sha="merge-1", integration_tree="merge-tree-1", parent_1="main-1", parent_2="candidate-1", always_fresh_gate_results=gates)
        queue.transition("entry-1", "INDEPENDENT_REVIEW", actor="owner-1")
        review_path = self.root / "independent-review.json"
        cpc.atomic_write_json(review_path, {
            "schema": "canonical-publication-independent-review-v1", "decision": "APPROVED",
            "reviewer_role": "INDEPENDENT_PUBLICATION_REVIEWER", "reviewer_actor": "reviewer-1",
            "candidate": "candidate-1", "tree": "candidate-tree-1",
            "integration_sha": "merge-1", "integration_tree": "merge-tree-1",
        })
        queue.record_independent_review("entry-1", evidence={"PATH": str(review_path), "SHA256": cpc.file_digest(review_path)}, actor="reviewer-1", timestamp="2026-09-10T00:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))

    def test_exclusivity_owner_and_release(self):
        self.slot.acquire("owner-1", acquirable_entry(), "main-1")
        with self.assertRaises(cpc.ControlError):
            self.slot.acquire("owner-2", acquirable_entry("entry-2"), "main-1")
        with self.assertRaises(cpc.ControlError):
            self.slot.release("owner-2", outcome="EXPLICIT_FAIL_CLOSED_RELEASE", queue_state="INTEGRATING")
        released = self.slot.release("owner-1", outcome="EXPLICIT_FAIL_CLOSED_RELEASE", queue_state="INTEGRATING")
        self.assertEqual("AVAILABLE", released["STATUS"])

    def test_unresolved_or_nonqueued_entry_cannot_acquire_slot(self):
        unresolved = acquirable_entry()
        unresolved["DEPENDENCIES"] = [{"NAME": "proof", "STATUS": "UNRESOLVED"}]
        with self.assertRaises(cpc.ControlError):
            self.slot.acquire("owner-1", unresolved, "main-1")
        not_queued = acquirable_entry()
        not_queued["CURRENT_STATE"] = "PREVALIDATING"
        with self.assertRaises(cpc.ControlError):
            self.slot.acquire("owner-1", not_queued, "main-1")

    def test_publication_requires_slot_and_holder(self):
        item = self.approved_entry()
        with self.assertRaises(cpc.ControlError):
            self.slot.authorize_publication(owner="owner-1", entry=item, current_observed_main="main-1", exact_parent_1="main-1", exact_parent_2="candidate-1")
        self.slot.acquire("owner-1", acquirable_entry(), "main-1")
        with self.assertRaises(cpc.ControlError):
            self.slot.authorize_publication(owner="owner-2", entry=item, current_observed_main="main-1", exact_parent_1="main-1", exact_parent_2="candidate-1")

    def test_frozen_review_retains_slot(self):
        self.acquire_and_freeze()
        for state in ("FROZEN_FOR_REVIEW", "INDEPENDENT_REVIEW", "APPROVED_FOR_PUBLICATION"):
            self.slot.assert_retained_for_review("owner-1", "entry-1", state)
        with self.assertRaises(cpc.ControlError):
            self.slot.release("owner-1", outcome="ROUTINE_RELEASE", queue_state="INDEPENDENT_REVIEW")
        self.assertEqual("HELD", self.slot.load()["STATUS"])

    def test_exact_normal_authorization_receipt(self):
        self.acquire_and_freeze()
        receipt = self.slot.authorize_publication(owner="owner-1", entry=self.approved_entry(), current_observed_main="main-1", exact_parent_1="main-1", exact_parent_2="candidate-1")
        self.assertEqual("EXACT_NORMAL_PUBLICATION_ONLY", receipt["AUTHORIZATION"])
        self.assertFalse(receipt["GIT_PUBLICATION_PERFORMED"])
        self.assertEqual("main-1", receipt["EXACT_PARENT_1"])
        self.assertEqual("candidate-1", receipt["EXACT_PARENT_2"])

    def test_parent_order_main_race_force_and_rewrite_rejected(self):
        self.acquire_and_freeze()
        item = self.approved_entry()
        cases = (
            {"current_observed_main": "main-2", "exact_parent_1": "main-2", "exact_parent_2": "candidate-1"},
            {"current_observed_main": "main-1", "exact_parent_1": "main-1", "exact_parent_2": "other"},
            {"current_observed_main": "main-1", "exact_parent_1": "main-1", "exact_parent_2": "candidate-1", "force_push": True},
            {"current_observed_main": "main-1", "exact_parent_1": "main-1", "exact_parent_2": "candidate-1", "history_rewrite": True},
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaises(cpc.ControlError):
                    self.slot.authorize_publication(owner="owner-1", entry=item, **arguments)

    def test_freeze_requires_exact_parents_and_complete_always_fresh_gates(self):
        self.slot.acquire("owner-1", acquirable_entry(), "main-1")
        validating = queue_entry(state="VALIDATING_INTEGRATION")
        with self.assertRaises(cpc.ControlError):
            self.slot.freeze_integration(owner="owner-1", entry=validating, integration_sha="merge-1", integration_tree="tree", parent_1="main-2", parent_2="candidate-1", always_fresh_gate_results={})
        with self.assertRaises(cpc.ControlError):
            self.slot.freeze_integration(owner="owner-1", entry=validating, integration_sha="merge-1", integration_tree="tree", parent_1="main-1", parent_2="candidate-1", always_fresh_gate_results={})

    def test_candidate_and_post_publication_identity_readbacks(self):
        self.acquire_and_freeze()
        item = self.approved_entry()
        candidate = self.slot.identity_readback(owner="owner-1", entry=item, gate_name="REMOTE_CANDIDATE_READBACK", observed_sha="merge-1")
        main = self.slot.identity_readback(owner="owner-1", entry=item, gate_name="POST_PUBLICATION_MAIN_READBACK", observed_sha="merge-1")
        self.assertEqual("PASS", candidate["RESULT"])
        self.assertEqual("PASS", main["RESULT"])
        self.assertFalse(main["GIT_OPERATION_PERFORMED"])
        with self.assertRaises(cpc.ControlError):
            self.slot.identity_readback(owner="owner-1", entry=item, gate_name="POST_PUBLICATION_MAIN_READBACK", observed_sha="other")


class LockAndStateTests(unittest.TestCase):
    def test_dual_lock_order_and_immediate_registry_release(self):
        guard = cpc.LockOrderGuard()
        with self.assertRaises(cpc.ControlError):
            guard.acquire_worktree_registry_for_bounded_mutation()
        guard.acquire_publication_slot()
        guard.acquire_worktree_registry_for_bounded_mutation()
        with self.assertRaises(cpc.ControlError):
            guard.enter_review()
        guard.release_worktree_registry()
        guard.enter_review()
        self.assertTrue(guard.publication_slot)

    def test_stable_state_readback_is_two_identical_reads_and_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            cpc.atomic_write_json(path, {"stable": True})
            receipt = cpc.stable_state_readback(path)
            self.assertTrue(receipt["BYTE_IDENTICAL_READS"])
            self.assertEqual(receipt["SHA256_FIRST"], receipt["SHA256_SECOND"])
            self.assertEqual(cpc.file_digest(path), receipt["SHA256_FIRST"])

    def test_inventory_import_counts_and_forward_cutover(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = cpc.initialize_state(root, INVENTORY)
            inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
            ledger = result["ledger"]
            self.assertEqual(21, len(ledger["EVENTS"]))
            self.assertEqual(0, inventory["unknown_phase_count"])
            self.assertEqual(inventory["transition_counts"], ledger["TRANSITION_COUNTS"])
            self.assertEqual(0, ledger["ACTIVE_TASK_RESTART_COUNT"])
            self.assertEqual(0, ledger["ACTIVE_CANDIDATE_REBUILD_COUNT"])

    def test_initialized_queue_is_one_h7_prevalidating_and_slot_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = cpc.initialize_state(root, INVENTORY)
            entries = result["queue"]["ENTRIES"]
            self.assertEqual(1, len(entries))
            entry = entries[0]
            self.assertEqual("timeline-operation-first-real-media-cut", entry["LANE_ID"])
            self.assertEqual("f5af2537cb95d5693be460f4d17064f0fa4a6e43", entry["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"])
            self.assertEqual("e0cbac55fa888229fefc362cf2aa37e66d04d675", entry["CANDIDATE_TREE"])
            self.assertEqual("PREVALIDATING", entry["CURRENT_STATE"])
            self.assertEqual("UNRESOLVED", entry["DEPENDENCIES"][0]["STATUS"])
            self.assertEqual("AVAILABLE", result["slot"]["STATUS"])

    def test_all_fourteen_named_negative_controls_pass(self):
        receipt = cpc.run_red_controls()
        self.assertEqual(14, receipt["RED_CONTROL_COUNT"])
        self.assertEqual("PASS", receipt["PUBLICATION_CONTROL_RED_MATRIX"])
        self.assertEqual(14, len(receipt["ROWS"]))
        self.assertTrue(all(row["RESULT"] == "PASS" for row in receipt["ROWS"]))


class IntegratedCorrectionTests(unittest.TestCase):
    CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
    TREE = "fd37409d0274662abbe86f69e3d963c05b379696"
    PREDECESSOR = "EP19-EXACT-CANDIDATE-CANONICAL-PUBLICATION-V1"
    SUCCESSOR = "EP19-ELIGIBILITY-COHERENCE-RECOVERY-SUCCESSOR-V1"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="canonical-integrated-")
        self.root = Path(self.temporary.name)
        predecessor = queue_entry(state="RELEASED_FAILED")
        predecessor.update({
            "QUEUE_ENTRY_ID": self.PREDECESSOR,
            "LANE_ID": "ep19-entitlement-query-authority",
            "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "86d6aef94fd5e58da552e97c11473cff6eca734e",
            "CANDIDATE_TREE": "dba5e1e457af28cfca865e44f48eedabcc28aebb",
            "PUBLICATION_STATUS": "PUBLISHED_POST_PUBLICATION_SANITY_BLOCKED",
            "FAILURE_REASON": "POST_PUBLICATION_ARCHITECTURE_SCAN_CONTAMINATION_AND_OBJECT_ATTRIBUTE_MONITOR_STOP",
        })
        cpc.atomic_write_json(self.root / "queue.json", {
            "SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1",
            "PROTOCOL_VERSION": cpc.PROTOCOL_VERSION,
            "ENTRIES": [predecessor],
        })
        cpc.atomic_write_json(self.root / "transition-ledger.json", {
            "SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1",
            "EVENTS": [{"EVENT_TYPE": "PRESERVED_HISTORY", "VALUE": 1}],
        })
        slot_available(self.root / "slot.json")
        self.before_predecessor = json.loads(json.dumps(predecessor))
        self.before_events = json.loads((self.root / "transition-ledger.json").read_text())["EVENTS"]

    def tearDown(self):
        self.temporary.cleanup()

    def reference(self, name, value):
        path = self.root / name
        cpc.atomic_write_json(path, value)
        return {"PATH": str(path), "SHA256": cpc.file_digest(path)}

    def admission_reference(self):
        executor = self.reference("executor.json", {"schema": "ep19-executor-identity-v1", "candidate": self.CANDIDATE, "tree": self.TREE, "native_entry": "coherence-executor"})
        config = self.reference("config.json", {"schema": "ep19-executor-config-v1", "candidate": self.CANDIDATE, "tree": self.TREE})
        policy = self.reference("policy.json", {"schema": "ep19-gate-policy-v1", "candidate": self.CANDIDATE, "gate_count": 29})
        return self.reference("admission.json", {
            "schema": "ep19-original-control-plane-admission-evidence-v1", "result": "PASS", "fixture_only": False,
            "successor_id": self.SUCCESSOR, "predecessor_id": self.PREDECESSOR,
            "authorization_id": "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1",
            "candidate": self.CANDIDATE, "tree": self.TREE,
            "product_patch_sha256": "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690",
            "historical_formal_consumed": "2/2", "new_formal_total": 1, "new_formal_used": 0,
            "global_next_ordinal": 3, "successor_registered": False, "ledger_route_ready": True,
            "publication_route_ready": True, "dependencies_ready": True, "live_state_mutated_by_writer": False,
            "implementation_sha256": executor["SHA256"], "EXECUTOR_IDENTITY": executor,
            "canonical_controller_sha256": cpc.file_digest(SCRIPT),
            "CONFIG_IDENTITY": config, "POLICY_IDENTITY": policy,
        })

    def formal_reference(self, *, gate_override=None):
        executor_sha = cpc.file_digest(self.root / "executor.json")
        gates = {}
        for gate in json.loads((cpc.REFERENCE_DIR / "protocol-v1.json").read_text())["ep19_successor"]["formal_gate_order"]:
            record = {
                "schema": "ep19-native-gate-result-v1", "gate": gate, "candidate": self.CANDIDATE,
                "tree": self.TREE, "native_result": "PASS", "native_exit_code": 0,
                "acceptance": "ACCEPTED", "executor_sha256": executor_sha, "executor_actor": "formal-executor",
            }
            if gate_override and gate == gate_override[0]:
                record[gate_override[1]] = gate_override[2]
            gates[gate] = self.reference(f"gate-{gate}.json", record)
        seal = self.reference("seal.json", {"schema": "ep19-protection-final-seal-v1", "result": "PASS", "candidate": self.CANDIDATE, "tree": self.TREE, "executor_sha256": executor_sha})
        return self.reference("formal-result.json", {
            "schema": "ep19-original-control-plane-formal-result-v1", "result": "PASS", "native_result": "PASS",
            "native_exit_code": 0, "candidate": self.CANDIDATE, "tree": self.TREE,
            "formal_attempt_id": "EP19-CANDIDATE-FORMAL-OWNER-EXTENSION-001",
            "executor_sha256": executor_sha, "gate_order": list(gates), "gate_results": gates, "protection_final_seal": seal,
        })

    def register_and_accept(self):
        admission = self.admission_reference()
        control = cpc.EP19AcceptanceControl(self.root)
        control.register_successor(evidence=admission, idempotency_key="register-chain", actor="parent-controller", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        control.record_formal_start(idempotency_key="formal-start", actor="formal-executor", timestamp="2026-09-09T18:10:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        control.record_formal_result(evidence=self.formal_reference(), idempotency_key="formal-result", actor="formal-executor", timestamp="2026-09-09T18:20:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        engineering = self.reference("engineering-review.json", {
            "schema": "ep19-independent-engineering-acceptance-v1", "decision": "ACCEPTED",
            "candidate": self.CANDIDATE, "tree": self.TREE, "reviewer_role": "INDEPENDENT_ENGINEERING_REVIEWER",
            "reviewer_actor": "independent-engineer", "implementation_sha256": cpc.file_digest(self.root / "executor.json"),
            "reviewed_controller_sha256": cpc.file_digest(SCRIPT),
            "reviewed_formal_evidence_sha256": cpc.QueueControl(self.root / "queue.json").get(self.SUCCESSOR)["FORMAL_RESULT_EVIDENCE"]["VERIFIED_SHA256"],
        })
        control.record_engineering_acceptance(evidence=engineering, idempotency_key="engineering", actor="independent-engineer", timestamp="2026-09-09T18:30:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        return control

    def test_partial_state_journal_blocks_original_queue_and_slot_readers(self):
        (self.root / ".canonical-publication-state-transaction.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(cpc.ControlError):
            cpc.QueueControl(self.root / "queue.json").get(self.PREDECESSOR)
        with self.assertRaises(cpc.ControlError):
            cpc.SlotControl(self.root).load()

    def test_reachable_stable_reader_rejects_partial_authority(self):
        (self.root / cpc.STATE_JOURNAL_NAME).write_text("{}\n", encoding="utf-8")
        with self.assertRaises(cpc.ControlError):
            cpc.stable_state_readback(self.root / "queue.json")

    def test_recovery_rejects_nonexact_authority_set(self):
        control = cpc.EP19AcceptanceControl(self.root)
        kwargs = dict(evidence=self.admission_reference(), idempotency_key="register-malformed-recovery",
            actor="parent", timestamp="2026-09-09T18:00:00Z",
            expected_queue_sha256=cpc.file_digest(self.root / "queue.json"),
            expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"),
            fault="AFTER_WRITE_1")
        with self.assertRaises(cpc.InjectedFault):
            control.register_successor(**kwargs)
        journal = json.loads((self.root / cpc.STATE_JOURNAL_NAME).read_text())
        journal["AFTER"]["unexpected.json"] = {}
        journal["AFTER_SHA256"]["unexpected.json"] = cpc.sha256_bytes(cpc.canonical_json_bytes({}))
        cpc.atomic_write_json(self.root / cpc.STATE_JOURNAL_NAME, journal)
        with self.assertRaises(cpc.ControlError):
            cpc.StateTransaction(self.root).recover()

    def test_interrupted_original_transaction_blocks_readers_then_recovers_exactly_once(self):
        control = cpc.EP19AcceptanceControl(self.root)
        kwargs = dict(evidence=self.admission_reference(), idempotency_key="register-fault", actor="parent", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"), fault="AFTER_WRITE_1")
        with self.assertRaises(cpc.InjectedFault):
            control.register_successor(**kwargs)
        with self.assertRaises(cpc.ControlError):
            cpc.QueueControl(self.root / "queue.json").load()
        with self.assertRaises(cpc.ControlError):
            cpc.SlotControl(self.root).load()
        self.assertEqual("RECOVERED_COMMITTED", cpc.StateTransaction(self.root).recover()["STATUS"])
        self.assertEqual("IDEMPOTENT_REPLAY", control.register_successor(**kwargs)["STATUS"])

    def test_successor_registration_uses_original_transaction_and_is_replay_safe(self):
        control = cpc.EP19AcceptanceControl(self.root)
        before_queue = cpc.file_digest(self.root / "queue.json")
        before_ledger = cpc.file_digest(self.root / "transition-ledger.json")
        kwargs = dict(evidence=self.admission_reference(), idempotency_key="register-001", actor="parent-controller", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=before_queue, expected_ledger_sha256=before_ledger)
        self.assertEqual("COMMITTED", control.register_successor(**kwargs)["STATUS"])
        self.assertEqual("IDEMPOTENT_REPLAY", control.register_successor(**kwargs)["STATUS"])
        queue = json.loads((self.root / "queue.json").read_text())
        ledger = json.loads((self.root / "transition-ledger.json").read_text())
        self.assertEqual(self.before_predecessor, queue["ENTRIES"][0])
        self.assertEqual(self.before_events, ledger["EVENTS"][:len(self.before_events)])
        self.assertEqual(1, sum(e["QUEUE_ENTRY_ID"] == self.SUCCESSOR for e in queue["ENTRIES"]))

    def test_nonexistent_or_fake_digest_admission_is_rejected_without_state_change(self):
        control = cpc.EP19AcceptanceControl(self.root)
        before = cpc.file_digest(self.root / "queue.json")
        bad = {"PATH": str(self.root / "missing.json"), "SHA256": "1" * 64}
        with self.assertRaises(cpc.ControlError):
            control.register_successor(evidence=bad, idempotency_key="bad", actor="parent", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=before, expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        self.assertEqual(before, cpc.file_digest(self.root / "queue.json"))

    def test_concurrent_original_writers_serialize_and_do_not_lose_updates(self):
        control = cpc.EP19AcceptanceControl(self.root)
        qhash = cpc.file_digest(self.root / "queue.json")
        lhash = cpc.file_digest(self.root / "transition-ledger.json")
        evidence_ref = self.admission_reference()
        barrier = threading.Barrier(2)
        outcomes = []
        def run(key):
            barrier.wait()
            try:
                outcomes.append(control.register_successor(evidence=evidence_ref, idempotency_key=key, actor="parent", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=qhash, expected_ledger_sha256=lhash)["STATUS"])
            except cpc.ControlError:
                outcomes.append("REJECTED")
        threads = [threading.Thread(target=run, args=(key,)) for key in ("a", "b")]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(["COMMITTED", "REJECTED"], sorted(outcomes))

    def test_direct_ff_is_exact_candidate_only_and_default_two_parent_stays_default(self):
        protocol = json.loads((cpc.REFERENCE_DIR / "protocol-v1.json").read_text())
        self.assertEqual(self.CANDIDATE, protocol["ep19_successor"]["candidate"])
        self.assertEqual("EXACT_NORMAL_PUBLICATION_ONLY", protocol["publication_authorization_receipt_schema"]["authorization"])
        self.assertEqual("EXACT_A298_DIRECT_FAST_FORWARD_EXCEPTION", protocol["ep19_successor"]["direct_ff_authorization"])
        self.assertTrue(hasattr(cpc.SlotControl, "authorize_ep19_direct_ff"))

    def test_generic_transition_cannot_bypass_dedicated_publication_consumers(self):
        control = self.register_and_accept()
        queue = cpc.QueueControl(self.root / "queue.json")
        queue.transition(self.SUCCESSOR, "QUEUED", actor="parent-controller")
        slot = cpc.SlotControl(self.root)
        slot.acquire("publication-controller", queue.get(self.SUCCESSOR), "86d6aef94fd5e58da552e97c11473cff6eca734e")
        for state in ("INTEGRATING", "VALIDATING_INTEGRATION", "FROZEN_FOR_REVIEW",
                      "INDEPENDENT_REVIEW", "APPROVED_FOR_PUBLICATION", "CANONICAL"):
            with self.subTest(state=state), self.assertRaises(cpc.ControlError):
                queue.transition(self.SUCCESSOR, state, actor="publication-controller")

    def test_direct_ff_dedicated_ordering_and_exact_caller_entry(self):
        self.register_and_accept()
        queue = cpc.QueueControl(self.root / "queue.json")
        queue.transition(self.SUCCESSOR, "QUEUED", actor="parent-controller")
        slot = cpc.SlotControl(self.root)
        fresh = "86d6aef94fd5e58da552e97c11473cff6eca734e"
        slot.acquire("publication-controller", queue.get(self.SUCCESSOR), fresh)
        slot.prepare_ep19_direct_ff(owner="publication-controller", entry=queue.get(self.SUCCESSOR),
            idempotency_key="prepare-direct", timestamp="2026-09-09T18:40:00Z",
            expected_queue_sha256=cpc.file_digest(self.root / "queue.json"),
            expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        wrong = dict(queue.get(self.SUCCESSOR)); wrong["QUEUE_ENTRY_ID"] = "wrong-entry"
        ancestry = self.reference("bound-ancestry.json", {"schema": "ep19-fresh-main-ancestry-v1", "result": "PASS", "native_exit_code": 0, "candidate": self.CANDIDATE, "candidate_tree": self.TREE, "fresh_main": fresh, "is_ancestor": True, "actor": "publication-controller"})
        race = self.reference("bound-race.json", {"schema": "ep19-final-main-race-check-v1", "result": "PASS", "native_exit_code": 0, "observed_main": fresh, "no_race": True, "actor": "publication-controller"})
        remote = self.reference("bound-remote.json", {"schema": "ep19-remote-candidate-readback-v1", "result": "PASS", "native_exit_code": 0, "candidate": self.CANDIDATE, "candidate_tree": self.TREE, "actor": "publication-controller"})
        with self.assertRaises(cpc.ControlError):
            slot.authorize_ep19_direct_ff(owner="publication-controller", entry=wrong,
                ancestry_evidence=ancestry, race_evidence=race, remote_evidence=remote,
                idempotency_key="wrong-target", timestamp="2026-09-09T19:00:00Z",
                expected_queue_sha256=cpc.file_digest(self.root / "queue.json"),
                expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))

    def test_real_formal_bytes_reject_not_run_and_wrong_executor(self):
        control = cpc.EP19AcceptanceControl(self.root)
        control.register_successor(evidence=self.admission_reference(), idempotency_key="register-formal", actor="parent", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        control.record_formal_start(idempotency_key="start-formal", actor="formal-executor", timestamp="2026-09-09T18:10:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        for override in (("BOOTJAR", "native_result", "NOT_RUN"), ("FORMAL", "executor_sha256", "0" * 64)):
            with self.subTest(override=override):
                with self.assertRaises(cpc.ControlError):
                    control.record_formal_result(evidence=self.formal_reference(gate_override=override), idempotency_key="bad-formal-" + override[0], actor="formal-executor", timestamp="2026-09-09T18:20:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))

    def test_real_formal_failure_is_appended_consumed_and_cannot_retry(self):
        control = cpc.EP19AcceptanceControl(self.root)
        control.register_successor(evidence=self.admission_reference(), idempotency_key="register-failure", actor="parent", timestamp="2026-09-09T18:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        control.record_formal_start(idempotency_key="start-failure", actor="formal-executor", timestamp="2026-09-09T18:10:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        failure = self.reference("formal-failure.json", {
            "schema": "ep19-original-control-plane-formal-result-v1", "result": "INTERRUPTED",
            "native_result": "INTERRUPTED", "native_exit_code": 130, "acceptance": "REJECTED",
            "candidate": self.CANDIDATE, "tree": self.TREE,
            "formal_attempt_id": "EP19-CANDIDATE-FORMAL-OWNER-EXTENSION-001",
            "executor_sha256": cpc.file_digest(self.root / "executor.json"),
        })
        control.record_formal_result(evidence=failure, idempotency_key="result-failure", actor="formal-executor", timestamp="2026-09-09T18:20:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        entry = cpc.QueueControl(self.root / "queue.json").get(self.SUCCESSOR)
        self.assertEqual("RELEASED_FAILED", entry["CURRENT_STATE"])
        self.assertEqual(1, entry["FORMAL"]["NEW_USED"])
        self.assertFalse(entry["FORMAL"]["AUTO_RETRY"])
        with self.assertRaises(cpc.ControlError):
            control.record_formal_start(idempotency_key="forbidden-retry", actor="formal-executor", timestamp="2026-09-09T18:30:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))

    def test_actual_slot_direct_ff_publication_and_closure_chain_consumes_real_receipts(self):
        control = self.register_and_accept()
        queue = cpc.QueueControl(self.root / "queue.json")
        queue.transition(self.SUCCESSOR, "QUEUED", actor="parent-controller")
        slot = cpc.SlotControl(self.root)
        entry = queue.get(self.SUCCESSOR)
        fresh = "86d6aef94fd5e58da552e97c11473cff6eca734e"
        slot.acquire("publication-controller", entry, fresh)
        for state in ("INTEGRATING", "VALIDATING_INTEGRATION", "FROZEN_FOR_REVIEW", "INDEPENDENT_REVIEW", "APPROVED_FOR_PUBLICATION"):
            queue.transition(self.SUCCESSOR, state, actor="publication-controller")
        ancestry = self.reference("ancestry.json", {"schema": "ep19-fresh-main-ancestry-v1", "result": "PASS", "native_exit_code": 0, "candidate": self.CANDIDATE, "candidate_tree": self.TREE, "fresh_main": fresh, "is_ancestor": True, "actor": "publication-controller"})
        race = self.reference("race.json", {"schema": "ep19-final-main-race-check-v1", "result": "PASS", "native_exit_code": 0, "observed_main": fresh, "no_race": True, "actor": "publication-controller"})
        remote = self.reference("remote.json", {"schema": "ep19-remote-candidate-readback-v1", "result": "PASS", "native_exit_code": 0, "candidate": self.CANDIDATE, "candidate_tree": self.TREE, "actor": "publication-controller"})
        bad_race = self.reference("bad-race.json", {"schema": "ep19-final-main-race-check-v1", "result": "PASS", "native_exit_code": 0, "observed_main": fresh, "no_race": False, "actor": "publication-controller"})
        with self.assertRaises(cpc.ControlError):
            slot.authorize_ep19_direct_ff(owner="publication-controller", entry=queue.get(self.SUCCESSOR), ancestry_evidence=ancestry, race_evidence=bad_race, remote_evidence=remote, idempotency_key="direct-bad", timestamp="2026-09-09T19:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        result = slot.authorize_ep19_direct_ff(owner="publication-controller", entry=queue.get(self.SUCCESSOR), ancestry_evidence=ancestry, race_evidence=race, remote_evidence=remote, idempotency_key="direct-good", timestamp="2026-09-09T19:00:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        self.assertEqual("EXACT_A298_DIRECT_FAST_FORWARD_EXCEPTION", result["RECEIPT"]["AUTHORIZATION"])
        canonical = self.reference("canonical.json", {"schema": "ep19-canonical-main-readback-v1", "result": "PASS", "native_exit_code": 0, "candidate": self.CANDIDATE, "candidate_tree": self.TREE, "actor": "publication-controller"})
        slot.record_ep19_publication_result(owner="publication-controller", canonical_readback_evidence=canonical, idempotency_key="published", timestamp="2026-09-09T19:05:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        sanity_gates = json.loads((cpc.REFERENCE_DIR / "protocol-v1.json").read_text())["ep19_successor"]["post_publication_sanity_gates"]
        sanity_results = {gate: self.reference(f"sanity-{gate}.json", {"schema": "ep19-post-publication-sanity-gate-v1", "gate": gate, "candidate": self.CANDIDATE, "tree": self.TREE, "native_result": "PASS", "native_exit_code": 0, "acceptance": "ACCEPTED"}) for gate in sanity_gates}
        sanity = self.reference("sanity.json", {"schema": "ep19-post-publication-sanity-v1", "result": "PASS", "candidate": self.CANDIDATE, "tree": self.TREE, "implementation_sha256": cpc.file_digest(self.root / "executor.json"), "gate_order": sanity_gates, "gate_results": sanity_results})
        closure = self.reference("closure.json", {"schema": "ep19-independent-closure-review-v1", "decision": "ACCEPTED", "candidate": self.CANDIDATE, "tree": self.TREE, "reviewer_role": "INDEPENDENT_CLOSURE_REVIEWER", "reviewer_actor": "independent-closer", "implementation_sha256": cpc.file_digest(self.root / "executor.json"), "reviewed_controller_sha256": cpc.file_digest(SCRIPT), "reviewed_sanity_sha256": sanity["SHA256"], "reviewed_canonical_readback_sha256": canonical["SHA256"]})
        control.close_successor(sanity_evidence=sanity, closure_review_evidence=closure, idempotency_key="close", actor="independent-closer", timestamp="2026-09-09T19:30:00Z", expected_queue_sha256=cpc.file_digest(self.root / "queue.json"), expected_ledger_sha256=cpc.file_digest(self.root / "transition-ledger.json"))
        self.assertEqual("CLOSED_ACCEPTED_SUCCESSOR", queue.get(self.SUCCESSOR)["EP19_CLOSED"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
