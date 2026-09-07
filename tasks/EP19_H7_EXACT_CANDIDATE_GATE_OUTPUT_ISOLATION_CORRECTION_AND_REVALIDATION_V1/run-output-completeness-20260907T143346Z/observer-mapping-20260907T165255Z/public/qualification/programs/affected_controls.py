#!/usr/bin/env python3
"""Focused fixture-only controls for the unchanged, restored observer.

No helper patches: injected tests supply event records explicitly; native tests
use real inotify and observe.run. All Git databases and outputs stay under --out.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import zlib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
HELPERS = ROOT.parent / 'executor'
REF = 'refs/heads/agent/frontend-wave2-product-ux-v1'
ACCEPT = 'AUTHORIZED_FRONTEND_REACHABLE_NEW_OBJECT_APPEND_WRITER_UNKNOWN'
PENDING = 'PENDING_SHARED_OBJECT_SCOPE_PROOF'
REJECT = 'REJECT_UNRESOLVED_SHARED_METADATA_SCOPE'
sys.dont_write_bytecode = True
sys.path.insert(0, str(HELPERS))


def put(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def env_for(root):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1',
               GIT_ALLOW_PROTOCOL='', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(root))
    return env


class Fixture:
    def __init__(self, root, variant):
        self.root, self.variant = root, variant
        self.git = root / 'canonical.git'
        self.primary = root / 'PRIMARY.git'
        self.env = env_for(root)
        for g in (self.git, self.primary):
            r = subprocess.run(['git', 'init', '--bare', '--template=', str(g)],
                               env=self.env, capture_output=True)
            (root / (g.name + '-init.log')).write_bytes(r.stdout + r.stderr)
            if r.returncode:
                raise RuntimeError('GIT_INIT_FAILED')
        self.ref = self.git / REF
        self.ref.parent.mkdir(parents=True)
        tree, p, raw = self.encode('tree', b'')
        p.write_bytes(raw)
        base, p, raw = self.encode('commit', self.commit(tree))
        p.write_bytes(raw)
        self.existing = p
        self.ref.write_text(base + '\n')
        (self.git / 'HEAD').write_text('ref: ' + REF + '\n')
        (self.primary / 'index').write_bytes(b'fixture index')
        self.objects = {}
        blob, self.blob, raw = self.encode('blob', b'new bounded frontend content')
        self.objects[str(self.blob)] = raw.hex()
        tree, p, raw = self.encode('tree', b'100644 file\0' + bytes.fromhex(blob))
        self.objects[str(p)] = raw.hex()
        self.tip, p, raw = self.encode('commit', self.commit(tree, base))
        self.objects[str(p)] = raw.hex()
        self.extra = None
        self.target = None
        if variant == 'unreachable':
            _, p, raw = self.encode('blob', b'unreachable loose object')
            self.objects[str(p)] = raw.hex()
        elif variant == 'corrupt':
            self.objects[str(self.blob)] = b'not zlib'.hex()
        elif variant == 'hash_mismatch':
            self.objects[str(self.blob)] = zlib.compress(b'blob 5\0wrong').hex()
        elif variant == 'symlink':
            self.target = root / 'symlink-body'
            self.target.write_bytes(bytes.fromhex(self.objects[str(self.blob)]))
            del self.objects[str(self.blob)]
        elif variant in ('temp', 'resolved_temp'):
            self.extra = self.blob.parent / 'tmp_obj_fixture'
        elif variant == 'unbound_dir':
            self.extra = next(self.git / 'objects' / f'{n:02x}' for n in range(256)
                              if not (self.git / 'objects' / f'{n:02x}').exists())
        elif variant.startswith('strict_'):
            self.extra = {'strict_existing': self.existing,
                          'strict_canonical': self.git / 'config',
                          'strict_primary': self.primary / 'index'}[variant]
        self.plan = root / 'plan.json'
        put(self.plan, {'objects': self.objects, 'ref': str(self.ref), 'tip': self.tip,
                       'blob': str(self.blob), 'extra': str(self.extra) if self.extra else None,
                       'target': str(self.target) if self.target else None, 'variant': variant})

    def encode(self, kind, content):
        body = kind.encode() + b' ' + str(len(content)).encode() + b'\0' + content
        oid = hashlib.sha1(body).hexdigest()
        p = self.git / 'objects' / oid[:2] / oid[2:]
        p.parent.mkdir(exist_ok=True)
        return oid, p, zlib.compress(body)

    @staticmethod
    def commit(tree, parent=None):
        return ('tree ' + tree + '\n' + ('parent ' + parent + '\n' if parent else '') +
                'author Fixture <fixture@example.invalid> 1 +0000\n'
                'committer Fixture <fixture@example.invalid> 1 +0000\n\nfixture\n').encode()

    def args(self):
        return dict(protected=[], repositories=[], metadata_roots=[self.git, self.primary],
                    allowed=[], cross_lane=[] if self.variant == 'no_ref' else [self.ref],
                    shared_git=self.git)


def write_fixture(plan):
    p = json.loads(Path(plan).read_text())
    for name, raw in p['objects'].items():
        Path(name).write_bytes(bytes.fromhex(raw))
    if p['target']:
        Path(p['blob']).symlink_to(p['target'])
    if p['extra']:
        extra = Path(p['extra'])
        if p['variant'] == 'unbound_dir':
            extra.mkdir()
        elif p['variant'].startswith('strict_'):
            # Same-byte writes remain strict events, independently of endpoints.
            raw = extra.read_bytes()
            extra.write_bytes(raw)
        else:
            extra.write_bytes(b'unresolved')
            if p['variant'] == 'resolved_temp':
                extra.unlink()
    Path(p['ref']).write_text(p['tip'] + '\n')


class Controls(unittest.TestCase):
    def setUp(self):
        self.root = OUT / self._testMethodName
        self.root.mkdir()

    def check(self, mode, variant):
        fx = Fixture(self.root, variant)
        expected = variant in ('valid', 'resolved_temp')
        if mode == 'injected':
            w = OBSERVE.Watch(**fx.args())
            try:
                write_fixture(fx.plan)
                paths = list(map(Path, fx.objects))
                if fx.target:
                    paths.append(fx.blob)
                if fx.extra:
                    paths.append(fx.extra)
                classified = {str(p): w.classify(p, 8) for p in paths}
                w.events = [{'path': str(p), 'mask': 8, 'category': classified[str(p)],
                             'writer': 'NOT_ESTABLISHED', 'origin': 'INJECTED_EVENT'} for p in paths]
                w.resolve_shared()
                r = {'events': w.events, 'proof': w.shared_proof, 'rejected': w.rejected(),
                     'classifications': classified, 'observation_kind': 'INJECTED_EVENTS_REAL_GIT_RESOLVER'}
                put(self.root / 'observation.json', r)
                if variant.startswith('strict_'):
                    self.assertEqual(classified[str(fx.extra)], 'REJECT_GIT_METADATA_EVENT')
                else:
                    self.assertIn(PENDING, classified.values())
                self.assertEqual(w.rejected(), not expected, r)
                if expected:
                    self.assertTrue(all(e['category'] == ACCEPT for e in w.events))
                    self.assertEqual(w.shared_proof['authorized_ref_tips_observed'], {REF: fx.tip})
                else:
                    self.assertTrue(any(e['category'].startswith('REJECT') for e in w.events))
            finally:
                w.close()
        else:
            argv = [sys.executable, '-B', str(Path(__file__).resolve()), '--write-fixture', str(fx.plan)]
            r = OBSERVE.run(argv, self.root, self.root / 'child.log', env=fx.env, timeout=10, **fx.args())
            put(self.root / 'observation.json', {'observation_kind': 'REAL_INOTIFY_OBSERVE_RUN', **r})
            self.assertEqual(r['wrapper_exit'], 0 if expected else 1, r)
            self.assertTrue(r['ready_before_child'] and r['final_queue_drained'])
            self.assertEqual(r['owned_processes_remaining'], [])
            if expected:
                self.assertEqual(r['native_exit'], 0)
                self.assertEqual(r['result'], 'PASS_BOUNDED_OBSERVATION')
                self.assertEqual(r['shared_metadata_scope_proof']['authorized_ref_tips_observed'], {REF: fx.tip})
                self.assertTrue(any(e['category'] == ACCEPT for e in r['events']))
                self.assertEqual(r['gaps'], [])
            else:
                self.assertEqual(r['result'], 'REJECT')
                self.assertTrue(any(e['category'].startswith('REJECT') for e in r['events']), r)
                if variant.startswith('strict_'):
                    self.assertTrue(any(e['path'] == str(fx.extra) and e['category'] ==
                                        'REJECT_GIT_METADATA_EVENT' for e in r['events']), r)
            self.assertFalse(any(e['category'].startswith('PENDING_') for e in r['events']))
        if variant in ('corrupt', 'hash_mismatch', 'unreachable', 'symlink', 'temp', 'unbound_dir'):
            proof = r['proof'] if mode == 'injected' else r['shared_metadata_scope_proof']
            self.assertEqual(proof['disposition'], REJECT)
            if variant == 'hash_mismatch':
                self.assertEqual(proof['reason'], 'NEW_OBJECT_DIGEST_MISMATCH')
            if variant == 'corrupt':
                self.assertEqual(proof['error_type'], 'error')

    def test_late_pending_cannot_finalize(self):
        fx = Fixture(self.root, 'valid')
        native_drain, native_snapshot = OBSERVE.Watch.drain, OBSERVE.snapshot
        state = {'snapshots': 0, 'injected': False}

        def snapshot(*a, **kw):
            r = native_snapshot(*a, **kw)
            state['snapshots'] += 1
            return r

        def drain(w):
            native_drain(w)
            if state['snapshots'] == 2 and not state['injected']:
                state['injected'] = True
                w.events.append({'path': str(fx.blob), 'mask': 8, 'category': PENDING,
                                 'origin': 'INJECTED_LATE_EVENT', 'writer': 'NOT_ESTABLISHED'})

        with patch.object(OBSERVE, 'snapshot', snapshot), patch.object(OBSERVE.Watch, 'drain', drain):
            r = OBSERVE.run([sys.executable, '-B', '-c', 'pass'], self.root,
                            self.root / 'child.log', env=fx.env, timeout=10, **fx.args())
        put(self.root / 'observation.json', {'observation_kind': 'INJECTED_LATE_EVENT_REAL_FINALIZER', **r})
        self.assertTrue(state['injected'])
        self.assertEqual(r['native_exit'], 0)
        self.assertEqual(r['wrapper_exit'], 1)
        self.assertIn('LATE_SHARED_SCOPE_UNRESOLVED', r['observation_errors'])


for mode in ('injected', 'native'):
    for variant in ('valid', 'unreachable', 'corrupt', 'hash_mismatch', 'symlink', 'temp',
                    'resolved_temp', 'unbound_dir', 'no_ref', 'strict_existing',
                    'strict_canonical', 'strict_primary'):
        def test(self, mode=mode, variant=variant):
            self.check(mode, variant)
        setattr(Controls, 'test_' + mode + '_' + variant, test)


class Result(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append({'case': test.id(), 'actual': 'PASS'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.rows.append({'case': test.id(), 'actual': 'FAIL', 'detail': self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.rows.append({'case': test.id(), 'actual': 'ERROR', 'detail': self._exc_info_to_string(err, test)})


def main():
    global OUT, OBSERVE
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--observer', choices=['current', 'preimage'], default='current')
    p.add_argument('--positive-only', action='store_true')
    p.add_argument('--write-fixture', type=Path)
    a = p.parse_args()
    if a.write_fixture:
        plan = a.write_fixture.absolute()
        if plan.resolve() != plan or not plan.is_relative_to(ROOT):
            p.error('fixture must be local')
        write_fixture(plan)
        return 0
    if not a.out:
        p.error('--out required')
    OUT = a.out.absolute()
    if OUT.resolve() != OUT or not OUT.is_relative_to(ROOT):
        p.error('output must be under task cwd')
    OUT.mkdir(exist_ok=False)
    source = HELPERS / 'observe.py' if a.observer == 'current' else ROOT / 'observe.before.py'
    spec = importlib.util.spec_from_file_location('affected_observer', source)
    OBSERVE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(OBSERVE)
    suite = (unittest.TestSuite(Controls('test_' + m + '_valid') for m in ('injected', 'native'))
             if a.positive_only else unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    r = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    put(OUT / 'results.json', {'result': 'PASS' if r.wasSuccessful() else 'FAIL',
        'tests': r.testsRun, 'failures': len(r.failures), 'errors': len(r.errors), 'skipped': len(r.skipped),
        'cases': r.rows, 'observer': str(source), 'observer_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'product_gate_execution': False, 'independent_review': 'PENDING',
        'limitations': 'Fixture Git DBs only; injected events explicitly labeled; no PID attribution; no product/runtime requalification.'})
    return int(not r.wasSuccessful())


if __name__ == '__main__':
    raise SystemExit(main())
