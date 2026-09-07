"""Pure offline, table-driven qualification. Does NOT import/run browser programs."""
from pathlib import Path
import ast,copy,json,hashlib,sys,traceback
R=Path(__file__).resolve().parents[1];I=R/'inputs'
def read(p):return json.loads((I/p).read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def load(p):
 ns={};exec(compile(p.read_text(),str(p),'exec'),ns);return ns['verify']
old=load(I/'helpers/boundary_validator.py');new=load(R/'helpers/boundary_validator_v3.py')
proof=read('runs/lifecycle-v2/DEPARTURE_BOUNDARY_PROOF.json');fixtures=read('runs/qualification/FIXTURE_TRACES.json');prior=read('runs/qualification/QUALIFICATION_RESULTS.json');cases=[]
def bundle(p):return copy.deepcopy({k:p[k] for k in ['trace','armed','actual_bfcache']})
def add(name,b,want,origin,operations=None,recorded=None):cases.append({'name':name,'input':bundle(b),'expected_accept':want,'provenance':origin,'operations':operations or [],'recorded_old':recorded})
source=(I/'helpers/qualification.py').read_text();tree=ast.parse(source)
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.iter,ast.List) and isinstance(n.iter.elts[0],ast.Constant) and n.iter.elts[0].value=='sampling_before_retirement')
cut=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='v' for t in n.targets))
mutation_tree=ast.Module(body=loop.body[:cut],type_ignores=[])
assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) or (isinstance(n,ast.Name) and n.id in {'b','CanvasBrowser','exec','eval','open'}) for n in ast.walk(mutation_tree))
mutation_code=compile(mutation_tree,'EXTRACTED_PURE_ORIGINAL_MUTATIONS','exec');derived=[]
for record in prior['checks']:
 name=record['name']
 if name in fixtures:b=bundle(fixtures[name]);origin='RECORDED_FIXTURE_OFFLINE_REPLAY'
 elif name=='actual_full_reload_distinguished':
  b=bundle(fixtures['sync']);b['actual_bfcache']=record['old_document']==record['new_document'];origin='OFFLINE_REASSESSMENT_OF_RECORDED_RELOAD_DOCUMENT_IDENTITIES_NOT_NEW_RELOAD'
 else:
  ns={'copy':copy,'good':fixtures['sync'],'case':name};exec(mutation_code,ns);b={'trace':ns['t'],'armed':ns['a'],'actual_bfcache':ns['actual']};origin='EXACT_AST_EXTRACTED_ORIGINAL_STRUCTURED_NEGATIVE';derived.append({'name':name,'input':b,'canonical_sha256':digest(b)})
 add('original/'+name,b,record['expected_accept'],origin,recorded=record['actual'])
add('positive/intact_product',proof,True,'RECORDED_PRODUCT_PROOF')
for key in ['lifetime','primary']:
 b=bundle(proof);b['trace']=json.loads((R/'results'/('counterexample-'+key+'.json')).read_text());add('reviewer/missing_'+key,b,False,'EXACT_REVIEWER_THREE_ROW_DELETION',[{'op':'delete_each_stores_key','seq':[8,10,11],'key':key}])
def mutate(name,path,op='delete',value=None,want=False):
 b=bundle(proof);target=b
 for k in path[:-1]:target=target[k]
 if op=='delete':del target[path[-1]]
 else:target[path[-1]]=copy.deepcopy(value)
 add('contract/'+name,b,want,'FOCUSED_DECLARED_FIELD_CONTRACT',[{'op':op,'path':path,**({'value':value} if op!='delete' else {})}])
def change(name,path,value,want=False):mutate(name,path,'replace',value,want)
rows=proof['trace']['rows'];indices={k:next(i for i,r in enumerate(rows) if r['kind']==k and (k!='early-pageshow' or r['event']['persisted'] is True)) for k in ['early-pagehide','notify','late-pagehide','freeze','early-pageshow']}
for kind in ['early-pagehide','notify','late-pagehide','freeze']:
 i=indices[kind];base=['trace','rows',i];s=base+['stores',0]
 for key in ['store','lifetime','revision','refs','primary']:mutate(kind+'/missing_'+key,s+[key])
 for key in ['armed','stores']:mutate(kind+'/missing_'+key,base+[key])
 change(kind+'/empty_stores',base+['stores'],[])
 if kind!='early-pagehide':
  for label,value in [('null',None),('string','4'),('boolean',True)]:change(kind+'/lifetime_'+label,s+['lifetime'],value)
  for label,value in [('string','3'),('boolean',True)]:change(kind+'/revision_'+label,s+['revision'],value)
  change(kind+'/refs_null',s+['refs'],None);change(kind+'/refs_wrong_type',s+['refs'],{})
  change(kind+'/primary_explicit_null',s+['primary'],None,True)
  change(kind+'/primary_wrong_type',s+['primary'],[])
  change(kind+'/primary_nonempty',s+['primary'],proof['armed']['primary'])
  change(kind+'/refs_nonempty',s+['refs'],proof['armed']['refs'])
