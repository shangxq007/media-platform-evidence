"""Local-only self-contained export; no remote or product Git mutation."""
from pathlib import Path
import json,hashlib,shutil,sys,zipfile,re
E=Path(__file__).resolve().parent;V=E/sys.argv[1];R=E/'LOCAL_REVIEW_PACKAGE';R.mkdir(exist_ok=False)
assert (V/'PRESERVATION_FINAL.json').is_file() and (E/'FINAL_REVIEW_REPORT_ZH.md').is_file()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(src,rel):
 dst=R/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def tree(src,rel):
 for p in sorted(src.rglob('*')):
  if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:copy(p,Path(rel)/p.relative_to(src))
for name in ['FINAL_REVIEW_REPORT_ZH.md','FINAL_FIELDS.json','FINAL_GATE_WRAPPER_EXIT.json','FINAL_GATE_WRAPPER.log','WRITER_ROUTER.log','SCOPE_AND_SOURCE_MAP.md','ALLOWLIST.json','WRITER_BRIEF.md','BASELINE_INSPECTION.json','BASELINE_VERIFICATION.json','BASELINE_TEST_REFERENCE.json','V6_FULL_UNIT.json','HELPER_PROVENANCE.json','PRESERVATION_BEFORE.json','SOURCE_CONTRACT_TEST_MAPPING.md','CONTROLLER_REVIEW.md','LAUNCH_RECOVERY.json','WRITER_HANDOFF.md','WRITER_CORRECTION_HANDOFF.md','INTERIM_CONTROLLER_OBSERVATIONS.md','CONTAINMENT_PREFLIGHT.json','BUILD_TARGET_PRESERVATION_BEFORE.json','FINAL_BROWSER_ACCOUNTING.json']:
 copy(E/name,name)
for p in sorted(E.glob('*.py')):copy(p,Path('harness')/p.name)
if (E/'writer-runs').exists():tree(E/'writer-runs','writer-runs')
for name in ['FINAL_TREE.txt','TASK_DELTA.patch','FINAL_TREE_MANIFEST.txt','SOURCE_DELTA.json','FINAL_VALIDATION_PLAN.json','TEST_IDENTITY_ACCOUNTING.json','BUILD_MANIFEST.json','BUILD_MANIFEST.sha256','PRESERVATION_FINAL.json','BUILD_TARGET_PRESERVATION_FINAL.json','PATCH_REPLAY.json','FULL_UNIT.json','TARGETED_FINAL.json','FIXTURE_HOST_INPUTS.json']:
 copy(V/name,Path('validation')/name)
copy(V/'fixture-host/entry.tsx','validation/fixture-host/entry.tsx')
for sub in ['gates','source','before-source','build']:tree(V/sub,Path('validation')/sub)
for sub in ['src','scripts']:tree(V/'snapshot/frontend'/sub,Path('context/frontend')/sub)
for p in sorted((V/'snapshot/frontend').iterdir()):
 if p.is_file() and p.suffix in ['.json','.ts','.js','.mjs','.html']:copy(p,Path('context/frontend')/p.name)
for name in ['frontend-product-information-architecture-v1.md','frontend-foundation-checkpoint-a-implementation-v1.md','frontend-current-governed-scope-ledger-v1.tsv','frontend-product-path-classification-v1.tsv','frontend-backend-application-api-gap-ledger-v1.md']:
 p=V/'snapshot/docs/architecture/governance'/name
 if p.is_file():copy(p,Path('context/docs/architecture/governance')/name)
for name in ['UX_WAVE_1_REVIEW.md','BACKEND_ENABLEMENT_REQUESTS.tsv']:copy(V/'snapshot/frontend/governance'/name,Path('context/frontend/governance')/name)
copy(V/'snapshot/AGENTS.md','context/AGENTS.md')
copy(Path('/home/user/Documents/03-大模型上下文-精简版.md'),'context/OWNER_DECISION_CONTEXT_ZH.md')
B=V/json.loads((E/'FINAL_BROWSER_ACCOUNTING.json').read_text())['directory']
for p in sorted(B.iterdir()):
 if p.is_file():copy(p,Path('browser')/p.name)
