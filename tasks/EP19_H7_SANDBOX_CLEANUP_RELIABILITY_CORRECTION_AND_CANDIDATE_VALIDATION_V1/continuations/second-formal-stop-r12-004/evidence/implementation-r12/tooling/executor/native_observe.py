"""Task-scoped local inotify observation; no PID attribution is inferred."""
from pathlib import Path
import ctypes,errno,hashlib,json,os,re,select,signal,stat,struct,subprocess,time
import bookkeeping_v2
import bookkeeping_v3
import capture as bounded_capture
import durability
import causal
MASK=0x2|0x4|0x8|0x40|0x80|0x100|0x200|0x400|0x800

def snapshot(paths,expected_missing=()):
 from preservation import capture_files
 return capture_files(paths,expected_missing)


class Watch:
 def __init__(self,protected,repositories,metadata_roots,allowed,cross_lane=(),shared_git=None,shadow_root=None,shadow_declared=(),enumeration_roots=(),pruned_roots=(),expected_missing=(),frozen_roots=(),bookkeeping_policy=None):
  self.frozen_roots=list(map(Path,frozen_roots))
  self.protected=set(map(Path,protected));self.protected_ancestors={ancestor for p in self.protected for ancestor in p.parents};self.repositories=list(map(Path,repositories));self.metadata_roots=list(map(Path,metadata_roots));self.allowed=list(map(Path,allowed));self.cross_lane=list(map(Path,cross_lane));self.shared_git=Path(shared_git) if shared_git else None;self.shadow_root=Path(shadow_root) if shadow_root else None;self.shadow_conditional=({self.shadow_root/p for p in [*shadow_declared,'.git/index','.git/index.lock']} if self.shadow_root else set())
  self.expected_missing=set(map(str,expected_missing));self.enumeration_roots=list(map(Path,enumeration_roots));self.pruned_roots=list(map(Path,pruned_roots));self.shadow_declared=list(shadow_declared)
  self.bookkeeping_policy=(json.loads(Path(bookkeeping_policy).read_text()) if isinstance(bookkeeping_policy,(str,Path)) else bookkeeping_policy)
  self.bookkeeping_v3=bool(self.bookkeeping_policy and self.bookkeeping_policy.get('schema')==bookkeeping_v3.SCHEMA)
  self.bookkeeping_target=(Path(self.bookkeeping_policy['paths']['usage']) if self.bookkeeping_v3 else Path(self.bookkeeping_policy['target'])) if self.bookkeeping_policy else None
  self.bookkeeping_root=(Path(self.bookkeeping_policy['root']) if self.bookkeeping_v3 else Path(self.bookkeeping_policy['skills_root'])) if self.bookkeeping_policy else None
  self.bookkeeping_paths=(set(map(Path,self.bookkeeping_policy['paths'].values())) if self.bookkeeping_v3 else {self.bookkeeping_target} if self.bookkeeping_policy else set())
  self.bookkeeping_limits=[]
  self.initial_acquisition_deadline=time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  self.libc=ctypes.CDLL(None,use_errno=True);self.fd=bounded_capture.guarded_call(self.initial_acquisition_deadline,self.libc.inotify_init1,os.O_NONBLOCK|os.O_CLOEXEC)
  if self.fd<0:raise OSError(ctypes.get_errno(),'inotify_init1')
  self.watches={};self.watched_paths=set();self.events=[];self.errors=[];self.gaps=[];self.dynamic=0;self.metadata_files=set();self.metadata_dirs=set();self.shared_proof={};self.closed=False;self.shutdown_wds=set()
  try:
   for root in self.metadata_roots:
    if bounded_capture.guarded_call(self.initial_acquisition_deadline,Path.resolve,root)!=root or not stat.S_ISDIR(bounded_capture.guarded_call(self.initial_acquisition_deadline,os.stat,root).st_mode):raise RuntimeError('UNRESOLVED_METADATA_ROOT')
    dirs,files=self.add_tree(root,deadline=self.initial_acquisition_deadline);self.metadata_dirs.update(dirs);self.metadata_files.update(files)
   for p in self.protected:
    parent=p.parent
    while not stat.S_ISDIR(bounded_capture.guarded_call(self.initial_acquisition_deadline,os.stat,parent).st_mode):parent=parent.parent
    self.add(parent,deadline=self.initial_acquisition_deadline)
   for root in [*self.repositories,*self.enumeration_roots]:self.add_tree(root,prune=True,deadline=self.initial_acquisition_deadline)
   ancestors={ancestor for root in [*self.repositories,*self.metadata_roots,*self.enumeration_roots,*self.protected] for ancestor in root.parents}
   for ancestor in sorted(ancestors):self.add(ancestor,deadline=self.initial_acquisition_deadline)
   self.capture_paths=(self.protected|{p for p in self.metadata_files if not self.within(p,self.cross_lane)})-self.shadow_conditional
   from preservation import identity
   self.initial_directories={str(p):identity(bounded_capture.guarded_call(self.initial_acquisition_deadline,os.stat,p)) for p in self.watches.values()}
  except BaseException as original:
   try:os.close(self.fd)
   except BaseException as cleanup:
    raise BaseExceptionGroup('WATCH_CONSTRUCTOR_PRIMARY_AND_CLEANUP_FAILURE',[original,cleanup]) from None
   raise
 @staticmethod
 def within(path,roots):return any(path==p or p in path.parents for p in roots)
 def add(self,path,deadline=None):
  deadline=deadline or time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  mode=bounded_capture.guarded_call(deadline,os.lstat,path).st_mode
  if stat.S_ISLNK(mode):raise RuntimeError('SYMLINK_WATCH')
  if path in self.watched_paths:return
  from preservation import parent_fd,identity
  with bounded_capture._deadline_guard(bounded_capture._remaining(deadline)):
   with parent_fd(path/'__sentinel__') as (pfd,unused):
    before=os.fstat(pfd)
    wd=self.libc.inotify_add_watch(self.fd,os.fsencode('/proc/self/fd/'+str(pfd)),MASK|0x01000000)
    if identity(before)!=identity(os.stat(path)):raise RuntimeError('WATCH_DIRECTORY_REPLACED')
  if wd<0:raise OSError(ctypes.get_errno(),'inotify_add_watch',str(path))
  self.watches[wd]=path;self.watched_paths.add(path)
 def add_tree(self,path,prune=False,deadline=None):
  from preservation import directory_inventory
  deadline=deadline or time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  dirs,files=directory_inventory(path,[*self.allowed,*self.pruned_roots,*self.metadata_roots] if prune else [],deadline=deadline)
  for directory in dirs:self.add(directory,deadline=deadline)
  return dirs,files
 def classify(self,path,mask):
  if self.bookkeeping_v3 and (path in self.bookkeeping_paths or (path.parent==self.bookkeeping_root and bookkeeping_v3.TEMP_RE.fullmatch(path.name))):
   return 'DELEGATED_TO_CONTINUOUS_V3_OBSERVER'
  if path in self.shadow_conditional:return 'SHADOW_INDEX_REFRESH_REQUIRES_SEMANTIC_RECONCILIATION' if path.parent==self.shadow_root/'.git' else 'SHADOW_DECLARED_CONTENT_REQUIRES_RESTORATION_PROOF'
  if self.within(path,self.cross_lane):return 'AUTHORIZED_CONCURRENT_FRONTEND_METADATA'
  if self.shared_git and path not in self.metadata_files and any(path==Path(str(ref)+'.lock') for ref in self.cross_lane if ref.is_relative_to(self.shared_git/'refs')):return 'PENDING_EXACT_FRONTEND_REF_LOCK'
  if self.shared_git and path.is_relative_to(self.shared_git/'objects'):
   rel=path.relative_to(self.shared_git/'objects').as_posix()
   if re.fullmatch(r'[0-9a-f]{2}(?:/(?:[0-9a-f]{38}|tmp_obj_.+))?',rel) and path not in self.metadata_files and path not in self.metadata_dirs:
    return 'PENDING_SHARED_OBJECT_SCOPE_PROOF'
  if self.bookkeeping_policy and path==self.bookkeeping_target:
   if mask&0x4:return 'REJECT_BOOKKEEPING_TARGET_ATTRIBUTE_EVENT'
   if mask&0x40:return 'REJECT_BOOKKEEPING_TARGET_MOVED_OUT'
   return 'SCOPED_BOOKKEEPING_EVENT_PENDING_FINAL_EVALUATION'
  if self.bookkeeping_policy and bookkeeping_v2.is_reserved_temp(path,self.bookkeeping_root):
   return 'SCOPED_BOOKKEEPING_EVENT_PENDING_FINAL_EVALUATION'
  if self.within(path,self.enumeration_roots):return 'REJECT_INSTRUCTION_EVENT'
  if path in self.protected or self.within(path,self.frozen_roots):return 'REJECT_PROTECTED_INPUT_EVENT'
  if self.within(path,self.metadata_roots):return 'REJECT_GIT_METADATA_EVENT'
  if self.within(path,self.allowed):return 'DECLARED_BUILD_OUTPUT'
  if self.within(path,self.repositories):return 'REJECT_UNDECLARED_REPOSITORY_WRITE'
  if mask&MASK and path in self.protected_ancestors:return 'REJECT_PROTECTED_ANCESTOR_EVENT'
  return 'OUTSIDE_PROTECTED_PATH_INVENTORY'
 def drain(self,deadline=None):
  deadline=deadline or time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  while True:
   if time.monotonic()>=deadline:self.errors.append('EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED');return
   try:data=bounded_capture.guarded_call(deadline,os.read,self.fd,1024*1024)
   except BlockingIOError:return
   except bounded_capture.CaptureError:self.errors.append('EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED');return
   if not data:self.errors.append('WATCH_EOF');return
   offset=0
   while offset<len(data):
    if time.monotonic()>=deadline:self.errors.append('EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED');return
    if offset+16>len(data):self.errors.append('MALFORMED_EVENT');return
    wd,mask,cookie,n=struct.unpack_from('iIII',data,offset);offset+=16
    if offset+n>len(data):self.errors.append('MALFORMED_EVENT');return
    name=os.fsdecode(data[offset:offset+n].split(b'\0')[0]);offset+=n
    if mask&0x4000:self.errors.append('QUEUE_OVERFLOW');continue
    if mask&0x8000 and wd in self.shutdown_wds:
     self.shutdown_wds.discard(wd);self.watches.pop(wd,None);continue
    if mask&(0x8000|0x2000):self.errors.append('WATCH_LOSS')
    if wd not in self.watches:self.errors.append('UNKNOWN_WATCH');continue
    path=self.watches[wd]/name;category=self.classify(path,mask)
    if category=='SCOPED_BOOKKEEPING_EVENT_PENDING_FINAL_EVALUATION' and path!=self.bookkeeping_target:
     try:
      s=bounded_capture.guarded_call(deadline,os.lstat,path)
      if stat.S_ISLNK(s.st_mode) or not stat.S_ISREG(s.st_mode) or s.st_nlink!=1:
       category='REJECT_BOOKKEEPING_TEMP_LINK_OR_TYPE'
      elif s.st_dev!=self.bookkeeping_policy['baseline_root']['metadata']['st_dev']:
       category='REJECT_BOOKKEEPING_TEMP_FILESYSTEM_BOUNDARY'
      elif s.st_uid!=self.bookkeeping_policy['baseline_usage_metadata']['st_uid'] or s.st_gid!=self.bookkeeping_policy['baseline_usage_metadata']['st_gid'] or stat.S_IMODE(s.st_mode)!=0o600:
       category='REJECT_BOOKKEEPING_TEMP_OWNER_GROUP_MODE'
     except FileNotFoundError:
      self.bookkeeping_limits.append({'path':str(path),'kind':'SHORT_LIVED_TEMP_DETAILS_UNAVAILABLE','disposition':'OBSERVATIONAL_LIMIT_ONLY_FINAL_STATE_STILL_REQUIRED'})
     except bounded_capture.CaptureError:
      category='REJECT_BOOKKEEPING_TEMP_CAPTURE_TIMEOUT';self.errors.append(category)
     except OSError as e:
      category='REJECT_BOOKKEEPING_TEMP_CAPTURE_ERROR';self.errors.append(category+':'+type(e).__name__+':'+str(getattr(e,'errno',None)))
    if category not in ['DECLARED_BUILD_OUTPUT','OUTSIDE_PROTECTED_PATH_INVENTORY']:
     if len(self.events)>=bookkeeping_v3.LIMITS['pending_events_max']:
      self.errors.append('PENDING_EVENT_LIMIT_EXCEEDED_DURING_ACQUISITION');return
     self.events.append({'path':str(path),'mask':mask,'cookie':cookie,'category':category,'observed_ns':time.monotonic_ns(),'writer':'NOT_ESTABLISHED'})
    if mask&0x40000000 and mask&(0x100|0x80) and self.within(path,[*self.metadata_roots,*self.repositories,*self.enumeration_roots]) and not self.within(path,[*self.allowed,*self.pruned_roots]):
     count=len(self.watches)
     if category.startswith('REJECT'):
      self.gaps.append({'path':str(path),'kind':'NEW_SUBTREE_NOT_SCANNED_AFTER_FAIL_CLOSED_CLASSIFICATION','category':category})
      self.errors.append('PROTECTED_SUBTREE_PREWATCH_GAP');continue
     try:self.add_tree(path,deadline=deadline)
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
 def validate_directory_identities(self):
  from preservation import identity
  deadline=time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  for path,wanted in self.initial_directories.items():
   try:
    if identity(bounded_capture.guarded_call(deadline,os.stat,path))!=wanted:self.errors.append('DIRECTORY_IDENTITY_CHANGED '+path)
   except bounded_capture.CaptureError:self.errors.append('DIRECTORY_IDENTITY_ACQUISITION_TIME_LIMIT_EXCEEDED');break
   except OSError:self.errors.append('DIRECTORY_MISSING '+path)
  return not self.rejected()
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
 def resolve_bookkeeping(self):
  if not self.bookkeeping_policy:return
  if self.bookkeeping_v3:return
  scoped=[e for e in self.events if e['category']=='SCOPED_BOOKKEEPING_EVENT_PENDING_FINAL_EVALUATION']
  for event in scoped:
   path=Path(event['path']);mask=event['mask'];cookie=event.get('cookie',0)
   if path!=self.bookkeeping_target and mask&0x40:
    paired=any(Path(other['path'])==self.bookkeeping_target and other['mask']&0x80 and other.get('cookie')==cookie and cookie for other in scoped)
    if not paired:event['category']='REJECT_BOOKKEEPING_TEMP_RENAME_OUTSIDE_TARGET'
   if path==self.bookkeeping_target and mask&0x80:
    paired=any(bookkeeping_v2.is_reserved_temp(Path(other['path']),self.bookkeeping_root) and other['mask']&0x40 and other.get('cookie')==cookie and cookie for other in scoped)
    if not paired:event['category']='REJECT_BOOKKEEPING_TARGET_RENAME_FROM_UNREGISTERED_SOURCE'
 def rejected(self):return bool(self.errors or any(e['category'].startswith('REJECT') for e in self.events))
 def close(self):
  if not self.closed:
   os.close(self.fd);self.closed=True
 def stop_and_drain(self,endpoint_ns):
  """Remove watches after endpoint_ns and drain all earlier queued events before close."""
  if self.closed:return endpoint_ns
  deadline=time.monotonic()+bookkeeping_v3.LIMITS['capture_total_seconds_per_boundary_max']
  self.shutdown_wds=set(self.watches)
  for wd in sorted(self.shutdown_wds):
   try:
    rc=bounded_capture.guarded_call(deadline,self.libc.inotify_rm_watch,self.fd,wd)
    if rc<0:raise OSError(ctypes.get_errno(),'inotify_rm_watch')
   except Exception as error:
    self.errors.append('WATCH_SHUTDOWN_FAILED:'+type(error).__name__);break
  while self.shutdown_wds and time.monotonic()<deadline:
   try:ready=bounded_capture.guarded_call(deadline,select.select,[self.fd],[],[],.01)[0]
   except bounded_capture.CaptureError:break
   if ready:self.drain(deadline=deadline)
  if self.shutdown_wds:self.errors.append('WATCH_SHUTDOWN_QUEUE_NOT_DRAINED')
  self.close();return endpoint_ns

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


