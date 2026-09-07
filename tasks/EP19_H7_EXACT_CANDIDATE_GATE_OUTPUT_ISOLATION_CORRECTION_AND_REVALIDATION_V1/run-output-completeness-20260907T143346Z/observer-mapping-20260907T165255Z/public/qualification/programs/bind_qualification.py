#!/usr/bin/env python3
"""Minimal current-identity receipt: fresh affected fixtures + verified prior evidence.

Never executes parent qualification, product gates, runtime probes or network.
The historical receipt is immutable; its observer identity resolves to the
preserved preimage, while the new receipt seals the actual current helpers.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
from evidence_support import ROOT, OLD, CURRENT, digest, load, put, local_output, focused, sources

HELPERS = ROOT.parent / 'executor'
PRIOR = ROOT.parent / 'qualification/parent-native-final-001/QUALIFICATION.json'
PRIOR_SHA = '8b8ef962cd5921306900699d8d1c7de1b8e9e715f0cda2ab7d07d02d3739177c'
OBSERVER = HELPERS / 'observe.py'
PREIMAGE = ROOT / 'observe.before.py'
sys.path.insert(0, str(HELPERS))
import coverage

AFFECTED = {
    'runtime_controls.PreservationControls.test_frontend_new_append_actual_observer_rejects_unknown_writer': 'native_valid',
    'runtime_controls.PreservationControls.test_frontend_reachable_new_object_still_rejects': 'injected_valid',
    'runtime_controls.PreservationControls.test_frontend_unreachable_new_object_rejects': 'injected_unreachable',
    'runtime_controls.PreservationControls.test_frontend_corrupt_new_object_rejects': 'injected_corrupt',
    'runtime_controls.PreservationControls.test_frontend_symlink_new_object_rejects': 'injected_symlink',
    'runtime_continuation.Controls.test_shared_loose_object_pending_not_pass': 'native_no_ref',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_source_delta():
    require(digest(OBSERVER) == CURRENT, 'UNEXPECTED_CURRENT_OBSERVER')
    require(digest(PREIMAGE) == OLD, 'PREIMAGE_CHANGED')

    def split(path):
        text = path.read_text()
        node = next(n for n in ast.walk(ast.parse(text))
                    if isinstance(n, ast.FunctionDef) and n.name == 'resolve_shared')
        lines = text.splitlines(keepends=True)
        return ''.join(lines[:node.lineno-1]), ''.join(lines[node.end_lineno:]), ast.get_source_segment(text, node)

    before, after = split(PREIMAGE), split(OBSERVER)
    require(before[:2] == after[:2], 'CHANGE_OUTSIDE_RESOLVE_SHARED')
    return {'prior_path': str(OBSERVER), 'prior_sha256': OLD, 'preserved_preimage': str(PREIMAGE),
            'current_path': str(OBSERVER), 'current_sha256': CURRENT,
            'only_changed_method': 'Watch.resolve_shared', 'all_other_source_bytes_equal': True,
            'prior_method_sha256': hashlib.sha256(before[2].encode()).hexdigest(),
            'current_method_sha256': hashlib.sha256(after[2].encode()).hexdigest()}


def verify_prior_dependencies(files, observer=OBSERVER, preimage=PREIMAGE):
    """Verify every byte entry; exactly one narrowly pinned historical mapping."""
    require(files.get(str(observer)) == OLD, 'OLD_OBSERVER_BINDING_MISSING')
    require(digest(observer) == CURRENT, 'UNEXPECTED_CURRENT_OBSERVER')
    require(digest(preimage) == OLD, 'PREIMAGE_CHANGED')
    resolved = {}
    for name, expected in files.items():
        path = preimage if name == str(observer) else Path(name)
        require(digest(path) == expected, 'PRIOR_DEPENDENCY_CHANGED ' + name)
        resolved[str(path)] = expected
    return resolved


def verify_bound_map(mapping, files, label):
    for name, sha in mapping.items():
        require(files.get(name) == sha, 'UNBOUND_' + label + ' ' + name)


def prior_evidence(q):
    files = q['dependencies']
    require(q['result'] == 'PASS' and q['product_gate_execution'] is False, 'PRIOR_NOT_PASS')
    require(set(q['helpers']) == set(map(str, coverage.local_imports()[0])), 'HELPER_UNIVERSE_CHANGED')
    verify_bound_map(q['helpers'], files, 'PRIOR_HELPERS')
    stage_rows = {}
    for stage in ('focused', 'controls', 'frontend', 'lean', 'formal'):
        path = PRIOR.parent / (stage + '-process.json')
        require(str(path) in files, 'STAGE_NOT_BOUND')
        p = load(path)
        require(p.get('native_exit') == 0 and p.get('source_drift') is False and
                p.get('product_gate_execution') is False, 'STAGE_NOT_PASS ' + stage)
        require(p['helpers'] == q['helpers'], 'STAGE_HELPER_IDENTITY ' + stage)
        require(files.get(p['raw_log']) == p['log_sha256'], 'STAGE_LOG_BINDING ' + stage)
        for label in ('helpers', 'programs', 'evidence'):
            require(bool(p[label]), 'EMPTY_STAGE_MAP ' + stage)
            verify_bound_map(p[label], files, stage + '_' + label)
        stage_rows[stage] = {'process_receipt': str(path), 'process_sha256': files[str(path)],
                             'raw_log': p['raw_log'], 'log_sha256': p['log_sha256'],
                             'evidence_entries': len(p['evidence']), 'execution': 'REUSED_PRIOR_NATIVE'}
    fq_path = q['focused_qualification']
    require(fq_path in files, 'FOCUSED_RECEIPT_NOT_BOUND')
    fq = load(fq_path)
    verify_bound_map(fq['dependencies'], files, 'FOCUSED_CLOSURE')
    require(fq['helpers'] == q['helpers'] and fq['real_gradle_instrumentation'] == 'PASS',
            'FOCUSED_SOURCE_OR_GRADLE')
    fp = load(fq['process_receipt'])
    require(fp['native_exit'] == 0 and fp['wrapper_exit'] == 0 and fp['source_drift'] == [] and
            files.get(fp['raw_log']) == fp['log_sha256'], 'FOCUSED_PROCESS')
    verify_bound_map(fp['source_before'], files, 'FOCUSED_SOURCES')
    for area, path in q['runtime_area_receipts'].items():
        require(path in files, 'RUNTIME_NOT_BOUND ' + area)
        r = load(path)
        require(r['result'] == 'PASS' and r['formal_wrapper_sha256'] == digest(HELPERS / 'execution.py'),
                'RUNTIME_WRAPPER_CHANGED ' + area)
        require(r['probe_program'] in files, 'RUNTIME_PROGRAM_NOT_BOUND')
        for proc in r.get('process_receipts', []):
            require(proc in files, 'RUNTIME_PROCESS_NOT_BOUND')
            pr = load(proc)
            require(pr['native_exit'] == 0 and files.get(pr['raw_log']) == pr['log_sha256'],
                    'RUNTIME_PROCESS_NOT_PASS')
    front = load(q['runtime_area_receipts']['frontend'])
    lean = load(q['runtime_area_receipts']['lean'])
    require(all(front.get(k) == 'PASS' for k in ('readonly', 'private_pid', 'xdg_runtime')),
            'FRONTEND_RUNTIME_INCOMPLETE')
    require(lean.get('strict_collector') == 'PASS', 'LEAN_RUNTIME_INCOMPLETE')
    require(coverage.formal_boundary_qualified(q), 'FORMAL_REUSE_INCOMPLETE')
    return fq, stage_rows


def method_reuse(q, fq):
    """Map original recorded methods, retaining historical counts and verdicts."""
    result = {}
    seen_affected = set()
    for label, receipt in (('focused', fq['result_receipt']), ('broader', q['result_receipt'])):
        r = load(receipt)
        require(r['result'] == 'PASS' and r['failures'] == r['errors'] == r['skipped'] == 0,
                'PRIOR_RESULTS_NOT_PASS')
        rows = []
        for case in r['cases']:
            name = case['case'].split(' (', 1)[0]
            require(case['actual'] == 'PASS', 'PRIOR_CASE_NOT_PASS ' + name)
            match = re.fullmatch(r'(\w+)\.(\w+)\.(test_\w+)', name)
            require(match is not None, 'UNKNOWN_PRIOR_CASE ' + name)
            module, cls, method = match.groups()
            program = (HELPERS if module.startswith('test_') else ROOT.parent / 'qualification') / (module + '.py')
            require(str(program) in q['dependencies'], 'METHOD_PROGRAM_NOT_BOUND')
            source = program.read_text()
            klass = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == cls)
            node = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == method)
            affected = name in AFFECTED
            if affected:
                seen_affected.add(name)
            rows.append({'case': case['case'], 'method': name, 'program': str(program),
                'program_sha256': q['dependencies'][str(program)],
                'method_sha256': hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest(),
                'historical_actual': case['actual'],
                'disposition': 'SUPERSEDED_BY_FRESH_AFFECTED_CONTROL' if affected else 'REUSE_UNCHANGED_INPUT_EVIDENCE',
                'fresh_replacement': 'Controls.test_' + AFFECTED[name] if affected else None,
                'reason': ('Calls changed resolve_shared with pending objects; old positive rejection policy is not current authority.'
                           if affected else 'Input/source closure verified. This method does not exercise pending shared-object resolution; all observer bytes outside resolve_shared are identical.')})
        result[label] = {'receipt': receipt, 'historical_tests': r['tests'], 'recorded_rows': len(rows),
                         'unique_methods': len({x['method'] for x in rows}), 'methods': rows,
                         'fresh_executions': 0,
                         'superseded_methods': len({x['method'] for x in rows if x['fresh_replacement']})}
    require(seen_affected == set(AFFECTED), 'AFFECTED_METHOD_MAPPING_INCOMPLETE')
    return result


def preflight_schema_problems(q):
    """Execute only the five qualification clauses from actual runner.preflight.

    No prepare/baseline/preflight invocation, product repositories or gates.
    Fail closed if the original schema block changes shape.
    """
    path = HELPERS / 'runner.py'
    tree = ast.parse(path.read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'preflight')
    markers = {'REAL_GRADLE_INSTRUMENTATION_NOT_QUALIFIED', 'CORRECTION_QUALIFICATION_MISSING ',
               'FRONTEND_BOUNDARY_QUALIFICATION_NOT_PASS', 'FORMAL_BOUNDARY_QUALIFICATION_NOT_PASS',
               'QUALIFICATION_AREA_NOT_PASS '}
    selected = []
    for block in fn.body:
        if isinstance(block, ast.Try):
            for statement in block.body:
                constants = {n.value for n in ast.walk(statement) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
                if constants & markers:
                    selected.append(copy.deepcopy(statement))
    require(len(selected) == 5, 'PREFLIGHT_SCHEMA_SHAPE_CHANGED')
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    namespace = {'qualification': q, 'coverage': coverage, 'problems': []}
    exec(compile(module, str(path) + ':qualification-schema-only', 'exec'), namespace)
    return namespace['problems']


def assemble(out):
    out = local_output(out)
    out.mkdir(exist_ok=False)
    started = time.time()
    source_before = sources()
    try:
        require(digest(PRIOR) == PRIOR_SHA, 'PRIOR_RECEIPT_IDENTITY_CHANGED')
        delta = verify_source_delta()
        q = load(PRIOR)
        resolved = verify_prior_dependencies(q['dependencies'])
        print('Verified all', len(q['dependencies']), 'prior dependency entries; one pinned preimage mapping.', flush=True)
        fq, stages = prior_evidence(q)
        mapping = method_reuse(q, fq)
        process = focused(out / 'fresh')
        rpath = out / 'fresh/fixtures/results.json'
        require(process['native_exit'] == 0 and process['source_drift'] is False, 'FRESH_PROCESS_FAILED')
        r = load(rpath)
        require(r['result'] == 'PASS' and r['tests'] == 25 and r['failures'] == r['errors'] == r['skipped'] == 0,
                'FRESH_CONTROLS_FAILED_OR_INCOMPLETE')
        require(r['observer_sha256'] == CURRENT, 'FRESH_OBSERVER_IDENTITY')
        # Derive verdicts only after all fresh controls and reusable evidence pass.
        ledger = {'schema': 'ep19-observer-evidence-reuse-v1', 'prior_receipt': str(PRIOR),
            'prior_receipt_sha256': PRIOR_SHA, 'observer_mapping': delta,
            'prior_dependency_resolution': {'rule': 'Every original path retains its hash except the single observer path resolves to preserved_preimage.',
                'entries_verified': len(q['dependencies']), 'unverified_entries': 0,
                'manifest': str(PRIOR), 'manifest_field': 'dependencies', 'mapped_entries': 1},
            'original_native_stages': stages, 'original_methods': mapping,
            'fresh': {'tests': r['tests'], 'result_receipt': str(rpath),
                      'injected_classifier_resolver_controls': 12, 'real_inotify_observe_run_controls': 12,
                      'injected_late_event_real_finalizer_controls': 1},
            'areas': {area: {'result': 'PASS', 'basis': 'Verified original method/input evidence; pending shared-object cases superseded by fresh controls.'}
                      for area in ('collector', 'coverage', 'shadow', 'packaging', 'freshness', 'launch', 'dependency_preparation')},
            'runtime_reuse': {'areas': ['real_gradle_instrumentation', 'frontend_boundary', 'formal_boundary', 'lean_runtime'],
                'execution_wrapper_sha256': digest(HELPERS / 'execution.py'),
                'basis': 'Exact unchanged execution.py, probe programs, fixtures and raw dependency hashes verified. resolve_shared is not on runtime-probe paths. Prior native execution only; zero fresh Gradle/frontend/Lean/Coq executions.',
                'raw_receipts': q['runtime_area_receipts']},
            'limits': ['No old aggregate PASS is represented as fresh execution.',
                       'No product gates, network, current container probe, or full preflight run.',
                       'No writer attribution. Known fanout directories used for native positive cases; no claim of gap-free new-subtree observation.',
                       'Linux/inotify fixture evidence covers a command interval only.',
                       'Independent review remains PENDING and is not a new launch blocker.'],
            'independent_review': 'PENDING', 'product_gate_execution': False}
        put(out / 'REUSE_LEDGER.json', ledger)
        # Record negative fixture links, never turn their targets into regular proof entries.
        links = {str(p): str(p.readlink()) for p in (out / 'fresh').rglob('*') if p.is_symlink()}
        put(out / 'fixture-links.json', {'negative_fixture_symlinks_not_followed': links})
        require(source_before == sources(), 'TASK_OR_HELPER_SOURCE_DRIFT')
        helpers = coverage.seal(coverage.local_imports()[0])
        dependencies = {**resolved, **helpers, str(PRIOR): PRIOR_SHA}
        for p in [*ROOT.glob('*.py'), ROOT / 'CODEX_BRIEF.md', ROOT / 'OBSERVER_CORRECTION.json',
                  ROOT / 'OBSERVER.diff', *out.rglob('*')]:
            if p.is_file() and not p.is_symlink():
                dependencies[str(p)] = digest(p)
        receipt = {'schema': 'ep19-output-corrections-v2', 'result': 'PASS',
            'helpers': helpers, 'dependencies': dependencies,
            'qualification_program': str(Path(__file__).resolve()),
            'raw_log': str(out / 'fresh/native.log'), 'process_receipt': str(out / 'fresh/process.json'),
            'result_receipt': str(rpath), 'reuse_ledger': str(out / 'REUSE_LEDGER.json'),
            'product_gate_execution': False, 'independent_review': 'PENDING',
            'areas': q['areas'], **{k: 'PASS' for k in ledger['areas']},
            'real_gradle_instrumentation': 'PASS', 'frontend_boundary': 'PASS',
            'formal_boundary': 'PASS', 'lean_runtime': 'PASS',
            'formal_boundary_receipt': q['formal_boundary_receipt'],
            'lean_runtime_receipt': q['lean_runtime_receipt'],
            'runtime_area_receipts': q['runtime_area_receipts'],
            'formal_runtime_qualification': 'REUSED_VERIFIED_PRIOR_SYNTHETIC_NATIVE',
            'reuse': [{'ledger': str(out / 'REUSE_LEDGER.json'), 'prior_receipt': str(PRIOR)}],
            'fresh_tests': r['tests'], 'fresh_failures': 0, 'fresh_errors': 0,
            'historical_tests': {k: v['historical_tests'] for k, v in mapping.items()},
            'superseded_historical_methods': sorted(AFFECTED)}
        require(coverage.formal_boundary_qualified(receipt), 'FORMAL_BOUNDARY_REUSE_REJECTED')
        problems = preflight_schema_problems(receipt)
        require(not problems, 'PREFLIGHT_QUALIFICATION_SCHEMA_REJECT ' + repr(problems))
        put(out / 'QUALIFICATION.json', receipt)
        inputs = coverage.qualification_inputs(out / 'QUALIFICATION.json')
        validation = {'result': 'PASS', 'qualification_inputs': 'PASS',
            'formal_boundary_qualified': True, 'runner_preflight_qualification_schema': 'PASS',
            'runner_sha256': digest(HELPERS / 'runner.py'), 'full_preflight_execution': False,
            'qualification': str(out / 'QUALIFICATION.json'), 'qualification_sha256': digest(out / 'QUALIFICATION.json'),
            'sealed_input_count_including_receipt': len(inputs), 'fresh_tests': r['tests'],
            'source_drift': source_before != sources(), 'seconds': time.time() - started,
            'independent_review': 'PENDING', 'product_gate_execution': False}
        require(not validation['source_drift'], 'SOURCE_DRIFT_AFTER_ACCEPTANCE')
        put(out / 'VALIDATION.json', validation)
        print(out / 'QUALIFICATION.json', flush=True)
        return 0
    except Exception as ex:
        put(out / 'FAILURE.json', {'result': 'FAIL', 'error_type': type(ex).__name__, 'reason': str(ex),
                                  'seconds': time.time() - started, 'product_gate_execution': False})
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    raise SystemExit(assemble(a.out))
