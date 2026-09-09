"""FD-relative preservation capture. Ordinary reads are explicit, never a fallback.

Contract: inputs/MONITOR_CONTRACT.txt lines 6,12. No bodies are exported.
Ancestors are opened with O_PATH and never enumerated; every binding is rechecked.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse, hashlib, json, os, stat, time
import capture as bounded_capture
import causal

FIELDS = ('st_dev','st_ino','st_mode','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns','st_nlink')
INSTRUCTIONS = ('USER_HOME/.hermes/skills', 'USER_HOME/.hermes/memories')
MAX_CAPTURE_SECONDS = 300.0
MAX_CAPTURE_ENTRIES = 262144
def metadata(s): return {k:getattr(s,k) for k in FIELDS}
def identity(s): return s.st_dev,s.st_ino,s.st_mode

def _raise_owned(label,primary,cleanup):
    causal.raise_composed(label,primary,
        [('cleanup',stage,error) for stage,error in cleanup],
        dimensions={'observer_preservation_failure':True},primary_stage=label)

def absolute(path):
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts or str(p)!=os.path.normpath(str(p)):
        raise ValueError('NONCANONICAL_SCOPE_PATH')
    return p

@contextmanager
def parent_fd(path):
    """Keep ALL ancestor FDs and verify every parent/name binding on exit."""
    p=absolute(path); fds=[]; links=[];primary=None
    try:
        fd=os.open('/',os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(fd)
        for part in p.parts[1:-1]:
            before=os.stat(part,dir_fd=fd,follow_symlinks=False)
            nxt=os.open(part,os.O_PATH|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
            fds.append(nxt)
            if identity(before)!=identity(os.fstat(nxt)): raise RuntimeError('ANCESTOR_REPLACED')
            links.append((fd,part,nxt,identity(before)));fd=nxt
        yield fd,p.name
        for parent,name,child,wanted in links:
            if identity(os.stat(name,dir_fd=parent,follow_symlinks=False))!=wanted or identity(os.fstat(child))!=wanted:
                raise RuntimeError('ANCESTOR_REPLACED')
    except BaseException as error:
        primary=error
    finally:
        cleanup=[]
        for fd in reversed(fds):
            try:os.close(fd)
            except BaseException as error:cleanup.append(('ANCESTOR_FD_CLOSE',error))
        _raise_owned('PARENT_FD_BODY_AND_ANCESTOR_CLEANUP_FAILURE',primary,cleanup)

class Collector:
    def __init__(self, roots=(), files=(), *, expected_nonempty=(), expected_files=None, noatime=False, hook=None, expected_missing=(),max_seconds=MAX_CAPTURE_SECONDS,max_entries=MAX_CAPTURE_ENTRIES):
        self.roots=[absolute(p) for p in roots];self.files=[absolute(p) for p in files]
        self.nonempty=set(map(str,expected_nonempty));self.expected_files=expected_files
        self.expected_missing=set(map(str,expected_missing))
        if not self.expected_missing<=set(map(str,self.files)):raise ValueError("EXPECTED_ABSENCE_MUST_BE_EXPLICIT_FILE_SCOPE")
        self.noatime=noatime;self.hook=hook or (lambda phase,path:None)
        if max_seconds<=0 or max_entries<1:raise ValueError('PRESERVATION_ACQUISITION_LIMIT_INVALID')
        self.max_seconds=max_seconds;self.max_entries=max_entries;self.deadline=None;self.acquired=0
        self.rows={};self.errors=[]
    def error(self,path,e):
        row=causal.record(e,'capture','PRESERVATION_CAPTURE','same-captured-path',path=str(path))
        row.update(type=type(e).__name__,errno=getattr(e,'errno',None))
        self.errors.append(row)
    def read(self,parent,name,path,recurse):
        bounded_capture._remaining(self.deadline)
        before=os.stat(name,dir_fd=parent,follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode):raise RuntimeError('SYMLINK_SCOPE_REJECTED')
        isdir=stat.S_ISDIR(before.st_mode)
        if not isdir and not stat.S_ISREG(before.st_mode):raise RuntimeError('UNSUPPORTED_SCOPE_TYPE')
        flags=os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK
        if isdir:flags|=os.O_DIRECTORY
        if self.noatime:flags|=os.O_NOATIME
        self.hook('before_open',path)
        fd=os.open(name,flags,dir_fd=parent)
        primary=None
        try:
            if metadata(before)!=metadata(os.fstat(fd)):raise RuntimeError('TARGET_REPLACED')
            row={'metadata':metadata(before),'kind':'directory' if isdir else 'file'}
            if isdir and recurse:
                self.hook('enumerate',path)
                names=bounded_capture._bounded_names(fd,deadline=self.deadline,
                    max_entries=max(1,self.max_entries-self.acquired));row['children']=names
                for child in names:
                    self.acquired+=1
                    if self.acquired>self.max_entries:raise RuntimeError('PRESERVATION_ACQUISITION_CAPACITY_EXCEEDED')
                    try:self.read(fd,child,path/child,True)
                    except Exception as e:self.error(path/child,e)
                if bounded_capture._bounded_names(fd,deadline=self.deadline,
                    max_entries=max(1,self.max_entries-self.acquired+len(names)))!=names:raise RuntimeError('DIRECTORY_UNSTABLE')
            elif not isdir:
                h=hashlib.sha256();blob=hashlib.sha1(b"blob "+str(before.st_size).encode()+b"\0")
                while True:
                    bounded_capture._remaining(self.deadline)
                    self.hook('read',path);chunk=os.read(fd,1024*1024)
                    if not chunk:break
                    h.update(chunk);blob.update(chunk)
                row['sha256']=h.hexdigest();row['git_blob']=blob.hexdigest()
            self.hook('after_read',path)
            if metadata(before)!=metadata(os.fstat(fd)) or metadata(before)!=metadata(os.stat(name,dir_fd=parent,follow_symlinks=False)):
                raise RuntimeError('CAPTURE_UNSTABLE_OR_REPLACED')
            self.rows[str(path)]=row
        except BaseException as error:primary=error
        cleanup=[]
        try:os.close(fd)
        except BaseException as error:cleanup.append(('COLLECTOR_TARGET_FD_CLOSE',error))
        _raise_owned('COLLECTOR_READ_AND_FD_CLEANUP_FAILURE',primary,cleanup)
    def capture(self):
        start=time.time_ns()
        self.deadline=time.monotonic()+self.max_seconds
        for path,recurse in [(p,True) for p in self.roots]+[(p,False) for p in self.files]:
            try:
                self.acquired+=1
                if self.acquired>self.max_entries:raise RuntimeError('PRESERVATION_ACQUISITION_CAPACITY_EXCEEDED')
                with bounded_capture._deadline_guard(bounded_capture._remaining(self.deadline)):
                    with parent_fd(path) as (fd,name):
                        if str(path) in self.expected_missing:
                            try:os.stat(name,dir_fd=fd,follow_symlinks=False)
                            except FileNotFoundError:self.rows[str(path)]={'kind':'missing','expected_absence':True}
                            else:raise RuntimeError('EXPECTED_ABSENCE_CHANGED')
                        else:self.read(fd,name,path,recurse)
            except Exception as e:self.error(path,e)
        hashed={p for p,r in self.rows.items() if 'sha256' in r}
        for root in self.nonempty:
            if not any(p.startswith(root+'/') for p in hashed):self.error(root,RuntimeError('EXPECTED_NONEMPTY_UNIVERSE'))
        if self.expected_files is not None and hashed!=set(self.expected_files):self.error('universe',RuntimeError('EXPECTED_UNIVERSE_MISMATCH'))
        return {'result':'INCOMPLETE' if self.errors else 'COMPLETE','native_exit':1 if self.errors else 0,
                'start_ns':start,'end_ns':time.time_ns(),'entries':self.rows,'errors':self.errors,'hashed':len(hashed),
                'read_policy':'O_NOATIME_REQUIRED_NO_FALLBACK' if self.noatime else 'ORDINARY_READ_EXPLICIT_CONTRACT_ATIME_NOT_FROZEN',
                'metadata_fields':FIELDS,'timestamp_restoration':False,'body_export':False,'claim':'Current sequential endpoints; not atomic or historical continuity'}

def capture_files(paths,expected_missing=()):
    r=Collector(files=paths,expected_missing=expected_missing).capture()
    if r['result']!='COMPLETE':
        error=RuntimeError('INCOMPLETE_CAPTURE')
        error.causal_errors=causal.unique([
            leaf for row in r['errors'] for leaf in row.get('causal_errors',[])])
        error.preservation_receipt=r
        raise error
    return r['entries']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--instructions',action='store_true');ap.add_argument('--scope',type=Path);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    if a.instructions==bool(a.scope):ap.error('select instructions OR explicit scope')
    cfg={'roots':INSTRUCTIONS,'expected_nonempty':INSTRUCTIONS} if a.instructions else json.loads(a.scope.read_text())
    r=Collector(**cfg).capture()
    with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps({k:r[k] for k in ('result','native_exit','hashed','errors')}));return r['native_exit']
if __name__=='__main__':raise SystemExit(main())


def directory_inventory(root,prune=(),*,deadline=None,max_entries=262144):
    """Secure bounded enumeration; never follows a symlink or lists ancestors."""
    root=absolute(root);prune=set(map(str,prune));directories=[];files=[]
    deadline=deadline or time.monotonic()+bounded_capture.MAX_STABLE_SECONDS
    acquired=0
    def visit(parent,name,path):
        nonlocal acquired
        before=bounded_capture.guarded_call(deadline,os.stat,name,dir_fd=parent,follow_symlinks=False)
        fd=bounded_capture.guarded_call(deadline,os.open,name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        primary=None
        try:
            if identity(before)!=identity(bounded_capture.guarded_call(deadline,os.fstat,fd)):raise RuntimeError('DIRECTORY_REPLACED')
            directories.append(path)
            names=bounded_capture._bounded_names(fd,deadline=deadline,max_entries=max_entries)
            for child in names:
                acquired+=1
                if acquired>max_entries:raise RuntimeError('DIRECTORY_INVENTORY_CAPACITY_EXCEEDED')
                p=path/child
                if str(p) in prune:continue
                st=bounded_capture.guarded_call(deadline,os.stat,child,dir_fd=fd,follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):visit(fd,child,p)
                elif stat.S_ISLNK(st.st_mode):raise RuntimeError('SYMLINK_ENUMERATION_REJECT '+str(p))
                elif stat.S_ISREG(st.st_mode):files.append(p)
                else:raise RuntimeError('SPECIAL_ENUMERATION_REJECT '+str(p))
            if (bounded_capture._bounded_names(fd,deadline=deadline,max_entries=max_entries)!=names or
                    identity(bounded_capture.guarded_call(deadline,os.stat,name,dir_fd=parent,follow_symlinks=False))!=identity(before)):
                raise RuntimeError('DIRECTORY_ENUMERATION_UNSTABLE')
        except BaseException as error:primary=error
        cleanup=[]
        try:os.close(fd)
        except BaseException as error:cleanup.append(('DIRECTORY_INVENTORY_FD_CLOSE',error))
        _raise_owned('DIRECTORY_INVENTORY_AND_FD_CLEANUP_FAILURE',primary,cleanup)
    with bounded_capture._deadline_guard(bounded_capture._remaining(deadline)):
        with parent_fd(root) as (fd,name):visit(fd,name,root)
    return directories,files
