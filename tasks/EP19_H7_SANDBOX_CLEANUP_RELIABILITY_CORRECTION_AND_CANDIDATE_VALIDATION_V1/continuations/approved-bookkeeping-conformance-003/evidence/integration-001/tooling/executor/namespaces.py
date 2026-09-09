"""Exclusive local candidate materialization; original roots are read-only sources."""
from pathlib import Path
import json, os, subprocess
from execution import D,O,H,SHA,TREE,BASE,git,exact,environment,PARENT,CLONE_SOURCE,verify_object_source
from coverage import put,digest
ROLES=('backend','frontend','shadow-fixture')
def repos(run):return [Path(run)/'sources'/r for r in ROLES]
def mappings(run):
 run=Path(run)
 return {str(O/'sources'/r):str(run/'sources'/r) for r in ROLES}
def clone(source,dest,sha=SHA,tree=TREE,base=PARENT):
 verify_object_source(source,sha,tree,base)
 source=Path(source);dest=Path(dest).absolute()
 if dest.resolve()!=dest or not dest.is_relative_to(D) or dest.exists():raise RuntimeError('NONEXCLUSIVE_CLONE_DESTINATION')
 if git(source,'rev-parse',sha+'^{tree}').decode().strip()!=tree:raise RuntimeError('OBJECT_SOURCE_TREE')
 dest.parent.mkdir(parents=True,exist_ok=True)
 env=environment('clone',dest.parent.parent)
 env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0')
 log=dest.parent/(dest.name+'-clone.native.log')
 with log.open('xb') as f:
  # Local object transfer copies bytes (--no-hardlinks), never alternates or shared metadata.
  for argv in [['git','-c','core.hooksPath=/dev/null','clone','--local','--no-hardlinks','--no-checkout','--no-tags',str(source),str(dest)],['git','--no-optional-locks','-c','core.hooksPath=/dev/null','-C',str(dest),'checkout','--detach',sha]]:
   f.write((json.dumps(argv)+'\n').encode());f.flush()
   subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 if (dest/'.git/objects/info/alternates').exists():raise RuntimeError('ALTERNATES')
 if git(dest,'rev-parse','HEAD').decode().strip()!=sha or git(dest,'rev-parse','HEAD^{tree}').decode().strip()!=tree or git(dest,'rev-parse','HEAD^').decode().strip()!=base:raise RuntimeError('CLONE_IDENTITY')
 for p in dest.rglob('*'):
  if p.is_symlink() or (p.is_file() and p.stat().st_nlink!=1):raise RuntimeError('CLONE_LINK '+str(p))
 gd=Path(git(dest,'rev-parse','--absolute-git-dir').decode().strip())
 common=Path(git(dest,'rev-parse','--path-format=absolute','--git-common-dir').decode().strip())
 if gd!=dest/'.git' or common!=gd:raise RuntimeError('SHARED_GIT_METADATA')
 return {'root':str(dest),'object_source':str(source),'git_dir':str(gd),'common_dir':str(common),'candidate':sha,'tree':tree,'base':BASE,'immediate_parent':base,'canonical_comparison_base':BASE,'hardlinks':0,'alternates':0,'clone_log':str(log)}
def prepare(run):
 rows=[clone(CLONE_SOURCE,root,sha=SHA,tree=TREE,base=PARENT) for root in repos(run)]
 for root in repos(run):
  exact(root)
  # Empty directories referenced by the existing candidate's settings/builds.
  (root/'remote-render-worker').mkdir(exist_ok=True)
 put(Path(run)/'namespaces.json',{'schema':'ep19-run-namespaces-v2','original_root':str(O),'version_root':str(D),'helper_root':str(H),'run_root':str(run),'mapping':mappings(run),'repositories':rows,'runtime':str(Path(run)/'runtime'),'resolved_namespaces':resolved_namespaces(run),'shared_dependency_caches':[],'review':'REQUIRED/PENDING'})
 return rows

def scope_roles(scope,run):
 """Add run roles while retaining every canonical/original protected member."""
 old=json.loads((O/'PROTECTION_SCOPE.json').read_text())
 mapping=mappings(run)
 scope['repositories']=old['repositories']+list(mapping.values())
 scope['metadata_roots']=old['metadata_roots']+[str(r/'.git') for r in repos(run)]
 scope['shadow_root']=str(Path(run)/'sources/shadow-fixture')
 allowed=[str(Path(run)/'runtime')]
 for p in old['allowed']:
  for before,after in mapping.items():
   if Path(p).is_relative_to(before):allowed.append(after+str(p)[len(before):])
 # Candidate frontend may also have tool-generated build directories, all bounded.
 scope['allowed']=sorted(set(allowed))
 scope['protected']=sorted(set(scope['protected'])|{str(p) for root in repos(run) for p in exact(root)})
 if 'coverage_derivation' in scope:
  scope['coverage_derivation']['classes']['DECLARED_RUNTIME_OUTPUT']=scope['allowed']
  scope['coverage_derivation']['classes']['FROZEN_EXECUTION_INPUT']=scope['protected']
 scope['preservation_mapping']={'original_roles_retained':True,'run_roles':mapping,'original_output_execution':'FORBIDDEN','review':'REQUIRED/PENDING'}
 return scope

def resolved_namespaces(run):
 run=Path(run);old=json.loads((O/'PROTECTION_SCOPE.json').read_text());mapping=mappings(run)
 rows={}
 for role,root in zip(ROLES,repos(run)):
  oldroot=O/'sources'/role
  outputs=[str(root/Path(p).relative_to(oldroot)) for p in old['allowed'] if Path(p).is_relative_to(oldroot)]
  lane='shadow' if role=='shadow-fixture' else role
  rows[role]={'checkout':str(root),'git_dir':str(root/'.git'),'common_dir':str(root/'.git'),'build_and_tool_outputs':outputs,'gradle_project_cache':str(root/'.gradle'),'node_modules':str(root/'frontend/node_modules') if role=='frontend' else None,'dependency_cache':str(run/'runtime/cache'/lane),'gradle_user_home':str(run/'runtime/cache'/lane/'gradle'),'home':str(run/'runtime/cache'/lane/'home'),'tmp':str(run/'runtime/tmp'/lane),'evidence':str(run/'runtime/gates'),'helper_root':str(H)}
 return rows
