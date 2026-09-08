"""Fresh affected-only qualification; historical 129 controls are not rerun."""
from pathlib import Path
import hashlib
import json
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))


class RecordingResult(unittest.TextTestResult):
    def startTest(self, test):
        self.identities.append(test.id())
        super().startTest(test)


class RecordingRunner(unittest.TextTestRunner):
    resultclass = RecordingResult

    def _makeResult(self):
        result = super()._makeResult()
        result.identities = []
        return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    start = time.time()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite([
        loader.loadTestsFromName("test_lean_materialization"),
        loader.loadTestsFromName("test_lean_binding"),
    ])
    runner = RecordingRunner(stream=sys.stdout, verbosity=2)
    result = runner.run(suite)
    identities = result.identities
    if len(identities) != len(set(identities)):
        raise RuntimeError("DUPLICATE_FRESH_TEST_IDENTITY")
    receipt = {
        "schema": "ep19-lean-materialization-fresh-result-v1",
        "result": "PASS" if result.wasSuccessful() else "FAIL",
        "tests": result.testsRun, "pass": result.testsRun - len(result.failures) - len(result.errors),
        "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "unique": len(set(identities)), "duplicates": len(identities) - len(set(identities)),
        "identities": identities, "start": start, "end": time.time(),
        "historical_129_controls_executed": False,
        "product_gate_execution": False,
    }
    output = ROOT / "qualification/FRESH_RESULT.json"
    with output.open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps({key: receipt[key] for key in
                      ("result", "tests", "pass", "failures", "errors", "skipped", "unique", "duplicates")}))
    return int(not result.wasSuccessful())


if __name__ == "__main__":
    raise SystemExit(main())
