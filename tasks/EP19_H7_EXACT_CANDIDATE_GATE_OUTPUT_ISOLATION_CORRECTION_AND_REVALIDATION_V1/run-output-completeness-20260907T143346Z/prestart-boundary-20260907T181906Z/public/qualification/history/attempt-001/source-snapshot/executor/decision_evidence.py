"""External endpoint decision receipts; no observer or preservation policy changes.

Exclusive, read-only receipts are append-only by this program, not tamper-proof
against their owner. Failed/partial writes are never removed or reused.
"""
from pathlib import Path
import hashlib
import json
import os
import stat
import sys
import time
import uuid
from preservation import Collector, absolute, parent_fd, metadata, identity


def digest(value):
    return hashlib.sha256(value).hexdigest()


def error(exc, path=None):
    return {'path':str(path) if path is not None else None,
            'type':type(exc).__name__, 'errno':getattr(exc, 'errno', None),
            'reason':str(exc)}


def read_json(path):
    """One checked read supplies both parsed values and the raw identity."""
    with parent_fd(path) as (parent, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise RuntimeError('DECISION_CONTROL_NOT_REGULAR '+str(path))
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b''.join(chunks)
            if (metadata(before) != metadata(os.fstat(fd)) or
                    metadata(before) != metadata(os.stat(name, dir_fd=parent, follow_symlinks=False))):
                raise RuntimeError('DECISION_CONTROL_UNSTABLE '+str(path))
        finally:
            os.close(fd)
    return json.loads(raw), {'path':str(path), 'raw_sha256':digest(raw),
                             'metadata':metadata(before)}


def capture(paths, missing):
    started = time.time_ns()
    collector = None
    try:
        collector = Collector(files=paths, expected_missing=missing)
        return collector.capture()
    except Exception as exc:
        # Retain accumulated rows and errors even when capture itself raises.
        return {'result':'INCOMPLETE', 'native_exit':1, 'start_ns':started,
                'end_ns':time.time_ns(), 'entries':dict(collector.rows) if collector else {},
                'errors':list(collector.errors) + [error(exc)] if collector else [error(exc)],
                'claim':'Current sequential endpoints; not atomic or historical continuity'}


def differences(before, current, errors):
    rows = []
    for path in sorted(before.keys() | current.keys() | {e['path'] for e in errors if e.get('path')}):
        a, b = before.get(path), current.get(path)
        faults = [e for e in errors if e.get('path') == path]
        if a == b and not faults:
            continue
        fields = []
        def walk(x, y, prefix=''):
            if isinstance(x, dict) and isinstance(y, dict):
                for key in sorted(x.keys() | y.keys()):
                    if key not in x or key not in y:
                        fields.append({'field':prefix+key, 'before_present':key in x,
                                       'current_present':key in y, 'before':x.get(key), 'current':y.get(key)})
                    elif x[key] != y[key]:
                        walk(x[key], y[key], prefix+key+'.')
            else:
                fields.append({'field':prefix.rstrip('.') or '$', 'before':x, 'current':y})
        walk(a, b)
        categories = []
        if path not in before or (a or {}).get('kind') == 'missing': categories.append('added')
        if path not in current or (b or {}).get('kind') == 'missing': categories.append('missing')
        for fault in faults:
            reason = fault.get('reason', '')
            categories.append('unstable' if any(s in reason for s in ('UNSTABLE', 'REPLACED')) else
                              'missing' if fault.get('errno') == 2 else 'unreadable')
        rows.append({'path':path, 'categories':sorted(set(categories or ['changed'])),
                     'fields':fields, 'capture_errors':faults})
    return rows


def validate_destination(run, scope, baseline, sealed=()):
    target = absolute(run) / 'runtime/decision-evidence'
    protected = set(baseline) | set(sealed)
    # Refuse overlap in BOTH directions, including captured parent directories.
    for key in ('protected', 'sealed_inputs', 'frozen_roots', 'enumeration_roots',
                'repositories', 'metadata_roots', 'expected_missing'):
        protected.update(scope[key] if key in scope else [])
    for raw in protected:
        path = absolute(raw)
        if target == path or target.is_relative_to(path) or path.is_relative_to(target):
            raise RuntimeError('DECISION_EVIDENCE_SCOPE_OVERLAP '+str(path))
    if not any(target.is_relative_to(absolute(p)) for p in scope.get('allowed', [])):
        raise RuntimeError('DECISION_EVIDENCE_NOT_DECLARED_RUNTIME')
    return target


def write_receipt(run, scope, baseline, sealed, receipt):
    target = validate_destination(run, scope, baseline, sealed)
    leaf = str(time.time_ns())+'-'+uuid.uuid4().hex+'.json'
    # runtime must already exist; no automatic repair of a run namespace.
    with parent_fd(target) as (parent, name):
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            wanted = identity(os.fstat(fd))
            if wanted != identity(os.stat(name, dir_fd=parent, follow_symlinks=False)):
                raise RuntimeError('DECISION_EVIDENCE_DIRECTORY_REPLACED')
            out = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400, dir_fd=fd)
            try:
                payload = (json.dumps(receipt, indent=2, ensure_ascii=True)+'\n').encode()
                view = memoryview(payload)
                while view:
                    written = os.write(out, view)
                    if written <= 0:
                        raise OSError('DECISION_EVIDENCE_ZERO_WRITE')
                    view = view[written:]
                os.fsync(out)
            finally:
                os.close(out)
            os.fsync(fd)
            parent_sync = os.open('.', os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent)
            try:
                os.fsync(parent_sync)
            finally:
                os.close(parent_sync)
            if wanted != identity(os.stat(name, dir_fd=parent, follow_symlinks=False)):
                raise RuntimeError('DECISION_EVIDENCE_DIRECTORY_REPLACED')
        finally:
            os.close(fd)
    return target / leaf