for a in sorted(E.glob('final-validation-*')):
 if a==V:continue
 for p in sorted(a.glob('gates/*')):
  if p.is_file():copy(p,Path('prior-attempts')/a.name/'gates'/p.name)
 for name in ['FINAL_TREE.txt','SOURCE_DELTA.json']:
  if (a/name).is_file():copy(a/name,Path('prior-attempts')/a.name/name)
for a in sorted(V.glob('browser-*')):
 if a==B or not a.is_dir():continue
 for p in a.iterdir():
  if p.is_file():copy(p,Path('prior-browser-attempts')/a.name/p.name)
# Omit unrelated shared-repository stash descriptions from public-ready copies.
# Preserve original local writer records and a hash of every omitted value.
san=[]
for rel in ['writer-runs/correction-00-start-state.json','writer-runs/correction-05-preservation.json']:
 p=R/rel
 if not p.exists():continue
 original=p.read_bytes();obj=json.loads(original)
 def redact(value,keys):
  if isinstance(value,dict):
   for key in list(value):
    if key=='stash' and isinstance(value[key],str):
     raw=value[key].encode();san.append({'path':rel,'json_path':keys+[key],'original_file_sha256':hashlib.sha256(original).hexdigest(),'omitted_value_sha256':hashlib.sha256(raw).hexdigest(),'omitted_bytes':len(raw),'reason':'unrelated shared-repository stash descriptions; original local record preserved; token-shape scan matched a task branch-name substring, not established credential'})
     value[key]='OMITTED_UNRELATED_STASH_DESCRIPTIONS_SEE_SANITIZATION_RECEIPT'
    else:redact(value[key],keys+[key])
  elif isinstance(value,list):
   for i,item in enumerate(value):redact(item,keys+[i])
 redact(obj,[]);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 for row in san:
  if row['path']==rel:row['sanitized_file_sha256']=sha(p)
(R/'SANITIZATION_RECEIPT.json').write_text(json.dumps({'records':san,'original_local_records_unchanged':True,'product_source_endpoints_unchanged':True},indent=2))
chunkmap=[]
for p in list((R/'validation/build').rglob('*.js')):
 raw=p.read_bytes()
 if len(raw)<=100000:continue
 text=raw.decode('utf-8');parts=[]
 for i,start in enumerate(range(0,len(text),50000)):
  data=text[start:start+50000].encode('utf-8');q=R/'build-review-chunks'/p.name/(f'{i:04d}.txt');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);parts.append({'path':str(q.relative_to(R)),'bytes':len(data),'sha256':sha(q)})
 assert b''.join((R/x['path']).read_bytes() for x in parts)==raw
 chunkmap.append({'original':str(p.relative_to(R)),'bytes':len(raw),'sha256':sha(p),'encoding':'ordered UTF-8 byte concatenation; Unicode-character boundaries','parts':parts})
(R/'BUILD_CHUNK_RECONSTRUCTION.json').write_text(json.dumps(chunkmap,indent=2))
delta=json.loads((V/'SOURCE_DELTA.json').read_text());lines=['# V7 Render observability — local source review','',f"Accepted base `{delta['baseline_tree']}` → unfrozen implementation `{delta['final_tree']}`. INDEPENDENT_REVIEW REQUIRED. No product commit or remote publication.",'','[中文报告](FINAL_REVIEW_REPORT_ZH.md) · [Controller review](CONTROLLER_REVIEW.md) · [Contract/test mapping](SOURCE_CONTRACT_TEST_MAPPING.md) · [Complete patch](validation/TASK_DELTA.patch) · [Replay](validation/PATCH_REPLAY.json) · [Tests](validation/TEST_IDENTITY_ACCOUNTING.json) · [Browser accounting](FINAL_BROWSER_ACCOUNTING.json) · [Build manifest](validation/BUILD_MANIFEST.json)','','| Status | Path | Base endpoint | Final endpoint |','|---|---|---|---|']
for r in delta['paths']:
 p=r['path'];before=f'[base](validation/before-source/{p})' if r['status']!='A' else 'ABSENT (new path)';lines.append(f"|{r['status']}|`{p}`|{before}|[final](validation/source/{p})|")
