"""Independent gate evidence. Receipts never depend on mutable output bytes."""
from pathlib import Path, PurePosixPath
import hashlib, os, stat
from execution import SHA,TREE

def read(path):
 p=Path(path)
 if not p.is_absolute() or p.resolve()!=p:raise RuntimeError('ARTIFACT_SYMLINK_OR_ESCAPE '+str(p))
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  a=os.fstat(fd)
  if not stat.S_ISREG(a.st_mode) or a.st_nlink!=1:raise RuntimeError('ARTIFACT_NOT_INDEPENDENT_REGULAR '+str(p))
  with os.fdopen(fd,'rb',closefd=False) as f:data=f.read()
  b=os.fstat(fd);c=p.stat()
  fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)
  if fields(a)!=fields(b) or fields(b)!=fields(c) or len(data)!=a.st_size:raise RuntimeError('ARTIFACT_UNSTABLE')
  return data
 finally:os.close(fd)
def files(root):
 root=Path(root);result=[]
 if root.is_symlink() or root.resolve()!=root:raise RuntimeError('ARTIFACT_ROOT_LINK')
 for p in sorted(root.rglob('*')):
  if p.is_symlink():raise RuntimeError('ARTIFACT_TREE_LINK '+str(p))
  if p.is_file():read(p);result.append(p)
  elif not p.is_dir():raise RuntimeError('ARTIFACT_SPECIAL')
 return result

def seal(paths,gate,run_id,producer):
 gate=Path(gate);dest=gate/'sealed';dest.mkdir(exist_ok=False)
 rows=[]
 for i,p in enumerate(sorted(set(map(Path,paths)))):
  data=read(p);target=dest/('%06d'%i);h=hashlib.sha256(data).hexdigest()
  with target.open('xb') as f:f.write(data)
  if read(target)!=data or read(p)!=data:raise RuntimeError('ARTIFACT_COPY_MISMATCH')
  rows.append({'path':str(target.relative_to(gate)),'size':len(data),'sha256':h,'run_id':run_id,'candidate':SHA,'tree':TREE,'producer_gate':producer,'original_path':str(p)})
 if not rows:raise RuntimeError('EMPTY_ARTIFACT_SEAL')
 return rows

def verify(rows,gate,run_id,producer):
 gate=Path(gate)
 if not rows or len({r['path'] for r in rows})!=len(rows) or len({r['original_path'] for r in rows})!=len(rows):raise RuntimeError('ARTIFACT_MEMBERSHIP')
 wanted=set()
 for r in rows:
  rel=PurePosixPath(r['path'])
  if rel.is_absolute() or '..' in rel.parts or rel.parts[0]!='sealed':raise RuntimeError('ARTIFACT_RELATIVE_PATH')
  if any(r.get(k)!=v for k,v in {'run_id':run_id,'producer_gate':producer,'candidate':SHA,'tree':TREE}.items()):raise RuntimeError('ARTIFACT_IDENTITY')
  p=gate/rel;data=read(p);wanted.add(p)
  if len(data)!=r['size'] or hashlib.sha256(data).hexdigest()!=r['sha256']:raise RuntimeError('SEALED_ARTIFACT_CHANGED')
 if set(files(gate/'sealed'))!=wanted:raise RuntimeError('SEALED_ARTIFACT_MEMBERSHIP_CHANGED')
 return True

def live_equal(paths,receipts,run,directories=()):
 """Consumers read live paths only if equal to latest sealed producer copy."""
 latest={}
 for receipt in receipts:
  base=Path(run)/'runtime/gates'/receipt['gate']
  verify(receipt['artifacts'],base,Path(run).name,receipt['gate'])
  for row in receipt['artifacts']:latest[row['original_path']]=(base/row['path'],row)
 for directory in map(Path,directories):
  current=set(files(directory))
  expected=set()
  for receipt in receipts:
   members={Path(r['original_path']) for r in receipt['artifacts'] if Path(r['original_path']).is_relative_to(directory)}
   if members:expected=members
  if current!=expected:raise RuntimeError('CONSUMER_DIRECTORY_MEMBERSHIP_CHANGED '+str(directory))
 for p in paths:
  if str(p) not in latest:raise RuntimeError('UNSEALED_CONSUMER_INPUT '+str(p))
  saved,row=latest[str(p)]
  if read(p)!=read(saved):raise RuntimeError('LIVE_PRODUCER_COPY_MISMATCH '+str(p))
 return True

def finalize(receipt,gate,paths,after_copy=None):
 rows=seal(paths,gate,receipt['run_id'],receipt['gate'])
 receipt['artifacts']=rows
 verify(rows,gate,receipt['run_id'],receipt['gate'])
 if after_copy:after_copy({r['original_path']:Path(gate)/r['path'] for r in rows})
 receipt['evidence_root']=str(gate)
 receipt['evidence']={str(Path(gate)/r['path']):r['sha256'] for r in rows}
 receipt['result']='PASS';receipt['wrapper_exit']=0
 return receipt

def producer_inputs(receipts,run,repo):
 """Check live generated inputs before a consumer/cleanup can mutate them.

 Only this repository's build scopes participate; other run roles remain independent.
 Historical receipts themselves are verified exclusively through sealed copies.
 """
 import json
 repo=Path(repo);latest={};roots=set()
 for receipt in receipts:
  if receipt.get('repository')!=str(repo):continue
  base=Path(run)/'runtime/gates'/receipt['gate']
  verify(receipt['artifacts'],base,Path(run).name,receipt['gate'])
  manifest=next((r for r in receipt['artifacts'] if r['original_path']==str(base/'generated-output-digests.json')),None)
  if manifest:
   latest={p:h for p,h in json.loads(read(base/manifest['path'])).items() if Path(p).is_relative_to(repo) and 'build' in Path(p).relative_to(repo).parts}
 for name in latest:
  p=Path(name);parts=p.relative_to(repo).parts;roots.add(repo.joinpath(*parts[:parts.index('build')+1]))
 if latest:live_equal(list(map(Path,latest)),receipts,run)
 # Reject introduced unsealed files within already-produced build scopes as well.
 for root in roots:
  current=set(files(root));expected={Path(p) for p in latest if Path(p).is_relative_to(root)}
  if current!=expected:raise RuntimeError('LIVE_BUILD_MEMBERSHIP_CHANGED '+str(root))
 return {'verified_files':len(latest),'build_roots':sorted(map(str,roots))}
