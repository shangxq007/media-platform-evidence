#!/usr/bin/env python3
"""Prepared regression, not executed. Final-interface labels are mandatory, never guessed.
CDP native pointer/key delivery, DOM target/read/focus/scroll/locale assistance.
"""
from chromium_helpers import Browser
from pathlib import Path
from urllib.parse import urlsplit
import json,time,traceback
R=Path(__file__).parent
C=json.loads((R/'FINAL_INTERFACE.json').read_text())
NODE='[data-testid="workflow-sketch-node"]'; NS='Array.from(document.querySelectorAll('+json.dumps(NODE)+'))'; COUNT=NS+'.length'
MATRIX=[('en',1440,1000),('en',390,844)]
SCENARIOS=['ordinary-unconfigured','empty-add-categories','multi-node-selection-inspection','title-validation-recovery','pointer-keyboard-bounds','capacity-reachability','selected-delete-cancel-confirm','last-delete-cancel-confirm','close-focus','context-owner-retirement','workspace-failure-recovery','no-workflow-io-persistence']
assert C['reviewed'] is True
for locale,_,_ in MATRIX:
 for k in ['add','title','x','y','remove','deleteCancel','deleteConfirm','reset','resetCancel','resetConfirm','boundary','empty','capacity','titleEmptyError','titleLongError','boundaryFeedback','canonical','inspectOpen','inspectClose']:
  assert k in C['labels'][locale],(locale,k)
RETIREMENTS=['project','workspace','tenant']+C['lifecycle_kinds']
SCENARIOS.remove('context-owner-retirement')
SCENARIOS += ['retirement-'+kind for kind in RETIREMENTS] + ['sdk-late-getter-signout-rejection','document-owner-departure']
b=Browser(); runs=[]; locale='en'; width=1440; scenario=''; bootstrap=[]
def target(expr):
 b.ev("document.querySelectorAll('[data-native-target]').forEach(e=>e.removeAttribute('data-native-target'))")
 b.ev('(()=>{const e=('+expr+');if(!e)throw Error("target missing");e.setAttribute("data-native-target","");e.scrollIntoView({block:"nearest",inline:"nearest"});const r=e.getBoundingClientRect();if(!r.width||!r.height)throw Error("target hidden");})()')
 b.click('[data-native-target]')