lines+=['','## Final browser screenshots','']+[f'![{p.stem}](browser/{p.name})' for p in sorted((R/'browser').glob('*.png'))]
lines+=['','## Boundaries','V6 original reporter is preserved historical evidence; V7 gates/browser are fresh exact-tree execution. Explicit isolated simulated identity/data, CDP focus emulation and DOM locator/locale/fixture assistance are disclosed in browser records. No real contract, server permission, backend integration or physical device/IME/screenreader acceptance. Historical narrow/internal scrolling and governance limits remain open. Product tracked dist is preserved; tested runtime is the complete external build. Receipt absolute paths preserve native provenance; portable payload paths are in this index. Parent must independently verify and separately publish evidence. STOP before Workflow.']
(R/'REVIEW_INDEX.md').write_text('\n'.join(lines)+'\n')
index={'report_fields':json.loads((E/'FINAL_FIELDS.json').read_text()),'task':'FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7','lane':'FRONTEND','final_tree':delta['final_tree'],'base_tree':delta['baseline_tree'],'changed_paths':len(delta['paths']),'report':'FINAL_REVIEW_REPORT_ZH.md','source_index':'REVIEW_INDEX.md','test_accounting':'validation/TEST_IDENTITY_ACCOUNTING.json','browser':'browser','build':'validation/build','patch':'validation/TASK_DELTA.patch','replay':'validation/PATCH_REPLAY.json','publication':'NOT_PERFORMED','independent_review':'REQUIRED','files':[{'path':str(p.relative_to(R)),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file()]}
(R/'REVIEW_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}')]
findings=[]
for p in R.rglob('*'):
 if p.is_file() and p.suffix not in ['.png','.woff','.woff2'] and any(x.search(p.read_bytes()) for x in patterns):findings.append(str(p.relative_to(R)))
assert not findings,findings
(R/'BOUNDED_SECRET_SCAN.json').write_text(json.dumps({'findings':findings,'scope':'Review payload private-key/GitHub/OpenAI-like token shapes only, not whole-host guarantee. Raw agent reasoning and account logs excluded.','fixture_markers':'explicit simulated noncredential identifiers retained'},indent=2))
# Offline index links and source endpoints.
for href in re.findall(r'\]\(([^)]+)\)',(R/'REVIEW_INDEX.md').read_text()):assert (R/href).is_file(),href
for row in delta['paths']:
 assert sha(R/'validation/source'/row['path'])==row['after_sha256']
 if row['before_sha256']:assert sha(R/'validation/before-source'/row['path'])==row['before_sha256']
files=sorted((p for p in R.rglob('*') if p.is_file()),key=lambda p:str(p.relative_to(R)).encode())
manifest=''.join(sha(p)+'  '+str(p.relative_to(R))+'\n' for p in files);(R/'MANIFEST.sha256').write_text(manifest)
for line in manifest.splitlines():
 h,p=line.split('  ',1);assert sha(R/p)==h
Z=E/'LOCAL_REVIEW_PACKAGE.zip'
with zipfile.ZipFile(Z,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==sha(R/n)
 count=len(z.namelist())
receipt={'tree':delta['final_tree'],'package':str(R),'manifest_files':len(files),'manifest_sha256':sha(R/'MANIFEST.sha256'),'archive':str(Z),'archive_entries':count,'archive_sha256':sha(Z),'archive_integrity_and_all_entry_bytes':'PASS','source_index_sha256':sha(R/'REVIEW_INDEX.md'),'machine_index_sha256':sha(R/'REVIEW_INDEX.json'),'report_sha256':sha(R/'FINAL_REVIEW_REPORT_ZH.md'),'local_only':True,'independent_review':'REQUIRED'}
(E/'LOCAL_PACKAGE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
