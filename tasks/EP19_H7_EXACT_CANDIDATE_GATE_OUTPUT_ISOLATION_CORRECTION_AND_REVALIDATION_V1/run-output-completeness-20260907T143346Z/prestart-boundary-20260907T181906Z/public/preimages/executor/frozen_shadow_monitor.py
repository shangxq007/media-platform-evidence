from pathlib import Path
import hashlib,subprocess,os

def digest(b):return hashlib.sha256(b).hexdigest()
def snapshot(root,env):
 def git(*args):return subprocess.check_output(['git','-C',str(root),*args],env=env)
 raw=git('ls-files','--stage','-z');entries=[]
 for item in raw.split(b'\0'):
  if not item:continue
  meta,path=item.split(b'\t',1);mode,blob,stage=meta.decode().split();entries.append({'path':os.fsdecode(path),'mode':mode,'blob':blob,'stage':stage})
 refs=git('for-each-ref','--format=%(refname) %(objectname)').decode()
 head=(root/'.git/HEAD').read_text()
 return {'index_byte_sha256':digest((root/'.git/index').read_bytes()),'index_semantic_sha256':digest(raw),'entries':entries,'head':git('rev-parse','HEAD').decode().strip(),'head_state':head,'refs':refs,'ref_set_digest':digest(refs.encode())}

def classify_event(scope,path,declared):
 if scope=='PRIMARY':return 'PRIMARY_GIT_METADATA_WRITE' if path.startswith('.git/') else 'PRIMARY_TRACKED_CONTENT_WRITE'
 if path in ['.git/index','.git/index.lock']:return 'SHADOW_GIT_INDEX_METADATA_REFRESH'
 if path in ['.git/HEAD','.git/HEAD.lock']:return 'SHADOW_HEAD_MUTATION'
 if path.startswith(('.git/refs/','.git/logs/refs/')) or path in ['.git/packed-refs','.git/packed-refs.lock']:return 'SHADOW_REF_MUTATION'
 if path.startswith('.git/'):return 'SHADOW_UNCLASSIFIED_GIT_METADATA_WRITE'
 return 'SHADOW_DECLARED_TRACKED_CONTENT_WRITE' if path in declared else 'SHADOW_UNDECLARED_TRACKED_CONTENT_WRITE'

def reconcile(scope,before,after,events,declared,dirty):
 b={(r['path'],r['stage']):r for r in before['entries']};a={(r['path'],r['stage']):r for r in after['entries']}
 added=set(a)-set(b);removed=set(b)-set(a);changed={k for k in set(a)&set(b) if a[k]!=b[k]}
 sem=before['index_semantic_sha256']!=after['index_semantic_sha256'];byt=before['index_byte_sha256']!=after['index_byte_sha256'];head=before['head']!=after['head'] or before['head_state']!=after['head_state'];refs=before['refs']!=after['refs']
 classified=[dict(e,workspace_scope=scope,category=classify_event(scope,e['path'],declared)) for e in events]
 cats={e['category'] for e in classified};reason='NONE'
 if scope=='PRIMARY':
  if byt or head or refs or 'PRIMARY_GIT_METADATA_WRITE' in cats:reason='PRIMARY_GIT_METADATA_MUTATION'
  elif dirty or 'PRIMARY_TRACKED_CONTENT_WRITE' in cats:reason='PRIMARY_TRACKED_CONTENT_WRITE'
 else:
  if sem:reason='SHADOW_INDEX_SEMANTIC_MUTATION'
  elif head or 'SHADOW_HEAD_MUTATION' in cats:reason='SHADOW_HEAD_MUTATION'
  elif refs or 'SHADOW_REF_MUTATION' in cats:reason='SHADOW_REF_MUTATION'
  elif 'SHADOW_UNDECLARED_TRACKED_CONTENT_WRITE' in cats:reason='SHADOW_UNDECLARED_TRACKED_CONTENT_WRITE'
  elif 'SHADOW_UNCLASSIFIED_GIT_METADATA_WRITE' in cats:reason='SHADOW_GIT_METADATA_UNCLASSIFIED'
  elif dirty:reason='SHADOW_FINAL_TRACKED_CONTENT_MISMATCH'
 return {'workspace_scope':scope,'result':'PASS' if reason=='NONE' else 'FAIL_'+reason,'stop_reason':reason,'events':classified,'index_byte_changed':byt,'index_semantic_changed':sem,'head_changed':head,'refs_changed':refs,'staged_added':len(added),'staged_removed':len(removed),'staged_changed':len(changed),'mode_changed':sum(a[k]['mode']!=b[k]['mode'] for k in changed),'blob_changed':sum(a[k]['blob']!=b[k]['blob'] for k in changed),'metadata_refresh_count':sum(e['category']=='SHADOW_GIT_INDEX_METADATA_REFRESH' for e in classified) if not sem and not head and not refs else 0,'index_byte_change_classification':'SEMANTIC_INDEX_MUTATION' if sem else 'NON_SEMANTIC_GIT_METADATA_REFRESH' if byt else 'NO_BYTE_CHANGE'}
