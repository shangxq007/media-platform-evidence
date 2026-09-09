"""Run-local Lean preparation and non-gate native compatibility probe."""
from pathlib import Path
import ast
import hashlib
import inspect
import json
import os
import subprocess
import shutil
import time

import coverage
import execution
import lean_materialization
from preservation import Collector


PREFERRED = (execution.O / "owner-clarified-execution-20260907T1120Z" /
             "prepared-tools/lean-4.19.0-linux")
RAW = Path("USER_HOME/Documents/workspace/audit-runs/"
           "EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/"
           "formal-tools/lean-4.19.0-linux")
HISTORICAL = execution.HISTORICAL_D / "inputs/LEAN_CACHE_MATERIALIZATION.historical.json"
LEAN_SHA256 = "92c3d35b5bfaa5e0fea413a775d504cf46cd95e1345df61c2274f76779e7e023"


def _collector_identity() -> dict:
    source = inspect.getsource(Collector)
    parsed = ast.parse(source)
    return {
        "module": str(Path(inspect.getsourcefile(Collector)).resolve()),
        "module_sha256": coverage.digest(Path(inspect.getsourcefile(Collector)).resolve()),
        "collector_ast_sha256": hashlib.sha256(
            ast.dump(parsed, include_attributes=False).encode()
        ).hexdigest(),
        "class": "preservation.Collector",
        "policy": "UNCHANGED_STRICT_COLLECTOR; SYMLINK/SPECIAL/UNSTABLE CAPTURE REJECTS",
    }


def _native(argv: list[str], cwd: Path, env: dict[str, str], output: Path) -> dict:
    start = time.time()
    native_exit = None
    failure = None
    try:
        with output.open("xb") as stream:
            process = subprocess.run(argv, cwd=cwd, env=env, stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=120)
        native_exit = process.returncode
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
    receipt = {
        "argv": argv, "cwd": str(cwd), "native_exit": native_exit,
        "start": start, "end": time.time(), "raw_log": str(output),
        "log_sha256": coverage.digest(output) if output.is_file() else None,
        "synthetic_preparation_probe": True, "product_gate": False,
        "failure": failure,
    }
    receipt_path = output.with_suffix(output.suffix + ".process.json")
    coverage.put(receipt_path, receipt)
    if failure is not None:
        raise RuntimeError("LEAN_PREPARATION_NATIVE_PROBE_EXCEPTION " + json.dumps(failure))
    if native_exit != 0:
        raise RuntimeError("LEAN_PREPARATION_NATIVE_PROBE_FAILED " + output.read_text(errors="replace"))
    receipt["process_receipt"] = str(receipt_path)
    return receipt


def _resolved_runtime_tools() -> list[Path]:
    result = []
    for name in ("python3", "git", "java", "javac", "node", "npm", "npx", "bash", "bwrap", "podman"):
        found = shutil.which(name)
        if not found:
            raise RuntimeError("MISSING_PREPARATION_RUNTIME_TOOL " + name)
        resolved = Path(found).resolve(strict=True)
        if not resolved.is_file() or resolved.is_symlink():
            raise RuntimeError("INVALID_PREPARATION_RUNTIME_TOOL " + name)
        result.append(resolved)
    return sorted(set(result))


