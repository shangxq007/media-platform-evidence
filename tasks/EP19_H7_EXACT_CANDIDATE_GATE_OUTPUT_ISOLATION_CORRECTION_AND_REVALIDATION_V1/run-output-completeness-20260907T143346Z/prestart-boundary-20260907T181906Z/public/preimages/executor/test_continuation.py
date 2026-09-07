"""Bounded synthetic controls only. Fixtures and failed attempts are retained."""
from pathlib import Path
import errno, hashlib, json, os, subprocess, sys, unittest, uuid, warnings, zipfile
from unittest.mock import patch
import bindings, coverage, execution, freshness, observe, packaging, preservation, runner

D=execution.D
Q=D/'qualification/continuation-controls'
Q.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
class Controls(unittest.TestCase):
    def setUp(self):
        self.root=Q/(self._testMethodName+'-'+uuid.uuid4().hex);self.root.mkdir();self.addCleanup(self.receipt)
    def receipt(self):
        coverage.put(self.root/'control.json',{'test':self._testMethodName,'synthetic_only':True,'fixture_retained':True})
    def target(self):
        p=self.root/'allowed';p.mkdir();f=p/'target';f.write_bytes(b'allowed target bytes');return p,f
    def capture(self,root,**kwargs):
        r=preservation.Collector(roots=[root],expected_nonempty=[root],**kwargs).capture();coverage.put(self.root/('capture-'+uuid.uuid4().hex+'.json'),r);return r
    def test_collector_nonowned_ancestor_and_correct_hash(self):
        root,f=self.target();calls=[];native=os.open
        def record(path,flags,*args,**kwargs):calls.append((str(path),flags));return native(path,flags,*args,**kwargs)
        with patch('preservation.os.open',record):r=self.capture(root)
        self.assertEqual(r['result'],'COMPLETE');self.assertEqual(r['entries'][str(f)]['sha256'],sha(f.read_bytes()))
        self.assertNotEqual(Path('/').stat().st_uid,os.getuid())
        flags=next(flags for p,flags in calls if p=='/');self.assertTrue(flags&os.O_PATH);self.assertFalse(flags&os.O_NOATIME)
    def test_collector_symlink_escape(self):
        root,f=self.target();(root/'escape').symlink_to(self.root/'outside');(self.root/'outside').write_text('outside')
        r=self.capture(root);self.assertEqual(r['result'],'INCOMPLETE');self.assertNotIn(str(self.root/'outside'),r['entries'])
    def test_collector_symlink_ancestor(self):
        root,f=self.target();link=self.root/'link';link.symlink_to(root,target_is_directory=True)
        r=preservation.Collector(files=[link/'target']).capture();self.assertEqual(r['result'],'INCOMPLETE')
    def test_collector_empty_universe(self):
        root=self.root/'empty';root.mkdir();self.assertEqual(self.capture(root)['result'],'INCOMPLETE')
    def test_collector_expected_universe_mismatch(self):
        root,f=self.target();self.assertEqual(self.capture(root,expected_files=[])['result'],'INCOMPLETE')
    def test_collector_injected_read_oserror(self):
        root,f=self.target()
        def hook(phase,path):
            if phase=='read':raise OSError(errno.EACCES,'INJECTED_READ_ERROR_NOT_NATIVE_PERMISSION_SYSCALL')
        r=self.capture(root,hook=hook);self.assertEqual(r['native_exit'],1);self.assertEqual(r['errors'][0]['errno'],errno.EACCES)
    def test_collector_injected_enumeration_oserror(self):
        root,f=self.target()
        def hook(phase,path):
            if phase=='enumerate':raise OSError(errno.EACCES,'INJECTED_ENUMERATION_ERROR_NOT_NATIVE_PERMISSION_SYSCALL')
        self.assertEqual(self.capture(root,hook=hook)['result'],'INCOMPLETE')
    def test_collector_metadata_contract_no_restoration(self):
        root,f=self.target();before=preservation.metadata(f.stat());r=self.capture(root)
        self.assertEqual(before,preservation.metadata(f.stat()));self.assertNotIn('st_atime_ns',r['metadata_fields']);self.assertFalse(r['timestamp_restoration'])
    def test_collector_file_replacement(self):
        root,f=self.target()
        def hook(phase,path):
            if phase=='before_open' and path==f:f.rename(root/'old');f.write_bytes(b'allowed target bytes')
        self.assertEqual(self.capture(root,hook=hook)['result'],'INCOMPLETE')
    def test_collector_during_read_instability(self):
        root,f=self.target()
        def hook(phase,path):
            if phase=='after_read' and path==f:f.write_bytes(b'new')
        self.assertEqual(self.capture(root,hook=hook)['result'],'INCOMPLETE')
    def test_collector_directory_replacement(self):
        root,f=self.target()
        def hook(phase,path):
            if phase=='after_read' and path==root:root.rename(self.root/'old');root.mkdir()
        self.assertEqual(self.capture(root,hook=hook)['result'],'INCOMPLETE')
    def test_collector_ancestor_replacement(self):
        root,f=self.target();parent=self.root/'parent';parent.mkdir();root.rename(parent/'allowed');root=parent/'allowed';f=root/'target'
        def hook(phase,path):
            if phase=='after_read' and path==f:parent.rename(self.root/'moved');parent.mkdir()
        self.assertEqual(self.capture(root,hook=hook)['result'],'INCOMPLETE')
    def test_collector_cli_incomplete_is_nonzero(self):
        root=self.root/'empty';root.mkdir();cfg=self.root/'scope.json';cfg.write_text(json.dumps({'roots':[str(root)],'expected_nonempty':[str(root)]}))
        cmd=[sys.executable,'-B',str(D/'owned/preservation.py'),'--scope',str(cfg),'--output',str(self.root/'native-receipt.json')]
        r=subprocess.run(cmd,capture_output=True);(self.root/'native.log').write_bytes(r.stdout+r.stderr);self.assertEqual(r.returncode,1)
    def observe(self,code,**kwargs):
        p=self.root/'frozen';p.write_text('fixed');cmd=[sys.executable,'-B','-c',code]
        r=observe.run(cmd,self.root,self.root/'native.log',[p],[],[],[],timeout=5,**kwargs)
        coverage.put(self.root/'observation.json',r);return r
    def test_native_failure_independent_wrapper(self):
        r=self.observe('raise SystemExit(7)');self.assertEqual(r['native_exit'],7);self.assertEqual(r['wrapper_exit'],1)
    def test_tracked_drift_actual_acceptance_path(self):
        r=self.observe('from pathlib import Path;Path("frozen").write_text("changed")')
        r.update(run_id='synthetic',gate='SYNTHETIC',candidate=execution.SHA,tree=execution.TREE)
        with self.assertRaisesRegex(RuntimeError,'PRESERVATION_REJECT'):freshness.require_fresh_outputs([],{},r,'synthetic','SYNTHETIC',lambda:{'result':'PASS'})
    def test_deep_new_subtree_rejected(self):
        repo=self.root/'repo';(repo/'deep/empty').mkdir(parents=True);w=observe.Watch([], [repo],[],[])
        try:
            (repo/'deep/empty/new').mkdir();(repo/'deep/empty/new/x').write_text('new');w.drain();self.assertTrue(w.rejected());self.assertTrue(w.gaps)
        finally:w.close()
    def test_deep_deleted_directory_rejected(self):
        repo=self.root/'repo';(repo/'deep/empty').mkdir(parents=True);w=observe.Watch([], [repo],[],[])
        try:(repo/'deep/empty').rmdir();w.drain();self.assertTrue(w.rejected())
        finally:w.close()
    def test_instruction_runtime_metadata_drift_rejects(self):
        root,f=self.target();w=observe.Watch([],[],[],[],enumeration_roots=[root])
        try:f.chmod(0o600);w.drain();self.assertTrue(w.rejected())
        finally:w.close()
    def test_runtime_output_not_frozen(self):
        repo=self.root/'repo';repo.mkdir();out=repo/'build';out.mkdir();w=observe.Watch([], [repo],[],[out])
        try:(out/'log').write_text('grows');w.drain();self.assertFalse(w.rejected())
        finally:w.close()
    def shadow(self,variant):
        root=self.root/'shadow';root.mkdir();controlled=root/'control';controlled.write_text('fixed')
        def reconcile(events,tag):
            import copy
            import frozen_shadow_monitor as frozen
            from shadow_binding import dh
            before={'entries':[{'path':'control','stage':'0','mode':'100644','blob':'1'*40}],
                    'index_semantic_sha256':'a'*64,'index_byte_sha256':'b'*64,'head':execution.SHA,'head_state':execution.SHA+'\n','refs':''}
            after=copy.deepcopy(before);after['index_byte_sha256']='c'*64
            if variant=='semantic':after['entries'][0]['blob']='2'*40;after['index_semantic_sha256']='d'*64
            relative=[{**e,'path':str(Path(e['path']).relative_to(root))} for e in events if Path(e['path']).is_relative_to(root)]
            content={'result':'PASS','checked':1,'mismatches':[]}
            semantic=frozen.reconcile('SHADOW',before,after,relative,['control'],[])
            p={'result':'PASS','run_binding':tag,'root':str(root),'semantic_check':semantic,'final_content_check':content,
               'before_sha256':dh(before),'after_sha256':dh(after),'events_sha256':dh(relative),'final_content_sha256':dh(content),
               'evidence':{'before':before,'after':after,'events':relative,'final_content':content}}
            if variant=='wrong_digest':p['events_sha256']='0'*64
            if variant=='content_missing':del p['final_content_check']
            if variant=='content_fail':p['final_content_check']['result']='FAIL'
            if variant=='pending':p['result']='NEEDS_RECONCILIATION'
            if variant=='missing_evidence':del p['events_sha256']
            return p
        cmd=[sys.executable,'-B','-c','from pathlib import Path;p=Path('+repr(str(controlled))+');p.write_text("changed");p.write_text("fixed")']
        r=observe.run(cmd,self.root,self.root/'native.log',[controlled],[root],[],[],shadow_root=root,shadow_declared=['control'],shadow_reconciler=None if variant=='missing' else reconcile,timeout=5)
        coverage.put(self.root/'observation.json',r);return r
    def test_shadow_permitted_actual_observe_acceptance(self):self.assertEqual(self.shadow('pass')['wrapper_exit'],0)
    def test_shadow_missing_reconciler_rejects(self):self.assertEqual(self.shadow('missing')['wrapper_exit'],1)
    def test_shadow_missing_bound_evidence_rejects(self):self.assertEqual(self.shadow('missing_evidence')['wrapper_exit'],1)
    def test_shadow_semantic_delta_rejects(self):self.assertEqual(self.shadow('semantic')['wrapper_exit'],1)
    def test_shadow_missing_content_rejects(self):self.assertEqual(self.shadow('content_missing')['wrapper_exit'],1)
    def test_shadow_failed_content_rejects(self):self.assertEqual(self.shadow('content_fail')['wrapper_exit'],1)
    def test_shadow_pending_never_passes(self):self.assertEqual(self.shadow('pending')['wrapper_exit'],1)
    def manifest(self):
        data=b'candidate static';blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        m={'candidate':execution.SHA,'tree':execution.TREE,'transforms':'NONE_SUPPORTED','rows':[{'relative':'index.html','git_path':packaging.STATIC+'index.html','blob':blob,'sha256':sha(data),'mode':'100644'}]}
        root=self.root/'resources/static';root.mkdir(parents=True);(root/'index.html').write_bytes(data)
        return m,root,data
    def zip(self,data,extra=(),prefix='BOOT-INF/classes/'):
        p=self.root/('artifact-'+uuid.uuid4().hex+'.jar')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('META-INF/MANIFEST.MF','Manifest-Version: 1.0\nSpring-Boot-Classes: '+prefix+'\n')
                z.writestr(prefix+'static/index.html',data)
                for n,b in extra:z.writestr(n,b)
        return p
    def rule(self,prefix='BOOT-INF/classes/'):return {'task':':platform-app:bootJar','resources_task':':platform-app:processResources','boot_classes':prefix,'transforms':'NONE_SUPPORTED'}
    def test_packaging_resources_and_zip_positive(self):
        m,root,data=self.manifest();self.assertEqual(packaging.resources(m,root)['result'],'PASS');r=packaging.jar(m,self.zip(data),self.rule());self.assertEqual(r['result'],'PASS');coverage.put(self.root/'packaging.json',r)
    def test_packaging_discovers_prefix(self):
        m,root,data=self.manifest();prefix='ACTUAL/classes/';r=packaging.jar(m,self.zip(data,prefix=prefix),self.rule(prefix));self.assertEqual(r['discovered_prefix'],prefix)
    def test_packaging_missing_resource(self):
        m,root,data=self.manifest();(root/'index.html').unlink()
        with self.assertRaises(RuntimeError):packaging.resources(m,root)
    def test_packaging_extra_resource(self):
        m,root,data=self.manifest();(root/'extra').write_text('extra')
        with self.assertRaises(RuntimeError):packaging.resources(m,root)
    def test_packaging_wrong_candidate(self):
        m,root,data=self.manifest();m['candidate']='0'*40
        with self.assertRaises(RuntimeError):packaging.resources(m,root)
    def test_packaging_unsupported_transform(self):
        m,root,data=self.manifest();m['transforms']='minify'
        with self.assertRaises(RuntimeError):packaging.resources(m,root)
    def test_packaging_hash_mismatch(self):
        m,root,data=self.manifest()
        with self.assertRaises(RuntimeError):packaging.jar(m,self.zip(b'wrong'),self.rule())
    def test_packaging_zip_extra(self):
        m,root,data=self.manifest()
        with self.assertRaises(RuntimeError):packaging.jar(m,self.zip(data,[('BOOT-INF/classes/static/extra',b'x')]),self.rule())
    def test_packaging_zip_duplicate(self):
        m,root,data=self.manifest()
        with self.assertRaisesRegex(RuntimeError,'DUPLICATE'):packaging.jar(m,self.zip(data,[('BOOT-INF/classes/static/index.html',data)]),self.rule())
    def test_packaging_zip_conflict(self):
        m,root,data=self.manifest()
        with self.assertRaises(RuntimeError):packaging.jar(m,self.zip(data,[('BOOT-INF/classes/static/index.html/child',b'x')]),self.rule())
    def fresh(self,kind):
        output=self.root/'output.json';code='from pathlib import Path;Path("output.json").write_text(\'{"result":"PASS"}\')'
        if kind=='missing':code='pass'
        if kind=='native_failure':code='raise SystemExit(3)'
        if kind=='stale':output.write_text('{"result":"PASS"}');code='pass'
        before={str(output):'PRESENT' if output.exists() else 'ABSENT'}
        process=self.observe(code);process.update(run_id='synthetic',gate='SYNTHETIC',candidate=execution.SHA,tree=execution.TREE)
        if kind=='preservation':process['wrapper_exit']=1
        def parser():
            result=json.loads(output.read_text())
            if kind=='incomplete':raise RuntimeError('INCOMPLETE_REQUIRED_OUTPUT')
            if kind=='parser_pending':result['result']='PENDING'
            return result
        return freshness.require_fresh_outputs([output],before,process,'synthetic','SYNTHETIC',parser)
    def test_fresh_output_positive_actual_path(self):self.assertEqual(self.fresh('pass')['result'],'PASS')
    def test_fresh_missing_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('missing')
    def test_fresh_stale_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('stale')
    def test_fresh_native_failure_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('native_failure')
    def test_fresh_incomplete_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('incomplete')
    def test_fresh_unresolved_preservation_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('preservation')
    def test_fresh_pending_parser_reject(self):
        with self.assertRaises(RuntimeError):self.fresh('parser_pending')
    def test_bindings_exact_all_29(self):
        m=bindings.build(D/'outputs/continuation-runs/synthetic');old=json.loads((D/'GATE_EXECUTION_MATRIX.json').read_text());self.assertEqual(m['order'],old['order']);self.assertEqual(len(m['gates']),29)
        for n in m['order']:
            self.assertEqual(m['gates'][n]['authoritative_command'],old['gates'][n]['command']);self.assertTrue(m['gates'][n]['parser']);self.assertTrue(m['gates'][n]['required'])
    def test_detached_seal_rejects_mutation(self):
        p=self.root/'input';p.write_text('old');seal=coverage.seal([p]);p.write_text('new')
        with self.assertRaises(RuntimeError):coverage.check_seal(seal)
    def test_dependency_missing_or_wrong_run(self):
        with self.assertRaises(RuntimeError):freshness.dependency({'result':'PASS','run_id':'old'},'new')
    def test_packaging_wrong_blob_rejected(self):
        m,root,data=self.manifest();m['rows'][0]['blob']='0'*40
        with self.assertRaisesRegex(RuntimeError,'WRONG_GIT_BLOB'):packaging.resources(m,root)
    def test_packaging_missing_jar_rejects(self):
        m,root,data=self.manifest()
        with self.assertRaises(FileNotFoundError):packaging.jar(m,self.root/'not-built.jar',self.rule())
    def test_packaging_missing_zip_static(self):
        m,root,data=self.manifest();m['rows'][0].update(relative='missing.html',git_path=packaging.STATIC+'missing.html')
        with self.assertRaises(RuntimeError):packaging.jar(m,self.zip(data),self.rule())
    def test_primary_transient_index_write_strict(self):
        import frozen_shadow_monitor as frozen
        state={'entries':[],'index_semantic_sha256':'same','index_byte_sha256':'same','head':'same','head_state':'same','refs':'same'}
        r=frozen.reconcile('PRIMARY',state,state,[{'path':'.git/index.lock'}],[],[])
        self.assertEqual(r['result'],'FAIL_PRIMARY_GIT_METADATA_MUTATION')
    def test_shadow_frozen_semantics_not_modified(self):
        self.assertEqual(coverage.digest(D/'owned/frozen_shadow_monitor.py'),coverage.digest(D/'inputs/original-shadow_monitor.py'))
    def test_runtime_namespace_command_paths(self):
        run=D/'outputs/continuation-runs/synthetic';m=bindings.build(run)
        for gate in m['gates'].values():
            for word in gate['command']:
                self.assertNotIn(str(D/'outputs/backend'),word);self.assertNotIn(str(D/'outputs/frontend'),word)
            self.assertTrue(gate['environment_namespaces']['TMPDIR'].startswith(str(run)))
    def test_cleanup_preserves_preimage(self):
        p=self.root/'output';p.write_bytes(b'old');rows=freshness.preserve_cleanup([p],self.root/'cleanup-preimages',[self.root])
        self.assertFalse(p.exists());self.assertEqual(Path(rows[0]['preimage']).read_bytes(),b'old')
    def test_readonly_registered_ancestor_replacement(self):
        p=self.root/'parent';p.mkdir();f=p/'input';f.write_text('fixed');w=observe.Watch([f],[],[],[])
        try:p.rename(self.root/'moved');p.mkdir();w.drain();self.assertTrue(w.rejected())
        finally:w.close()
    def test_shared_loose_object_pending_not_pass(self):
        root=self.root/'git';(root/'objects/aa').mkdir(parents=True);w=observe.Watch([],[],[root],[],shared_git=root)
        try:
            f=root/'objects/aa'/('b'*38);f.write_bytes(b'not a git object');w.drain();w.resolve_shared();self.assertTrue(w.rejected())
        finally:w.close()
    def test_frontend_ref_lock_without_bound_target_rejected(self):
        root=self.root/'git';(root/'refs/heads').mkdir(parents=True);ref=root/'refs/heads/frontend';ref.write_text('0'*40);w=observe.Watch([],[],[root],[],cross_lane=[ref],shared_git=root)
        try:
            lock=Path(str(ref)+'.lock');lock.write_text('0'*40);lock.unlink();w.drain();w.resolve_frontend_locks();self.assertTrue(w.rejected())
        finally:w.close()
    def test_frontend_native_readonly_and_private_pid(self):
        import time
        front=self.root/'front';front.mkdir();back=self.root/'back';back.mkdir()
        code="""from pathlib import Path
import errno,subprocess,sys
front=Path(sys.argv[1]);back=Path(sys.argv[2]);(front/'allowed').write_text('allowed')
try:
 (back/'forbidden').write_text('forbidden')
 raise AssertionError('ESCAPED_WRITE')
except OSError as e:
 assert e.errno==errno.EROFS,e
child='import time;from pathlib import Path;time.sleep(.2);Path('+repr(str(front/'escaped'))+').write_text("escaped")'
subprocess.Popen([sys.executable,'-B','-c',child],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('FRONTEND_READONLY_PRIVATE_PID=PASS')
"""
        cmd=execution.frontend_sandbox([sys.executable,'-B','-c',code,str(front),str(back)],front,[front])
        r=subprocess.run(cmd,capture_output=True);(self.root/'native.log').write_bytes(r.stdout+r.stderr)
        coverage.put(self.root/'process.json',{'argv':cmd,'native_exit':r.returncode,'synthetic_only':True})
        self.assertEqual(r.returncode,0,r.stderr.decode());time.sleep(.4)
        self.assertFalse((back/'forbidden').exists());self.assertFalse((front/'escaped').exists());self.assertTrue((front/'allowed').is_file())
    def test_changed_resolved_dependency_rejects(self):
        with self.assertRaisesRegex(RuntimeError,'DEPENDENCY_CHANGED'):freshness.compare_dependencies({'a':{'sha256':'old'}},{'a':{'sha256':'new'}})
    def test_new_resolved_dependency_is_explicit_output(self):
        r=freshness.compare_dependencies({'a':{'sha256':'fixed'}},{'a':{'sha256':'fixed'},'b':{'sha256':'new'}})
        self.assertEqual(r['unchanged_existing'],1);self.assertEqual(set(r['newly_resolved']),{'b'})
    def test_source_bound_existing_absence_preserved(self):
        absent=self.root/'historically-missing'
        r=preservation.Collector(files=[absent],expected_missing=[absent]).capture()
        self.assertEqual(r['result'],'COMPLETE');self.assertTrue(r['entries'][str(absent)]['expected_absence'])
    def test_expected_absence_reappearance_rejects(self):
        p=self.root/'historically-missing';p.write_text('unexpected repair')
        self.assertEqual(preservation.Collector(files=[p],expected_missing=[p]).capture()['result'],'INCOMPLETE')
    def test_new_unexpected_missing_stays_failure(self):
        self.assertEqual(preservation.Collector(files=[self.root/'missing']).capture()['result'],'INCOMPLETE')
    def test_missing_ancestor_not_expected_leaf_absence(self):
        p=self.root/'missing-parent/leaf'
        self.assertEqual(preservation.Collector(files=[p],expected_missing=[p]).capture()['result'],'INCOMPLETE')
    def test_shadow_wrong_evidence_digest_rejects(self):self.assertEqual(self.shadow('wrong_digest')['wrapper_exit'],1)
    def test_failed_dependency_stops_actual_graph_and_keeps_all_keys(self):
        calls=[];failures=[]
        def execute(name,results):calls.append(name);return {'result':'FAIL','native_exit':7,'wrapper_exit':1}
        result,stopped=runner.execute_graph(['A','B','C'],execute,lambda name,r:failures.append(name),'synthetic')
        self.assertTrue(stopped);self.assertEqual(calls,['A']);self.assertEqual(failures,['A']);self.assertEqual(set(result),{'A','B','C'});self.assertEqual(result['B']['result'],'NOT_RUN');self.assertEqual(result['C']['result'],'NOT_RUN')
    def test_backend_untagged_detached_child_remains_observed(self):
        p=self.root/'frozen'
        child='import os,time;from pathlib import Path;os.environ.pop("EP19_GATE_SCOPE",None);os.setsid();os.chdir("/");time.sleep(.2);Path('+repr(str(p))+').write_text("late")'
        parent='import subprocess,sys;subprocess.Popen([sys.executable,"-B","-c",'+repr(child)+'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)'
        r=self.observe(parent);self.assertEqual(r['native_exit'],0);self.assertEqual(r['wrapper_exit'],1);self.assertEqual(r['owned_processes_remaining'],[])
if __name__=='__main__':unittest.main(verbosity=2)
