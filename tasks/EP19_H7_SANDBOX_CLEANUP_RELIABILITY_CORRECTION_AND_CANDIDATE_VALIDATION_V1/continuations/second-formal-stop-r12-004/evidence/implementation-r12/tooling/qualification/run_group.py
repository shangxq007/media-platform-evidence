"""Persist a native unittest group log plus process/result receipts."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        view = memoryview(raw)
        while view:
            view = view[os.write(fd, view):]
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", required=True)
    parser.add_argument("--module", default="test_conformance_corrections")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, mode=0o700)
    args.fixture_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = {**os.environ, "EP19_QUALIFICATION_FIXTURE_ROOT": str(args.fixture_root.absolute()),
           "PYTHONDONTWRITEBYTECODE": "1"}
    argv = [sys.executable, "-B", "-m", "unittest", "-v",
            args.module + "." + args.group]
    started_wall = time.time_ns()
    started_mono = time.monotonic_ns()
    process = subprocess.run(argv, cwd=Path(__file__).parent, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finished_mono = time.monotonic_ns()
    finished_wall = time.time_ns()
    log = args.output / "NATIVE.log"
    write(log, process.stdout)
    result = {"schema": "ep19-conformance-group-result-v1", "group": args.group,
              "result": "PASS" if process.returncode == 0 else "FAIL",
              "native_exit": process.returncode, "expected_phase": "RED_OR_GREEN",
              "formal_attempt": False, "product_tests": False,
              "shared_probes": False, "shared_preparation": False, "formal_baseline": False}
    write(args.output / "RESULT.json", (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())
    receipt = {"schema": "ep19-conformance-group-process-v1", "argv": argv,
               "group": args.group, "native_exit": process.returncode,
               "started_wall_ns": started_wall, "finished_wall_ns": finished_wall,
               "started_monotonic_ns": started_mono, "finished_monotonic_ns": finished_mono,
               "duration_seconds": (finished_mono - started_mono) / 1e9,
               "log": str(log.absolute()), "log_sha256": hashlib.sha256(process.stdout).hexdigest(),
               "formal_attempt": False, "product_tests": False}
    write(args.output / "PROCESS.json", (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    sys.stdout.buffer.write(process.stdout)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
