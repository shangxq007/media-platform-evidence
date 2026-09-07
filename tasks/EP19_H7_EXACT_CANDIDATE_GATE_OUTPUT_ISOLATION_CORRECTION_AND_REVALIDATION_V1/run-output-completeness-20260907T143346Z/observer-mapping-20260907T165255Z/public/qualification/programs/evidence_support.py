"""Task-owned append-only evidence utilities; no writes outside this directory."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
OLD = '0cb21b755471c5e554aa971f9f633e298bce55b722ed48a4773e79955677a3e8'
CURRENT = '2e060dd77ed4b24132d581e36cc3fa84c8b67d928cd9ec7689dcdc8823e991e2'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def put(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def local_output(path):
    path = Path(path).absolute()
    if path.resolve() != path or not path.is_relative_to(ROOT) or path == ROOT:
        raise RuntimeError('OUTPUT_OUTSIDE_TASK_OR_SYMLINK')
    return path


def sources():
    return {str(p): digest(p) for p in [*(ROOT.parent / 'executor').iterdir(),
            *ROOT.glob('*.py')] if p.is_file()}


def focused(out, observer='current', positive_only=False):
    out = local_output(out)
    out.mkdir(exist_ok=False)
    before = sources()
    argv = [sys.executable, '-B', str(ROOT / 'affected_controls.py'), '--out',
            str(out / 'fixtures'), '--observer', observer]
    if positive_only:
        argv.append('--positive-only')
    raw = out / 'native.log'
    started = time.time()
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(out), GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='/dev/null', GIT_ALLOW_PROTOCOL='', GIT_NO_LAZY_FETCH='1')
    rc, error = None, None
    with raw.open('xb') as log:
        try:
            rc = subprocess.run(argv, cwd=ROOT, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=120).returncode
        except (OSError, subprocess.TimeoutExpired) as ex:
            error = repr(ex)
    after = sources()
    process = {'argv': argv, 'cwd': str(ROOT), 'native_exit': rc, 'error': error,
               'raw_log': str(raw), 'log_sha256': digest(raw), 'start': started,
               'end': time.time(), 'sources_before': before, 'sources_after': after,
               'source_drift': before != after, 'product_gate_execution': False}
    put(out / 'process.json', process)
    return process


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--observer', choices=['current', 'preimage'], default='current')
    p.add_argument('--positive-only', action='store_true')
    a = p.parse_args()
    r = focused(a.out, a.observer, a.positive_only)
    print(json.dumps({k: r[k] for k in ('native_exit', 'source_drift', 'raw_log')}))
    raise SystemExit(r['native_exit'] if r['native_exit'] is not None else 2)
