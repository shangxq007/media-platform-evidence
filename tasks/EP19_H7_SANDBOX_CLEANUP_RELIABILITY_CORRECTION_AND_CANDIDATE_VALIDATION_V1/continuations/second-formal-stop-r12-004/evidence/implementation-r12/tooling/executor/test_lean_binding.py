from pathlib import Path
import ast
import hashlib
import json
import unittest

import coverage
import execution


ROOT = execution.D
PREIMAGE = ROOT / "preimages/executor-v2"
OLD_QUALIFICATION = ROOT.parent / "bookkeeping-v2-20260908T004809Z/qualification/QUALIFICATION.json"


def component(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text())
    node = next(row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == name)
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


class LeanBindingTests(unittest.TestCase):
    def test_strict_collector_is_byte_unchanged(self):
        self.assertEqual(coverage.digest(execution.H / "preservation.py"),
                         coverage.digest(PREIMAGE / "preservation.py"))

    def test_a_b_c_helpers_are_byte_unchanged(self):
        names = ("namespaces.py", "artifacts.py", "compile_inventory.py",
                 "vite_closure.py", "packaging.py", "freshness.py")
        self.assertEqual(
            {name: coverage.digest(execution.H / name) for name in names},
            {name: coverage.digest(PREIMAGE / name) for name in names},
        )

    def test_sandbox_algorithms_are_unchanged(self):
        for name in ("exact", "frontend_sandbox", "formal_sandbox"):
            self.assertEqual(component(execution.H / "execution.py", name),
                             component(PREIMAGE / "execution.py", name))

    def test_historical_129_controls_remain_historical(self):
        document = json.loads(OLD_QUALIFICATION.read_text())
        self.assertEqual(document["result"], "PASS")
        self.assertEqual(document["tests"], 129)
        self.assertEqual(document["schema"], "ep19-bookkeeping-v2-qualified-v1")
        self.assertTrue(coverage.formal_boundary_qualified(document))
        self.assertTrue(coverage.full_capsule_reuse_qualified(document))

    def test_prepare_materializes_before_prepared_receipt(self):
        source = (execution.H / "runner.py").read_text()
        materialize = source.index("lean_result=lean_preparation.prepare(run)")
        receipt = source.index("put(run/'prepare.json'", materialize)
        self.assertLess(materialize, receipt)

    def test_formal_gate_binds_run_local_lean_and_libraries(self):
        source = (execution.H / "runner.py").read_text()
        self.assertIn("env.update(LEAN=str(lean_root/'bin/lean'),LEAN_PATH=str(lean_root/'lib/lean')", source)
        self.assertIn("LD_LIBRARY_PATH=str(lean_root/'lib')", source)

    def test_hermes_entrypoints_parse_and_execution_is_ordered(self):
        tools = ROOT / "tools"
        for name in ("hermes_review.py", "hermes_execute_once.py", "finalize_report.py",
                     "revalidate_preparation.py"):
            ast.parse((tools / name).read_text())
        execution_source = (tools / "hermes_execute_once.py").read_text()
        self.assertLess(execution_source.index('call("baseline"'),
                        execution_source.index('call("preflight"'))
        self.assertLess(execution_source.index('call("preflight"'),
                        execution_source.index('call("run"'))
        report_source = (tools / "finalize_report.py").read_text()
        for field in ("FAILED_RUN_PRESERVED", "PREPARATION_COLLECTOR_COMPATIBILITY",
                      "ACTUAL_TEST_IDENTITY_ACCOUNTING", "PACK_HISTORICAL_BYTE_IMMUTABILITY",
                      "PUBLIC_MANIFEST_SHA256", "REMOTE_VERIFICATION"):
            self.assertIn('"' + field + '"', report_source)

    def test_native_probe_persists_receipt_before_rejecting(self):
        source = (execution.H / "lean_preparation.py").read_text()
        self.assertLess(source.index("coverage.put(receipt_path, receipt)"),
                        source.index('raise RuntimeError("LEAN_PREPARATION_NATIVE_PROBE_EXCEPTION'))

    def test_failed_v2_run_is_preserved_as_not_run(self):
        stop = json.loads((ROOT / "historical/V2_STOP_CONDITION.json").read_text())
        fields = json.loads((ROOT / "historical/V2_FINAL_FIELDS.json").read_text())
        self.assertEqual(stop["result"], "STOP_INCOMPLETE_STRICT_INPUT_CAPTURE")
        self.assertIs(fields["FORMAL_START_CREATED"], False)
        self.assertEqual(fields["NOT_RUN"], 29)


if __name__ == "__main__":
    unittest.main()
