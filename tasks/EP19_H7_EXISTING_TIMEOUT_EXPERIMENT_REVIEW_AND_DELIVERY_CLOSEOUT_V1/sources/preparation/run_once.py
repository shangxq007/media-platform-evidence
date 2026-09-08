"""Owner-authorized one-shot controller. No retries or gate execution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
PLAN = ROOT / 'evidence' / 'EXPERIMENT_PLAN.json'

def dump(path, value, exclusive=False):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    with path.open('xb' if exclusive else 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    plan = json.loads(PLAN.read_text())
    assert plan['classification'] == 'INSTRUMENTED_EXPERIMENT'
    assert plan['attempt_limit'] == 1
    runtime = Path(plan['runtime_directory'])
    assert runtime.parent == ROOT / 'evidence'
    assert runtime.is_dir()
    for entry in plan['execution_inputs']:
        path = Path(entry['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('Execution input changed: ' + str(path))
    before = time.monotonic_ns()
    consumed = {
        'experiment_id': plan['experiment_id'],
        'state': 'CONSUMED_BEFORE_JAVA_START_NO_RETRY',
        'attempts_consumed': 1,
        'time_utc': datetime.now(timezone.utc).isoformat(),
        'monotonic_ns': before,
        'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'command': plan['command'],
    }
    dump(runtime / 'owner-attempt-consumed', consumed, exclusive=True)
    fd = os.open(runtime, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    receipt = {'attempts_consumed': 1, 'java_started': False, 'command': plan['command'],
               'outer_timeout_seconds': plan['outer_timeout_seconds'], 'outer_teardown': []}
    code = 2
    child = None
    with (runtime / 'native.stdout.log').open('xb') as out, (runtime / 'native.stderr.log').open('xb') as err:
        try:
            child = subprocess.Popen(plan['command'], cwd=plan['cwd'], env=plan['environment'],
                                     stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            receipt.update(java_started=True, java_pid=child.pid)
            dump(runtime / 'controller-start.json', receipt)
            try:
                code = child.wait(timeout=plan['outer_timeout_seconds'])
                receipt['outer_timeout'] = False
            except subprocess.TimeoutExpired:
                receipt['outer_timeout'] = True
                # Only this exact, not-yet-reaped Popen child; no process names, PID scans or groups.
                child.terminate()
                receipt['outer_teardown'].append('owned_java_Process_terminate')
                try:
                    code = child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    receipt['outer_teardown'].append('owned_java_Process_kill')
                    code = child.wait(timeout=3)
                receipt['risk'] = 'Java timed out: retained identity journal requires separate scoped inspection; no descendant reaping claim.'
        except Exception as failure:
            receipt['controller_error'] = {'type': type(failure).__name__, 'message': str(failure)}
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                receipt['outer_teardown'].append('exceptional_owned_java_terminate')
                try:
                    code = child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill()
                    receipt['outer_teardown'].append('exceptional_owned_java_kill')
                    code = child.wait(timeout=3)
            receipt.update(native_exit=code, duration_ns=time.monotonic_ns() - before,
                           finished_utc=datetime.now(timezone.utc).isoformat())
            dump(runtime / 'controller-receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return code if 0 <= code <= 255 else 2

if __name__ == '__main__':
    sys.exit(main())
