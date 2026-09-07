from pathlib import Path
import json,hashlib,subprocess,shutil,os,collections
R=Path(__file__).resolve().parents[1];A=R.parent/'FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1';S=R/'snapshot';T=(R/'inputs/corrected-tree.txt').read_text().strip()
def sha(b):return hashlib.sha256(b).hexdigest()
seal=json.loads((A/'BROWSER_INPUT_SEAL.json').read_text());assert sha((A/'PYTHON_ENVIRONMENT_MANIFEST.json').read_bytes())==seal['environment_manifest_sha256'];em=json.loads((A/'PYTHON_ENVIRONMENT_MANIFEST.json').read_text())
for f,h in em['installed_files'].items():assert sha((A/'venv'/f).read_bytes())==h,f
print('QUALIFIED_ENV_FILES',len(em['installed_files']))
manifest={str(p.relative_to(R/'build')):sha(p.read_bytes()) for p in sorted((R/'build').rglob('*')) if p.is_file()};(R/'inputs/BUILD_MANIFEST.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in manifest.items()));bh=sha((R/'inputs/BUILD_MANIFEST.sha256').read_bytes())
paths=json.loads((R/'inputs/baseline.json').read_text())['files'];source={f:sha((S/f).read_bytes()) for f in paths};(R/'inputs/SOURCE_MANIFEST.json').write_text(json.dumps({'tree':T,'files':source},indent=2))
# Expanded execution/discovery identity bridge, preserving names and ancestor arrays.
disc=json.loads((R/'gates/discovery-tests.json').read_text());full=json.loads((R/'gates/full-tests.json').read_text());ident=[]
for f in full['testResults']:
 for a in f['assertionResults']:ident.append({'file':str(Path(f['name']).relative_to(S/'frontend')),'ancestors':a['ancestorTitles'],'title':a['title'],'status':a['status']})
print('DISC_SAMPLE',disc[:1]);dc=collections.Counter((str(Path(x['file']).relative_to(S/'frontend')),' > '.join([x['name']]) if False else x['name']) for x in disc);ec=collections.Counter((x['file'],' > '.join(x['ancestors']+[x['title']])) for x in ident);assert dc==ec,(dc-ec,ec-dc)
(R/'gates/TEST_IDENTITIES.json').write_text(json.dumps({'identities':ident,'discovery_count':len(disc),'execution_count':len(ident),'missing':[],'unexpected':[],'statuses':dict(collections.Counter(x['status'] for x in ident))},indent=2))
H=R/'harness';H.mkdir();transform=[]
for f,h in seal['harness'].items():
 assert sha((A/'harness'/f).read_bytes())==h
 if f not in ['BASELINE.json','TREE_BINDING.json','BUILD_ARTIFACT_BOUNDARY.json','scope_check.py']:shutil.copyfile(A/'harness'/f,H/f)
(H/'TREE_BINDING.json').write_text(json.dumps({'FINAL_EXACT_IMPLEMENTATION_TREE':T,'accepted_diagnosis_tree':'ffeec76721e7334325a4a4c9f3aaea84174d0cb4','status':'FRESH_CORRECTED_TREE_VALIDATION_NOT_ACCEPTANCE'},indent=2));(H/'BUILD_ARTIFACT_BOUNDARY.json').write_text(json.dumps({'build_manifest_sha256':bh,'build_artifacts':manifest},indent=2))
# Scope binding differs intentionally from historical seven-lane shared-ref freeze.
(H/'scope_check.py').write_text('''from pathlib import Path
import json,hashlib,time
E=Path(__file__).parent
ROOT=Path('''+repr(str(R))+''')
def check(label):
 source=json.loads((ROOT/'inputs/SOURCE_MANIFEST.json').read_text());build=json.loads((E/'BUILD_ARTIFACT_BOUNDARY.json').read_text())
 bad=[p for p,h in source['files'].items() if hashlib.sha256((ROOT/'snapshot'/p).read_bytes()).hexdigest()!=h]
 bad += [p for p,h in build['build_artifacts'].items() if hashlib.sha256((ROOT/'build'/p).read_bytes()).hexdigest()!=h]
 row={'label':label,'time':time.time(),'tree':source['tree'],'source_entries':len(source['files']),'build_entries':len(build['build_artifacts']),'changed':bad,'backend_refs_not_monitored':True}
 with (E/'SCOPE_TRIPWIRE.jsonl').open('a') as f:f.write(json.dumps(row)+'\\n')
 assert not bad,row
 return row
''')
wheel=next((A/'wheels').glob('*.whl')) if (A/'wheels').exists() else next(A.rglob('websockets-15.0.1-py3-none-any.whl'))
config={'interpreter':str(A/'venv/bin/python3'),'version':'15.0.1','wheel':str(wheel),'wheel_sha256':'f7a866fbc1e97b5c617ee4116daaa09b722101d4a3c170c787450ba409f9736f','connect_api':'connect','sources':{p.name:sha(p.read_bytes()) for p in H.iterdir() if p.is_file()}}
(R/'inputs/qualification-config.json').write_text(json.dumps(config,indent=2));p=subprocess.run([config['interpreter'],'-B',str(H/'environment_preflight.py'),str(R/'inputs/qualification-config.json')],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'});(R/'inputs/ENVIRONMENT_QUALIFICATION.json').write_text(p.stdout);assert p.returncode==0,p.stdout+p.stderr
for f in ['scope_check.py','TREE_BINDING.json','BUILD_ARTIFACT_BOUNDARY.json']:
 transform.append({'file':f,'original_sha256':seal['harness'][f],'new_sha256':sha((H/f).read_bytes()),'reason':'New exact source/build and task-owned preservation binding; backend concurrent branches excluded as explicitly required by Owner. No scenario assertion/input changes.'})
(R/'inputs/HARNESS_BINDING_CHANGES.json').write_text(json.dumps(transform,indent=2));print('BUILD',bh,'TESTS',len(ident),'QUALIFICATION_PASS')
