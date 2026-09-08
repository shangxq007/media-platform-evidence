"""Local review export; run only after final gates/browser review."""
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
for name in ['FINAL_REVIEW_REPORT_ZH.md','SELECTION_AND_SCOPE.md','ALLOWLIST.json','EXPECTED_PATH_CLASSIFICATION.json','EXPECTED_PATH_CLASSIFICATION_FINAL.json','WRITER_BRIEF.md','BASELINE_INSPECTION.json','BASELINE_VERIFICATION.json','BASELINE_TEST_REFERENCE.json','V5_FULL_UNIT.json','RESUME_PREFLIGHT.json','HELPER_PROVENANCE.md','PRESERVATION_BEFORE.json','SOURCE_CONTRACT_TEST_MAPPING.md','CONTROLLER_REVIEW.md','EXECUTION_APPROVAL_RECOVERY.md','PREVIOUS_BLOCKER_RECEIPT.json','CLASSIFICATION8_APPROVED_CORRECTION.md','CLASSIFICATION8_VERIFIED.json','FINAL_GATE_WRAPPER_EXIT.json','BROWSER_COVERAGE_EXTENSION.md','FINAL_BROWSER_POINTER.json','FINAL_BROWSER_ACCOUNTING.json','CONTROLLER_REVIEW_REQUEST.md','FINAL_BOUNDED_REVIEW_FOLLOWUP.md']:
 copy(E/name,name)
for p in sorted(E.glob('*.py')):copy(p,Path('harness')/p.name)
for p in sorted((E/'writer').rglob('*')):
 if p.is_file() and p.suffix in ['.md','.json','.log','.txt','.py','.exit','.tsv','.patch']:copy(p,Path('writer')/p.relative_to(E/'writer'))
for name in ['FINAL_TREE.txt','TASK_DELTA.patch','FINAL_TREE_MANIFEST.txt','SOURCE_DELTA.json','FINAL_VALIDATION_PLAN.json','TEST_IDENTITY_ACCOUNTING.json','LINT_DIAGNOSTIC_ACCOUNTING.json','BUILD_MANIFEST.json','BUILD_MANIFEST.sha256','PRESERVATION_FINAL.json','PATCH_REPLAY.json','FULL_UNIT.json','TARGETED_FINAL.json']:
 copy(V/name,Path('validation')/name)
copy(V/'fixture-host/entry.tsx','validation/fixture-host/entry.tsx')
copy(V/'FIXTURE_HOST_INPUTS.json','validation/FIXTURE_HOST_INPUTS.json')
for sub in ['gates','source','before-source','build']:tree(V/sub,Path('validation')/sub)
# Preserve every final frontend source plus actual guard and dependency configuration.
for sub in ['src','scripts']:tree(V/'snapshot/frontend'/sub,Path('context/frontend')/sub)
for p in sorted((V/'snapshot/frontend').iterdir()):
 if p.is_file() and p.suffix in ['.json','.ts','.js','.mjs','.html']:copy(p,Path('context/frontend')/p.name)
for name in ['frontend-product-information-architecture-v1.md','frontend-foundation-checkpoint-a-implementation-v1.md','frontend-current-governed-scope-ledger-v1.tsv','frontend-product-path-classification-v1.tsv','frontend-backend-application-api-gap-ledger-v1.md']:
 p=V/'snapshot/docs/architecture/governance'/name
 if p.is_file():copy(p,Path('context/docs/architecture/governance')/name)
copy(V/'snapshot/AGENTS.md','context/AGENTS.md')
B=V/json.loads((E/'FINAL_BROWSER_POINTER.json').read_text())['directory']
for p in sorted(B.iterdir()):
 if p.is_file():copy(p,Path('browser')/p.name)
# Keep failed attempt receipts separately, not in final successful denominators.
for a in sorted(E.glob('final-validation-*')):
 if a==V:continue
 for p in sorted(a.glob('gates/*')):
  if p.is_file():copy(p,Path('prior-attempts')/a.name/'gates'/p.name)
 for name in ['FINAL_TREE.txt','SOURCE_DELTA.json']:
  if (a/name).is_file():copy(a/name,Path('prior-attempts')/a.name/name)
for a in sorted(V.glob('browser-*')):
 if a==B or not a.is_dir() or not (a/'NATIVE_CHECKS.json').is_file():continue
 for p in a.iterdir():
  if p.is_file():copy(p,Path('prior-browser-attempts')/a.name/p.name)
