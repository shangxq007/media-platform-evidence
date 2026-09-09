from pathlib import Path
import shutil,json,hashlib,zipfile,re
C=Path(__file__).resolve().parent;E=C.parent;V=C/'validation-01';B=C/'browser-continuation';R=B/'focused-03';P=C/'LOCAL_REVIEW_PACKAGE';P.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
def copy(src,name):
 dest=P/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
for n in ['REVIEW_REPORT_ZH.md','BROWSER_PARENT_VERIFICATION.json','OLD_PACKAGE_VERIFIED.json','RENEWAL_VISUAL_COMPARISON.png','PRELIMINARY_REVIEW.md','capture_final.py','gate.py','test_accounting.py']:
 copy(C/n,n)
for n in ['FINAL_TREE.txt','TASK_DELTA.patch','FINAL_TREE_MANIFEST.txt','SOURCE_DELTA.json','PATCH_REPLAY.json','PRESERVATION.json','REQUIRED_GATE_SUMMARY.json','FINAL_VALIDATION_PLAN.json','TARGETED_FINAL.json','FULL_UNIT.json','TEST_IDENTITY_ACCOUNTING.json','LINT.json','LINT_ACCOUNTING.json','BUILD_MANIFEST.sha256']:
 copy(V/n,'validation/'+n)
for sub in ['source','before-source','gates','build']:
 for f in (V/sub).rglob('*'):
  if f.is_file():copy(f,'validation/'+str(f.relative_to(V)))
# Additional unchanged relevant production source for local reviewers.
for n in ['src/product/workflow-sketch/WorkflowSketch.tsx','src/product/workflow-sketch/model.ts','src/interaction/SelectionContext.tsx','src/foundation/projectContext.tsx','src/foundation/effectiveAccess.tsx','src/foundation/platformClient.ts','src/auth/oidcConfig.ts','package.json','package-lock.json']:
 copy(V/'snapshot/frontend'/n,'context-source/frontend/'+n)
for f in (C/'writer').iterdir():
 if f.is_file() and f.suffix in ['.json','.md','.txt','.log','.patch']:copy(f,'writer/'+f.name)
for n in ['BROWSER_HANDOFF.md','BROWSER_FINAL_HANDOFF.md','build.log','build-02.log','build-03.log','BUILD_02.json','BUILD_03.json','build-options-03.mjs','parent-build-03.mjs']:
 copy(B/n,'browser/'+n)
for f in (B/'fixture-host').iterdir():
 if f.is_file():copy(f,'browser/fixture-host/'+f.name)
for sub in ['focused-01','focused-02','focused-03']:
 for f in (B/sub).iterdir():
  if f.is_file():copy(f,'browser/'+sub+'/'+f.name)
for f in (B/'build-03').rglob('*'):
 if f.is_file():copy(f,'browser/build-03/'+str(f.relative_to(B/'build-03')))
for n in ['FINAL_REPORT_ZH.md','NEW_PUSH.log','PUSH_RETRY_02.log','NEW_PUSH_RESULT.json','PUSH_RETRY_02_RESULT.json']:
 copy(E/n,'history/'+n)
for n in ['writer-native.log','writer-native-02.log','writer-native-03.log']:copy(C/n,'history/'+n)
# Existing UTF-8 chunk/reassembly scheme, original and chunks independently hashed.
rebuild=[]
for root in [P/'validation/build',P/'browser/build-03']:
 for f in sorted(root.rglob('*')):
  if not f.is_file() or f.stat().st_size<=96000:continue
  data=f.read_bytes();parts=[];start=0;num=0
  while start<len(data):
   end=min(start+96000,len(data))
   while True:
    try:data[start:end].decode('utf-8');break
    except UnicodeDecodeError:end-=1
   chunk=data[start:end];name='build-chunks/'+str(f.relative_to(P)).replace('/','__')+f'.part{num:03d}.txt';out=P/name;out.parent.mkdir(exist_ok=True);out.write_bytes(chunk)
   parts.append({'path':name,'bytes':len(chunk),'sha256':sha(chunk)});start=end;num+=1
  rebuild.append({'original':str(f.relative_to(P)),'bytes':len(data),'sha256':sha(data),'parts':parts})