def text(k):return C['labels'][locale][k]
def visible(expr):return '('+expr+').filter(e=>e.getClientRects().length && getComputedStyle(e).visibility!=="hidden")'
def button_value(value):target(visible('Array.from(document.querySelectorAll("button"))')+'.find(e=>e.textContent.trim()==='+json.dumps(value)+'||e.getAttribute("aria-label")==='+json.dumps(value)+')')
def button(k):button_value(text(k))
def field(k):return visible('Array.from(document.querySelectorAll("label"))')+'.find(e=>e.textContent.trim()==='+json.dumps(text(k))+')?.querySelector("input")'
def typefield(k,value):
 target(field(k));b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'a','code':'KeyA','windowsVirtualKeyCode':65,'modifiers':2});b.raw('Input.insertText',{'text':value}) if value else b.raw('Input.dispatchKeyEvent',{'type':'keyDown','key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8});b.raw('Input.dispatchKeyEvent',{'type':'keyUp','key':'Backspace','code':'Backspace','windowsVirtualKeyCode':8}) if not value else None;time.sleep(.15)
 for label in C.get('commit_after',{}).get(k,[]):button_value(C['labels'][locale][label])
def check(name,expr):
 before=len(b.checks)
 try:b.check(scenario+'/'+name,expr)
 finally:
  if len(b.checks)>before:
   b.checks[-1].update(scenario_id=scenario,run_id=runs[-1]['run_id'],locale=locale,viewport=[width,height])
   (R/'NATIVE_CHECKS.json').write_text(json.dumps(b.checks,ensure_ascii=False,indent=2))
def includes(k):return 'document.body.innerText.includes('+json.dumps(text(k))+')'
def begin(name):
 global scenario
 scenario=name;runs.append({'scenario':name,'run_id':f'{locale}-{width}-{name}','locale':locale,'viewport':[width,height],'status':'running','assertions_before':len(b.checks)})
def end():
 runs[-1].update(status='passed',assertions_after=len(b.checks)); b.shot(f'{locale}-{width}-{scenario}')
 (R/'SCENARIO_RUNS.json').write_text(json.dumps(runs,indent=2))
def fresh():
 b.ev('window.__leavingDocument=true')
 b.raw('Page.navigate',{'url':'http://127.0.0.1:4198/w/workflow-workspace/projects/workflow-project/workflow?workflowFixture=1'})
 b.wait('!window.__leavingDocument && !!document.querySelector(".ff-workflow-sketch")'); b.locale(locale)
 b.wait('!!window.__WorkflowHost')
def add(i=0):button_value(text('add')[i])
def node(i=0):return NS+f'[{i}]'
def select(i=0,key=False):
 if b.ev('!!document.querySelector("[role=dialog]")'):b.key('\ue00c')
 if key:b.ev(node(i)+'.focus()');b.key('\ue007')
 else:target(node(i))
def inspect():
 # Final selectors map the actual existing/shared inspector, not another authority.
 if not b.ev('!!document.querySelector("[role=dialog]")'):button('inspectOpen')
 b.wait('!!('+field('title')+')')
def close():
 if b.ev('!!document.querySelector("[role=dialog]")'):b.key('\ue00c')
def focus_ok():return 'document.activeElement!==document.body && document.activeElement?.isConnected && !document.activeElement.disabled'
def titles():return NS+'.map(e=>e.getAttribute("aria-label"))'
def axis(i,axis):return 'parseFloat('+node(i)+'.style.getPropertyValue("--workflow-node-'+axis+'"))'
def bounds():return NS+'.every(e=>{const x=parseFloat(e.style.getPropertyValue("--workflow-node-x")),y=parseFloat(e.style.getPropertyValue("--workflow-node-y"));return x>=16&&x<=896&&y>=16&&y<=560})'
def context(kind):b.ev('window.__WorkflowHost.context('+json.dumps(kind)+')');time.sleep(.3)
def storage():return b.ev('JSON.stringify({local:Object.fromEntries(Object.entries(localStorage)),session:Object.fromEntries(Object.entries(sessionStorage))})')

SCENARIOS=['renewal-twice','new-session-principal','stale-getter-loaded','logout-late-rejection','long-title-layout','add-arrange-delete','project-access-boundary']
def host(code):
 b.ev('window.__WorkflowHost.'+code);time.sleep(.2)
def close():
 if b.ev('!!document.querySelector("[role=dialog]")'):b.key('\ue00c')
 elif b.ev('!!document.querySelector("#selection-inspector")'):button('inspectClose')
def authored(title='Authored original'):
 add();select();inspect();typefield('title',title)
def retired():
 check('old owner withdrawn',COUNT+'===0 && !document.querySelector("[role=dialog]") && !document.querySelector("#selection-inspector")')
def snap():
 b.ev('window.__savedNodes='+NS+';window.__savedInput='+field('title')+';window.__savedState=JSON.stringify('+NS+'.map(e=>[e.getAttribute("aria-label"),e.style.cssText,e.getAttribute("aria-pressed")]));')
def preserved():
 check('authored DOM state selection and incomplete input retained','window.__savedNodes.every((e,i)=>e==='+NS+'[i]) && window.__savedState===JSON.stringify('+NS+'.map(e=>[e.getAttribute("aria-label"),e.style.cssText,e.getAttribute("aria-pressed")])) && window.__savedInput==='+field('title')+' && window.__savedInput.value==="" && document.activeElement===window.__savedInput')
try:
 for locale,width,height in MATRIX:
  b.viewport(width,height)
  for sid in SCENARIOS:
   begin(sid);fresh();persist=storage();netstart=len(b.network)
   if sid=='renewal-twice':
    add(1);authored();typefield('x','120');typefield('y','152');typefield('title','');snap();b.shot(f'{width}-renewal-before')
    for i in range(2):
     host('setCurrent()');host('emitLoaded()');preserved()
    b.shot(f'{width}-renewal-after')
   elif sid=='new-session-principal':
    for change in [{'sid':'session-B'},{'sid':'session-C','sub':'principal-C'}]:
     authored('OLD');host('setCurrent('+json.dumps(change)+')');host('emitLoaded()');retired();b.shot(f'{width}-retirement-'+change['sid']);authored('NEW');check('new editing works',node()+'.getAttribute("aria-label")==="NEW"');close();button('reset');button('resetConfirm')
   elif sid=='stale-getter-loaded':
    authored('OLD');host('pendingLoaded()');host('setCurrent({sid:"new-sid",sub:"new-principal"})');host('emitLoaded()');retired();authored('NEW');typefield('title','');snap();host('settleGetter()');preserved();host('emitLoaded(true)');preserved();check('disposed native subscriptions inert','window.__WorkflowHost.replayRetired()>0 && window.__WorkflowHost.disposedProbeDeliveries()===0')
   elif sid=='logout-late-rejection':
    authored('OLD');host('pendingLoaded()');context('signout');retired();check('signout synchronous withdrawal','window.__WorkflowHost.synchronousRetirements.at(-1).cards===0');authored('NEW');host('settleGetter()');host('settleSignout(true)');check('late result and rejected redirect do not restore old',COUNT+'===1 && '+node()+'.getAttribute("aria-label")==="NEW" && window.__WorkflowHost.sdkLog.some(e=>e.signout==="rejected")')
   elif sid=='long-title-layout':
    values=['中'*120,'A'*120,'中Ab9'*30]
    for i in range(5):add(i)
    for i,value in enumerate(values):
     select(i,key=True);inspect();typefield('title',value);check('full inspector title '+str(i),field('title')+'.value==='+json.dumps(value));close()
    geometry=b.ev(NS+".map(e=>{const r=e.getBoundingClientRect(),t=e.querySelector('strong').getBoundingClientRect();return {name:e.getAttribute('aria-label'),x:parseFloat(e.style.getPropertyValue('--workflow-node-x')),y:parseFloat(e.style.getPropertyValue('--workflow-node-y')),height:r.height,titleHeight:t.height,lineHeight:getComputedStyle(e.querySelector('strong')).lineHeight,contained:t.left>=r.left&&t.right<=r.right&&t.top>=r.top&&t.bottom<=r.bottom}})")
    (R/f'{width}-GEOMETRY.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2))
    check('fixed cards titles contained two lines',json.dumps(all(g['height']==120 and g['titleHeight']<=40 and g['contained'] for g in geometry)))
    check('default next row 136 spacing',json.dumps(geometry[4]['y']-geometry[0]['y']==136))
    check('full accessible names',json.dumps([g['name'] for g in geometry[:3]]==values))
    b.ev('document.querySelector(".ff-workflow-board").scrollIntoView({block:"start"});document.querySelector(".ff-workflow-board").scrollLeft=0');b.shot(f'{width}-longtitle-board')
    select(2,key=True);b.ev('Array.from(document.querySelectorAll("button")).find(e=>e.textContent.trim()==="Check selected card").focus()');b.key('\ue007');b.wait('!!('+field('title')+')');check('keyboard full inspector accessible',field('title')+'.value==='+json.dumps(values[2])+' && '+focus_ok());b.shot(f'{width}-longtitle-inspector')
   elif sid=='add-arrange-delete':
    authored();close();select(key=True);oldx=b.ev(axis(0,'x'));b.key('\ue014');check('native arrow movement',axis(0,'x')+'==='+str(oldx+24));inspect();button('down');close();button('remove');button('deleteCancel');check('cancel retains',COUNT+'===1');button('remove');button('deleteConfirm');check('delete empty with palette focus',COUNT+'===0 && document.activeElement===document.querySelector(".ff-workflow-palette button:not(:disabled)")')
   elif sid=='project-access-boundary':
    for kind in ['project','access-denied','access-unknown']:
     authored('OLD');context(kind);retired();check('canonical invocation disabled',visible('Array.from(document.querySelectorAll("button"))')+'.some(e=>e.textContent.trim()==="Invoke workflow"&&e.disabled)')
    authored('NEW');check('local editing without canonical grant',COUNT+'===1')
   check('no storage delta',json.dumps(persist==storage()))
   application=[r for r in b.network[netstart:] if r['type'] in ['Fetch','XHR','WebSocket'] or r['method'] not in ['GET','HEAD'] or urlsplit(r['url']).hostname!='127.0.0.1']
   check('no application network writes or requests',json.dumps(not application))
   (R/f'{width}-{sid}-SDK.json').write_text(json.dumps(b.ev('window.__WorkflowHost.sdkLog'),indent=2))
   end()
except Exception:
 if runs:runs[-1]['status']='failed'
 (R/'FAILURE.txt').write_text(traceback.format_exc());b.shot('failed-state');raise
finally:
 (R/'SCENARIO_RUNS.json').write_text(json.dumps(runs,indent=2))
 (R/'ACCOUNTING.json').write_text(json.dumps({'planned_scenarios':len(SCENARIOS),'planned_runs':len(SCENARIOS)*len(MATRIX),'scenario_runs':len(runs),'passed_runs':sum(r['status']=='passed' for r in runs),'checks':len(b.checks),'passed_checks':sum(c['passed'] for c in b.checks),'distinct_check_names':len({c['name'] for c in b.checks}),'repeated_check_executions':len(b.checks)-len({c['name'] for c in b.checks}),'matrix':MATRIX,'acceptance':False},indent=2))
 (R/'BROWSER_DIAGNOSTICS.json').write_text(json.dumps(b.diagnostics,indent=2))
 try:b.raw('Browser.close',{})
 except Exception:pass
