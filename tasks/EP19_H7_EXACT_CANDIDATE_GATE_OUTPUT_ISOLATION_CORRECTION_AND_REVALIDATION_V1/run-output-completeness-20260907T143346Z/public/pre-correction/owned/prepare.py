from pathlib import Path
import ast,collections,csv,hashlib,json,os,shutil,subprocess
from execution import D,SHA,TREE,exact,git,environment
from account import canonical,fe_identity
P=D.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1';OLD=D.parent/'EP19_EXACT_CANDIDATE_CANONICAL_PUBLICATION_AND_POST_PUBLICATION_VERIFICATION_V1';B=D/'sources/backend';F=D/'sources/frontend';R=Path('/home/user/Documents/workspace/projects/media-platform')
def put(n,o):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(o,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['FULL_TEST_EXPECTED_FROZEN.tsv','FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv','runtime_summary.py','PROOF_GATE_INVENTORY.json','FRONTEND_IDENTITIES.native.log','FRONTEND_TEST_RESULTS.json']:
 p=D/'inputs'/n
 if not p.exists():shutil.copyfile(P/n,p)
for n in ['native_runner.py','shadow_monitor.py','control.py','FCV_COMMAND_INVENTORY.tsv','classpath.init.gradle','ExposureProbe.java']:shutil.copyfile(OLD/n,D/'inputs'/('original-'+n))
shutil.copyfile(OLD/'ExposureProbe.java',D/'owned/ExposureProbe.java');shutil.copyfile(OLD/'shadow_monitor.py',D/'owned/frozen_shadow_monitor.py')
init=(OLD/'classpath.init.gradle').read_text().replace(str(OLD/'classpath.txt'),str(D/'outputs/backend/classpath.txt')).replace(str(OLD/'engine-classpath.txt'),str(D/'outputs/backend/engine-classpath.txt'));(D/'owned/classpath.init.gradle').write_text(init)
full=list(csv.DictReader((D/'inputs/FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv').open(),delimiter='\t'));frozen=list(csv.DictReader((D/'inputs/FULL_TEST_EXPECTED_FROZEN.tsv').open(),delimiter='\t'))
expected=[canonical([r['TASK'],r['CLASSNAME'],r['TESTNAME']]) for r in full]
status={canonical([':'+r['module'].replace('/',':')+':test',r['test_class'],r['test_identity']]):r['expected_status'] for r in frozen}
assert len(expected)==len(set(expected))==7973 and set(status)==set(expected)
skips=[i for i in expected if status[i]=='SKIPPED'];assert len(skips)==29
sets={'FULL_BACKEND':{'identities':expected,'skips':skips}}
for gate,classes in {'AFFECTED_INTEGRATION':['com.example.platform.ModularityTest','com.example.platform.entitlement.api.EntitlementDecisionQueryPublicationTest','com.example.platform.identity.architecture.AuthorizationArchitectureGuardTest'],'RUNTIME_PREFLIGHT':['com.example.platform.sandbox.BubblewrapSandboxProcessLauncherIntegrationTest','com.example.platform.sandbox.ContainerSandboxProcessLauncherIntegrationTest']}.items():
 ids=[canonical([r['TASK'],r['CLASSNAME'],r['TESTNAME']]) for r in full if r['CLASSNAME'] in classes];sets[gate]={'identities':ids,'skips':[i for i in ids if i in skips]}
old_fe=json.loads((P/'FRONTEND_TEST_RESULTS.json').read_text());flat=json.loads((P/'FRONTEND_IDENTITIES.native.log').read_text());bridge=[];structured=[]
for suite in old_fe['testResults']:
 for case in suite['assertionResults']:
  bridge.append((suite['name'],' > '.join([*case['ancestorTitles'],case['title']])));structured.append(fe_identity(suite['name'],case['ancestorTitles'],case['title'],P/'candidate'))
assert collections.Counter(bridge)==collections.Counter((r['file'],r['name']) for r in flat)
assert len(bridge)==len(set(bridge))==len(structured)==len(set(structured))==149
sets['FRONTEND_TEST']={'identities':structured,'skips':[]}
for gate,file in [('H7_FOCUSED',B/'scripts/guards/test_h7_input_boundary.py'),('CLASSIFIER_TEST',B/'scripts/ci/test_change_impact_classifier.py')]:
 sets[gate]={'identities':[n.name for n in ast.walk(ast.parse(file.read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')],'skips':[]}
func=next(n for n in ast.parse((B/'scripts/guards/h7-architecture-guard.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='run_self_test')
sets['H7_MUTATIONS']={'identities':[n.args[0].elts[0].value for n in ast.walk(func) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='cases' and n.func.attr=='append'],'skips':[]}
put('inputs/EXPECTED_IDENTITIES.json',sets)
put('inputs/FRONTEND_INVENTORY_DERIVATION.json',{'expected_count':149,'source_commit':SHA,'source_tree':TREE,'original_flat_inventory_sha256':h(P/'FRONTEND_IDENTITIES.native.log'),'historical_structured_report_sha256':h(P/'FRONTEND_TEST_RESULTS.json'),'bridge_bijective':True,'flat_collision_count':0,'structured_collision_count':0,'relocation':{'from':str(P/'candidate'),'to':str(F),'operation':'Exact root-relative conversion; no whitespace or hierarchy normalization'},'use':'Expected identities only; no historical PASS reused'})
for root in [B,F]:
 (root/'remote-render-worker').mkdir(exist_ok=True)
 exact(root)
shadow=D/'sources/shadow-fixture';assert not shadow.exists();subprocess.run(['git','clone','--no-local','--no-checkout',str(B/'.git'),str(shadow)],check=True);subprocess.run(['git','--no-optional-locks','-C',str(shadow),'checkout','--detach',SHA],check=True);exact(shadow);(shadow/'remote-render-worker').mkdir(exist_ok=True)
for root in [B,shadow]:
 (root/'.gradle').mkdir(exist_ok=True)
 for p in [root/'build',*((p.parent/'build') for p in root.rglob('build.gradle.kts'))]:p.mkdir(parents=True,exist_ok=True)
for n in ['outputs/backend','outputs/frontend-evidence','outputs/frontend','outputs/shadow','outputs/qualification/frontend','outputs/qualification/evidence','observations','xml','cache/frontend']:(D/n).mkdir(parents=True,exist_ok=True)
for name in ['.vite','.vite-temp']:(F/'frontend/node_modules'/name).mkdir(exist_ok=True)
for lane in ['backend','frontend']:environment(lane)
# Data inputs and prior failed scenes are separate from mutable build namespaces.
failed=P/'candidate';protected=exact(B)+exact(F)+exact(shadow)
protected.extend(R/os.fsdecode(n) for n in git(R,'ls-files','-z').split(b'\0') if n)
protected.extend(failed/os.fsdecode(n) for n in git(failed,'ls-files','-z').split(b'\0') if n)
protected.extend(failed/os.fsdecode(n) for n in git(failed,'ls-files','--others','--exclude-standard','-z').split(b'\0') if n)
protected.extend(p for p in P.iterdir() if p.is_file());protected.extend(p for p in (P/'owned').rglob('*') if p.is_file())
protected.extend(p for p in (D/'inputs').rglob('*') if p.is_file())
front_meta=Path('/home/user/Documents/workspace/worktrees/frontend-wave2-product-ux-v1/.git').read_text().strip();assert front_meta.startswith('gitdir: ');front_meta=Path(front_meta[len('gitdir: '):]);assert front_meta.is_relative_to(R/'.git/worktrees')
ref='refs/heads/agent/frontend-wave2-product-ux-v1';tracking='refs/remotes/origin/agent/frontend-wave2-product-ux-v1'
allowed=[B/'.gradle',F/'frontend/node_modules',shadow/'.gradle',*[p for root in [B,shadow] for p in [root/'build',*((x.parent/'build') for x in root.rglob('build.gradle.kts'))]]]
put('PROTECTION_SCOPE.json',{'protected':sorted(set(map(str,protected))),'repositories':list(map(str,[R,failed,B,F,shadow])),'metadata_roots':list(map(str,[R/'.git',failed/'.git',B/'.git',F/'.git',shadow/'.git'])),'allowed':list(map(str,allowed)),'cross_lane':list(map(str,[R/'.git'/ref,R/'.git/logs'/ref,R/'.git'/tracking,R/'.git/logs'/tracking,front_meta])),'shared_git':str(R/'.git'),'shadow_root':str(shadow),'shadow_declared':['typed-schema-module/jooq-baseline.properties','typed-schema-module/jooq-plain-sql-allowlist.txt','typed-schema-module/jooq-dynamic-identifier-allowlist.txt']})
print(json.dumps({'baseline_counts':{k:len(v['identities']) for k,v in sets.items()},'protected_file_count':len(set(protected)),'source_roots':[str(B),str(F)],'shadow_fixture':str(shadow)}))