def prepare(run: Path) -> dict:
    run = Path(run).absolute()
    destination = run / "runtime/cache/backend/formal-tools/lean-4.19.0-linux"
    materialization = lean_materialization.materialize(
        PREFERRED, destination, HISTORICAL, raw_corroboration=RAW
    )
    if materialization["selected_source"] != "PREFERRED_HISTORICAL_MATERIALIZED":
        raise RuntimeError("PREFERRED_LEAN_SOURCE_NOT_SELECTED")
    lean = destination / "bin/lean"
    if coverage.digest(lean) != LEAN_SHA256:
        raise RuntimeError("LEAN_BINARY_PIN_MISMATCH")
    coverage.put(run / "lean-materialization.json", materialization)

    init_root = run / "runtime/cache/backend/gradle/init.d"
    tools = _resolved_runtime_tools()
    expected = [str(destination / row["path"]) for row in materialization["file_manifest"]]
    expected += [str(init_root / "ep19-packaging.gradle"), *map(str, tools)]
    collector = Collector(roots=[destination, init_root], files=tools,
                          expected_nonempty=[destination, init_root],
                          expected_files=expected).capture()
    coverage.put(run / "preparation-collector.json", collector)
    if collector["result"] != "COMPLETE" or collector["hashed"] != len(set(expected)):
        raise RuntimeError("STRICT_COLLECTOR_PREPARATION_INCOMPATIBLE " + repr(collector["errors"]))

    probe_dir = run / "runtime/tmp/backend/lean-preparation-probe"
    probe_dir.mkdir(parents=True, exist_ok=False)
    source = probe_dir / "PreparationProbe.lean"
    source.write_text(
        "import Lean\n"
        "open Lean\n"
        "theorem materialized_toolchain_reflexive (n : Nat) : n = n := by rfl\n",
        encoding="utf-8",
    )
    output = probe_dir / "PreparationProbe.olean"
    env = execution.environment("backend", run)
    env.update({
        "LEAN": str(lean),
        "LEAN_PATH": str(destination / "lib/lean"),
        "LD_LIBRARY_PATH": str(destination / "lib"),
    })
    probes = []
    commands = [
        ("version", [str(lean), "--version"]),
        ("prefix", [str(lean), "--print-prefix"]),
        ("import-compile-proof", [str(lean), "--root=" + str(probe_dir),
                                  "-o", str(output), str(source)]),
    ]
    for name, command in commands:
        # Use the unchanged formal boundary wrapper, an absolute Lean path, and
        # explicit library variables. This is a preparation probe, not FORMAL.
        argv = execution.formal_sandbox(command, probe_dir, run, env)
        receipt = _native(argv, probe_dir, env, probe_dir / (name + ".native.log"))
        receipt["name"] = name
        receipt["lean_absolute"] = str(lean)
        receipt["lean_sha256"] = LEAN_SHA256
        receipt["LEAN_PATH"] = env["LEAN_PATH"]
        receipt["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH"]
        probes.append(receipt)
    if "version 4.19.0" not in (probe_dir / "version.native.log").read_text():
        raise RuntimeError("LEAN_VERSION_OUTPUT_MISMATCH")
    prefix = (probe_dir / "prefix.native.log").read_text().strip()
    if Path(prefix) != destination:
        raise RuntimeError("LEAN_LIBRARY_PREFIX_NOT_RUN_LOCAL " + prefix)
    if not output.is_file() or output.stat().st_size <= 0:
        raise RuntimeError("LEAN_PROBE_OUTPUT_MISSING")

    # Ensure the probe did not mutate any frozen tool input.
    post = lean_materialization.inspect_tree(destination, allow_file_links=False)
    if lean_materialization._projection(post) != lean_materialization._projection(
            {"files": materialization["file_manifest"]}):
        raise RuntimeError("LEAN_TOOLCHAIN_CHANGED_BY_PROBE")
    result = {
        "schema": "ep19-lean-preparation-compatibility-v1", "result": "PASS",
        "run_id": run.name, "candidate": execution.SHA, "tree": execution.TREE,
        "base": execution.BASE, "formal_gate_execution": False,
        "lean_source_selected": str(PREFERRED),
        "lean_source_identity_verified": True,
        "materialization_performed": True,
        "run_local_toolchain_verified": True,
        "disallowed_symlink_count": post["symlink_count"],
        "strict_collector": {"result": collector["result"], "hashed": collector["hashed"],
                             "identity": _collector_identity()},
        "full_strict_tool_input_set": {
            "roots": [str(destination), str(init_root)],
            "resolved_runtime_binaries": [{"path": str(path), "sha256": coverage.digest(path)} for path in tools],
            "lean_files": 4617, "expected_files": len(set(expected)),
            "captured_files": collector["hashed"], "capture_result": collector["result"],
        },
        "native_toolchain_probe_results": {
            "result": "PASS", "version": "4.19.0", "library_prefix": prefix,
            "explicit_lean": str(lean), "explicit_LEAN_PATH": env["LEAN_PATH"],
            "explicit_LD_LIBRARY_PATH": env["LD_LIBRARY_PATH"],
            "system_fallback": False, "receipts": probes,
            "output": str(output), "output_sha256": coverage.digest(output),
        },
        "historical_counting_method": materialization["historical_verification"]["counting_method"],
        "raw_link_chains_verified": materialization["raw_corroboration"],
        "preparation_compatibility_not_baseline": True,
        "baseline_created": False, "seal_created": False, "preflight_result": "NOT_RUN",
    }
    coverage.put(run / "PREPARATION_COMPATIBILITY.json", result)
    return result
