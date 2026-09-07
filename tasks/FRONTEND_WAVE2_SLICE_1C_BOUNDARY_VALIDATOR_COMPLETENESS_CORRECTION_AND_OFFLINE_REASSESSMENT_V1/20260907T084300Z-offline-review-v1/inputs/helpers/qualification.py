import sys,json,copy,traceback
from pathlib import Path
R=Path(sys.argv[1]);ROOT=R.parents[1];sys.path.insert(0,str(R));sys.path.insert(0,str(ROOT/'helpers'));from native_common import CanvasBrowser
from boundary_validator import verify
b=CanvasBrowser();results=[];traces={}
try:
 for case in ['sync','none','restore_only']:
  url='http://127.0.0.1:4196/lifecycle-away?fixture='+case;b.raw('Page.navigate',{'url':url});b.wait('document.readyState==="complete" && location.search==='+json.dumps('?fixture='+case));b.ev((R/'lifecycle-observer.js').read_text());b.ev((ROOT/'helpers/lifecycle-boundary-v2.js').read_text());b.ev('''(()=>{document.body.innerHTML='<div class="ff-workspace-canvas"></div>';let state={lifetime:{},revision:2,selectedRefs:[{localId:'fixture'}],primaryRef:{localId:'fixture'},agentOpen:false};const listeners=new Set();window.fixtureStore={getSnapshot:()=>state,select:()=>{throw Error('fixture disallows select')},subscribe:fn=>(listeners.add(fn),()=>listeners.delete(fn))};window.fixtureRetire=()=>{state={...state,lifetime:{},revision:3,selectedRefs:[],primaryRef:null};listeners.forEach(fn=>fn())}})()''');armed=b.ev('__boundary.arm(()=>[fixtureStore])')
  if case=='sync':b.ev("addEventListener('pagehide',fixtureRetire)")
  if case=='restore_only':b.ev("addEventListener('pageshow',e=>{if(e.persisted)fixtureRetire()})")
  b.ev('__boundary.installLate()');before=b.ev('__boundary.documentId');b.raw('Page.navigate',{'url':'http://127.0.0.1:4196/lifecycle-away?destination='+case});b.wait('location.search==='+json.dumps('?destination='+case));h=b.raw('Page.getNavigationHistory',{});b.raw('Page.navigateToHistoryEntry',{'entryId':h['entries'][h['currentIndex']-1]['id']});b.wait('typeof __boundary!=="undefined"');trace=b.ev('({documentId:__boundary.documentId,rows:__boundary.rows})');actual=trace['documentId']==before and any(r['kind']=='early-pageshow' and r['event']['persisted'] for r in trace['rows']);v=verify(trace,armed,actual);traces[case]={'trace':trace,'armed':armed,'actual_bfcache':actual};results.append({'name':case,'expected_accept':case=='sync','actual':v,'passed':v['passed']==(case=='sync')});assert results[-1]['passed'],results[-1]
 good=traces['sync']
 for case in ['sampling_before_retirement','wrong_document','wrong_store','wrong_lifetime','missing_rows','truncated_rows','missing_notification','missing_freeze','preview_residue','capture_residue','ordinary_reload_not_bfcache']:
  t=copy.deepcopy(good['trace']);a=copy.deepcopy(good['armed']);actual=good['actual_bfcache'];freeze=next(r for r in t['rows'] if r['kind']=='freeze');hide=next(r for r in t['rows'] if r['kind']=='early-pagehide')
  if case=='sampling_before_retirement':freeze['stores']=copy.deepcopy(hide['stores'])
  if case=='wrong_document':t['documentId']='wrong-document'
  if case=='wrong_store':a['store']+=100
  if case=='wrong_lifetime':a['lifetime']+=100
  if case=='missing_rows':t['rows']=[]
  if case=='truncated_rows':t['rows']=t['rows'][:-2]
  if case=='missing_notification':t['rows']=[r for r in t['rows'] if r['kind']!='notify']
  if case=='missing_freeze':t['rows']=[r for r in t['rows'] if r['kind']!='freeze']
  if case=='preview_residue':freeze['dom']['preview']=True
  if case=='capture_residue':freeze['dom']['capture']=[{'held':[1]}]
  if case=='ordinary_reload_not_bfcache':actual=False
  v=verify(t,a,actual);results.append({'name':case,'fixture_type':'STRUCTURED_NEGATIVE_DERIVATIVE_OF_ACTUAL_FIXTURE_TRACE','expected_accept':False,'actual':v,'passed':not v['passed']});assert not v['passed'],case
 # Real ordinary reload control, not only a flag mutation.
 old=b.ev('__boundary.documentId');b.raw('Page.reload',{});b.wait('document.readyState==="complete" && typeof __boundary==="undefined"');b.ev((R/'lifecycle-observer.js').read_text());b.ev((ROOT/'helpers/lifecycle-boundary-v2.js').read_text());new=b.ev('__boundary.documentId');assert old!=new;v=verify(good['trace'],good['armed'],old==new);results.append({'name':'actual_full_reload_distinguished','old_document':old,'new_document':new,'expected_accept':False,'actual':v,'passed':not v['passed']});assert not v['passed']
except Exception:
 (R/'FAILURE.txt').write_text(traceback.format_exc());raise
finally:
 (R/'QUALIFICATION_RESULTS.json').write_text(json.dumps({'checks':results,'passed':sum(x['passed'] for x in results),'count':len(results),'fixture_mutations_only':True,'negative_rejections_are_expected_not_product_failures':True},indent=2));(R/'FIXTURE_TRACES.json').write_text(json.dumps(traces,indent=2));(R/'COMMANDS.json').write_text(json.dumps(b.commands,indent=2));b.ws.close()
