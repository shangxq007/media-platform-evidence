"""Real Chromium CDP inputs; task-local simulated adapter, not backend proof."""
from pathlib import Path
import json,time,traceback
from chromium_helpers import Browser
from control import T,now
R=Path(__file__).parent
LABELS=json.loads((R/'LABELS.json').read_text())
b=Browser();locale='en';ESC='\ue00c';BASE='/operations/renders';FIXTURE=BASE+'?metadataFixture=1'
def q(value):return json.dumps(value,ensure_ascii=False)
def label(key):return LABELS[locale][key]
def has(value):return 'document.body.innerText.includes('+q(value)+')'
def locate(selector,name=None):
 b.ev('(()=>{const es=[...document.querySelectorAll('+q(selector)+')].filter(e=>e.getClientRects().length'+('&&(e.getAttribute("aria-label")==='+q(name)+'||e.textContent.trim()==='+q(name)+')' if name else '')+');if(es.length!==1)throw Error("locator count "+es.length);document.querySelectorAll("[data-native-target]").forEach(e=>e.removeAttribute("data-native-target"));es[0].dataset.nativeTarget="yes";es[0].scrollIntoView({block:"center"})})()')
 return '[data-native-target="yes"]'
def button(name):b.click(locate('.ff-render-browser button,[role=dialog] button',name))
def mode(value):b.ev('window.__MetadataFixture.setMode('+q(value)+')')
def launcher(name='Courtyard <final>'):return label('inspectNamed').replace('{name}',name)
def ready(name='Courtyard <final>'):
 b.wait('[...document.querySelectorAll(".ff-render-browser button")].some(e=>e.getAttribute("aria-label")==='+q(launcher(name))+')')
def inspect(name='Courtyard <final>'):
 button(launcher(name));b.wait('!!document.querySelector("[role=dialog] .ff-render-artifacts")')
def close(native=True):
 if native:b.key(ESC)
 else:button(label('detailClose'))
 b.check('Native '+('Escape' if native else 'close pointer')+' focus return '+locale,'!document.querySelector("[role=dialog]")&&document.activeElement.getAttribute("aria-label")==='+q(launcher()))
def refresh(value):
 mode(value);before=b.ev('window.__MetadataFixture.calls.length');button(label('refresh'))
 b.wait('window.__MetadataFixture.calls.length>'+str(before)+'&&window.__MetadataFixture.calls.at(-1).returned');ready()
