"""Independent gate evidence. Receipts never depend on mutable output bytes."""
from pathlib import Path, PurePosixPath
import hashlib, json, os, stat
from execution import SHA,TREE
import durability

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

def seal(paths,gate,run_id,producer,namespace='sealed'):
 gate=Path(gate);dest=gate/namespace;durability.exclusive_directory(dest,0o700)
 rows=[]
 for i,p in enumerate(sorted(set(map(Path,paths)))):
  data=read(p);target=dest/('%06d'%i);h=hashlib.sha256(data).hexdigest()
  durability.exclusive_bytes(target,data,0o400)
  if read(target)!=data or read(p)!=data:raise RuntimeError('ARTIFACT_COPY_MISMATCH')
  rows.append({'path':str(target.relative_to(gate)),'size':len(data),'sha256':h,'run_id':run_id,'candidate':SHA,'tree':TREE,'producer_gate':producer,'original_path':str(p)})
 if not rows:raise RuntimeError('EMPTY_ARTIFACT_SEAL')
 return rows

def seal_digest(rows):
 return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()

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

def seal_failure(receipt,gate,paths):
    """Seal diagnostic evidence without converting a failed gate into PASS."""
    gate=Path(gate);paths=set(map(Path,paths));sealed=gate/'sealed'
    if not sealed.exists():
     rows=seal(paths,gate,receipt['run_id'],receipt['gate'])
     verify(rows,gate,receipt['run_id'],receipt['gate'])
     receipt['artifacts']=rows
     receipt['evidence_root']=str(gate)
     receipt['evidence']={str(Path(gate)/r['path']):r['sha256'] for r in rows}
     receipt['failure_evidence_sealed']=True
     receipt['failure_evidence_kind']='PRIMARY_FAILURE_SEAL'
     return receipt
    # A successful immutable copy may later be rejected by its post-copy checks.
    # Preserve that snapshot and publish the later causal detail in a separate,
    # exclusive immutable namespace bound to the exact original seal manifest.
    original=receipt.get('artifacts')
    verify(original,gate,receipt['run_id'],receipt['gate'])
    details=gate/'failure-details.json'
    if details not in paths or not details.is_file():raise RuntimeError('FAILURE_DETAILS_NOT_IN_SUPPLEMENT_INPUTS')
    payload=read(details);payload_digest=hashlib.sha256(payload).hexdigest()
    dest=gate/'failure-supplement';durability.exclusive_directory(dest,0o700)
    binding={'schema':'ep19-immutable-failure-supplement-v1','run_id':receipt['run_id'],
             'producer_gate':receipt['gate'],'candidate':SHA,'tree':TREE,
             'original_seal_manifest_sha256':seal_digest(original),
             'failure_details_original_path':str(details),'failure_details_sha256':payload_digest}
    binding_raw=(json.dumps(binding,indent=2,sort_keys=True)+'\n').encode()
    durability.exclusive_bytes(dest/'binding.json',binding_raw,0o400)
    target=dest/'000000';durability.exclusive_bytes(target,payload,0o400)
    row={'path':str(target.relative_to(gate)),'size':len(payload),'sha256':payload_digest,
         'run_id':receipt['run_id'],'candidate':SHA,'tree':TREE,
         'producer_gate':receipt['gate'],'original_path':str(details)}
    supplement={'schema':'ep19-immutable-failure-supplement-v1',
                'binding_path':str((dest/'binding.json').relative_to(gate)),
                'binding_sha256':hashlib.sha256(binding_raw).hexdigest(),
                'original_seal_manifest_sha256':seal_digest(original),'artifacts':[row]}
    verify_failure_supplement(supplement,gate,receipt['run_id'],receipt['gate'],original)
    receipt['failure_supplement']=supplement
    receipt['failure_evidence_sealed']=True
    receipt['failure_evidence_kind']='IMMUTABLE_FAILURE_SUPPLEMENT'
    return receipt

def verify_failure_supplement(supplement,gate,run_id,producer,original_rows):
 gate=Path(gate);dest=gate/'failure-supplement'
 if not isinstance(supplement,dict) or supplement.get('schema')!='ep19-immutable-failure-supplement-v1':raise RuntimeError('FAILURE_SUPPLEMENT_SCHEMA')
 verify(original_rows,gate,run_id,producer)
 if supplement.get('original_seal_manifest_sha256')!=seal_digest(original_rows):raise RuntimeError('FAILURE_SUPPLEMENT_ORIGINAL_SEAL_BINDING')
 binding_path=gate/PurePosixPath(supplement.get('binding_path',''))
 binding_raw=read(binding_path)
 if hashlib.sha256(binding_raw).hexdigest()!=supplement.get('binding_sha256'):raise RuntimeError('FAILURE_SUPPLEMENT_BINDING_DIGEST')
 binding=json.loads(binding_raw)
 if any(binding.get(key)!=value for key,value in {'run_id':run_id,'producer_gate':producer,'candidate':SHA,'tree':TREE,'original_seal_manifest_sha256':seal_digest(original_rows)}.items()):raise RuntimeError('FAILURE_SUPPLEMENT_IDENTITY')
 rows=supplement.get('artifacts')
 if not isinstance(rows,list) or len(rows)!=1:raise RuntimeError('FAILURE_SUPPLEMENT_MEMBERSHIP')
 row=rows[0];path=gate/PurePosixPath(row.get('path',''))
 if path.parent!=dest or row.get('original_path')!=binding.get('failure_details_original_path'):raise RuntimeError('FAILURE_SUPPLEMENT_PATH')
 payload=read(path)
 if len(payload)!=row.get('size') or hashlib.sha256(payload).hexdigest()!=row.get('sha256') or row.get('sha256')!=binding.get('failure_details_sha256'):raise RuntimeError('FAILURE_SUPPLEMENT_CONTENT')
 if set(files(dest))!={binding_path,path}:raise RuntimeError('FAILURE_SUPPLEMENT_DIRECTORY_MEMBERSHIP')
 return True

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