def cleanup_owned_descendants(scope,timeout_seconds=5.0,poll_seconds=.01):
 """Bounded cleanup of retained subreaper-owned PID/birth identities only."""
 deadline=time.monotonic()+timeout_seconds;terminated=[];remaining=[];errors=[];seen=set();identities={}
 def record(kind,**detail):
  key=(kind,detail.get('pid'),detail.get('error_type'),detail.get('reason'))
  if key not in seen:seen.add(key);errors.append({'kind':kind,**detail})
 def discover(final=False):
  try:return list(scope.pending())
  except PermissionError as error:
   record('OWNED_DESCENDANT_FINAL_DISCOVERY_PERMISSION' if final else 'OWNED_DESCENDANT_DISCOVERY_PERMISSION',
          error_type=type(error).__name__,reason=str(error));return []
  except (OSError,RuntimeError) as error:
   record('OWNED_DESCENDANT_FINAL_DISCOVERY_UNKNOWN' if final else 'OWNED_DESCENDANT_DISCOVERY_UNKNOWN',
          error_type=type(error).__name__,reason=str(error));return []
 def inspect(pids,send_signal):
  unresolved=[]
  for pid in sorted(set(pids)|set(scope.known)):
   wanted=scope.known.get(pid)
   if wanted is None:
    record('OWNED_DESCENDANT_IDENTITY_UNKNOWN',pid=pid);unresolved.append(pid);continue
   try:observed=scope.birth(pid)
   except PermissionError as error:
    identities[str(pid)]={'retained_birth':wanted,'observed_birth_before_signal':'NOT_ESTABLISHED'}
    record('OWNED_DESCENDANT_IDENTITY_PERMISSION',pid=pid,error_type=type(error).__name__,reason=str(error))
    unresolved.append(pid);continue
   except (OSError,RuntimeError) as error:
    identities[str(pid)]={'retained_birth':wanted,'observed_birth_before_signal':'NOT_ESTABLISHED'}
    record('OWNED_DESCENDANT_IDENTITY_UNKNOWN',pid=pid,error_type=type(error).__name__,reason=str(error))
    unresolved.append(pid);continue
   identities[str(pid)]={'retained_birth':wanted,'observed_birth_before_signal':observed}
   if observed is None:continue
   if observed!=wanted:
    record('OWNED_DESCENDANT_PID_REUSED',pid=pid,retained_birth=wanted,observed_birth=observed)
    unresolved.append(pid);continue
   try:
    done,_status=os.waitpid(pid,os.WNOHANG)
    if done:continue
   except ChildProcessError:pass
   if not send_signal:
    unresolved.append(pid);continue
   try:
    os.kill(pid,signal.SIGKILL)
    if pid not in terminated:terminated.append(pid)
    unresolved.append(pid)
   except ProcessLookupError:pass
   except PermissionError as error:
    record('OWNED_DESCENDANT_SIGNAL_PERMISSION',pid=pid,error_type=type(error).__name__,reason=str(error));unresolved.append(pid)
   except OSError as error:
    record('OWNED_DESCENDANT_SIGNAL_UNKNOWN',pid=pid,error_type=type(error).__name__,reason=str(error));unresolved.append(pid)
  return unresolved
 while time.monotonic()<deadline:
  pending=discover()
  unresolved=inspect(pending,True)
  if not unresolved and not errors:
   return {'result':'QUIESCENT','owned_identities':identities,'terminated':terminated,
           'remaining':[],'errors':[],'timeout_seconds':timeout_seconds,
           'scope':'ChildScope children minus pre-existing children, exact retained PID/birth identity'}
  time.sleep(min(poll_seconds,max(0,deadline-time.monotonic())))
 remaining=inspect(discover(final=True),False)
 if remaining or errors:
  record('OWNED_DESCENDANT_CLEANUP_TIMEOUT',remaining=list(remaining))
 return {'result':'NOT_QUIESCENT','owned_identities':identities,'terminated':terminated,
         'remaining':list(remaining),'errors':errors,'timeout_seconds':timeout_seconds,
         'scope':'ChildScope children minus pre-existing children, exact retained PID/birth identity'}

