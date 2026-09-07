"""Only bounded fixtures; actual runner.run_all/preflight decisions remain unmocked.

The launch fixture substitutes data roots and gate bodies, not authorization,
seal, baseline, coverage, qualification, candidate identity, or decision functions.
A synthetic qualification PASS inside this fixture is never the real FORMAL result.
"""
from pathlib import Path
import copy, hashlib, io, json, os, shutil, subprocess, sys, time, unittest, uuid, zlib
from unittest.mock import patch
import artifacts, namespaces
import bindings, coverage, execution, freshness, observe, runner, frozen_shadow_monitor as frozen

D=execution.D
O=execution.O
E=O/'owner-clarified-execution-20260907T1120Z'
ATTEMPT=Path(os.environ['EP19_QUALIFICATION_DIR']).absolute()
if not ATTEMPT.is_relative_to(D/'qualification') or ATTEMPT.resolve()!=ATTEMPT:
    raise RuntimeError('QUALIFICATION_FIXTURE_SCOPE')
ATTEMPT.mkdir(parents=True,exist_ok=False)

def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    coverage.put(p,v)

def replace_json(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def load(p):return json.loads(p.read_text())

class LaunchControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mirror=ATTEMPT/'launch-data';cls.mirror.mkdir()
        shutil.copytree(execution.H,cls.mirror/'owned')
        shutil.copytree(O/'inputs',cls.mirror/'inputs')
        cls.repo=cls.mirror/'candidate'
        namespaces.clone(O/'sources/backend',cls.repo)
        for name in ('GATE_EXECUTION_MATRIX.json',):shutil.copyfile(O/name,cls.mirror/name)
        auth=cls.mirror/'owner-clarified-execution-20260907T1120Z';auth.mkdir()
        for name in ('OWNER_DECISION.txt','OWNER_PROVENANCE.json'):shutil.copyfile(E/name,auth/name)
        (auth/'ENGINEERING_MAPPING.md').write_text('SYNTHETIC FIXTURE MAPPING, NOT REAL COVERAGE\n')
        (cls.mirror/'qualification').mkdir()
        shutil.copyfile(O/'qualification/CONTINUATION_PRESERVATION_CONTRACT.md',cls.mirror/'qualification/CONTINUATION_PRESERVATION_CONTRACT.md')
        cls.old={'protected':[],'allowed':[],'repositories':[],'metadata_roots':[],'cross_lane':[],
                 'shared_git':None,'shadow_root':str(D/'sources/shadow-fixture'),'shadow_declared':[
                 'typed-schema-module/jooq-baseline.properties','typed-schema-module/jooq-plain-sql-allowlist.txt',
                 'typed-schema-module/jooq-dynamic-identifier-allowlist.txt']}
        put(cls.mirror/'PROTECTION_SCOPE.json',cls.old)
    def setUp(self):
        self.root=self.mirror/self._testMethodName;self.root.mkdir()
        self.patches=[patch.object(coverage,'O',self.mirror),patch.object(bindings,'O',self.mirror),patch.object(namespaces,'O',self.mirror),
                      patch.object(runner,'O',self.mirror),patch.object(runner,'AUTHORITY',self.mirror/'owner-clarified-execution-20260907T1120Z'),
                      patch.object(namespaces,'repos',return_value=[self.repo]),
                      patch.object(namespaces,'mappings',return_value={str(O/'sources/backend'):str(self.repo)})]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.run=runner.runpath('runtime-'+uuid.uuid4().hex);self.run.mkdir(parents=True);(self.run/'runtime').mkdir()
        if self._testMethodName=='test_pending_review_actual_launch_and_completion':
            namespaces.clone(O/'sources/backend',self.run/'sources/shadow-fixture')
        init=self.run/'runtime/cache/backend/gradle/init.d';init.mkdir(parents=True)
        shutil.copyfile(self.mirror/'owned/packaging.init.gradle',init/'ep19-packaging.gradle')
        lean=self.run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean';lean.parent.mkdir(parents=True);lean.write_text('SYNTHETIC TOOL PRESENCE ONLY; NEVER EXECUTED\n')
        self.q=self.root/'qualification.json'
        raw=self.root/'synthetic-native.log';raw.write_text('SYNTHETIC DATA FOR LAUNCH CONTROLS ONLY\n')
        process=self.root/'synthetic-process.json';put(process,{'native_exit':0,'raw_log':str(raw),'log_sha256':coverage.digest(raw),'formal_wrapper_sha256':coverage.digest(self.mirror/'owned/execution.py')})
        result=self.root/'synthetic-result.json';put(result,{'result':'PASS','tests':1,'failures':0,'errors':0})
        program=self.root/'synthetic-program.py';program.write_text('# Synthetic closure target, never executed\n')
        ledger=self.root/'synthetic-reuse.json';put(ledger,{'synthetic_only':True})
        formal=self.root/'synthetic-formal-boundary.json';inv=load(self.mirror/'inputs/PROOF_GATE_INVENTORY.json')
        put(formal,{'result':'PASS','synthetic_only':True,'container_ids':['synthetic-only-no-real-container'],'containers_remaining':[],
                    'coq_image':inv['environment']['COQ_IMAGE'],'observed_coq_image_id':inv['coq_image_id_raw'],
                    'script_sha256':inv['pins']['candidate/scripts/formal/validate-faof2.sh'],
                    'formal_wrapper_sha256':coverage.digest(self.mirror/'owned/execution.py'),'probe_program':str(program),'process_receipts':[str(process)],
                    **{k:'PASS' for k in ('namespace_tmp_probe','container_tool_visibility','namespace_bind_interpretation','output_path_provenance','container_cleanup','unchanged_source')}})
        helpers=coverage.seal(coverage.local_imports()[0]);files={**helpers,**coverage.seal([raw,process,result,program,ledger,formal])}
        put(self.q,{'schema':'ep19-owner-qualified-v1','result':'PASS','helpers':helpers,'dependencies':files,
                    'formal_boundary_receipt':str(formal),'qualification_program':str(program),'raw_log':str(raw),'process_receipt':str(process),
                    'result_receipt':str(result),'reuse_ledger':str(ledger),'product_gate_execution':False,'real_gradle_instrumentation':'PASS',
                    **{k:'PASS' for k in ('frontend_boundary','formal_boundary','collector','coverage','shadow','packaging','freshness','launch')}})
        put(self.run/'prepare.json',{'qualification':str(self.q)})
        put(self.run/'bindings.json',bindings.build(self.run))
        put(self.run/'namespaces.json',{'synthetic_fixture_mapping':str(self.repo)})
        put(self.run/'identity.json',{'synthetic_scope':True})
        put(self.run/'source-recovery.json',{'synthetic_scope':True})
        py=Path(sys.executable).resolve();put(self.run/'toolchain.json',{'python3':{'path':str(py),'realpath':str(py),'sha256':coverage.digest(py)}})
        inputs=coverage.qualification_inputs(self.q)+[self.mirror/'owner-clarified-execution-20260907T1120Z'/n for n in ('OWNER_DECISION.txt','OWNER_PROVENANCE.json','ENGINEERING_MAPPING.md')]
        inputs += [self.mirror/n for n in ('GATE_EXECUTION_MATRIX.json','PROTECTION_SCOPE.json','qualification/CONTINUATION_PRESERVATION_CONTRACT.md')]
        inputs += [p for p in (self.mirror/'inputs').rglob('*') if p.is_file()]
        inputs += [init/'ep19-packaging.gradle',lean]
        scope={**self.old,'protected':sorted(set(map(str,inputs))), 'allowed':[str(self.run/'runtime')],
               'enumeration_roots':[],'pruned_roots':[],'expected_missing':[],
               'frozen_roots':[str(init),str(self.run/'runtime/cache/backend/formal-tools')],
               'instruction_capture':{'result':'COMPLETE','entries':{}},'synthetic_only':True}
        scope=namespaces.scope_roles(scope,self.run)
        put(self.run/'scope.json',scope)
        put(self.run/'baseline.json',{'result':'COMPLETE','entries':observe.snapshot(scope['protected'])})
        self.seal_inputs=inputs+[self.run/(n+'.json') for n in ('prepare','bindings','identity','source-recovery','toolchain','scope','baseline','namespaces')]
        self.seal()
        put(self.run/'preflight.json',{'result':'ENGINEERING_READY','engineering_blockers':[],'run_id':self.run.name,'candidate':execution.SHA,'tree':execution.TREE,'base':execution.BASE,'synthetic_only':True})
        self.review=self.root/'engineering-launch.json'
        self.decision={'engineering_execution_authorization':'OWNER_AUTHORIZED','owner_decision_sha256':runner.OWNER_SHA256,
                       'independent_review':'PENDING',**runner.REVIEW_STATES,
                       'run_id':self.run.name,'candidate':execution.SHA,'tree':execution.TREE,'base':execution.BASE}
        self.bind_review()
        self.calls=[]
        def synthetic_gate(name,m,run,scope,sealed,results):
            self.calls.append(name)
            gate=run/'runtime/gates'/name;gate.mkdir(parents=True)
            return artifacts.finalize({'result':'PASS','native_exit':0,'wrapper_exit':0,
                'run_id':run.name,'gate':name,'candidate':execution.SHA,'tree':execution.TREE,
                'synthetic_only':True},gate,[self.root/'synthetic-native.log'])
        p=patch.object(runner,'run_gate',synthetic_gate);p.start();self.addCleanup(p.stop)
    def seal(self):
        replace_json(self.run/'seal.json',{'files':coverage.seal(self.seal_inputs),'run_id':self.run.name,'candidate':execution.SHA,'tree':execution.TREE,'base':execution.BASE})
    def bind_review(self):
        self.decision.update(seal_sha256=coverage.digest(self.run/'seal.json'),preflight_sha256=coverage.digest(self.run/'preflight.json'))
        replace_json(self.review,self.decision)
    def reject(self,reason):
        with self.assertRaisesRegex((RuntimeError,FileNotFoundError),reason):runner.run_all(self.run,self.review)
        self.assertEqual(self.calls,[]);self.assertFalse((self.run/'runtime/START.json').exists())
    def test_pending_review_actual_launch_and_completion(self):
        self.assertEqual(runner.run_all(self.run,self.review),0)
        self.assertEqual(self.calls,load(self.run/'bindings.json')['order'])
        r=load(self.run/'runtime/RESULTS.json')
        self.assertEqual(r['independent_review'],'PENDING')
        for k,v in runner.REVIEW_STATES.items():self.assertEqual(r[k],v)
        with self.assertRaisesRegex(RuntimeError,'NO_RETRY'):runner.run_all(self.run,self.review)
    def test_missing_execution_authorization(self):
        self.decision.pop('engineering_execution_authorization');self.bind_review();self.reject('AUTHORIZATION_REQUIRED')
    def test_unbound_owner_authorization(self):
        self.decision['owner_decision_sha256']='0'*64;self.bind_review();self.reject('AUTHORIZATION_UNBOUND')
    def test_failed_preflight(self):
        p=load(self.run/'preflight.json');p['result']='ENGINEERING_PREFLIGHT_BLOCKED';replace_json(self.run/'preflight.json',p);self.bind_review();self.reject('PREFLIGHT_NOT_READY')
    def test_incomplete_preflight(self):
        p=load(self.run/'preflight.json');p.pop('engineering_blockers');replace_json(self.run/'preflight.json',p);self.bind_review();self.reject('PREFLIGHT_NOT_READY')
    def test_wrong_candidate(self):
        self.decision['candidate']='0'*40;self.bind_review();self.reject('IDENTITY_MISMATCH')
    def test_wrong_tree(self):
        self.decision['tree']='0'*40;self.bind_review();self.reject('IDENTITY_MISMATCH')
    def test_wrong_base(self):
        self.decision['base']='0'*40;self.bind_review();self.reject('IDENTITY_MISMATCH')
    def test_independent_accept_cannot_be_fabricated(self):
        self.decision['independent_review']='ACCEPT';self.bind_review();self.reject('STATES_MUST_STAY_SEPARATE')
    def test_publication_cannot_be_granted(self):
        self.decision['product_publication']='AUTHORIZED';self.bind_review();self.reject('STATES_MUST_STAY_SEPARATE')
    def test_harness_replacement_cannot_be_granted(self):
        self.decision['publication_harness_replacement']='AUTHORIZED';self.bind_review();self.reject('STATES_MUST_STAY_SEPARATE')
    def test_unbound_preflight_receipt(self):
        self.decision['preflight_sha256']='0'*64;replace_json(self.review,self.decision);self.reject('UNBOUND_ENGINEERING')
    def test_qualification_program_changed(self):
        (self.root/'synthetic-program.py').write_text('changed\n');self.reject('FROZEN_INPUT_CHANGED')
    def test_qualification_raw_log_changed(self):
        (self.root/'synthetic-native.log').write_text('changed\n');self.reject('FROZEN_INPUT_CHANGED')
    def test_qualification_result_changed(self):
        (self.root/'synthetic-result.json').write_text('{}\n');self.reject('FROZEN_INPUT_CHANGED')
    def test_qualification_closure_missing(self):
        q=load(self.q);q['dependencies'].pop(q['raw_log']);replace_json(self.q,q)
        self.seal();self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_current_formal_boundary_rejects_old_ready_record(self):
        q=load(self.q);q['formal_boundary']='BLOCKED';replace_json(self.q,q)
        self.seal();self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_formal_pass_label_cannot_override_blocked_actual_receipt(self):
        formal=self.root/'synthetic-formal-boundary.json';r=load(formal);r['result']='BLOCKED';replace_json(formal,r)
        q=load(self.q);q['dependencies'][str(formal)]=coverage.digest(formal);replace_json(self.q,q)
        self.seal();self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_formal_pass_without_bound_process_evidence_rejects(self):
        formal=self.root/'synthetic-formal-boundary.json';r=load(formal);r['process_receipts']=[];replace_json(formal,r)
        q=load(self.q);q['dependencies'][str(formal)]=coverage.digest(formal);replace_json(self.q,q)
        self.seal();self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_current_baseline_rejects_old_ready_record(self):
        b=load(self.run/'baseline.json');b['entries'].pop(next(iter(b['entries'])));replace_json(self.run/'baseline.json',b)
        self.seal();self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_runtime_init_changed_rejects(self):
        (self.run/'runtime/cache/backend/gradle/init.d/ep19-packaging.gradle').write_text('changed\n');self.reject('FROZEN_INPUT_CHANGED')
    def test_runtime_extra_init_rejects(self):
        (self.run/'runtime/cache/backend/gradle/init.d/extra.gradle').write_text('new\n');self.reject('UNDECLARED_GRADLE_INIT')
    def test_run_control_omitted_from_seal_rejects(self):
        seal=load(self.run/'seal.json');seal['files'].pop(str(self.run/'bindings.json'))
        replace_json(self.run/'seal.json',seal);self.bind_review();self.reject('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    def test_missing_lean_rejects_current_preflight(self):
        (self.run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean').unlink();self.reject('lean')

class PreservationControls(unittest.TestCase):
    def setUp(self):
        self.root=ATTEMPT/self._testMethodName;self.root.mkdir()
    def observed(self,relative,shadow=False,variant='same',restore=True):
        root=self.root/'repo';root.mkdir();(root/'.git').mkdir()
        declared=['typed-schema-module/jooq-baseline.properties','typed-schema-module/jooq-plain-sql-allowlist.txt','typed-schema-module/jooq-dynamic-identifier-allowlist.txt']
        tracked=[root/p for p in [*declared,'ordinary']]
        for p in tracked:p.parent.mkdir(exist_ok=True);p.write_text('fixed')
        for name in ('index','HEAD','config'):(root/'.git'/name).write_text('fixed')
        target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.write_text('fixed')
        state={'entries':[{'path':str(p.relative_to(root)),'stage':'0','mode':'100644','blob':'1'*40} for p in tracked],
               'index_semantic_sha256':'a'*64,'index_byte_sha256':'b'*64,'head':execution.SHA,'head_state':execution.SHA,'refs':'fixed'}
        def reconcile(events,tag):
            from shadow_binding import dh
            after=copy.deepcopy(state)
            if relative.startswith('.git/index'):after['index_byte_sha256']='c'*64
            if variant in ('semantic','mode','stage','blob','add','remove'):
                after['index_semantic_sha256']='d'*64
                if variant=='mode':after['entries'][0]['mode']='100755'
                elif variant=='stage':after['entries'][0]['stage']='1'
                elif variant=='blob':after['entries'][0]['blob']='2'*40
                elif variant=='add':after['entries'].append({'path':'extra','stage':'0','mode':'100644','blob':'1'*40})
                elif variant=='remove':after['entries'].pop()
            if variant=='head':after['head']='0'*40
            if variant=='refs':after['refs']='changed'
            relative_events=[{**e,'path':str(Path(e['path']).relative_to(root))} for e in events if Path(e['path']).is_relative_to(root)]
            dirty=[str(p.relative_to(root)) for p in tracked if p.read_text()!='fixed']
            content={'result':'FAIL' if dirty else 'PASS','checked':len(tracked),'mismatches':dirty}
            semantic=frozen.reconcile('SHADOW',state,after,relative_events,declared,dirty)
            evidence={'before':state,'after':after,'events':relative_events,'final_content':content}
            return {'result':'PASS' if semantic['result']=='PASS' and not dirty else 'FAIL','run_binding':tag,'root':str(root),
                    'semantic_check':semantic,'final_content_check':content,'evidence':evidence,
                    **{k+'_sha256':dh(v) for k,v in evidence.items()}}
        code='from pathlib import Path;p=Path('+repr(str(target))+');p.write_text("changed");'+('p.write_text("fixed")' if restore else '')
        r=observe.run([sys.executable,'-B','-c',code],root,self.root/'native.log',tracked,[root],[root/'.git'],[],
                      shadow_root=root if shadow else None,shadow_declared=declared,shadow_reconciler=reconcile if shadow else None,timeout=5)
        put(self.root/'observation.json',r);return r
    def test_primary_transient_content_event(self):self.assertEqual(self.observed('ordinary')['wrapper_exit'],1)
    def test_primary_transient_index_event(self):self.assertEqual(self.observed('.git/index')['wrapper_exit'],1)
    def test_primary_declared_shadow_path_still_rejects(self):self.assertEqual(self.observed('typed-schema-module/jooq-baseline.properties')['wrapper_exit'],1)
    def test_shadow_index_semantic_refresh_allowed(self):self.assertEqual(self.observed('.git/index',True)['wrapper_exit'],0)
    def test_shadow_index_lock_semantic_refresh_allowed(self):self.assertEqual(self.observed('.git/index.lock',True)['wrapper_exit'],0)
    def test_shadow_all_declared_paths_restored(self):
        for name in ('jooq-baseline.properties','jooq-plain-sql-allowlist.txt','jooq-dynamic-identifier-allowlist.txt'):
            with self.subTest(name=name):
                old=self.root;self.root=old/name;self.root.mkdir()
                self.assertEqual(self.observed('typed-schema-module/'+name,True)['wrapper_exit'],0);self.root=old
    def test_shadow_all_semantic_deltas_reject(self):
        for variant in ('semantic','mode','stage','blob','add','remove','head','refs'):
            with self.subTest(variant=variant):
                old=self.root;self.root=old/variant;self.root.mkdir()
                self.assertEqual(self.observed('.git/index',True,variant)['wrapper_exit'],1);self.root=old
    def test_shadow_head_event_rejects_even_restored(self):self.assertEqual(self.observed('.git/HEAD',True)['wrapper_exit'],1)
    def test_shadow_ref_event_rejects_even_restored(self):self.assertEqual(self.observed('.git/refs/heads/main',True)['wrapper_exit'],1)
    def test_shadow_unclassified_metadata_rejects(self):self.assertEqual(self.observed('.git/config',True)['wrapper_exit'],1)
    def test_shadow_undeclared_content_restored_rejects(self):self.assertEqual(self.observed('ordinary',True)['wrapper_exit'],1)
    def test_shadow_final_declared_content_mismatch_rejects(self):self.assertEqual(self.observed('typed-schema-module/jooq-baseline.properties',True,restore=False)['wrapper_exit'],1)
    def test_runtime_init_transient_write_rejects(self):
        cache=self.root/'cache';init=cache/'gradle/init.d';init.mkdir(parents=True);f=init/'ep19.gradle';f.write_text('fixed')
        cmd=[sys.executable,'-B','-c','from pathlib import Path;p=Path('+repr(str(f))+');p.write_text("change");p.write_text("fixed")']
        r=observe.run(cmd,self.root,self.root/'native.log',[f],[],[],[cache],frozen_roots=[init]);put(self.root/'observation.json',r)
        self.assertEqual(r['wrapper_exit'],1)
    def test_runtime_new_init_rejects(self):
        cache=self.root/'cache';init=cache/'gradle/init.d';init.mkdir(parents=True);f=init/'new.gradle'
        cmd=[sys.executable,'-B','-c','from pathlib import Path;Path('+repr(str(f))+').write_text("new")']
        r=observe.run(cmd,self.root,self.root/'native.log',[],[],[],[cache],frozen_roots=[init],enumeration_roots=[init]);put(self.root/'observation.json',r)
        self.assertEqual(r['wrapper_exit'],1)
    def test_shadow_missing_required_controls_reject_native_success(self):
        import parsers
        gate=self.root/'gate';gate.mkdir()
        (gate/'native.log').write_text('OK: PFIRR1-B1 jOOQ authority verification is fail-closed and non-mutating\n')
        process={'native_exit':0,'wrapper_exit':0,'run_id':'synthetic','gate':'SHADOW','candidate':execution.SHA,'tree':execution.TREE}
        with self.assertRaisesRegex(RuntimeError,'SHADOW_EXPECTED_CONTROL_COUNT'):
            freshness.require_fresh_outputs([],{},process,'synthetic','SHADOW',lambda:parsers.parse('SHADOW',self.root,gate,self.root))
    def test_shadow_required_controls_accept_after_integrity_success(self):
        import parsers
        gate=self.root/'gate';gate.mkdir()
        (gate/'native.log').write_text(''.join('PASS: control'+str(i)+' rejects missing authority and does not recreate file\n' for i in range(3))+
                                      'OK: PFIRR1-B1 jOOQ authority verification is fail-closed and non-mutating\n')
        process={'native_exit':0,'wrapper_exit':0,'run_id':'synthetic','gate':'SHADOW','candidate':execution.SHA,'tree':execution.TREE}
        self.assertEqual(freshness.require_fresh_outputs([],{},process,'synthetic','SHADOW',lambda:parsers.parse('SHADOW',self.root,gate,self.root))['result'],'PASS')
    def test_alternate_index_forbidden(self):
        with self.assertRaisesRegex(RuntimeError,'ALTERNATE_INDEX_FORBIDDEN'):
            observe.run([sys.executable,'-B','-c','pass'],self.root,self.root/'native.log',[],[],[],[],env={'GIT_INDEX_FILE':str(self.root/'index')})
    def shared(self,variant):
        # Hand-encoded synthetic Git objects; no commit/ref operation touches a repository.
        g=self.root/'git';(g/'objects').mkdir(parents=True);(g/'refs/heads/agent').mkdir(parents=True)
        (g/'HEAD').write_text('ref: refs/heads/agent/synthetic-frontend\n')
        def obj(kind,data):
            full=kind.encode()+b' '+str(len(data)).encode()+b'\0'+data;oid=hashlib.sha1(full).hexdigest()
            p=g/'objects'/oid[:2]/oid[2:];p.parent.mkdir(exist_ok=True);p.write_bytes(zlib.compress(full));return oid,p
        blob,bp=obj('blob',b'synthetic frontend');tree,tp=obj('tree',b'100644 file\0'+bytes.fromhex(blob))
        commit,cp=obj('commit',('tree '+tree+'\nauthor Synthetic <synthetic@example.invalid> 1 +0000\ncommitter Synthetic <synthetic@example.invalid> 1 +0000\n\nfixture\n').encode())
        ref=g/'refs/heads/agent/synthetic-frontend';ref.write_text(commit+'\n')
        w=observe.Watch([],[],[g],[],cross_lane=[ref],shared_git=g)
        try:
            # Only the new object membership is synthetic; git reachability and
            # zlib/content hashing in the actual resolver execute without mocks.
            w.metadata_files.remove(bp)
            if variant=='unreachable':
                _,bp=obj('blob',b'unreachable')
            if variant=='corrupt':bp.write_bytes(b'not a git object')
            if variant=='symlink':
                raw=bp.read_bytes();bp.unlink();target=self.root/'body';target.write_bytes(raw);bp.symlink_to(target)
            w.events=[{'path':str(bp),'category':'PENDING_SHARED_OBJECT_SCOPE_PROOF','mask':8}]
            w.resolve_shared();put(self.root/'shared-proof.json',{'events':w.events,'proof':w.shared_proof,'rejected':w.rejected()})
            return w.events[0]['category']
        finally:w.close()
    def test_frontend_new_append_actual_observer_rejects_unknown_writer(self):
        g=self.root/'git';(g/'objects').mkdir(parents=True);(g/'refs/heads/agent').mkdir(parents=True)
        ref=g/'refs/heads/agent/synthetic-frontend'
        (g/'HEAD').write_text('ref: refs/heads/agent/synthetic-frontend\n')
        def encoded(kind,data):
            body=kind.encode()+b' '+str(len(data)).encode()+b'\0'+data
            oid=hashlib.sha1(body).hexdigest();p=g/'objects'/oid[:2]/oid[2:]
            p.parent.mkdir(exist_ok=True);return oid,p,zlib.compress(body)
        def commit(tree,parent=''):
            return ('tree '+tree+'\n'+('parent '+parent+'\n' if parent else '')+
                    'author Synthetic <synthetic@example.invalid> 1 +0000\ncommitter Synthetic <synthetic@example.invalid> 1 +0000\n\nfixture\n').encode()
        tree,tp,raw=encoded('tree',b'');tp.write_bytes(raw)
        base,bp,raw=encoded('commit',commit(tree));bp.write_bytes(raw);ref.write_text(base+'\n')
        blob,p1,r1=encoded('blob',b'new frontend bytes')
        tree,p2,r2=encoded('tree',b'100644 file\0'+bytes.fromhex(blob))
        tip,p3,r3=encoded('commit',commit(tree,base))
        plan=self.root/'append-input.json';put(plan,{'objects':{str(p):r.hex() for p,r in [(p1,r1),(p2,r2),(p3,r3)]},'ref':str(ref),'tip':tip})
        code='import json;from pathlib import Path;p=json.loads(Path('+repr(str(plan))+').read_text());[Path(n).write_bytes(bytes.fromhex(b)) for n,b in p["objects"].items()];Path(p["ref"]).write_text(p["tip"]+"\\n")'
        r=observe.run([sys.executable,'-B','-c',code],self.root,self.root/'native.log',[],[],[g],[],cross_lane=[ref],shared_git=g,timeout=5)
        put(self.root/'observation.json',r)
        self.assertEqual(r['wrapper_exit'],1,r)
        self.assertTrue(any(e['category']=='REJECT_UNRESOLVED_SHARED_METADATA_SCOPE' for e in r['events']))
    def test_frontend_reachable_new_object_still_rejects(self):self.assertEqual(self.shared('pass'),'REJECT_UNRESOLVED_SHARED_METADATA_SCOPE')
    def test_frontend_unreachable_new_object_rejects(self):self.assertTrue(self.shared('unreachable').startswith('REJECT'))
    def test_frontend_corrupt_new_object_rejects(self):self.assertTrue(self.shared('corrupt').startswith('REJECT'))
    def test_frontend_symlink_new_object_rejects(self):self.assertTrue(self.shared('symlink').startswith('REJECT'))

if __name__=='__main__':
    # Re-execute existing controls with only their fixture destination redirected.
    # The unknown-writer legacy test_contract is neither imported nor executed.
    import test_continuation
    test_continuation.Q=ATTEMPT/'recovered-controls';test_continuation.Q.mkdir()
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(test_continuation.Controls),
                             unittest.defaultTestLoader.loadTestsFromTestCase(LaunchControls),
                             unittest.defaultTestLoader.loadTestsFromTestCase(PreservationControls)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    put(ATTEMPT/'RESULT.json',{'result':'PASS' if result.wasSuccessful() else 'FAIL','tests':result.testsRun,
                             'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
                             'synthetic_only':True,'product_gates':'NOT_RUN'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