chunkmap=[]
for p in list((R/'validation/build').rglob('*.js')):
 raw=p.read_bytes()
 if len(raw)<=100000:continue
 text=raw.decode('utf-8');parts=[]
 for i,start in enumerate(range(0,len(text),50000)):
  data=text[start:start+50000].encode('utf-8');q=R/'build-review-chunks'/p.name/(f'{i:04d}.txt');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);parts.append({'path':str(q.relative_to(R)),'bytes':len(data),'sha256':sha(q)})
 assert b''.join((R/x['path']).read_bytes() for x in parts)==raw
 chunkmap.append({'original':str(p.relative_to(R)),'bytes':len(raw),'sha256':sha(p),'encoding':'ordered UTF-8 byte concatenation; boundaries at Unicode characters','parts':parts})
(R/'BUILD_CHUNK_RECONSTRUCTION.json').write_text(json.dumps(chunkmap,indent=2))
delta=json.loads((V/'SOURCE_DELTA.json').read_text());lines=['# Source review index','',f"Accepted base `{delta['baseline_tree']}` → unfrozen implementation `{delta['final_tree']}`. No source commit or publication.",'','[Chinese report](FINAL_REVIEW_REPORT_ZH.md) · [Controller review](CONTROLLER_REVIEW.md) · [Contract/test mapping](SOURCE_CONTRACT_TEST_MAPPING.md) · [Complete patch](validation/TASK_DELTA.patch) · [Replay](validation/PATCH_REPLAY.json)','','| Status | Path | Base endpoint | Final endpoint |','|---|---|---|---|']
for r in delta['paths']:
 p=r['path'];before=f'[base](validation/before-source/{p})' if r['status']!='A' else 'ABSENT (new path)';lines.append(f"|{r['status']}|`{p}`|{before}|[final](validation/source/{p})|")
lines+=['','## Browser screenshots','']+[f'![{p.stem}](browser/{p.name})' for p in sorted((R/'browser').glob('*.png'))]
lines+=['','## Provenance and limits','Absolute receipt paths name original execution locations. Portable payload paths are indexed here and in REVIEW_INDEX.json; receipts are copied without rewriting their native provenance. Baseline V5 unit reporter is historical, final validation and browser receipts are fresh. Prior attempts are retained and excluded from final PASS counts. Historical tracked dist is preserved, not the fresh runtime. This package does not independently accept or publish product code.']
(R/'REVIEW_INDEX.md').write_text('\n'.join(lines)+'\n')
index={'final_tree':delta['final_tree'],'base_tree':delta['baseline_tree'],'changed_paths':len(delta['paths']),'report':'FINAL_REVIEW_REPORT_ZH.md','source_index':'REVIEW_INDEX.md','test_accounting':'validation/TEST_IDENTITY_ACCOUNTING.json','browser':'browser','build':'validation/build','patch':'validation/TASK_DELTA.patch','replay':'validation/PATCH_REPLAY.json','publication':'NOT_PERFORMED','independent_acceptance':'NOT_CLAIMED','files':[{'path':str(p.relative_to(R)),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(R.rglob('*')) if p.is_file()]}
(R/'REVIEW_INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
# Bounded secret-shape scan, no raw suspicious value output.
patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}')]
findings=[]
for p in R.rglob('*'):
 if p.is_file() and p.suffix not in ['.png','.woff','.woff2']:
  data=p.read_bytes()
  if any(x.search(data) for x in patterns):findings.append(str(p.relative_to(R)))
assert not findings,findings
(R/'BOUNDED_SECRET_SCAN.json').write_text(json.dumps({'findings':findings,'scope':'review payload, private-key/GitHub/OpenAI-like token shapes only; not whole-host guarantee','fixture_markers':'explicit simulated noncredential identifiers retained'},indent=2))
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
receipt={'tree':delta['final_tree'],'package':str(R),'manifest_files':len(files),'manifest_sha256':sha(R/'MANIFEST.sha256'),'archive':str(Z),'archive_entries':count,'archive_sha256':sha(Z),'archive_integrity_and_all_entry_bytes':'PASS','source_index_sha256':sha(R/'REVIEW_INDEX.md'),'report_sha256':sha(R/'FINAL_REVIEW_REPORT_ZH.md'),'local_only':True}
(E/'LOCAL_PACKAGE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
