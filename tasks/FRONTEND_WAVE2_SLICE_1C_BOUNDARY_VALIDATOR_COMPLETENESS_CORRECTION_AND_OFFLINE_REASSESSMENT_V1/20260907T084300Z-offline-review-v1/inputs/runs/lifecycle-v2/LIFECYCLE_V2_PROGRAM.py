import json,time,traceback
from native_common import CanvasBrowser,R,T
from scope_check import check
b=CanvasBrowser();b.viewport(1440,1000)
b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(R/'lifecycle-observer.js').read_text()})
b.raw('Page.addScriptToEvaluateOnNewDocument',{'source':(ROOT/'helpers/lifecycle-boundary-v2.js').read_text()})
P='[data-canvas-node="project-node"]'
def probe():return b.ev('({id:__lifecycleProbe.documentId,events:__lifecycleProbe.events,snapshot:__lifecycleProbe.snapshot(),proposals:__lifecycleProbe.proposals(),capture:__lifecycleProbe.captureState(),observations:__lifecycleProbe.observations})')
def ready():b.wait('document.querySelectorAll("[data-canvas-node]").length===2 && __lifecycleProbe.snapshot().length===1');time.sleep(.3)
def record(name,expected,actual,ok,assistance='CDP real document/history navigation and trusted pointer input; read-only React fiber/DOM lifetime observation; no synthetic lifecycle events'):
 b.record(name,expected,actual,ok,assistance=assistance)
def back():
 h=b.raw('Page.getNavigationHistory',{});entry=h['entries'][h['currentIndex']-1];b.raw('Page.navigateToHistoryEntry',{'entryId':entry['id']});ready()
def forward():
 h=b.raw('Page.getNavigationHistory',{});entry=h['entries'][h['currentIndex']+1];b.raw('Page.navigateToHistoryEntry',{'entryId':entry['id']});b.wait('document.title==="External lifecycle fixture"')
try:
 check('browser-lifecycle-before');b.reset();ready();b.click(P);time.sleep(.3);initial=probe();assert initial['snapshot'][0]['selectedRefs']
 b.ev('__lifecycleProbe.router().navigate({to:location.pathname,search:{lifecycleProbe:"same"},hash:"main-content"})');ready();same=probe()
 record('same-scope-query-hash-live-owner','same owner, same lifetime, same revision and membership',{'before':initial,'after':same},initial['snapshot']==same['snapshot'],'DOM-assisted real router navigation intent; read-only React fiber observation, not Selection writes')
 b.ev('document.querySelector("#main-content").focus()');focus=probe()
 record('focus-is-not-selection','focus alone preserves Selection snapshot',{'before':same['snapshot'],'after':focus['snapshot']},same['snapshot']==focus['snapshot'],'DOM focus helper; no Selection mutation')
 b.click('.ff-agent-launcher');b.wait('!!document.querySelector(".ff-agent-composer")');b.click('.ff-agent-composer button[type="submit"]');b.wait('!!document.querySelector("[data-testid=agent-proposal]")');pending=probe()
 record('same-live-proposal-remains-current','proposal token equals current lifetime/revision before navigation',pending,bool(pending['proposals']) and all(p['lifetime']==pending['snapshot'][0]['lifetime'] and p['revision']==pending['snapshot'][0]['revision'] for p in pending['proposals']))
 armed=b.ev('__boundary.arm()');b.ev('__boundary.installLate()')
 b.raw('Page.navigate',{'url':'http://127.0.0.1:4196/lifecycle-away'});b.wait('document.title==="External lifecycle fixture"');away=probe()
 record('full-document-navigation-no-selection','new document has no previous application Selection',away,away['id']!=pending['id'] and away['snapshot']==[])
 back();restored=probe();boundary=b.ev('({documentId:__boundary.documentId,rows:__boundary.rows})');hide=[e for e in restored['events'] if e['event']=='pagehide'];show=[e for e in restored['events'] if e['event']=='pageshow'];actual=restored['id']==pending['id'] and any(e['persisted'] for e in show)
 (R/'BF_CACHE_RUNTIME_OBSERVATIONS.json').write_text(json.dumps({'tree':T,'browser':b.browser_version,'before':pending,'after':restored,'actual_restoration':actual},indent=2))
 record('real-bfcache-restoration-observed','same suspended document returns with real pageshow.persisted=true',{'document_preserved':restored['id']==pending['id'],'pagehide':hide,'pageshow':show},actual)
 verdict=verify(boundary,armed,actual);old_measurement=bool(hide) and all(not v['selectedRefs'] and v['primaryRef'] is None and v['lifetime']!=pending['snapshot'][0]['lifetime'] for e in hide for v in e['snapshot'])
 (R/'DEPARTURE_BOUNDARY_PROOF.json').write_text(json.dumps({'armed':armed,'trace':boundary,'actual_bfcache':actual,'verdict':verdict,'superseded_original_measurement_passed':old_measurement,'original_measurement_is_not_new_gate':True},indent=2))
 record('real-pagehide-retires-before-suspension','matched same-store retirement during pagehide, empty transient state at trusted freeze before suspension, real BFCache return',verdict,verdict['passed'])
 record('real-pageshow-fresh-lifetime','bfcache active Selection empty with fresh lifetime',restored,restored['snapshot'][0]['selectedRefs']==[] and restored['snapshot'][0]['primaryRef'] is None and restored['snapshot'][0]['lifetime']!=pending['snapshot'][0]['lifetime'])
 record('back-does-not-restore-selection','browser Back restored navigation but not Selection snapshot',restored,restored['snapshot'][0]['selectedRefs']==[])
 record('agent-proposal-stale-after-document-retirement','old proposal lifetime differs; retired conversation cannot apply old proposal',{'before':pending['proposals'],'after':restored['proposals'],'snapshot':restored['snapshot'],'proposal_ui_present':b.ev('!!document.querySelector("[data-testid=agent-proposal]")')},all(p['lifetime']!=restored['snapshot'][0]['lifetime'] for p in pending['proposals']) and not b.ev('!!document.querySelector("[data-testid=agent-proposal]")'))
 b.click(P);time.sleep(.3);forward();dest=probe()
 record('forward-does-not-restore-selection','browser Forward restores destination only, no source Selection',dest,dest['snapshot']==[])
 back();again=probe();record('repeat-bfcache-no-membership-resurrection','second restore empty',again,again['snapshot'][0]['selectedRefs']==[])
 b.click(P);time.sleep(.3);pre_reload=probe();b.raw('Page.reload',{});ready();reloaded=probe()
 record('document-reload-no-selection-restoration','fresh document empty Selection, no persistence',{'before':pre_reload,'after':reloaded},reloaded['id']!=pre_reload['id'] and not reloaded['snapshot'][0]['selectedRefs'])
 check('browser-lifecycle-after')
except Exception as e:
 (R/'BROWSER_LIFECYCLE_FAILURE.json').write_text(json.dumps({'tree':T,'error':str(e),'traceback':traceback.format_exc(),'product_or_harness_classification':'REQUIRES_ANALYSIS'},indent=2));raise
finally:
 (R/'BROWSER_LIFECYCLE_RAW_LOG.txt').write_text(json.dumps(b.commands,ensure_ascii=False,indent=2));(R/'NATIVE_LIFECYCLE_RESULTS.json').write_text(json.dumps({'tree':T,'checks':b.checks},indent=2));b.ws.close()
print('REAL_BROWSER_DOCUMENT_BFCACHE_CHECKS_PASS',flush=True)
