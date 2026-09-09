"""Parent-observed focused runner with immutable pre/post source snapshots."""
from pathlib import Path
import argparse, hashlib, json, os, re, subprocess, sys, time

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def manifest(roots):
    rows = {}
    for root in map(Path, roots):
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rows[str(path.absolute())] = digest(path)
    return rows

def snapshot(roots, destination):
    """Copy every bound source byte before/after execution, then hash the copies."""
    destination = Path(destination)
    destination.mkdir(mode=0o700)
    rows = {}
    for label, root in roots:
        root = Path(root).absolute()
        for source in sorted(root.rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            relative = source.relative_to(root)
            target = destination / label / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            exclusive(target, source.read_bytes(), raw=True)
            rows[str(source)] = {"source_sha256": digest(source),
                                 "snapshot": str(target.absolute()),
                                 "snapshot_sha256": digest(target)}
    exclusive(destination / "SOURCE_SNAPSHOT.json", {
        "schema": "ep19-r9-immutable-source-snapshot-v1", "files": rows})
    return rows

def exclusive(path, payload, *, raw=False):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    body = payload if raw else (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        view = memoryview(body)
        while view:
            count = os.write(fd, view)
            if count <= 0: raise OSError("ZERO_RECEIPT_WRITE")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tested-tooling", type=Path, required=True)
    p.add_argument("--test-root", type=Path, required=True)
    p.add_argument("--test-module", required=True)
    p.add_argument("--fixture-root", type=Path, required=True)
    p.add_argument("--dependency-binding", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); tested = a.tested_tooling.absolute(); tests = a.test_root.absolute()
    output = a.output.absolute(); output.mkdir(parents=True, mode=0o700)
    a.fixture_root.mkdir(parents=True, mode=0o700)
    dependency = a.dependency_binding.absolute(); roots = [tested / "executor", tests]
    named_roots = [("executor", roots[0]), ("qualification", roots[1])]
    before = manifest(roots); dependency_before = digest(dependency)
    snapshot_before = snapshot(named_roots, output / "sources.before")
    argv = [sys.executable, "-B", "-m", "unittest", "-v", a.test_module]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "EP19_TEST_EXECUTOR_ROOT": str(tested / "executor"),
           "EP19_TEST_TOOLING_ROOT": str(tested),
           "EP19_QUALIFICATION_FIXTURE_ROOT": str(a.fixture_root.absolute())}
    started_wall = time.time_ns(); started_mono = time.monotonic_ns()
    process = subprocess.Popen(argv, cwd=tests, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, start_new_session=True)
    child_pid = process.pid
    parent_pid_namespace = os.readlink("/proc/self/ns/pid")
    child_pid_namespace = os.readlink(f"/proc/{child_pid}/ns/pid")
    stdout, _ = process.communicate(timeout=120)
    finished_mono = time.monotonic_ns(); finished_wall = time.time_ns()
    after = manifest(roots); dependency_after = digest(dependency)
    snapshot_after = snapshot(named_roots, output / "sources.after")
    stable = before == after and dependency_before == dependency_after
    exclusive(output / "NATIVE.log", stdout, raw=True)
    pattern = re.compile(r"^(\S+) \(([^)]+)\) \.\.\. (ok|FAIL|ERROR|skipped.*)$")
    prefix = re.compile(r"^(\S+) \(([^)]+)\) \.\.\. ")
    status_only = re.compile(r"^(ok|FAIL|ERROR|skipped.*)$")
    controls = []; pending_identity = None
    for line in stdout.decode(errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            _method, identity, status = match.groups()
            controls.append({"id": identity, "actual": "PASS" if status == "ok" else
                             "FAIL" if status == "FAIL" else "ERROR" if status == "ERROR" else "SKIP"})
            pending_identity = None
            continue
        started = prefix.match(line)
        if started:
            pending_identity = started.group(2)
            continue
        completed = status_only.match(line)
        if completed and pending_identity:
            status = completed.group(1)
            controls.append({"id": pending_identity, "actual": "PASS" if status == "ok" else
                             "FAIL" if status == "FAIL" else "ERROR" if status == "ERROR" else "SKIP"})
            pending_identity = None
    snapshot_stable = ({path: row["snapshot_sha256"] for path, row in snapshot_before.items()} ==
                       {path: row["snapshot_sha256"] for path, row in snapshot_after.items()} == before == after)
    stable = stable and snapshot_stable
    result = {"schema": "ep19-r9-focused-result-v1",
              "result": "PASS" if process.returncode == 0 and stable else "FAIL",
              "native_exit": process.returncode, "source_binding_stable": stable,
              "native_status": "PASS" if process.returncode == 0 else "FAIL",
              "controls": controls, "raw_log": str((output / "NATIVE.log").absolute()),
              "process_receipt": str((output / "PROCESS.json").absolute()),
              "formal_attempt": False, "product_tests": False, "product_gate_execution": False,
              "fixture_only": True}
    exclusive(output / "RESULT.json", result)
    receipt = {"schema": "ep19-r9-parent-process-v1", "argv": argv, "cwd": str(tests),
               "pid": child_pid, "native_exit": process.returncode, "wrapper_exit": 0 if stable else 125,
               "native_status": "PASS" if process.returncode == 0 else "FAIL",
               "wrapper_status": "PASS" if stable else "FAIL",
               "parent_pid_namespace": parent_pid_namespace,
               "child_pid_namespace": child_pid_namespace,
               "started_wall_ns": started_wall, "finished_wall_ns": finished_wall,
               "started_monotonic_ns": started_mono, "finished_monotonic_ns": finished_mono,
               "duration_seconds": (finished_mono - started_mono) / 1e9,
               "raw_log": str((output / "NATIVE.log").absolute()),
               "raw_log_sha256": digest(output / "NATIVE.log"),
               "result_receipt": str((output / "RESULT.json").absolute()),
               "result_sha256": digest(output / "RESULT.json"),
               "control_ids": [row["id"] for row in controls],
               "control_statuses": {row["id"]: row["actual"] for row in controls},
               "tested_tooling": str(tested), "dependency_binding": str(dependency),
               "dependency_sha256_before": dependency_before,
               "dependency_sha256_after": dependency_after,
               "source_binding_before": before, "source_binding_after": after,
               "source_binding_stable": stable, "source_snapshot_before": snapshot_before,
               "source_snapshot_after": snapshot_after,
               "source_snapshot_stable": snapshot_stable, "fresh_replay": True,
               "historical_execution_bytes_claimed": False, "formal_attempt": False,
               "product_tests": False, "shared_preparation": False, "shared_probes": False,
               "shared_baseline": False}
    exclusive(output / "PROCESS.json", receipt)
    sys.stdout.buffer.write(stdout)
    return process.returncode if stable else 125

if __name__ == "__main__": raise SystemExit(main())
