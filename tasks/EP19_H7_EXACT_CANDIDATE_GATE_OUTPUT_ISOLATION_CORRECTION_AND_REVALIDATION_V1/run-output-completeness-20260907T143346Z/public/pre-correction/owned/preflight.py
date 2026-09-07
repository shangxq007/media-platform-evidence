from pathlib import Path
import os,subprocess,json,hashlib,time,shutil,zipfile
D=Path(__file__).resolve().parents[1];P=D.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1';R=Path('/home/user/Documents/workspace/projects/media-platform')
SHA='689ab9456461a8d19a72d059f5157092efc43aff';TREE='6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6';BASE='86d6aef94fd5e58da552e97c11473cff6eca734e'
ENV={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};ENV['GIT_OPTIONAL_LOCKS']='0';ENV['GIT_NO_REPLACE_OBJECTS']='1'
def git(root,*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*a],env=ENV)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,o):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(o,f,indent=2,sort_keys=True);f.write('\n')
def filesnapshot(root,names):
 out={}
 for n in sorted(set(names)):
  p=root/n
  if not p.exists() and not p.is_symlink():out[n]={'missing':True};continue
  s=p.lstat();out[n]={'sha256':hashlib.sha256(os.fsencode(os.readlink(p)) if p.is_symlink() else p.read_bytes()).hexdigest(),'size':s.st_size,'mode':s.st_mode,'dev':s.st_dev,'inode':s.st_ino,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
 return out
assert h(P/'REVIEW_PACKAGE.zip')=='a2969caf4912858dfa0b5f7eacd27085ff1eb643156f9f1f7ab43e8ac070b69b'
F=Path(json.loads((P/'FULL_BACKEND.receipt.json').read_text())['cwd'])
assert git(F,'show','-s','--format=%H %T %P','HEAD').decode().strip()==f'{SHA} {TREE} {BASE}'
assert git(F,'diff','HEAD')==(P/'CANDIDATE_EXECUTION_DRIFT.diff').read_bytes()
prior_names=[str(p.relative_to(P)) for p in P.iterdir() if p.is_file()]+[str(p.relative_to(P)) for p in (P/'owned').glob('*.py')]
tracked=git(R,'ls-files','-z').decode().rstrip('\0').split('\0');failed_names=git(F,'ls-files','-z').decode().rstrip('\0').split('\0')+git(F,'ls-files','--others','--exclude-standard','-z').decode().rstrip('\0').split('\0');failed_names=[n for n in failed_names if n]
start=time.time()
put('observations/BEFORE.json',{'start':start,'canonical_tracked':filesnapshot(R,tracked),'canonical_index_head':filesnapshot(R,['.git/index','.git/HEAD']),'canonical_pack':filesnapshot(R,[str(p.relative_to(R)) for p in (R/'.git/objects/pack').iterdir() if p.is_file()]),'refs':git(R,'for-each-ref','--format=%(refname) %(objectname)').decode(),'registrations':git(R,'worktree','list','--porcelain').decode(),'failed_scene':filesnapshot(F,failed_names),'failed_status':git(F,'status','--porcelain').decode(),'prior_evidence':filesnapshot(P,prior_names),'end':time.time()})
required=['FINAL_REPORT.txt','FINAL_DELIVERY_INDEX.txt','EXECUTION_DRIFT_DISPOSITION.json','CANDIDATE_IDENTITY.json','MONITOR_CONTRACT.txt','SCOPE_CLASSIFICATION.txt','TEST_IDENTITY_ACCOUNTING.json','FINAL_DELIVERY_DISPOSITION.json','INSTRUCTION_IDENTITIES_FINAL.json','EVIDENCE_DELIVERY_RECEIPT.json','FULL_TEST_EXPECTED_FROZEN.tsv','FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv','FRONTEND_IDENTITIES.native.log','GATE_INVENTORY.json','FCV_STAGE2_INVENTORY.json','CI_EXTRA_INVENTORY.json','PROOF_GATE_INVENTORY.json','CHANGE_IMPACT.json','FULL_BACKEND.native.log','FULL_BACKEND.receipt.json','FRONTEND_BUILD.native.log','FCV_STOP.json']
(D/'inputs').mkdir(exist_ok=True)
for n in required:shutil.copyfile(P/n,D/'inputs'/n)
with zipfile.ZipFile(P/'REVIEW_PACKAGE.zip') as z:
 assert z.testzip() is None
 manifest=z.read('EXTERNAL_MANIFEST.sha256').decode().splitlines();assert len(z.namelist())==len(set(z.namelist()))==1181 and len(manifest)==1180
 for row in manifest:
  digest,name=row.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
put('PRIOR_EVIDENCE_VERIFICATION.json',{'zip_sha256':h(P/'REVIEW_PACKAGE.zip'),'archive_entries_checked':1181,'manifest_members_checked':1180,'new_readback':'CRC and every manifest member verified from prior ZIP; not independent acceptance','prior_native_counts':json.loads((P/'TEST_IDENTITY_ACCOUNTING.json').read_text())['FULL_BACKEND'],'frozen_scene_location':str(F),'registry_relation':'Independent prior repository, not linked canonical worktree. Found via preserved receipt and WRITE_SCOPE, not reconstructed.','branch_literal_rejected':'refs/heads/a gent/frontend-wave2-product-ux-v1','owner_corrected_ref':'refs/heads/agent/frontend-wave2-product-ux-v1'})
for n in ['backend','frontend']:
 dest=D/'sources'/n;assert not dest.exists();dest.parent.mkdir(exist_ok=True)
 subprocess.run(['git','clone','--no-local','--no-checkout',str(F/'.git'),str(dest)],env=ENV,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['git','-C',str(dest),'checkout','--detach',SHA],env=ENV,check=True,stdout=subprocess.DEVNULL)
 assert git(dest,'rev-parse','HEAD^{tree}').decode().strip()==TREE and not git(dest,'status','--porcelain')
 assert not (dest/'.git/objects/info/alternates').exists()
 for item in git(dest,'ls-tree','-rz',SHA).split(b'\0'):
  if not item:continue
  meta,name=item.split(b'\t',1);mode,kind,oid=meta.split();p=dest/os.fsdecode(name)
  if kind!=b'blob':continue
  raw=os.fsencode(os.readlink(p)) if mode==b'120000' else p.read_bytes()
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest().encode()==oid
sets={str(root):{(p.stat().st_dev,p.stat().st_ino) for p in (root/'.git/objects').rglob('*') if p.is_file()} for root in [R,F,D/'sources/backend',D/'sources/frontend']}
for x in ['backend','frontend']:
 k=str(D/'sources'/x)
 assert all(not (sets[k]&v) for n,v in sets.items() if n!=k)
for n in ['outputs','logs','receipts','fixtures','cache/gradle','cache/npm','cache/home','cache/xdg','tmp/backend','tmp/frontend']:(D/n).mkdir(parents=True,exist_ok=True)
put('CANDIDATE_IDENTITY.json',{'base':BASE,'commit':SHA,'tree':TREE,'product_source_changes':0,'product_commits_created':0,'repositories':{n:str(D/'sources'/n) for n in ['backend','frontend']},'failed_prior_checkout':str(F),'failed_prior_preserved':True,'alternates':0,'object_inode_intersections':0,'tracked_blob_validation':'All materialized tracked blob bytes match frozen tree','source':'Explicit immutable prior Git object database, not failed checkout filesystem inputs'})
inst=[R/'AGENTS.md',Path('/home/user/Documents/03-大模型上下文-精简版.md'),Path('/home/user/.hermes/skills/software-development/media-platform-worktree-registry-control/SKILL.md'),Path('/home/user/.hermes/skills/github/change-impact-ci-governance/SKILL.md'),Path('/home/user/.hermes/skills/software-development/test-driven-development/SKILL.md'),Path('/home/user/.hermes/skills/.usage.json'),Path('/home/user/.hermes/skills/.curator_ledger.jsonl')]
put('observations/INSTRUCTIONS_BEFORE.json',{'interval':'After initial reads and before harness qualification','files':[{'path':str(p),'sha256':h(p),'mtime_ns':p.stat().st_mtime_ns} for p in inst if p.is_file()],'no_contents_exported':True})
print('PREFLIGHT=PASS; prior failed scene preserved; two exact independent repositories materialized')
