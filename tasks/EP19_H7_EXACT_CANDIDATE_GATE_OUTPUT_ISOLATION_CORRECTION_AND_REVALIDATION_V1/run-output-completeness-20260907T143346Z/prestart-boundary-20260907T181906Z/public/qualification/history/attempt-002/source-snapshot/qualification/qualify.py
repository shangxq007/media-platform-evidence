#!/usr/bin/env python3
"""Run/verify bounded diagnostics controls; never prepares or launches a product run."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with path.open('x') as file:
        json.dump(value, file, indent=2); file.write('\n')


def inputs():
    return sorted([*filter(Path.is_file, (ROOT/'executor').iterdir()),
                   *filter(Path.is_file, (ROOT/'preimages/executor').iterdir()),
                   ROOT/'CODEX_BRIEF.md', ROOT/'SCOPE.md',
                   ROOT/'qualification/test_decisions.py', ROOT/'qualification/qualify.py',
                   ROOT/'qualification/CONTROLS.md', ROOT/'qualification/PARENT_COMMANDS.md'])


def verify(out):
    manifest = json.loads((out/'qualification.json').read_text())
    if (manifest.get('schema') != 'ep19-external-diagnostics-qualification-v1' or
            manifest.get('result') != 'PASS' or manifest.get('product_gate_execution') is not False):
        raise RuntimeError('DIAGNOSTIC_QUALIFICATION_NOT_PASS')
    if set(manifest['source_inputs']) != set(map(str, inputs())):
        raise RuntimeError('QUALIFICATION_SOURCE_UNIVERSE_CHANGED')
    for path, wanted in {**manifest['source_inputs'], **manifest['evidence']}.items():
        if sha(path) != wanted:
            raise RuntimeError('QUALIFICATION_DEPENDENCY_CHANGED '+path)
    required = {str(out/p) for p in ('native.log', 'process.json', 'test-results.json', 'source.diff')}
    if not required <= set(manifest['evidence']):
        raise RuntimeError('QUALIFICATION_EVIDENCE_MISSING')
    process = json.loads((out/'process.json').read_text())
    result = json.loads((out/'test-results.json').read_text())
    if process['native_exit'] != 0 or process['log_sha256'] != sha(out/'native.log'):
        raise RuntimeError('QUALIFICATION_NATIVE_OR_LOG_REJECT')
    if (result['result'] != 'PASS' or result['tests'] <= 0 or
            result['failures'] or result['errors'] or result['skipped'] or
            len(result['controls']) != result['tests'] or
            any(row['result'] != 'PASS' for row in result['controls'])):
        raise RuntimeError('QUALIFICATION_TEST_RESULT_REJECT')
    print(json.dumps({'result':'PASS', 'tests':result['tests'], 'output_dir':str(out),
                      'product_gate_execution':False, 'qualification':'external diagnostics only'}))
    return 0


def run(out):
    if not out.is_absolute() or out.resolve() != out or not out.is_relative_to(ROOT/'qualification/runs'):
        raise RuntimeError('OUTPUT_MUST_BE_CANONICAL_UNDER_QUALIFICATION_RUNS')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    sources = {str(p):sha(p) for p in inputs()}
    put(out/'source-inputs-before.json', sources)
    snapshot = out/'source-snapshot'
    for path in inputs():
        copy = snapshot/path.relative_to(ROOT)
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, copy)
        if sha(copy) != sources[str(path)]:
            raise RuntimeError('QUALIFICATION_SOURCE_CHANGED_DURING_SNAPSHOT '+str(path))
    diff = []
    for name in sorted({p.name for p in (ROOT/'executor').iterdir()} | {p.name for p in (ROOT/'preimages/executor').iterdir()}):
        old, new = ROOT/'preimages/executor'/name, ROOT/'executor'/name
        diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],
                                        new.read_text().splitlines(True) if new.exists() else [],
                                        fromfile='preimages/executor/'+name, tofile='executor/'+name))
    with (out/'source.diff').open('x') as file: file.writelines(diff)
    argv = [sys.executable, '-B', str(ROOT/'qualification/test_decisions.py')]
    started = time.time_ns()
    with (out/'native.log').open('xb') as log:
        process = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                 env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1',
                                      'EP19_DIAGNOSTIC_TEST_OUTPUT':str(out)})
    put(out/'process.json', {'argv':argv, 'cwd':str(ROOT), 'native_exit':process.returncode,
        'start_ns':started, 'end_ns':time.time_ns(), 'raw_log':str(out/'native.log'),
        'log_sha256':sha(out/'native.log'), 'product_gate_execution':False,
        'fixture_adapters':'Owner authorization, technical preflight and expensive gates; see control ledger'})
    changed = [p for p, h in sources.items() if sha(p) != h]
    passed = process.returncode == 0 and not changed
    evidence = {str(p):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and not p.is_symlink()}
    put(out/'qualification.json', {'schema':'ep19-external-diagnostics-qualification-v1',
        'result':'PASS' if passed else 'FAIL', 'source_inputs':sources, 'evidence':evidence,
        'changed_sources_during_run':changed, 'product_gate_execution':False,
        'formal_readiness':'NOT_ESTABLISHED', 'publication':'PARENT_OWNED_NOT_PERFORMED',
        'scope':'External prestart decision diagnostics only; this is not a formal launch qualification'})
    if passed:
        return verify(out)
    print(json.dumps({'result':'FAIL', 'native_exit':process.returncode, 'output_dir':str(out),
                      'failed_attempt_retained':True}))
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output-dir', type=Path)
    group.add_argument('--verify-output', type=Path)
    args = parser.parse_args()
    return run(args.output_dir) if args.output_dir else verify(args.verify_output)


if __name__ == '__main__':
    raise SystemExit(main())
