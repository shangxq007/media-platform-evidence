"""FD-relative preservation capture. Ordinary reads are explicit, never a fallback.

Contract: inputs/MONITOR_CONTRACT.txt lines 6,12. No bodies are exported.
Ancestors are opened with O_PATH and never enumerated; every binding is rechecked.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse, hashlib, json, os, stat, time

FIELDS = ('st_dev','st_ino','st_mode','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns','st_nlink')
INSTRUCTIONS = ('/home/user/.hermes/skills', '/home/user/.hermes/memories')
def metadata(s): return {k:getattr(s,k) for k in FIELDS}
def identity(s): return s.st_dev,s.st_ino,s.st_mode

def absolute(path):
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts or str(p)!=os.path.normpath(str(p)):
        raise ValueError('NONCANONICAL_SCOPE_PATH')
    return p

@contextmanager
def parent_fd(path):
    """Keep ALL ancestor FDs and verify every parent/name binding on exit."""
    p=absolute(path); fds=[]; links=[]
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
    finally:
        for fd in reversed(fds):os.close(fd)

class Collector:
    def __init__(self, roots=(), files=(), *, expected_nonempty=(), expected_files=None, noatime=False, hook=None, expected_missing=()):
        self.roots=[absolute(p) for p in roots];self.files=[absolute(p) for p in files]
        self.nonempty=set(map(str,expected_nonempty));self.expected_files=expected_files
        self.expected_missing=set(map(str,expected_missing))
        if not self.expected_missing<=set(map(str,self.files)):raise ValueError("EXPECTED_ABSENCE_MUST_BE_EXPLICIT_FILE_SCOPE")
        self.noatime=noatime;self.hook=hook or (lambda phase,path:None)
        self.rows={};self.errors=[]
    def error(self,path,e):self.errors.append({'path':str(path),'type':type(e).__name__,'errno':getattr(e,'errno',None),'reason':str(e)})
    def read(self,parent,name,path,recurse):
        before=os.stat(name,dir_fd=parent,follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode):raise RuntimeError('SYMLINK_SCOPE_REJECTED')
        isdir=stat.S_ISDIR(before.st_mode)
        if not isdir and not stat.S_ISREG(before.st_mode):raise RuntimeError('UNSUPPORTED_SCOPE_TYPE')
        flags=os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK
        if isdir:flags|=os.O_DIRECTORY
        if self.noatime:flags|=os.O_NOATIME
        self.hook('before_open',path)
        fd=os.open(name,flags,dir_fd=parent)
        try:
            if metadata(before)!=metadata(os.fstat(fd)):raise RuntimeError('TARGET_REPLACED')
            row={'metadata':metadata(before),'kind':'directory' if isdir else 'file'}
            if isdir and recurse:
                self.hook('enumerate',path); names=sorted(os.listdir(fd));row['children']=names
                for child in names:
                    try:self.read(fd,child,path/child,True)
                    except Exception as e:self.error(path/child,e)
                if sorted(os.listdir(fd))!=names:raise RuntimeError('DIRECTORY_UNSTABLE')
            elif not isdir:
                h=hashlib.sha256();blob=hashlib.sha1(b"blob "+str(before.st_size).encode()+b"\0")
                while True:
                    self.hook('read',path);chunk=os.read(fd,1024*1024)
                    if not chunk:break
                    h.update(chunk);blob.update(chunk)
                row['sha256']=h.hexdigest();row['git_blob']=blob.hexdigest()
            self.hook('after_read',path)
            if metadata(before)!=metadata(os.fstat(fd)) or metadata(before)!=metadata(os.stat(name,dir_fd=parent,follow_symlinks=False)):
                raise RuntimeError('CAPTURE_UNSTABLE_OR_REPLACED')
            self.rows[str(path)]=row
        finally:os.close(fd)
    def capture(self):
        start=time.time_ns()
        for path,recurse in [(p,True) for p in self.roots]+[(p,False) for p in self.files]:
            try:
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
    if r['result']!='COMPLETE':raise RuntimeError('INCOMPLETE_CAPTURE '+json.dumps(r['errors']))
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


def directory_inventory(root,prune=()):
    """Secure bounded enumeration; never follows a symlink or lists ancestors."""
    root=absolute(root);prune=set(map(str,prune));directories=[];files=[]
    def visit(parent,name,path):
        before=os.stat(name,dir_fd=parent,follow_symlinks=False)
        fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
        try:
            if identity(before)!=identity(os.fstat(fd)):raise RuntimeError('DIRECTORY_REPLACED')
            directories.append(path);names=sorted(os.listdir(fd))
            for child in names:
                p=path/child
                if str(p) in prune:continue
                st=os.stat(child,dir_fd=fd,follow_symlinks=False)
                if stat.S_ISDIR(st.st_mode):visit(fd,child,p)
                elif stat.S_ISLNK(st.st_mode):raise RuntimeError('SYMLINK_ENUMERATION_REJECT '+str(p))
                elif stat.S_ISREG(st.st_mode):files.append(p)
                else:raise RuntimeError('SPECIAL_ENUMERATION_REJECT '+str(p))
            if sorted(os.listdir(fd))!=names or identity(os.stat(name,dir_fd=parent,follow_symlinks=False))!=identity(before):raise RuntimeError('DIRECTORY_ENUMERATION_UNSTABLE')
        finally:os.close(fd)
    with parent_fd(root) as (fd,name):visit(fd,name,root)
    return directories,files
