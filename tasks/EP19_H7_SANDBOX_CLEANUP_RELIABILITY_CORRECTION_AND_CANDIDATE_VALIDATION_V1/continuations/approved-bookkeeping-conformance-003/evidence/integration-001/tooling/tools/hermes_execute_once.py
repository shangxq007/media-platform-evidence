"""Hermes-only one-shot baseline, preflight, launch receipt, and graph execution."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import coverage
import runner
import sequence

RUN_ID = os.environ.get("H7_RUN_ID")  # explicit, validated against the sealed two-name set


def call(*argv: str) -> None:
    run=runner.runpath(RUN_ID);folder=run/'runtime/orchestration'
    folder.mkdir(mode=0o700,exist_ok=True)
    log=folder/(argv[0]+'.native.log');started=time.time_ns()
    command=[sys.executable,'-B',str(ROOT/'executor/runner.py'),*argv]
    with log.open('xb') as stream:
        process=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        code=process.wait();stream.flush();os.fsync(stream.fileno())
    sequence.durable(folder/(argv[0]+'.process.json'),{'argv':command,'pid':process.pid,'native_exit':code,
        'started_ns':started,'finished_ns':time.time_ns(),'raw_log':str(log),'log_sha256':coverage.digest(log)})
    if code:raise subprocess.CalledProcessError(code,command)


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
    attempt=sequence.consume(run,'launcher')
    disposition,endpoints=sequence.verify(run)
    print(json.dumps({'prepared_external_endpoints':endpoints,'preparation_disposition_sha256':coverage.digest(run/'PREPARATION_DISPOSITION.json')}),flush=True)
    call("baseline", "--run-id", RUN_ID, "--launcher-attempt",attempt["attempt_id"])
    if not (run / "seal.json").is_file():
        raise RuntimeError("BASELINE_DID_NOT_CREATE_SEAL")
    sequence.verify(run)
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
    sequence.verify(run)
    call("run", "--run-id", RUN_ID, "--review", str(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
