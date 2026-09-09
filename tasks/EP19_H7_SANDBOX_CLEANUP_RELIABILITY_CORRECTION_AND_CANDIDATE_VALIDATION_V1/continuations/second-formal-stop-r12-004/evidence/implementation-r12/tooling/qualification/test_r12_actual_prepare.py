"""Actual private prepare CLI seam; product producers are never re-run.

The imported private source snapshot changes only fixture ancestry and the
qualification precondition.  binding_contract.load, runner.prepare,
execution.verify_object_source and identity_delta.validate remain real.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


PYTHON = Path("USER_HOME/.hermes/hermes-agent/venv/bin/python3")
CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
TREE = "fd37409d0274662abbe86f69e3d963c05b379696"
PARENT = "689ab9456461a8d19a72d059f5157092efc43aff"
BASE = "86d6aef94fd5e58da552e97c11473cff6eca734e"
PRODUCT_PATCH = "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690"
PRODUCT_DELTA_SHA256 = "4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source_binding(root):
    root = Path(root)
    return {str(path): digest(path) for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
            and "outputs" not in path.relative_to(root).parts}


class R12ActualPrepareConsumerControls(unittest.TestCase):
    maxDiff = None

    def test_actual_cli_prepare_identity_contract_and_negative_matrix(self):
        tested = Path(os.environ["EP19_TEST_TOOLING_ROOT"]).resolve()
        continuation = tested.parents[1]
        task = continuation.parent
        fixture_root = continuation / "fixtures-r12"
        fixture_root.mkdir(mode=0o700, exist_ok=True)
        snapshot = Path(tempfile.mkdtemp(prefix="implementation-r12-cli-", dir=fixture_root))
        tooling = snapshot / "tooling"
        shutil.copytree(tested, tooling)

        # Private-only substitutions: preserve the actual target validators, while
        # adapting this extra nesting and replacing only the already-qualified
        # preparation precondition with a sealed fixture source check.
        binding_path = tooling / "executor/binding_contract.py"
        binding_text = binding_path.read_text()
        binding_text = binding_text.replace("TASK = ROOT.parents[2]", "TASK = ROOT.parents[3]")
        binding_text = binding_text.replace("writer-evidence-r11", "writer-evidence-r12")
        binding_path.write_text(binding_text)
        dependency_path = tooling / "executor/dependency_contract.py"
        dependency_path.write_text(dependency_path.read_text().replace(
            'resolve().parents[4]/"checkout"', 'resolve().parents[5]/"checkout"'))
        coverage_path = tooling / "executor/coverage.py"
        needle = "    path=Path(path);q=json.loads(path.read_text())\n"
        private_validator = needle + (
            "    if q.get('schema')=='ep19-r12-private-preparation-qualification-v1':\n"
            "        required={'schema','result','purpose','product_gate_execution','formal_attempt','shared_preparation','source_binding','test_body','test_body_sha256','substitutions'}\n"
            "        binding_contract.require(set(q)==required and q['result']=='PASS', 'PRIVATE_PREPARATION_QUALIFICATION_SCHEMA')\n"
            "        binding_contract.require(q['purpose']=='TARGET_VALIDATOR_PATH_ONLY_NOT_INTEGRATED_QUALIFICATION' and q['product_gate_execution'] is False and q['formal_attempt'] is False and q['shared_preparation'] is False, 'PRIVATE_PREPARATION_QUALIFICATION_SCOPE')\n"
            "        actual={str(p):digest(p) for p in sorted(D.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'outputs' not in p.relative_to(D).parts}\n"
            "        binding_contract.require(q['source_binding']==actual and digest(q['test_body'])==q['test_body_sha256'], 'PRIVATE_PREPARATION_QUALIFICATION_SOURCE')\n"
            "        return [path,Path(q['test_body'])]\n")
        self.assertIn(needle, coverage_path.read_text())
        coverage_path.write_text(coverage_path.read_text().replace(needle, private_validator, 1))

        substitutions = {
            "binding_contract_task_ancestry": "ROOT.parents[2] -> ROOT.parents[3] for nested private fixture",
            "dependency_checkout_ancestry": "matrix parents[4] -> parents[5] for nested private fixture",
            "qualification_precondition": "sealed private source check; not a real integrated qualification",
            "target_validators_substituted": False,
            "lean_or_container_proof_claimed": False,
        }
        imported = source_binding(tooling)
        evidence_root = fixture_root / "writer-evidence-r12"
        evidence_root.mkdir(mode=0o700, exist_ok=True)
        token = snapshot.name.removeprefix("implementation-r12-cli-")
        q_path = evidence_root / ("PRIVATE_PREP_QUALIFICATION." + token + ".json")
        test_body = Path(__file__).resolve()
        write_json(q_path, {
            "schema": "ep19-r12-private-preparation-qualification-v1",
            "result": "PASS",
            "purpose": "TARGET_VALIDATOR_PATH_ONLY_NOT_INTEGRATED_QUALIFICATION",
            "product_gate_execution": False,
            "formal_attempt": False,
            "shared_preparation": False,
            "source_binding": imported,
            "test_body": str(test_body),
            "test_body_sha256": digest(test_body),
            "substitutions": substitutions,
        })

        fixed_path = evidence_root / ("FIXED29." + token + ".json")
        dependency = evidence_root / ("DEPENDENCY." + token + ".json")
        product_delta = task / "candidate-preparation/native-delta-001/DELTA.json"
        external_delta = continuation / "writer-evidence-r11/IMPLEMENTATION.r10-to-r11.final-002.patch"
        dependency_argv = [str(PYTHON), "-B", str(tooling / "qualification/build_dependency_evidence.py"),
            "--historical-fixed", str(continuation / "writer-evidence-r11/INPUT_FIXED29_CONSUMER_BINDING.r11.candidate-001.json"),
            "--applicability", str(continuation / "writer-evidence-r2/INPUT_CURRENT_APPLICABILITY.json"),
            "--private-map", str(continuation / "private-r12/ELIGIBLE_SKILLS_MAP.private.json"),
            "--private-inventory", str(continuation / "private-r12/STRICT_PACKAGE_INVENTORY.private.json")]
        dependency_builder = (tooling / "qualification/build_dependency_evidence.py").read_text()
        if "product-identity-delta" in dependency_builder:
            dependency_argv += ["--product-identity-delta", str(product_delta),
                                "--external-implementation-delta", str(external_delta)]
        dependency_argv += ["--output-fixed", str(fixed_path),
                            "--output-dependency", str(dependency)]
        built = subprocess.run(dependency_argv, cwd=fixture_root, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=120)
        self.assertEqual(built.returncode, 0, built.stdout.decode(errors="replace"))

        self.assertEqual(digest(product_delta), PRODUCT_DELTA_SHA256)
        control = tooling / "candidate-inputs-v3"
        base_binding = {
            "schema": "ep19-external29-runtime-binding-v1", "root": str(tooling),
            "clone_source": str(task / "checkout"), "candidate": CANDIDATE, "tree": TREE,
            "immediate_parent": PARENT, "canonical_comparison_base": BASE,
            "product_patch_sha256": PRODUCT_PATCH, "control_root": str(control),
            "matrix_sha256": digest(control / "GATE_EXECUTION_MATRIX.json"),
            "inventories": {p.name: digest(p) for p in sorted((control / "inputs").iterdir()) if p.is_file()},
            "run_id": "candidate-formal-002", "owner": str(continuation / "OWNER_AUTHORIZATION.verbatim.txt"),
            "owner_sha256": digest(continuation / "OWNER_AUTHORIZATION.verbatim.txt"),
            "dependency": str(dependency), "dependency_sha256": digest(dependency),
            "qualification": str(q_path), "qualification_sha256": digest(q_path),
            "adapter_qualification": str(tooling / "adapter71-qualification.reused.json"),
            "adapter_qualification_sha256": digest(tooling / "adapter71-qualification.reused.json"),
            "applicability": str(continuation / "writer-evidence-r2/INPUT_CURRENT_APPLICABILITY.json"),
            "applicability_sha256": digest(continuation / "writer-evidence-r2/INPUT_CURRENT_APPLICABILITY.json"),
            "private_map": str(continuation / "private-r12/ELIGIBLE_SKILLS_MAP.private.json"),
            "private_map_sha256": digest(continuation / "private-r12/ELIGIBLE_SKILLS_MAP.private.json"),
            "private_inventory": str(continuation / "private-r12/STRICT_PACKAGE_INVENTORY.private.json"),
            "private_inventory_sha256": digest(continuation / "private-r12/STRICT_PACKAGE_INVENTORY.private.json"),
            "source_binding": imported,
        }
        corrected_contract = "product_identity_delta" in binding_path.read_text()
        if corrected_contract:
            base_binding["schema"] = "ep19-external29-runtime-binding-v2"
            base_binding["product_identity_delta"] = {"path": str(product_delta), "sha256": digest(product_delta)}
            base_binding["external_implementation_delta"] = {"path": str(external_delta), "sha256": digest(external_delta)}
        else:
            base_binding["reviewed_delta"] = {"path": str(external_delta), "sha256": digest(external_delta)}

        run = tooling / "outputs/continuation-runs/candidate-formal-002"
        run.mkdir(parents=True, mode=0o700)
        sentinel = run / "PREEXISTING_PRIVATE_SENTINEL"
        sentinel.write_text("identity validator must finish before this sentinel is reported\n")
        original_run_bytes = sentinel.read_bytes()
        cases_dir = evidence_root / ("CLI_CASES." + token)
        cases_dir.mkdir(mode=0o700)

        def invoke(name, value, supplied_seal=None):
            config = evidence_root / (name + "." + token + ".binding.json")
            write_json(config, value)
            argv = [str(PYTHON), "-B", str(tooling / "executor/external29_driver.py"),
                    "prepare", "--run-id", "candidate-formal-002", "--binding", str(config),
                    "--binding-sha256", supplied_seal or digest(config)]
            started = time.time_ns()
            process = subprocess.run(argv, cwd=fixture_root, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, timeout=120)
            finished = time.time_ns()
            (cases_dir / (name + ".stdout")).write_bytes(process.stdout)
            (cases_dir / (name + ".stderr")).write_bytes(process.stderr)
            try:
                diagnostic = json.loads(process.stderr)
            except Exception:
                diagnostic = None
            receipt = {"case": name, "argv": argv, "native_exit": process.returncode,
                       "started_ns": started, "finished_ns": finished,
                       "stdout_sha256": hashlib.sha256(process.stdout).hexdigest(),
                       "stderr_sha256": hashlib.sha256(process.stderr).hexdigest(),
                       "diagnostic": diagnostic, "run_preexisted": True,
                       "sentinel_unchanged": sentinel.read_bytes() == original_run_bytes,
                       "formal_attempt": False, "product_tests": False,
                       "shared_preparation": False, "shared_probes": False}
            write_json(cases_dir / (name + ".process.json"), receipt)
            return receipt

        positive = invoke("positive-genuine-product-identity", base_binding)
        self.assertEqual(positive["native_exit"], 1)
        self.assertIsNotNone(positive["diagnostic"])
        self.assertEqual(positive["diagnostic"]["error_type"], "FileExistsError")
        self.assertTrue(positive["sentinel_unchanged"])

        # The predecessor fails the preceding assertion with the real missing API.
        # Once corrected, every invalid binding must reject before the sentinel.
        product_key = "product_identity_delta"
        wrong_patch = json.loads(json.dumps(base_binding))
        wrong_patch[product_key] = {"path": str(external_delta), "sha256": digest(external_delta)}
        cases = [("external-patch-in-product-identity", wrong_patch, "JSONDecodeError", None)]
        for label, mutate, expected_reason in (
            ("wrong-product-schema", lambda value: value.__setitem__("schema", "wrong-product-schema"), "DELTA_SCHEMA"),
            ("wrong-product-identity", lambda value: value.__setitem__("candidate", PARENT), "DELTA_CANDIDATE candidate")):
            artifact = evidence_root / (label + "." + token + ".json")
            value = json.loads(product_delta.read_text())
            mutate(value); write_json(artifact, value)
            config = json.loads(json.dumps(base_binding))
            config[product_key] = {"path": str(artifact), "sha256": digest(artifact)}
            cases.append((label, config, "RuntimeError", expected_reason))
        bad_hash = json.loads(json.dumps(base_binding)); bad_hash[product_key]["sha256"] = "0" * 64
        cases.append(("wrong-product-hash", bad_hash, "RuntimeError", "PRODUCT_IDENTITY_DELTA_BINDING_CHANGED"))
        missing = json.loads(json.dumps(base_binding)); missing.pop(product_key)
        cases.append(("missing-product-identity", missing, "RuntimeError", "STRICT_BINDING_SCHEMA"))
        for name, config, error_type, reason in cases:
            receipt = invoke(name, config)
            self.assertEqual(receipt["native_exit"], 1, name)
            self.assertEqual(receipt["diagnostic"]["error_type"], error_type, name)
            if reason:
                hashes = {row["reason_sha256"] for row in receipt["diagnostic"].get("causal_errors", [])}
                self.assertIn(hashlib.sha256(reason.encode()).hexdigest(), hashes, name)
            self.assertTrue(receipt["sentinel_unchanged"], name)

        bad_seal = invoke("wrong-config-seal", base_binding, "0" * 64)
        self.assertEqual(bad_seal["diagnostic"]["error_type"], "RuntimeError")
        self.assertTrue(bad_seal["sentinel_unchanged"])
        write_json(cases_dir / "SUMMARY.json", {
            "result": "PASS", "corrected_contract": corrected_contract,
            "genuine_product_delta": str(product_delta),
            "genuine_product_delta_sha256": digest(product_delta),
            "external_delta": str(external_delta), "external_delta_sha256": digest(external_delta),
            "actual_cli": True, "actual_parser_modules_runner_prepare": True,
            "actual_verify_object_source": True, "actual_identity_delta_validate": True,
            "private_preexisting_run_cutoff": True, "namespace_creation_tested": False,
            "target_validators_substituted": False, "substitutions": substitutions,
        })


if __name__ == "__main__":
    unittest.main()
