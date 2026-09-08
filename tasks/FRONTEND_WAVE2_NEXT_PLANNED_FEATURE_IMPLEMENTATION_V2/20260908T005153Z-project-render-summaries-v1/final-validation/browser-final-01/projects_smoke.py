"""Native Chromium Projects workflow. DOM reads/scroll/locale and explicit simulated adapter control are disclosed."""
from pathlib import Path
import json,sys,traceback,urllib.parse
from chromium_helpers import Browser
from control import T
R=Path(__file__).parent;b=Browser();q=json.dumps;failures=[];error=None
base='/w/simulated-workspace/projects';root='.ff-project-browser';listing='.ff-project-browser-list';detail='.ff-project-detail'
def check(name,expr):
 value=b.ev(expr);passed=value is True;b.checks.append({'tree':T,'name':name,'expression':expr,'value':value,'passed':passed})
 (R/'NATIVE_CHECKS.json').write_text(json.dumps(b.checks,ensure_ascii=False,indent=2))
 if not passed:failures.append(name)
def click(selector):
 b.ev('document.querySelector('+q(selector)+').scrollIntoView({block:"nearest"})');b.click(selector)
def button(label):
 expr='Array.from(document.querySelectorAll(".ff-project-browser button")).find(e=>(e.getAttribute("aria-label")||e.textContent.trim())==='+q(label)+')'
 b.ev('('+expr+').scrollIntoView({block:"nearest"})');rect=b.ev('(()=>{const r=('+expr+').getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()')
 for typ in ['mousePressed','mouseReleased']:b.raw('Input.dispatchMouseEvent',{'type':typ,**rect,'button':'left','clickCount':1})
def tabto(selector):
 for _ in range(60):
  if b.ev('document.activeElement===document.querySelector('+q(selector)+')'):return
  b.key('\ue004')
 raise AssertionError('Native Tab cannot reach '+selector)
def typequery(text):
 click(root+' input[type=search]');b.call('input.performActions',{'actions':[{'type':'key','id':'keyboard','actions':[{'type':'keyDown','value':'\ue009'},{'type':'keyDown','value':'a'},{'type':'keyUp','value':'a'},{'type':'keyUp','value':'\ue009'}]}]})
 # Backspace is native key delivery, not DOM input mutation.
 b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8})
 for ch in text:b.key(ch)
def nav(params='projectsFixture=1',locale='en',width=1440):
 b.viewport(width,844 if width<500 else 1000);b.nav(base+('?' + params if params else ''));b.locale(locale);b.wait('!!document.querySelector(".ff-project-browser")')
