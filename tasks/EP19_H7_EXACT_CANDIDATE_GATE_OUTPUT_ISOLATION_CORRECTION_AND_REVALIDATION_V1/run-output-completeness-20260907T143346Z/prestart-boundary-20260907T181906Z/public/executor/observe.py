"""Task-scoped local inotify observation; no PID attribution is inferred."""
from pathlib import Path
import ctypes,errno,hashlib,os,re,select,signal,stat,struct,subprocess,time
MASK=0x2|0x4|0x8|0x40|0x80|0x100|0x200|0x400|0x800

def snapshot(paths,expected_missing=()):
 from preservation import capture_files
 return capture_files(paths,expected_missing)


class Watch:
 def __init__(self,protected,repositories,metadata_roots,allowed,cross_lane=(),shared_git=None,shadow_root=None,shadow_declared=(),enumeration_roots=(),pruned_roots=(),expected_missing=(),frozen_roots=()):
  self.frozen_roots=list(map(Path,frozen_roots))
  self.protected=set(map(Path,protected));self.protected_ancestors={ancestor for p in self.protected for ancestor in p.parents};self.repositories=list(map(Path,repositories));self.metadata_roots=list(map(Path,metadata_roots));self.allowed=list(map(Path,allowed));self.cross_lane=list(map(Path,cross_lane));self.shared_git=Path(shared_git) if shared_git else None;self.shadow_root=Path(shadow_root) if shadow_root else None;self.shadow_conditional=({self.shadow_root/p for p in [*shadow_declared,'.git/index','.git/index.lock']} if self.shadow_root else set())
  self.expected_missing=set(map(str,expected_missing));self.enumeration_roots=list(map(Path,enumeration_roots));self.pruned_roots=list(map(Path,pruned_roots));self.shadow_declared=list(shadow_declared)
  self.libc=ctypes.CDLL(None,use_errno=True);self.fd=self.libc.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC)
  if self.fd<0:raise OSError(ctypes.get_errno(),'inotify_init1')
  self.watches={};self.watched_paths=set();self.events=[];self.errors=[];self.gaps=[];self.dynamic=0;self.metadata_files=set();self.metadata_dirs=set();self.shared_proof={}
  try:
   for root in self.metadata_roots:
    if root.resolve()!=root or not root.is_dir():raise RuntimeError('UNRESOLVED_METADATA_ROOT')
    dirs,files=self.add_tree(root);self.metadata_dirs.update(dirs);self.metadata_files.update(files)
   for p in self.protected:
    parent=p.parent
    while not parent.is_dir():parent=parent.parent
    self.add(parent)
   for root in [*self.repositories,*self.enumeration_roots]:self.add_tree(root,prune=True)
   ancestors={ancestor for root in [*self.repositories,*self.metadata_roots,*self.enumeration_roots,*self.protected] for ancestor in root.parents}
   for ancestor in sorted(ancestors):self.add(ancestor)
   self.capture_paths=(self.protected|{p for p in self.metadata_files if not self.within(p,self.cross_lane)})-self.shadow_conditional
   self.initial_directories={str(p):(p.stat().st_dev,p.stat().st_ino) for p in self.watches.values()}
  except BaseException:
   os.close(self.fd);raise
 @staticmethod
 def within(path,roots):return any(path==p or p in path.parents for p in roots)
 def add(self,path):
  if path.is_symlink():raise RuntimeError('SYMLINK_WATCH')
  if path in self.watched_paths:return
  from preservation import parent_fd,identity
  with parent_fd(path/'__sentinel__') as (pfd,unused):
   before=os.fstat(pfd)
   wd=self.libc.inotify_add_watch(self.fd,os.fsencode('/proc/self/fd/'+str(pfd)),MASK|0x01000000)
   if identity(before)!=identity(path.stat()):raise RuntimeError('WATCH_DIRECTORY_REPLACED')
  if wd<0:raise OSError(ctypes.get_errno(),'inotify_add_watch',str(path))
  self.watches[wd]=path;self.watched_paths.add(path)
 def add_tree(self,path,prune=False):
  from preservation import directory_inventory
  dirs,files=directory_inventory(path,[*self.allowed,*self.pruned_roots,*self.metadata_roots] if prune else [])
  for directory in dirs:self.add(directory)
  return dirs,files
 def classify(self,path,mask):
  if path in self.shadow_conditional:return 'SHADOW_INDEX_REFRESH_REQUIRES_SEMANTIC_RECONCILIATION' if path.parent==self.shadow_root/'.git' else 'SHADOW_DECLARED_CONTENT_REQUIRES_RESTORATION_PROOF'
  if self.within(path,self.cross_lane):return 'AUTHORIZED_CONCURRENT_FRONTEND_METADATA'
  if self.shared_git and path not in self.metadata_files and any(path==Path(str(ref)+'.lock') for ref in self.cross_lane if ref.is_relative_to(self.shared_git/'refs')):return 'PENDING_EXACT_FRONTEND_REF_LOCK'
  if self.shared_git and path.is_relative_to(self.shared_git/'objects'):
   rel=path.relative_to(self.shared_git/'objects').as_posix()
   if re.fullmatch(r'[0-9a-f]{2}(?:/(?:[0-9a-f]{38}|tmp_obj_.+))?',rel) and path not in self.metadata_files and path not in self.metadata_dirs:
    return 'PENDING_SHARED_OBJECT_SCOPE_PROOF'
  if self.within(path,self.enumeration_roots):return 'REJECT_INSTRUCTION_EVENT'
  if path in self.protected or self.within(path,self.frozen_roots):return 'REJECT_PROTECTED_INPUT_EVENT'
  if self.within(path,self.metadata_roots):return 'REJECT_GIT_METADATA_EVENT'
  if self.within(path,self.allowed):return 'DECLARED_BUILD_OUTPUT'
  if self.within(path,self.repositories):return 'REJECT_UNDECLARED_REPOSITORY_WRITE'
  if mask&MASK and path in self.protected_ancestors:return 'REJECT_PROTECTED_ANCESTOR_EVENT'
  return 'OUTSIDE_PROTECTED_PATH_INVENTORY'
 def drain(self):
  while True:
   try:data=os.read(self.fd,1024*1024)
   except BlockingIOError:return
   if not data:self.errors.append('WATCH_EOF');return
   offset=0
   while offset<len(data):
    if offset+16>len(data):self.errors.append('MALFORMED_EVENT');return
    wd,mask,cookie,n=struct.unpack_from('iIII',data,offset);offset+=16
    if offset+n>len(data):self.errors.append('MALFORMED_EVENT');return
    name=os.fsdecode(data[offset:offset+n].split(b'\0')[0]);offset+=n
    if mask&0x4000:self.errors.append('QUEUE_OVERFLOW');continue
    if mask&(0x8000|0x2000):self.errors.append('WATCH_LOSS')
    if wd not in self.watches:self.errors.append('UNKNOWN_WATCH');continue
    path=self.watches[wd]/name;category=self.classify(path,mask)
    if category not in ['DECLARED_BUILD_OUTPUT','OUTSIDE_PROTECTED_PATH_INVENTORY']:
     self.events.append({'path':str(path),'mask':mask,'cookie':cookie,'category':category,'observed_ns':time.monotonic_ns(),'writer':'NOT_ESTABLISHED'})
    if mask&0x40000000 and mask&(0x100|0x80) and self.within(path,[*self.metadata_roots,*self.repositories,*self.enumeration_roots]) and not self.within(path,[*self.allowed,*self.pruned_roots]):
     count=len(self.watches)
     try:self.add_tree(path)
     except (OSError,RuntimeError) as e:self.errors.append('DYNAMIC_WATCH_FAILED:'+type(e).__name__)
     self.dynamic+=len(self.watches)-count
     self.gaps.append({'path':str(path),'kind':'NEW_SUBTREE_PREWATCH_INTERVAL','category':category})
     if category.startswith('REJECT'):self.errors.append('PROTECTED_SUBTREE_PREWATCH_GAP')
 def resolve_frontend_locks(self):
  pending=[e for e in self.events if e['category']=='PENDING_EXACT_FRONTEND_REF_LOCK']
  for event in pending:
   lock=Path(event['path']);target=Path(str(lock)[:-5])
   paired=any(e['path']==str(target) and e['category']=='AUTHORIZED_CONCURRENT_FRONTEND_METADATA' for e in self.events)
   if lock.exists() or lock.is_symlink() or not paired:
    event['category']='REJECT_UNRESOLVED_FRONTEND_REF_LOCK'
   else:
    try:
     oid=target.read_text().strip()
     if target.is_symlink() or not re.fullmatch('[0-9a-f]{40}',oid):raise RuntimeError('INVALID_FRONTEND_REF')
     env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'}
     kind=subprocess.check_output(['git','--no-optional-locks','--git-dir='+str(self.shared_git),'cat-file','-t',oid],env=env).strip()
     if kind!=b'commit':raise RuntimeError('FRONTEND_REF_NOT_COMMIT')
     event.update(category='AUTHORIZED_EXACT_FRONTEND_REF_LOCK_COMPLETED',target=str(target),target_oid=oid,lock_final_absent=True,source='OWNER_FRONTEND_REF_CONFIRMATION.txt normal exact-ref development exception; transient lock paired with exact target update; no packed-refs exception')
    except Exception as error:event.update(category='REJECT_UNRESOLVED_FRONTEND_REF_LOCK',reason=str(error))
 def resolve_shared(self):
  import zlib
  pending=[e for e in self.events if e['category']=='PENDING_SHARED_OBJECT_SCOPE_PROOF']
  if not pending:return
  refs=[str(p.relative_to(self.shared_git)) for p in self.cross_lane if p.is_relative_to(self.shared_git/'refs/heads') and not str(p).endswith('.lock')]
  checked={};tips={}
  try:
   if not refs:raise RuntimeError('NO_AUTHORIZED_FRONTEND_REF')
   env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'};base=['git','--no-optional-locks','--git-dir='+str(self.shared_git)]
   for ref in refs:tips[ref]=subprocess.check_output(base+['rev-parse','--verify',ref],env=env).decode().strip()
   reachable={line.split(b' ',1)[0].decode() for line in subprocess.check_output(base+['rev-list','--objects',*tips.values()],env=env).splitlines()}
   for path in {Path(e['path']) for e in pending}:
    rel=path.relative_to(self.shared_git/'objects').as_posix()
    if re.fullmatch(r'[0-9a-f]{2}/[0-9a-f]{38}',rel):
     oid=rel.replace('/','')
     if path.is_symlink() or oid not in reachable:raise RuntimeError('NEW_OBJECT_NOT_BOUND_TO_AUTHORIZED_REF')
     raw=path.read_bytes();decoder=zlib.decompressobj();content=decoder.decompress(raw)+decoder.flush()
     if not decoder.eof or decoder.unused_data or hashlib.sha1(content).hexdigest()!=oid:raise RuntimeError('NEW_OBJECT_DIGEST_MISMATCH')
     checked[rel]=hashlib.sha256(raw).hexdigest()
   for e in pending:
    path=Path(e['path']);rel=path.relative_to(self.shared_git/'objects').as_posix();prefix=rel.split('/')[0]
    if rel not in checked:
     if not any(k.startswith(prefix+'/') for k in checked):raise RuntimeError('UNBOUND_NEW_OBJECT_DIRECTORY_OR_TEMP')
     if '/tmp_obj_' in rel and path.exists():raise RuntimeError('SHARED_TEMP_STILL_PRESENT')
   self.shared_proof={'authorized_ref_tips_observed':tips,'new_loose_objects_sha256':checked,'scope':'Authorized frontend-reachable new loose object append only after actual content/reachability checks. Existing metadata stays strict; writer NOT_ESTABLISHED; new-subtree observation gaps are not waived.'}
   for e in pending:e['category']='AUTHORIZED_FRONTEND_REACHABLE_NEW_OBJECT_APPEND_WRITER_UNKNOWN'
  except Exception as error:
   self.shared_proof={'error_type':type(error).__name__,'reason':str(error),'disposition':'REJECT_UNRESOLVED_SHARED_METADATA_SCOPE'}
   for e in pending:e['category']='REJECT_UNRESOLVED_SHARED_METADATA_SCOPE'
 def rejected(self):return bool(self.errors or any(e['category'].startswith('REJECT') for e in self.events))
 def close(self):os.close(self.fd)

