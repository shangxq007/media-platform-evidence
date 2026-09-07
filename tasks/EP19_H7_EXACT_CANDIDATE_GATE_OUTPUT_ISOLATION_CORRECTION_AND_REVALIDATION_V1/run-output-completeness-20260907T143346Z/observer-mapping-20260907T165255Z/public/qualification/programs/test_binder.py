#!/usr/bin/env python3
"""Small negative/positive binder fixtures; does not edit any receipt or helper."""
import argparse
import copy
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import bind_qualification as binder
from evidence_support import ROOT, OLD, CURRENT, digest, load, put, local_output
from affected_controls import Result


class BinderControls(unittest.TestCase):
    def setUp(self):
        self.root = OUT / self._testMethodName
        self.root.mkdir()
        self.observer = self.root / 'observe.py'
        self.preimage = self.root / 'observe.before.py'
        self.other = self.root / 'unchanged-source'
        self.observer.write_bytes(binder.OBSERVER.read_bytes())
        self.preimage.write_bytes(binder.PREIMAGE.read_bytes())
        self.other.write_bytes(b'unchanged prior input')
        self.files = {str(self.observer): OLD, str(self.other): digest(self.other)}

    def verify(self):
        return binder.verify_prior_dependencies(self.files, self.observer, self.preimage)

    def test_exact_single_preimage_mapping(self):
        resolved = self.verify()
        self.assertEqual(resolved, {str(self.preimage): OLD, str(self.other): self.files[str(self.other)]})

    def test_unrelated_dependency_drift_rejects(self):
        self.other.write_bytes(b'changed source')
        with self.assertRaisesRegex(RuntimeError, 'PRIOR_DEPENDENCY_CHANGED'):
            self.verify()

    def test_unexpected_current_observer_rejects(self):
        self.observer.write_bytes(self.preimage.read_bytes())
        with self.assertRaisesRegex(RuntimeError, 'UNEXPECTED_CURRENT_OBSERVER'):
            self.verify()

    def test_false_preimage_rejects(self):
        self.preimage.write_bytes(self.observer.read_bytes())
        with self.assertRaisesRegex(RuntimeError, 'PREIMAGE_CHANGED'):
            self.verify()

    def test_old_identity_cannot_be_relabelled_current(self):
        self.files[str(self.observer)] = CURRENT
        with self.assertRaisesRegex(RuntimeError, 'OLD_OBSERVER_BINDING_MISSING'):
            self.verify()

    def test_unbound_stage_evidence_rejects(self):
        with self.assertRaisesRegex(RuntimeError, 'UNBOUND_fixture'):
            binder.verify_bound_map({str(self.other): '0' * 64}, self.files, 'fixture')

    def test_actual_preflight_schema_accepts_bound_receipt(self):
        self.assertEqual(binder.preflight_schema_problems(QUALIFICATION), [])
        self.assertEqual(QUALIFICATION['independent_review'], 'PENDING')

    def test_actual_preflight_schema_rejects_missing_area(self):
        q = dict(QUALIFICATION, collector='NOT_RUN')
        self.assertIn('QUALIFICATION_AREA_NOT_PASS collector', binder.preflight_schema_problems(q))

    def test_actual_formal_schema_rejects_unbound_pass_label(self):
        q = dict(QUALIFICATION, formal_boundary_receipt=None)
        self.assertFalse(binder.coverage.formal_boundary_qualified(q))
        self.assertIn('FORMAL_BOUNDARY_QUALIFICATION_NOT_PASS', binder.preflight_schema_problems(q))

    def test_actual_qualification_rejects_helper_rebinding(self):
        q = dict(QUALIFICATION, helpers=dict(QUALIFICATION['helpers']))
        q['helpers'][str(binder.OBSERVER)] = OLD
        receipt = self.root / 'false-qualification.json'
        put(receipt, q)
        with self.assertRaisesRegex(RuntimeError, 'QUALIFICATION_HELPER_BINDING'):
            binder.coverage.qualification_inputs(receipt)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--qualification', required=True, type=Path)
    a = p.parse_args()
    OUT = local_output(a.out)
    OUT.mkdir(exist_ok=False)
    QUALIFICATION = load(a.qualification)
    r = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(BinderControls))
    put(OUT / 'results.json', {'result': 'PASS' if r.wasSuccessful() else 'FAIL',
        'tests': r.testsRun, 'failures': len(r.failures), 'errors': len(r.errors),
        'skipped': len(r.skipped), 'cases': r.rows, 'product_gate_execution': False,
        'qualification': str(a.qualification.absolute()),
        'qualification_sha256': digest(a.qualification), 'program_sha256': digest(__file__)})
    raise SystemExit(int(not r.wasSuccessful()))