def loaded():b.wait('document.querySelectorAll(".ff-project-browser-list li").length>0')
inject=r'''(()=>{let e=document.querySelector('.ff-project-browser');let f=e[Object.keys(e).find(k=>k.startsWith('__reactFiber$'))];while(f&&!f.memoizedProps?.source?.adapter)f=f.return;if(!f)throw Error('No Projects source');const source=f.memoizedProps.source;if(source.adapter.origin!=='simulated')throw Error('Refuse real source');const adapter=source.adapter,original=adapter.listRecent;const h=window.__projectsHarness={source,adapter,original,hold:true,pending:[],outcome:'ok'};adapter.listRecent=function(request,signal){if(h.hold)return new Promise((resolve,reject)=>h.pending.push({request,signal,resolve,reject}));if(h.outcome!=='ok')return Promise.resolve({status:h.outcome,scope:request.scope,requestId:request.requestId,explanation:'Controlled simulated failure'});return original(request,signal)};h.finish=async index=>{const p=h.pending[index];p.resolve(await original(p.request,new AbortController().signal))};return {origin:adapter.origin,scope:source.scope}})()'''
try:
 nav('');check('ordinary-unavailable','document.querySelector(".ff-project-browser").textContent.includes("Recent projects unavailable")');check('ordinary-no-fixture','!document.querySelector(".ff-project-browser-list") && !document.querySelector(".ff-project-browser").textContent.includes("SIMULATED PROJECT DATA")');b.shot('ordinary-unavailable')
 nav();loaded();check('three-recent-items','document.querySelectorAll(".ff-project-browser-list li").length===3');check('simulation-disclosed','document.querySelector(".ff-project-browser").textContent.includes("SIMULATED PROJECT DATA")');check('not-full-inventory','document.querySelector(".ff-project-browser").textContent.includes("not a full project inventory")')
 check('default-name-order','Array.from(document.querySelectorAll(".ff-project-browser-list button")).map(e=>e.getAttribute("aria-label")).join("|")==="Inspect Alpha project|Inspect Alpha project|Inspect Zeta <project>"');b.shot('desktop-recent')
 typequery('description literal');check('description-search','document.querySelectorAll(".ff-project-browser-list li").length===1 && document.querySelector(".ff-project-browser-list").textContent.includes("Zeta <project>")')
 typequery('missing-query');check('no-match-distinct','document.querySelector(".ff-project-browser").textContent.includes("No matching recent projects")');button('Reset filters');loaded();check('reset-restores-three','document.querySelectorAll(".ff-project-browser-list li").length===3')
 click('.ff-project-controls select');b.key('\ue015');b.key('\ue007');check('native-status-filter','document.querySelectorAll(".ff-project-browser-list li").length===2')
 click('.ff-project-controls select');b.key('\ue013');b.key('\ue007');click('.ff-project-controls label:last-child select');b.key('\ue015');b.key('\ue007');check('native-desc-sort','document.querySelector(".ff-project-browser-list button").getAttribute("aria-label")==="Inspect Zeta <project>"')
 target='.ff-project-browser-list button[aria-label="Inspect Zeta <project>"]';tabto(target);b.key('\ue007');b.wait('!!document.querySelector(".ff-project-detail")');check('native-enter-exact-details','document.querySelector(".ff-project-detail").textContent.includes("project-zeta") && document.querySelector(".ff-project-detail").textContent.includes("description literal 原文")');check('opaque-no-markup','!document.querySelector(".ff-project-detail project")');b.key('\ue004');check('native-tab-contained','!!document.activeElement.closest(".ff-project-detail")');b.shot('desktop-details');b.key('\ue00c');check('native-escape-closes','!document.querySelector(".ff-project-detail")');check('native-launcher-restored','document.activeElement===document.querySelector('+q(target)+')')
 binding=b.ev(inject);(R/'ADAPTER_ASSISTANCE.json').write_text(json.dumps(binding,indent=2));button('Refresh recent projects');b.wait('window.__projectsHarness.pending.length===1');check('refresh-clears-old-data','!document.querySelector(".ff-project-browser-list")');check('pending-focus-in-workflow','!!document.activeElement.closest(".ff-project-browser")');b.shot('pending-refresh');button('Cancel loading');check('cancelled-distinct','document.querySelector(".ff-project-browser").textContent.includes("Loading cancelled.")');check('cancel-focus-in-workflow','!!document.activeElement.closest(".ff-project-browser")');b.ev('window.__projectsHarness.finish(0)');check('late-cancelled-result-hidden','!document.querySelector(".ff-project-browser-list")');b.ev('window.__projectsHarness.hold=false');button('Retry loading');loaded();check('retry-real-fixture-result','document.querySelectorAll(".ff-project-browser-list li").length===3');b.ev('window.__projectsHarness.outcome="error"');button('Refresh recent projects');b.wait('document.querySelector(".ff-project-browser").textContent.includes("Recent projects error")');check('failure-not-empty','!document.querySelector(".ff-project-browser-list") && !document.querySelector(".ff-project-browser").textContent.includes("No recent projects in this snapshot")');b.shot('failed-refresh');b.ev('window.__projectsHarness.outcome="ok"');button('Retry loading');loaded()
 for state in ['denied','unknown','unsupported','unavailable','error']:
  nav('projectsFixture=1&projectsFixtureFailure='+state);expected='Recent projects access unknown' if state=='unknown' else 'Recent projects '+state;b.wait('document.querySelector(".ff-project-browser").textContent.includes('+q(expected)+')');check('failure-state-'+state,'!document.querySelector(".ff-project-browser-list")');b.shot('state-'+state)
 nav('projectsFixture=1&projectsFixtureEmpty=1');b.wait('document.querySelector(".ff-project-browser").textContent.includes("No recent projects in this snapshot")');check('loaded-empty','!document.querySelector(".ff-project-browser-list")');b.shot('loaded-empty')
 nav('projectsFixture=1&projectsFixtureLimited=1');loaded();check('limited-one','document.querySelectorAll(".ff-project-browser-list li").length===1');b.shot('limited-snapshot')
 nav(locale='zh-CN',width=390);loaded();check('chinese-title','document.querySelector(".ff-project-browser h1").textContent==="最近项目"');check('narrow-no-document-overflow','document.documentElement.scrollWidth<=window.innerWidth+1');b.shot('narrow-chinese');button('检查 Zeta <project>');b.wait('!!document.querySelector(".ff-project-detail")');check('chinese-details','document.querySelector(".ff-project-detail").textContent.includes("项目详情")');check('opaque-chinese-content-retained','document.querySelector(".ff-project-detail").textContent.includes("description literal 原文")');check('narrow-dialog-bounded','(()=>{const r=document.querySelector(".ff-project-detail").getBoundingClientRect();return r.left>=0 && r.right<=window.innerWidth+1})()');b.shot('narrow-chinese-details');b.key('\ue00c');check('narrow-escape-closes','!document.querySelector(".ff-project-detail")')
except BaseException:
 error=traceback.format_exc();(R/'HARNESS_FAILURE.txt').write_text(error);traceback.print_exc()
finally:
 try:
  network=[x for x in b.network if x['url'].startswith(('http:','https:'))];external=[x for x in network if urllib.parse.urlsplit(x['url']).hostname!='127.0.0.1'];mutations=[json.loads(l) for l in (R/'MUTATION_ATTEMPTS.jsonl').read_text().splitlines()] if (R/'MUTATION_ATTEMPTS.jsonl').exists() else []
  (R/'HTTP_ASSERTIONS.json').write_text(json.dumps({'browser_http_requests':len(network),'external_attempts':external,'real_backend_requests':len(external),'projects_http_queries':[x for x in network if '/api/' in x['url'] and x['method']=='GET'],'local_auth_posts':len(mutations),'mutations':mutations},indent=2));assert not external
 except BaseException:error=(error or '')+traceback.format_exc()
 rc=2 if error else 1 if failures else 0
 (R/'SMOKE_EXIT.json').write_text(json.dumps({'assertion_exit':rc,'harness_error':error,'tree':T,'checks':len(b.checks),'passed':sum(x['passed'] for x in b.checks),'failed':failures,'native_inputs':'CDP pointer/Tab/Enter/Escape/arrows/text key events','assistance':['CDP focus emulation','DOM locale and scrollIntoView','explicit simulated adapter via React fiber for held/failure query; no product-byte mutation'],'physical_device':False,'screen_reader_speech':False},ensure_ascii=False,indent=2))
 try:b.raw('Browser.close',{});(R/'BROWSER_CLOSE.json').write_text(json.dumps({'acknowledged':True}))
 except BaseException as exc:(R/'BROWSER_CLOSE.json').write_text(json.dumps({'acknowledged':False,'error_type':type(exc).__name__}))
 b.ws.close()
sys.exit(rc)