for key,wrong in [('documentId',1),('store',True),('lifetime',True),('revision',True),('refs',{}),('primary',[])]:
 for label,op,value in [('missing','delete',None),('null','replace',None),('wrong_type','replace',wrong)]:mutate('expected/'+key+'/'+label,['armed',key],op,value)
change('expected/empty_refs',['armed','refs'],[])
for key in ['documentId','rows']:mutate('trace/missing_'+key,['trace',key])
change('trace/null',['trace'],None);change('trace/wrong_type',['trace'],[]);change('expected/null',['armed'],None)
for key in ['seq','kind','documentId']:mutate('row/missing_'+key,['trace','rows',0,key])
change('row/null',['trace','rows',0],None);change('row/seq_bool',['trace','rows',0,'seq'],True);change('row/seq_string',['trace','rows',0,'seq'],'1')
change('row/kind_wrong_type',['trace','rows',0,'kind'],[])
change('restore/wrong_document',['trace','rows',indices['early-pageshow'],'documentId'],'different-document')
for kind in ['early-pagehide','late-pagehide','freeze','early-pageshow']:
 base=['trace','rows',indices[kind],'event']
 mutate(kind+'/missing_event',base)
 for key in ['id','type','trusted','persisted']:mutate(kind+'/event/missing_'+key,base+[key])
 change(kind+'/event/id_bool',base+['id'],True);change(kind+'/event/trusted_string',base+['trusted'],'true')
 change(kind+'/event/type_wrong_value',base+['type'],'synthetic-other-event')
 if kind!='freeze':change(kind+'/event/persisted_string',base+['persisted'],'true')
 else:change(kind+'/event/persisted_not_null',base+['persisted'],True)
base=['trace','rows',indices['freeze'],'departure']
mutate('freeze/missing_departure',base)
for key in ['id','trusted','persisted']:mutate('freeze/departure/missing_'+key,base+[key])
for key in ['trusted','persisted']:change('freeze/departure/'+key+'_string',base+[key],'true')
for kind in ['late-pagehide','freeze']:
 base=['trace','rows',indices[kind],'dom'];mutate(kind+'/missing_dom',base)
 for key in ['preview','proposal','capture']:mutate(kind+'/dom/missing_'+key,base+[key])
 for key in ['preview','proposal']:change(kind+'/dom/'+key+'_string',base+[key],'false')
 mutate(kind+'/capture/missing_held',base+['capture',0,'held'])
 change(kind+'/capture/null_held',base+['capture',0,'held'],None)
 change(kind+'/capture/wrong_held',base+['capture',0,'held'],{})
 change(kind+'/capture/empty_observation',base+['capture'],[])
for label,value in [('string','true'),('integer',1),('null',None),('false',False)]:change('actual_restoration/'+label,['actual_bfcache'],value)
results=[]
for case in cases:
 b=case['input'];before=copy.deepcopy(b);h=digest(b)
 def invoke(fn):
  try:return fn(b['trace'],b['armed'],b['actual_bfcache'])
  except Exception as exc:return {'passed':False,'exception':type(exc).__name__,'message':str(exc)}
 ov=invoke(old);nv=invoke(new);again=invoke(new);unchanged=b==before and digest(b)==h;recorded_equal=case['recorded_old'] is None or ov==case['recorded_old'];ok=nv.get('passed') is case['expected_accept'] and 'exception' not in nv and unchanged and nv==again and recorded_equal and (nv['passed'] or bool(nv.get('errors')))
 results.append({k:v for k,v in case.items() if k!='input'}|{'input_canonical_sha256':h,'old_actual':ov,'corrected_actual':nv,'recorded_old_verdict_exact_match':recorded_equal,'input_unchanged':unchanged,'deterministic_repeat':nv==again,'passed':ok})
assert len({r['name'] for r in results})==len(results)
summary={'mode':'OFFLINE_VALIDATOR_CONTROLS_NOT_BROWSER_CHECKS','count':len(results),'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),'expected_accept_count':sum(r['expected_accept'] for r in results),'expected_reject_count':sum(not r['expected_accept'] for r in results),'prior_controls_replayed':len(prior['checks']),'checks':results}
(R/'results/OFFLINE_QUALIFICATION_RESULTS.json').write_text(json.dumps(summary,indent=2))
(R/'results/ORIGINAL_NEGATIVE_DERIVATIVES.json').write_text(json.dumps({'extracted_mutation_source':ast.unparse(mutation_tree),'source_file_sha256':hashlib.sha256(source.encode()).hexdigest(),'cases':derived},indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))
for r in results:
 if not r['passed']:print('FAILED',r['name'],r['corrected_actual'])
sys.exit(0 if summary['failed']==0 else 1)
