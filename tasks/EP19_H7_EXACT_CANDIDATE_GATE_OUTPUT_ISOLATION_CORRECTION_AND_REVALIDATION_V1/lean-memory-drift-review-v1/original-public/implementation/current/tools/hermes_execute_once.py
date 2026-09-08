"""Hermes-only one-shot baseline, preflight, launch receipt, and graph execution."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import coverage
import runner

RUN_ID = "lean-materialized-formal-001"


def call(*argv: str) -> None:
    subprocess.run([sys.executable, "-B", str(ROOT / "executor/runner.py"), *argv],
                   cwd=ROOT, check=True)


def endpoint_checks() -> dict:
    bwrap = Path("/usr/bin/bwrap")
    podman = Path("/usr/bin/podman")
    socket = Path("/run/user/1000/podman/podman.sock")
    if not bwrap.is_file() or not os.access(bwrap, os.X_OK):
        raise RuntimeError("BWRAP_ENDPOINT_UNAVAILABLE")
    if not podman.is_file() or not os.access(podman, os.X_OK):
        raise RuntimeError("PODMAN_ENDPOINT_UNAVAILABLE")
    if not socket.is_socket():
        raise RuntimeError("PODMAN_SOCKET_UNAVAILABLE")
    image = "docker.io/coqorg/coq@sha256:e50d77c4c5a9aa0d76ae1b343d79c5f922da3a75054b79c5dc635895438e4674"
    env = dict(os.environ)
    env.update(XDG_RUNTIME_DIR="/run/user/1000",
               CONTAINER_HOST="unix:///run/user/1000/podman/podman.sock")
    observed = subprocess.check_output([str(podman), "image", "inspect", image,
                                        "--format", "{{.Id}}"], env=env, text=True).strip()
    expected = "b80d66c91b4da3a1b3c5d3e6672cf8f4ab72ed2f7a6a1f0cf7d3aef747cf6a4b"
    if observed != expected:
        raise RuntimeError("COQ_IMAGE_IDENTITY_MISMATCH")
    return {"bwrap": str(bwrap), "podman": str(podman), "socket": str(socket),
            "coq_image": image, "coq_image_id": observed, "result": "PASS"}


def main() -> int:
    run = runner.runpath(RUN_ID)
    if (run / "baseline.json").exists() or (run / "runtime/START.json").exists():
        raise RuntimeError("ONE_SHOT_NAMESPACE_ALREADY_CONSUMED")
    # Fail before baseline when a current external endpoint is unavailable.
    endpoints = endpoint_checks()
    print(json.dumps({"external_endpoints": endpoints}, indent=2), flush=True)
    call("baseline", "--run-id", RUN_ID)
    if not (run / "seal.json").is_file():
        raise RuntimeError("BASELINE_DID_NOT_CREATE_SEAL")
    call("preflight", "--run-id", RUN_ID)
    preflight = json.loads((run / "preflight.json").read_text())
    if preflight.get("result") != "ENGINEERING_READY" or preflight.get("engineering_blockers") != []:
        print(json.dumps({"result": "STOP_PREFLIGHT_BLOCKED",
                          "engineering_blockers": preflight.get("engineering_blockers")}, indent=2))
        return 2
    executor = runner.verify_executor_identity()
    qualification = Path(json.loads((run / "prepare.json").read_text())["qualification"])
    policy = run / "bookkeeping-policy-v2.private.json"
    receipt = {
        "run_id": run.name, "candidate": runner.SHA, "tree": runner.TREE, "base": runner.BASE,
        "engineering_execution_authorization": "OWNER_AUTHORIZED",
        "owner_decision_sha256": runner.OWNER_SHA256,
        "owner_contract_version": runner.OWNER_CONTRACT_VERSION,
        "executor_identity": executor["identity"],
        "bookkeeping_policy_sha256": coverage.digest(policy),
        "qualification_sha256": coverage.digest(qualification),
        "independent_review": "PENDING", **runner.REVIEW_STATES,
        "seal_sha256": coverage.digest(run / "seal.json"),
        "preflight_sha256": coverage.digest(run / "preflight.json"),
        "external_endpoint_check": endpoints,
    }
    review = run / "engineering-launch.json"
    coverage.put(review, receipt)
    # runner.run_all performs a fresh preflight and PRESTART comparison before START.
    call("run", "--run-id", RUN_ID, "--review", str(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
