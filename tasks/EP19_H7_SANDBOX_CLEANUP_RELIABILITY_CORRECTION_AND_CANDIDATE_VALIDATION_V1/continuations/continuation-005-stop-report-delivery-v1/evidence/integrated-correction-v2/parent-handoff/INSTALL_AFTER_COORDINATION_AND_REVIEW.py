#!/usr/bin/env python3
"""Expected-before installer for the reviewed original controller correction.

This entry is intentionally outside the enabled Skill. It installs only the
three exact original targets after parsing a machine review, then invokes the
installed canonical controller for recovery/registration/readback. It is not a
queue or ledger writer itself.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "INSTALL_MANIFEST.json"
JOURNAL = HERE / ".original-controller-install-transaction.json"


class InstallError(RuntimeError):
    pass


class InjectedInstallFault(RuntimeError):
    pass


def assess_existing_maintenance_coordination() -> dict[str, Any]:
    """Report the discovered original coordination capability without inventing one.

    The enabled Skill exposes only its publication-slot/state locks. Neither is
    an installation/consumer-quiescence authority and an old process would not
    observe a newly invented task-local lock. Therefore shared activation must
    remain disabled until the original manager supplies such a mechanism.
    """
    return {
        "status": "BLOCKED_MISSING_EXISTING_COORDINATION_MECHANISM",
        "install_permitted": False,
        "missing": "original manager interlock covering all controller consumers and all three targets for the complete check/replace/recovery window",
        "publication_slot_is_maintenance_authority": False,
        "task_local_lock_accepted": False,
    }


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def atomic_write(path: Path, data: bytes, mode: int | None = None) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def load_verified_review(path: Path, expected_sha256: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file() or digest(path) != expected_sha256:
        raise InstallError("independent review path/digest mismatch")
    review = json.loads(path.read_text(encoding="utf-8"))
    exact = {
        "schema": "ep19-original-controller-independent-review-v1",
        "decision": "APPROVED", "approved": True, "install_authorized": True,
        "reviewer_role": "INDEPENDENT_TECHNICAL_REVIEWER",
        "patch_sha256": manifest["patch_sha256"],
        "installer_sha256": manifest["installer_sha256"],
        "install_manifest_sha256": digest_bytes(canonical(manifest)),
    }
    for field, expected in exact.items():
        if review.get(field) != expected:
            raise InstallError(f"independent machine review does not approve exact {field}")
    reviewed = review.get("reviewed_targets")
    expected_targets = [{"path": item["target"], "candidate_sha256": item["candidate_sha256"]} for item in manifest["targets"]]
    if reviewed != expected_targets:
        raise InstallError("independent review target identities differ from install manifest")
    return review


def install_targets(manifest: dict[str, Any], journal_path: Path, fault_after: int | None = None) -> dict[str, Any]:
    targets = manifest["targets"]
    if journal_path.exists():
        journal = json.loads(journal_path.read_text(encoding="utf-8"))
        if journal.get("schema") != "ep19-original-controller-install-transaction-v1" or journal.get("manifest_sha256") != digest_bytes(canonical(manifest)):
            raise InstallError("unknown or stale installation recovery journal")
        if not isinstance(journal.get("targets"), list) or len(journal["targets"]) != len(targets):
            raise InstallError("installation recovery journal target count differs from manifest")
        for item, row in zip(targets, journal["targets"]):
            candidate = Path(item["candidate"])
            if not candidate.is_file() or digest(candidate) != item["candidate_sha256"]:
                raise InstallError("manifest candidate bytes are absent or changed during recovery")
            payload = candidate.read_bytes()
            exact = {"target": item["target"], "before_sha256": item["original_sha256"],
                     "after_sha256": item["candidate_sha256"],
                     "after_base64": base64.b64encode(payload).decode("ascii")}
            if any(row.get(key) != value for key, value in exact.items()) or set(row) != set(exact) | {"mode"} or not isinstance(row.get("mode"), int):
                raise InstallError("installation recovery journal row differs from exact manifest")
    else:
        rows = []
        for item in targets:
            target = Path(item["target"])
            candidate = Path(item["candidate"])
            if not target.is_file() or not candidate.is_file():
                raise InstallError(f"install target/candidate is absent: {target}")
            candidate_bytes = candidate.read_bytes()
            if digest_bytes(candidate_bytes) != item["candidate_sha256"]:
                raise InstallError(f"candidate bytes differ from manifest: {candidate}")
            current = digest(target)
            if current not in {item["original_sha256"], item["candidate_sha256"]}:
                raise InstallError(f"unknown target bytes; overwrite denied: {target}")
            rows.append({
                "target": str(target), "before_sha256": item["original_sha256"],
                "after_sha256": item["candidate_sha256"],
                "after_base64": base64.b64encode(candidate_bytes).decode("ascii"),
                "mode": target.stat().st_mode & 0o777,
            })
        journal = {
            "schema": "ep19-original-controller-install-transaction-v1", "authority": False,
            "manifest_sha256": digest_bytes(canonical(manifest)), "targets": rows,
        }
        atomic_write(journal_path, canonical(journal), 0o600)
    for index, row in enumerate(journal["targets"], 1):
        target = Path(row["target"])
        current = digest(target)
        if current not in {row["before_sha256"], row["after_sha256"]}:
            raise InstallError(f"target changed outside interrupted install: {target}")
        if current != row["after_sha256"]:
            payload = base64.b64decode(row["after_base64"], validate=True)
            if digest_bytes(payload) != row["after_sha256"]:
                raise InstallError("installation journal candidate payload is corrupt")
            atomic_write(target, payload, row["mode"])
        if fault_after == index:
            raise InjectedInstallFault(f"synthetic interruption after target {index}")
    if any(digest(Path(row["target"])) != row["after_sha256"] for row in journal["targets"]):
        raise InstallError("installed target readback mismatch")
    journal_path.unlink()
    return {"status": "INSTALLED_OR_IDENTICAL", "target_count": len(journal["targets"])}


def run_controller(controller: Path, arguments: list[str]) -> dict[str, Any]:
    process = subprocess.run([sys.executable, "-B", str(controller), *arguments], text=True, capture_output=True, check=False)
    if process.returncode != 0:
        raise InstallError(f"canonical controller rejected operation rc={process.returncode}: {process.stdout.strip()} {process.stderr.strip()}")
    value = json.loads(process.stdout)
    if not isinstance(value, dict):
        raise InstallError("canonical controller output is not an object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-verdict", required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--admission-path", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--expected-queue-sha256", required=True)
    parser.add_argument("--expected-ledger-sha256", required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("installer_sha256") != digest(Path(__file__)):
            raise InstallError("installer bytes differ from install manifest")
        load_verified_review(Path(args.review_verdict), args.review_sha256, manifest)
        coordination = assess_existing_maintenance_coordination()
        if coordination["install_permitted"] is not True:
            raise InstallError(coordination["status"] + ": " + coordination["missing"])
        installed = install_targets(manifest, JOURNAL)
        controller = Path(manifest["targets"][0]["target"])
        state_root = Path(args.state_root)
        if (state_root / ".canonical-publication-state-transaction.json").exists():
            run_controller(controller, ["recover-state", "--state-root", str(state_root)])
        registration = run_controller(controller, [
            "register-ep19-successor", "--state-root", str(state_root),
            "--evidence-path", args.admission_path, "--evidence-sha256", args.admission_sha256,
            "--idempotency-key", args.idempotency_key, "--actor", args.actor, "--timestamp", args.timestamp,
            "--expected-queue-sha256", args.expected_queue_sha256,
            "--expected-ledger-sha256", args.expected_ledger_sha256,
        ])
        readback = run_controller(controller, ["inspect-ep19-successor", "--state-root", str(state_root)])
        if readback.get("COMMITTED") is not True:
            raise InstallError("successor registration readback is not committed")
        print(json.dumps({"install": installed, "registration": registration, "readback": readback}, sort_keys=True, indent=2))
        return 0
    except (InstallError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REJECTED", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