def compare(run, results, *, phase, gate, scope_override, sealed, source_paths,
            candidate, base, tree, exact):
    receipt = {'schema':'ep19-external-prestart-decision-v1', 'run':str(run),
               'run_id':run.name, 'candidate':candidate, 'base':base, 'tree':tree,
               'phase':phase, 'gate':gate, 'decision':'REJECT', 'reason':None,
               'capture_errors':[], 'evidence_errors':[], 'shadow_omitted':[],
               'gate_process_status':'NOT_ESTABLISHED',
               'call_boundary':('GATE_COMMAND_NOT_YET_INVOKED_BY_THIS_CALL' if gate else
                                'GATES_NOT_YET_INVOKED_BY_THIS_RUN_ALL_CALL' if phase == 'PRESTART' else
                                'NO_PROCESS_STATUS_INFERRED'),
               'coverage_bounds':'Sequential endpoint capture of the original wanted keys and all original fields; '
                   'directories in file scope retain metadata only. No new enumeration, no atomic snapshot, '
                   'no continuous command-gap monitoring, no writer attribution. START presence is an endpoint '
                   'observation, not proof of process history. No bodies exported.',
               'started_ns':time.time_ns()}
    baseline = {}; wanted = {}; current = {}; scope = None
    rejection = None
    try:
        control, receipt['baseline_identity'] = read_json(run/'baseline.json')
        baseline = control['entries']; wanted = dict(baseline)
        scope, receipt['policy_identity'] = read_json(run/'scope.json')
        if scope_override is not None:
            # Both policy inputs are explicit; use the effective launch scope for overlap.
            receipt['effective_scope_sha256'] = digest(json.dumps(scope_override, sort_keys=True).encode())
            scope = scope_override
        sources = capture(source_paths, [])
        receipt['executor_identity'] = sources
        if sources['result'] != 'COMPLETE':
            receipt['evidence_errors'].extend(sources['errors'])
            raise RuntimeError('DECISION_EXECUTOR_IDENTITY_INCOMPLETE')
        if results.get('SHADOW', {}).get('result') == 'PASS':
            root = Path(scope['shadow_root'])
            for name in [*scope['shadow_declared'], '.git/index']:
                path = str(root/name)
                if path in wanted:
                    receipt['shadow_omitted'].append(path)
                wanted.pop(path, None)
            exact(root)
        captured = capture(wanted, [p for p, r in wanted.items() if r.get('kind') == 'missing'])
        receipt['capture'] = captured
        current = captured['entries']
        receipt['capture_errors'] = captured['errors']
        if captured['result'] != 'COMPLETE' or captured['errors']:
            raise RuntimeError('INCOMPLETE_CAPTURE '+json.dumps(captured['errors']))
        if current != wanted:
            raise RuntimeError('FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP')
        receipt['decision'] = 'PASS'
    except Exception as exc:
        rejection = exc
        receipt['reason'] = str(exc)
        if 'capture' not in receipt:
            receipt['evidence_errors'].append(error(exc))
    receipt.update(baseline_entries=baseline, before=wanted, current=current,
                   differences=differences(wanted, current, receipt['capture_errors']))
    # No second comparison read: all decision fields above come from captured values.
    start_path = run/'runtime/START.json'
    receipt['START'] = {'status':'NOT_ESTABLISHED', 'observed_ns':time.time_ns()}
    try:
        with parent_fd(start_path) as (fd, name):
            try:
                row = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                receipt['START']['status'] = 'ABSENT_AT_CAPTURE'
            else:
                receipt['START'].update(status='FILE_PRESENT_AT_CAPTURE' if stat.S_ISREG(row.st_mode)
                                        else 'NOT_ESTABLISHED', metadata=metadata(row))
    except Exception as exc:
        receipt['START'].update(status='NOT_ESTABLISHED', error=error(exc, start_path))
    receipt['finished_ns'] = time.time_ns()
    try:
        if scope is None:
            raise RuntimeError('DECISION_EVIDENCE_SCOPE_NOT_ESTABLISHED')
        saved = write_receipt(run, scope, baseline, sealed, receipt)
    except Exception as exc:
        # Storage failure cannot reliably be recorded on that same storage.
        message = 'DECISION_EVIDENCE_WRITE_FAILED '+json.dumps(error(exc))
        if rejection is not None:
            message += ' comparison_reason='+str(rejection)
        print(message, file=sys.stderr)
        raise RuntimeError(message) from exc
    if rejection is not None:
        raise rejection
    return saved
