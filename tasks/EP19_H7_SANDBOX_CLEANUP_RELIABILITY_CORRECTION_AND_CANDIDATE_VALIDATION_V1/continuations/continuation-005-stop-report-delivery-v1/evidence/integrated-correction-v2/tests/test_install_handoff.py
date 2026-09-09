import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "parent-handoff" / "INSTALL_AFTER_COORDINATION_AND_REVIEW.py"
SPEC = importlib.util.spec_from_file_location("install_handoff", SCRIPT)
installer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(installer)


class InstallHandoffTests(unittest.TestCase):
    def test_real_manifest_binds_installer_candidates_and_expected_before(self):
        manifest_path = SCRIPT.parent / "INSTALL_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["installer_sha256"], installer.digest(SCRIPT))
        self.assertEqual(3, len(manifest["targets"]))
        for item in manifest["targets"]:
            self.assertEqual(item["candidate_sha256"], installer.digest(Path(item["candidate"])))
            self.assertEqual(item["original_sha256"], installer.digest(Path(item["target"])))

    def test_unknown_overwrite_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.py"
            candidate = root / "candidate.py"
            target.write_bytes(b"unknown")
            candidate.write_bytes(b"after")
            manifest = {"targets": [{"target": str(target), "candidate": str(candidate), "original_sha256": installer.digest_bytes(b"before"), "candidate_sha256": installer.digest(candidate)}]}
            with self.assertRaises(installer.InstallError):
                installer.install_targets(manifest, root / "journal.json")
            self.assertEqual(b"unknown", target.read_bytes())

    def test_interrupted_install_replays_to_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            targets = []
            for index in range(3):
                target = root / f"target-{index}"
                candidate = root / f"candidate-{index}"
                target.write_bytes(f"before-{index}".encode())
                candidate.write_bytes(f"after-{index}".encode())
                targets.append({"target": str(target), "candidate": str(candidate), "original_sha256": installer.digest(target), "candidate_sha256": installer.digest(candidate)})
            manifest = {"targets": targets}
            journal = root / "journal.json"
            with self.assertRaises(installer.InjectedInstallFault):
                installer.install_targets(manifest, journal, fault_after=1)
            self.assertTrue(journal.exists())
            result = installer.install_targets(manifest, journal)
            self.assertEqual("INSTALLED_OR_IDENTICAL", result["status"])
            self.assertFalse(journal.exists())
            for item in targets:
                self.assertEqual(item["candidate_sha256"], installer.digest(Path(item["target"])))

    def test_recovery_journal_must_match_exact_manifest_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); target = root / "target"; candidate = root / "candidate"
            target.write_bytes(b"before"); candidate.write_bytes(b"after")
            manifest = {"targets": [{"target": str(target), "candidate": str(candidate),
                "original_sha256": installer.digest(target), "candidate_sha256": installer.digest(candidate)}]}
            journal = root / "journal.json"
            with self.assertRaises(installer.InjectedInstallFault):
                installer.install_targets(manifest, journal, fault_after=1)
            value = json.loads(journal.read_text()); value["targets"][0]["target"] = str(root / "other")
            journal.write_text(json.dumps(value) + "\n")
            with self.assertRaises(installer.InstallError):
                installer.install_targets(manifest, journal)

    def test_no_existing_maintenance_coordination_fails_closed_before_install(self):
        status = installer.assess_existing_maintenance_coordination()
        self.assertEqual("BLOCKED_MISSING_EXISTING_COORDINATION_MECHANISM", status["status"])
        self.assertFalse(status["install_permitted"])

    def test_review_body_not_environment_controls_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = {"patch_sha256": "a" * 64, "installer_sha256": "c" * 64, "targets": [{"target": "/exact", "candidate_sha256": "b" * 64}]}
            review = root / "review.json"
            review.write_text(json.dumps({"schema": "ep19-original-controller-independent-review-v1", "decision": "REJECTED", "approved": False, "install_authorized": False, "reviewer_role": "INDEPENDENT_TECHNICAL_REVIEWER", "patch_sha256": "a" * 64, "reviewed_targets": [{"path": "/exact", "candidate_sha256": "b" * 64}]}) + "\n")
            with self.assertRaises(installer.InstallError):
                installer.load_verified_review(review, installer.digest(review), manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)