def run(argv,cwd,log,protected,repositories,metadata_roots,allowed,cross_lane=(),shared_git=None,env=None,timeout=2400,shadow_root=None,shadow_declared=(),enumeration_roots=(),pruned_roots=(),expected_missing=(),shadow_reconciler=None,frozen_roots=(),bookkeeping_policy=None):
 import uuid
 tag=uuid.uuid4().hex;env=dict(os.environ if env is None else env)
 if 'GIT_INDEX_FILE' in env:raise RuntimeError('ALTERNATE_INDEX_FORBIDDEN')
 env.update(EP19_GATE_SCOPE=tag,GIT_OPTIONAL_LOCKS='0')
 started=time.time();watcher=None;children=None;child=None;result=None;primary_error=None;cleanup_errors=[];descendant_cleanup=None
 stage='WATCH_ACQUISITION';rc=None;ready=None;timed_out=False;termination_causes=[];terminated=[];pending=[]
 before={};after={};changed=[];unapproved_changed=[];quiescence_start=None
 try:
  watcher=Watch(protected,repositories,metadata_roots,allowed,cross_lane,shared_git,shadow_root,shadow_declared,enumeration_roots,pruned_roots,expected_missing,frozen_roots,bookkeeping_policy)
  stage='CHILD_SCOPE_ACQUISITION'
  children=ChildScope()
  stage='INITIAL_SNAPSHOT'
  before=snapshot(watcher.capture_paths,watcher.expected_missing);watcher.drain()
  if watcher.rejected():raise RuntimeError('PRESERVATION_REJECT_BEFORE_CHILD')
  ready=time.time();stage='EVIDENCE_LOG_PERSISTENCE'
  with durability.exclusive_stream(log,0o400) as f:
   stage='PROCESS_LAUNCH'
   child=subprocess.Popen(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   stage='PROCESS_OBSERVATION'
   while child.poll() is None:
    if select.select([watcher.fd],[],[],.025)[0]:watcher.drain()
    if watcher.rejected() or time.time()-ready>timeout:
     protection_reject=watcher.rejected();timed_out=time.time()-ready>timeout
     if protection_reject:termination_causes.append('PROTECTION_REJECTION')
     if timed_out:termination_causes.append('WORKLOAD_TIMEOUT')
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
     if 'OWNED_DESCENDANT_CLEANUP' not in termination_causes:termination_causes.append('OWNED_DESCENDANT_CLEANUP')
     for pid in pending:
      try:os.kill(pid,signal.SIGKILL);terminated.append(pid)
      except ProcessLookupError:pass
    if time.time()-quiescence_start>15:watcher.errors.append('OWNED_PROCESS_NOT_QUIESCENT');break
    select.select([watcher.fd],[],[],.05);watcher.drain()
   watcher.resolve_frontend_locks();watcher.resolve_shared();after=snapshot(watcher.capture_paths,watcher.expected_missing);watcher.drain();watcher.resolve_bookkeeping()
   if any(e['category'].startswith('PENDING_') for e in watcher.events):watcher.errors.append('LATE_SHARED_SCOPE_UNRESOLVED')
   stage='EVIDENCE_LOG_FINALIZATION'
  stage='POST_PROCESS_RECONCILIATION'
  changed=[p for p in before.keys()|after.keys() if before.get(p)!=after.get(p)]
  bookkeeping_evaluation=None;unapproved_changed=list(changed)
  if watcher.bookkeeping_policy and not watcher.bookkeeping_v3:
   bookkeeping_evaluation=bookkeeping_v2.evaluate(watcher.bookkeeping_policy)
   if bookkeeping_evaluation['V2_BOOKKEEPING_EVALUATION']!='PASS':watcher.errors.append('V2_BOOKKEEPING_FINAL_REJECT:'+repr(bookkeeping_evaluation['reasons']))
   allowed_changes={str(watcher.bookkeeping_target),str(watcher.bookkeeping_root)}
   unapproved_changed=[p for p in changed if p not in allowed_changes]
  elif watcher.bookkeeping_v3:
   delegated={str(path) for path in watcher.bookkeeping_paths}|{str(watcher.bookkeeping_root)}
   unapproved_changed=[p for p in changed if p not in delegated and not (Path(p).parent==watcher.bookkeeping_root and bookkeeping_v3.TEMP_RE.fullmatch(Path(p).name))]
  watcher.validate_directory_identities()
  reconciliation=None
  if shadow_root:
   try:
    if shadow_reconciler is None:raise RuntimeError('MISSING_BOUND_SHADOW_RECONCILIATION')
    reconciliation=shadow_reconciler(watcher.events,tag)
    require_shadow_reconciliation(reconciliation,shadow_root,tag,shadow_declared)
   except Exception as error:watcher.errors.append('SHADOW_ACCEPTANCE:'+str(error))
  rejected=bool(rc or unapproved_changed or timed_out or watcher.rejected())
  dimensions={'native_invocation':True,'native_exit':rc,
              'native_command_exit_failure':rc not in (None,0),
              'product_assertion_failure':False,
              'observer_preservation_failure':bool(unapproved_changed or watcher.rejected()),
              'workload_timeout_or_cancellation':timed_out,
              'wrapper_or_environment_failure':False,
              'evidence_persistence_failure':False,'cleanup_failure':False}
  result={'shadow_reconciliation':reconciliation,'result':'REJECT' if rejected else 'PASS_BOUNDED_OBSERVATION','native_exit':rc,'wrapper_exit':1 if rejected else 0,'before':before,'after':after,'changed':changed,'unapproved_changed':unapproved_changed,'bookkeeping_evaluation':bookkeeping_evaluation,'bookkeeping_observation_limits':watcher.bookkeeping_limits,'events':watcher.events,'shared_metadata_scope_proof':watcher.shared_proof,'observation_errors':watcher.errors,'gaps':watcher.gaps,'dynamic_watches':watcher.dynamic,'registered_watches':len(watcher.watches),'ready_before_child':True,'final_queue_drained':True,'child_pid':child.pid,'gate_process_scope':tag,'child_containment':'Linux process-local subreaper plus tag observation; private PID namespace additionally enforced for frontend','owned_processes_remaining':pending,'owned_processes_terminated':terminated,'quiescence_seconds':time.time()-quiescence_start,'start':started,'ready':ready,'end':time.time(),'timeout':timed_out,'observer_terminated_child':bool(termination_causes),'termination_causes':termination_causes,'failure_dimensions':dimensions,'command':argv,'cwd':str(cwd),'scope_limits':'Local inotify plus captured endpoint fields, no universal mmap/network/attribute coverage or writer PID attribution; per-command interval only. Exact .usage.json V2 changes and verified direct-child .usage_<8 chars>.tmp events require final semantic evaluation; short-lived temp details may remain unavailable. Strict Skill/Memory events and unclassifiable gaps reject.'}
 except BaseException as error:
  primary_error=error
 finally:
  if primary_error is not None and child is not None and child.poll() is None:
   if 'EXCEPTIONAL_CHILD_CLEANUP' not in termination_causes:termination_causes.append('EXCEPTIONAL_CHILD_CLEANUP')
   try:
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=3)
    except subprocess.TimeoutExpired:
     os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
   except ProcessLookupError:pass
   except BaseException as error:cleanup_errors.append(error)
  if primary_error is not None and children is not None:
   if 'EXCEPTIONAL_OWNED_DESCENDANT_CLEANUP' not in termination_causes:termination_causes.append('EXCEPTIONAL_OWNED_DESCENDANT_CLEANUP')
   try:
    descendant_cleanup=cleanup_owned_descendants(children)
    terminated.extend(pid for pid in descendant_cleanup['terminated'] if pid not in terminated)
    pending=list(descendant_cleanup['remaining'])
    for row in descendant_cleanup['errors']:
     cleanup_errors.append(RuntimeError(row['kind']+':'+str({k:v for k,v in row.items() if k!='kind'})))
   except BaseException as error:cleanup_errors.append(error)
  if children is not None:
   try:children.close()
   except BaseException as error:cleanup_errors.append(error)
  if watcher is not None:
   try:watcher.close()
   except BaseException as error:cleanup_errors.append(error)
 if primary_error is not None:
  observed_exit=rc if rc is not None else child.returncode if child is not None else None
  dimensions={'native_invocation':child is not None,'native_exit':observed_exit,
              'native_command_exit_failure':observed_exit not in (None,0),
              'product_assertion_failure':False,
              'observer_preservation_failure':bool((watcher and watcher.rejected()) or unapproved_changed),
              'workload_timeout_or_cancellation':bool(timed_out or termination_causes),
              'wrapper_or_environment_failure':stage in ('WATCH_ACQUISITION','CHILD_SCOPE_ACQUISITION','INITIAL_SNAPSHOT','PROCESS_LAUNCH'),
              'evidence_persistence_failure':stage in ('EVIDENCE_LOG_PERSISTENCE','EVIDENCE_LOG_FINALIZATION'),
              'parser_helper_process_failure':False,'cleanup_failure':bool(cleanup_errors)}
  dimensions.update(getattr(primary_error,'failure_dimensions',{}) or {})
  causal_rows=causal.rows(primary_error,'primary',stage,'native-observation-primary')
  for error in cleanup_errors:
   causal_rows.extend(causal.rows(error,'cleanup','RESOURCE_CLEANUP','secondary-for-native-observation'))
  causal_rows=causal.unique(causal_rows)
  receipt={'result':'REJECT','native_exit':observed_exit,'wrapper_exit':1,
           'child_pid':child.pid if child is not None else None,'native_invocation':child is not None,
           'start':started,'ready':ready,'end':time.time(),'timeout':timed_out,'command':argv,'cwd':str(cwd),
           'termination_causes':termination_causes,'observer_terminated_child':bool(termination_causes),
           'owned_processes_remaining':pending,'owned_processes_terminated':terminated,
           'owned_descendant_cleanup':descendant_cleanup,
           'before':before,'after':after,'changed':changed,'unapproved_changed':unapproved_changed,
           'events':list(watcher.events) if watcher else [],
           'observation_errors':list(watcher.errors) if watcher else [],
           'gaps':list(watcher.gaps) if watcher else [],'failure_stage':stage,
           'failure_dimensions':dimensions,'causal_errors':causal_rows}
  failure=(BaseExceptionGroup('NATIVE_OBSERVE_PRIMARY_AND_CLEANUP_FAILURE',[primary_error,*cleanup_errors])
           if cleanup_errors else primary_error)
  setattr(failure,'native_observe_receipt',receipt)
  raise failure from None
 if cleanup_errors:
  result['cleanup_errors']=[type(error).__name__+':'+str(error) for error in cleanup_errors]
  result['failure_dimensions']['cleanup_failure']=True
  result['causal_errors']=causal.unique([row for error in cleanup_errors for row in
      causal.rows(error,'cleanup','RESOURCE_CLEANUP','native-observation-cleanup')])
  result['result']='REJECT';result['wrapper_exit']=1
 return result


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