def tagged_processes(tag):
 result=[]
 needle=('EP19_GATE_SCOPE='+tag).encode()
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   if p.stat().st_uid==os.getuid() and needle in (p/'environ').read_bytes().split(b'\0'):result.append(int(p.name))
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 return result

class ChildScope:
 """Process-local Linux subreaping; changes no uid, capability or access policy.

 Adopted descendants remain visible even if they unset tags, setsid, or chdir.
 The caller owns this serialized invocation; pre-existing children are excluded.
 """
 def __init__(self):
  self.libc=ctypes.CDLL(None,use_errno=True);old=ctypes.c_int()
  if self.libc.prctl(37,ctypes.byref(old),0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_GET_CHILD_SUBREAPER')
  self.old=old.value;self.prior=set(self.children());self.known={}
  if self.libc.prctl(36,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_SET_CHILD_SUBREAPER')
 @staticmethod
 def children():
  result=set()
  for thread in Path('/proc/self/task').iterdir():
   try:result.update(map(int,(thread/'children').read_text().split()))
   except FileNotFoundError:pass
  return result
 @staticmethod
 def birth(pid):
  try:return Path('/proc') .joinpath(str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
  except FileNotFoundError:return None
 def pending(self):
  result=[]
  for pid in self.children()-self.prior:
   born=self.birth(pid)
   if born is None:continue
   self.known.setdefault(pid,born)
   if self.known[pid]!=born:raise RuntimeError('OWNED_PID_REUSED')
   try:
    done,status=os.waitpid(pid,os.WNOHANG)
    if done:continue
   except ChildProcessError:continue
   result.append(pid)
  return result
 def close(self):
  if self.libc.prctl(36,self.old,0,0,0)!=0:raise OSError(ctypes.get_errno(),'RESTORE_PROCESS_SUBREAPER_MODE')

def run(argv,cwd,log,protected,repositories,metadata_roots,allowed,cross_lane=(),shared_git=None,env=None,timeout=2400,shadow_root=None,shadow_declared=(),enumeration_roots=(),pruned_roots=(),expected_missing=(),shadow_reconciler=None,frozen_roots=()):
 import uuid
 tag=uuid.uuid4().hex;env=dict(os.environ if env is None else env)
 if 'GIT_INDEX_FILE' in env:raise RuntimeError('ALTERNATE_INDEX_FORBIDDEN')
 env.update(EP19_GATE_SCOPE=tag,GIT_OPTIONAL_LOCKS='0')
 started=time.time();watcher=Watch(protected,repositories,metadata_roots,allowed,cross_lane,shared_git,shadow_root,shadow_declared,enumeration_roots,pruned_roots,expected_missing,frozen_roots)
 children=ChildScope()
 try:
  before=snapshot(watcher.capture_paths,watcher.expected_missing);watcher.drain()
  if watcher.rejected():raise RuntimeError('PRESERVATION_REJECT_BEFORE_CHILD')
  ready=time.time();timed_out=False
  with Path(log).open('xb') as f:
   child=subprocess.Popen(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   while child.poll() is None:
    if select.select([watcher.fd],[],[],.025)[0]:watcher.drain()
    if watcher.rejected() or time.time()-ready>timeout:
     timed_out=time.time()-ready>timeout
     try:os.killpg(child.pid,signal.SIGTERM)
     except ProcessLookupError:pass
     try:child.wait(timeout=3)
     except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL)
     break
   rc=child.wait();watcher.drain();quiescence_start=time.time();terminated=[]
   while True:
    pending=sorted(set(tagged_processes(tag))|set(children.pending()))
    if not pending:break
    watcher.drain()
    if watcher.rejected() or time.time()-quiescence_start>10:
     watcher.errors.append('OWNED_DESCENDANT_REQUIRED_TERMINATION')
     for pid in pending:
      try:os.kill(pid,signal.SIGKILL);terminated.append(pid)
      except ProcessLookupError:pass
    if time.time()-quiescence_start>15:watcher.errors.append('OWNED_PROCESS_NOT_QUIESCENT');break
    select.select([watcher.fd],[],[],.05);watcher.drain()
   watcher.resolve_frontend_locks();watcher.resolve_shared();after=snapshot(watcher.capture_paths,watcher.expected_missing);watcher.drain()
   if any(e['category'].startswith('PENDING_') for e in watcher.events):watcher.errors.append('LATE_SHARED_SCOPE_UNRESOLVED')
  changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
  for p,wanted in watcher.initial_directories.items():
   try:
    s=Path(p).stat()
    if (s.st_dev,s.st_ino)!=wanted:watcher.errors.append('DIRECTORY_REPLACED '+p)
   except OSError:watcher.errors.append('DIRECTORY_MISSING '+p)
  reconciliation=None
  if shadow_root:
   try:
    if shadow_reconciler is None:raise RuntimeError('MISSING_BOUND_SHADOW_RECONCILIATION')
    reconciliation=shadow_reconciler(watcher.events,tag)
    require_shadow_reconciliation(reconciliation,shadow_root,tag,shadow_declared)
   except Exception as error:watcher.errors.append('SHADOW_ACCEPTANCE:'+str(error))
  rejected=bool(rc or changed or timed_out or watcher.rejected())
  return {'shadow_reconciliation':reconciliation,'result':'REJECT' if rejected else 'PASS_BOUNDED_OBSERVATION','native_exit':rc,'wrapper_exit':1 if rejected else 0,'before':before,'after':after,'changed':changed,'events':watcher.events,'shared_metadata_scope_proof':watcher.shared_proof,'observation_errors':watcher.errors,'gaps':watcher.gaps,'dynamic_watches':watcher.dynamic,'registered_watches':len(watcher.watches),'ready_before_child':True,'final_queue_drained':True,'child_pid':child.pid,'gate_process_scope':tag,'child_containment':'Linux process-local subreaper plus tag observation; private PID namespace additionally enforced for frontend','owned_processes_remaining':pending,'owned_processes_terminated':terminated,'quiescence_seconds':time.time()-quiescence_start,'start':started,'ready':ready,'end':time.time(),'timeout':timed_out,'command':argv,'cwd':str(cwd),'scope_limits':'Local inotify plus captured endpoint fields, no universal mmap/network/attribute coverage or writer PID attribution; per-command interval only. Only the exact authorized frontend ref/worktree metadata exception applies. New shared loose objects require actual content/reachability checks against the exact authorized frontend ref; unresolved checks reject; no restoration or writer attribution.'}
 finally:
  children.close();watcher.close()


def require_shadow_reconciliation(proof,root,tag,declared):
 if not isinstance(proof,dict) or proof.get('run_binding')!=tag or proof.get('root')!=str(root):raise RuntimeError('MISSING_OR_UNBOUND_RECONCILIATION')
 if proof.get('result')!='PASS' or proof.get('semantic_check',{}).get('result')!='PASS':raise RuntimeError('SHADOW_SEMANTIC_NOT_PASS')
 content=proof.get('final_content_check',{})
 if content.get('result')!='PASS' or content.get('checked',0)<=0 or content.get('mismatches')!=[]:raise RuntimeError('SHADOW_FINAL_CONTENT_NOT_PASS')
 for key in ['before_sha256','after_sha256','events_sha256','final_content_sha256']:
  if not re.fullmatch('[0-9a-f]{64}',proof.get(key,'')):raise RuntimeError('MISSING_RECONCILIATION_EVIDENCE '+key)

 import json
 from frozen_shadow_monitor import reconcile
 evidence=proof.get('evidence',{})
 for name,key in [('before','before_sha256'),('after','after_sha256'),('events','events_sha256'),('final_content','final_content_sha256')]:
  if name not in evidence or hashlib.sha256(json.dumps(evidence[name],sort_keys=True).encode()).hexdigest()!=proof[key]:raise RuntimeError('RECONCILIATION_EVIDENCE_DIGEST_MISMATCH')
 if evidence['final_content']!=content or content['checked']!=len(evidence['before']['entries']):raise RuntimeError('INCOMPLETE_BOUND_FINAL_CONTENT')
 actual=reconcile('SHADOW',evidence['before'],evidence['after'],evidence['events'],declared,content['mismatches'])
 if actual!=proof['semantic_check'] or actual['result']!='PASS':raise RuntimeError('BOUND_SHADOW_REDUCER_MISMATCH')
