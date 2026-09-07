"""One integrated executor: prepare/baseline/preflight are distinct from parent-only run.

No historical module is imported. Every failed formal invocation permanently stops
this run namespace. Synthetic controls use freshness.require_fresh_outputs too.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time, traceback
import namespaces, artifacts, compile_inventory
import bindings, coverage, freshness, observe, packaging, parsers, shadow_binding, engineering
from execution import D,O,H,BASE,SHA,TREE,exact,git,environment,frontend_sandbox,formal_sandbox
from preservation import Collector,INSTRUCTIONS

def repos(run):return namespaces.repos(run)
AUTHORITY=O/'owner-clarified-execution-20260907T1120Z'
OWNER_SHA256='bdb8ce769624677a0e5aacfaad066965d8512e2c232f18caae6ab9f88f9564ca'
REVIEW_STATES={'new_monitor_independent_review':'PENDING','preservation_mapping_independent_review':'PENDING',
               'publication_harness_replacement':'NOT_AUTHORIZED','product_publication':'NOT_AUTHORIZED'}
def put(p,r):coverage.put(p,r)
def load(p):return json.loads(Path(p).read_text())
def runpath(name):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{1,80}',name):raise RuntimeError('INVALID_RUN_ID')
    p=D/'outputs/continuation-runs'/name
    if p.resolve()!=p:raise RuntimeError('RUN_NAMESPACE_SYMLINK')
    return p

def identities(run):
    r={}
    for root in repos(run):
        paths=exact(root)
        r[str(root)]={'tracked':len(paths),'candidate':SHA,'tree':TREE,'index_sha256':coverage.digest(root/'.git/index'),
                      'status':git(root,'status','--porcelain','--untracked-files=no').decode(),
                      'branch':git(root,'symbolic-ref','-q','HEAD').decode().strip() if (root/'.git/HEAD').read_text().startswith('ref:') else 'DETACHED'}
    scope=load(O/'PROTECTION_SCOPE.json');objects={}
    for root in repos(run):
        obj=root/'.git/objects'
        if (obj/'info/alternates').exists():raise RuntimeError('ALTERNATES_PRESENT')
        objects[str(root)]={(p.stat().st_dev,p.stat().st_ino) for p in obj.rglob('*') if p.is_file()}
    for i,a in enumerate(objects):
        for b in list(objects)[i+1:]:
            if objects[a]&objects[b]:raise RuntimeError('SHARED_OBJECT_INODE '+a+' '+b)
    return {'result':'PASS','repositories':r,'shared_object_inode_intersections':0,'alternates':0}

def prepare(run,qualification=None):
    run.mkdir(parents=True,exist_ok=False)
    for rel in ['runtime/gates','runtime/outputs/backend','runtime/outputs/frontend','runtime/outputs/frontend-evidence','runtime/producer-events','runtime/tmp/backend','runtime/tmp/frontend','runtime/cache/backend','runtime/cache/frontend']:(run/rel).mkdir(parents=True,exist_ok=True)
    namespaces.prepare(run)
    m=bindings.build(run);put(run/'bindings.json',m)
    put(run/'source-recovery.json',engineering.source_recovery(run/'sources/backend'))
    for lane in ('backend','frontend','shadow'):
        env=environment(lane,run)
        if lane=='backend':
            target=Path(env['GRADLE_USER_HOME'])/'init.d';target.mkdir()
            shutil.copyfile(H/'packaging.init.gradle',target/'ep19-packaging.gradle')
    put(run/'prepare.json',{'result':'PREPARED_NOT_BASELINED','run_id':run.name,'candidate':SHA,'tree':TREE,'base':BASE,'formal_gate_execution':False,
        'qualification':str(Path(qualification or AUTHORITY/'QUALIFICATION.json').absolute()),
        'dependency_preparation':'Parent may populate only this runtime cache before baseline/seal. No copied FE assets. Fresh per-run independent clones; original checkouts never execute.',
        'commands':{'baseline':f'python3 -B executor/runner.py baseline --run-id {run.name}',
                    'preflight':f'python3 -B executor/runner.py preflight --run-id {run.name}',
                    'run':f'python3 -B executor/runner.py run --run-id {run.name} --review /absolute/parent-review.json'}})

def baseline(run):
    if (run/'baseline.json').exists():raise RuntimeError('BASELINE_ALREADY_EXISTS_NEW_NAMESPACE_REQUIRED')
    ids=identities(run);put(run/'identity.json',ids)
    scope=coverage.derive(run,[run/'bindings.json',run/'prepare.json',run/'identity.json',run/'source-recovery.json',run/'namespaces.json'])
    put(run/'scope.json',scope)
    if scope['instruction_capture']['result']!='COMPLETE':
        put(run/'baseline.json',{'result':'INCOMPLETE','instruction_errors':scope['instruction_capture']['errors']});return 1
    # The observer registers the complete bounded scope; no child/product command.
    w=observe.Watch(**{k:v for k,v in coverage.watch_args(scope).items()})
    try:
        before=observe.snapshot(w.capture_paths,w.expected_missing);w.drain()
        if w.errors or w.rejected():raise RuntimeError('BASELINE_OBSERVATION_REJECT')
        put(run/'baseline.json',{'result':'COMPLETE','entries':before,'watches':len(w.watches),
                               'time':time.time(),'claim':'Current endpoints only; not historical preservation'})
    finally:w.close()
    initdir=run/'runtime/cache/backend/gradle/init.d'
    if {p.name for p in initdir.iterdir()}!={'ep19-packaging.gradle'}:raise RuntimeError('UNDECLARED_GRADLE_INIT_INPUT')
    inputs=[*scope['sealed_inputs'],run/'scope.json',run/'baseline.json',run/'runtime/cache/backend/gradle/init.d/ep19-packaging.gradle']
    # Dependency configuration/binaries are measured without executing tools or gates.
    tools={}
    for n in ('python3','git','java','javac','node','npm','npx','bash','bwrap','podman'):
        p=shutil.which(n)
        tools[n]={'path':p,'realpath':str(Path(p).resolve()) if p else None,'sha256':coverage.digest(Path(p).resolve()) if p else None}
    put(run/'toolchain.json',tools);inputs.append(run/'toolchain.json')
    inputs += [Path(t['realpath']) for t in tools.values() if t['realpath']]
    for p in (run/'runtime/cache/backend/formal-tools').rglob('*'):
        if p.is_file():inputs.append(p)
    put(run/'seal.json',{'files':coverage.seal(inputs),'run_id':run.name,'candidate':SHA,'tree':TREE,'base':BASE,'policy_acceptance':'NOT_SELF_APPROVED'})
    return 0

def preflight(run,output=None,write=True):
    problems=[];checks={}
    for name in ['bindings','baseline','identity','scope','seal','toolchain']:
        p=run/(name+'.json');checks[name]='PRESENT' if p.is_file() else 'NOT_RUN'
        if not p.is_file():problems.append(name.upper()+'_NOT_PREPARED')
    if (run/'seal.json').is_file():
        try:coverage.check_seal(load(run/'seal.json')['files']);checks['helper_seal']='PASS'
        except Exception as e:problems.append(str(e));checks['helper_seal']='FAIL'
    qualification={'result':'NOT_RUN'}
    try:
        q=Path(load(run/'prepare.json')['qualification']);qualification=load(q)
        inputs=coverage.qualification_inputs(q)
        inputs += [AUTHORITY/n for n in ('OWNER_DECISION.txt','OWNER_PROVENANCE.json','ENGINEERING_MAPPING.md')]
        inputs += [O/'GATE_EXECUTION_MATRIX.json',O/'PROTECTION_SCOPE.json',O/'qualification/CONTINUATION_PRESERVATION_CONTRACT.md']
        inputs += [p for p in (O/'inputs').rglob('*') if p.is_file()]
        inputs += [run/'runtime/cache/backend/gradle/init.d/ep19-packaging.gradle']
        sealed=load(run/'seal.json')['files'];scope=load(run/'scope.json')
        run_inputs={str(run/(n+'.json')) for n in ('prepare','bindings','identity','source-recovery','toolchain','scope','baseline','namespaces')}
        if not run_inputs<=set(sealed):problems.append('RUN_CONTROL_INPUT_NOT_SEALED')
        if not set(map(str,inputs))<=set(sealed):problems.append('MANDATORY_EXECUTION_INPUT_NOT_SEALED')
        if not set(map(str,inputs))<=set(scope['protected']):problems.append('MANDATORY_EXECUTION_INPUT_NOT_OBSERVED')
        old=load(O/'PROTECTION_SCOPE.json')
        if not set(old['protected'])<=set(scope['protected']):problems.append('ORIGINAL_PROTECTION_MEMBERS_MISSING')
        for key in ('cross_lane','shared_git','shadow_declared'):
            if scope[key]!=old[key]:problems.append('ORIGINAL_SCOPE_CHANGED '+key)
        expected_roles=namespaces.scope_roles(dict(scope),run)
        for key in ('repositories','metadata_roots','shadow_root','allowed'):
            if scope[key]!=expected_roles[key]:problems.append('RUN_SCOPE_MAPPING_CHANGED '+key)
        if scope['instruction_capture']['result']!='COMPLETE':problems.append('INSTRUCTION_COVERAGE_INCOMPLETE')
        if scope.get('frozen_roots')!=[str(run/'runtime/cache/backend/gradle/init.d'),str(run/'runtime/cache/backend/formal-tools')]:problems.append('RUNTIME_EXECUTABLE_SCOPE_NOT_FROZEN')
        expected=set(scope['protected'])|set(scope['instruction_capture']['entries'])
        if not expected<=set(load(run/'baseline.json')['entries']):problems.append('BASELINE_COVERAGE_INCOMPLETE')
        if qualification.get('real_gradle_instrumentation')!='PASS':problems.append('REAL_GRADLE_INSTRUMENTATION_NOT_QUALIFIED')
        if qualification.get('schema')=='ep19-output-corrections-v2':
            for area in ('run_isolation','artifact_copy','compile_completeness','vite_closure','packaging'):
                if area not in qualification.get('areas',[]):problems.append('CORRECTION_QUALIFICATION_MISSING '+area)
        if qualification.get('frontend_boundary')!='PASS':problems.append('FRONTEND_BOUNDARY_QUALIFICATION_NOT_PASS')
        if not coverage.formal_boundary_qualified(qualification):problems.append('FORMAL_BOUNDARY_QUALIFICATION_NOT_PASS')
        for area in ('collector','coverage','shadow','packaging','freshness','launch'):
            if qualification.get(area)!='PASS':problems.append('QUALIFICATION_AREA_NOT_PASS '+area)
        checks['qualification_closure']='PASS'
    except Exception as e:problems.append('QUALIFICATION_OR_COVERAGE_REJECT '+str(e))
    try:
        owner_authorization();checks['owner_authorization']='OWNER_AUTHORIZED'
        for root in repos(run):exact(root)
        checks['current_exact_sha_tree_base']='PASS'
        check_execution_seal(run,load(run/'seal.json')['files'])
        compare_baseline(run,{})
        checks['current_baseline']='PASS'
    except Exception as e:problems.append(str(e))
    if (run/'baseline.json').is_file() and load(run/'baseline.json').get('result')!='COMPLETE':problems.append('BASELINE_INCOMPLETE')
    if (run/'toolchain.json').is_file():
        for name,tool in load(run/'toolchain.json').items():
            if not tool['path']:problems.append('MISSING_RUNTIME_TOOL '+name)
    if (run/'bindings.json').is_file():
        m=load(run/'bindings.json');checks['matrix_keys']=m['order']
        if m!=bindings.build(run):problems.append('EXECUTION_BINDINGS_CHANGED')
    else:checks['matrix_keys']=load(O/'GATE_EXECUTION_MATRIX.json')['order']
    lean=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean'
    if not lean.is_file():problems.append('LEAN_4_19_0_NOT_PREPARED_IN_RUN_CACHE')
    r={'result':'ENGINEERING_READY' if not problems else 'ENGINEERING_PREFLIGHT_BLOCKED',
       'run_id':run.name,'candidate':SHA,'tree':TREE,'base':BASE,'checks':checks,'engineering_blockers':problems,
       'independent_review':'PENDING',**REVIEW_STATES,
       'collector_baseline':checks['baseline'],'qualification':qualification,
       'packaging':{'synthetic':qualification.get('packaging','NOT_RUN'),'actual':'NOT_RUN_NOT_BUILT',
                    'scheduled':'processResources and bootJar doLast; producer receipts checked before gate acceptance'},
       'review_required':{'monitor':'inputs/MONITOR_CONTRACT.txt NEW_MONITOR_REVIEW=REQUIRED; parent decides applicability with source-backed disposition',
                          'independent_review':'CONTINUATION_IMPLEMENTATION_BRIEF.md requires independent review',
                          'external_runtime':'Backend container socket/storage/network/kernel external scope; environment paths alone are not isolation'},
       'product_gates':'NOT_RUN','publication':'NOT_PERFORMED','sanity':'NOT_RUN','EP19_CLOSED':'NO','ROADMAP_23_SECOND_WAVE':'NO_GO'}
    if write:put(output or run/'preflight.json',r)
    return r

def owner_authorization():
    if coverage.digest(AUTHORITY/'OWNER_DECISION.txt')!=OWNER_SHA256:
        raise RuntimeError('OWNER_EXECUTION_AUTHORIZATION_MISSING_OR_CHANGED')
    if load(AUTHORITY/'OWNER_PROVENANCE.json')['instruction_sha256']!=OWNER_SHA256:
        raise RuntimeError('OWNER_PROVENANCE_MISMATCH')

def check_execution_seal(run,files):
    coverage.check_seal(files)
    init=run/'runtime/cache/backend/gradle/init.d'
    if {p.name for p in init.iterdir()}!={'ep19-packaging.gradle'}:
        raise RuntimeError('UNDECLARED_GRADLE_INIT_INPUT')
    if coverage.digest(init/'ep19-packaging.gradle')!=coverage.digest(H/'packaging.init.gradle'):
        raise RuntimeError('RUNTIME_GRADLE_INIT_CHANGED')

def archive_xml(repo,gate):
    paths=sorted(repo.glob('**/build/test-results/test/TEST-*.xml'))
    for p in paths:
        if p.resolve()!=p or p.is_symlink():raise RuntimeError('XML_SYMLINK')
        t=gate/'xml'/p.relative_to(repo);t.parent.mkdir(parents=True,exist_ok=True)
        with t.open('xb') as f:f.write(p.read_bytes())
    return paths

def packaging_receipts(run,name,required=False,jar_required=False):
    events=sorted((run/'runtime/producer-events').glob(name+'-*'))
    if required and not events:raise RuntimeError('MISSING_RESOURCE_PRODUCER_RECEIPT')
    sawjar=False;result=[]
    for event in events:
        process=load(event/'process.json');rule=load(event/'rule.json');check=load(event/'check.json')
        if process['exit']!=0 or process['run']!=str(run) or process['gate']!=name or rule['run_root']!=str(run) or rule['producer_gate']!=name:raise RuntimeError('PACKAGING_PRODUCER_BINDING')
        if check['resources']['result']!='PASS':raise RuntimeError('PACKAGING_RESOURCES_REJECT')
        if rule['actual_task']==':platform-app:bootJar':
            sawjar=True
            if check['jar']['result']!='PASS' or check['jar']['jar']!=rule['archive_file'] or coverage.digest(rule['archive_file'])!=check['jar']['jar_sha256']:raise RuntimeError('PACKAGING_JAR_REJECT')
        result.append({'event':str(event),'files':coverage.seal([event/x for x in ['process.json','rule.json','check.json','native.log']])})
    if jar_required and not sawjar:raise RuntimeError('MISSING_BOOTJAR_PRODUCER_RECEIPT')
    return result

def aux(argv,cwd,log,env,scope,timeout=120):
    r=observe.run(argv,cwd,log,env=env,timeout=timeout,**coverage.watch_args(scope))
    put(log.with_suffix('.receipt.json'),r)
    if r['native_exit']!=0 or r['wrapper_exit']!=0:raise RuntimeError('AUXILIARY_PROCESS_REJECT')
    return r

def run_gate(name,m,run,scope,sealed,results):
    spec=m['gates'][name];repo=Path(spec['repository']);gate=run/'runtime/gates'/name;gate.mkdir()
    r={'result':'FAIL','repository':str(repo),'gate':name,'run_id':run.name,'candidate':SHA,'tree':TREE,'native_exit':None,'wrapper_exit':1}
    try:
        check_execution_seal(run,sealed)
        if any((run/'runtime/producer-events').glob(name+'-*')):raise RuntimeError('STALE_PRODUCER_EVENT_NAMESPACE')
        for n in spec['dependencies']:freshness.dependency(results[n],run.name)
        for root in repos(run):exact(root)
        compare_baseline(run,results)
        env=environment('frontend' if name.startswith('FRONTEND_') else 'shadow' if name=='SHADOW' else 'backend',run)
        env.update(EP19_RUN_ROOT=str(run),EP19_HELPER_ROOT=str(H),EP19_GATE_ID=name,EP19_CANDIDATE=SHA)
        if name=='COMPILE':
            stale=[str(p) for p in repo.rglob('*.class') if 'build' in p.relative_to(repo).parts]
            put(gate/'compile-scope-before.json',{'preexisting_classes':stale,'run_id':run.name,'repository':str(repo)})
            if stale:raise RuntimeError('PREEXISTING_COMPILE_CLASSES')
        r['live_producer_inputs']=artifacts.producer_inputs(list(results.values()),run,repo)
        command=list(spec['command']);required=list(map(Path,spec['output_bindings']['required_files']))
        cleanup=[p for p in required if p.exists()]
        if name in bindings.XML:cleanup+=sorted(repo.glob('**/build/test-results/test/TEST-*.xml'))
        if name=='BOOTJAR':cleanup+=sorted((repo/'platform-app/build/libs').glob('*.jar'))
        if name=='FRONTEND_BUILD':cleanup+=sorted(p for p in (run/'runtime/outputs/frontend').rglob('*') if p.is_file())
        freshness.preserve_cleanup(cleanup,gate/'cleanup-preimages',[run/'runtime',*[Path(x) for x in scope['allowed']]],repo)
        before={str(p):'ABSENT' if not p.exists() else 'PRESENT' for p in required}
        if name=='APPLICATION_PROBE':
            artifacts.live_equal([run/'runtime/outputs/backend/classpath.txt'],results.values(),run)
            cp=(run/'runtime/outputs/backend/classpath.txt').read_text().strip();classes=run/'runtime/outputs/backend/probe-classes';classes.mkdir(exist_ok=True)
            paths=[Path(p) for p in cp.split(os.pathsep)];depfiles=[]
            for p in paths:
                if p.is_file():depfiles.append(p)
                elif p.is_dir():depfiles+=sorted(x for x in p.rglob('*') if x.is_file())
                else:raise RuntimeError('CLASSPATH_DEPENDENCY_MISSING')
            artifacts.live_equal(depfiles,results.values(),run,[p for p in paths if p.is_dir()])
            dependency_files=coverage.seal(depfiles);put(gate/'classpath-dependencies.json',dependency_files)
            compile_cmd=['javac','-cp',cp,'-d',str(classes),str(H/'ExposureProbe.java')]
            aux(compile_cmd,repo,gate/'javac.log',env,scope)
            coverage.check_seal(dependency_files)
            args=run/'runtime/outputs/backend/probe.args'
            with args.open('x') as f:f.write('\n'.join(json.dumps(a) for a in ['-cp',str(classes)+os.pathsep+cp,'ExposureProbe'])+'\n')
        if name=='FORMAL':
            env.update(load(O/'inputs/PROOF_GATE_INVENTORY.json')['environment']);env['LEAN']=str(run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean')
            # Hard-coded /tmp is confined with a mount; original product script unchanged.
            command=formal_sandbox(command,repo,run,env)
        if name.startswith('FRONTEND_'):
            mods=repo/'frontend/node_modules';mods.mkdir(exist_ok=True)
            for n in ('.vite','.vite-temp'):(mods/n).mkdir(exist_ok=True)
            writes=[run/'runtime/cache/frontend',run/'runtime/tmp/frontend',run/'runtime/outputs/frontend',run/'runtime/outputs/frontend-evidence',gate]+([mods] if name=='FRONTEND_INSTALL' else [mods/'.vite',mods/'.vite-temp'])
            if name=='FRONTEND_BUILD':
                cmd=['node',str(H/'vite_resolution.mjs'),str(repo/'frontend'),str(run/'runtime/outputs/frontend'),str(gate/'resolution.json')]
                aux(frontend_sandbox(cmd,repo/'frontend',writes,run),repo/'frontend',gate/'resolution.log',env,scope)
            command=frontend_sandbox(command,Path(spec['cwd']),writes,run)
        dependencies_before=freshness.dependency_inputs(run,repo) if name!='FRONTEND_INSTALL' else {}
        put(gate/'dependencies-before.json',dependencies_before)
        put(gate/'invocation.json',{'argv':command,'authoritative_argv':spec['authoritative_command'],'cwd':spec['cwd'],'run_id':run.name,'candidate':SHA,'tree':TREE,'sealed_inputs':sealed,'environment':{k:env.get(k) for k in ['PATH','JAVA_HOME','GRADLE_USER_HOME','HOME','TMPDIR','JAVA_TOOL_OPTIONS','DOCKER_HOST','EP19_RUN_ROOT','EP19_GATE_ID']},'before_outputs':before,'native_handling':'main child and auxiliaries have separate process receipts','output_producer':{str(p):'bound javac/argfile preparation plus main probe' if name=='APPLICATION_PROBE' else name for p in required}})
        kwargs=coverage.watch_args(scope,shadow=name=='SHADOW')
        if name=='SHADOW':kwargs['shadow_reconciler']=shadow_binding.bind(repo,env,scope['shadow_declared'],gate)
        observed=observe.run(command,Path(spec['cwd']),gate/'native.log',env=env,timeout=spec['timeout_seconds'],**kwargs)
        r.update(observed);r.update(gate=name,run_id=run.name,candidate=SHA,tree=TREE)
        put(gate/'observation.json',observed)
        # Preserve XML even for a failed native gate, before any later task can rewrite it.
        if name in bindings.XML:
            xml=archive_xml(repo,gate);required+=xml
            before.update({str(p):'ABSENT' for p in xml}) # Cleanup above covered every matching report.
        for root in repos(run):exact(root)
        check_execution_seal(run,sealed)
        accepted=freshness.require_fresh_outputs(required,before,r,run.name,name,lambda:parsers.parse(name,run,gate,repo))
        dependencies_after=freshness.dependency_inputs(run,repo)
        r['dependency_resolution']=freshness.compare_dependencies(dependencies_before,dependencies_after)
        put(gate/'dependencies-after.json',dependencies_after)
        r['acceptance']=accepted
        generated=[]
        for out in [Path(x) for x in scope['allowed'] if Path(x).is_relative_to(repo)]+([run/'runtime/outputs/frontend'] if name=='FRONTEND_BUILD' else []):
            if out.name in ['node_modules','.gradle']:continue
            generated += [p for p in out.rglob('*') if p.is_file()]
        put(gate/'generated-output-digests.json',coverage.seal(generated))
        if name=='COMPILE':
            r['compile']=compile_inventory.validate(run,gate,repo)
            put(gate/'compile-manifest.json',r['compile'])
        r['packaging']=packaging_receipts(run,name,required=name in ['COMPILE','AFFECTED_INTEGRATION','FULL_BACKEND','BOOTJAR'],jar_required=name=='BOOTJAR')
        r['result']='VALIDATED_AWAITING_INDEPENDENT_COPY'
    except Exception as error:
        r.update(result='FAIL',wrapper_exit=1,error_type=type(error).__name__,reason=str(error),traceback=traceback.format_exc())
    # Every accepted path (including mutable builds, JARs and producer events)
    # is independently copied before PASS. Failed evidence remains in-place.
    try:
        if r['result']=='VALIDATED_AWAITING_INDEPENDENT_COPY':
            evidence=artifacts.files(gate)
            evidence+=list(map(Path,r.get('acceptance',{}).get('outputs',{})))
            evidence+=generated
            for row in r.get('packaging',[]):
                evidence+=list(map(Path,row['files']))
                rule=load(Path(row['event'])/'rule.json')
                if rule['actual_task']==':platform-app:bootJar':evidence.append(Path(rule['archive_file']))
            if name=='APPLICATION_CLASSPATH':
                for p in map(Path,(run/'runtime/outputs/backend/classpath.txt').read_text().strip().split(os.pathsep)):
                    evidence+=artifacts.files(p) if p.is_dir() else [p]
            def recheck(saved):
                expected=dict(r['acceptance']['outputs'])
                expected.update(load(gate/'generated-output-digests.json'))
                for row in r.get('compile',{}).get('manifest',[]):expected[row['path']]=row['sha256']
                closure=r.get('acceptance',{}).get('parser',{}).get('closure',{})
                for path,row in closure.get('inventory',{}).items():expected[str(run/'runtime/outputs/frontend'/path)]=row['sha256']
                for path,digest in expected.items():
                    if path not in saved or coverage.digest(saved[path])!=digest:raise RuntimeError('SEALED_ACCEPTANCE_MANIFEST_MISMATCH '+path)
                for row in r.get('packaging',[]):
                    event=Path(row['event']);rule=load(saved[str(event/'rule.json')]);check=load(saved[str(event/'check.json')])
                    # Producer's Git -> checkout -> processResources mapping was
                    # checked in doLast; rebind it to the independently copied ZIP.
                    if rule['actual_task']==':platform-app:bootJar':
                        r.setdefault('preserved_packaging',[]).append(packaging.jar(check['source_manifest'],saved[rule['archive_file']],rule))
            artifacts.finalize(r,gate,evidence,recheck)
    except Exception as error:
        r.update(result='FAIL',wrapper_exit=1,error_type=type(error).__name__,reason=str(error),traceback=traceback.format_exc())
    put(gate/'receipt.json',r);return r

def compare_baseline(run,results):
    baseline=load(run/'baseline.json')['entries'];wanted=dict(baseline)
    # Only the successfully reconciled original disposable Shadow behavior can
    # leave refreshed metadata. Exact tracked content/index semantics stay checked.
    if results.get('SHADOW',{}).get('result')=='PASS':
        scope=load(run/'scope.json');root=Path(scope['shadow_root'])
        for name in [*scope['shadow_declared'],'.git/index']:
            wanted.pop(str(root/name),None)
        exact(root)
    current=observe.snapshot(wanted,[p for p,r in wanted.items() if r.get('kind')=='missing'])
    if current!=wanted:raise RuntimeError('FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP')


def run_all(run,review):
    if (run/'runtime/START.json').exists():raise RuntimeError('NO_RETRY_AFTER_FORMAL_START')
    owner_authorization()
    decision=load(review)
    if decision.get('engineering_execution_authorization')!='OWNER_AUTHORIZED':
        raise RuntimeError('OWNER_EXECUTION_AUTHORIZATION_REQUIRED')
    if decision.get('owner_decision_sha256')!=OWNER_SHA256:
        raise RuntimeError('OWNER_EXECUTION_AUTHORIZATION_UNBOUND')
    if decision.get('independent_review')!='PENDING' or any(decision.get(k)!=v for k,v in REVIEW_STATES.items()):
        raise RuntimeError('ENGINEERING_REVIEW_PUBLICATION_STATES_MUST_STAY_SEPARATE')
    seal=load(run/'seal.json');check_execution_seal(run,seal['files'])
    if any(seal.get(k)!=v or decision.get(k)!=v for k,v in {'candidate':SHA,'tree':TREE,'base':BASE,'run_id':run.name}.items()):
        raise RuntimeError('LAUNCH_CANDIDATE_IDENTITY_MISMATCH')
    p=load(run/'preflight.json')
    if p.get('result')!='ENGINEERING_READY' or p.get('engineering_blockers')!=[]:
        raise RuntimeError('ENGINEERING_PREFLIGHT_NOT_READY')
    if any(p.get(k)!=v for k,v in {'candidate':SHA,'tree':TREE,'base':BASE,'run_id':run.name}.items()):
        raise RuntimeError('PREFLIGHT_CANDIDATE_IDENTITY_MISMATCH')
    if decision.get('seal_sha256')!=coverage.digest(run/'seal.json') or decision.get('preflight_sha256')!=coverage.digest(run/'preflight.json'):
        raise RuntimeError('UNBOUND_ENGINEERING_LAUNCH_RECEIPT')
    # Recompute the actual checks now; an old successful JSON cannot authorize a run.
    current=preflight(run,write=False)
    put(run/'runtime/launch-preflight.json',current)
    if current['result']!='ENGINEERING_READY':raise RuntimeError('CURRENT_TECHNICAL_PREFLIGHT_REJECT')
    scope=load(run/'scope.json');sealed={**seal['files'],str(review):coverage.digest(review),str(run/'seal.json'):coverage.digest(run/'seal.json'),str(run/'preflight.json'):coverage.digest(run/'preflight.json')}
    scope['protected']=sorted(set(scope['protected'])|set(sealed));m=load(run/'bindings.json');results={};stopped=False
    # No expected hash moves: compare the original baseline to fresh endpoints.
    compare_baseline(run,{})
    put(run/'runtime/START.json',{'time':time.time(),'run_id':run.name,'review':str(review),'review_sha256':coverage.digest(review),'sealed_inputs':sealed})
    def failure(name,r):
        put(run/'runtime/STOP.json',{'gate':name,'reason':r.get('reason'),'native_exit':r['native_exit'],'wrapper_exit':r['wrapper_exit'],'retry_authorized':False})
    results,stopped=execute_graph(m['order'],lambda name,results:run_gate(name,m,run,scope,sealed,results),failure,run.name)
    if not stopped:
        try:
            compare_baseline(run,results)
            check_execution_seal(run,sealed)
            for receipt in results.values():freshness.dependency(receipt,run.name)
        except Exception as error:
            stopped=True;put(run/'runtime/STOP.json',{'reason':str(error),'phase':'FINAL_ACCEPTANCE','retry_authorized':False})
    put(run/'runtime/RESULTS.json',{'result':'FAIL' if stopped else 'PASS','results':results,'candidate_acceptance':'PENDING_PARENT','publication':'NOT_PERFORMED','independent_review':'PENDING',**REVIEW_STATES})
    return int(stopped)

def execute_graph(order,executor,on_failure,run_id):
    results={};stopped=False
    for name in order:
        if stopped:r={'gate':name,'result':'NOT_RUN','reason':'PRIOR_REQUIRED_FAILURE','run_id':run_id,'candidate':SHA,'tree':TREE}
        else:r=executor(name,results)
        results[name]=r
        if r['result'] not in ['PASS','NOT_RUN']:
            stopped=True;on_failure(name,r)
    return results,stopped


def main():
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','baseline','preflight','run']);a.add_argument('--run-id',required=True);a.add_argument('--review',type=Path);a.add_argument('--output',type=Path);a.add_argument('--qualification',type=Path);x=a.parse_args();run=runpath(x.run_id)
    if x.phase=='prepare':prepare(run,x.qualification)
    elif x.phase=='baseline':return baseline(run)
    elif x.phase=='preflight':
        result=preflight(run,x.output);print(json.dumps(result));return int(result['result']!='ENGINEERING_READY')
    else:
        if x.review is None:a.error('--review required for parent run')
        return run_all(run,x.review.absolute())
    return 0
if __name__=='__main__':raise SystemExit(main())
