"""Focused synthetic A/B/C qualification. Every fixture remains under this cwd."""
from pathlib import Path
import copy,hashlib,json,os,shutil,subprocess,sys,unittest,uuid,zipfile
from unittest.mock import patch
D=Path(__file__).resolve().parents[1];sys.path.insert(0,str(D/'executor'))
import artifacts,bindings,compile_inventory,coverage,execution,freshness,namespaces,packaging,parsers,runner,vite_closure
Q=Path(os.environ['EP19_QUALIFICATION_ROOT']);Q.mkdir(parents=True,exist_ok=True)

def put(p,r):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2)+'\n')
def native(argv,cwd,log,env=None):
 with log.open('xb') as f:r=subprocess.run(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 put(Path(str(log)+'.process.json'),{'argv':list(map(str,argv)),'cwd':str(cwd),'native_exit':r.returncode,'raw_log':str(log),'log_sha256':coverage.digest(log),'synthetic_only':True})
 return r.returncode

class Cases(unittest.TestCase):
 def setUp(self):
  self.root=Q/(self._testMethodName+'-'+uuid.uuid4().hex[:8]);self.root.mkdir()
 def gate(self,name='A',gate='COMPILE'):
  run=runner.runpath('qualification-'+Q.name+'-'+name+'-'+uuid.uuid4().hex[:8]);p=run/'runtime/gates'/gate;p.mkdir(parents=True);return run,p
 def receipt(self,run,gate='COMPILE'):
  return {'run_id':run.name,'gate':gate,'candidate':execution.SHA,'tree':execution.TREE,'native_exit':0,'wrapper_exit':0}
 def test_A_two_real_candidate_runs(self):
  """PASS: all six exact clones and Git directories independent; B writes cannot alter A."""
  runs=[]
  for n in ['A','B']:
   run=runner.runpath('qualification-'+Q.name+'-'+n);runner.prepare(run,Q/'QUALIFICATION.json');runs.append(run)
  a,b=runs
  oldscope=json.loads((execution.O/'PROTECTION_SCOPE.json').read_text());mapped=namespaces.scope_roles(copy.deepcopy(oldscope),a)
  self.assertTrue(set(oldscope['protected'])<=set(mapped['protected']));self.assertEqual(mapped['cross_lane'],oldscope['cross_lane']);self.assertEqual(mapped['shared_git'],oldscope['shared_git']);self.assertEqual(mapped['shadow_root'],str(a/'sources/shadow-fixture'));self.assertTrue(all(Path(p).is_relative_to(a) for p in mapped['allowed']))
  put(self.root/'scope-mapping.json',{'protected_original_retained':True,'original_count':len(oldscope['protected']),'mapped_count':len(mapped['protected']),'roles':mapped['preservation_mapping'],'allowed':mapped['allowed']})
  paths=[p for run in runs for repo in namespaces.repos(run) for p in (repo/'.git/objects').rglob('*') if p.is_file()]
  inodes=[(p.stat().st_dev,p.stat().st_ino) for p in paths];self.assertEqual(len(inodes),len(set(inodes)))
  for run in runs:
   for repo in namespaces.repos(run):execution.exact(repo)
  ga=a/'runtime/gates/COMPILE';ga.mkdir();p=a/'sources/backend/build/proof.class';p.parent.mkdir();p.write_bytes(b'run A class')
  receipt=artifacts.finalize(self.receipt(a),ga,[p]);put(ga/'receipt.json',receipt)
  pb=b/'sources/backend/build/proof.class';pb.parent.mkdir();pb.write_bytes(b'run B different class')
  freshness.dependency(receipt,a.name);self.assertEqual(p.read_bytes(),b'run A class')
  p.unlink();freshness.dependency(receipt,a.name)
  put(self.root/'runs.json',{'A':str(a),'B':str(b),'identities':[runner.identities(r) for r in runs],'artifacts':receipt})
 def test_A_sealed_changed_removed_symlink_hardlink(self):
  """REJECT: mutation, loss, symlink and hardlink of sealed artifact."""
  for variant in ['changed','removed','symlink','hardlink']:
   with self.subTest(variant=variant):
    run,gate=self.gate(variant);p=run/'mutable';p.write_bytes(b'original');r=artifacts.finalize(self.receipt(run),gate,[p]);put(gate/'receipt.json',r);saved=gate/r['artifacts'][0]['path']
    if variant=='changed':saved.write_bytes(b'changed')
    elif variant=='removed':saved.unlink()
    elif variant=='symlink':saved.unlink();saved.symlink_to(p)
    else:os.link(saved,run/'hardlink')
    with self.assertRaises((RuntimeError,OSError)):freshness.dependency(r,run.name)
 def test_A_copy_link_inputs_and_consumer_equality(self):
  """REJECT: linked producer bytes and mutable consumer divergence."""
  run,gate=self.gate();p=run/'mutable';p.write_bytes(b'original');r=artifacts.finalize(self.receipt(run),gate,[p]);artifacts.live_equal([p],[r],run)
  p.write_bytes(b'diverged')
  with self.assertRaisesRegex(RuntimeError,'LIVE_PRODUCER_COPY_MISMATCH'):artifacts.live_equal([p],[r],run)
  link=run/'symlink';link.symlink_to(p)
  with self.assertRaises(RuntimeError):artifacts.read(link)
  os.link(p,run/'hardlink')
  with self.assertRaises(RuntimeError):artifacts.read(p)
 def test_A_matrix_preservation_mapping(self):
  """PASS: all 29 authoritative argv/dependencies retained, execution roots rebound."""
  run=runner.runpath('qualification-mapping');m=bindings.build(run);old=json.loads((execution.O/'GATE_EXECUTION_MATRIX.json').read_text())
  self.assertEqual(m['order'],old['order'])
  for n,s in m['gates'].items():
   self.assertEqual(s['authoritative_command'],old['gates'][n]['command']);self.assertEqual(s['dependencies'],old['gates'][n]['dependencies'])
   for field in ['repository','cwd','cache','tmp']:self.assertTrue(Path(s[field]).is_relative_to(run))
   for arg in s['command']:
    for part in ['sources','outputs','cache','tmp','owned']:self.assertNotIn(str(execution.O/part)+'/',arg)
  self.assertIn('--rerun-tasks',m['gates']['COMPILE']['command']);self.assertIn('--no-build-cache',m['gates']['COMPILE']['command']);self.assertIn('--manifest',m['gates']['FRONTEND_BUILD']['command'])
  expected=json.loads((execution.O/'inputs/EXPECTED_IDENTITIES.json').read_text());self.assertEqual(len(expected['FULL_BACKEND']['identities']),7973);self.assertEqual(len(expected['FULL_BACKEND']['skips']),29)
  put(self.root/'bindings.json',m)
 def compile_fixture(self):
  run=self.root/'run';repo=run/'sources/backend';gate=run/'runtime/gates/COMPILE';repo.mkdir(parents=True);gate.mkdir(parents=True)
  (repo/'settings.gradle').write_text("rootProject.name='tiny'\ninclude 'empty'\n")
  (repo/'empty').mkdir();(repo/'empty/build.gradle').write_text("plugins { id 'java' }\n")
  (repo/'build.gradle').write_text("""plugins { id 'java' }
def generated = layout.buildDirectory.dir('generated/sources/demo')
tasks.register('generateDemo') {
 outputs.dir(generated)
 doLast { def f=new File(generated.get().asFile,'Generated.java');f.parentFile.mkdirs();f.text='class Generated {}' }
}
sourceSets.main.java.srcDir(tasks.named('generateDemo'))
""")
  src=repo/'src/main/java/Main.java';src.parent.mkdir(parents=True);src.write_text('class Main { static class Inner {} }\n')
  gradles=list(Path('/home/user/.gradle/wrapper/dists').glob('**/bin/gradle'));self.assertTrue(gradles,'Cached real Gradle required by this qualification')
  env=execution.environment('backend',run);env.update(EP19_RUN_ROOT=str(run),EP19_GATE_ID='COMPILE',EP19_CANDIDATE=execution.SHA,H7_SOURCE_TREE=execution.TREE)
  cmd=[str(gradles[0]),'-I',str(execution.H/'compile.init.gradle'),'compileJava','compileTestJava','--offline','--no-daemon','--rerun-tasks','--no-build-cache','--console=plain','--max-workers=2']
  rc=native(cmd,repo,gate/'native.log',env)
  if rc:
   log=(gate/'native.log').read_text()
   if 'Could not determine a usable wildcard IP' not in log: self.fail(log[-4000:])
   put(gate/'REAL_GRADLE_BLOCKED.json',{'result':'BLOCKED','native_exit':rc,'reason':'Restricted runtime denies socket creation before Gradle init execution','real_instrumentation_executed':False})
   if os.environ.get('EP19_REQUIRE_REAL_GRADLE')=='1':self.fail('REAL_GRADLE_RUNTIME_BLOCKED; native failure retained')
   self.synthetic_compile(run,gate,repo,env)
  return run,gate,repo
 def synthetic_compile(self,run,gate,repo,env):
  # Explicit synthetic event model, not a claimed Gradle task observation.
  generated=repo/'build/generated/sources/demo/Generated.java';generated.parent.mkdir(parents=True);generated.write_text('class Generated {}')
  dest=repo/'build/classes/java/main';dest.mkdir(parents=True)
  sources=compile_inventory.inventory([repo/'src/main/java/Main.java',generated])
  self.assertEqual(native(['javac','-d',str(dest),*[r['path'] for r in sources]],repo,gate/'javac.native.log',env),0)
  required=[]
  for task in [':compileJava',':compileTestJava',':empty:compileJava',':empty:compileTestJava']:
   output=dest if task==':compileJava' else repo/('empty/' if task.startswith(':empty') else '')/'build/classes/java'/('test' if task.endswith('TestJava') else 'main')
   ss=[{'name':'main' if task.endswith(':compileJava') else 'test','compileTask':task.split(':')[-1],'javaDirs':[str(repo/'src/main/java')],'classDirs':[str(output)]}]
   required.append({'path':task,'outputs':[str(output)],'destination':str(output),'sourceSets':ss,'graph_sources':sources if task==':compileJava' else [],'preexisting':[]})
   before={'task':task,'outputs':[str(output)],'sources':sources if task==':compileJava' else [],'preexisting':[]}
   after={**before,'executed':True,'didWork':task==':compileJava','skipped':task!=':compileJava','skipMessage':None if task==':compileJava' else 'NO-SOURCE','noSource':task!=':compileJava','upToDate':False,'failure':None,'files':compile_inventory.inventory(artifacts.files(output)) if output.exists() else []}
   put(gate/('compile-before'+task.replace(':','_')+'.json'),before);put(gate/('compile-after'+task.replace(':','_')+'.json'),after)
  put(gate/'compile-graph.json',{'synthetic_fixture':True,'run_root':str(run),'gate':'COMPILE','candidate':execution.SHA,'tree':execution.TREE,'repository':str(repo),'required':required,'expected_source_set_tasks':[r['path'] for r in required],'graph':[{'path':r['path'],'type':'JavaCompile','dependencies':[]} for r in required]})

 def test_B_external_gradle_instrumentation_compiles(self):
  """PASS: external init compiles with the real cached Gradle/Groovy API jars."""
  dist=next(Path('/home/user/.gradle/wrapper/dists').glob('**/bin/gradle')).parent.parent
  dest=self.root/'groovy-classes';dest.mkdir()
  env=execution.environment('backend',self.root)
  cmd=['java','-cp',str(dist/'lib/*')+os.pathsep+str(dist/'lib/plugins/*'),'org.codehaus.groovy.tools.FileSystemCompiler','-d',str(dest),str(execution.H/'compile.init.gradle')]
  self.assertEqual(native(cmd,self.root,self.root/'groovy.native.log',env),0,(self.root/'groovy.native.log').read_text())
  self.assertTrue(list(dest.rglob('*.class')))
 def test_B_real_gradle_generated_no_source_and_seal(self):
  """PASS: compile acceptance; real Gradle attempt or explicit blocked runtime + synthetic records/javac."""
  run,gate,repo=self.compile_fixture();r=compile_inventory.validate(run,gate,repo);put(gate/'compile-manifest.json',r)
  self.assertEqual(len(r['tasks']),4);self.assertTrue(any('Generated.java' in s['path'] for t in r['tasks'] for s in t['sources']))
  classes=[Path(x['path']) for x in r['manifest'] if x['path'].endswith('.class')];self.assertEqual(len(classes),3)
  receipt=artifacts.finalize(self.receipt(run),gate,artifacts.files(gate)+[Path(x['path']) for x in r['manifest']]);put(gate/'receipt.json',receipt)
  classes[0].unlink();artifacts.verify(receipt['artifacts'],gate,run.name,'COMPILE')
  saved=next(gate/x['path'] for x in receipt['artifacts'] if x['original_path'].endswith('.class'));saved.unlink()
  with self.assertRaises(OSError):artifacts.verify(receipt['artifacts'],gate,run.name,'COMPILE')
 def test_B_negative_scope_and_outcomes(self):
  """REJECT: missing tasks/outputs, stale class, altered sources, skipped/cached/up-to-date and false NO-SOURCE."""
  run,gate,repo=self.compile_fixture();compile_inventory.validate(run,gate,repo)
  graph=json.loads((gate/'compile-graph.json').read_text());after=json.loads((gate/'compile-after_compileJava.json').read_text())
  for variant in ['missing_task','missing_output','stale_class','skipped','cache','uptodate','false_no_source','source_changed','preexisting']:
   with self.subTest(variant=variant):
    case=self.root/variant;shutil.copytree(run,case);cg=case/'runtime/gates/COMPILE';cr=case/'sources/backend'
    # Relocate synthetic record paths, preserving all real observed records as source.
    for f in cg.glob('*.json'):f.write_text(f.read_text().replace(str(run),str(case)))
    gp=cg/'compile-graph.json';g=json.loads(gp.read_text());ap=cg/'compile-after_compileJava.json';a=json.loads(ap.read_text())
    if variant=='missing_task':g['required']=[t for t in g['required'] if t['path']!=':compileJava'];put(gp,g)
    elif variant=='missing_output':(cr/'build/classes/java/main/Main.class').unlink()
    elif variant=='stale_class':(cr/'build/classes/java/main/Stale.class').write_bytes(b'stale')
    elif variant=='source_changed':(cr/'src/main/java/Main.java').write_text('class Different {}')
    elif variant=='preexisting':g['required'][0]['preexisting']=['stale'];put(gp,g)
    else:
     a.update(skipped=True,skipMessage={'cache':'FROM-CACHE','uptodate':'UP-TO-DATE','false_no_source':'NO-SOURCE'}.get(variant,'SKIPPED'),upToDate=variant=='uptodate',noSource=variant=='false_no_source');put(ap,a)
    with self.assertRaises((RuntimeError,OSError)):compile_inventory.validate(case,cg,cr)
 def vite_fixture(self,base='/app/'):
  out=self.root/'dist';(out/'assets').mkdir(parents=True);(out/'.vite').mkdir()
  files={'index.html':'<script type="module" src="'+base+'assets/main.js?v=1#x"></script><link rel="stylesheet" href="'+base+'assets/main.css"><link rel="modulepreload" href="'+base+'assets/lazy.js"><link rel="preload" as="image" href="'+base+'assets/p.png"><a href="/route">route</a>',
  'assets/main.js':"import './lazy.js?x#y';import('./dynamic.js');new URL('./p.png?v#x',import.meta.url);import 'https://example.test/ext.js';",
  'assets/lazy.js':'export const x=1;','assets/dynamic.js':'export default 2;',
  'assets/main.css':'@import "./theme.css?v#x";x{background:url("./p.png?q#f");mask:url(data:image/png;base64,abc)}',
  'assets/theme.css':'x{color:red}', 'assets/p.png':'image',
  '.vite/manifest.json':json.dumps({'index.html':{'file':'assets/main.js','isEntry':True,'imports':['lazy'],'dynamicImports':['dynamic'],'css':['assets/main.css'],'assets':['assets/p.png']},'lazy':{'file':'assets/lazy.js'},'dynamic':{'file':'assets/dynamic.js'}})}
  for name,text in files.items():(out/name).write_text(text)
  return out
 def check_vite(self,out,base='/app/',name='closure'):
  return vite_closure.validate(out,base,D/'tools',self.root/(name+'.json'))
 def test_C_html_js_css_manifest_positive(self):
  """PASS: HTML, manifest, JS, CSS, base/query/fragment, external/data and routes."""
  r=self.check_vite(self.vite_fixture());self.assertGreater(len(r['edges']),15);self.assertEqual(len(r['inventory']),8);self.assertGreater(len(r['ignored']),2)
 def test_C_relative_root_and_cdn_bases(self):
  """PASS/REJECT: relative, root and configured CDN bases resolve into the same output scope."""
  for index,base in enumerate(['./','/','https://cdn.example.test/app/']):
   with self.subTest(base=base):
    folder=self.root/str(index);folder.mkdir();old=self.root;self.root=folder
    try:
     out=self.vite_fixture(base);r=self.check_vite(out,base);self.assertEqual(r['result'],'PASS')
     with (out/'index.html').open('a') as f:f.write('<script src="'+base+'absent.js"></script>')
     with self.assertRaises(RuntimeError):self.check_vite(out,base,'missing')
    finally:self.root=old
 def test_C_missing_html_js_css_transitive_and_escape(self):
  """REJECT: absent HTML assets, transitive chunk/asset, manifest graph hole and boundary escape."""
  original=self.vite_fixture()
  for variant in ['html_js','html_css','chunk','asset','manifest','escape','encoded_escape','dynamic_expression','css_escape']:
   with self.subTest(variant=variant):
    out=self.root/variant;shutil.copytree(original,out)
    if variant in ['html_js','html_css']:
     with (out/'index.html').open('a') as f:f.write('<script src="/app/absent.js"></script>' if variant=='html_js' else '<link rel="stylesheet" href="/app/absent.css">')
    elif variant=='chunk':(out/'assets/dynamic.js').unlink()
    elif variant=='asset':(out/'assets/p.png').unlink()
    elif variant=='manifest':
     p=out/'.vite/manifest.json';m=json.loads(p.read_text());m['index.html']['imports']=['missing-key'];put(p,m)
    elif variant=='dynamic_expression':(out/'assets/main.js').write_text('import(window.chunk)')
    elif variant=='css_escape':(out/'assets/main.css').write_text('a{background:url(../../outside.png)}')
    else:(out/'assets/main.js').write_text('import "'+('../../outside.js' if variant=='escape' else '%2e%2e/%2e%2e/outside.js')+'";')
    with self.assertRaises(RuntimeError):self.check_vite(out,name=variant)
 def test_C_real_tiny_vite_acceptance_and_seal(self):
  """PASS: tiny real Vite build, actual parsers.parse acceptance and independent full output copy."""
  src=self.root/'tiny';src.mkdir();(src/'index.html').write_text('<script type="module" src="/main.js"></script>')
  (src/'main.js').write_text("import './style.css';import('./lazy.js').then(console.log);document.body.innerHTML='tiny';")
  (src/'lazy.js').write_text('export default 42;');(src/'style.css').write_text('body{color:green}')
  run=self.root/'run';gate=run/'runtime/gates/FRONTEND_BUILD';gate.mkdir(parents=True);out=run/'runtime/outputs/frontend'
  cmd=['node',str(D/'tools/node_modules/vite/bin/vite.js'),'build',str(src),'--outDir',str(out),'--emptyOutDir','--manifest','--base','/app/']
  self.assertEqual(native(cmd,src,gate/'native.log',execution.environment('frontend',run)),0,(gate/'native.log').read_text())
  put(gate/'resolution.json',{'outDir':str(out),'emptyOutDir':True,'base':'/app/'})
  r=parsers.parse('FRONTEND_BUILD',run,gate,src);self.assertEqual(r['result'],'PASS')
  receipt=artifacts.finalize(self.receipt(run,'FRONTEND_BUILD'),gate,artifacts.files(gate)+artifacts.files(out));put(gate/'receipt.json',receipt)
  for p in out.rglob('*.js'):p.unlink()
  artifacts.verify(receipt['artifacts'],gate,run.name,'FRONTEND_BUILD')
 def test_A_consumer_directory_missing_class_reject(self):
  """REJECT: missing class in otherwise present consumer classpath directory."""
  run,gate=self.gate();out=run/'classes';out.mkdir();a=out/'A.class';b=out/'B.class';a.write_bytes(b'A');b.write_bytes(b'B')
  r=artifacts.finalize(self.receipt(run),gate,[a,b]);b.unlink()
  with self.assertRaisesRegex(RuntimeError,'DIRECTORY_MEMBERSHIP_CHANGED'):artifacts.live_equal([a],[r],run,[out])
 def test_C_actual_parser_missing_entry_asset_rejects(self):
  """REJECT: FRONTEND_BUILD parser rejects missing JS even with index.html and success marker."""
  source=self.vite_fixture();run=self.root/'run';out=run/'runtime/outputs/frontend';out.parent.mkdir(parents=True);shutil.copytree(source,out)
  gate=run/'runtime/gates/FRONTEND_BUILD';gate.mkdir(parents=True);(gate/'native.log').write_text('built in 1s')
  put(gate/'resolution.json',{'outDir':str(out),'emptyOutDir':True,'base':'/app/'})
  (out/'assets/main.js').unlink()
  with self.assertRaisesRegex(RuntimeError,'VITE_CLOSURE_REJECT'):parsers.parse('FRONTEND_BUILD',run,gate,self.root)
 def test_packaging_preserved_jar_independent_revalidation(self):
  """PASS then REJECT: recheck preserved JAR mapping; changed/duplicate/missing bytes fail."""
  from test_continuation import Controls
  helper=Controls('test_packaging_resources_and_zip_positive');helper.root=self.root
  m,resources,data=helper.manifest();jar=helper.zip(data);rule=helper.rule()
  run,gate=self.gate('jar','BOOTJAR');receipt=self.receipt(run,'BOOTJAR')
  def recheck(saved):self.assertEqual(packaging.jar(m,saved[str(jar)],rule)['result'],'PASS')
  artifacts.finalize(receipt,gate,[jar,*artifacts.files(resources)],recheck);jar.unlink()
  artifacts.verify(receipt['artifacts'],gate,run.name,'BOOTJAR')
  saved=gate/next(r['path'] for r in receipt['artifacts'] if r['original_path'].endswith('.jar'))
  self.assertEqual(packaging.jar(m,saved,rule)['result'],'PASS')
  with zipfile.ZipFile(saved,'a') as z:z.writestr('BOOT-INF/classes/static/contamination',b'bad')
  with self.assertRaises(RuntimeError):packaging.jar(m,saved,rule)
 def test_integrated_gate_success_and_copied_manifest_reject(self):
  """PASS/REJECT: run_gate finalizes a synthetic native command, then refuses copy-time corruption."""
  for corrupt in [False,True]:
   run,unused=self.gate('integrated-'+str(corrupt),'SETUP');repo=run/'sources/backend';repo.mkdir(parents=True);build=repo/'build';build.mkdir()
   init=run/'runtime/cache/backend/gradle/init.d';init.mkdir(parents=True);shutil.copyfile(execution.H/'packaging.init.gradle',init/'ep19-packaging.gradle')
   put(run/'baseline.json',{'entries':{}})
   target=build/'proof.class';code='from pathlib import Path;Path('+repr(str(target))+').write_bytes(b"compiled")'
   spec={'repository':str(repo),'cwd':str(repo),'command':[sys.executable,'-B','-c',code],'authoritative_command':['synthetic qualification command'],'dependencies':[],'output_bindings':{'required_files':[]},'timeout_seconds':20}
   scope={k:[] for k in ['protected','repositories','metadata_roots','allowed','cross_lane','enumeration_roots','pruned_roots','expected_missing']};scope.update(shared_git=None,allowed=[str(build)])
   original=artifacts.seal
   def seal(*args):
    rows=original(*args)
    if corrupt:
     row=next(r for r in rows if r['original_path']==str(target));p=Path(args[1])/row['path'];p.write_bytes(b'corrupted')
     row['size']=len(b'corrupted');row['sha256']=hashlib.sha256(b'corrupted').hexdigest()
    return rows
   with patch.object(runner,'repos',return_value=[]),patch.object(artifacts,'seal',side_effect=seal):
    r=runner.run_gate('ARCHITECTURE_SYNTAX',{'gates':{'ARCHITECTURE_SYNTAX':spec}},run,scope,{}, {})
   self.assertEqual(r['native_exit'],0)
   if corrupt:self.assertEqual(r['result'],'FAIL');self.assertIn('SEALED_ACCEPTANCE_MANIFEST_MISMATCH',r['reason'])
   else:
    self.assertEqual(r['result'],'PASS',r.get('reason'));freshness.dependency(r,run.name)
    artifacts.producer_inputs([r],run,repo);target.write_bytes(b'mutable changed')
    freshness.dependency(r,run.name)
    with self.assertRaises(RuntimeError):artifacts.producer_inputs([r],run,repo)
 def test_integrated_gate_acceptance_rejects_missing_compile_evidence(self):
  """REJECT: native success cannot bypass COMPILE completeness on run_gate path."""
  run=self.root/'run';repo=run/'sources/backend';repo.mkdir(parents=True);(run/'runtime/gates').mkdir(parents=True)
  spec={'repository':str(repo),'cwd':str(repo),'command':[sys.executable,'-B','-c','print("BUILD SUCCESSFUL in 1s")'],'authoritative_command':['synthetic'],'dependencies':[],'output_bindings':{'required_files':[]},'timeout_seconds':20}
  scope={k:[] for k in ['protected','repositories','metadata_roots','allowed','cross_lane','enumeration_roots','pruned_roots','expected_missing']};scope['shared_git']=None
  # Synthetic repository identity/preservation setup only; real observer, parser,
  # compile validator, error receipt and finalization execute unchanged.
  with patch.object(runner,'check_execution_seal'),patch.object(runner,'compare_baseline'),patch.object(runner,'repos',return_value=[]):
   r=runner.run_gate('COMPILE',{'gates':{'COMPILE':spec}},run,scope,{}, {})
  self.assertEqual(r['native_exit'],0);self.assertEqual(r['result'],'FAIL');self.assertIn('compile-graph.json',r['reason'])