(P/'BUILD_CHUNK_RECONSTRUCTION.json').write_text(json.dumps(rebuild,indent=2)+'\n')
index={'TASK':'FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8','CONTINUATION':'SESSION_CONTINUITY_AND_NODE_TITLE_LAYOUT_CORRECTION','tree':(V/'FINAL_TREE.txt').read_text().strip(),'report':'REVIEW_REPORT_ZH.md','delta':'validation/TASK_DELTA.patch','source_endpoints':'validation/SOURCE_DELTA.json','engineering_gates':'validation/REQUIRED_GATE_SUMMARY.json','test_accounting':'validation/TEST_IDENTITY_ACCOUNTING.json','browser':'browser/focused-03/ACCOUNTING.json','parent_verification':'BROWSER_PARENT_VERIFICATION.json','manifest':'MANIFEST.sha256','chunks':'BUILD_CHUNK_RECONSTRUCTION.json','INDEPENDENT_REVIEW':'REQUIRED','PRODUCT_PUBLICATION':'NOT_PERFORMED','STOP':'YES'}
(P/'REVIEW_INDEX.json').write_text(json.dumps(index,indent=2)+'\n')
(P/'REVIEW_INDEX.md').write_text('# V8 continuation independent review\n\n[中文报告](REVIEW_REPORT_ZH.md) · [Machine index](REVIEW_INDEX.json) · [Manifest](MANIFEST.sha256)\n\nActual implementation tree `'+index['tree']+'`. Seven frontend gates PASS; final browser 7 scenarios / 14 runs / 88 assertions. Conditional continuity with explicit missing-session and untagged-SDK limits; not actual IdP integration. Independent review REQUIRED; product publication NOT_PERFORMED.\n\n[Exact patch](validation/TASK_DELTA.patch) · [Endpoints](validation/SOURCE_DELTA.json) · [Test identity accounting](validation/TEST_IDENTITY_ACCOUNTING.json) · [Browser checks](browser/focused-03/NATIVE_CHECKS.json) · [Visual/readback verification](BROWSER_PARENT_VERIFICATION.json).\n\n[Chunk reconstruction](BUILD_CHUNK_RECONSTRUCTION.json): concatenate listed UTF-8 parts in order; validate each SHA256 and reconstructed original SHA256. Original assets are included for byte comparison.\n\nPrior sealed evidence and two HTTP408 failures are historical; current transport verification is recorded separately in local detached receipt, not recursively republished.\n')
files={str(f.relative_to(P)):f.read_bytes() for f in P.rglob('*') if f.is_file()}
for n,data in files.items():
 assert not re.search(rb'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',data),n
manifest=''.join(sha(data)+'  '+n+'\n' for n,data in sorted(files.items())).encode();(P/'MANIFEST.sha256').write_bytes(manifest);files['MANIFEST.sha256']=manifest
Z=C/'LOCAL_REVIEW_PACKAGE.zip'
with zipfile.ZipFile(Z,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,data in sorted(files.items()):z.writestr(n,data)
with zipfile.ZipFile(Z) as z:
 assert len(z.namelist())==len(files) and set(z.namelist())==set(files)
 for n,data in files.items():assert z.read(n)==data and (P/n).read_bytes()==data
for entry in rebuild:
 data=b''.join((P/x['path']).read_bytes() for x in entry['parts']);assert sha(data)==entry['sha256'] and data==(P/entry['original']).read_bytes()
r={'payload_files':len(files)-1,'archive_entries':len(files),'payload_bytes':sum(map(len,files.values())),'archive_bytes':Z.stat().st_size,'manifest_sha256':sha(manifest),'archive_sha256':sha(Z.read_bytes()),'mismatches':0,'chunks_reconstructed':len(rebuild),'excluded':'all node_modules, browser profiles/home caches, object directories and unrelated historical snapshots; original history retained locally'}
(C/'LOCAL_PACKAGE_VERIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
