"""Completeness of actual JavaCompile task/output scopes, not predicted class counts."""
from pathlib import Path
import json,hashlib
import artifacts
from execution import SHA,TREE

def inventory(paths):
 return [{'path':str(p),'size':len(b),'sha256':hashlib.sha256(b).hexdigest()} for p in sorted(set(paths)) for b in [artifacts.read(p)]]
def validate(run,gate,repo):
 run,gate,repo=map(Path,(run,gate,repo));load=lambda p:json.loads(p.read_text())
 graph=load(gate/'compile-graph.json')
 if any(graph.get(k)!=v for k,v in {'run_root':str(run),'gate':'COMPILE','candidate':SHA,'tree':TREE,'repository':str(repo)}.items()):raise RuntimeError('COMPILE_IDENTITY')
 required=graph['required'];tasks=[r['path'] for r in required];allgraph=[r['path'] for r in graph['graph']]
 if not tasks or len(set(tasks))!=len(tasks) or not set(graph['expected_source_set_tasks'])<=set(tasks) or not set(tasks)<=set(allgraph):raise RuntimeError('MISSING_REQUIRED_COMPILE_TASK')
 if len(list(gate.glob('compile-before*.json')))!=len(tasks) or len(list(gate.glob('compile-after*.json')))!=len(tasks):raise RuntimeError('COMPILE_OUTCOME_MEMBERSHIP')
 manifest=[];outcomes=[]
 for task in required:
  tid=task['path'].replace(':','_');before=load(gate/('compile-before'+tid+'.json'));after=load(gate/('compile-after'+tid+'.json'))
  if before['task']!=task['path'] or after['task']!=task['path'] or before['outputs']!=task['outputs'] or after['outputs']!=task['outputs']:raise RuntimeError('COMPILE_OUTPUT_SCOPE_CHANGED')
  if task['preexisting'] or before['preexisting']:raise RuntimeError('PREEXISTING_COMPILE_OUTPUT')
  outputs=list(map(Path,task['outputs']));dest=Path(task['destination'])
  if not outputs or dest not in outputs or any(p.resolve()!=p or not p.is_relative_to(repo) or 'build' not in p.relative_to(repo).parts for p in outputs):raise RuntimeError('COMPILE_OUTPUT_BOUNDARY')
  if before['sources']!=after['sources'] or inventory([Path(r['path']) for r in before['sources']])!=before['sources']:raise RuntimeError('COMPILE_SOURCE_CHANGED')
  if any(not Path(r['path']).is_relative_to(repo) for r in before['sources']):raise RuntimeError('COMPILE_SOURCE_ESCAPE')
  current=inventory([p for out in outputs for p in (artifacts.files(out) if out.is_dir() else [out] if out.is_file() else [])])
  if current!=after['files']:raise RuntimeError('COMPILE_DECLARED_OUTPUT_LOSS_OR_STALE')
  if after['failure'] or not after['executed']:raise RuntimeError('COMPILE_NOT_EXECUTED')
  if before['sources']:
   if after['skipped'] or after['upToDate'] or after['noSource'] or not after['didWork'] or after['skipMessage']:raise RuntimeError('COMPILE_SKIPPED_CACHED_OR_UP_TO_DATE')
   classes=[r for r in current if Path(r['path']).is_relative_to(dest) and r['path'].endswith('.class') and r['size']>0]
   if not classes:raise RuntimeError('MISSING_REQUIRED_CLASS_OUTPUT')
  else:
   if not after['noSource'] or after['skipMessage']!='NO-SOURCE' or current:raise RuntimeError('UNJUSTIFIED_NO_SOURCE')
  manifest.extend(current);outcomes.append({'task':task['path'],'sources':before['sources'],'outputs':task['outputs'],'outcome':after,'sourceSets':task['sourceSets']})
 return {'result':'PASS','run_id':run.name,'candidate':SHA,'tree':TREE,'tasks':outcomes,'manifest':manifest,'limit':'Actual task graph, source sets including generated participation, observed outcomes and full declared output scopes. No compiler-independent predicted class count.'}
