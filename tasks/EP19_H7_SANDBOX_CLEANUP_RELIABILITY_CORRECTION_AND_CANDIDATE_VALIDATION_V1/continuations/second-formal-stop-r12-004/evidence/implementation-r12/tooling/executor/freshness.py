"""Shared actual execution acceptance path, also exercised by synthetic controls."""
from pathlib import Path
import hashlib,json,os,stat
from coverage import digest,put
from execution import SHA,TREE,git
import durability

def _stable_bytes(path):
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1:raise RuntimeError('CLEANUP_SOURCE_NOT_INDEPENDENT_REGULAR')
        chunks=[]
        while True:
            chunk=os.read(fd,1024*1024)
            if not chunk:break
            chunks.append(chunk)
        after=os.fstat(fd)
        fields=lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns,value.st_nlink)
        if fields(before)!=fields(after):raise RuntimeError('CLEANUP_SOURCE_CHANGED_DURING_CAPTURE')
        return b''.join(chunks),fields(after)
    finally:os.close(fd)

def preserve_cleanup(paths,dest,allowed,repo=None):
    rows=[]
    for p in sorted(set(map(Path,paths))):
        if not p.exists():continue
        if p.is_symlink() or p.resolve()!=p or not p.is_file() or not any(p.is_relative_to(Path(a)) for a in allowed):raise RuntimeError('UNAUTHORIZED_OUTPUT_CLEANUP')
        if repo and p.is_relative_to(repo) and git(repo,'ls-files','-z','--',str(p.relative_to(repo))):raise RuntimeError('TRACKED_OUTPUT_CLEANUP_REFUSED')
        target=dest/str(len(rows));payload,identity=_stable_bytes(p)
        durability.exclusive_bytes(target,payload,0o400)
        current=p.stat();fields=lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns,value.st_nlink)
        if fields(current)!=identity or digest(p)!=hashlib.sha256(payload).hexdigest():raise RuntimeError('CLEANUP_SOURCE_CHANGED_BEFORE_UNLINK')
        rows.append({'path':str(p),'preimage':str(target),'sha256':digest(target)})
        p.unlink()
        durability.fsync_directory(p.parent)
    put(dest.parent/'cleanup.json',rows)
    return rows

def require_fresh_outputs(required,before,process,run_id,gate_id,parser):
    if process.get('native_exit')!=0 or process.get('wrapper_exit')!=0:raise RuntimeError('PROCESS_OR_PRESERVATION_REJECT')
    if process.get('run_id')!=run_id or process.get('gate')!=gate_id or process.get('candidate')!=SHA or process.get('tree')!=TREE:raise RuntimeError('PRODUCER_IDENTITY_MISMATCH')
    result={}
    for p in map(Path,required):
        if before.get(str(p))!='ABSENT':raise RuntimeError('STALE_OR_UNBOUND_OUTPUT '+str(p))
        if p.is_symlink() or p.resolve()!=p or not p.is_file():raise RuntimeError('MISSING_REQUIRED_OUTPUT '+str(p))
        result[str(p)]=digest(p)
    parsed=parser()
    if not isinstance(parsed,dict) or parsed.get('result')!='PASS':raise RuntimeError('PARSER_NOT_PASS')
    return {'result':'PASS','outputs':result,'parser':parsed,'producer':{'run_id':run_id,'gate':gate_id,'candidate':SHA,'tree':TREE}}

def dependency(receipt,run_id):
    if receipt.get('result')!='PASS' or receipt.get('run_id')!=run_id or receipt.get('candidate')!=SHA or receipt.get('tree')!=TREE:raise RuntimeError('DEPENDENCY_NOT_PASS_OR_WRONG_RUN')
    import artifacts
    from execution import D
    gate=D/'outputs/continuation-runs'/run_id/'runtime/gates'/receipt['gate']
    if receipt.get('evidence_root')!=str(gate):raise RuntimeError('DEPENDENCY_EVIDENCE_ROOT')
    artifacts.verify(receipt.get('artifacts'),gate,run_id,receipt['gate'])


def dependency_inputs(run,repo):
    """Measure resolved dependencies, pruning only declared volatile tool outputs.

    Existing artifacts are immutable within an invocation. New resolutions remain
    explicit producer outputs; they are never represented as pre-run frozen input.
    """
    paths=[];result={};cache=run/'runtime/cache/backend'
    for p in cache.rglob('*'):
        if p.is_file() and p.suffix in ('.jar','.pom','.module'):paths.append(p)
    mods=repo/'frontend/node_modules'
    if mods.is_dir():
        import os
        for directory,dirs,files in os.walk(mods,followlinks=False):
            if Path(directory)==mods:dirs[:]=[n for n in dirs if n not in ['.vite','.vite-temp']]
            for n in dirs:
                if (Path(directory)/n).is_symlink():raise RuntimeError('DEPENDENCY_SYMLINK_DIRECTORY')
            paths += [Path(directory)/n for n in files]
    for p in paths:
        if p.is_symlink():
            if not p.resolve().is_relative_to(mods):raise RuntimeError('DEPENDENCY_SYMLINK_ESCAPE')
            result[str(p)]={'symlink':str(p.readlink()),'sha256':digest(p)}
        else:result[str(p)]={'sha256':digest(p)}
    return result

def compare_dependencies(before,after):
    changed=[p for p,value in before.items() if after.get(p)!=value]
    if changed:raise RuntimeError('RESOLVED_DEPENDENCY_CHANGED '+repr(changed[:5]))
    return {'unchanged_existing':len(before),'newly_resolved':{p:v for p,v in after.items() if p not in before}}
