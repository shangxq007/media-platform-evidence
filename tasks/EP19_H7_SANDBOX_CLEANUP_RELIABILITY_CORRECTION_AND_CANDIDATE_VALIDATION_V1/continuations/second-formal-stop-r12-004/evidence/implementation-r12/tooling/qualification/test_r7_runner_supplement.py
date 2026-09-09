"""Source-bound RED/GREEN for the real runner supplement serialization seam."""
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'executor'))
from test_r5_remaining import R5FailureTransitionControls


class R7RunnerSupplementControl(unittest.TestCase):
    def test_real_runner_supplement_keeps_every_composed_persistence_leaf(self):
        helper=R5FailureTransitionControls('test_supplement_persistence_failure_stays_secondary_and_never_success')
        helper.setUp();self.addCleanup(helper.doCleanups)
        runner=helper.actual_runner();base=helper.base
        run=base/'r7-supplement-run';repo=base/'r7-supplement-repo'
        repo.mkdir();(run/'runtime/gates').mkdir(parents=True)
        output=run/'runtime/outputs/result.bin'
        command=[sys.executable,'-B','-c','pass']
        matrix={'gates':{'FIXTURE':{'repository':str(repo),'dependencies':[],
            'command':command,'authoritative_command':command,'cwd':str(repo),
            'timeout_seconds':2,'output_bindings':{'required_files':[str(output)]}}}}
        observed={'result':'PASS_BOUNDED_OBSERVATION','native_exit':0,'wrapper_exit':0,
            'child_pid':456,'failure_dimensions':{'native_invocation':True,'native_exit':0,
            'native_command_exit_failure':False,'product_assertion_failure':False,
            'observer_preservation_failure':False,'workload_timeout_or_cancellation':False,
            'wrapper_or_environment_failure':False,'evidence_persistence_failure':False,
            'cleanup_failure':False}}

        def execute(*_args,**_kwargs):
            output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(b'accepted output')
            return observed

        ordinary_digest=runner.coverage.digest
        def fail_postseal(path):
            if 'sealed' in Path(path).parts and Path(path).name.isdigit():
                raise OSError('r7 original postseal leaf')
            return ordinary_digest(path)

        real_exclusive_directory=runner.durability.exclusive_directory
        def composed_supplement_failure(path,*args,**kwargs):
            if Path(path).name!='failure-supplement':
                return real_exclusive_directory(path,*args,**kwargs)
            runner.durability._composed('R7_SUPPLEMENT_COMPOSED_FAILURE',
                OSError('r7 supplement write leaf'),[
                    ('directory-close','DIRECTORY_FD_CLOSE',OSError('r7 supplement close leaf')),
                    ('parent-fsync','PUBLISHING_PARENT_FSYNC',OSError('r7 supplement parent fsync leaf'))])

        with patch.object(runner,'check_execution_seal',return_value=True), \
             patch.object(runner,'repos',return_value=[]), \
             patch.object(runner,'compare_baseline',return_value={}), \
             patch.object(runner.artifacts,'producer_inputs',return_value={}), \
             patch.object(runner.freshness,'preserve_cleanup',return_value=[]), \
             patch.object(runner.freshness,'dependency_inputs',return_value={}), \
             patch.object(runner,'packaging_receipts',return_value=[]), \
             patch.object(runner.observe,'run',side_effect=execute), \
             patch.object(runner.parsers,'parse',return_value={'result':'PASS'}), \
             patch.object(runner.coverage,'digest',side_effect=fail_postseal), \
             patch.object(runner.durability,'exclusive_directory',side_effect=composed_supplement_failure):
            result=runner.run_gate('FIXTURE',matrix,run,{'allowed':[]},{},{})
        self.assertEqual(result['result'],'FAIL')
        self.assertFalse(result['failure_evidence_sealed'])
        joined=' '.join(row.get('reason','') for row in result.get('secondary_failures',[]))
        for expected in ('r7 supplement write leaf','r7 supplement close leaf',
                         'r7 supplement parent fsync leaf'):
            self.assertIn(expected,joined,result)


def load_tests(loader,_tests,_pattern):
    """Exclude the imported helper TestCase; it is discovered in its source module."""
    return loader.loadTestsFromTestCase(R7RunnerSupplementControl)


if __name__=='__main__':unittest.main(verbosity=2)
