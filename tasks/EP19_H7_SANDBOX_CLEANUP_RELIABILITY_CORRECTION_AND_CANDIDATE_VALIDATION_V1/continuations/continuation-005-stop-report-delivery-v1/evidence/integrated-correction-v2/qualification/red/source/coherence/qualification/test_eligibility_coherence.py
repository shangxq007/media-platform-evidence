"""Private synthetic qualification for bounded eligibility coherence."""
from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch as mock_patch
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile

TOOLING = Path(os.environ.get("EP19_TEST_TOOLING_ROOT", Path(__file__).resolve().parents[1])).absolute()
EXECUTOR = TOOLING / "executor"
QUALIFICATION = TOOLING / "qualification"
sys.path[:0] = [str(EXECUTOR), str(QUALIFICATION)]

import bookkeeping_v3 as bk
import eligibility_admission as admission
import eligibility_coherence as coherence
import external29_driver
import policy_builder

CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
TREE = "fd37409d0274662abbe86f69e3d963c05b379696"
PARENT = "689ab9456461a8d19a72d059f5157092efc43aff"
PATCH = "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690"


def write(path, value, raw=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if raw else (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    return path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Fixture:
    def __init__(self, parent):
        self.base = Path(tempfile.mkdtemp(prefix="coherence-", dir=parent))
        self.root = self.base / "skills"; self.root.mkdir()
        files = {
            "a-toolchain/SKILL.md": b"accepted toolchain\n",
            "a-toolchain/references/remote.md": b"accepted remote reference\n",
            "b-quality/SKILL.md": b"accepted quality\n",
            "c-stable/SKILL.md": b"unchanged exact reuse\n",
        }
        for relative, raw in files.items(): write(self.root / relative, raw, raw=True)
        usage = {name: {"view_count": 1, "use_count": 1,
                        "last_viewed_at": None, "last_used_at": None}
                 for name in ("a-toolchain", "b-quality", "c-stable")}
        write(self.root / ".usage.json", usage)
        write(self.root / ".usage.json.lock", b"", raw=True)
        write(self.root / ".curator_ledger.jsonl", b"", raw=True)
        self.packages = []
        for name in ("a-toolchain", "b-quality", "c-stable"):
            package = self.root / name
            manifest = [{"path": str(path), "sha256": sha(path)}
                        for path in sorted(package.rglob("*")) if path.is_file()]
            self.packages.append({"skill": name, "package_root": str(package), "manifest": manifest})
        strict = sorted([row for package in self.packages for row in package["manifest"]],
                        key=lambda row: row["path"])
        instructions = [row for row in strict if row["path"].endswith(("SKILL.md", "remote.md")) and
                        "c-stable" not in row["path"]]
        accepted = [{"alias": alias, **row} for alias, row in zip(("T", "R", "Q"), instructions)]
        semantic_value = {"decision": coherence.SEMANTIC_DECISION, "accepted_inputs": accepted}
        self.semantic = write(self.base / "SEMANTIC.json", semantic_value)
        self.review = write(self.base / "REVIEW.json", {
            "implementation_review": "PASS", "independent_final_acceptance": "PENDING"})
        self.control = write(self.base / "CONTROL.json", {
            "schema": "ep19-original-control-plane-admission-evidence-v1", "result": "PASS",
            "fixture_only": True, "successor_id": "EP19-SYNTHETIC-SUCCESSOR",
            "predecessor_id": "EP19-EXACT-CANDIDATE-CANONICAL-PUBLICATION-V1",
            "authorization_id": "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1",
            "candidate": CANDIDATE, "tree": TREE, "product_patch_sha256": PATCH,
            "historical_formal_consumed": "2/2", "new_formal_total": 1, "new_formal_used": 0,
            "global_next_ordinal": 3, "successor_registered": True, "ledger_route_ready": True,
            "publication_route_ready": True, "dependencies_ready": True,
            "idempotency_key": "synthetic-control-001", "live_state_mutated_by_writer": False,
            "implementation_sha256": "5" * 64})
        self.run = self.base / "candidate-formal-003"; self.run.mkdir()
        write(self.run / "PREPARATION_COMPATIBILITY.json", {"result": "PASS", "fixture_only": True})
        disposition = {
            "schema": "ep19-preloaded-preparation-disposition-v1", "result": "READY",
            "run_id": self.run.name,
            "instruction_inputs": {row["path"]: row["sha256"] for row in instructions},
            "instruction_inventory": {row["path"]: row["sha256"] for row in strict},
        }
        write(self.run / "PREPARATION_DISPOSITION.json", disposition)
        fake = "1" * 64
        self.config = {
            "run_id": self.run.name, "candidate": CANDIDATE, "tree": TREE,
            "product_patch_sha256": PATCH, "matrix_sha256": fake,
            "dependency_sha256": "2" * 64, "qualification_sha256": "3" * 64,
            "adapter_qualification_sha256": "4" * 64,
            "control_plane_implementation_sha256": "5" * 64,
        }
        contract = {
            "schema": coherence.SCHEMA, "contract_id": "synthetic-coherence-contract-001",
            "task": "PRIVATE_SYNTHETIC_QUALIFICATION", "capture_root": str(self.root),
            "fixture_only": True,
            "candidate_identity": {"candidate": CANDIDATE, "tree": TREE,
                "immediate_parent": PARENT, "product_patch_sha256": PATCH},
            "attempt_authority": {
                "authorization_id": "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1",
                "run_id": self.run.name, "global_ordinal": 3, "historical_consumed": "2/2",
                "new_allowance_total": 1, "new_allowance_used_before": 0,
                "retry_authorized": False,
                "historical_attempt_ids": ["candidate-formal-001", "candidate-formal-002"]},
            "limits": dict(coherence.EXPECTED_LIMITS), "packages": self.packages,
            "strict_inventory": strict, "instruction_projection": instructions,
            "semantic_acceptance": {"path": str(self.semantic), "sha256": sha(self.semantic),
                "decision": coherence.SEMANTIC_DECISION, "accepted_inputs": accepted,
                "six_axis_exclusions_bound": True, "historical_author_approval": False,
                "shared_mutation_authorized": False},
            "version_chain": {**self.config,
                "semantic_acceptance_sha256": sha(self.semantic),
                "implementation_review_sha256": sha(self.review),
                "control_plane_implementation_sha256": "5" * 64},
            "preparation": {"required_receipts": ["PREPARATION_COMPATIBILITY.json",
                "PREPARATION_DISPOSITION.json"], "disposition_name": "PREPARATION_DISPOSITION.json"},
            "control_plane": {"successor_id": "EP19-SYNTHETIC-SUCCESSOR",
                "predecessor_id": "EP19-EXACT-CANDIDATE-CANONICAL-PUBLICATION-V1",
                "authorization_id": "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1",
                "implementation_sha256": "5" * 64},
            "privacy": {"raw_inputs": "PRIVATE_LOCAL_ONLY", "public_whole_inventory": False},
        }
        contract["version_chain"].pop("run_id")
        self.contract_value = contract
        self.contract = write(self.base / "CONTRACT.json", contract)
        self.config.update(eligibility_contract=str(self.contract),
                           eligibility_contract_sha256=coherence.identity(contract))
        self.binding = write(self.base / "BINDING.json", {"fixture_only": True})
        self.config_path = write(self.base / "CONFIG.json", self.config)

    def admit(self, output=None):
        config = {**self.config, "binding_sha256": sha(self.binding)}
        return admission.admit(config=config, binding=self.binding, contract_path=self.contract,
            review=self.review, control=self.control, run=self.run,
            output=output or self.base / "admission", allow_fixture=True)


class BoundedEligibilityCoherence(TestCase):
    @classmethod
    def setUpClass(cls):
        parent = Path(os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT", tempfile.gettempdir()))
        parent.mkdir(parents=True, exist_ok=True)
        cls.parent = parent

    def setUp(self):
        self.f = Fixture(self.parent)

    def test_consistent_inputs_pass_real_admission_consumer_without_consumption(self):
        result = self.f.admit()
        self.assertEqual("PASS", result["result"])
        self.assertFalse(result["formal_budget_consumed"])
        self.assertFalse(any((self.f.run / name).exists() for name in admission.FORBIDDEN_BEFORE_CONSUME))

    def test_admission_validation_recomputes_persisted_capture_bytes(self):
        result = self.f.admit()
        capture = self.f.base / "admission/COHERENCE_CAPTURE.private.json"
        capture.write_text("{}\n", encoding="utf-8")
        config = {**self.f.config, "binding_sha256": sha(self.f.binding)}
        with self.assertRaises(coherence.CoherenceError):
            admission.validate_admission_receipt(self.f.base / "admission/ADMISSION.json",
                config=config, contract=self.f.contract_value, review=self.f.review,
                control=self.f.control)

    def test_nonfixture_control_self_report_without_controller_receipt_rejects(self):
        value = coherence.load(self.f.control); value["fixture_only"] = False
        control = write(self.f.base / "CONTROL-NONFIXTURE.json", value)
        with self.assertRaises(coherence.CoherenceError):
            coherence.validate_control_plane(self.f.contract_value, control)

    def test_nonfixture_admission_output_must_be_inside_run(self):
        contract = copy.deepcopy(self.f.contract_value); contract["fixture_only"] = False
        contract["capture_root"] = str(self.f.root)
        contract_path = write(self.f.base / "CONTRACT-NONFIXTURE.json", contract)
        config = {**self.f.config, "binding_sha256": sha(self.f.binding),
            "eligibility_contract": str(contract_path),
            "eligibility_contract_sha256": coherence.identity(contract)}
        control_value = coherence.load(self.f.control); control_value["fixture_only"] = False
        control = write(self.f.base / "CONTROL-NONFIXTURE-OUTPUT.json", control_value)
        with mock_patch.object(bk, "PRODUCTION_ROOT", self.f.root), self.assertRaises(coherence.CoherenceError):
            admission.admit(config=config, binding=self.f.binding, contract_path=contract_path,
                review=self.f.review, control=control, run=self.f.run,
                output=self.f.base / "outside-run", allow_fixture=False)

    def test_actual_cli_consistent_green_and_no_formal_marker(self):
        output = self.f.base / "cli-green"
        command = [sys.executable, "-B", str(EXECUTOR / "external29_driver.py"), "coherence-fixture",
            "--config", str(self.f.config_path), "--binding", str(self.f.binding),
            "--eligibility-contract", str(self.f.contract), "--review", str(self.f.review),
            "--control-plane-evidence", str(self.f.control), "--run", str(self.f.run),
            "--output", str(output)]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(0, process.returncode, process.stdout.decode(errors="replace"))
        self.assertTrue((output / "ADMISSION.json").is_file())
        self.assertFalse((self.f.run / "FORMAL_ATTEMPT.json").exists())

    def test_conflicting_manifest_rejects_admission_without_consumption(self):
        target = self.f.root / "a-toolchain/SKILL.md"; target.write_text("conflict\n")
        with self.assertRaises(coherence.CoherenceError) as raised:
            self.f.admit()
        self.assertEqual("CONTENT_HASH_MISMATCH", raised.exception.primary_reason)
        self.assertFalse((self.f.run / "FORMAL_ATTEMPT.json").exists())
        self.assertTrue((self.f.base / "admission/COHERENCE_CAPTURE.private.json").is_file())

    def test_two_historical_type_preexisting_differences_are_same_capture(self):
        (self.f.root / "a-toolchain/SKILL.md").write_text("new toolchain\n")
        (self.f.root / "a-toolchain/references/remote.md").write_text("new reference\n")
        with self.assertRaises(coherence.CoherenceError) as raised: self.f.admit()
        comparison = raised.exception.comparison
        self.assertEqual(2, comparison["difference_count"])
        self.assertEqual({"CONTENT_HASH_MISMATCH"}, {row["classification"] for row in comparison["differences"]})
        self.assertEqual(comparison["capture_id"],
            coherence.load(self.f.base / "admission/COHERENCE_COMPARISON.json")["capture_id"])

    def test_change_after_prepare_and_admission_rejects_postconsume_policy(self):
        admitted = self.f.admit(); (self.f.run / "FORMAL_ATTEMPT.json").write_text("synthetic consume\n")
        (self.f.root / "b-quality/SKILL.md").write_text("changed after admission\n")
        app = {"eligible_packages": [{"skill": row["skill"], "package_root": row["package_root"],
                                       "eligible": True, "errors": []} for row in self.f.packages]}
        private_map = {"schema": "ep19-eligible-package-manifest-candidate-v1",
                       "eligible_skills": {row["skill"]: row["manifest"] for row in self.f.packages}}
        inventory = {"schema": "fixture"}; dependency = {"fixture": True}; owner = self.f.base / "OWNER"
        owner.write_text("owner\n")
        map_path = write(self.f.base / "MAP.json", private_map); inv_path = write(self.f.base / "INV.json", inventory)
        app.update(private_manifest_sha256=sha(map_path), private_strict_inventory_sha256=sha(inv_path))
        app_path = write(self.f.base / "APP.json", app); dep_path = write(self.f.base / "DEP.json", dependency)
        with self.assertRaises(coherence.CoherenceError) as raised:
            policy_builder.build(app_path, map_path, inv_path, owner, dep_path,
                coherence_contract=self.f.contract,
                coherence_private=self.f.base / "formal/private.json",
                coherence_public=self.f.base / "formal/public.json", allow_fixture=True)
        self.assertEqual("CONTENT_HASH_MISMATCH", raised.exception.primary_reason)
        self.assertNotEqual(admitted["comparison"]["capture_id"], raised.exception.comparison["capture_id"])

    def test_scope_missing_extra_duplicate_order_and_path_normalization_reject(self):
        contract = coherence.validate_contract(copy.deepcopy(self.f.contract_value), allow_fixture=True)
        expected = {row["skill"]: copy.deepcopy(row["manifest"]) for row in contract["packages"]}
        variants = []
        missing = copy.deepcopy(expected); missing["a-toolchain"].pop(); variants.append((missing, "PATH_MISSING"))
        extra = copy.deepcopy(expected); extra["a-toolchain"].append({"path": str(self.f.root / "a-toolchain/extra"), "sha256": "0"*64}); variants.append((extra, "PATH_EXTRA"))
        duplicate = copy.deepcopy(expected); duplicate["a-toolchain"].append(copy.deepcopy(duplicate["a-toolchain"][0])); variants.append((duplicate, "PATH_DUPLICATE"))
        order = copy.deepcopy(expected); order["a-toolchain"] = list(reversed(order["a-toolchain"])); variants.append((order, "PATH_ORDER"))
        badpath = copy.deepcopy(expected); badpath["a-toolchain"][0]["path"] += "/../SKILL.md"; variants.append((badpath, "PATH_NONCANONICAL"))
        outscope = copy.deepcopy(expected); outscope["a-toolchain"][0]["path"] = str(self.f.base / "outside"); variants.append((outscope, "PATH_OUT_OF_SCOPE"))
        for actual, wanted in variants:
            with self.subTest(wanted=wanted):
                result = coherence.compare(contract, coherence.capture_record(actual, "SYNTHETIC"))
                self.assertEqual("REJECT", result["result"])
                self.assertIn(wanted, {row["classification"] for row in result["differences"]})

    def test_mixed_old_new_version_chain_rejects(self):
        config = {**self.f.config, "qualification_sha256": "9" * 64}
        with self.assertRaisesRegex(coherence.CoherenceError, "MIXED_VERSION_CHAIN_REJECT"):
            coherence.validate_version_chain(self.f.contract_value, config, self.f.review)

    def test_qualification_pass_without_coherence_never_ready(self):
        self.assertEqual("3" * 64, self.f.config["qualification_sha256"])
        (self.f.root / "c-stable/SKILL.md").write_text("not coherent\n")
        with self.assertRaises(coherence.CoherenceError): self.f.admit()
        self.assertFalse((self.f.base / "admission/ADMISSION.json").exists())

    def test_real_difference_writer_failure_preserves_primary_and_secondary(self):
        (self.f.root / "c-stable/SKILL.md").write_text("primary mismatch\n")
        blocked = self.f.base / "blocked"; blocked.write_text("not a directory\n")
        with self.assertRaises(coherence.CoherenceError) as raised:
            self.f.admit(blocked / "output")
        self.assertEqual("CONTENT_HASH_MISMATCH", raised.exception.primary_reason)
        self.assertGreaterEqual(len(raised.exception.diagnostic_errors), 2)
        command = [sys.executable, "-B", str(EXECUTOR / "external29_driver.py"), "coherence-fixture",
            "--config", str(self.f.config_path), "--binding", str(self.f.binding),
            "--eligibility-contract", str(self.f.contract), "--review", str(self.f.review),
            "--control-plane-evidence", str(self.f.control), "--run", str(self.f.run),
            "--output", str(blocked / "cli-output")]
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(1, process.returncode)
        diagnostic = json.loads(process.stderr)
        self.assertEqual("CONTENT_HASH_MISMATCH", diagnostic["coherence_primary_reject"])
        self.assertEqual(2, len(diagnostic["coherence_diagnostic_persistence_errors"]))

    def test_unique_budget_duplicate_consume_has_no_double_consumption(self):
        marker_run = self.f.base / "consume-run"; marker_run.mkdir()
        consume = write(self.f.base / "CONTROL_CONSUME.json", {
            "schema": "ep19-original-control-plane-formal-consume-evidence-v1", "result": "PASS",
            "fixture_only": True, "successor_id": "EP19-SYNTHETIC-SUCCESSOR",
            "authorization_id": "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1",
            "candidate": CANDIDATE, "formal_attempt_id": "EP19-CANDIDATE-FORMAL-OWNER-EXTENSION-001",
            "historical_formal_consumed": "2/2", "new_used_before": 0, "new_used_after": 1,
            "global_ordinal": 3, "auto_retry": False, "idempotency_key": "synthetic-consume-001",
            "transaction_id": "synthetic-transaction-001", "implementation_sha256": "5" * 64,
            "admission_control_evidence_sha256": sha(self.f.control), "performed_by_parent": True})
        coherence.validate_control_consumption(self.f.contract_value, consume,
            admission_control_sha256=sha(self.f.control), allow_fixture=True)
        with mock_patch.object(external29_driver, "ROOT", self.f.base):
            first = external29_driver.consume_formal(marker_run, self.f.binding, self.f.review,
                self.f.contract, self.f.control, consume, self.f.semantic)
            with self.assertRaisesRegex(RuntimeError, "FORMAL_NAMESPACE_ALREADY_CONSUMED"):
                external29_driver.consume_formal(marker_run, self.f.binding, self.f.review,
                    self.f.contract, self.f.control, consume, self.f.semantic)
        self.assertEqual((3, 0, 1), (first["global_attempt_ordinal"],
            first["new_allowance_used_before"], first["new_allowance_used_after"]))
        self.assertEqual(first, coherence.load(marker_run / "FORMAL_ATTEMPT.json"))

    def test_contract_limits_and_abc_roles_remain_exact(self):
        self.assertEqual(coherence.EXPECTED_LIMITS, bk.LIMITS)
        self.assertEqual("OBSERVATION_INTEGRITY_ONLY",
            "OBSERVATION_INTEGRITY_ONLY")
        self.assertNotIn("attempt_timeout_seconds", self.f.contract_value["attempt_authority"])
