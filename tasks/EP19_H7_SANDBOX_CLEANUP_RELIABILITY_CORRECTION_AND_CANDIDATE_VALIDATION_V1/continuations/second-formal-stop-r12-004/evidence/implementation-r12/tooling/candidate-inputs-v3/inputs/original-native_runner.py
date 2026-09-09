from control import *
import ctypes,struct,select,signal
from shadow_monitor import snapshot as git_snapshot,classify_event,reconcile
DECLARED={'typed-schema-module/jooq-baseline.properties','typed-schema-module/jooq-plain-sql-allowlist.txt','typed-schema-module/jooq-dynamic-identifier-allowlist.txt'}
def run(cid,name,cmd,shadow=False,allow_failure=False):
 assert not (A/'STOP.json').exists(),'STOP_ALREADY_SET';assert not (A/(name+'.receipt.json')).exists(),'NO_RETRY'
 inv={r['command_id']:r for r in csv.DictReader((A/'FCV_COMMAND_INVENTORY.tsv').open(),delimiter='\t')};assert cid in inv;assert h(A/'FCV_COMMAND_INVENTORY.tsv')==load('COMMAND_INVENTORY_SEAL.json')['sha256']
 root=SHADOW if shadow else X;before=checked_manifest(root,name+'.pre.tsv');assert all(r['matches_git_blob'] for r in before);index=h(root/'.git/index');paths={r['path'] for r in before};scope='SHADOW' if shadow else 'PRIMARY';git_before=git_snapshot(root,ENV);j(name+'.git-before.json',git_before)
 libc=ctypes.CDLL(None,use_errno=True);fd=libc.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC);assert fd>=0;watch={}
 for d in {str(q) for p in paths for q in (root/p).parents if q==root or root in q.parents}|{str(root/'.git')}|{str(p) for p in (root/'.git').rglob('*') if p.is_dir()}:
  wd=libc.inotify_add_watch(fd,d.encode(),0x2|0x4|0x8|0x40|0x80|0x100|0x200|0x400|0x800);assert wd>=0;watch[wd]=Path(d)
 record(cid,cmd,'NATIVE_GATE');events=[];bad=[];start=time.time();j('CURRENT_STAGE.json',{'command_id':cid,'name':name,'start':start})
 with (A/name).open('wb') as out:
  p=S.Popen(cmd,cwd=root,env=ENV,stdout=out,stderr=S.STDOUT,start_new_session=True)
  while True:
   if select.select([fd],[],[],.1)[0]:
    data=os.read(fd,1024*1024);off=0
    while off<len(data):
     wd,mask,cookie,n=struct.unpack_from('iIII',data,off);off+=16;fname=data[off:off+n].split(b'\0')[0];off+=n
     if mask&0x4000:bad.append('INOTIFY_QUEUE_OVERFLOW');continue
     if wd not in watch:continue
     rel=str((watch[wd]/os.fsdecode(fname)).relative_to(root));affected=([rel] if rel.startswith('.git/') else [])+[x for x in paths if x==rel or ((mask&0x40000000) and x.startswith(rel+'/'))]
     for path in affected:
      events.append({'path':path,'mask':mask,'epoch':time.time(),'workspace_scope':scope,'category':classify_event(scope,path,DECLARED)})
      if classify_event(scope,path,DECLARED) not in ['SHADOW_DECLARED_TRACKED_CONTENT_WRITE','SHADOW_GIT_INDEX_METADATA_REFRESH']:bad.append(path)
    if bad and p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
   if p.poll() is not None:break
  rc=p.wait()
 os.close(fd);after=checked_manifest(root,name+'.post.tsv');mismatch=[r['path'] for r in after if not r['matches_git_blob']]
 git_after=git_snapshot(root,ENV);j(name+'.git-after.json',git_after)
 integrity=reconcile(scope,git_before,git_after,events,DECLARED,mismatch)
 ok=rc==0 and not bad and not mismatch and integrity['result']=='PASS'
 if shadow:
  def entries_file(n,entries):
   with (A/n).open('w') as out:
    w=csv.DictWriter(out,['path','mode','blob','stage'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(entries)
  entries_file('SHADOW_INDEX_ENTRIES_BEFORE.tsv',git_before['entries']);entries_file('SHADOW_INDEX_ENTRIES_AFTER.tsv',git_after['entries'])
  j('SHADOW_INDEX_INTEGRITY.json',{'SHADOW_INDEX_BYTE_SHA256_BEFORE':git_before['index_byte_sha256'],'SHADOW_INDEX_BYTE_SHA256_AFTER':git_after['index_byte_sha256'],'SHADOW_INDEX_BYTE_CHANGED':'YES' if integrity['index_byte_changed'] else 'NO','SHADOW_INDEX_SEMANTIC_SHA256_BEFORE':git_before['index_semantic_sha256'],'SHADOW_INDEX_SEMANTIC_SHA256_AFTER':git_after['index_semantic_sha256'],'SHADOW_INDEX_SEMANTIC_CHANGED':'YES' if integrity['index_semantic_changed'] else 'NO','SHADOW_INDEX_SEMANTIC_MUTATION_COUNT':int(integrity['index_semantic_changed']),'SHADOW_STAGED_PATH_ADDED_COUNT':integrity['staged_added'],'SHADOW_STAGED_PATH_REMOVED_COUNT':integrity['staged_removed'],'SHADOW_STAGED_PATH_CHANGED_COUNT':integrity['staged_changed'],'SHADOW_STAGE_ENTRY_MODE_CHANGED_COUNT':integrity['mode_changed'],'SHADOW_STAGE_ENTRY_BLOB_CHANGED_COUNT':integrity['blob_changed'],'SHADOW_INDEX_BYTE_CHANGE_CLASSIFICATION':integrity['index_byte_change_classification'],'SHADOW_GIT_OPTIONAL_LOCKS':ENV.get('GIT_OPTIONAL_LOCKS'),'SHADOW_ALTERNATE_INDEX_USED':'NO','SHADOW_GIT_INDEX_BYTE_IMMUTABILITY_REQUIRED':'NO','SHADOW_GIT_INDEX_SEMANTIC_IMMUTABILITY_REQUIRED':'YES'})
  for n,v in [('BEFORE',git_before),('AFTER',git_after)]:j('SHADOW_HEAD_REF_'+n+'.json',{k:v[k] for k in ['head','head_state','refs','ref_set_digest']})
  j('SHADOW_HEAD_REF_INTEGRITY.json',{'SHADOW_HEAD_BEFORE':git_before['head'],'SHADOW_HEAD_AFTER':git_after['head'],'head_state_before':git_before['head_state'],'head_state_after':git_after['head_state'],'ref_set_digest_before':git_before['ref_set_digest'],'ref_set_digest_after':git_after['ref_set_digest'],'changed_refs':sorted(set(git_before['refs'].splitlines())^set(git_after['refs'].splitlines())),'SHADOW_HEAD_MUTATION_COUNT':int(integrity['head_changed']),'SHADOW_REF_MUTATION_COUNT':int(integrity['refs_changed'])})
  passes=sum(line.startswith('PASS: ') and 'rejects missing authority' in line for line in (A/name).read_text().splitlines());ok=ok and passes==3
  integrity.update(S01_EXIT_CODE=rc,S01_EXPECTED_NEGATIVE_CASE_COUNT=3,S01_EXPECTED_NEGATIVE_CASE_PASS_COUNT=passes,S01_RESULT='PASS' if ok else 'FAIL',SHADOW_DECLARED_AUTHORITY_PATH_COUNT=3,SHADOW_DECLARED_TRACKED_CONTENT_WRITE_EVENT_COUNT=sum(e['category']=='SHADOW_DECLARED_TRACKED_CONTENT_WRITE' for e in events),SHADOW_UNDECLARED_TRACKED_CONTENT_WRITE_COUNT=sum(e['category']=='SHADOW_UNDECLARED_TRACKED_CONTENT_WRITE' for e in events),SHADOW_GIT_METADATA_EVENT_COUNT=sum(e['path'].startswith('.git/') for e in events),SHADOW_GIT_INDEX_METADATA_REFRESH_COUNT=integrity['metadata_refresh_count'])
  for ix,path in enumerate(sorted(DECLARED),1):integrity['SHADOW_CONTROLLED_PATH_'+str(ix)+'_FINAL_BYTES_EQUAL_CANDIDATE']='YES' if path not in mismatch else 'NO'
 elif integrity['result']!='PASS':ok=False
 rec={'command_id':cid,'command':cmd,'workspace':str(root),'shadow':shadow,'workspace_scope':scope,'scope_integrity':integrity,'write_events':events,'primary_git_index_byte_mutation_count':int(not shadow and integrity['index_byte_changed']),'primary_head_mutation_count':int(not shadow and integrity['head_changed']),'primary_ref_mutation_count':int(not shadow and integrity['refs_changed']),'outer_sandbox_used':False,'host_native':True,'start':start,'end':time.time(),'duration_seconds':time.time()-start,'exit_code':rc,'tracked_write_events':[e for e in events if not e['path'].startswith('.git/')],'undeclared_write_events':bad,'final_tracked_mismatches':mismatch,'index_before':index,'index_after':h(root/'.git/index'),'retry_count':0,'result':'PASS' if ok else 'FAIL'};j(name+'.receipt.json',rec)
 if not ok and (not allow_failure or bad or mismatch or integrity['result']!='PASS'):j('STOP.json',{'gate':name,'workspace_scope':scope,'result':'FAIL_HARNESS' if integrity['result']!='PASS' or bad or mismatch else 'FAIL_CANDIDATE_CONTROL_BEHAVIOR' if shadow else 'FAIL','reason':integrity['stop_reason'] if integrity['stop_reason']!='NONE' else scope+'_MONITOR_QUEUE_OVERFLOW' if bad else 'SHADOW_CONTROL_BEHAVIOR_FAILURE' if shadow else 'PRIMARY_COMMAND_FAILURE','time':time.time()})
 if cid=='P01':j('ENVIRONMENT_PREFLIGHT_SUMMARY.json',{'GRADLE_ENVIRONMENT_PREFLIGHT':rec['result'],'GRADLE_CONFIGURATION_RESULT':rec['result'],'REMOTE_RENDER_WORKER_PROJECT_DIRECTORY_WRITABLE':'YES','PREFLIGHT_TRACKED_WRITE_EVENT_COUNT':len(events)})
 if cid=='P02':
  dest=A/'runtime-preflight-xml';dest.mkdir(exist_ok=True)
  for f in root.glob('sandbox-isolation-module/build/test-results/test/TEST-*.xml'):shutil.copyfile(f,dest/f.name)
 if cid=='F02':
  dest=A/'full-run-xml';dest.mkdir(exist_ok=True)
  for f in root.glob('**/build/test-results/*/TEST-*.xml'):
   if f.stat().st_mtime<start:continue
   target=dest/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 if cid=='C01' and rc==0:j('CHANGE_IMPACT_CLASSIFIER.json',json.loads((A/name).read_text()))
 completed(cid,rec['result'])
 print(json.dumps({'gate':name,'result':rec['result'],'exit_code':rc,'duration_seconds':rec['duration_seconds'],'tracked_events':len(events)}),flush=True)
 return ok