def audit(state,tag):
 # outerHTML AND every raw attribute value/textContent: includes hidden DOM, aria/title/data, href and descendants.
 result=b.ev('''(()=>{const root=document.querySelector('[role=dialog] .ff-render-artifacts');if(!root)throw Error('missing artifact subtree');const scan=e=>({html:e.outerHTML,text:e.textContent,attrs:[e,...e.querySelectorAll('*')].flatMap(n=>[...n.attributes].map(a=>[a.name,a.value]))});return {root:scan(root.closest('section')),items:[...root.children].map(scan),visible:[...root.children].map(e=>e.innerText),links:root.closest('section').querySelectorAll('a[href],[download],button,input,form').length,dialog:document.querySelector('[role=dialog]').innerText}})()''')
 (R/(tag+'-DOM.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2))
 items=b.ev('window.__MetadataFixture.items')
 assert len(result['items'])==len(items)==5,'Must retain generic placeholders for every item'
 restricted=[]
 for i,item in enumerate(items):
  access=item['metadataAccess'] if state=='mixed' else ('inspectable' if state=='visible' else state.removeprefix('all-'))
  protected=[item[k] for k in ['id','name','type','availability','version','taskId']]
  serialized=json.dumps(result['items'][i],ensure_ascii=False)
  allowed=access=='inspectable'
  passed=all(v in result['visible'][i] for v in protected) if allowed else all(v not in serialized for v in protected)
  b.check(tag+' item '+str(i)+' '+access+' all protected fields '+('visible' if allowed else 'absent'),str(passed).lower())
  if not allowed:
   restricted.append(item)
   key={'denied':'artifactDenied','unknown':'artifactUnknown','stale':'artifactStale','unavailable':'artifactUnavailable'}[access]
   b.check(tag+' generic localized placeholder '+str(i),str(label(key) in result['visible'][i]).lower())
 root=json.dumps(result['root'],ensure_ascii=False)
 for item in restricted:
  # Shared task link independently authorized on allowed items; all other values must be absent across entire artifact section.
  values=[item[k] for k in ['id','name','type','availability','version']]
  b.check(tag+' entire artifact section no restricted identity '+item['id'],str(all(v not in root for v in values)).lower())
 if len(restricted)==5:b.check(tag+' entire artifact subtree excludes restricted taskId',str('task-courtyard' not in root).lower())
 b.check(tag+' task identifier has independent task-level basis',str('task-courtyard' in result['dialog']).lower())
 b.check(tag+' no artifact link download or mutation controls',str(result['links']==0).lower())
 b.ev('document.querySelector(".ff-render-artifacts").scrollIntoView({block:"start"})');b.shot(tag)
 b.check(tag+' viewport has no document horizontal overflow','document.documentElement.scrollWidth<=innerWidth')
def context(value):b.ev('window.__MetadataFixture.changeContext('+q(value)+')')
def start_pending():
 mode('pending');button(label('refresh'));b.wait('window.__MetadataFixture.pendingIds().length>0')
 b.check('Pending clears prior visible artifact tree','!document.querySelector(".ff-render-artifacts")&&!document.querySelector(".ff-render-browser-list")')
def release():
 b.ev('window.__MetadataFixture.resolvePending()');b.wait('window.__MetadataFixture.pendingIds().length===0');time.sleep(.3)
def save_calls(tag):(R/(tag+'-FIXTURE_READ_CALLS.json')).write_text(json.dumps(b.ev('window.__MetadataFixture.calls'),indent=2))
try:
 b.viewport(1440,1000);b.raw('Browser.setDownloadBehavior',{'behavior':'deny','eventsEnabled':True});b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/'});time.sleep(.4)
 b.ev('localStorage.setItem("dev_access_token","SIMULATED_LOCAL_ONLY_NOT_A_CREDENTIAL")')
 b.nav(BASE);b.locale('en');b.wait(has('Render observability unavailable'))
 b.check('Plain unconfigured route remains unavailable',has('Render observability unavailable')+'&&!window.__MetadataFixture&&!document.querySelector("[data-metadata-host]")');b.shot('ordinary-unavailable')
 for locale,width,height in [('en',1440,1000),('en',390,844),('zh-CN',390,844)]:
  tag=locale+'-'+str(width);b.viewport(width,height);b.nav(FIXTURE);b.locale(locale);ready()
  inspect();audit('mixed',tag+'-mixed');close(False)
  # Actual refresh reads, never Render retry/execution. IDs and ordinary values remain unchanged.
  for target in ['all-denied','all-unknown','all-stale','all-unavailable']:
   refresh('visible');inspect();audit('visible',tag+'-before-'+target);close()
   refresh(target);inspect();audit(target,tag+'-'+target);close()
  # Exercise ready OPEN details disappearing under a fixture provider access change.
  for destination in ['denied','unknown','session']:
   refresh('visible');inspect();audit('visible',tag+'-open-before-'+destination)
   context(destination)
   if destination=='session':ready('New session render')
   else:b.wait(has(label('failureDeniedTitle' if destination=='denied' else 'failureUnknownTitle')))
   b.check(tag+' open details removed by provider '+destination,'!document.querySelector("[role=dialog]")&&!document.querySelector(".ff-render-artifacts")&&!document.body.outerHTML.includes("ordinary-version-0")')
   b.shot(tag+'-open-revoked-'+destination);context('reset');ready()
  # A superseded pending success must not restore fields after a newer item-level denial.
  start_pending();button(label('cancel'));mode('all-denied');button(label('retry'));ready();inspect();audit('all-denied',tag+'-denied-before-late')
  release();audit('all-denied',tag+'-denied-after-late');close()
  refresh('visible');inspect();audit('visible',tag+'-new-explicit-allow');close()
  refresh('mixed');start_pending();button(label('cancel'));release()
  b.check(tag+' native cancellation fences late adapter result',has(label('cancelledTitle'))+'&&!document.querySelector(".ff-render-browser-list")')
  mode('mixed');context('reset');ready()
  for destination in ['denied','unknown','session']:
   start_pending();mode('mixed');context(destination)
   if destination=='session':ready('New session render')
   else:b.wait(has(label('failureDeniedTitle' if destination=='denied' else 'failureUnknownTitle')))
   release()
   if destination=='session':
    b.check(tag+' old session response cannot overwrite new owner',has('New session render')+'&&!'+has('Courtyard <final>'))
    inspect('New session render');audit('mixed',tag+'-new-session');b.key(ESC)
   else:b.check(tag+' access '+destination+' fences late reply','!document.querySelector(".ff-render-browser-list")&&!document.querySelector(".ff-render-artifacts")&&!document.querySelector("[role=dialog]")')
   context('reset');ready()
  save_calls(tag)
 requests=b.network
 bad=[x for x in requests if x['method']!='GET' or not (x['url'].startswith('http://127.0.0.1:4198/') or x['url']=='about:blank') or ('/api/' in x['url'] and '/api/v1/me/dashboard' not in x['url']) or '/artifacts/' in x['url']]
 (R/'APPLICATION_TRAFFIC.json').write_text(json.dumps({'requests':requests,'forbidden':bad,'http_mutations':sum(x['method']!='GET' for x in requests)},indent=2))
 assert not bad,bad
 exceptions=[x for x in b.diagnostics if x.get('method')=='Runtime.exceptionThrown']
 assert not exceptions,exceptions
 assert not [x for x in b.diagnostics if 'download' in x.get('method','').lower()], 'Unexpected download event'
 (R/'RESULT.json').write_text(json.dumps({'status':'PASS','tree':T,'checks':len(b.checks),'timestamp':now()},indent=2))
except BaseException:
 (R/'FAILURE.txt').write_text(traceback.format_exc())
 try:b.shot('failure');save_calls('failure')
 except Exception:pass
 raise
finally:
 (R/'ASSISTANCE.json').write_text(json.dumps({'tree':T,'native':'Real Chromium CDP pointer and Escape; DOM locators scroll and mark targets; locale helper dispatches input/change (not native locale input).','fixture':'Opt-in simulated adapter controls outcomes/context and delayed response; no backend permission/auth proof. No render retry/execution. Inert localStorage auth marker in isolated disposable profile.','focus_emulation':True,'viewports':[[1440,1000],[390,844]],'limits':['Desktop headless viewport emulation, not physical mobile/touch/IME/screenreader acceptance','Shared task-courtyard has independent task/attempt basis outside artifact subtree; mixed allowed item independently permits its task link; restricted item subtrees exclude taskId and all-restricted artifact section excludes taskId','DOM includes raw attributes/title/aria/data/hidden/links; React internal JS props are not DOM disclosure','Independent final review and parent-owned gates remain required']},ensure_ascii=False,indent=2))
 try:b.raw('Browser.close',{})
 except Exception:pass
 b.ws.close()
